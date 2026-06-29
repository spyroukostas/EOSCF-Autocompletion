# Licence

<! --- SPDX-License-Identifier: CC-BY-4.0  -- >

## Overview

The autocompletion pipeline supports multiple **resource types** (services, training resources, datasources, organisations, etc.). Which types are active and which fields are suggested for each type is driven entirely by the deployment configuration — no code changes are needed to add a new field or enable a new resource type.

Each resource type declares:

- `TEXT_ATTRIBUTES` — the text fields embedded with SBERT to compute similarity.
- `ENUMERATED_FIELDS` — the structured fields to suggest values for, each with a `VOCABULARY_TYPE` that is resolved at runtime from the EOSC vocabulary API (`/vocabulary/byType/<TYPE>`).

See [Configuration]({% link configuration.md %}) for the full YAML reference.

---

## Supported Resource Types

The following resource types have a normalisation branch implemented in `CatalogueAPI._reformat_resource()` and can be enabled via configuration without any code changes:

| Resource type key | API endpoint | Notable enumerable fields |
|---|---|---|
| `service` | `/service/all` | `categories`, `scientific_domains`, `access_types`, `trl`, `jurisdiction`, `order_type` |
| `training_resource` | `/trainingResource/all` | `target_groups`, `expertise_level`, `learning_resource_types`, `content_resource_types`, `qualifications`, `access_rights` |
| `datasource` | `/datasource/all` | `scientific_domains`, `datasource_classification`, `jurisdiction`, `trl`, `order_type` |
| `organisation` | `/public/provider/all` | `country`, `legal_status` |
| `adapter` | `/adapter/all` | `programming_language` |
| `interoperability_record` | `/interoperabilityRecord/all` | — |
| `deployable_application` | `/deployableApplication/all` | `scientific_domains` |

---

## Available Vocabulary Types

Vocabulary values are resolved at runtime by calling the EOSC API endpoint `/vocabulary/byType/<VOCABULARY_TYPE>`. Use the `VOCABULARY_TYPE` string from the table below in the YAML configuration:

| Resource category | `VOCABULARY_TYPE` | Typical field name |
|---|---|---|
| Service | `SUBCATEGORY` | `categories` |
| Service | `SCIENTIFIC_SUBDOMAIN` | `scientific_domains` |
| Service | `ACCESS_TYPE` | `access_types` |
| Service | `ORDER_TYPE` | `order_type` |
| Service | `TRL` | `trl` |
| Service | `JURISDICTION` | `jurisdiction` |
| TrainingResource | `TR_EXPERTISE_LEVEL` | `expertise_level` |
| TrainingResource | `TR_ACCESS_RIGHT` | `access_rights` |
| TrainingResource | `TR_CONTENT_RESOURCE_TYPE` | `content_resource_types` |
| TrainingResource | `TR_DCMI_TYPE` | `learning_resource_types` |
| TrainingResource | `TR_QUALIFICATION` | `qualifications` |
| TrainingResource | `TARGET_USER` | `target_groups` |
| Datasource | `DS_CLASSIFICATION` | `datasource_classification` |
| Datasource | `DS_JURISDICTION` | `jurisdiction` |
| Organisation | `PROVIDER_LEGAL_STATUS` | `legal_status` |
| DeployableApplication | `SCIENTIFIC_SUBDOMAIN` | `scientific_domains` |
| Shared | `COUNTRY` | `country` |
| Shared | `LANGUAGE` | `languages` |

---

## Configuring Resource Types

Resource types are configured under `AUTO_COMPLETION.RESOURCE_TYPES` in the YAML config file (`app/config/backend-providers-recommender-prod.yaml`):

```yaml
AUTO_COMPLETION:
  RESOURCE_TYPES:
    service:                                   # resource type key (snake_case)
      TEXT_ATTRIBUTES: ["tagline", "description"]  # fields embedded with SBERT
      ENUMERATED_FIELDS:
        categories:                            # field name in the normalised resource dict
          VOCABULARY_TYPE: "SUBCATEGORY"       # EOSC vocabulary type string
          SIMILARITY_THRESHOLD: 0.5            # min similarity to treat a resource as "similar"
          CONSIDERED_SERVICES_THRESHOLD: 5     # max similar resources to inspect
          FREQUENCY_THRESHOLD: 0.1             # value must appear in ≥10% of similar resources
        scientific_domains:
          VOCABULARY_TYPE: "SCIENTIFIC_SUBDOMAIN"
          SIMILARITY_THRESHOLD: 0.5
          CONSIDERED_SERVICES_THRESHOLD: 5
          FREQUENCY_THRESHOLD: 0.1
    # training_resource:                       # uncomment to enable
    #   TEXT_ATTRIBUTES: ["title", "description"]
    #   ENUMERATED_FIELDS:
    #     expertise_level:
    #       VOCABULARY_TYPE: "TR_EXPERTISE_LEVEL"
    #       SIMILARITY_THRESHOLD: 0.5
    #       CONSIDERED_SERVICES_THRESHOLD: 5
    #       FREQUENCY_THRESHOLD: 0.1
```

Each resource type gets its own Redis key (`{TYPE}_TEXT_EMBEDDINGS`) so types do not interfere with each other. The update loop (`GET /v1/update`) rebuilds embeddings for every type listed under `RESOURCE_TYPES`.

---

## Adding a New Field

To suggest values for an additional field on an existing resource type:

1. Add the field under the resource type's `ENUMERATED_FIELDS` in the YAML config, with a `VOCABULARY_TYPE` from the table above.
2. Restart the service and call `GET /v1/update` to rebuild the embeddings.

Example — adding `trl` suggestions to the `service` type:

```yaml
service:
  TEXT_ATTRIBUTES: ["tagline", "description"]
  ENUMERATED_FIELDS:
    categories:
      VOCABULARY_TYPE: "SUBCATEGORY"
      ...
    trl:
      VOCABULARY_TYPE: "TRL"
      SIMILARITY_THRESHOLD: 0.5
      CONSIDERED_SERVICES_THRESHOLD: 5
      FREQUENCY_THRESHOLD: 0.1
```

---

## Enabling a New Resource Type

To enable autocompletion for a resource type listed in [Supported Resource Types](#supported-resource-types):

1. Add (or uncomment) a block for the type under `AUTO_COMPLETION.RESOURCE_TYPES` in the YAML config.
2. Restart the service and call `GET /v1/update`.

To enable a resource type **not yet listed** above, a code change is also required: add entries for the type in `RESOURCE_TYPE_ENDPOINTS` and `RESOURCE_BY_ID_ENDPOINTS`, and add a normalisation branch in `_reformat_resource()` in `app/databases/registry/catalog_api.py`. Once added there, it can be enabled and configured entirely through YAML going forward.

---

## API Usage

The `POST /v1/auto_completion/suggest` endpoint accepts an optional `resource_type` field:

```json
{
  "resource_type": "service",
  "new_service": {
    "tagline": "...",
    "description": "..."
  },
  "fields_to_suggest": ["categories", "scientific_domains"],
  "maximum_suggestions": 3,
  "existing_fields_values": {}
}
```

- `resource_type` defaults to `"service"` if omitted, preserving backward compatibility with existing callers.
- `fields_to_suggest` must be a subset of the fields configured under `ENUMERATED_FIELDS` for the given resource type, plus `"tags"` for free-text tag suggestions.
