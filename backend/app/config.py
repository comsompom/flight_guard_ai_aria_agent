from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FlightGuard Agent API"
    environment: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000

    airia_api_url: str = Field(default="")
    airia_api_key: str = Field(default="")
    airia_router_agent_id: str = Field(default="")
    airia_timeout_seconds: int = 20

    # Optional external APIs for production-ready MCP tools.
    openweather_api_key: str = Field(default="")
    open_topo_base_url: str = Field(default="https://api.opentopodata.org/v1")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
