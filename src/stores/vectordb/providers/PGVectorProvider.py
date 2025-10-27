from ..VectorDBInterface import VecotrDBInterface
from ..VectorDBEnum import PGvectorDistanceMethodsEnum,PGvectorTableSchemaEnums,PGVectorIndexTypeEnum

from models import RetrievedDocument
import logging
from typing import List
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VecotrDBInterface):

    def __init__(self, db_client , distance_methods :str = None ,default_vector_size :int =786):

        self.db_client =db_client 
        self.distance_methods =distance_methods
        self.default_vector_size =default_vector_size
        self.pgvector_prefix =PGvectorTableSchemaEnums._PREFIX.value # to define each table as pgvector table 

        self.logger =logging.getLogger('uvicorn')

        self.default_index_name =lambda collection_name: f"{collection_name}_vector_idx"


    async def connect(self):
        ''' try to connect to pgvector extextion and 
            if not extists it will create one 
        '''
        async with self.db_client() as session :
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENTION IF NOT EXIST vector"
                ))
            await session.commit()

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name:str) -> bool:
          record =None

          async with self.db_client() as session:
                async with session.begin():
                    list_tables =sql_text('''
                                            select * from pg_tables 
                                            where table_name = : collection_name
                                            ''')
                    results =session.execute(list_tables,{'collection_name':collection_name})
                    record =results.scalar_one_or_none()

                return record
          
    async def list_all_collections(self):
         
         records =[]

         async with self.db_client() as session:
                async with session.begin():
                    list_tables =sql_text('''
                                            select table_name from pg_tables 
                                            where table_name like :prefix
                                            ''')
                    results =session.execute(list_tables,{'prefix':self.pgvector_prefix})
                    records =results.scalars.all()

                return records
   
    async def get_collection_info(self, collection_name:str):
         
        async with self.db_client as session:
            async with session.begin():
                table_info_sql =sql_text('''
                    select schemaname, tablename, tableowner, tablespace, hasindexes 
                    from pg_tables
                    where table_name = : collection_name
                    
                  ''')
                
                table_count_records =sql_text('''select count(*) from : collection_name''')

                table_info =session.execute(table_info_sql,{'collection_name':collection_name})
                table_num_records =session.execute(table_count_records,{'collection_name':collection_name})


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
        async with self.db_client as session:
            async with session.begin():
                self.logger.info('Deleting collection {collection_name}')

                query =sql_text('''
                    drop table if exists : collection_name
                  ''')
                
                await session.execute(query,{'collection_name':collection_name})
                await session.commit()
        return True
    
    async def create_collection(self,collection_name:str,embedding_size:int, do_reset:bool=False):

        if do_reset:
            _ =self.delete_collection(collection_name=collection_name)
        
        is_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_exist:
            self.logger.info('creating collection {collection_name}')

            async with self.db_client as session:
                async with session.begin():
                    query =sql_text(
                             f'create table {collection_name} ('
                             f'{PGvectorTableSchemaEnums.ID.value} bigserial primary key,',
                             f'{PGvectorTableSchemaEnums.TEXT.value} text,'
                             f"{PGvectorTableSchemaEnums.CHUNK_ID.value} intger ,"
                             f'{PGvectorTableSchemaEnums.VECTOR.value} vectore({embedding_size}),'
                             f'{PGvectorTableSchemaEnums.METADATA.value} jsonb default \'{{}}\','
                             f'foreing key {PGvectorTableSchemaEnums.CHUNK_ID.value} references chunks(chunk_id)'
                             ')'         
                    )

                    await session.execute(query)
                    await session.commit()

                return True
            
            return False
        
    async def is_index_existed(self,collection_name) ->bool :

        index_name = self.default_index_name(collection_name)

        async with self.db_client as session:
            async with session.begin():
                check_sql =sql_text('''
                                    select 1
                                    from pg_indexes
                                    where collection_name = : collection_name and index_name = :index_name 
                                    ''')
               
                result =await session.execute(check_sql,{
                    'collection_name' :collection_name,
                    'index_name': index_name
                })

                return bool(result.scalar_one_or_none())



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
                sql_query =sql_text(f'insert into {collection_name}'
                                    f'({PGvectorTableSchemaEnums.TEXT.value},{PGvectorTableSchemaEnums.CHUNK_ID.value},'
                                    f'{PGvectorTableSchemaEnums.VECTOR.value},'
                                    f'{PGvectorTableSchemaEnums.METADATA.value},'
                                    'values (:text, :record_id, :vector, :metadata)')
                
                await session.execute(sql_query,{
                    'text': text,
                    'vector': "["+','.join([ str(v) for v in vector])+"]",
                    'metadata': metadata_json,
                    'record_id' : record_id 
                })
              
                await session.commit()

        return True

    async def insert_many(self,collection_name:str, texts:list ,vecotrs:list,
                    metadata:list=None ,record_id:list=None,
                    batch_size:int =50):
        
           # check if collection is existed or not 
        is_collection_exist =await self.is_collection_existed(collection_name=collection_name)

        if not is_collection_exist:
            self.logger.error(f"Can not insert new record to not existed collection {collection_name}")
            return False
        

        # validate if len vectors == len text 
        if len(vecotrs) != len(texts):
            self.logger.error(f'len vectors not equal len texts this is not valid to insert into {collection_name}')
            return False
        
        if len(metadata) == 0 or not metadata:
            metadata =[None] * len(texts)

        
        async with self.db_client as session:
            async with session.begin():

                for i in range(0,len(texts),batch_size):

                    batch_text =texts[i:i+batch_size]
                    batch_vectors =vecotrs[i:i+batch_size]
                    batch_metadata =metadata[i:i+batch_size]
                    batch_record_id = record_id[i+i+batch_size]
                    

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
                                            f'{PGvectorTableSchemaEnums.METADATA.value},'
                                            'values (:text, :record_id, :vector, :metadata)')
                            
                        await session.execute(sql_query,values)
                    
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









        


     


 
         






