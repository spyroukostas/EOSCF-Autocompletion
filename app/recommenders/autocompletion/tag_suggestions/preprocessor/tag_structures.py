import logging

import numpy as np
import pandas as pd
from app.databases.redis_db import (check_key_existence, delete_object,
                                    get_object, store_object)
from app.databases.registry.registry_selector import get_registry
from app.exceptions import MissingStructure
from app.recommenders.autocompletion.tag_suggestions.components.filtering.enumerated_fields_filtering import \
    enumerated_fields_filtering
from app.recommenders.autocompletion.tag_suggestions.components.filtering.filtering import \
    filter_based_on_manual_rules
from app.recommenders.autocompletion.tag_suggestions.preprocessor.tags_embeddings import \
    create_tag_embeddings
from app.settings import APP_SETTINGS
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger(__name__)


class TagStructuresManager:

    @staticmethod
    def _get_tags():
        """
        Returns (dict):  dictionary with the tags text and the popularity of each existing tag
        """
        db = get_registry()
        services_tags = db.get_services(attributes=["tags"])

        def update_tags(tags, new_tag):
            # If there are multiple tags as one (e.g., Combine text, mathematics, ...)
            if "," in new_tag:
                new_tags = [t.strip() for t in new_tag.split(",")]
            else:
                new_tags = [new_tag]

            for tag in new_tags:
                if tag != "":
                    tags[tag] = (tags[tag] + 1) if tag in tags else 1

        tags = {}
        # For every service
        for _, row in services_tags.iterrows():
            # If the service has tags
            if row["tags"] is not None and tags != "":
                # For every tag
                for tag in row["tags"]:
                    update_tags(tags, tag)

        tags = pd.DataFrame({"text": tags.keys(), "popularity": tags.values()})

        # Normalize popularity
        # Log of popularity will give emphasis on smaller popularities differences i.e. 0 and 2
        # compared to differences of higher popularities i.e. 14 and 16
        services_num = services_tags.shape[0]
        tags["norm_popularity"] = (np.log(tags["popularity"]) - np.log(0.4))/(np.log(services_num)-np.log(0.4))

        return tags

    @staticmethod
    def _filter_tags(tags):

        logger.debug("Filtering tags...")

        sim_threshold = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["TAGS"]["PHRASES_SIM_THRESHOLD"]
        tags, _ = enumerated_fields_filtering(tags, resource_type="service", sim_threshold=sim_threshold)
        tags = filter_based_on_manual_rules(tags)

        return tags


    @staticmethod
    def _merge_duplicates(tags):
        logger.debug("Merge duplicates...")

        # Get the lemma of each tag
        text_processor = APP_SETTINGS["BACKEND"]["TEXT_PROCESSOR"]
        tags["text_lemma"] = tags["text"].map(lambda text: text_processor.lemmatization(text))

        idxs_to_remove = []
        # Group based on lemma
        for _, duplicates_group in tags.groupby("text_lemma"):
            # If there is more than 1 entry with this lemma
            if duplicates_group.shape[0] > 1:
                # Get the most popular among the duplicates
                most_popular_duplicate = duplicates_group[["popularity"]].idxmax()[0]
                # Add all the duplicates but the most popular to the list of rows that will be removed
                duplicate_idxs = duplicates_group.index.tolist()
                duplicate_idxs.remove(most_popular_duplicate)
                idxs_to_remove.extend(duplicate_idxs)

                # Modify the popularity of the most popular duplicate
                pop_sum = duplicates_group["popularity"].sum()
                tags.at[most_popular_duplicate, "popularity"] = pop_sum

        # Remove all the duplicates
        tags.drop(idxs_to_remove, inplace=True)
        tags = tags.reset_index()

        return tags


    def create_tags_structures(self):
        """
        Stores to elastic search a dictionary (columns=[keyword, popularity, prepr_keyword])
        with the existing tags
        """

        logger.debug("Initializing tag structures...")

        # Get a dataframe with the existing tags and their popularity (# of services in which they appear)
        tags = self._get_tags()

        # Filter tags
        tags = self._filter_tags(tags)

        # Remove duplicates
        tags = self._merge_duplicates(tags)

        # Create tags embeddings
        tags = create_tag_embeddings(tags)

        # Store dictionary with tags
        store_object(tags, "TAGS")

        # Create nn structure for efficient search based on embeddings
        embeddings = tags[tags["embedding"].notnull()]["embedding"]
        if embeddings.empty:
            logger.warning("No tag embeddings available; skipping nearest-neighbor structure.")
            store_object(None, "TAGS_NN")
        else:
            nbrs = NearestNeighbors(n_neighbors=min(5, len(embeddings)), algorithm='ball_tree', metric='euclidean')\
                .fit(embeddings.values.tolist())
            store_object(nbrs, "TAGS_NN")

    def get_tag_structure(self):
        if not self.existence_tag_structures():
            raise MissingStructure("Tags structure does not exist!")
        return get_object("TAGS")

    def get_tag_nn_structure(self):
        if not self.existence_tag_structures():
            raise MissingStructure("Tags nearest_neighbors structure does not exist!")
        return get_object("TAGS_NN")

    def get_most_similar_tags(self, value):
        """
        Returns the 5 most similar tags based on the given embedding
        Args:
            value (np.array): The embedding of a tag

        Returns: DataFrame
        """

        tags_nn = self.get_tag_nn_structure()

        if tags_nn is None:
            return pd.DataFrame()

        distances, indices = tags_nn.kneighbors([value])

        tags = self.get_tag_structure()

        # Ignore tags without embedding
        tags = tags[tags["embedding"].notnull()]

        most_similar_tags = tags.iloc[indices[0]]
        most_similar_tags["similarity_score"] = [1/(1 + distance) for distance in distances[0]]

        return most_similar_tags

    def get_tag(self, value):
        """
        Returns an existing tag if there is an exact march with the value.
        (Checks only existing tags without embeddings)
        Args:
            value (str): The name of a tag

        Returns (DataFrame)
        """
        tags = self.get_tag_structure()

        # Get all the tags without embedding
        oov_tags = tags[tags["embedding"].isnull()]

        return oov_tags[oov_tags["text"] == value]

    @staticmethod
    def existence_tag_structures():
        return check_key_existence("TAGS") and check_key_existence("TAGS_NN")

    def initialize_tag_structures(self):
        if not self.existence_tag_structures():
            logging.info("Tag structures do not exist.Creating...")
            self.create_tags_structures()

    @staticmethod
    def delete_tag_structures():
        delete_object("TAGS")
        delete_object("TAGS_NN")


if __name__ == "__main__":
    TagStructuresManager().create_tags_structures()
