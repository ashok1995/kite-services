"""
Configuration Settings for Kite Services
========================================

Centralized configuration management using Pydantic Settings.
Supports environment variables, .env files, and default values.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Union, Any
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


def _parse_list_from_str(v: Union[str, List[str]]) -> List[str]:
    """Parse List[str] from string (JSON, comma-separated, or single value)."""
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        v = v.strip()
        # Try JSON first
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        # Fall back to comma-separated
        if "," in v:
            return [item.strip() for item in v.split(",") if item.strip()]
        # Single value
        if v:
            return [v]
    # Default
    return ["*"]

# Load environment variables from .env file
# Get the project root directory (parent of 'src')
_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.parent  # Go up from config/ to src/
_project_root = _src_dir.parent  # Go up from src/ to project root
_env_file = _project_root / ".env"

# Load .env from project root
load_dotenv(_env_file)


class KiteConfig(BaseSettings):
    """Kite Connect API configuration."""

    api_key: str = Field(default_factory=lambda: os.getenv("KITE_API_KEY", ""))
    api_secret: str = Field(default_factory=lambda: os.getenv("KITE_API_SECRET", ""))
    access_token: str = Field(default_factory=lambda: os.getenv("KITE_ACCESS_TOKEN", ""))

    model_config = {"extra": "ignore"}

    def __init__(self, **data):
        super().__init__(**data)
        # Fallback to access_token.json if env vars not set
        if not self.api_key or not self.access_token:
            self._load_from_json()

    def _load_from_json(self):
        """Load credentials from access_token.json file."""
        try:
            import json
            json_file = Path(__file__).parent.parent / "access_token.json"
            if json_file.exists():
                with open(json_file, 'r') as f:
                    creds = json.load(f)

                if not self.api_key and creds.get("api_key"):
                    self.api_key = creds["api_key"]
                if not self.access_token and creds.get("access_token"):
                    self.access_token = creds["access_token"]
                if not self.api_secret and creds.get("api_secret"):
                    self.api_secret = creds["api_secret"]

                # Update the settings object
                object.__setattr__(self, 'api_key', self.api_key)
                object.__setattr__(self, 'access_token', self.access_token)
                object.__setattr__(self, 'api_secret', self.api_secret)

        except Exception as e:
            pass  # Silently fail, credentials might be set via env vars
    
    # Connection settings
    reconnect_interval: int = Field(30, env="KITE_RECONNECT_INTERVAL")
    max_reconnect_attempts: int = Field(5, env="KITE_MAX_RECONNECT_ATTEMPTS")
    tick_mode: str = Field("full", env="KITE_TICK_MODE")
    subscription_mode: str = Field("mode_quote", env="KITE_SUBSCRIPTION_MODE")
    
    # Credentials file
    credentials_file: str = Field("access_token.json", env="KITE_CREDENTIALS_FILE")


class YahooConfig(BaseSettings):
    """Yahoo Finance API configuration."""
    
    api_key: Optional[str] = Field(None, env="YAHOO_API_KEY")
    base_url: str = Field("https://query1.finance.yahoo.com", env="YAHOO_BASE_URL")
    timeout: int = Field(30, env="YAHOO_TIMEOUT")
    rate_limit: int = Field(100, env="YAHOO_RATE_LIMIT")  # requests per minute
    
    model_config = {"extra": "ignore"}


class TradingConfig(BaseSettings):
    """Trading configuration."""
    
    initial_capital: float = Field(100000.0, env="INITIAL_CAPITAL")
    max_positions: int = Field(10, env="MAX_POSITIONS")
    position_size_percent: float = Field(0.1, env="POSITION_SIZE_PERCENT")
    stop_loss_percent: float = Field(0.05, env="STOP_LOSS_PERCENT")
    take_profit_percent: float = Field(0.15, env="TAKE_PROFIT_PERCENT")
    
    model_config = {"extra": "ignore"}
    
    # Risk management
    max_daily_loss: float = Field(5000.0, env="MAX_DAILY_LOSS")
    max_position_value: float = Field(20000.0, env="MAX_POSITION_VALUE")
    
    # Strategy settings
    rsi_period: int = Field(14, env="RSI_PERIOD")
    sma_periods: List[int] = Field([5, 20, 50], env="SMA_PERIODS")
    bollinger_period: int = Field(20, env="BOLLINGER_PERIOD")
    bollinger_std: float = Field(2.0, env="BOLLINGER_STD")
    atr_period: int = Field(14, env="ATR_PERIOD")


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    url: str = Field("sqlite+aiosqlite:///../data/kite_services.db", env="DATABASE_URL")
    echo: bool = Field(False, env="DATABASE_ECHO")
    pool_size: int = Field(5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    
    model_config = {"extra": "ignore"}


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = Field("json", env="LOG_FORMAT")  # json or text
    file_path: str = Field("logs/kite_services.log", env="LOG_FILE_PATH")
    max_file_size: int = Field(10485760, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    model_config = {"extra": "ignore"}
    
    # Structured logging
    include_request_id: bool = Field(True, env="LOG_INCLUDE_REQUEST_ID")
    include_user_id: bool = Field(True, env="LOG_INCLUDE_USER_ID")
    include_performance: bool = Field(True, env="LOG_INCLUDE_PERFORMANCE")


class ServiceConfig(BaseSettings):
    """Service configuration."""
    
    name: str = Field("kite-services", env="SERVICE_NAME")
    version: str = Field("1.0.0", env="SERVICE_VERSION")
    host: str = Field("0.0.0.0", env="SERVICE_HOST")
    port: int = Field(8079, env="SERVICE_PORT")  # DEV on 8079, PROD on 8179
    workers: int = Field(1, env="SERVICE_WORKERS")
    
    model_config = {"extra": "ignore"}
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    
    # CORS - store as Optional[str] to avoid JSON parsing, then convert via computed fields
    cors_origins_raw: Optional[str] = Field(default=None, env="CORS_ORIGINS")
    cors_methods_raw: Optional[str] = Field(default=None, env="CORS_METHODS")
    cors_headers_raw: Optional[str] = Field(default=None, env="CORS_HEADERS")
    
    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from env var."""
        if self.cors_origins_raw:
            return _parse_list_from_str(self.cors_origins_raw)
        return ["*"]
    
    @computed_field
    @property
    def cors_methods(self) -> List[str]:
        """Parse CORS methods from env var."""
        if self.cors_methods_raw:
            return _parse_list_from_str(self.cors_methods_raw)
        return ["*"]
    
    @computed_field
    @property
    def cors_headers(self) -> List[str]:
        """Parse CORS headers from env var."""
        if self.cors_headers_raw:
            return _parse_list_from_str(self.cors_headers_raw)
        return ["*"]
    
    # Rate limiting
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")

    # Quotes endpoint limits
    quotes_max_symbols: int = Field(50, env="QUOTES_MAX_SYMBOLS")


