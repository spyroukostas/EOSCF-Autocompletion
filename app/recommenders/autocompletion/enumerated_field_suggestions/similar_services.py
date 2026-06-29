import logging
import time

import pandas as pd
from app.recommenders.algorithms.similar_services_retrieval.preprocessor.embeddings.text_embeddings import \
    get_text_embeddings
from app.recommenders.algorithms.similar_services_retrieval.preprocessor.similarities.text_similarities import \
    TextSimilaritiesManager
from app.settings import APP_SETTINGS

logger = logging.getLogger(__name__)


def naive_search(fields, embeddings, embedding, resource_type="service",
                 similarity_threshold=None, considered_services_threshold=None):

    start_time = time.time()
    similarity_with_services = TextSimilaritiesManager().calculate_similarities_of_service(embedding, embeddings)
    similarity_with_services_df = pd.DataFrame(
        similarity_with_services, columns=["similarity"],
        index=[ind for ind, _ in embeddings]
    )
    logger.debug(f"Auto completion - Naive similarities calculation of similar services {time.time() - start_time}")

    field_config = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"][resource_type]["ENUMERATED_FIELDS"]

    similar_services_per_field = {}
    for field in fields:
        st = similarity_threshold if similarity_threshold is not None else field_config[field]["SIMILARITY_THRESHOLD"]
        cst = considered_services_threshold if considered_services_threshold is not None \
            else field_config[field]["CONSIDERED_SERVICES_THRESHOLD"]

        most_similar = similarity_with_services_df\
            .sort_values(by='similarity', ascending=False)\
            .head(cst)

        most_similar = most_similar[most_similar["similarity"] >= st]

        similar_services_per_field[field] = list(most_similar.index.to_list())

    return similar_services_per_field


def get_similar_services(fields, text_embedding, resource_type="service",
                         similarity_threshold=None, considered_services_threshold=None):
    """
    @param text_embedding: list, the text embedding of the current resource
    @param resource_type: str, the type of resource being autocompleted
    @return: dict mapping each field to a list of similar resource ids
    """

    existing_text_embeddings = get_text_embeddings(resource_type)

    similar_services = naive_search(fields, existing_text_embeddings, text_embedding, resource_type,
                                    similarity_threshold, considered_services_threshold)

    return similar_services
