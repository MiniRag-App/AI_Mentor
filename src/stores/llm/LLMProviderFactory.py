from .LLMEnum import LLMEnum
from .providers import CoHerProvider ,GroqProvider

class LLMProviderFactory:

    def __init__(self,config:dict):
        self.config =config


    def create(self,provider:str):
        if provider == LLMEnum.GROQ.value :
            return GroqProvider(
                api_key =self.config.GROQ_API_KEY,
                default_input_max_characters =self.config.default_input_max_characters,
                default_generation_max_output_tokens=self.config.default_generation_max_output_tokens,
                default_generation_temprature =self.config.default_generation_temprature
            )

        if provider ==LLMEnum.COHER.value:
            return CoHerProvider(
                api_key =self.config.COHER_API_KEY,
                default_input_max_characters =self.config.default_input_max_characters,
                default_generation_max_output_tokens=self.config.default_generation_max_output_tokens,
                default_generation_temprature =self.config.default_generation_temprature
            )

        return None


    