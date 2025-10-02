from fastapi import APIRouter,UploadFile,status,Request
from helpers.config import Settings,get_settings
from fastapi.responses import JSONResponse
from controllers import DataController,ProjectController,ProcessController
from models import ResponseSignals,ProjectDataModel,ChunkDataModel
from models import AssetTypeEnum
import os
import aiofiles
import logging
from models import DataChunk,ProjectDataModel,AssetModel ,Assets
from datetime import datetime


from .schemes import ProcessRequest

logger =logging.getLogger('uvicorn.error')

data_router =APIRouter(
    prefix="/api/v1/data",
    tags=['api_v1','data']
)
app_settings =get_settings()

@data_router.post('/upload/{project_id}')
async def upload_data(request:Request,project_id:str,file:UploadFile):
       # store project_id in mongodb
       project_model =await ProjectDataModel.create_instance(
              db_client =request.app.db_client
       )

       # store or get prject 

       project =await project_model.get_project_or_create_one(
              project_id=project_id
       )

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
 

       # store file_id in asset collection in mongodb
       asset_model =await AssetModel.create_instance(
              db_client=request.app.db_client
              )
       
       asset =Assets(
              asset_project_id =project.id,
              asset_type=AssetTypeEnum.ASSET_TYPE.value,
              asset_name =file_id,
              asset_size =os.path.getsize(file_path)
       )
       asset_record =await asset_model.create_asset(asset=asset)

       return JSONResponse(
                     content={
                            'singal':ResponseSignals.FILE_UPLOADED_SUCCESS.value,
                            'file_id':str(asset_record.id)
                     }     )
  


@data_router.post('/process/{project_id}')
async def process_endpoint(request:Request,project_id:str,process_request:ProcessRequest):
       chunk_size =process_request.chunk_size
       overlap =process_request.overlap
       do_reset =process_request.do_reset

       project_model =await ProjectDataModel.create_instance(
              db_client=request.app.db_client
       )
       project =await project_model.get_project_or_create_one(project_id=project_id)

       project_files_ids={}

       if process_request.file_id:
              asset_model =await AssetModel.create_instance(
              db_client=request.app.db_client
              )
              asset_record =await asset_model.get_asset_record(
                     asset_project_id=project.id,
                     asset_name =process_request.file_id
                     )
              
              if asset_record is None:
                     return JSONResponse(
                     status_code =status.HTTP_400_BAD_REQUEST,
                     content={
                     'singal':ResponseSignals.FILE_ID_ERROR.value
                      }
                 
                     )

              project_files_ids={
                     asset_record.id:asset_record.asset_name
              }
       else:
              asset_model =await AssetModel.create_instance(
              db_client=request.app.db_client
              )
              
              project_files_list =await asset_model.get_all_project_assets(
                     asset_project_id=project.id,
                     asset_type=AssetTypeEnum.ASSET_TYPE.value
              )

              project_files_ids ={
                     record.id:record.asset_name
                     for record in project_files_list
              }

       if len(project_files_ids) ==0:
                  return JSONResponse(
                     status_code =status.HTTP_400_BAD_REQUEST,
                     content={
                     'singal':ResponseSignals.NO_FILES_ERROR.value
                      }
                 
                     )
       
      # delete chunks from database 
       chunk_model =await ChunkDataModel.create_instance(
                     db_client=request.app.db_client
              )

       if do_reset ==1:
              _ = await chunk_model.delete_chunk_by_project_id(
                     project_id =project.id
                     )


       process_controller =ProcessController(project_id =project_id)
       
       no_chunks=0
       no_files=0

       for asset_id,file_id in project_files_ids.items():
              file_content =process_controller.get_file_content(file_id=file_id)

              if file_content is None:
                     logger.error(f"error while processing file id {file_id}")
                     continue
              
              file_chunks =process_controller.get_file_chunks(
                     chunk_size =chunk_size,
                     overlap_size=overlap,
                     file_content =file_content
                     )
              
              if file_chunks is None or len(file_chunks) ==0:
                     
                     return JSONResponse(
                            status_code =status.HTTP_400_BAD_REQUEST,
                            content={
                            'singal':ResponseSignals.FILE_PROCESSING_FIALED.value
                            }
                     
                            )
              
              # store file chunks in mongodb
       
              
              file_chunks_reco =[
                     DataChunk(
                     chunk_text=chunk.page_content,
                     chunk_order=i+1,
                     chunk_metadata=chunk.metadata,
                     chunk_project_id =project.id,
                     chunk_asset_id=asset_id
                     )
                     for i,chunk in enumerate(file_chunks)
              ]

              no_chunks +=await chunk_model.insert_many_chunks(
                     chunks=file_chunks_reco,
              )
              no_files +=1




       return JSONResponse(
              content={
                     'signal':ResponseSignals.FILE_PROCESSING_SUCESS.value,
                     'inserted_chunks':no_chunks,
                     'processed_files':no_files
              }
       )

