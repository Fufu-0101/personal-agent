from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    zhipuai_api_key: str = ""

    # Model
    model_name: str = "gpt-4o"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Memory
    memory_db_path: str = "./data/memory.db"

    model_config = {"protected_namespaces": ()}

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
