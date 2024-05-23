from pydantic import BaseModel
from typing import List, Union, Dict

class Metadata(BaseModel):
    id: str = ""

class ResponseGeneral(BaseModel):
    success: bool = True
    statusCode: int = 200
    message: str = ""
    body: Union[Dict, List, str] = {}
    metadata: Metadata = Metadata()