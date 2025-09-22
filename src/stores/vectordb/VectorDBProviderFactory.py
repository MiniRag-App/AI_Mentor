from .providers import QdrantDBProvider
from .VectorDBEnum import VectorDBEnum
from controllers.BaseController import BaseController

class VectorDBProviderFactory:
    def __init__(self,config):
        self.config= config
        self.BaseController =BaseController()


    def create(self,Provider:str):
        db_path =self.BaseController.get_vectoredb_path(db_name =self.config.VECTORE_DB_PATH)
        if Provider == VectorDBEnum.QDRANT.value:
            return QdrantDBProvider(
                db_path =db_path,
                distance_method =self.config.VECTORE_DB_DISTANCE_METHOD
            )

        return None