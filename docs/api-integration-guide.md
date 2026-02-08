# API Integration Guide (Kite-enabled)

Base URL: `http://localhost:8079`

## Health
```bash
curl -s http://localhost:8079/health | jq
```

## UI Market Overview (Top 5 Indexes)
```bash
curl -s http://localhost:8079/api/ui/market-overview | jq '.indexes'
```
- Returns: name, level, change %, intelligent `market_status`, `next_open/close`.

## UI Market Summary (Simplified)
```bash
curl -s http://localhost:8079/api/ui/market-summary | jq
```
- Minimal fields for dashboards.

## Real-time Stock Data (Kite)
```bash
curl -s -X POST http://localhost:8079/api/stock-data/real-time \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]}' | jq
```
- Source: Kite Connect (falls back to Yahoo if token invalid)
- Limit: 50 symbols per call

## Market Sentiment
```bash
curl -s http://localhost:8079/api/market-sentiment | jq '{overall: .overall_market_sentiment, count: (.indices|length)}'
```

## Market Context (V2)
```bash
curl -s http://localhost:8079/api/v2/market-context | jq
```

## Market Intelligence (V3)
```bash
curl -s "http://localhost:8079/api/v3/market-intelligence?horizon=swing" | jq
```
- Note: If TA lookback is insufficient in current environment, some sections may be null.

## Data Quality
```bash
curl -s http://localhost:8079/api/data-quality/system-health | jq
```

## Token Management (Kite)
- Check status:
```bash
curl -s http://localhost:8079/api/token/status | jq
```
- Get refresh info (login URL + submit endpoint):
```bash
curl -s http://localhost:8079/api/token/refresh-info | jq
```
- Submit request token to generate access token:
```bash
curl -s -X POST http://localhost:8079/api/token/submit-token \
  -H "Content-Type: application/json" \
  -d '{"request_token": "<REQUEST_TOKEN>"}' | jq
```

## Frontend usage example (fetch)
```javascript
const base = 'http://localhost:8079';
const res = await fetch(`${base}/api/ui/market-overview`);
const data = await res.json();
for (const idx of data.indexes) {
  console.log(`${idx.name}: ${idx.current_level} (${idx.change_percent}%), status=${idx.market_status}`);
}
```

## Notes
- Logging: JSON logs, no secrets printed
- Rate limits: Safe for dashboards; batch stock quotes in one POST
- Environments: Dev 8079, Prod 8179
- Dependencies: Token auto-saved to `data/zerodha_token.json`
