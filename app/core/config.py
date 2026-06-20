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
    tailscale_consumer_map: dict[str, str] = {
        "100.70.21.69":   "danny",
        "100.122.253.108": "danny",   # GEKtek / d-monet
        "100.66.224.28":  "danny",    # Legion / subsense
        "100.84.163.13":  "jt",
        "100.123.146.66": "kenny",
    }
    alert_threshold_dollars: float = 5.0


settings = Settings()
