from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
from models import ProcessingEnum

from langchain_community.document_loaders import PyMuPDFLoader,TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ProcessController(BaseController):
    def __init__(self,project_id:str):
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
        if file_ext ==ProcessingEnum.TXT.value:
            return TextLoader(file_path=file_path,encoding='utf-8')
        
        if file_ext ==ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path=file_path)
        
        return None
    
    def get_file_content(self,file_id:str):
        loader =self.get_file_loader(file_id=file_id)

        docs =loader.load()
        return docs
    
    def get_file_chunks(self,file_id:str,chunk_size=100,overlap_size=20):
        file_content =self.get_file_content(file_id=file_id)
        spliter =RecursiveCharacterTextSplitter(
              chunk_size=chunk_size,
              chunk_overlap=overlap_size,
              length_function =len
        )
        
        file_content_text=[
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata =[
            rec.metadata
            for rec in file_content
        ]

        chunks =spliter.create_documents(
            file_content_text,
            metadatas=file_content_metadata
        )
       
        return chunks