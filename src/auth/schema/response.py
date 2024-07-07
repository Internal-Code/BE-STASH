from pydantic import BaseModel

class ResponseDefault(BaseModel):
    success: bool = False
    message: str = ""
    data: None | dict | list = None