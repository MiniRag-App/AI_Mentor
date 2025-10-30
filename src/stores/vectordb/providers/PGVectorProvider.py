from ..VectorDBInterface import VecotrDBInterface
from ..VectorDBEnum import PGvectorDistanceMethodsEnum,PGvectorTableSchemaEnums,PGVectorIndexTypeEnum,DistanceMethodEnum

from models import RetrievedDocument
import logging
from typing import List
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VecotrDBInterface):

    def __init__(self, db_client , distance_methods :str = None ,default_vector_size :int =786 ,index_threshold :int =100):

        self.db_client =db_client 
        self.default_vector_size =default_vector_size
        self.pgvector_prefix =PGvectorTableSchemaEnums._PREFIX.value # to define each table as pgvector table
        self.index_threshold = index_threshold 

        if distance_methods == DistanceMethodEnum.COSINE.value:
            distance_methods =PGvectorDistanceMethodsEnum.COSINE.value
        if distance_methods == DistanceMethodEnum.DOT.value:
            distance_methods =PGvectorDistanceMethodsEnum.DOT.value

        self.logger =logging.getLogger('uvicorn')

        self.default_index_name =lambda collection_name: f"{collection_name}_vector_idx"


    async def connect(self):
        ''' try to connect to pgvector extextion and 
            if not extists it will create one 
        '''
        async with self.db_client() as session :
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
            await session.commit()

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name:str) -> bool:
          record =None

          async with self.db_client() as session:
                async with session.begin():
                    list_tables =sql_text('select * from pg_tables where tablename = :collection_name')
                    results =await session.execute(list_tables,{'collection_name':collection_name})
                    record =results.scalar_one_or_none()

                return record
          
    async def list_all_collections(self):
         
         records =[]

         async with self.db_client() as session:
                async with session.begin():
                    list_tables =sql_text('select table_name from pg_tables ' 
                                        f'where table_name like {self.pgvector_prefix}'
                                        )
                    results =await session.execute(list_tables)
                    records =results.scalars.all()

                return records
   
    async def get_collection_info(self, collection_name:str):
         
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql =sql_text(
                    'select schemaname, tablename, tableowner, tablespace, hasindexes ' 
                    'from pg_tables '
                    f'where table_name = {collection_name}'
                    )
                
                table_count_records =sql_text(f'select count(*) from {collection_name}')

                table_info =await session.execute(table_info_sql)
                table_num_records =await session.execute(table_count_records)


                table_data =table_info.fetchone()

                if table_data is None:
                    return None
                
                return  {
                    "table_info": {
                        "schemaname": table_data[0],
                        "tablename": table_data[1],
                        "tableowner": table_data[2],
                        "tablespace": table_data[3],
                        "hasindexes": table_data[4],
                    },
                    "record_count": table_num_records.scalar_one(),
                }
            
    async def delete_collection(self,collection_name):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f'Deleting collection {collection_name}')

                query =sql_text(
                   f' drop table if exists {collection_name}'
                )
                
                await session.execute(query)
                await session.commit()
        return True
    
    async def create_collection(self,collection_name:str,embedding_size:int, do_reset:bool=False):

        if do_reset:
            _ =await self.delete_collection(collection_name=collection_name)
        
        is_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_exist:
            self.logger.info('creating collection {collection_name}')

            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f"CREATE TABLE {collection_name} ("
                        f"{PGvectorTableSchemaEnums.ID.value} BIGSERIAL PRIMARY KEY, "
                        f"{PGvectorTableSchemaEnums.TEXT.value} TEXT, "
                        f"{PGvectorTableSchemaEnums.CHUNK_ID.value} INTEGER, "
                        f"{PGvectorTableSchemaEnums.VECTOR.value} vector({embedding_size}), "
                        f"{PGvectorTableSchemaEnums.METADATA.value} JSONB DEFAULT '{{}}'"
                        ")"
                    )

                    await session.execute(create_sql)
                    await session.commit()

                return True
            
            return False
        
    async def is_index_existed(self,collection_name) ->bool :

        index_name = self.default_index_name(collection_name)

        async with self.db_client() as session:
            async with session.begin():
                check_sql =sql_text(
                                    'select 1 '
                                    'from pg_indexes '
                                    f'where collection_name ={ collection_name} and index_name = {index_name}' 
                                )
               
                result =await session.execute(check_sql)

                return bool(result.scalar_one_or_none())

    async def create_vector_index(self,collection_name:str, index_type :str =PGVectorIndexTypeEnum.HNSW.value):

        # check if index existed  
        is_index_existed = self.is_index_existed(collection_name=collection_name)

        if  is_index_existed:
            self.logger.info("index is already existed")
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_sql =sql_text(' select count(*) as rows_count from {collection_name}')

                result =await session.execute(count_sql )
                count_rows  =result.scalar_one()

                if count_rows < self.index_threshold:
                    self.logger.info(f'number of records inside {collection_name} is less than index threshold {self.index_threshold}')
                    return False
                
                self.logger.info(f'START: creating vectore index for collection {collection_name}')
                
                index_name =self.default_index_name(collection_name)

                create_idx_sql =sql_text(f'create index  {index_name} on {collection_name} '
                                         f'using {index_type} {PGvectorTableSchemaEnums.VECTOR.value} {self.distance_methods}'
                                        )
                
                await session.execute(create_idx_sql)


                self.logger.info(f'END: created vectore index for collection {collection_name}')

                   
    async def reset_vector_index(self,collection_name:str,index_type:str =PGVectorIndexTypeEnum.HNSW.value)->bool:
        ''' we will drop old index and create new one '''

        # check if index existed  
        is_index_existed = await self.is_index_existed(collection_name=collection_name)

        if not is_index_existed:
            self.logger.info(f"index is not existed in {collection_name}")
            await self.create_vector_index(collection_name,index_type)
            return True
        
        index_name =self.default_index_name(collection_name)

        async with self.db_client() as session:
            async with session.begin():
                reset_idx_sql =sql_text(
                                         f'drop index if exist {index_name}'
                )
                
                await session.execute(reset_idx_sql)

        
        return await self.create_vector_index(collection_name,index_type)



    async def insert_one(self,collection_name:str,text:str ,vector:list,
                   metadata:dict=None ,record_id:str =None):
        
        '''record_id = chunk_id'''

        # check if collection is existed or not 
        is_collection_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_collection_exist:
            self.logger.error(f"Can not insert new record to not existed collection {collection_name}")
            return False
        
        if not record_id:
            self.logger.error(f"can not insert new record without chunk_id in : {collection_name}")
            return False
        
        async with self.db_client as session:
            async with session.begin():

                metadata_json = json.dumps(metadata,ensure_ascii=False) if metadata is not None else '{}'
                vector ="["+','.join([ str(v) for v in vector])+"]"

                sql_query =sql_text(f'insert into {collection_name}'
                                    f'({PGvectorTableSchemaEnums.TEXT.value},{PGvectorTableSchemaEnums.CHUNK_ID.value},'
                                    f'{PGvectorTableSchemaEnums.VECTOR.value},'
                                    f'{PGvectorTableSchemaEnums.METADATA.value},'
                                    f'values ({text}, {record_id}, {vector}, {metadata_json})')
                
                await session.execute(sql_query)
              
                await session.commit()
                await self.create_vector_index(collection_name=collection_name)

        return True

    async def insert_many(self,collection_name:str, texts:list ,record_id:list,vectors:list,
                        metadata:list=None ,batch_size:int =50):
        
           # check if collection is existed or not 
        is_collection_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_collection_exist:
            self.logger.error(f"Can not insert new record to not existed collection {collection_name}")
            return False
        

        # validate if len vectors == len text 
        if len(vectors) != len(texts):
            self.logger.error(f'len vectors not equal len texts this is not valid to insert into {collection_name}')
            return False
        
        if len(metadata) == 0 or not metadata:
            metadata =[None] * len(texts)

        if len(record_id) == 0:
            print('record id is None')
        async with self.db_client() as session:
            async with session.begin():

                for i in range(0,len(texts),batch_size):

                    batch_text =texts[i:i+batch_size]
                    batch_vectors =vectors[i:i+batch_size]
                    batch_metadata =metadata[i:i+batch_size]
                    batch_record_id = record_id[i:i+batch_size]
                    

                    values =[]
                    for _text ,_vector ,_metadata,_record_id in zip(batch_text,batch_vectors,batch_metadata,batch_record_id):
                        metadata_json =json.dumps(_metadata,ensure_ascii=False) if metadata is not None else '{}'
                        values.append({
                        'text': _text,
                        'vector': "["+','.join([ str(v) for v in _vector])+"]",
                        'metadata': metadata_json,
                        'record_id' : _record_id 
            
                        })
                    

                        sql_query =sql_text(f'insert into {collection_name}'
                                            f'({PGvectorTableSchemaEnums.TEXT.value},{PGvectorTableSchemaEnums.CHUNK_ID.value},'
                                            f'{PGvectorTableSchemaEnums.VECTOR.value},'
                                            f'{PGvectorTableSchemaEnums.METADATA.value})'
                                            'values (:text, :record_id, :vector, :metadata)')
                            
                        await session.execute(sql_query,values)
                        
        await self.create_vector_index(collection_name=collection_name)   
        return True
    
    async def  search_by_vector(self,collection_name:str ,vector:list ,limit :int) -> List [RetrievedDocument]:

        # check if collection is existed or not 
        is_collection_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_collection_exist:
            self.logger.error(f"Can not search for records in non existed collection {collection_name}")
            return False
        

        # convert vector into string 
        vector ="["+','.join([ str(v) for v in vector])+"]"

        # search on similar vectors by using cosine similarity : <=>

        async with self.db_client as session:
            async with session.begin():
                sql_query =sql_text(f'select {PGvectorTableSchemaEnums.TEXT.value} as text , '
                                    f'1- {PGvectorTableSchemaEnums.VECTOR.value} <=> :vector as score'
                                    f'from {collection_name}' 
                                    'order by score desc'
                                    f'limit {limit}'
                                    )
                
                result =await session.execute(sql_query,{'vector':vector})

                records =result.fetchall()

                return [
                    RetrievedDocument(
                        text = record.text,
                        score =record.score
                    )
                    for record in records 
                ]









        


     


 
         






