from app.recommenders.autocompletion.tag_suggestions.preprocessor.tag_structures import TagStructuresManager
from app.recommenders.autocompletion.tag_suggestions.preprocessor.tags_embeddings import create_tag_embedding
from app.settings import APP_SETTINGS


def map_with_tags_corpus(candidate_tags, equal_threshold=None, similar_threshold=None):
    """
    Creates a mapping with the existing corpus of tags
    Args:
        candidate_tags: DataFrame[columns={text, score}], a dataframe with candidate tags and their score
        equal_threshold (float): The threshold for 2 tags to be considered equal
        similar_threshold (float): The threshold for 2 tags to be considered similar

    Returns: DataFrame[columns={text, score, popularity}]

    """

    if equal_threshold is None:
        equal_threshold = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["TAGS"]["PHRASES_EQUAL_THRESHOLD"]

    if similar_threshold is None:
        equal_threshold = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["TAGS"]["PHRASES_SIM_THRESHOLD"]

    candidate_tags["norm_popularity"] = 0

    tag_structures = TagStructuresManager()

    # For each candidate tag find the most similar tags in the corpus
    for index, tag in candidate_tags.iterrows():

        tag_embedding = create_tag_embedding(tag["text"])

        # If there is an embedding for this tag
        if tag_embedding is not None:
            most_similar_tags = tag_structures.get_most_similar_tags(value=tag_embedding)
            # Set the score to 0 as they are not keywords from keyword extractor
            most_similar_tags["score"] = 0

            # Get the most similar tag
            most_similar_tag = most_similar_tags.iloc[0]
            # If the most similar tag is above a threshold replace the existing tag with the corpus tag
            if most_similar_tag["similarity_score"] > equal_threshold:
                candidate_tags.at[index, "text"] = most_similar_tag["text"]
                candidate_tags.at[index, "norm_popularity"] = most_similar_tag["norm_popularity"]
                most_similar_tags = most_similar_tags[1:]

            # Of the most similar tags keep the ones that exceed the similarity threshold
            most_similar_tags = most_similar_tags[most_similar_tags['similarity_score'] > similar_threshold]

            # Append to candidate keywords the similar tags
            if not most_similar_tags.empty:
                candidate_tags.merge(most_similar_tags)
        else:  # If the tag contains out-of-vocabulary words
            # Check if there is an exact match with the existing oov tags
            exact_match_tag = tag_structures.get_tag(value=tag["text"])

            if not exact_match_tag.empty:
                candidate_tags.at[index, "norm_popularity"] = exact_match_tag["norm_popularity"].iloc[0]

    return candidate_tags
