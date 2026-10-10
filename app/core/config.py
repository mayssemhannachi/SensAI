from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", extra="ignore")

	DATABASE_URL: str
	SECRET_KEY: str = "change-me-in-production"
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
	CORS_ORIGINS: list[str] = [
		"http://localhost:3000",
		"http://127.0.0.1:3000",
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	]
	AI_LLM_BASE_URL: str = "http://localhost:11434/v1"
	AI_LLM_API_KEY: str | None = None
	AI_LLM_MODEL: str = "qwen2.5:7b"
	AI_EMBEDDING_MODEL: str = "nomic-embed-text"
	AI_LLM_TIMEOUT_SECONDS: float = Field(default=45.0, gt=0)
	AI_EMBEDDING_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0)
	AI_RAG_TOP_K: int = Field(default=5, gt=0)
	AI_RAG_BATCH_SIZE: int = Field(default=32, gt=0)
	AI_SQL_FALLBACK_NOTE_LIMIT: int = Field(default=20, gt=0)
	AI_COMPARABLE_METRIC_KEYS: list[str] = Field(default_factory=list)


settings = Settings()
