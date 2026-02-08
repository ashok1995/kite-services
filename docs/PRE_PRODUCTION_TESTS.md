# 🚀 Pre-Production Test Suite

Comprehensive validation tests that **must pass** before every production deployment.

## 🎯 Overview

This test suite validates all critical functionality of the Kite Services API to ensure production readiness:

- ✅ **Core Market Context** - Primary data source for ML/trading systems
- ✅ **All Trading Styles** - Intraday, Swing, Long-term contexts
- ✅ **Performance** - Response times under acceptable limits
- ✅ **Error Handling** - Graceful failure and proper error messages
- ✅ **Data Quality** - Real data percentages and transparency
- ✅ **API Documentation** - OpenAPI spec availability

## 📋 Test Scripts

### 1. Quick Production Check (Recommended)
```bash
./pre_production_checklist.sh
```
**What it tests:**
- Service health
- Primary context functionality
- Full context with all features
- Data contract validation
- Performance benchmarks
- Error handling
- API documentation

**Exit codes:**
- `0` = ✅ Ready for production
- `1` = ❌ Not ready (fix issues first)

### 2. Comprehensive Test Suite
```bash
python3 pre_production_tests.py
```
**What it tests:**
- All enhanced context scenarios
- Quotes endpoint functionality
- Stock analysis endpoint
- Error handling scenarios
- Performance metrics

### 3. Production Readiness Check
```bash
python3 production_readiness_check.py
```
**What it tests:**
- Core functionality required for production
- Optional features (quotes, stock analysis)
- Overall deployment readiness assessment

## 🎯 Test Scenarios

### Enhanced Context Tests (MUST PASS)

| Scenario | Description | Critical For |
|----------|-------------|--------------|
| Primary Only | Basic market overview | ML feature extraction |
| Primary + Detailed | Market + technical analysis | Trading decisions |
| Full Context (Intraday) | Complete intraday setup | Day trading systems |
| Full Context (Swing) | Swing trading context | Position trading |
| Full Context (Long-term) | Investment context | Portfolio management |

### Optional Tests (NICE TO HAVE)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/api/market/quotes` | Multiple stock quotes | Requires valid Kite token |
| `/api/analysis/stock` | Single stock analysis | Requires valid Kite token |

## 📊 Success Criteria

### Core Requirements (MUST PASS)
- ✅ Service health check passes
- ✅ Primary context returns real market data
- ✅ All context levels (Primary/Detailed/Intraday/Swing/Long-term) work
- ✅ Response time < 5 seconds
- ✅ Data contract version 1.0.0 valid
- ✅ Error handling provides clear messages
- ✅ OpenAPI documentation available

### Performance Benchmarks
- **Primary Context**: < 1 second
- **Full Context**: < 5 seconds
- **Cache Hit**: Should improve performance on subsequent calls

### Data Quality Standards
- **Real Data %**: > 20% (acceptable with token issues)
- **Contract Version**: 1.0.0
- **Error Rate**: < 5% for core functionality

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Not Starting
```bash
# Check logs
tail -f logs/consolidated_api.log

# Restart service
./start_consolidated_api.sh
```

#### 2. Token Issues (Quotes/Stock Analysis Failing)
```bash
# Check auth status
curl http://localhost:8079/api/auth/status

# Refresh token (requires manual intervention)
# Use Kite Connect web interface to generate new token
```

#### 3. Performance Issues
```bash
# Check cache status
curl -s http://localhost:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true}' | jq '.cache_hit'

# Monitor Redis if performance degrades
```

#### 4. Data Quality Issues
```bash
# Check data sources
curl -s http://localhost:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true}' | jq '.data_quality'
```

## 🚀 Production Deployment Workflow

### Before Deployment
1. **Run Quick Check**: `./pre_production_checklist.sh`
2. **Run Full Tests**: `python3 pre_production_tests.py`
3. **Verify Token**: Ensure Kite token is valid for quotes/analysis
4. **Check Performance**: Ensure < 5s response times

### During Deployment
1. **Deploy to Production**: Use `deploy-production.sh`
2. **Health Check**: Verify service starts on port 8179
3. **Token Refresh**: Update Kite token in production environment

### After Deployment
1. **Monitor Logs**: Check for errors in production logs
2. **Performance Monitor**: Track response times and cache hits
3. **Data Quality**: Monitor real data percentages

## 📈 Monitoring in Production

### Key Metrics to Track
```bash
# Response times
curl -s http://localhost:8179/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true}' | jq '.processing_time_ms'

# Cache performance
curl -s http://localhost:8179/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true}' | jq '.cache_hit'

# Data quality
curl -s http://localhost:8179/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true}' | jq '.data_quality.real_data_percentage'
```

### Alert Thresholds
- **Response Time**: > 10 seconds → Investigate
- **Error Rate**: > 5% → Check service health
- **Real Data %**: < 20% → Check Kite token
- **Cache Hit Rate**: < 50% → Monitor Redis

## ✅ Validation Checklist

- [ ] Service health check passes
- [ ] Primary context returns data
- [ ] All context levels work (Primary/Detailed/Intraday/Swing/Long-term)
- [ ] Response time < 5 seconds
- [ ] Data contract version 1.0.0 valid
- [ ] Error handling works
- [ ] OpenAPI docs available
- [ ] Quotes endpoint works (optional)
- [ ] Stock analysis works (optional)

## 🎉 Ready for Production!

When all tests pass, your Kite Services API is ready for production deployment:

- ✅ **Core functionality verified**
- ✅ **Performance benchmarks met**
- ✅ **Error handling implemented**
- ✅ **Data quality transparent**
- ✅ **API documentation complete**

**Deploy with confidence!** 🚀
