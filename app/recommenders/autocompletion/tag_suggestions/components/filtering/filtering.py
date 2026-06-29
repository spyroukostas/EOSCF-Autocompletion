import logging

from app.databases.registry.registry_selector import get_registry
from app.recommenders.algorithms.phrases_similarity.phrases_similarity import \
    phrases_similarity
from app.recommenders.autocompletion.tag_suggestions.components.filtering.deduplication import \
    tags_deduplication
from app.recommenders.autocompletion.tag_suggestions.components.filtering.enumerated_fields_filtering import \
    enumerated_fields_filtering
from app.recommenders.autocompletion.tag_suggestions.components.filtering.manual_filtering_rules import \
    in_filter_out_rules
from app.settings import APP_SETTINGS

logger = logging.getLogger(__name__)


def filter_based_on_manual_rules(tags):
    return tags[tags.apply(lambda tag: not in_filter_out_rules(tag["text"]), axis=1)]


def filter_service_providers(tags, sim_threshold):
    # Get the names of all providers
    db = get_registry()
    service_providers = db.get_providers_names()

    tags = tags[~tags.apply(
        lambda tag:
        phrases_similarity(tag["text"], service_providers).apply(lambda sim: sim > sim_threshold).any(), axis=1)]

    return tags


def filtering(candidate_tags, existing_values=None, resource_type="service"):
    """
    Filters the tags candidates list
    Args:
        candidate_tags: DataFrame[columns={text, score}], a dataframe with tags and their score
        existing_values: list[str], a list with the existing tags
        resource_type: str, used to determine which enumerated fields to filter against

    Returns: DataFrame[columns={text, score}]

    """
    candidate_tags = candidate_tags[candidate_tags["score"] > 0]

    if existing_values is not None:
        candidate_tags = candidate_tags[~candidate_tags['text'].isin(existing_values)]

    max_words = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["TAGS"]["MAX_WORDS"]

    if len(candidate_tags) > 0:
        candidate_tags = candidate_tags[candidate_tags['text'].str.split().apply(len) <= max_words]

    sim_threshold = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["TAGS"]["PHRASES_SIM_THRESHOLD"]
    candidate_tags, filtered_enumerated_fields = \
        enumerated_fields_filtering(candidate_tags, resource_type=resource_type, sim_threshold=sim_threshold)

    candidate_tags = filter_based_on_manual_rules(candidate_tags)

    candidate_tags = tags_deduplication(candidate_tags)

    return candidate_tags, filtered_enumerated_fields
