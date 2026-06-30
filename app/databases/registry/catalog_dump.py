import pandas as pd
import requests
from app.databases.registry.registry_abc import Registry
from app.databases.utils.mongo_connector import (MongoDbConnector,
                                                 form_mongo_url)
from app.exceptions import (APIResponseFormatException, IdNotExists,
                            RegistryMethodNotImplemented)
from app.settings import APP_SETTINGS
from pymongo import MongoClient


class CatalogueDump(Registry):
    def is_valid_project(self, project_id):
        pass

    def is_valid_user(self, user_id):
        pass

    def __init__(self):
        super().__init__()
        self.catalogue_base_url = APP_SETTINGS["BACKEND"]["CATALOGUE_API"]["BASE_URL"]
        self.mongo_connector = MongoDbConnector(
            uri=form_mongo_url(
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_USERNAME'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_PASSWORD'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_HOST'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_PORT']
            ),
            db_name="catalog_dump"
        )
        self.mongo_connector.connect()

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

        return service

    def get_services_by_ids(self, ids, attributes=None, conditions=None, remove_generic_attributes=False):
        return self.get_services(attributes=attributes, conditions={'id': {'$in': ids}},
                                 remove_generic_attributes=remove_generic_attributes)

    def get_services(self, attributes=None, conditions=None, reformat=True, remove_generic_attributes=True):
        """
        Args:
            attributes: list, the requested attributes for the services
            reformat: boolean, when true services attributes are reformated to be independent of the selected registry
        """
        if attributes is None:
            attributes = []

        services = list(self.mongo_connector.get_db()["service"].find(conditions))

        if reformat:
            services = [self._reformat_service(service) for service in services]

        if len(services):
            services_df = pd.DataFrame(services)
            services_df.rename(columns={'id': 'service_id'}, inplace=True)
            services_df = services_df[list(set(["service_id"] + attributes))]
        else:  # If there are no services
            services_df = pd.DataFrame(columns=list(set(["service_id"] + attributes)))

        if remove_generic_attributes:
            self._remove_general_attributes_from_services(services_df)

        return services_df

    def get_service(self, service_id, reformat=True, remove_generic_attributes=True):
        service = self.mongo_connector.get_db()["service"].find_one({'id': service_id})
        if reformat and service is not None:
            service = self._reformat_service(service)
        if remove_generic_attributes:
            self._remove_general_attributes_from_single_service(service)
        return service

    def get_scientific_domains(self):
        return [domain["id"] for domain in self.mongo_connector.get_db()["scientific_domain"].find({}, {"id": 1})]

    def get_scientific_subdomains_id_and_name(self):
        return [(domain["id"], domain["name"])
                for domain in self.mongo_connector.get_db()["scientific_domain"].find({}, {"name": 1})]

    def get_scientific_upper_domains_id_and_name(self):
        return []

    def get_specific_scientific_domain_name(self, scientific_domain_id):
        res = self.mongo_connector.get_db()["scientific_domain"].find_one({"id": scientific_domain_id}, {"name": 1})
        if res is not None:
            return res["name"]
        else:
            raise IdNotExists(f"Scientific domain id {scientific_domain_id} does not exist!")

    def get_categories(self):
        return [domain["id"] for domain in self.mongo_connector.get_db()["category"].find({}, {"id": 1})]

    def get_subcategories_id_and_name(self):
        return [(domain["id"], domain["name"])
                for domain in self.mongo_connector.get_db()["category"].find({}, {"name": 1})]

    def get_upper_categories_id_and_name(self):
        return []

    def get_specific_category_name(self, category_id):
        res = self.mongo_connector.get_db()["category"].find_one({"id": category_id}, {"name": 1})
        if res is not None:
            return res["name"]
        else:
            raise IdNotExists(f"Category id {category_id} does not exist!")

    def get_vocabulary(self, vocabulary_type: str) -> list:
        return [item["id"] for item in
                _get_request(f"{self.catalogue_base_url}/vocabulary/byType/{vocabulary_type}")]

    def get_vocabulary_with_names(self, vocabulary_type: str) -> list:
        return [(item["id"], item["name"]) for item in
                _get_request(f"{self.catalogue_base_url}/vocabulary/byType/{vocabulary_type}")]

    def get_resources_of_type(self, resource_type: str, attributes: list):
        raise RegistryMethodNotImplemented(
            f"get_resources_of_type is not implemented in CatalogueDump")

    def get_resources_by_ids(self, resource_type: str, ids: list, attributes: list = None,
                             remove_generic_attributes: bool = False):
        raise RegistryMethodNotImplemented(
            f"get_resources_by_ids is not implemented in CatalogueDump")

    def get_providers_names(self):
        return [provider["name"] for provider in self.mongo_connector.get_db()["provider"].find(
            {}, {"name": 1})]

    def _remove_general_attributes_from_services(self, services):
        attributes = ['scientific_domains', 'categories']

        def remove_fields_containing_other(attribute_values):
            return [attr for attr in attribute_values if '-other-other' not in attr and 'generic' not in attr]

        for attribute in attributes:
            if attribute in services:
                services[attribute] = services[attribute].apply(remove_fields_containing_other)

    def _remove_general_attributes_from_single_service(self, service):
        attributes = ['scientific_domains', 'categories']

        for attribute in attributes:
            if attribute in service:
                service[attribute] = [attr for attr in service[attribute] if
                                      '-other-other' not in attr and 'generic' not in attr]

    def is_valid_service(self, service_id):
        return self.get_service(service_id) is not None

    def get_catalog_id_mappings(self):
        mappings_df = self.get_services()
        mappings_df.rename(columns={'service_id': 'catalog_id'}, inplace=True)
        mappings_df['id'] = mappings_df.loc[:, 'catalog_id']
        return mappings_df

    def get_non_published_services(self):
        """
        Since we are using this db for evaluation we do not (and should not) care about the published services
        """
        return []

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


def _get_request(request):
    response = requests.get(request)

    if response.status_code != 200:
        raise APIResponseFormatException("Problem with catalogue API!")

    return response.json()


def _populate_catalog_db(db, base_url):
    # Create a collection of services
    services_collection = db["service"]
    # Populate services collection
    # TODO currently we have hardcoded 800 as maximum quantity
    services_collection.insert_many(_get_request(f"{base_url}/service/all?quantity=10000")["results"])

    # Create a collection of categories
    category_collection = db["category"]
    # Populate the category collection
    category_collection.insert_many(_get_request(f"{base_url}/vocabulary/byType/SUBCATEGORY"))

    # Create a collection of scientific domains
    scientific_domain_collection = db["scientific_domain"]
    # Populate scientific domain collection
    scientific_domain_collection.insert_many(_get_request(f"{base_url}/vocabulary/byType/SCIENTIFIC_SUBDOMAIN"))

    # Create a collection of providers
    providers_collection = db["provider"]
    # Populate the target users collection
    # TODO currently we have hardcoded 400 as maximum quantity
    providers_collection.insert_many(_get_request(f"{base_url}/organisation/all?quantity=10000")["results"])


if __name__ == '__main__':
    # Create catalog_dump database
    conn = MongoClient(form_mongo_url(
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_USERNAME'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_PASSWORD'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_HOST'],
                APP_SETTINGS["CREDENTIALS"]['RS_MONGO_PORT']
            ))
    db = conn["catalog_dump"]
    # Populate the database
    base_url = APP_SETTINGS["BACKEND"]["CATALOGUE_API"]["BASE_URL"]
    _populate_catalog_db(db, base_url)
