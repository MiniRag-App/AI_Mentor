from fastapi import FastAPI ,APIRouter,Depends,Request
from models.ProjectDataModel import ProjectDataModel
from evaluation.DeepEvalRAGEvaluator import DeepEvalRAGEvaluator
from controllers.NLPController import NLPController

eval_router =APIRouter(
    prefix='/api/v1',
    tags=['api_v1']
)


@eval_router.post('/eval/{project_id}')
async def evaluation_rag_system(request:Request,project_id:int):
    
    project_model =ProjectDataModel(request.app.db_client)
    
    project =await project_model.get_project_or_create_one(project_id=project_id)
    
    nlp_controller =NLPController(
                     vectordb_client=request.app.vectordb_client,
                     generation_client=request.app.generation_client,
                     embedding_client=request.app.embedding_client,
                     template_parser =request.app.template_parser
    )
    deep_eval =DeepEvalRAGEvaluator(nlp_controller=nlp_controller)
    results = await deep_eval.run_evaluation(project=project)
    
    return results