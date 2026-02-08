# Kite Services - Trading API

A comprehensive FastAPI-based trading services API for stock market data, analysis, and intelligent trading decisions.

## Features

- 🔐 **Authentication**: Kite Connect OAuth integration
- 📊 **Market Data**: Real-time quotes, historical data, market status
- 🧠 **Market Intelligence**: Context analysis, sentiment, technical indicators
- 💰 **Trading Support**: Position tracking, holdings, opportunities
- 📈 **Monitoring**: Comprehensive logging, metrics, health checks
- 🐳 **Docker**: Production-ready containerization
- 🚀 **CI/CD**: Automated testing and deployment pipeline

## Quick Start

### Development

```bash
# Install dependencies
poetry install

# Run development server
cd src
python main.py

# Server runs on http://localhost:8079
```

### Production

```bash
# Using Docker Compose
docker compose -f docker-compose.prod.yml up -d

# Server runs on http://localhost:8179
```

## API Endpoints

### Core
- `GET /` - Service information
- `GET /health` - Health check
- `GET /health?detailed=true` - Detailed health with metrics
- `GET /metrics` - Application metrics
- `GET /docs` - API documentation (dev only)

### Authentication
- `POST /api/auth/login` - Login with request token
- `GET /api/auth/status` - Authentication status

### Market Data
- `GET /api/market/status` - Market status
- `GET /api/market/instruments` - Available instruments
- `POST /api/market/quotes` - Get quotes
- `POST /api/market/data` - Universal market data

### Analysis
- `POST /api/analysis/context` - Market context
- `POST /api/analysis/stock` - Stock analysis
- `POST /api/analysis/context/enhanced` - Enhanced context
- `POST /api/opportunities/quick` - Quick opportunities

### Trading
- `GET /api/trading/status` - Trading status (positions, holdings)

## Configuration

### Environment Variables

See `config/production.env.example` for all configuration options.

Key variables:
- `KITE_API_KEY` - Kite Connect API key
- `KITE_ACCESS_TOKEN` - Kite Connect access token
- `SERVICE_PORT` - Server port (8079=dev, 8179=prod)
- `ENVIRONMENT` - development or production
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
- `LOG_FORMAT` - json or text

## Development

### Project Structure

```
kite-services/
├── src/                    # Application source
│   ├── api/               # API routes
│   ├── core/              # Core services
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── config/            # Configuration
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                 # Documentation
├── .github/workflows/    # CI/CD pipelines
└── pyproject.toml        # Poetry dependencies
```

### Running Tests

```bash
# All tests
poetry run pytest

# Unit tests only
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# E2E tests
poetry run pytest tests/e2e/

# With coverage
poetry run pytest --cov=src --cov-report=html
```

## CI/CD Pipeline

### Branch Strategy

- **main/master**: Production deployments
- **develop**: Image build + test stage
- **feature/***: Tests only, no deployment

### Pipeline Stages

1. **Lint** - Code quality checks
2. **Unit Tests** - Component tests
3. **Integration Tests** - Service integration
4. **E2E Tests** - End-to-end validation
5. **Build Image** - Docker image creation
6. **Test Image** (develop only) - Container testing
7. **Deploy Production** (main only) - Production deployment
8. **Post-Deployment Tests** (main only) - Smoke tests

See [CI/CD Pipeline Documentation](docs/CI_CD_PIPELINE.md) for details.

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8179/health

# Detailed health with metrics
curl "http://localhost:8179/health?detailed=true"
```

### Metrics

```bash
# Application metrics
curl http://localhost:8179/metrics
```

### Logging

- **Format**: JSON (production), Text (development)
- **Location**: `logs/kite_services.log`
- **Rotation**: 10MB files, 5 backups
- **Request IDs**: All requests tracked with unique IDs

See [Production Monitoring Guide](docs/PRODUCTION_MONITORING.md) for details.

## Deployment

### Production Deployment

Production deployments are automated via GitHub Actions when code is pushed to `main` branch.

Manual deployment:
```bash
ssh root@203.57.85.72
cd /opt/kite-services
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Environment URLs

- **Development**: http://localhost:8079
- **Production**: http://203.57.85.72:8179

## Documentation

- [API Documentation](docs/api.md)
- [Architecture](docs/architecture.md)
- [CI/CD Pipeline](docs/CI_CD_PIPELINE.md)
- [Production Monitoring](docs/PRODUCTION_MONITORING.md)
- [Git Setup](docs/GIT_SETUP.md)

## License

Private project - All rights reserved

## Support

For issues and questions, please open an issue in the repository.
