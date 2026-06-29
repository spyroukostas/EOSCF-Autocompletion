from app.recommenders.algorithms.similar_services_retrieval.preprocessor.embeddings import \
    text_embeddings
from app.recommenders.autocompletion.tag_suggestions.preprocessor import tag_structures
from app.recommenders.update.update import Update
from app.settings import APP_SETTINGS


class FieldSuggestionUpdate(Update):
    def initialize(self):
        for resource_type in APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"]:
            text_embeddings.initialize_text_embeddings(resource_type)
        tag_structures.TagStructuresManager().initialize_tag_structures()

    def update(self):
        for resource_type in APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"]:
            text_embeddings.create_text_embeddings(resource_type)
        tag_structures.TagStructuresManager().create_tags_structures()

    def update_for_new_service(self, service_id: int):
        text_embeddings.update_text_embedding_for_one_service(new_service_id=service_id)

    def revert(self):
        for resource_type in APP_SETTINGS["BACKEND"]["AUTO_COMPLETION"]["RESOURCE_TYPES"]:
            text_embeddings.delete_text_embeddings(resource_type)
        tag_structures.TagStructuresManager().delete_tag_structures()
