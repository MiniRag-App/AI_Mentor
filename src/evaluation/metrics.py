import json
import os 
from models.ProjectDataModel import ProjectDataModel
from ragas import evaluate
from datasets import Dataset
from helpers.config import Settings

from models.db_schemes import Project
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
 

class EvaluationMetrics:  
    def __init__(self,nlp_controller,generation_client,embedding_client):
        self.results =[]
        self.base_dir =os.path.dirname(os.path.dirname(__file__))
        self.evaluation_data_path =os.path.join(self.base_dir,'evaluation/evaluation_dataset.json')
        self.test_questions =[]
        self.nlp_controller =nlp_controller
        self.generation_client =generation_client
        self.embedding_client =embedding_client
        self.settings =Settings()
        
    def load_evlauation_data(self):
        with open(self.evaluation_data_path,'r',encoding='utf-8') as f:
            data =json.load(f)
        self.test_questions =data['Questions']
        
    async def construct_full_results_ragas(self,project):
        for test_case in self.test_questions:
            question =test_case['question']
            
            answer, full_prompt, chat_history,context=await self.nlp_controller.answer_rag_question(
                project =project,
                query =question
            )
            
            self.results.append({
                "question":question,
                "answer":answer,
                'retrieved_contexts':[doc.text for doc in context],
                "ground_truth":test_case['ground_truth']
            })
    
    async def ragas_evaluation(self,project):
        # step_1: load evalutaion data
        self.load_evlauation_data()
        
        # step_2 construct data for ragas
        await self.construct_full_results_ragas(project=project)
        
        # step_3 : calculate evalution metrics
        ragas_data ={
            "question":[ res['question']  for res in self.results],
            "answer":[res['answer'] for res in self.results],
            "retrieved_contexts":[ res['retrieved_contexts'] for res in self.results],
            "ground_truth":[ res['ground_truth'] for res in self.results]
        }
        
        dataset =Dataset.from_dict(ragas_data)
        
        # ragas llm 
       # Create LangChain-compatible LLM
        langchain_llm = ChatOpenAI(
            model=self.settings.GENERATION_MODEL_ID ,
            api_key=self.settings.OPENAI_API_KEY,
            base_url=self.settings.OPENAI_BASE_URL,
            temperature=0.2  # Low temp for evaluation consistency
        )
        
        ragas_llm = LangchainLLMWrapper(langchain_llm)
        
        evaluation_result =evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,        # Answer based on retrieved context?
                answer_relevancy,    # Answer addresses the question?
                context_precision,   # Retrieved contexts relevant?
                context_recall       # Retrieved all necessary info?
            ],
            llm=ragas_llm
        )
        return evaluation_result
    
 
        
        