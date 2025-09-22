from ..LLMInterface import LLMInterface
from ..LLMEnum import CoherEnum, DocumentTypeEnum 
import cohere
import logging
  


class CoHerProvider(LLMInterface):
    def __init__(self, api_key:str,
                 default_input_max_characters:int = 1000,
                 default_generation_max_output_tokens:int =1000,
                 default_generation_temprature: float= 0.1):
              
        self.api_key=api_key
        self.default_input_max_characters=default_input_max_characters
        self.default_generation_max_output_tokens=default_generation_max_output_tokens
        self.default_generation_temprature=default_generation_temprature
        
        self.generation_mdoel_id=None
        self.embedding_model_id=None
        self.embedding_size=None


        self.client =cohere.ClientV2(
            api_key =self.api_key
        )

        self.logger =logging.getLogger(__name__)

    def set_generation_model(self, model_id:str): # make you able to change model name during run time 
        self.generation_mdoel_id =model_id

    def set_embedding_model(self, model_id:str,embedding_size:int):
        self.embedding_model_id =model_id 
        self.embedding_size=embedding_size


    def generate_text(self, prompt, chat_history:list=[], max_output_tokens:int = None, temprature:int = None):
        
        if self.client is None:
            self.logger.error('CoHer client was not set')

        if self.generation_mdoel_id is None:
            self.logger.error('Generation model id was not set')

        max_output_tokens= max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temprature =temprature if temprature else self.default_generation_temprature

        chat_history.append(
            self.consturct_prompt(prompt,CoherEnum.USER.value)
        )
        response =self.client.chat(
            model =self.generation_mdoel_id,
            messages=chat_history,
            max_tokens= max_output_tokens,
            temperature=temprature 
        )

        if response is None or response.message is None or  response.message[0].text is None:
            self.logger.error('Failed to generate text')
            return None
         
        return response.message[0].text

   # process any prompt before passing it to any model
    def proecess_text(self,text:str):
        return text[:self.default_input_max_characters].strip()
    
    def consturct_prompt(self, prompt, role):
        return {
            'role':role,
            "content":self.proecess_text(prompt)
        }

    def embed_text(self,text:str,document_type:str =None):
         
        if self.client is None:
            self.logger.error('CoHer client was not set')

        if  self.embedding_model_id is None:
            self.logger.error(' embedding model id was not set')

        input_type=CoherEnum.DOCUMENT.value

        if  document_type ==  DocumentTypeEnum.QUERY.value:
            input_type = CoherEnum.QUERY.value

        response =self.client.embed(
            model =self.embedding_model_id,
            texts =[self.proecess_text(text)],
            input_type=input_type,
            embedding_types=["float"],
        )    


        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error('error while embedding with coher ') 
            return None
        
        return response.embeddings.float[0]


        
