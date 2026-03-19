import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_TOP_K: int = 5
    ISOLATION_FOREST_CONTAMINATION: float = 0.05
    AUDIT_POLICIES_PATH: str = os.path.join(
        os.path.dirname(__file__), "audit", "audit_policies.json"
    )
    MONGO_URI: str = "mongodb+srv://admin:admin@lit-coders.dcuhn.mongodb.net/?retryWrites=true&w=majority&appName=lit-coders"
    MONGO_DB: str = "error_stupifyed"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = "utf-8"


settings = Settings()
