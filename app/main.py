from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import documents, qa
from app.core.config import settings

app = FastAPI(
    title="RAG Docs API",
    description="API para Q&A sobre documentos utilizando Retrieval-Augmented Generation (RAG)",
    version="1.0.0"
)

# Rutas de la API
app.include_router(documents.router)
app.include_router(qa.router)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", tags=["general"])
def root():
    return FileResponse("static/index.html")

