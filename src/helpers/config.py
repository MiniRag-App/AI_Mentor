from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME:str
    APP_VERSION:str
    FILE_ALLOWED_TYPES:list
    FILE_MAX_SIZE:int
    FILE_DEFAULT_CHUNK_SIZE:int


    POSTGRES_USERNAME :str
    POSTGRES_HOST :str
    POSTGRES_PASSWORD :str
    POSTGRES_PORT :int
    POSTGRES_MAIN_DATABASE :str


    GENERATION_BACKEND :str
    EMBEDDING_BACKEND :str 


    OPENAI_API_KEY :str =None
    COHER_API_KEY:str =None
    GROQ_API_KEY :str =None

    OPENAI_BASE_URL_LITERAL :List[str] = None
    OPENAI_BASE_URL:str= None

    GENERATION_MODEL_ID_LITERAL :List[str] = None

    GENERATION_MODEL_ID :str =None
    EMBEDDING_MODEL_ID  :str =None
    EMBEDDING_MODEL_SIZE:int =None


    default_input_max_characters :int =None
    default_generation_max_output_tokens :int =None
    default_generation_temprature :float =None

    VECTORE_DB_BACKEND :str
    VECTORE_DB_PATH :str
    VECTORE_DB_DISTANCE_METHOD :str =None

    DEFAULT_LANG :str 
    PRIMARY_LANG :str

    class Config:
        env_file='.env'

def get_settings():
    return Settings()