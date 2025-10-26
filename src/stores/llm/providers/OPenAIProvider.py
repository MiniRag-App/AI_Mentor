from ..LLMInterface import LLMInterface
from ..LLMEnum import OpenAIEnum
from openai import OpenAI
import logging

class OpenAIProvider(LLMInterface):
    def __init__(self, api_key:str,base_url:str,
                 default_input_max_characters:int = 1000,
                 default_generation_max_output_tokens:int =1000,
                 default_generation_temprature: float= 0.1):
              
        self.api_key=api_key
        self.base_url =base_url

        self.default_input_max_characters=default_input_max_characters
        self.default_generation_max_output_tokens=default_generation_max_output_tokens
        self.default_generation_temprature=default_generation_temprature
        
        self.generation_mdoel_id=None
        self.embedding_model_id=None
        self.embedding_size=None

        self.client=OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                )

        self.logger=logging.getLogger(__name__)

        self.enums=OpenAIEnum


    def set_generation_model(self, model_id:str): # make you able to change model name during run time 
        self.generation_mdoel_id =model_id

    def set_embedding_model(self, model_id:str,embedding_size:int):
        self.embedding_model_id =model_id 
        self.embedding_size=embedding_size


    def generate_text(self,prompt:str,chat_history:list=[],max_output_tokens:int =None,temprature:float=None):
        
        if self.client is None:
            self.logger.error(' client was not set')

        if self.generation_mdoel_id is None:
            self.logger.error('generation model was not set')

        
        max_output_tokens= max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temprature =temprature if temprature else self.default_generation_temprature



        chat_history.append(
            self.consturct_prompt(prompt, role=self.enums.USER.value)
        )

        response = self.client.chat.completions.create(
            model=self.generation_mdoel_id,
            messages=chat_history,
            temperature=temprature,
            max_tokens=max_output_tokens
        )

        # validate response
        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error('error while generating text ')
            return None

        return response.choices[0].message.content


    # process any prompt before passing it to any model
    def proecess_text(self,text:str):
        return text[:self.default_input_max_characters].strip()
    
    def consturct_prompt(self, prompt, role):
        return {
            'role':role,
            "content":prompt
        }
        



    def embed_text(self,text:str,document_type:str):
        
        raise NotImplementedError


        