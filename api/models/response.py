from pydantic import BaseModel
from typing import List, Union, Dict

class Metadata(BaseModel):
    id: str = ""

class ResponseGeneral(BaseModel):
    status_code: int = 200
    message: str = ""
    success: bool = True
    body: Union[Dict, List, str] = []
    metadata: Metadata = Metadata()