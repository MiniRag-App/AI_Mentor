from .BaseController import BaseController
from models import Project,DataChunk
from typing import List
from stores import DocumentTypeEnum
import time 
import json

class NLPController(BaseController):
    def __init__(self,generation_client, embedding_client, vectordb_client,template_parser):
        super().__init__()

        self.generation_client =generation_client
        self.embedding_client =embedding_client
        self.vectordb_client =vectordb_client
        self.template_parser =template_parser


    def create_collection_name(self ,project_id:str):
        return f"collection_{project_id}".strip()
    

    def reset_vectordb_collection(self,project:Project):
        collection_name =self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name)
    
   
    def get_vectordb_collection_info(self,project:Project):
        collection_name =self.create_collection_name(project_id=project.project_id)
        collection_info= self.vectordb_client.get_collection_info(collection_name)

        return  json.loads(
            json.dumps(collection_info,default=lambda x:x.__dict__)
        ) 
    


    def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                                   chunks_ids: List[int], 
                                   do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: manage items
        texts = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in  chunks]
        vectors = [
            self.embedding_client.embed_text(text=text, 
                                             document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]

        # step3: create collection if not exists
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # step4: insert into vector db
        _ = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors
        )

        return True
    
    def search_vectordb_collection(self,project:Project ,text:str, limit:int):

        # step1: get collection name 
        collection_name =self.create_collection_name(project_id=project.project_id)

        # step2: get embedding vector for text
        vector =self.embedding_client.embed_text(
            text =text ,
            document_type=DocumentTypeEnum.QUERY.value
        )

        if not vector or len(vector) ==0 :
            return False
        

        # step3: get semantic search
        
        result = self.vectordb_client.search_by_vector(
             collection_name = collection_name,
             vector = vector, 
             limit =limit
        )

        if not result:
            return False 
    
       
        # return  json.loads(
        #     json.dumps(result,default=lambda x:x.__dict__)
        # ) 
        
        return result
    

    def answer_rag_question(self,project:Project ,query:str ,limit:int=10):

        print("[DEBUG] Step 1: Retrieving relevant documents...")
        retrieved_documents = self.search_vectordb_collection(project=project, text=query, limit=limit)
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
                    "chunk_text": doc.text
                })
            for idx, doc in enumerate(retrieved_documents)
        ])

        print("[DEBUG] Step 4: Constructing footer prompt...")


        footer_prompt = self.template_parser.get_prompt_value(group='rag', key='Footer_prompt',vars={"query":query})

        print("[DEBUG] Step 5: Constructing chat history...")
        chat_histoy = [
            self.generation_client.consturct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        print("[DEBUG] Step 6: Constructing full prompt...")
        full_prompt = '\n\n'.join([document_prompts, footer_prompt])

        print("[DEBUG] Step 7: Calling LLM generate_text...")
        answer = self.generation_client.generate_text(prompt=full_prompt, chat_history=chat_histoy)
        print("[DEBUG] Step 8: LLM response received.")

        return answer, full_prompt, chat_histoy


