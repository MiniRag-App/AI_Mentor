from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest, SearchRequest
from models import ProjectDataModel
from models import ChunkDataModel
from controllers import NLPController
from models import ResponseSignals
from tqdm.auto import tqdm
import asyncio
import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):

    project_model = await  ProjectDataModel.create_instance(
        db_client=request.app.db_client
    )

    chunk_model = await ChunkDataModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignals.PROJECT_NOT_FOUND_ERROR.value
            }
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0

    # create collection if not exists
    collection_name = nlp_controller.create_collection_name(project_id=project.project_id)

    _ = await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        embedding_size=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_reset,
    )

    # setup batching
    total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
    pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)

    while has_records:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.project_id, page_no=page_no)
        if len(page_chunks):
            page_no += 1
        
        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids =  [ c.chunk_id for c in page_chunks ]
        idx += len(page_chunks)
        
        is_inserted = await nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids=chunks_ids
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignals.INSERT_INTO_VECTORDB_ERROR.value
                }
            )

        pbar.update(len(page_chunks))
        inserted_items_count += len(page_chunks)
        
    return JSONResponse(
        content={
            "signal": ResponseSignals.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    
    project_model = await ProjectDataModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser =request.app.template_parser
    )

    collection_info = await nlp_controller.get_vectordb_collection_info(project=project)

    return JSONResponse(
        content={
            "signal": ResponseSignals.VECTORDB_COLLECTION_INFO_RETRIVED.value,
            "collection_info": collection_info
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request:Request ,project_id:int ,search_request:SearchRequest):


      
    project_model = await ProjectDataModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser =request.app.template_parser
    )
    

    results =await nlp_controller.search_vectordb_collection(project =project,query =search_request.query ,limit =search_request.limit)

    
    if not results:
        return JSONResponse(
        status_code =status.HTTP_400_BAD_REQUEST,
        content={
            "signal": ResponseSignals.VECTOREDB_SEARCH_ERROR.value
        }
    )



    return JSONResponse(
        content={
            "signal": ResponseSignals.VECTORDB_SEARCH_SUCCESS.value,
            "results":[ res.dict()   for res in results]
        }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request:Request ,project_id:int ,search_request:SearchRequest):

    logger.info("[DEBUG] Received request for answer endpoint with project_id=%s, text=%s", project_id, search_request.text)

    project_model = await ProjectDataModel.create_instance(
        db_client=request.app.db_client
    )
    logger.info("[DEBUG] Project model created.")

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )
    logger.info("[DEBUG] Project loaded or created: %s", project)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser =request.app.template_parser
    )
    logger.info("[DEBUG] NLPController initialized.")

    try:
        answer, full_prompt, chat_histoy = await nlp_controller.answer_rag_question(
            project=project,
            query=search_request.text,
            job_desc =search_request.job_desc,
            limit=search_request.limit
        )
        logger.info("[DEBUG] answer_rag_question completed.")
    except Exception as e:
        logger.error("[ERROR] Exception in answer_rag_question: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignals.RAG_ANSWER_ERROR.value,
                "error": str(e)
            }
        )

    if not answer:
        logger.info("[DEBUG] No answer returned from answer_rag_question.")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignals.RAG_ANSWER_ERROR.value
            }
        )

    logger.info("[DEBUG] Returning answer response.")
    return JSONResponse(
        content={
            "signal": ResponseSignals.RAG_ANSWER_SUCCESS.value,
            "answer": answer
        }
    )
    




   