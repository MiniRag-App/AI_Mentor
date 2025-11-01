from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest, SearchRequest
from routes.schemes.drop_create import CreateCollection
from models import ProjectDataModel
from models import ChunkDataModel
from controllers import NLPController
from models import ResponseSignals
from tqdm.auto import tqdm
import asyncio
import logging

logger = logging.getLogger('uvicorn.error')

drop_router = APIRouter(
    prefix="/api/v1/drop",
    tags=["api_v1", "drop"],
)


@drop_router.post("/")
async def drop_table(request:Request, collection_name:str):

    is_deleted =await request.app.vectordb_client.delete_collection(collection_name =collection_name)

    is_existed =await request.app.vectordb_client.is_collection_existed(collection_name=collection_name)
    if not is_deleted and is_existed:
        return {
            "Collection not deleted and existed "
        }
    
    if  is_existed and is_deleted:
        return {
            "collection deleted successfully but still exist"
        }
    
    if not is_existed and is_deleted:
        return {
            "collection are deleted exactly"
        }


@drop_router.post("/create_table/")
async def drop_table(request:Request, create_collection:CreateCollection):

    is_existed =await request.app.vectordb_client.is_collection_existed(collection_name=create_collection.collection_name)
    
    
    if not is_existed :
        is_created = await request.app.vectordb_client.create_collection( collection_name =create_collection.collection_name,
                                                        embedding_size=request.app.embedding_client.embedding_size,
                                                       do_reset=create_collection.do_reset)
        
        if is_created:
            return {
            "collection are created successfully"
            }
        
        return "collection are already existed"


 