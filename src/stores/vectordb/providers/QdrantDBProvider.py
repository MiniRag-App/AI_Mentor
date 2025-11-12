from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VecotrDBInterface
from ..VectorDBEnum import DistanceMethodEnums
from models import RetrievedDocument
import logging
from typing import List
import time
import os
import shutil
# from models.db_schemes import RetrievedDocument

class QdrantDBProvider(VecotrDBInterface):

    def __init__(self,db_client: str, distance_methods :str = None ,default_vector_size :int =786 ,index_threshold :int =100):

        self.client = None
        self.db_client =db_client
        self.distance_method = distance_methods
        self.default_vector_size =default_vector_size
        self.index_threshold =index_threshold

        if distance_methods == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_methods == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger('uvicorn')

    async def connect(self):
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        if self.client is None :
            print("qdrant client is None")
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    async def delete_collection(self, collection_name: str):
        if await self.is_collection_existed(collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)



    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
       
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
            time.sleep(0.2)  # Give Qdrant time to remove the collection
            

            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            print(f"collection created-------{collection_name}--------------")

        if not await self.is_collection_existed(collection_name=collection_name):  # Always (re)create the collection after deletion
            self.logger.info(f'creating new qdran collection {collection_name}')
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            print(f"collection created-------{collection_name}--------------")
        return True
    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=[record_id],
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True
    
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            # Use UUIDs for unique IDs to avoid overwriting points
            import uuid
            record_ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )

                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True
        
    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):

        results = self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

        if not results or len(results) == 0:
            return None
        

        return [
            RetrievedDocument(**{
                "score":doc.score,
                "text":doc.payload['text']
            })

            for doc in results
        ]
        # return results