from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
from models import ProcessingEnum
import logging
from models.enumrations.QueryEnum import QueryEnum

from langchain_community.document_loaders import PyMuPDFLoader,TextLoader
from controllers.TextSpliterController import TextSpliterController

logger =logging.getLogger('uvicorn.error')

class ProcessController(BaseController):
    def __init__(self,project_id:int):
        super().__init__()
        self.project_id =project_id
        self.project_path =ProjectController().get_project_path(project_id=project_id)



    
    def get_file_extenstion(self,file_id:str):
        extention =os.path.splitext(file_id)[-1]
        return extention
    
    def get_file_loader(self,file_id:str):
        file_ext =self.get_file_extenstion(file_id=file_id)
        file_path =os.path.join(
            self.project_path,
            file_id
        )
        
        # check if file exists or not 
        if not os.path.exists(file_path):
            return None
        

        if file_ext ==ProcessingEnum.TXT.value:
            return TextLoader(file_path=file_path,encoding='utf-8')
        
        if file_ext ==ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path=file_path)
        
        return None
    
    def get_file_content(self,file_id:str):
        loader =self.get_file_loader(file_id=file_id)
        if loader:
            docs =loader.load()
            return docs
        return None
    
    def get_clean_text(self,text):
        return text.replace('\x00', '').strip()



    def get_file_chunks(self,file_content,project_id:int, asset_id:int,doc_type:str):
        
        file_content_text=[
            self.get_clean_text(rec.page_content)
            for rec in file_content
        ]
        text ="\n".join(file_content_text)
        
        TextSpliter =TextSpliterController(doc_type=doc_type)
        chunks =TextSpliter.split_text_chunks(text =text , project_id= project_id ,asset_id=asset_id)
        print("len(file_chunks) =",len(chunks))
        return chunks