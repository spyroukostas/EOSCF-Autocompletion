from datetime import datetime, timezone

from app.databases import redis_db
from app.databases.content_based_rec_db import ContentBasedRecsMongoDB
from app.databases.registry.catalog_api import CatalogueAPI
from app.databases.registry.rs_mongo import RSMongoDB
from app.exceptions import ModeDoesNotExist
from app.recommenders.algorithms.similar_services_retrieval.preprocessor.embeddings.text_embeddings import \
    get_text_embeddings_status
from app.settings import APP_SETTINGS


def test_rs_mongo():
    db = RSMongoDB()

    health_check_error = db.check_health()

    if health_check_error is None:
        return {
            "rs_mongo": {
                "status": "UP",
                "database_type": "Mongo"
            }
        }
    else:
        return {
            "rs_mongo": {
                "status": "DOWN",
                "error": health_check_error,
                "database_type": "Mongo"
            }
        }


def test_catalogue_api():
    db = CatalogueAPI()

    health_check_error = db.check_health()

    if health_check_error is None:
        return {
            "catalog_api": {
                "status": "UP",
                "database_type": "API"
            }
        }
    else:
        return {
            "catalog_api": {
                "status": "DOWN",
                "error": health_check_error,
                "database_type": "API"
            }
        }


def test_content_based_rs_mongo():
    db = ContentBasedRecsMongoDB()
    health_check_error = db.check_health()

    if health_check_error is None:
        return {
            "content_based_recs_mongo": {
                "status": "UP",
                "database_type": "Mongo"
            }
        }
    else:
        return {
            "content_based_recs_mongo": {
                "status": "DOWN",
                "error": health_check_error,
                "database_type": "Mongo"
            }
        }


def test_redis():
    health_check_error = redis_db.check_health()

    if health_check_error is None:
        return {
            "memory_store": {
                "status": "UP",
                "database_type": "Redis"
            }
        }
    else:
        return {
            "memory_store": {
                "status": "DOWN",
                "error": health_check_error,
                "database_type": "Redis"
            }
        }


def test_text_embeddings_freshness():
    resource_types = APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"]
    max_age_hours = 2 * APP_SETTINGS["BACKEND"]["SCHEDULING"]["EVERY_N_HOURS"]

    resource_type_statuses = {}
    for resource_type in resource_types:
        status = get_text_embeddings_status(resource_type)

        if not status["exists"]:
            state = "DOWN"
        elif status["last_error"]:
            state = "STALE"
        elif status["last_updated"] is None:
            state = "STALE"
        else:
            age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(status["last_updated"])) \
                .total_seconds() / 3600
            state = "STALE" if age_hours > max_age_hours else "UP"

        resource_type_statuses[resource_type] = {
            "status": state,
            "last_updated": status["last_updated"],
            "last_error": status["last_error"],
        }

    overall_status = "UP" if all(rt["status"] == "UP" for rt in resource_type_statuses.values()) else "DOWN"

    return {
        "text_embeddings": {
            "status": overall_status,
            "resource_types": resource_type_statuses,
        }
    }


def get_mode_tests():
    if APP_SETTINGS['BACKEND']['MODE'] == 'PORTAL-RECOMMENDER':
        return [test_rs_mongo(), test_content_based_rs_mongo(), test_redis()]
    elif APP_SETTINGS['BACKEND']['MODE'] == 'PROVIDERS-RECOMMENDER':
        return [test_catalogue_api(), test_redis(), test_text_embeddings_freshness()]
    elif APP_SETTINGS['BACKEND']['MODE'] == "SIMILAR_SERVICES_EVALUATION":
        return []
    else:
        raise ModeDoesNotExist(f"Mode {APP_SETTINGS['BACKEND']['MODE']} is not recognised.")


def service_health_test():
    tests = get_mode_tests()

    response = {
        "status": "UP"
    }

    for test in tests:
        response = response | test
        if list(test.values())[0]['status'] == 'DOWN':
            response['status'] = "DOWN"

    return response
