import logging
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)
from app.databases.registry.registry_abc import Registry
from app.exceptions import (APIResponseError, APIResponseFormatException,
                            IdNotExists, RegistryMethodNotImplemented)


class CatalogueAPI(Registry):
    def __init__(self):
        super().__init__()
        self.catalogue_base_url = "https://api.providers.sandbox.eosc-beyond.eu"

    def check_health(self) -> Optional[str]:
        try:
            self._get_request(f"{self.catalogue_base_url}/vocabulary/byType")
        except APIResponseError as e:
            return "Cannot connect with catalogue API"
        return None

    @staticmethod
    def _get_request(request):
        response = requests.get(request)

        if response.status_code == 404:
            return None
        elif response.status_code != 200:
            raise APIResponseError("Error at request in catalogue API!")

        return response.json()

    @staticmethod
    def _get_leaves_of_metadata_hierarchies(scientific_domains, categories):
        scientific_subdomains = [item["scientificSubdomain"] for item in scientific_domains]
        subcategories = [item["subcategory"] for item in categories]

        return scientific_subdomains, subcategories

    def _normalize_domain_category_fields(self, r: dict) -> None:
        subdomains, subcategories = self._get_leaves_of_metadata_hierarchies(
            r.pop("scientificDomains", None) or [],
            r.pop("categories", None) or []
        )
        r["scientific_domains"] = subdomains
        r["categories"] = subcategories

    def _reformat_service(self, service):
        self._normalize_domain_category_fields(service)
        return service

    # TODO change to one call
    def get_services_by_ids(self, ids, attributes=None, remove_generic_attributes=False):
        services = []
        for service_id in ids:
            service = self._get_request(f"{self.catalogue_base_url}/resource/{service_id}")
            if service is None:
                raise IdNotExists(f"Service id {service_id} does not exist!")
            services.append(self._reformat_service(service))

        if len(services):
            services_df = pd.DataFrame(services)
            services_df.rename(columns={'id': 'service_id'}, inplace=True)
            services_df = services_df[["service_id"] + attributes]
        else:
            services_df = pd.DataFrame(columns=["service_id"] + attributes)

        if remove_generic_attributes:
            self._remove_general_attributes_from_services(services_df)

        return services_df

    def get_services(self, attributes=None, reformat=True):
        """
        Args:
            attributes: list, the requested attributes for the services
            reformat: boolean, when true services attributes are reformated to be independent of the selected registry
        """
        if attributes is None:
            attributes = []

        # TODO currently we have hardcoded 8000 as maximum quantity
        response = self._get_request(f"{self.catalogue_base_url}/service/all?quantity=8000")

        try:
            if reformat:
                services = [self._reformat_service(service) for service in response["results"]]
            else:
                services = response["results"]
        except KeyError as e:
            raise APIResponseFormatException(f"{e} does not exist in the response's fields")

        cols = list(set(["service_id"] + attributes))
        if len(services):
            services_df = pd.DataFrame(services)
            services_df.rename(columns={'id': 'service_id'}, inplace=True)
            services_df = services_df.reindex(columns=cols, fill_value="")
        else:  # If there are no services
            services_df = pd.DataFrame(columns=cols)

        self._remove_general_attributes_from_services(services_df)

        return services_df

    def get_service(self, service_id, reformat=True, remove_generic_attributes=True):
        service = self._get_request(f"{self.catalogue_base_url}/resource/{service_id}")

        if service is None:
            raise IdNotExists(f"Service id {service_id} does not exist!")

        if reformat:
            service = self._reformat_service(service)

        if remove_generic_attributes:
            self._remove_general_attributes_from_single_service(service)
        return service

    def get_scientific_domains(self):
        return [item["id"] for item in
                self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SCIENTIFIC_SUBDOMAIN")]

    def get_scientific_subdomains_id_and_name(self):
        return [(item["id"], item["name"]) for item in
                self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SCIENTIFIC_SUBDOMAIN")]

    def get_scientific_upper_domains_id_and_name(self):
        return [(item["id"], item["name"]) for item in
                self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SCIENTIFIC_DOMAIN")]

    def get_specific_scientific_domain_name(self, scientific_domain_id):
        res = self._get_request(f"{self.catalogue_base_url}/vocabulary/{scientific_domain_id}")
        if res is not None:
            return res["name"]
        else:
            raise IdNotExists(f"Scientific domain id {scientific_domain_id} does not exist!")

    def get_categories(self):
        return [item["id"] for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SUBCATEGORY")]

    def get_subcategories_id_and_name(self):
        return [(item["id"], item["name"])
                for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SUBCATEGORY")]

    def get_upper_categories_id_and_name(self):
        supercategory = [(item["id"], item["name"])
                         for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/SUPERCATEGORY")]

        category = [(item["id"], item["name"])
                    for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/CATEGORY")]

        return supercategory + category

    def get_specific_category_name(self, category_id):
        res = self._get_request(f"{self.catalogue_base_url}/vocabulary/{category_id}")
        if res is not None:
            return res["name"]
        else:
            raise IdNotExists(f"Category id {category_id} does not exist!")

    def get_vocabulary(self, vocabulary_type: str) -> list:
        try:
            response = self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/{vocabulary_type}")
        except APIResponseError:
            logger.warning(f"Could not fetch vocabulary '{vocabulary_type}' from API.")
            return []
        return [item["id"] for item in (response or [])]

    def get_vocabulary_with_names(self, vocabulary_type: str) -> list:
        try:
            response = self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/{vocabulary_type}")
        except APIResponseError:
            logger.warning(f"Could not fetch vocabulary '{vocabulary_type}' from API.")
            return []
        return [(item["id"], item["name"]) for item in (response or [])]

    def get_providers_names(self):
        # TODO currently we have hardcoded 8000 as maximum quantity
        return [item["name"] for item in
                self._get_request(f"{self.catalogue_base_url}/public/provider/"
                                  f"all?quantity=8000")["results"]]

    def _remove_general_attributes_from_services(self, services):
        attributes = ['scientific_domains', 'categories']

        def remove_fields_containing_other(attribute_values):
            return [attr for attr in attribute_values if '-other' not in attr]

        for attribute in attributes:
            if attribute in services:
                services[attribute] = services[attribute].apply(remove_fields_containing_other)

    def _remove_general_attributes_from_single_service(self, service):
        attributes = ['scientific_domains', 'categories']

        for attribute in attributes:
            if attribute in service:
                service[attribute] = [attr for attr in service[attribute] if '-other' not in attr]

    RESOURCE_TYPE_ENDPOINTS = {
        "service": "/service/all",
        "training_resource": "/trainingResource/all",
        "datasource": "/datasource/all",
        "organisation": "/public/provider/all",
        "adapter": "/adapter/all",
        "interoperability_record": "/interoperabilityRecord/all",
        "deployable_application": "/deployableApplication/all",
    }

    RESOURCE_BY_ID_ENDPOINTS = {
        "service": "/resource/{id}",
        "training_resource": "/trainingResource/{id}",
        "datasource": "/datasource/{id}",
        "organisation": "/public/provider/{id}",
        "adapter": "/adapter/{id}",
        "interoperability_record": "/interoperabilityRecord/{id}",
        "deployable_application": "/deployableApplication/{id}",
    }

    def _reformat_resource(self, resource: dict, resource_type: str) -> dict:
        if resource_type == "service":
            return self._reformat_service(resource)

        r = dict(resource)

        if resource_type == "training_resource":
            r["target_groups"] = r.pop("targetGroups", []) or []
            r["expertise_level"] = [r.pop("expertiseLevel")] if r.get("expertiseLevel") else []
            r["learning_resource_types"] = r.pop("learningResourceTypes", []) or []
            r["content_resource_types"] = r.pop("contentResourceTypes", []) or []
            r["qualifications"] = r.pop("qualifications", []) or []
            r["access_rights"] = [r.pop("accessRights")] if r.get("accessRights") else []

        elif resource_type == "datasource":
            self._normalize_domain_category_fields(r)
            r["datasource_classification"] = [r.pop("datasourceClassification")] if r.get("datasourceClassification") else []
            r["research_product_types"] = r.pop("researchProductTypes", []) or []
            r["jurisdiction"] = [r.pop("jurisdiction")] if r.get("jurisdiction") else []
            r["trl"] = [r.pop("trl")] if r.get("trl") else []
            r["order_type"] = [r.pop("orderType")] if r.get("orderType") else []

        elif resource_type == "organisation":
            r["country"] = [r.pop("country")] if r.get("country") else []
            r["legal_status"] = [r.pop("legalStatus")] if r.get("legalStatus") else []

        elif resource_type == "adapter":
            r["programming_language"] = [r.pop("programmingLanguage")] if r.get("programmingLanguage") else []
            r["package"] = r.pop("package", []) or []

        elif resource_type == "deployable_application":
            self._normalize_domain_category_fields(r)

        return r

    def get_resources_of_type(self, resource_type: str, attributes: list):
        endpoint = self.RESOURCE_TYPE_ENDPOINTS[resource_type]
        response = self._get_request(f"{self.catalogue_base_url}{endpoint}?quantity=8000")

        try:
            resources = [self._reformat_resource(r, resource_type) for r in response["results"]]
        except KeyError as e:
            raise APIResponseFormatException(f"{e} does not exist in the response's fields")

        cols = list(set(["service_id"] + attributes))
        if len(resources):
            df = pd.DataFrame(resources)
            df.rename(columns={"id": "service_id"}, inplace=True)
            df = df.reindex(columns=cols, fill_value="")
        else:
            df = pd.DataFrame(columns=cols)

        return df

    def get_resources_by_ids(self, resource_type: str, ids: list, attributes: list = None,
                             remove_generic_attributes: bool = False):
        if attributes is None:
            attributes = []

        endpoint_template = self.RESOURCE_BY_ID_ENDPOINTS[resource_type]
        resources = []
        for rid in ids:
            r = self._get_request(f"{self.catalogue_base_url}{endpoint_template.format(id=rid)}")
            if r is None:
                raise IdNotExists(f"Resource id {rid} does not exist!")
            resources.append(self._reformat_resource(r, resource_type))

        if len(resources):
            df = pd.DataFrame(resources)
            df.rename(columns={"id": "service_id"}, inplace=True)
            df = df[["service_id"] + attributes]
        else:
            df = pd.DataFrame(columns=["service_id"] + attributes)

        if remove_generic_attributes:
            self._remove_general_attributes_from_services(df)

        return df

    def is_valid_service(self, service_id):
        return self.get_service(service_id) is not None

    def get_catalog_id_mappings(self):
        mappings_df = self.get_services()
        mappings_df.rename(columns={'service_id': 'catalog_id'}, inplace=True)
        mappings_df['id'] = mappings_df.loc[:, 'catalog_id']
        return mappings_df

    def get_non_published_services(self):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def get_projects(self):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def get_project(self, project_id):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def get_project_services(self, project_id):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def get_users(self, **kwargs):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def get_user_services(self, user_id):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def is_valid_project(self, project_id):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")

    def is_valid_user(self, user_id):
        raise RegistryMethodNotImplemented(f"Method not implemented in {self.__class__.__name__}")
