import random

import pandas as pd
from app.databases.registry.registry_selector import get_registry
from app.recommenders.autocompletion.enumerated_field_suggestions.evaluation.evaluation import \
    evaluate_one


def create_random_suggestions(fields_values, max_suggestions_per_field):
    suggestions = {}
    for field, values in fields_values.items():
        suggestions[field] = random.sample(values, max_suggestions_per_field)

    return suggestions


def get_fields_values(fields):
    db = get_registry()

    fields_values = {}
    for field in fields:
        fields_values[field] = getattr(db, f"get_{field}")()

    return fields_values


def get_most_popular_fields_values(services_fields, number_of_values):

    fields_values = {}
    for field in services_fields.columns:
        value_counts = pd.Series([x for item in services_fields[field] for x in item]).value_counts()
        fields_values[field] = value_counts[:number_of_values].keys().to_list()

    return fields_values


def baseline_results(fields_values, services, max_suggestions_per_field):

    fields = fields_values.keys()

    # Initialize evaluation results structure
    evaluation_results = {field: {"precision": [], "recall": [], "f1_score": []} for field in fields}

    # For each existing service
    for _, service in services.iterrows():

        # Create random suggestions
        suggestions = create_random_suggestions(fields_values, max_suggestions_per_field)

        # For every field
        for field in fields:

            # Do not consider services with no field values
            if len(service[field]) == 0:
                continue

            for metric, value in evaluate_one(gold_values=set(service[field]),
                                              suggestions=set(suggestions[field])).items():
                evaluation_results[field][metric].append(value)

    # For every field compute the final results
    aggr_evaluation_results = {field: {metric: sum(results) / len(results)
                                       for metric, results in evaluation_results[field].items()}
                               for field in fields}

    return aggr_evaluation_results


def random_baseline_results(max_suggestions_per_field=3):
    fields = ["categories", "scientific_domains"]

    db = get_registry()
    services = db.get_services(fields)

    # Get all the values for every field
    fields_values = get_fields_values(fields)

    return baseline_results(fields_values, services, max_suggestions_per_field)


def most_popular_baseline_results(max_suggestions_per_field=3):
    fields = ["categories", "scientific_domains"]

    db = get_registry()
    services = db.get_services(fields)

    # Get the <max_suggestions_per_field> most popular values for every field
    fields_values = get_most_popular_fields_values(services[fields], number_of_values=max_suggestions_per_field)

    return baseline_results(fields_values, services, max_suggestions_per_field)


if __name__ == '__main__':

    results = most_popular_baseline_results()
    print(f"Most popular baseline results: {results}")

    results = random_baseline_results()
    print(f"Random baseline results: {results}")
