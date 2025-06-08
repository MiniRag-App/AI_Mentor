from fastapi import FastAPI
from routes import base,data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers import Settings,get_settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # when app startup
    app.mongo_connection = AsyncIOMotorClient(settings.MONGODB_URI)
    app.db_client = app.mongo_connection[settings.MONGODB_DATABASE]
    yield
    # when app shutdown
    app.mongo_connection.close()

    

app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
