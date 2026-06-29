# Licence

<! --- SPDX-License-Identifier: CC-BY-4.0  -- >

## Introduction

The autocompletion application uses both configuration files and environment variables to control its behaviour. We provide a detailed description of the configuration process below.

## Configuration Overview

The bare minimum configuration needed is creating the `.env` file in the root directory of the project. This file contains the environment variables needed to run the application.

One can then change the behavioral configuration file found in `app/config/backend-providers-recommender-prod.yaml` that has variables controlling fastapi settings, similar services model, and tag suggestion parameters.

- `.env`: Must be created, should never be committed to the repository.
- `app/config/backend-providers-recommender-prod.yaml`: Optional, the default values for the model configuration have been evaluated and work well.

## Configuration Files

The configuration file (`app/config/backend-providers-recommender-prod.yaml`) controls:

- The mode of the application (it should always be `"PROVIDERS-RECOMMENDER"`)
- `fastapi` configuration (workers, host, port, etc.)
- similar services model configuration
- auto-completion model configuration
- tag suggestion model configuration

We provide a detailed example of the configuration file below:

```yaml
VERSION_NAME: "v2"  # Should be changed to differentiate between different versions of the model
                    # It is used in logging and monitoring
MODE: "PROVIDERS-RECOMMENDER"  # Should always be "PROVIDERS-RECOMMENDER"

FASTAPI:  # Fastapi configuration
  WORKERS: 1  # To run in low memory setting we recommend using 1 worker
  DEBUG: False
  RELOAD: False
  HOST: '0.0.0.0'
  PORT: 4559

SCHEDULING:  # Decides the frequency of updating the internal structures of the model (embeddings, similarities)
  EVERY_N_HOURS: 6

SPACY_MODEL: "en_core_web_sm"  # Used for text processing. Using a bigger model did not affect performance.

SIMILAR_SERVICES:  # Used in PORTAL-RECOMMENDER mode only; controls the similar-services pipeline
  TEXT_ATTRIBUTES: ["tagline", "description"]  # Text attributes used for SBERT embeddings

  SENTENCE_FILTERING_METHOD: "KEYWORD"  # Possible values "NONE", "KEYWORD", "NER". Filters uninformative sentences before embedding.

  METHOD: "SBERT"  # Method used for calculating text embeddings. Currently only SBERT is supported.
  SBERT:  # SBERT configuration
    MODEL_NAME: 'paraphrase-MiniLM-L6-v2'
    DEVICE: "cpu"

AUTO_COMPLETION:  # Configuration for the auto-completion model
  RESOURCE_TYPES:   # One entry per resource type to enable autocompletion for
    service:
      TEXT_ATTRIBUTES: ["tagline", "description"]  # Text fields embedded with SBERT for this type
      ENUMERATED_FIELDS:  # Fields to suggest values for
        categories:
          VOCABULARY_TYPE: "SUBCATEGORY"   # Vocabulary type from /vocabulary/byType/<TYPE>
          SIMILARITY_THRESHOLD: 0.5  # Min similarity to treat a resource as "similar"
          CONSIDERED_SERVICES_THRESHOLD: 5  # Max number of similar resources to inspect
          FREQUENCY_THRESHOLD: 0.1  # Value must appear in ≥10% of similar resources to be suggested

        scientific_domains:
          VOCABULARY_TYPE: "SCIENTIFIC_SUBDOMAIN"
          SIMILARITY_THRESHOLD: 0.5
          CONSIDERED_SERVICES_THRESHOLD: 5
          FREQUENCY_THRESHOLD: 0.1

        # Uncomment to add more fields for this resource type.
        # The VOCABULARY_TYPE must be a valid EOSC vocabulary type string.
        # access_types:
        #   VOCABULARY_TYPE: "ACCESS_TYPE"
        #   SIMILARITY_THRESHOLD: 0.5
        #   CONSIDERED_SERVICES_THRESHOLD: 5
        #   FREQUENCY_THRESHOLD: 0.1

        # trl:
        #   VOCABULARY_TYPE: "TRL"
        #   SIMILARITY_THRESHOLD: 0.5
        #   CONSIDERED_SERVICES_THRESHOLD: 5
        #   FREQUENCY_THRESHOLD: 0.1

        # order_type:
        #   VOCABULARY_TYPE: "ORDER_TYPE"
        #   SIMILARITY_THRESHOLD: 0.5
        #   CONSIDERED_SERVICES_THRESHOLD: 5
        #   FREQUENCY_THRESHOLD: 0.1

        # jurisdiction:
        #   VOCABULARY_TYPE: "JURISDICTION"
        #   SIMILARITY_THRESHOLD: 0.5
        #   CONSIDERED_SERVICES_THRESHOLD: 5
        #   FREQUENCY_THRESHOLD: 0.1

    # Uncomment to enable autocompletion for additional resource types.
    # No code changes are required — just add the block here and restart the service.

    # training_resource:
    #   TEXT_ATTRIBUTES: ["title", "description"]
    #   ENUMERATED_FIELDS:
    #     target_groups:
    #       VOCABULARY_TYPE: "TARGET_USER"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
    #     expertise_level:
    #       VOCABULARY_TYPE: "TR_EXPERTISE_LEVEL"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
    #     learning_resource_types:
    #       VOCABULARY_TYPE: "TR_DCMI_TYPE"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1

    # datasource:
    #   TEXT_ATTRIBUTES: ["name", "description"]
    #   ENUMERATED_FIELDS:
    #     scientific_domains:
    #       VOCABULARY_TYPE: "SCIENTIFIC_SUBDOMAIN"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
    #     datasource_classification:
    #       VOCABULARY_TYPE: "DS_CLASSIFICATION"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
    #     jurisdiction:
    #       VOCABULARY_TYPE: "DS_JURISDICTION"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1

    # organisation:
    #   TEXT_ATTRIBUTES: ["name", "description"]
    #   ENUMERATED_FIELDS:
    #     country:
    #       VOCABULARY_TYPE: "COUNTRY"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
    #     legal_status:
    #       VOCABULARY_TYPE: "PROVIDER_LEGAL_STATUS"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1

    # deployable_application:
    #   TEXT_ATTRIBUTES: ["tagline", "description"]
    #   ENUMERATED_FIELDS:
    #     scientific_domains:
    #       VOCABULARY_TYPE: "SCIENTIFIC_SUBDOMAIN"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1

  TAGS:
    KEYWORD_EXTRACTION_METHOD: "textrank"  # Method that will be used for initial keyword discovery
    SCORE_WEIGHT: 0.7  # Weight of the score when deciding which tags to propose
    MAX_WORDS: 3  # Max number of words in a tag
    PHRASES_SIM_THRESHOLD: 0.7  # Threshold for considering two phrases similar
    PHRASES_EQUAL_THRESHOLD: 0.9  # Threshold for considering two phrases similar
    # Note: TEXT_ATTRIBUTES for tag suggestion is taken per resource type from RESOURCE_TYPES above
```

