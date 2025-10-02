from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest, SearchRequest
from models import ProjectDataModel
from models import ChunkDataModel
from controllers import NLPController
from models import ResponseSignals

import logging

logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):

    project_model = await ProjectDataModel.create_instance(
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
                "signal": ResponseSignals.PROJEFT_NOT_FOUND.value
            }
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser =request.app.template_parser
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0

    while has_records:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.id, page_no=page_no)
        if len(page_chunks):
            page_no += 1
        
        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids =  list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)
        
        is_inserted = nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            do_reset=push_request.do_rest,
            chunks_ids=chunks_ids
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignals.INSERT_INOT_VECTOR_DB_ERROR.value
                }
            )
        
        inserted_items_count += len(page_chunks)
        
    return JSONResponse(
        content={
            "signal": ResponseSignals.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    
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

    collection_info = nlp_controller.get_vectordb_collection_info(project=project)

    return JSONResponse(
        content={
            "signal": ResponseSignals.VECTORDB_COLLECTION_INFO_RETRIVED.value,
            "collection_info": collection_info
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request:Request ,project_id:str ,search_request:SearchRequest):


      
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
    

    results =nlp_controller.search_vectordb_collection(project =project,text =search_request.text ,limit =search_request.limit)

    
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
async def answer_rag(request:Request ,project_id:str ,search_request:SearchRequest):

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
        answer, full_prompt, chat_histoy = nlp_controller.answer_rag_question(
            project=project,
            query=search_request.text,
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
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_histoy
        }
    )
    




   