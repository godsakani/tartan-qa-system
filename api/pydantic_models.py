from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ModelName(str, Enum):
    GPT_O = "gpt-4o-2024-08-06"
    GPT_O_MINI = "gpt-4o-mini"
    
    
class QueryInput(BaseModel):
    question:str
    session_id:str=Field(default=None)
    model: ModelName = Field(default=ModelName.GPT_O)
    

class QueryResponse(BaseModel):
    answer:str
    session_id:str
    model:ModelName
    
    
class DocumentInfo(BaseModel):
    id:int
    filename:str
    upload_timestamp:datetime
    
class DeleFileRequest(BaseModel):
    file_id:int
