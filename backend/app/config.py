import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # seconds

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


class DevelopmentConfig(Config):
    DEBUG: bool = True


class ProductionConfig(Config):
    DEBUG: bool = False


class TestingConfig(Config):
    TESTING: bool = True
    DB_NAME: str = "enterprise_ai_test"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
