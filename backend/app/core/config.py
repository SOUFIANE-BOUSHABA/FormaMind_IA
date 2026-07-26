from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-change-me-formamind-auth-secret"


class Settings(BaseSettings):
    app_name: str = Field(default="FormaMind AI API", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=True, validation_alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    database_url: str = Field(
        default="sqlite:///./formamind.db",
        validation_alias="DATABASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        validation_alias="CORS_ORIGINS",
    )
    jwt_secret_key: str = Field(
        default=DEVELOPMENT_JWT_SECRET,
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=15,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    max_upload_size_mb: int = Field(default=20, validation_alias="MAX_UPLOAD_SIZE_MB")
    upload_directory: str = Field(
        default="uploads/documents",
        validation_alias="UPLOAD_DIRECTORY",
    )

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="", validation_alias="GEMINI_MODEL")
    chroma_persist_directory: str = Field(
        default="vector_store",
        validation_alias="CHROMA_PERSIST_DIRECTORY",
    )
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="EMBEDDING_MODEL_NAME",
    )
    rag_chunk_size: int = Field(default=800, validation_alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=120, validation_alias="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=5, validation_alias="RAG_TOP_K")
    rag_min_relevance_score: float = Field(
        default=0.24,
        validation_alias="RAG_MIN_RELEVANCE_SCORE",
    )

    assessment_max_questions: int = Field(
        default=20,
        validation_alias="ASSESSMENT_MAX_QUESTIONS",
    )
    assessment_context_top_k: int = Field(
        default=12,
        validation_alias="ASSESSMENT_CONTEXT_TOP_K",
    )
    assessment_agent_temperature: float = Field(
        default=0.2,
        validation_alias="ASSESSMENT_AGENT_TEMPERATURE",
    )
    learning_plan_max_modules: int = Field(
        default=6,
        validation_alias="LEARNING_PLAN_MAX_MODULES",
    )
    learning_plan_max_activities_per_module: int = Field(
        default=5,
        validation_alias="LEARNING_PLAN_MAX_ACTIVITIES_PER_MODULE",
    )
    learning_content_top_k: int = Field(
        default=10,
        validation_alias="LEARNING_CONTENT_TOP_K",
    )
    learning_coach_temperature: float = Field(
        default=0.2,
        validation_alias="LEARNING_COACH_TEMPERATURE",
    )
    default_daily_study_minutes: int = Field(
        default=45,
        validation_alias="DEFAULT_DAILY_STUDY_MINUTES",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value

        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", "prod", "production", "release"}:
            return False

        return True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> Settings:
        if (
            self.app_env != "development"
            and self.jwt_secret_key == DEVELOPMENT_JWT_SECRET
        ):
            msg = "JWT_SECRET_KEY must be configured outside development."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_rag_settings(self) -> Settings:
        if self.rag_chunk_size <= 0:
            msg = "RAG_CHUNK_SIZE must be greater than 0."
            raise ValueError(msg)

        if self.rag_chunk_overlap < 0:
            msg = "RAG_CHUNK_OVERLAP cannot be negative."
            raise ValueError(msg)

        if self.rag_chunk_overlap >= self.rag_chunk_size:
            msg = "RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE."
            raise ValueError(msg)

        if self.rag_top_k <= 0:
            msg = "RAG_TOP_K must be greater than 0."
            raise ValueError(msg)

        if not 0 <= self.rag_min_relevance_score <= 1:
            msg = "RAG_MIN_RELEVANCE_SCORE must be between 0 and 1."
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def validate_assessment_settings(self) -> Settings:
        if self.assessment_max_questions < 3:
            msg = "ASSESSMENT_MAX_QUESTIONS must be at least 3."
            raise ValueError(msg)

        if self.assessment_context_top_k <= 0:
            msg = "ASSESSMENT_CONTEXT_TOP_K must be greater than 0."
            raise ValueError(msg)

        if not 0 <= self.assessment_agent_temperature <= 1:
            msg = "ASSESSMENT_AGENT_TEMPERATURE must be between 0 and 1."
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def validate_learning_plan_settings(self) -> Settings:
        if self.learning_plan_max_modules < 1:
            msg = "LEARNING_PLAN_MAX_MODULES must be greater than 0."
            raise ValueError(msg)

        if self.learning_plan_max_activities_per_module < 1:
            msg = "LEARNING_PLAN_MAX_ACTIVITIES_PER_MODULE must be greater than 0."
            raise ValueError(msg)

        if self.learning_content_top_k <= 0:
            msg = "LEARNING_CONTENT_TOP_K must be greater than 0."
            raise ValueError(msg)

        if not 0 <= self.learning_coach_temperature <= 1:
            msg = "LEARNING_COACH_TEMPERATURE must be between 0 and 1."
            raise ValueError(msg)

        if self.default_daily_study_minutes < 15:
            msg = "DEFAULT_DAILY_STUDY_MINUTES must be at least 15."
            raise ValueError(msg)

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
