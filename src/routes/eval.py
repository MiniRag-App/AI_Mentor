from fastapi import FastAPI ,APIRouter,Depends,Request
from helpers.config import get_settings,Settings
from models.ProjectDataModel import ProjectDataModel
from evaluation.metrics import EvaluationMetrics
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
    evalutaion_metrics =EvaluationMetrics(nlp_controller=nlp_controller,
                                          generation_client=request.app.generation_client,
                                          embedding_client=request.app.embedding_client)
    
    evaluation_result =await evalutaion_metrics.ragas_evaluation(project=project)
    
    return {
        " Faithfulness:":evaluation_result['faithfulness'],
        "Answer Relevancy:": evaluation_result['answer_relevancy'],
        "Context Precision:":evaluation_result['context_precision'],
        "Context Recall:":evaluation_result['context_recall']
        }