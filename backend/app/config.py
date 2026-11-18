import os
import warnings
from dotenv import load_dotenv

load_dotenv()

_WEAK_SECRETS = {
    "change-me-to-a-random-secret-key",
    "change-me-to-a-random-jwt-secret",
    "dev-secret-key",
    "dev-jwt-secret",
    "REPLACE_WITH_RANDOM_HEX_32",
}


def _require_secret(value: str, name: str) -> str:
    if not value or value in _WEAK_SECRETS or len(value) < 16:
        warnings.warn(
            f"[SECURITY] {name} is weak or default. "
            "Generate a real secret: python -c \"import secrets; print(secrets.token_hex(32))\"",
            stacklevel=3,
        )
    return value


class Config:
    SECRET_KEY: str = _require_secret(
        os.environ.get("FLASK_SECRET_KEY", "dev-secret-key"), "FLASK_SECRET_KEY"
    )
    JWT_SECRET_KEY: str = _require_secret(
        os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"), "JWT_SECRET_KEY"
    )
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    # MySQL
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: int = int(os.environ.get("DB_PORT", 3306))
    DB_NAME: str = os.environ.get("DB_NAME", "enterprise_ai")
    DB_USER: str = os.environ.get("DB_USER", "root")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")

    # LLM
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

    # MLflow
    MLFLOW_TRACKING_URI: str = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001")

    # CORS
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "http://localhost:3000")

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ML_MODELS_DIR: str = os.path.join(BASE_DIR, "..", "ml", "models")
    DOCUMENTS_DIR: str = os.path.join(BASE_DIR, "..", "documents")
    VECTOR_STORE_DIR: str = os.path.join(BASE_DIR, "..", "ml", "data", "vector_store")

    # Security
    MAX_CONTENT_LENGTH: int = int(os.environ.get("MAX_CONTENT_LENGTH", 1_048_576))  # 1 MB

    # Rate limiting
    RATELIMIT_DEFAULT: str = os.environ.get("RATELIMIT_DEFAULT", "60 per minute")
    RATELIMIT_STORAGE_URL: str = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_HEADERS_ENABLED: bool = True


class DevelopmentConfig(Config):
    DEBUG: bool = True


class ProductionConfig(Config):
    DEBUG: bool = False


class TestingConfig(Config):
    TESTING: bool = True
    DB_NAME: str = "enterprise_ai_test"
    # Disable rate limiting in tests
    RATELIMIT_ENABLED: bool = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
