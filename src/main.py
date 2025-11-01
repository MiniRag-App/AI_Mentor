from fastapi import FastAPI
from routes import base,data,nlp,drop_try
from helpers import Settings,get_settings
from stores.llm import LLMProviderFactory
from stores.vectordb import VectorDBProviderFactory
from contextlib import asynccontextmanager
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker
from utils.metrics import setup_metrics




@asynccontextmanager
async def lifespan(app:FastAPI):
    settings = get_settings()
    # when app startup
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    # Database engine 
    app.db_engine =create_async_engine(postgres_conn)

    app.db_client = sessionmaker(
        bind =app.db_engine,
        class_=AsyncSession, 
        expire_on_commit=False
    )

    
    llm_provider_factory =LLMProviderFactory(config =settings)
    
    # generation client
    app.generation_client  =llm_provider_factory.create(provider =settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id =settings.GENERATION_MODEL_ID)
    
    # embedding client
    app.embedding_client =llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID
                                             ,embedding_size =settings.EMBEDDING_MODEL_SIZE)
    
    # vectore db 
    vectordb_provider_factory =VectorDBProviderFactory(config =settings,db_client=app.db_client)
    app.vectordb_client =vectordb_provider_factory.create(Provider=settings.VECTORE_DB_BACKEND)

    # connect to vectordb
    await app.vectordb_client.connect()

    # define object from template parser 
    app.template_parser =TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
        )


    yield
    # when app shutdown
    app.db_engine.dispose()
    await app.vectordb_client.disconnect()

    

app =FastAPI(lifespan=lifespan)

# setup promethues metrics 
setup_metrics(app)


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
app.include_router(drop_try.drop_router)

