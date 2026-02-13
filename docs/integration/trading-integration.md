# Trading & Opportunities Integration Guide

Base URL: `http://localhost:8079` (dev) | `http://YOUR_HOST:8179` (prod)

## Endpoints

### 1. GET /api/trading/status

Portfolio, positions, holdings, P&L.

**cURL:**

```bash
curl -s "http://localhost:8079/api/trading/status"
```

**Response 200:**

```json
{
  "success": true,
  "authenticated": true,
  "user_id": "AB1234",
  "enabled": false,
  "positions": [],
  "holdings": [],
  "total_positions": 0,
  "total_holdings": 0,
  "total_pnl": null,
  "day_pnl": null,
  "processing_time_ms": 45.2,
  "timestamp": "2024-01-15T14:30:00Z",
  "message": null
}
```

### 2. POST /api/opportunities/quick

Quick money-making opportunities – breakout/reversal/momentum signals.

**Request:**

```json
{
  "symbols": ["NSE:NIFTY 50", "NSE:NIFTY BANK"],
  "timeframe": "5minute",
  "opportunity_types": ["breakout", "reversal", "momentum"]
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/opportunities/quick" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["NSE:NIFTY 50"], "timeframe": "5minute"}'
```

**Response 200:**

```json
{
  "success": true,
  "opportunities": [],
  "processing_time_ms": 250.0,
  "message": null
}
```

Requires Kite Connect authentication; returns 500 if not configured.
