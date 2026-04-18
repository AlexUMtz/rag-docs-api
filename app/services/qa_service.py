from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from app.core.config import settings

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"

def get_vector_store():
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key
    )
    
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )

def ask_question(question: str, document_id: str | None = None) -> dict:
    vector_store = get_vector_store()
    
    # 1. Configurar Retriever
    search_kwargs = {"k": 4}
    if document_id:
        search_kwargs["filter"] = {"document_id": document_id}
        
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    
    # 2. Definir el prompt
    prompt = ChatPromptTemplate.from_template(
    """
    Eres un asistente experto en analizar documentos.
    Responde la pregunta basándote ÚNICAMENTE en el siguiente contexto.
    Si la respuesta no está en el contexto, di claramente que no tienes esa información.

    Contexto:
    {context}

    Pregunta: {question}

    Respuesta:                                             
    """)
    
    # 3. Configurar el LLM
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2
    )
    
    # 4. Construir la cadena LCEL
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # 5. Obtener chunks recuperados 
    retrieved_docs = retriever.invoke(question)
    
    # 6.Ejecutar cadena
    answer = chain.invoke(question)
    
    # 7. Construir las fuentes
    sources = []
    seen_contents = set()
    for doc in retrieved_docs:
        if doc.page_content not in seen_contents:
            seen_contents.add(doc.page_content)
            sources.append({
                "content": doc.page_content[:300],
                "filename": doc.metadata.get("filename", "unknown"),
                "page": doc.metadata.get("page", None)
            })
            
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }
    
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)