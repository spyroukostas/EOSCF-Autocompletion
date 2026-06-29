from app.databases.registry.registry_selector import get_registry
from app.recommenders.autocompletion.enumerated_field_suggestions.suggestion_generation import \
    get_suggestions_for_enumerated_fields
from app.settings import APP_SETTINGS


def evaluate_one(gold_values, suggestions):
    correct_suggestions = suggestions.intersection(gold_values)
    # Proportion of suggestions that are in the gold_values
    precision = len(correct_suggestions) / len(suggestions) if len(suggestions) else 0
    # Proportion of gold_values found in the suggestions
    recall = len(correct_suggestions) / len(gold_values) if len(gold_values) else None
    if recall is not None:
        f1_score = 2 * (precision * recall) / (precision + recall) if precision + recall != 0 else 0
    else:
        f1_score = None

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }


def evaluation(similarity_threshold=None, considered_services_threshold=None,
               frequency_threshold=None, maximum_suggestions=5):
    fields = ["categories", "scientific_domains"]

    text_attributes = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"]["service"]["TEXT_ATTRIBUTES"]
    db = get_registry()
    services = db.get_services(attributes=text_attributes + fields)

    # Initialize evaluation results structure
    evaluation_results = {field: {"precision": [], "recall": [], "f1_score": []} for field in fields}

    # For every service in the database
    for _, service in services.iterrows():

        # Create suggestions
        suggestions = get_suggestions_for_enumerated_fields(
            service.to_dict(), fields, evaluation_mode=True,
            similarity_threshold=similarity_threshold,
            considered_services_threshold=considered_services_threshold,
            frequency_threshold=frequency_threshold,
            maximum_suggestions=maximum_suggestions
        )

        # For every evaluated field
        for field in fields:

            # Do not consider services with no field values
            if len(service[field]) == 0:
                continue

            for metric, value in evaluate_one(gold_values=set(service[field]),
                                              suggestions=set(suggestions[field])).items():
                # TODO ignore all metrics of this evaluation or just None
                if value is not None:
                    evaluation_results[field][metric].append(value)

    # For every field compute the final results
    aggr_evaluation_results = {field: {metric: sum(results) / len(results)
                                       for metric, results in evaluation_results[field].items()}
                               for field in fields}

    return aggr_evaluation_results
