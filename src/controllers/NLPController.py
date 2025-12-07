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
        querys = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in  chunks]
        vectors = self.embedding_client.embed_text(text=querys, document_type=DocumentTypeEnum.DOCUMENT.value)
           

        # step3: create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
        )

        # step4: insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=querys,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids
        )

        return True
    
    async def search_vectordb_collection(self,project:Project ,query:str, limit:int):
        # step1: get collection name 
        collection_name =self.create_collection_name(project_id=project.project_id)


        # step2: get embedding vector for query
        query_vector =None 

        vectors =self.embedding_client.embed_text(
            text=query ,
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
             limit =limit
        )

        if not result:
            return False 
    
       
        # return  json.loads(
        #     json.dumps(result,default=lambda x:x.__dict__)
        # ) 
        
        return result
    

    async def answer_rag_question(self, project: Project, query: str, limit: int = 10, top_n_per_type: int = 2):
        print("[DEBUG] Step 1: Retrieving relevant documents...")
        retrieved_documents = await self.search_vectordb_collection(project=project, query=query, limit=limit)
        print(f"[DEBUG] Retrieved {len(retrieved_documents) if retrieved_documents else 0} documents.")

        if not retrieved_documents:
            print("[DEBUG] No documents retrieved. Returning None.")
            return None

        # Step 2: Separate CV and Job chunks
        cv_chunks = [doc for doc in retrieved_documents if doc.doc_type == QueryEnum.CV.value][:top_n_per_type]
        job_chunks = [doc for doc in retrieved_documents if doc.doc_type == QueryEnum.JD.value][:top_n_per_type]

        print(f"[DEBUG] Top {len(cv_chunks)} CV chunks, Top {len(job_chunks)} Job chunks selected.")

        # Step 3: Construct system prompt
        system_prompt_query = self.template_parser.get_prompt_value(group='rag', key='system_prompt')

        # Step 4: Construct Document prompts for CV and Job together
        document_prompts_list = []

        for idx, doc in enumerate(cv_chunks + job_chunks):
            document_prompts_list.append(
                self.template_parser.get_prompt_value(
                    group='rag',
                    key='Document_prompt',
                    vars={
                        "doc_num": idx + 1,
                        "doc_type": doc.doc_type,
                        "chunk_text": self.generation_client.proecess_text(doc.text)
                    }
                )
            )

        document_prompts = "\n".join(document_prompts_list)
        print(f"[DEBUG] Document prompts constructed with {len(document_prompts_list)} chunks.")

        # Step 5: Construct Footer prompt
        footer_prompt = self.template_parser.get_prompt_value(
            group='rag',
            key='Footer_prompt',
            vars={"query": query}
        )

        # Step 6: Construct chat history
        chat_history = [
            self.generation_client.consturct_prompt(
                prompt=system_prompt_query,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        # Step 7: Combine full prompt
        full_prompt = '\n\n'.join([document_prompts, footer_prompt])
        print("[DEBUG] Full prompt constructed. Length:", len(full_prompt))

        # Step 8: Call LLM
        answer = self.generation_client.generate(prompt=full_prompt, chat_history=chat_history)
        print("[DEBUG] LLM response received.")

        return answer, full_prompt, chat_history,retrieved_documents
