from .db_schemes import Assets
from .BaseDataModel import BaseDataModel
from .enumrations import DataBaseEnum
from .db_schemes import Assets
from bson.objectid import ObjectId

class AssetModel(BaseDataModel):
    def __init__(self,db_client:object):
        self.db_client =db_client
        self.collection =self.db_client[DataBaseEnum.COLLECTION_ASSSET_NAME.value]

    @classmethod
    async def create_instance(cls,db_client:object):
            instance=cls(db_client)
            await instance.init_collection()
            return instance


     # create index in collection
    async def init_collection(self):
            all_collections =await self.db_client.list_collection_names()
            if DataBaseEnum.COLLECTION_ASSSET_NAME.value not in all_collections:
                  # intialize refernce for db collection
                  self.collection =self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
                  indexes =Assets.get_indexs()
                  
                  for index in indexes:
                        await self.collection.create_index(
                              index['key'],
                              name =index['name'],
                              unique =index['unique']
                        )  
    async def create_asset(self,asset:Assets):
          result =await self.collection.insert_one(asset.model_dump(by_alias=True,exclude_unset=True))
          asset.id =result.inserted_id

          return asset
    
    async def get_all_project_assets(self,asset_project_id:str):
          return await self.collection.find({
                'asset_project_id':ObjectId(asset_project_id) if isinstance(asset_project_id,str) else asset_project_id
          }).to_list(length=None)
          