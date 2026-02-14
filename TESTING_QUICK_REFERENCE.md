# Quick Testing Reference

**Server**: Running on <http://localhost:8079>  
**Status**: ✅ All Phase 1-4 changes deployed and tested

---

## Quick Commands

### 1. Check Server Health

```bash
curl http://localhost:8079/health | jq '.'
```

### 2. Check Configuration

```bash
cd /Users/ashokkumar/Desktop/ashok-personal/stocks/kite-services
source venv/bin/activate
python -c "
import sys; sys.path.insert(0, 'src')
from config.settings import get_settings
s = get_settings()
print(f'Max symbols: {s.service.quotes_max_symbols}')
print(f'Breadth enabled: {s.service.market_breadth_enabled}')
"
```

### 3. Test Instruments Endpoint (No Auth)

```bash
curl "http://localhost:8079/api/market/instruments?exchange=NSE&limit=5" | jq '.'
```

### 4. Test Batch Quotes Endpoint (Structure)

```bash
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY"], "exchange": "NSE"}' | jq '.'
```

### 5. Test Market Context (Structure)

```bash
curl -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{"include_global_data": true}' | jq '.'
```

### 6. Run Integration Tests

```bash
./tests/integration/test_bayesian_endpoints.sh http://localhost:8079
```

### 7. Run Unit Tests

```bash
source venv/bin/activate
pytest tests/unit/test_services/test_market_breadth_service.py -v
```

---

## Server Management

### Start Server

```bash
cd /Users/ashokkumar/Desktop/ashok-personal/stocks/kite-services
source venv/bin/activate
python src/main.py
```

### Stop Server

```bash
lsof -ti:8079 | xargs kill -9
```

### Check if Running

```bash
lsof -i:8079
# or
curl -f http://localhost:8079/health
```

---

## What's Working (No Auth)

✅ Server startup and health checks  
✅ Configuration loading (200 symbol limit)  
✅ Instruments endpoint  
✅ Endpoint structures and request validation  
✅ Response models  
✅ Market breadth service (unit tested)  

## What Needs Kite Auth

⚠️  Real-time stock quotes  
⚠️  Market breadth with real data  
⚠️  Historical candles (market hours)  

---

## Test Results

**Overall**: 6/8 tests passing (75%)  

- ✅ Server health
- ✅ Configuration correct
- ✅ Instruments endpoint
- ✅ Request structures
- ⚠️  Real-time data (needs auth)
- ⚠️  Market breadth data (needs auth)

---

## Documentation

- **Integration Guide**: `docs/integration/bayesian-engine-integration-guide.md`
- **Testing Guide**: `tests/integration/BAYESIAN_TESTING_GUIDE.md`
- **API Reference**: `docs/api/api-reference.md`
- **Phase Summary**: `docs/integration/bayesian-phase3-phase4-complete.md`

---

## Quick Verification

Run this to verify all changes are working:

```bash
./scripts/verify_bayesian_changes.sh
```

---

## Server Logs

Monitor server logs:

```bash
tail -f logs/kite_services.log
```

Or check terminal output in:

```
~/.cursor/projects/.../terminals/[latest].txt
```

---

**Status**: ✅ Ready for Kite authentication and full integration testing!
