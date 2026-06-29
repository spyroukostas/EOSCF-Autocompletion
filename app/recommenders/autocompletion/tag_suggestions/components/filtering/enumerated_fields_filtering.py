import logging
import time

from app.databases import redis_db
from app.databases.registry.registry_selector import get_registry
from app.recommenders.algorithms.phrases_similarity.phrases_similarity import (
    phrase_similarity, phrases_similarity)
from app.settings import APP_SETTINGS

logger = logging.getLogger(__name__)


def enumerated_fields_filtering(tags, resource_type="service", sim_threshold=0.7):
    """
    Filter out tags that are similar to enumerated field values for the given resource type.
    Sub-values (leaf vocabulary items) are captured and returned so they can be injected
    into the enumerated field suggestions.  Upper/parent values are filtered silently.

    Args:
        tags: DataFrame(columns=[keywords, score])
        resource_type: str, the resource type whose ENUMERATED_FIELDS config is used
        sim_threshold: float ∈ [0,1]

    Returns: DataFrame(columns=[keywords, score]), dict mapping field names to matched IDs
    """
    if len(tags) == 0:
        return tags, {}

    tags, filtered_out_subvalues = filter_enumerated_fields_sub_values(tags, resource_type, sim_threshold)
    tags = filter_enumerated_fields_upper_values(tags, resource_type, sim_threshold)

    return tags, filtered_out_subvalues


def _get_cached_vocabulary_with_names(vocabulary_type):
    cache_key = f"VOCAB_NAMES_{vocabulary_type}"
    if redis_db.check_key_existence(cache_key):
        return redis_db.get_object(cache_key)

    db = get_registry()
    result = db.get_vocabulary_with_names(vocabulary_type)
    redis_db.store_object(result, cache_key, expire_seconds=60 * 60)
    return result


def get_enumerated_field(field_name):
    """Kept for upper-values filtering which uses fixed vocabulary type strings."""
    if redis_db.check_key_existence(field_name):
        return redis_db.get_object(field_name)

    db = get_registry()

    if field_name == "SUBCATEGORIES":
        ret_field = db.get_subcategories_id_and_name()
    elif field_name == "SCIENTIFIC_SUBDOMAINS":
        ret_field = db.get_scientific_subdomains_id_and_name()
    elif field_name == "UPPER_CATEGORIES":
        ret_field = db.get_upper_categories_id_and_name()
    elif field_name == "UPPER_SCIENTIFIC_DOMAINS":
        ret_field = db.get_scientific_upper_domains_id_and_name()
    else:
        raise ValueError(f"Field {field_name} not supported")

    redis_db.store_object(ret_field, field_name, expire_seconds=60 * 60)
    return ret_field


def filter_enumerated_fields_sub_values(tags, resource_type="service", sim_threshold=0.7):
    """
    Filter tags similar to any enumerated field value for the resource type.
    Captured matches are returned so they can be injected as enumerated field suggestions.
    """
    start_time = time.time()

    resource_config = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"].get(resource_type, {})
    enumerated_fields_config = resource_config.get("ENUMERATED_FIELDS", {})

    enumerated_field_values = {
        field: _get_cached_vocabulary_with_names(field_cfg["VOCABULARY_TYPE"])
        for field, field_cfg in enumerated_fields_config.items()
    }

    filtered_out_values_per_field = {}

    tags = tags.reset_index()
    selected_tags = [True] * len(tags)

    for field_category, field_values in enumerated_field_values.items():
        filtered_out_values_per_field[field_category] = \
            find_enumerated_field_sub_values(tags, field_values, sim_threshold, selected_tags)

    tags = tags[selected_tags]

    filtered_out_values_no_conflicts = {}
    for domain, values in filtered_out_values_per_field.items():
        filtered_out_values_no_conflicts[domain] = [value[0] for value in values if len(value) == 1]

    logger.debug(f"Filter metadata values {time.time() - start_time} sec")

    return tags, filtered_out_values_no_conflicts


def find_enumerated_field_sub_values(tags, field_values, sim_threshold, selected_tags):
    filtered_out_values = []

    for ind, row in tags.iterrows():
        matched_fields = []
        for field_id, field_name in field_values:
            if phrase_similarity(field_name, row["text"]) > sim_threshold:
                matched_fields.append(field_id)
                selected_tags[ind] = False

        if len(matched_fields) > 0:
            filtered_out_values.append(matched_fields)

    return filtered_out_values


def filter_enumerated_fields_upper_values(tags, resource_type="service", sim_threshold=0.7):
    """
    Filter tags similar to parent/upper vocabulary values (e.g. broad category names).
    Only applied when the resource type uses SUBCATEGORY or SCIENTIFIC_SUBDOMAIN vocabularies.
    """
    resource_config = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"].get(resource_type, {})
    vocab_types = {
        cfg["VOCABULARY_TYPE"]
        for cfg in resource_config.get("ENUMERATED_FIELDS", {}).values()
    }

    upper_values_names = []

    if "SUBCATEGORY" in vocab_types:
        upper_values_names.extend([v[1] for v in get_enumerated_field("UPPER_CATEGORIES")])

    if "SCIENTIFIC_SUBDOMAIN" in vocab_types:
        upper_values_names.extend([v[1] for v in get_enumerated_field("UPPER_SCIENTIFIC_DOMAINS")])

    if not upper_values_names:
        return tags

    tags = tags[~tags.apply(
        lambda tag:
        phrases_similarity(tag["text"], upper_values_names)
        .apply(lambda sim: sim > sim_threshold).any()
        , axis=1)]

    return tags
