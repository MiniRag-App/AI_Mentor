from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk,Project
from .enumrations import DataBaseEnum
from fastapi.responses import JSONResponse
from fastapi import status
from models import ResponseSignals
from sqlalchemy.future import select
from sqlalchemy import func ,delete


class ChunkDataModel(BaseDataModel):
    def __init__(self,db_client):
        super().__init__(db_client=db_client)
    
    
    @classmethod
    async def create_instance(cls,db_client:object):
        instance =cls(db_client)
        return instance
    
    async def create_chunk(self,chunk:DataChunk):
         async with self.db_client() as session:
                  async with session.begin():
                        session.add(chunk)

                  await session.commit()
                  await session.refresh(chunk)
    

    async def get_chunk(self,chunk_id:int):
       async with self.db_client() as session:
                  async with session.begin():
                        query = select(DataChunk).where(DataChunk.chunk_id ==chunk_id)
                        chunk =await session.execute(query).scalar_one()

    async def insert_many_chunks(self,chunks:list,batch_size:int=96):
        async with self.db_client() as session:
            async with session.begin():

                for i in range(0,len(chunks),batch_size):
                    batch =chunks[i:i+batch_size]
                    session.add_all(batch)
            await session.commit()

            return len(chunks)
   
    async def delete_chunk_by_project_id(self,project_id:int):
         
        async with self.db_client() as session:
            async with session.begin():
                  query =delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                  result = await session.execute(query)
            await session.commit()

        return result.rowcount

    async def get_project_chunks(self,project_id:int, page_no :int=1 ,page_size:int =96):
            async with self.db_client() as session:
                query =select(DataChunk).where(DataChunk.chunk_project_id == project_id).offset((page_no -1) * page_size).limit(page_size)
                result=await session.execute(query)
                records =result.scalars().all()

            return records
    
    async def get_total_chunks_count(self ,project_id :int):
        total_count =0
        async with self.db_client() as session:
                query =select(func.count(DataChunk.chunk_id)).where(DataChunk.chunk_project_id == project_id)
                result=await session.execute(query)
                total_count =result.scalar()

        return total_count
         

