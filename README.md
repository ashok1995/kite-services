# Kite Services - Independent Market Context & Trading Service

## 🎯 **Overview**

Independent service that provides comprehensive market context using Kite Connect and Yahoo Finance APIs, with intelligent trading decisions, position tracking, and stop-loss/target management with performance-based updates.

## 🏗️ **Architecture**

### **Core Services**
- **Market Context Service** - Real-time market data from Kite + Yahoo Finance
- **Intelligent Trading Engine** - Smart trading decisions with contextual analysis
- **Position Tracking Service** - Real-time position monitoring and management
- **Stop-loss & Target Manager** - Dynamic updates based on performance metrics
- **Performance Analytics** - Trading performance tracking and optimization

### **Key Features**
- ✅ Real-time market data streaming (Kite WebSocket)
- ✅ Yahoo Finance integration for broader market context
- ✅ Intelligent position tracking with risk management
- ✅ Dynamic stop-loss and target adjustments
- ✅ Performance-based decision making
- ✅ Paper trading with ML optimization
- ✅ Contextual bandit for trading decisions
- ✅ Comprehensive logging and monitoring

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- Kite Connect API credentials
- Virtual environment

### **Installation**
```bash
# Clone and setup
cd kite-services
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp env/env.example .env
# Edit .env with your Kite API credentials

# Run the service
python src/main.py
```

### **Docker Deployment**
```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 📡 **API Endpoints**

### **Market Context**
- `GET /api/market/context` - Current market context
- `GET /api/market/status` - Market status and hours
- `GET /api/market/instruments/{symbol}` - Instrument details

### **Trading Intelligence**
- `POST /api/trading/analyze` - Analyze trading opportunities
- `GET /api/trading/positions` - Current positions
- `POST /api/trading/execute` - Execute trading decisions
- `GET /api/trading/performance` - Performance metrics

### **Position Management**
- `GET /api/positions/active` - Active positions
- `PUT /api/positions/{id}/stoploss` - Update stop-loss
- `PUT /api/positions/{id}/target` - Update target
- `GET /api/positions/{id}/performance` - Position performance

### **Real-time Data**
- `WS /ws/market-data` - Real-time market data stream
- `WS /ws/positions` - Position updates stream
- `WS /ws/alerts` - Trading alerts stream

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Kite API
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token

# Yahoo Finance
YAHOO_API_KEY=your_yahoo_key  # Optional

# Service Configuration
SERVICE_PORT=8080
LOG_LEVEL=INFO
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///data/kite_services.db

# Trading Configuration
INITIAL_CAPITAL=100000
MAX_POSITIONS=10
POSITION_SIZE_PERCENT=0.1
STOP_LOSS_PERCENT=0.05
TAKE_PROFIT_PERCENT=0.15
```

## 📊 **Service Architecture**

```
kite-services/
├── src/
│   ├── api/                    # FastAPI routes
│   │   ├── market_routes.py
│   │   ├── trading_routes.py
│   │   ├── position_routes.py
│   │   └── websocket_routes.py
│   ├── services/               # Core business logic
│   │   ├── market_context.py
│   │   ├── intelligent_trading.py
│   │   ├── position_tracker.py
│   │   ├── stoploss_manager.py
│   │   └── performance_analyzer.py
│   ├── models/                 # Pydantic models
│   │   ├── market_models.py
│   │   ├── trading_models.py
│   │   └── position_models.py
│   ├── core/                   # Core utilities
│   │   ├── kite_client.py
│   │   ├── yahoo_client.py
│   │   └── database.py
│   ├── config/                 # Configuration
│   │   ├── settings.py
│   │   └── logging_config.py
│   └── main.py                 # Application entry point
├── tests/                      # Test suite
├── docs/                       # Documentation
├── logs/                       # Application logs
├── data/                       # Data storage
└── env/                        # Environment configs
```

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=src tests/
```

## 📈 **Monitoring & Logging**

- **Structured JSON Logging** - All operations logged with context
- **Performance Metrics** - Real-time performance tracking
- **Health Checks** - Service health monitoring
- **Error Tracking** - Comprehensive error logging and alerts

## 🔄 **Integration with Other Services**

This service is designed to work independently but can integrate with:
- **Seed Stocks Service** - For recommendation inputs
- **Strategy Service** - For trading strategy configurations
- **Notification Service** - For alerts and updates

## 📝 **Development**

### **Code Standards**
- Python 3.11+ with type hints
- Pydantic models for all data structures
- Async/await for I/O operations
- Comprehensive error handling
- Structured logging

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 **Support**

For issues and support, please check the documentation or create an issue in the repository.
