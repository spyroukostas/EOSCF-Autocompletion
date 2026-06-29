from typing import Optional

import pandas as pd
import requests
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

    def _reformat_service(self, service):
        scientific_subdomains, subcategories = self._get_leaves_of_metadata_hierarchies(service["scientificDomains"],
                                                                                        service["categories"])

        service["categories"] = subcategories
        service["scientific_domains"] = scientific_subdomains
        service["target_users"] = service.pop("targetUsers")

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

        if len(services):
            services_df = pd.DataFrame(services)
            services_df.rename(columns={'id': 'service_id'}, inplace=True)
            services_df = services_df[list(set(["service_id"] + attributes))]
        else:  # If there are no services
            services_df = pd.DataFrame(columns=list(set(["service_id"] + attributes)))

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

    def get_target_users(self):
        return [item["id"] for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/TARGET_USER")]

    def get_target_users_id_and_name(self):
        return [(item["id"], item["name"])
                for item in self._get_request(f"{self.catalogue_base_url}/vocabulary/byType/TARGET_USER")]

    def get_providers_names(self):
        # TODO currently we have hardcoded 8000 as maximum quantity
        return [item["name"] for item in
                self._get_request(f"{self.catalogue_base_url}/public/provider/"
                                  f"all?quantity=8000")["results"]]

    def _remove_general_attributes_from_services(self, services):
        attributes = ['scientific_domains', 'categories', 'target_users']

        def remove_fields_containing_other(attribute_values):
            return [attr for attr in attribute_values if '-other' not in attr]

        for attribute in attributes:
            if attribute in services:
                services[attribute] = services[attribute].apply(remove_fields_containing_other)

    def _remove_general_attributes_from_single_service(self, service):
        attributes = ['scientific_domains', 'categories', 'target_users']

        for attribute in attributes:
            if attribute in service:
                service[attribute] = [attr for attr in service[attribute] if '-other' not in attr]

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
