from .providers import QdrantDBProvider,PGVectorProvider
from .VectorDBEnum import VectorDBEnums
from controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker

class VectorDBProviderFactory:
    def __init__(self,config,db_client :sessionmaker =None):
        self.config= config
        self.BaseController =BaseController()
        self.db_client =db_client


    def create(self,Provider:str):
        qdrant_db_client =self.BaseController.get_vectoredb_path(db_name =self.config.VECTORE_DB_PATH)

        if Provider == VectorDBEnums.QDRANT.value:
            return QdrantDBProvider(
                db_client =qdrant_db_client,
                distance_methods =self.config.VECTORE_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRETHORD
            )
        if Provider == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client=self.db_client,
                distance_method =self.config.VECTORE_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRETHORD
            )

        return None