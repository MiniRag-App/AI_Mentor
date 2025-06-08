from pydantic import BaseModel,Filed,field_validator
from typing import Optional
from bson.objectid import ObjectId

class Project(BaseModel):
    _id:Optional[ObjectId]
    project_id:str =Filed(...,min_length=1)
    
    @field_validator(project_id)
    def validate_project_id(cls,value):
         if not value.isalnum():
              raise ValueError("project id must be alpha numeric")
         return value
    
    class Config:
         arbitrary_types_allowed=True