class RedisConfig(BaseSettings):
    """Redis configuration for caching and background tasks."""
    
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    model_config = {"extra": "ignore"}
    
    # Connection settings
    max_connections: int = Field(10, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(30, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(30, env="REDIS_SOCKET_CONNECT_TIMEOUT")


class MonitoringConfig(BaseSettings):
    """Monitoring and metrics configuration."""
    
    enabled: bool = Field(True, env="MONITORING_ENABLED")
    prometheus_port: int = Field(8081, env="PROMETHEUS_PORT")
    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    
    model_config = {"extra": "ignore"}
    
    # Alerting
    alert_webhook_url: Optional[str] = Field(None, env="ALERT_WEBHOOK_URL")
    alert_email: Optional[str] = Field(None, env="ALERT_EMAIL")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Sub-configurations
    kite: KiteConfig = Field(default_factory=KiteConfig)
    yahoo: YahooConfig = Field(default_factory=YahooConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8", 
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings


# Convenience functions for common settings
def get_kite_config() -> KiteConfig:
    """Get Kite configuration."""
    return get_settings().kite


def get_trading_config() -> TradingConfig:
    """Get trading configuration."""
    return get_settings().trading


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return get_settings().database


def is_production() -> bool:
    """Check if running in production environment."""
    return get_settings().service.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return get_settings().service.environment.lower() == "development"


# Example usage and validation
if __name__ == "__main__":
    # Load and validate settings
    settings = get_settings()
    
    print(f"Service: {settings.service.name} v{settings.service.version}")
    print(f"Environment: {settings.service.environment}")
    print(f"Port: {settings.service.port}")
    print(f"Debug: {settings.service.debug}")
    
    # Validate Kite credentials
    if settings.kite.api_key and settings.kite.access_token:
        print("✅ Kite credentials configured")
    else:
        print("⚠️ Kite credentials missing")
    
    # Validate database
    print(f"Database: {settings.database.url}")
    
    # Validate trading config
    print(f"Initial Capital: ₹{settings.trading.initial_capital:,.2f}")
    print(f"Max Positions: {settings.trading.max_positions}")
