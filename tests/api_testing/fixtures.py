import pytest


@pytest.fixture
def registered_user_rs_mongo():
    return {
        "request":
            {
                "user_id": 1,
                "service_id": 62,
                "num": 5
            },
        "expected_response":
            {
                "panel_id": "similar_services",
                "recommendations": [
                    386,
                    138,
                    370,
                    82,
                    118
                ],
                "explanations": [
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing."
                ],
                "explanations_short": [
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing"
                ],
                "score": [
                    0.43541143296862467,
                    0.5265261705092077,
                    0.3967509799607228,
                    0.5011148838074491,
                    0.42334997116232737
                ],
                "engine_version": "v3"
            }
    }


@pytest.fixture
def anonymous_user_rs_mongo():
    return {
        "request":
            {
                "service_id": 62,
                "num": 5
            },
        "expected_response":
            {
                "panel_id": "similar_services",
                "recommendations": [
                    386,
                    138,
                    370,
                    82,
                    505
                ],
                "explanations": [
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing.",
                    "Based on the metadata and the text attributes we retrieve the services that are most similar to the one you are currently viewing."
                ],
                "explanations_short": [
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing",
                    "Similar metadata and text to the service you are viewing"
                ],
                "score": [
                    0.5827761193116507,
                    0.5569315553154331,
                    0.4671127696832022,
                    0.5240613371576649,
                    0.4315552520485839
                ],
                "engine_version": "v3"
            }
    }


@pytest.fixture
def completed_project_empty():
    return {
        "request":
            {
                "project_id": 1,
                "num": 5
            },
        "expected_response":
            {
                "panel_id": "project_completion",
                "recommendations": [],
                "explanations": [],
                "explanations_short": [],
                "score": [],
                "engine_version": "v3"
            }
    }


@pytest.fixture
def onboarded_service():
    return {
        "request":
            {
                "resource_type": "service",
                "new_service": {
                    "tagline": "Compute compute compute",
                    "description": "Cloud compute cloud storage compute compute Compute compute compute"
                },
                "fields_to_suggest": [
                    "categories",
                    "scientific_domains"
                ],
                "maximum_suggestions": 3
            },
        "expected_response":
            [
                {
                    "field_name": "categories",
                    "suggestions": [
                        "subcategory-access_physical_and_eInfrastructures-compute-container_management",
                        "subcategory-access_physical_and_eInfrastructures-compute-virtual_machine_management",
                        "subcategory-access_physical_and_eInfrastructures-compute-other"
                    ]
                },
                {
                    "field_name": "scientific_domains",
                    "suggestions": [
                        "scientific_subdomain-generic-generic"
                    ]
                }
            ]
    }


@pytest.fixture
def project_assistant():
    return {
        "request":
            {
              "prompt": "I want a service to visualize my data",
              "max_num": 5
            },
        "expected_response":
            {
                "panel_id": "project_assistant",
                "recommendations": [
                    65,
                    560,
                    390,
                    517
                ],
                "explanations": [
                    "",
                    "",
                    "",
                    ""
                ],
                "explanations_short": [
                    "",
                    "",
                    "",
                    ""
                ],
                "score": [
                    0.5861983895301819,
                    0.5186969041824341,
                    0.5079697370529175,
                    0.5075398683547974
                ],
                "engine_version": "v3"
            }
    }
