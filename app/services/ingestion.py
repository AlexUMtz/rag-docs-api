import uuid
import chromadb
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"

def get_vector_store(collection_name: str = COLLECTION_NAME) -> Chroma:
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key
    )
    
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def ingest_document(file_path: str, filename: str) -> dict:
    document_id = str(uuid.uuid4())
    
    # 1. Cargar el PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    # 2. Dividir en chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = splitter.split_documents(pages)
    
    # 3. Agregar metadata a cada chunk
    for chunk in chunks:
        chunk.page_content = " ".join(chunk.page_content.split())
        chunk.metadata["document_id"] = document_id
        chunk.metadata["filename"] = filename
    
    # 4. Guardar en ChromaDB
    vector_store = get_vector_store("documents")
    vector_store.add_documents(chunks)
    
    return {
        "document_id": document_id,
        "filename": filename,
        "chunk_count": len(chunks)
    }
    
    
def list_documents() -> list:
    client = get_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    results = collection.get()
    
    seen = {}
    for metadata in results["metadatas"]:
        doc_id = metadata.get("document_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = metadata.get("filename","unknown")
            
    return [{"document_id": k, "filename": v} for k, v in seen.items()]


def delete_document(document_id: str) -> bool:
    client = get_chroma_client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    results = collection.get(where={"document_id": document_id})

    if not results["ids"]:
        return False
    
    collection.delete(where={"document_id": document_id})
    return True