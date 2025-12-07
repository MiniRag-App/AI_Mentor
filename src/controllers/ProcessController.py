from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
from models import ProcessingEnum
import logging
import re

from langchain_community.document_loaders import PyPDFLoader,TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models.db_schemes import DataChunk


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
            return PyPDFLoader(file_path=file_path)
        
        return None
    
    def get_file_content(self,file_id:str):
        loader =self.get_file_loader(file_id=file_id)
        if loader:
            docs =loader.load()
            return docs
        return None
    
    def get_clean_text(self, text):
        # Remove empty line 
        text = re.sub(r'\n\s*\n', '\n', text)
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()




    def get_file_chunks(self, file_content, asset_id, doc_type: str, chunk_size=1000, overlap_size=200):
        
        spliter =RecursiveCharacterTextSplitter(
              chunk_size=chunk_size,
              chunk_overlap=overlap_size,
              length_function =len,
              add_start_index=True,

        )
        # clean text befor split it 
        for doc in file_content:
            doc.page_content =self.get_clean_text(doc.page_content)

        chunks =spliter.split_documents(file_content)
        
        file_chunks = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=idx,
                chunk_project_id=self.project_id,
                chunk_asset_id=asset_id,
                chunk_doc_type=doc_type
            )
            for idx, chunk in enumerate(chunks)
        ]
        
        return file_chunks