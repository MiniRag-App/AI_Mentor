from pydantic import BaseModel
from typing import List,Optional

class CreateCollection(BaseModel):
    do_reset:Optional [int] =0
    collection_name:str