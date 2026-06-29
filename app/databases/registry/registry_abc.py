from abc import ABC, abstractmethod


class Registry(ABC):
    @abstractmethod
    def get_services_by_ids(self, ids, **kwargs):
        pass

    @abstractmethod
    def get_services(self, **kwargs):
        pass

    @abstractmethod
    def get_non_published_services(self):
        pass

    @abstractmethod
    def get_service(self, service_id, **kwargs):
        pass

    @abstractmethod
    def get_projects(self):
        pass

    @abstractmethod
    def get_project(self, project_id):
        pass

    @abstractmethod
    def get_project_services(self, project_id):
        pass

    @abstractmethod
    def get_users(self, **kwargs):
        pass

    @abstractmethod
    def get_user_services(self, user_id):
        pass

    @abstractmethod
    def get_scientific_domains(self):
        pass

    @abstractmethod
    def get_scientific_subdomains_id_and_name(self):
        pass

    @abstractmethod
    def get_scientific_upper_domains_id_and_name(self):
        pass

    @abstractmethod
    def get_specific_scientific_domain_name(self, scientific_domain_id):
        pass

    @abstractmethod
    def get_categories(self):
        pass

    @abstractmethod
    def get_subcategories_id_and_name(self):
        pass

    @abstractmethod
    def get_upper_categories_id_and_name(self):
        pass

    @abstractmethod
    def get_specific_category_name(self, category_id):
        pass

    @abstractmethod
    def get_providers_names(self):
        pass

    @abstractmethod
    def _remove_general_attributes_from_services(self, services):
        pass

    @abstractmethod
    def _remove_general_attributes_from_single_service(self, service):
        pass

    @abstractmethod
    def is_valid_service(self, service_id):
        pass

    @abstractmethod
    def is_valid_project(self, project_id):
        pass

    @abstractmethod
    def is_valid_user(self, user_id):
        pass

    @abstractmethod
    def get_vocabulary(self, vocabulary_type: str) -> list:
        pass

    @abstractmethod
    def get_vocabulary_with_names(self, vocabulary_type: str) -> list:
        pass

    @abstractmethod
    def get_resources_of_type(self, resource_type: str, attributes: list):
        pass

    @abstractmethod
    def get_resources_by_ids(self, resource_type: str, ids: list, attributes: list = None,
                             remove_generic_attributes: bool = False):
        pass

    @abstractmethod
    def get_catalog_id_mappings(self):
        pass
