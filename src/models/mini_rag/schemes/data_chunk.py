from .minirag_base import seqlalchemyBase
from sqlalchemy import Column ,Integer ,DateTime,func,String,ForeignKey
from sqlalchemy.dialects.postgresql import UUID ,JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel
import uuid


class DataChunk(seqlalchemyBase):
    __tablename__="DataChunks"

    chunk_id =Column(Integer ,primary_key=True,autoincrement=True)
    chunk_uuid =Column(UUID(as_uuid=True),default =uuid.uuid4,unique=True,nullable=False)
    chunk_text =Column(String,nullable=False)
    chunk_order =Column(Integer,nullable=False)

    chunk_metadata =Column(JSONB,nullable=True)

    created_at =Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at =Column(DateTime(timezone=True),onupdate=func.now(),nullable=True)

    chunk_project_id =Column(Integer,ForeignKey("Projects.project_id"),nullable=False)
    chunk_asset_id = Column(Integer,ForeignKey("Assets.asset_id"),nullable=False)

    __table_args__ =(
        Index("index_ chunk_project_id", chunk_project_id),
        Index("index_ chunk_asset_id", chunk_asset_id)
    )


    Project =relationship("Project",back_populates="DataChunks")
    Asset =relationship("Asset",back_populates="DataChunks")


class RetrivedDocuments(BaseModel):
     text:str
     score: float