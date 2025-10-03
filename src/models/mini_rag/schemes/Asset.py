from .minirag_base import seqlalchemyBase
from sqlalchemy import Column ,Integer ,DateTime,func,String,ForeignKey
from sqlalchemy.dialects.postgresql import UUID ,JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
import uuid


class Asset(seqlalchemyBase):
    __tablename__="Assets"

    asset_id =Column(Integer,primary_key =True,autoincrement=True)
    asset_uuid =Column(UUID(as_uuid=True),default =uuid.uuid4,unique=True,nullable=False)

    asset_name=Column(String,nullable=False)
    asset_type =Column(String,nullable=False)
    asset_size =Column(Integer,nullable=False)
    asset_config =Column(JSONB,nullable=True)

    created_at =Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at =Column(DateTime(timezone=True),onupdate=func.now(),nullable=True)
    # foreignkey
    asset_project_id =Column(Integer,ForeignKey("Projects.project_id"),nullable=False)

    Project =relationship("Project",back_populates="Assets")

    __table_args__ =(

        Index("indx_asset_project_id",asset_project_id),
        Index("indx_asset_type",asset_type)
    )

