# Licence

<! --- SPDX-License-Identifier: CC-BY-4.0  -- >

## Introduction

The Autocompletion service has the goal of generating autocompletion suggestions for categorical attributes of an onboarding service. To perform the autocompletion uses the text attributes of the service (i.e. tagline, description) that have already been filled.

Specifically the service currently suggests:

- Categorical fields (e.g. scientific domains, categories) — configurable per resource type
- Tags

The supported resource types and which fields are suggested for each are driven by the deployment configuration. See [Resource Types]({% link resource-types.md %}) for details on how to enable additional resource types or add new fields.

![assets/autocompletion_example.png](assets/autocompletion_example.png)

The application is built as a microservice with a REST API that is deployed in the providers infrastructure (from Athena).

## API

[Autocompletion API](https://app.swaggerhub.com/apis-docs/MikeXydas/Providers-Autocompletion/1.1.2)
