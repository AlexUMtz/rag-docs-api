from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    
    
    class Config:
        env_file = ".env"
        
settings = Settings()
    