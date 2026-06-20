from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API settings
    askedgar_api_key: str = "your-api-key-here"
    fmp_api_key: str = ""
    massive_api_key: str = ""
    askedgar_url: str = "https://eapi.askedgar.io"
    request_timeout: int = 30
    market_strength_db_path: str = "/var/lib/gaplens/market_strength.db"

    # CORS settings
    cors_origins: list = ["*"]

    # Admin dashboard settings
    usage_log_db_path: str = "/var/lib/gaplens/usage_log.db"
    tailscale_consumer_map: dict[str, str] = {}
    alert_threshold_dollars: float = 5.0
    admin_api_key: str = ""


settings = Settings()
