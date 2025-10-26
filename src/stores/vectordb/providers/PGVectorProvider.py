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








        


     


 
         






