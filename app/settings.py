import argparse

import spacy
import yaml
from app.exceptions import ModeDoesNotExist, NoTextAttributes
from dotenv import dotenv_values
from sentence_transformers import SentenceTransformer

from app.recommenders.algorithms.text_processing.text_processing import TextProcessor

VALID_MODES = [
    'PORTAL-RECOMMENDER',
    'PROVIDERS-RECOMMENDER',
    'SIMILAR_SERVICES_EVALUATION'
]


def load_sbert_model(sbert_settings):
    model = SentenceTransformer(sbert_settings["MODEL_NAME"], device=sbert_settings["DEVICE"])
    model._model_card_vars["name"] = sbert_settings["MODEL_NAME"]

    return model

def read_settings(config_path=None):
    if config_path is None:
        parser = argparse.ArgumentParser(description="Recommendation System CMD.")
        parser.add_argument(
            "--config_file", help="path to config file", type=str, required=True
        )
        args = parser.parse_args()
        config_file = args.config_file
    else:
        config_file = config_path

    with open(config_file) as file:
        backend_settings = yaml.load(file, Loader=yaml.FullLoader)

    # We need to know if we are running in prod or dev env
    if 'prod' in config_file:
        backend_settings['PROD'] = True
    else:
        backend_settings['PROD'] = False

    credentials = dotenv_values(".env")

    backend_settings["SIMILAR_SERVICES"]["SBERT"]["MODEL"] = \
        load_sbert_model(backend_settings["SIMILAR_SERVICES"]["SBERT"])

    backend_settings["TEXT_PROCESSOR"] = TextProcessor(backend_settings["SPACY_MODEL"])
    backend_settings.pop("SPACY_MODEL")

    return {
        'BACKEND': backend_settings,
        'CREDENTIALS': credentials,
    }


def update_backend_settings(config_path):
    with open(config_path) as file:
        backend_settings = yaml.load(file, Loader=yaml.FullLoader)

    APP_SETTINGS['BACKEND'] = backend_settings
    APP_SETTINGS['BACKEND']["SIMILAR_SERVICES"]["SBERT"]["MODEL"] = \
        load_sbert_model(backend_settings["SIMILAR_SERVICES"]["SBERT"])

    backend_settings["TEXT_PROCESSOR"] = TextProcessor(backend_settings["SPACY_MODEL"])
    backend_settings.pop("SPACY_MODEL")


def settings_validation():
    """
    Iterates over define validation methods that have to raise an exception if something went wrong
    """
    validators = [mode_setting_validation,
                  empty_text_attributes_validation]
    for validator in validators:
        validator()


def mode_setting_validation():
    if APP_SETTINGS['BACKEND']['MODE'] not in VALID_MODES:
        raise ModeDoesNotExist(f"FATAL: Mode {APP_SETTINGS['BACKEND']['MODE']} is not valid. Check your config file. "
                               f"Available modes: {VALID_MODES}")


def empty_text_attributes_validation():
    if APP_SETTINGS['BACKEND']['MODE'] == 'PROVIDERS-RECOMMENDER':
        resource_types = APP_SETTINGS['BACKEND'].get('AUTO_COMPLETION', {}).get('RESOURCE_TYPES', {})
        for rtype, rconfig in resource_types.items():
            if len(rconfig.get('TEXT_ATTRIBUTES', [])) == 0:
                raise NoTextAttributes(
                    f"FATAL: resource type '{rtype}' has empty TEXT_ATTRIBUTES in AUTO_COMPLETION config.")
    elif APP_SETTINGS['BACKEND']['MODE'] in ('PORTAL-RECOMMENDER', 'SIMILAR_SERVICES_EVALUATION') \
            and len(APP_SETTINGS['BACKEND']['SIMILAR_SERVICES'].get('TEXT_ATTRIBUTES', [])) == 0:
        raise NoTextAttributes(f"FATAL: Mode {APP_SETTINGS['BACKEND']['MODE']} cannot run with empty "
                               f"text attributes in the config.")


APP_SETTINGS = read_settings()
