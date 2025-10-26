from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignals
from .ProjectController import ProjectController
import re
import os 


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale =1048576  # to convert MB to Byte
   
    def validate_uploaded_file(self,file:UploadFile):
          if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
               return False,ResponseSignals.FILE_TYPE_NOT_SUPPORTED.value
          
          if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
               return False,ResponseSignals.FILE_SIZE_EXEEDED.value
          
          return True,ResponseSignals.FILE_UPLOADED_SUCCESS.value
    
    def generate_unique_file_path(self,original_file_name:str,project_id:int):
         random_key =self.generate_random_string()
         project_path =ProjectController().get_project_path(project_id=project_id)

         cleaned_file_name =self.get_clean_file_name(orignal_file_name=original_file_name)

         new_file_path =os.path.join(
              project_path,
              random_key+"_"+cleaned_file_name
         )

         while os.path.exists(new_file_path):
              random_key =self.generate_random_string()
              new_file_path =os.path.join(
              project_path,
              random_key+"_"+cleaned_file_name
          )

         return  new_file_path ,random_key+"_"+cleaned_file_name

    def get_clean_file_name(self,orignal_file_name:str):
         
         # remove any special character except _ or .
         cleaned_name =re.sub(r'[^\w.]','',orignal_file_name.strip())
         cleaned_name =cleaned_name.replace(' ','_')

         return cleaned_name

