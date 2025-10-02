from fastapi import FastAPI
from routes import base,data,nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers import Settings,get_settings
from stores.llm import LLMProviderFactory
from stores.vectordb import VectorDBProviderFactory
from contextlib import asynccontextmanager
from stores.llm.templates.template_parser import TemplateParser




@asynccontextmanager
async def lifespan(app:FastAPI):
    settings = get_settings()
    # when app startup
    app.mongo_connection = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_connection[settings.MONGODB_DATABASE]

    
    llm_provider_factory =LLMProviderFactory(settings)
    
    # generation client
    app.generation_client  =llm_provider_factory.create(provider =settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id =settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client =llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID
                                             ,embedding_size =settings.EMBEDDING_MODEL_SIZE)
    
    # vectore db 
    vectordb_provider_factory =VectorDBProviderFactory(settings)
    app.vectordb_client =vectordb_provider_factory.create(Provider=settings.VECTORE_DB_BACKEND)

    # connect to vectordb
    app.vectordb_client.connect()

    # define object from template parser 
    app.template_parser =TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
        )


    yield
    # when app shutdown
    app.mongo_connection.close()
    app.vectordb_client.disconnect()

    

app =FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)

