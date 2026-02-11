# Configuration Guide

## Overview

Kite Services uses environment-based configuration with Pydantic Settings for type-safe, validated configuration management.

## Configuration File

**Location**: `src/config/settings.py`

All configuration is managed through environment variables, with sensible defaults for development.

## Environment Variables

### Kite Connect Configuration

```bash
# Required for production
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here  
KITE_ACCESS_TOKEN=your_access_token_here

# Optional - Connection settings
KITE_RECONNECT_INTERVAL=30              # Seconds between reconnection attempts
KITE_MAX_RECONNECT_ATTEMPTS=5           # Max reconnection attempts
KITE_TICK_MODE=full                     # full | quote | ltp
KITE_SUBSCRIPTION_MODE=mode_quote       # WebSocket subscription mode
KITE_CREDENTIALS_FILE=access_token.json # Legacy token storage file
KITE_TOKEN_FILE=~/.kite-services/kite_token.json  # Outside project; survives git pull
```

### Yahoo Finance Configuration

```bash
# Optional - Yahoo Finance settings
YAHOO_API_KEY=                          # Not required (public API)
YAHOO_BASE_URL=https://query1.finance.yahoo.com
YAHOO_TIMEOUT=30                        # Request timeout in seconds
YAHOO_RATE_LIMIT=100                    # Requests per minute
```

### Service Configuration

```bash
# Service Settings
SERVICE_NAME=kite-services
SERVICE_VERSION=1.0.0
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8079                       # Dev: 8079, Prod: 8179
SERVICE_WORKERS=1                       # Number of worker processes

# Environment
ENVIRONMENT=development                 # development | production
DEBUG=True                              # Enable debug mode
```

### CORS Configuration

```bash
# CORS Settings (comma-separated)
CORS_ORIGINS=*                          # Allowed origins
CORS_METHODS=*                          # Allowed methods  
CORS_HEADERS=*                          # Allowed headers
```

### Database Configuration

```bash
# Database Settings
DATABASE_URL=sqlite:///data/kite_services.db
DATABASE_ECHO=False                     # Log SQL queries
DATABASE_POOL_SIZE=5                    # Connection pool size
DATABASE_MAX_OVERFLOW=10                # Max overflow connections
```

### Logging Configuration

```bash
# Logging Settings
LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                         # json | text
LOG_FILE_PATH=logs/kite_services.log    # Log file location
LOG_MAX_FILE_SIZE=10485760              # 10MB per file
LOG_BACKUP_COUNT=5                      # Number of backup files

# Structured Logging Options
LOG_INCLUDE_REQUEST_ID=True
LOG_INCLUDE_USER_ID=True
LOG_INCLUDE_PERFORMANCE=True
```

### Trading Configuration

```bash
# Trading Parameters (Future use)
INITIAL_CAPITAL=100000.0
MAX_POSITIONS=10
POSITION_SIZE_PERCENT=0.1               # 10% per position
STOP_LOSS_PERCENT=0.05                  # 5% stop loss
TAKE_PROFIT_PERCENT=0.15                # 15% take profit
MAX_DAILY_LOSS=5000.0
MAX_POSITION_VALUE=20000.0

# Technical Analysis Parameters
RSI_PERIOD=14
SMA_PERIODS=5,20,50                     # Comma-separated
BOLLINGER_PERIOD=20
BOLLINGER_STD=2.0
ATR_PERIOD=14
```

### Redis Configuration (Future)

```bash
# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                         # Optional
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=30
REDIS_SOCKET_CONNECT_TIMEOUT=30
```

### Monitoring Configuration

```bash
# Monitoring & Metrics
MONITORING_ENABLED=True
PROMETHEUS_PORT=8081                    # Metrics endpoint port
HEALTH_CHECK_INTERVAL=30                # Seconds between health checks

# Alerting (Optional)
ALERT_WEBHOOK_URL=                      # Webhook for alerts
ALERT_EMAIL=                            # Email for alerts
```

### Rate Limiting

```bash
# Rate Limiting Settings
RATE_LIMIT_REQUESTS=100                 # Max requests
RATE_LIMIT_WINDOW=60                    # Time window in seconds
```

---

## Configuration Files

### envs/ folder

Single source for all environment config. No other env files.

| File | Port | Use |
|------|------|-----|
| `envs/development.env` | 8079 | Local development |
| `envs/staging.env` | 8279 | Local staging |
| `envs/production.env` | 8179 | Production (VM) |

Settings loads `envs/{ENVIRONMENT}.env` based on `ENVIRONMENT` (default: development).

```bash
# Edit env for your environment (service config only)
vim envs/development.env

# Kite credentials go in ~/.kite-services/kite_token.json (not env)
cp kite_token.json.example ~/.kite-services/kite_token.json
# Edit with api_key, api_secret; access_token added after login
```

---

## Usage in Code

### Accessing Configuration

```python
from config.settings import get_settings, get_kite_config

# Get all settings
settings = get_settings()
print(settings.service.port)  # 8079

# Get specific config section
kite_config = get_kite_config()
print(kite_config.api_key)
```

