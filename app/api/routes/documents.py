import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion import ingest_document, list_documents, delete_document
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = "uploads"

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = ingest_document(file_path, file.filename)
    
    os.remove(file_path)
    
    return DocumentResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        chunk_count=result["chunk_count"],
        message=f"Document '{result['filename']}' ingested successfully with {result['chunk_count']} chunks."
    )

@router.get("/")
async def get_documents():
    documents = list_documents()
    return {"documents": documents}

@router.delete("/{document_id}")
async def remove_document(document_id: str):
    deleted = delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"message": f"Documento {document_id} eliminado correctamente"}