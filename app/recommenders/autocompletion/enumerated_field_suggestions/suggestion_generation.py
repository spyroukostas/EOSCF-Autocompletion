from app.databases.registry.registry_selector import get_registry
from app.recommenders.algorithms.similar_services_retrieval.preprocessor.embeddings.text_embeddings import \
    create_text_embedding
from app.recommenders.autocompletion.enumerated_field_suggestions.similar_services import \
    get_similar_services
from app.recommenders.autocompletion.enumerated_field_suggestions.suggestion_candidates import \
    get_candidates
from app.settings import APP_SETTINGS


def get_suggestions_for_enumerated_fields(new_service, requested_fields, maximum_suggestions=5,
                                          existing_fields_values=None, resource_type="service",
                                          evaluation_mode=False, similarity_threshold=None,
                                          considered_services_threshold=None, frequency_threshold=None):
    """
    Args:
        new_service: dict with the name and value for each filled field of a resource
        requested_fields: list<str>, the names of the fields for which auto-completion will be implemented
        maximum_suggestions: int, the maximum number of suggestions per field
        existing_fields_values: dict with the name and the current values of each field
        resource_type: str, the type of resource being autocompleted (e.g. "service", "training_resource")
        evaluation_mode: boolean
        similarity_threshold: float, override the similarity threshold for all fields
        considered_services_threshold: int, override the number of similar resources considered
        frequency_threshold: float, override the frequency threshold for all fields

    Returns: dict with the names and suggested values for all requested fields
    """

    text_embedding = create_text_embedding(new_service, resource_type=resource_type)

    similar_services_ids_per_field = get_similar_services(
        requested_fields, text_embedding, resource_type=resource_type,
        similarity_threshold=similarity_threshold,
        considered_services_threshold=considered_services_threshold)

    if evaluation_mode:
        for _, similar_services in similar_services_ids_per_field.items():
            if new_service["service_id"] in similar_services:
                similar_services.remove(new_service["service_id"])

    all_similar_services_ids = list(
        set().union(*[similar_services for _, similar_services in similar_services_ids_per_field.items()]))

    db = get_registry()
    similar_services = db.get_resources_by_ids(
        resource_type=resource_type,
        ids=all_similar_services_ids,
        attributes=requested_fields,
        remove_generic_attributes=True)

    field_config = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"][resource_type]["ENUMERATED_FIELDS"]

    suggestions = {}
    for requested_field in requested_fields:
        existing_values = existing_fields_values.get(requested_field) if existing_fields_values else None

        ft = frequency_threshold if frequency_threshold is not None \
            else field_config[requested_field]["FREQUENCY_THRESHOLD"]

        field_suggestions = get_candidates(
            field_values=similar_services[similar_services["service_id"]
            .isin(similar_services_ids_per_field[requested_field])][requested_field]
            .values.tolist(),
            frequency_threshold=ft,
            existing_values=existing_values)

        suggestions[requested_field] = field_suggestions \
            if len(field_suggestions) <= maximum_suggestions else field_suggestions[:maximum_suggestions]

    return suggestions
