from pydantic import BaseModel,Field
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    id:Optional[ObjectId]=Field(None,alias='_id')
     
    chunk_text:str=Field(...,min_length=1)
    chunk_metadata:dict
    chunk_order:int =Field(...,gt=0)
    chunk_project_id :ObjectId


    class Config:
        arbitrary_types_allowed=True

    
    # create index for chunk_project id
    @classmethod
    def get_chunk_indexs(cls):
          return [
               {
               'key':[
                    ('chunk_project_id',1) # 1 ,index ascending order
               ],
               'name':'chunk_project_id_1',
               'unique':False
               },
          ]
