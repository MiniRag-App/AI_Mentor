from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enumrations import DataBaseEnum


class ProjectDataModel(BaseDataModel):
      def __init__(self,db_client):
            super().__init__(db_client=db_client)
            self.collection =self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    
      async def create_project (self,project:Project):
            
            # insert new project into project collection 
            result =await self.collection.insert_one(project.model_dump())
            project._id =result.inserted_id

            return project
      
      async def get_project_or_create_one(self,project_id:str):
            
            record =await self.collection.find_one(
                  {
                        'project_id':project_id
                  }
            )

            if record is None:
                  # create new projct 
                  project =Project(project_id=project_id)
                  project =await self.create_project(project =project)