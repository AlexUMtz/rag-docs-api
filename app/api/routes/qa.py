from fastapi import APIRouter, HTTPException
from app.services.qa_service import ask_question
from app.schemas.qa import QuestionRequest, AnswerResponse, SourceDocument

router = APIRouter(prefix="/api/qa", tags=["qa"])

@router.post("/ask", response_model=AnswerResponse)
async def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = ask_question(
        question=request.question,
        document_id=request.document_id
    )

    sources = [SourceDocument(**s) for s in result["sources"]]

    return AnswerResponse(
        question=result["question"],
        answer=result["answer"],
        sources=sources
    )