### Configuration Structure

```python
class Settings(BaseSettings):
    kite: KiteConfig           # Kite Connect settings
    yahoo: YahooConfig         # Yahoo Finance settings
    trading: TradingConfig     # Trading parameters
    database: DatabaseConfig   # Database settings
    logging: LoggingConfig     # Logging configuration
    service: ServiceConfig     # Service settings
    redis: RedisConfig         # Redis settings
    monitoring: MonitoringConfig  # Monitoring config
```

### Type Safety

All configuration is type-checked:

```python
settings = get_settings()

# Type-safe access
port: int = settings.service.port
debug: bool = settings.service.debug
origins: List[str] = settings.service.cors_origins

# Validated values
assert settings.service.port >= 1024  # Validated by Pydantic
```

---

## Environment-Specific Configuration

### Development (envs/development.env)

```bash
ENVIRONMENT=development
SERVICE_PORT=8079
DEBUG=True
```

### Staging (envs/staging.env)

```bash
ENVIRONMENT=staging
SERVICE_PORT=8279
```

### Production (envs/production.env)

```bash
ENVIRONMENT=production
SERVICE_PORT=8179
DEBUG=false
```

Docker Compose uses `env_file: envs/production.env`.

---

## Configuration Validation

### Automatic Validation

Pydantic validates configuration on startup:

```python
# Invalid configuration
SERVICE_PORT="invalid"  # ❌ Will raise ValidationError

# Valid configuration
SERVICE_PORT=8079       # ✅ Parsed as int
```

### Required vs Optional

```python
class KiteConfig(BaseSettings):
    api_key: str = Field("", env="KITE_API_KEY")  # Optional (default "")
    api_secret: str = Field(..., env="KITE_API_SECRET")  # Required
```

### Custom Validation

```python
@validator('port')
def port_must_be_valid(cls, v):
    if v < 1024 or v > 65535:
        raise ValueError('Port must be between 1024 and 65535')
    return v
```

---

## Best Practices

### 1. Never Hardcode Credentials

```python
# ❌ Bad
kite_api_key = "abc123xyz"

# ✅ Good
kite_api_key = get_settings().kite.api_key
```

### 2. Use Environment Variables

```python
# Set in shell or .env file
export KITE_API_KEY="your_key"

# Access in code
api_key = get_settings().kite.api_key
```

### 3. Provide Defaults

```python
# Good: Sensible default for development
port: int = Field(8079, env="SERVICE_PORT")
```

### 4. Document All Config

```python
class ServiceConfig(BaseSettings):
    port: int = Field(
        8079,
        env="SERVICE_PORT",
        description="HTTP server port (8079=dev, 8179=prod)"
    )
```

### 5. Validate Early

```python
# Validate on startup, not at runtime
settings = get_settings()  # Will raise if invalid
```

---

## Troubleshooting

### Configuration Not Loading

**Problem**: Environment variables not being read

**Solution**:

```bash
# Check .env file exists
ls -la .env

# Verify variable is set
echo $KITE_API_KEY

# Check file encoding
file .env  # Should be ASCII or UTF-8
```

### Type Errors

**Problem**: `ValidationError` on startup

**Solution**:

```python
# Check Pydantic error details
try:
    settings = Settings()
except ValidationError as e:
    print(e.json())  # Shows exactly which fields are invalid
```

### Missing Credentials

**Problem**: API calls failing due to missing credentials

**Solution**:

```python
# Check if credentials are configured
settings = get_settings()
if not settings.kite.api_key:
    logger.error("KITE_API_KEY not configured")
```

---

## Configuration Reference

### Complete Example .env

```bash
# ===========================================
# Kite Services Configuration
# ===========================================

# Kite Connect API
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
KITE_ACCESS_TOKEN=your_access_token

# Service Settings
ENVIRONMENT=production
DEBUG=False
SERVICE_NAME=kite-services
SERVICE_VERSION=1.0.0
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8179
SERVICE_WORKERS=1

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=Content-Type,Authorization

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kite_services
DATABASE_ECHO=False
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=/var/log/kite_services/app.log
LOG_MAX_FILE_SIZE=10485760
LOG_BACKUP_COUNT=10

# Trading (Future Use)
INITIAL_CAPITAL=100000.0
MAX_POSITIONS=10
POSITION_SIZE_PERCENT=0.1

# Monitoring
MONITORING_ENABLED=True
PROMETHEUS_PORT=8081
HEALTH_CHECK_INTERVAL=30

# Redis (Future)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## Security Considerations

### 1. Env Files

`envs/*.env` files are committed as templates.
Edit with real credentials locally; avoid committing secrets.

### 2. Use Secret Management in Production

- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

### 3. Rotate Credentials Regularly

- Kite access tokens expire daily
- API keys should be rotated periodically

### 4. Restrict Access

```bash
# Restrict env file (if containing secrets)
chmod 600 envs/development.env
```

---

## Related Documentation

- [Architecture](architecture.md) - System design
- [APIs Used](apis-used.md) - External API configuration
- [Deployment](production-deployment.md) - Production setup
