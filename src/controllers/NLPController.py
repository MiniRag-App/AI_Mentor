from .BaseController import BaseController
from models.db_schemes import Project,DataChunk
from typing import List
from stores import DocumentTypeEnum
import json
from models.enumrations.QueryEnum import QueryEnum

class NLPController(BaseController):
    def __init__(self,generation_client, embedding_client, vectordb_client,template_parser):
        super().__init__()

        self.generation_client =generation_client
        self.embedding_client =embedding_client
        self.vectordb_client =vectordb_client
        self.template_parser =template_parser

    def classify_question(self,query: str) -> str:
        question_lower = query.lower()

        # Priority 1: Comparison (needs both)
        comparison_keywords = ['missing', 'lack', 'gap', 'match', 'score','imporve' 
                            'compare', 'qualify', 'fit', 'rate', 'eligible']
        if any(keyword in question_lower for keyword in comparison_keywords):
            return QueryEnum.BOTH.value
        
        # Priority 2: Self-reference (CV only)
        self_keywords = ['my ', 'i have', 'i worked', 'i studied', 'me ']
        if any(keyword in question_lower for keyword in self_keywords):
            return QueryEnum.CV.value
        
        # Priority 3: Job-reference (JD only)
        job_keywords = ['required', 'requirement', 'they want', 'job needs',
                    'looking for', 'responsibilities', 'duties', 'must have']
        if any(keyword in question_lower for keyword in job_keywords):
            return QueryEnum.JD.value
        
        # Default: General (both, let vectors decide)
        return QueryEnum.BOTH.value

    def create_collection_name(self ,project_id:int):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    

    async def reset_vectordb_collection(self,project:Project):
        collection_name =self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name)
    
   
    async def get_vectordb_collection_info(self,project:Project):
        collection_name =self.create_collection_name(project_id=project.project_id)
        collection_info= await self.vectordb_client.get_collection_info(collection_name)

        return  json.loads(
            json.dumps(collection_info,default=lambda x:x.__dict__)
        ) 
    


    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                                   chunks_ids: List[int]):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: manage items
        texts = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in  chunks]
        vectors = self.embedding_client.embed_text(text=texts, document_type=DocumentTypeEnum.DOCUMENT.value)
           

        # step3: create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
        )

        # step4: insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids
        )

        return True
    
    async def search_vectordb_collection(self,project:Project ,query:str, limit:int):
        # step:get query type
        query_type =self.classify_question(query)
         
        # step2: get collection name 
        collection_name =self.create_collection_name(project_id=project.project_id)


        # step2: get embedding vector for text
        query_vector =None 

        vectors =self.embedding_client.embed_text(
            text =query ,
            document_type=DocumentTypeEnum.QUERY.value
        )

        if not vectors or len(vectors) ==0 :
            return False
        
        if isinstance(vectors,list) or len(vectors) > 0:
            query_vector =vectors[0]

        if not query_vector : 
            return False
        

        # step3: get semantic search
        
        result = await self.vectordb_client.search_by_vector(
             collection_name = collection_name,
             vector = query_vector, 
             limit =limit,
             query_type =query_type
        )

        if not result:
            return False 
    
       
        # return  json.loads(
        #     json.dumps(result,default=lambda x:x.__dict__)
        # ) 
        
        return result
    

    async def answer_rag_question(self, project: Project, query: str, job_desc: str, limit: int = 10):

        print("[DEBUG] Step 1: Retrieving relevant documents...")
        retrieved_documents = await self.search_vectordb_collection(project=project, text=query, limit=limit)
        print(f"[DEBUG] Retrieved {len(retrieved_documents) if retrieved_documents else 0} documents.")

        if not retrieved_documents or len(retrieved_documents) == 0:
            print("[DEBUG] No documents retrieved. Returning None.")
            return None

        print("[DEBUG] Step 2: Constructing system prompt...")
        system_prompt = self.template_parser.get_prompt_value(group='rag', key='system_prompt')

        print("[DEBUG] Step 3: Constructing document prompts...")
        document_prompts = "\n".join([
            self.template_parser.get_prompt_value(
                group='rag',
                key='Document_prompt',
                vars={
                    "doc_num": idx,
                    "chunk_text": self.generation_client.proecess_text(doc.text)
                }
            )
            for idx, doc in enumerate(retrieved_documents)
        ])

        print("[DEBUG] Step 4: Constructing Job Description prompt...")
        jobdesc_prompt = self.template_parser.get_prompt_value(
            group='rag',
            key='JobDesc_prompt',
            vars={"job_description": job_desc}
        )

        print("[DEBUG] Step 5: Constructing footer prompt...")
        footer_prompt = self.template_parser.get_prompt_value(group='rag', key='Footer_prompt', vars={"query": query})

        print("[DEBUG] Step 6: Constructing chat history...")
        chat_history = [
            self.generation_client.consturct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        print("[DEBUG] Step 7: Constructing full prompt...")
        full_prompt = '\n\n'.join([document_prompts, jobdesc_prompt, footer_prompt])

        print("[DEBUG] Step 8: Calling LLM generate_text...")
        answer = self.generation_client.generate_text(prompt=full_prompt, chat_history=chat_history)
        print("[DEBUG] Step 9: LLM response received.")

        return answer, full_prompt, chat_history
