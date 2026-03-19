import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_TOP_K: int = 5
    ISOLATION_FOREST_CONTAMINATION: float = 0.05

    AUDIT_POLICIES_PATH: str = os.path.join(
        os.path.dirname(__file__), "audit", "audit_policies.json"
    )

    # read from .env
    MONGO_URI: str
    MONGO_DB: str

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = "utf-8"

settings = Settings()