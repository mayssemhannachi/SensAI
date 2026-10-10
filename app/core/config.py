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
	AI_LLM_BASE_URL: str | None = None
	AI_LLM_API_KEY: str | None = None
	AI_LLM_MODEL: str | None = None
	AI_EMBEDDING_MODEL: str | None = None
	AI_LLM_TIMEOUT_SECONDS: float = 45.0
	AI_EMBEDDING_TIMEOUT_SECONDS: float = 30.0
	AI_RAG_TOP_K: int = 5
	AI_RAG_BATCH_SIZE: int = 32
	AI_SQL_FALLBACK_NOTE_LIMIT: int = 20


settings = Settings()