### Adding a new enumerated field

To suggest values for an additional field (e.g. `trl`) on an existing resource type, add it under `ENUMERATED_FIELDS` in the YAML config with a valid `VOCABULARY_TYPE`. Available vocabulary types are listed in `ARCHITECTURE.md`. Restart the service and trigger `GET /v1/update` to rebuild the embeddings.

### Enabling a new resource type

To enable autocompletion for a new resource type (e.g. `training_resource`), uncomment or add a block under `AUTO_COMPLETION.RESOURCE_TYPES`. No code changes are required. The update loop will automatically build text embeddings for the new type on the next run (at startup or via `GET /v1/update`).

## Environmental Variables

The environmental variables control integration with other services and databases. The `.env` file should be created in the root directory of the project and should contain the following variables:

```bash
# Redis connection variables (deployed through docker-compose)
INTERNAL_REDIS_HOST=redis
INTERNAL_REDIS_PORT=6379
INTERNAL_REDIS_PASSWORD=redis_psd

# Monitoring services
SENTRY_SDN=https://asd1asd2.ingest.sentry.io/asd1asd2
CRONITOR_API_KEY=asd1asd2
```

## Security Considerations

Each variable that affects the behavior of the model and is not considered secret should be added to the configuration file (`app/config/backend-providers-recommender-prod.yaml`).

The variables that are considered secret should be added to the `.env` file. The `.env` file should never be committed to the repository. It should be created manually on the server.
