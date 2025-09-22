from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME:str
    APP_VERSION:str
    FILE_ALLOWED_TYPES:list
    FILE_MAX_SIZE:int
    FILE_DEFAULT_CHUNK_SIZE:int
    MONGODB_URL:str
    MONGODB_DATABASE:str


    GENERATION_BACKEND :str
    EMBEDDING_BACKEND :str 


    GROQ_API_KEY :str =None
    COHER_API_KEY:str =None

    GENERATION_MODEL_ID :str =None
    EMBEDDING_MODEL_ID  :str =None
    EMBEDDING_MODEL_SIZE:int =None


    default_input_max_characters :int =None
    default_generation_max_output_tokens :int =None
    default_generation_temprature :float =None

    VECTORE_DB_BACKEND :str
    VECTORE_DB_PATH :str
    VECTORE_DB_DISTANCE_METHOD :str =None

    class Config:
        env_file='.env'

def get_settings():
    return Settings()