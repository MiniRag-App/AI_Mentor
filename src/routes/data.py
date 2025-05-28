from fastapi import APIRouter,UploadFile,status
from helpers.config import Settings
from fastapi.responses import JSONResponse
from controllers import DataController,ProjectController,ProcessController
from models import ResponseSignals
import os
import aiofiles
import logging

from .schemes import ProcessRequest

logger =logging.getLogger('uvicorn.error')

data_router =APIRouter(
    prefix="/api/v1/data",
    tags=['api_v1','data']
)
app_settings =Settings()

@data_router.post('/upload/{project_id}')
async def upload_data(project_id:str,file:UploadFile):

       obj_data_controller =DataController()
       # validate the file properities
       is_valid,result_signal =obj_data_controller.validate_uploaded_file(file=file)
       
       if not is_valid:
              return JSONResponse(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     content={
                            'signal':result_signal
                     }
              )
       
       # project_dir_path =ProjectController().get_project_path(project_id=project_id)
       file_path ,file_id =obj_data_controller.generate_unique_file_path(
              original_file_name=file.filename,
              project_id = project_id

       )

       try:
              async with aiofiles.open(file_path,'wb') as f:
                     while chunk:=await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                            await f.write(chunk)

       except Exception as e:
              logger.error =(f"Error while uploading file :{e}")
              return JSONResponse(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     content={
                            'signal':ResponseSignals.FILE_UPLOADED_FAIL.value
                     }
              )

       return JSONResponse(
                     content={
                            'singal':ResponseSignals.FILE_UPLOADED_SUCCESS.value,
                            'file_id':file_id
                     }     )
  


@data_router.post('/process/{project_id}')
async def process_endpoint(project_id:str,process_request:ProcessRequest):
       file_id =process_request.file_id
       chunk_size =process_request.chunk_size
       overlap =process_request.overlap

       process_controller =ProcessController(project_id =project_id)
       
       file_chunks =process_controller.get_file_chunks(
              file_id=file_id,
              chunk_size =chunk_size,
              overlap_size=overlap
              )
       
       if file_chunks is None or len(file_chunks) ==0:
              
              return JSONResponse(
                     status_code =status.HTTP_400_BAD_REQUEST,
                     content={
                     'singal':ResponseSignals.FILE_PROCESSING_FIALED.value
                      }
                 
                     )
       
       return file_chunks

