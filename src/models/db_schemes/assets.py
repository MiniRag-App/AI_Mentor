from pydantic import BaseModel,Field
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime


class Assets(BaseModel):
    id:Optional[ObjectId]=Field(None,alias='_id')
    asset_project_id =ObjectId
    asset_type:str =Field(...,min_length=1)
    asset_name:str =Field(...,min_length=1)
    asset_size:int =Field(gt=0,default=None)
    asset_pushed_at:datetime =Field(default=datetime.utcnnow)
    asset_config:dict =Field(default=None)


    class Config:
        arbitrary_types_allowed=True


    # create index for asset_project_id and asset_project_name
    @classmethod
    def get_chunk_indexs(cls):
          return [
               {
               'key':[
                    ('asset_project_id',1) # 1 ,index ascending order
               ],
               'name':'asset_project_id_1',
               'unique':False
               },
               {
               'key':[
                    ('asset_project_id',1) ,# 1 ,index ascending order
                    ('asset_name',1)
               ],
               'name':'asset_project_name_id_1',
               'unique':True
               }
          ]


