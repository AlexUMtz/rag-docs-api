from pydantic import BaseModel
from typing import List


class QuestionRequest(BaseModel):
    question: str
    document_id: str | None = None
    
class SourceDocument(BaseModel):
    content: str
    filename: str
    page: int | None = None
    
class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceDocument]