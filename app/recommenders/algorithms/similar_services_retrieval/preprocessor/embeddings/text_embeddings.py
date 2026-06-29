import logging

import spacy
from app.databases.redis_db import (check_key_existence, delete_object,
                                    get_object, store_object)
from app.databases.registry.registry_selector import get_registry
from app.exceptions import (DeprecatedMethod, IdNotExists, MissingAttribute,
                            MissingStructure)
from app.recommenders.algorithms.similar_services_retrieval.preprocessor.sentence_filtering.service_text import \
    ServiceText
from app.settings import APP_SETTINGS
from tqdm import tqdm

logger = logging.getLogger(__name__)
sentencizer = spacy.load("en_core_web_sm")


def _embeddings_key(resource_type=None):
    if resource_type is None:
        return "TEXT_EMBEDDINGS"
    return f"{resource_type.upper()}_TEXT_EMBEDDINGS"


def get_sbert_embeddings(service_text):
    """
    Calculate the embeddings per sentence of the service text.

    Args:
        service_text (ServiceText): An object of type ServiceText containing the cleaned sentences

    Returns:
        A list of embeddings of each sentence
    """
    if len(service_text.sentences) == 0:
        return []

    model = APP_SETTINGS["BACKEND"]["SIMILAR_SERVICES"]["SBERT"]["MODEL"]
    return model.encode(service_text.sentences, show_progress_bar=False)


def create_text_embeddings(resource_type=None):
    """
    Creates the text-based embeddings for all resources of the given type.

    When resource_type is None, uses SIMILAR_SERVICES config (PORTAL mode / service-only).
    When resource_type is given, uses AUTO_COMPLETION.RESOURCE_TYPES config.
    """
    logger.debug("Initializing text embeddings...")

    if resource_type is None:
        text_attributes = APP_SETTINGS["BACKEND"]["SIMILAR_SERVICES"]["TEXT_ATTRIBUTES"]
        db = get_registry()
        resources = db.get_services(attributes=text_attributes)
        id_col = "service_id"
    else:
        text_attributes = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"][resource_type]["TEXT_ATTRIBUTES"]
        db = get_registry()
        resources = db.get_resources_of_type(resource_type, attributes=text_attributes)
        id_col = "service_id"

    if resources.empty:
        logger.warning(f"No resources found for resource type '{resource_type}'. Skipping text embeddings creation.")
        return []


    service_texts = [ServiceText(resource[text_attributes]) for _, resource in resources.iterrows()]
    resource_ids = resources[id_col]

    if APP_SETTINGS["BACKEND"]["SIMILAR_SERVICES"]['METHOD'] == 'SBERT':
        text_embeddings = [(rid, get_sbert_embeddings(text))
                           for rid, text in tqdm(
                                list(zip(resource_ids, service_texts)),
                                desc="Resource text embeddings",
                                disable=not APP_SETTINGS['BACKEND']['PROD']
                            )]
    elif APP_SETTINGS["BACKEND"]["SIMILAR_SERVICES"]['METHOD'] == 'TF-IDF':
        raise DeprecatedMethod("TF-IDF is not supported in version 3.0")
    else:
        raise ValueError("Check config. Allowed methods to generate embeddings are: \"SBERT\"")

    store_object(text_embeddings, _embeddings_key(resource_type))

    return text_embeddings


def create_text_embedding(service, resource_type=None):
    """
    Compute a text embedding for a single resource at request time.

    When resource_type is None, uses SIMILAR_SERVICES config.
    When resource_type is given, uses AUTO_COMPLETION.RESOURCE_TYPES config.
    """
    if resource_type is None:
        text_attributes = APP_SETTINGS["BACKEND"]["SIMILAR_SERVICES"]["TEXT_ATTRIBUTES"]
    else:
        text_attributes = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"][resource_type]["TEXT_ATTRIBUTES"]

    service_attributes = list(service.keys())

    if not all(attr in service_attributes for attr in text_attributes):
        raise MissingAttribute("Resource does not have all necessary fields! Make sure that "
                               f"{text_attributes} are given!")

    text_of_service = ServiceText(service_texts={attr: service[attr] for attr in text_attributes})

    return get_sbert_embeddings(text_of_service)


def update_text_embedding_for_one_service(new_service_id):
    db = get_registry()
    new_service = db.get_service(new_service_id)

    if new_service is None:
        raise IdNotExists("Service id does not exist!")

    embedding = create_text_embedding(new_service)

    embeddings = get_text_embeddings()
    embeddings.append((new_service["_id"], embedding))

    return embeddings


def existence_text_embeddings(resource_type=None):
    return check_key_existence(_embeddings_key(resource_type))


def get_text_embeddings(resource_type=None):
    if not existence_text_embeddings(resource_type):
        raise MissingStructure(f"Text embeddings do not exist for resource type '{resource_type}'!")
    return get_object(_embeddings_key(resource_type))


def delete_text_embeddings(resource_type=None):
    delete_object(_embeddings_key(resource_type))


def initialize_text_embeddings(resource_type=None):
    if not existence_text_embeddings(resource_type):
        logging.info(f"Text embeddings do not exist for resource type '{resource_type}'. Creating...")
        create_text_embeddings(resource_type)
