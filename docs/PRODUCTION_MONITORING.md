# Production Monitoring & Logging Guide

## Overview

The Kite Services application includes comprehensive logging and monitoring for production debugging and observability.

## Logging Features

### Structured JSON Logging

All logs are structured JSON in production, making them easy to parse and search:

```json
{
  "event": "HTTP Request",
  "logger": "main",
  "level": "info",
  "timestamp": "2026-02-07T15:00:00.000Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "url": "http://localhost:8179/api/market/status",
  "status_code": 200,
  "process_time_ms": 45.23,
  "client_ip": "127.0.0.1",
  "user_agent": "curl/8.7.1"
}
```

### Request Tracking

Every request gets a unique `X-Request-ID` header:
- Automatically generated if not provided
- Included in all log entries for that request
- Returned in response headers for client correlation

### Log Levels

- **ERROR**: Unhandled exceptions, critical failures
- **WARNING**: 4xx HTTP errors, degraded functionality
- **INFO**: Normal operations, HTTP requests (2xx, 3xx)
- **DEBUG**: Detailed debugging (dev only)

### Log Rotation

- Log files rotate at 10MB
- Keeps 5 backup files
- Logs stored in: `logs/kite_services.log`

## Monitoring Endpoints

### `/health` - Health Check

Basic health status:
```bash
curl http://localhost:8179/health
```

Response:
```json
{
  "status": "healthy",
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-02-07T15:00:00.000Z",
  "services": {
    "services": {
      "kite_client": {"status": "running"},
      "yahoo_service": {"status": "running"},
      ...
    }
  }
}
```

### `/health?detailed=true` - Detailed Health

Includes metrics:
```bash
curl http://localhost:8179/health?detailed=true
```

Additional fields:
- `uptime_seconds`: Service uptime
- `total_requests`: Total requests processed
- `successful_requests`: Successful (2xx, 3xx)
- `failed_requests`: Failed (4xx, 5xx)
- `average_response_time_ms`: Average response time
- `error_rate_percent`: Error rate percentage
- `last_error`: Last error message
- `last_error_time`: Timestamp of last error

### `/metrics` - Application Metrics

Comprehensive metrics for monitoring:
```bash
curl http://localhost:8179/metrics
```

Response:
```json
{
  "timestamp": "2026-02-07T15:00:00.000Z",
  "uptime_seconds": 3600.5,
  "status": "healthy",
  "requests": {
    "total": 1250,
    "per_minute": 45,
    "successful": 1200,
    "failed": 50
  },
  "performance": {
    "average_response_time_ms": 125.5,
    "error_rate_percent": 4.0
  },
  "top_endpoints": [
    {"endpoint": "GET /api/market/status", "count": 450},
    {"endpoint": "POST /api/market/quotes", "count": 320},
    ...
  ],
  "status_codes": {
    "200": 1200,
    "400": 30,
    "500": 20
  }
}
```

## Health Status Levels

- **healthy**: Error rate < 5%, all services running
- **degraded**: Error rate 5-10%, some services may be slow
- **unhealthy**: Error rate > 10%, critical issues

## Log Configuration

Environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Log format (json, text)
LOG_FORMAT=json

# Log file path
LOG_FILE_PATH=logs/kite_services.log

# Max log file size (bytes, default 10MB)
LOG_MAX_FILE_SIZE=10485760

# Number of backup files
LOG_BACKUP_COUNT=5

# Include request IDs in logs
LOG_INCLUDE_REQUEST_ID=true

# Include user IDs in logs
LOG_INCLUDE_USER_ID=true

# Include performance metrics
LOG_INCLUDE_PERFORMANCE=true
```

## Production Logging Best Practices

### 1. Use Request IDs

Always include `X-Request-ID` header in client requests:
```bash
curl -H "X-Request-ID: my-request-123" http://localhost:8179/api/market/status
```

### 2. Search Logs by Request ID

```bash
# Find all logs for a specific request
grep "550e8400-e29b-41d4-a716-446655440000" logs/kite_services.log

# Using jq for JSON logs
cat logs/kite_services.log | jq 'select(.request_id == "550e8400-e29b-41d4-a716-446655440000")'
```

### 3. Monitor Error Rates

```bash
# Check error rate from metrics
curl http://localhost:8179/metrics | jq '.performance.error_rate_percent'

# Alert if > 5%
```

### 4. Track Slow Requests

```bash
# Find slow requests (> 1 second)
cat logs/kite_services.log | jq 'select(.process_time_ms > 1000)'
```

### 5. Monitor Top Endpoints

```bash
# See which endpoints are most used
curl http://localhost:8179/metrics | jq '.top_endpoints'
```

## Docker Logs

View container logs:
```bash
# Follow logs
docker compose -f docker-compose.prod.yml logs -f kite-services

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 kite-services

# Filter by level
docker compose -f docker-compose.prod.yml logs kite-services | grep ERROR
```

## Log Aggregation

For production, consider:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (Grafana)
- **CloudWatch** (AWS)
- **Datadog** / **New Relic**

All logs are JSON-formatted and can be easily ingested.

## Alerting

Set up alerts based on:
- Error rate > 5% (degraded)
- Error rate > 10% (unhealthy)
- Average response time > 1000ms
- Service status != "running"

Example monitoring script:
```bash
#!/bin/bash
HEALTH=$(curl -s http://localhost:8179/health?detailed=true)
ERROR_RATE=$(echo $HEALTH | jq -r '.error_rate_percent')

if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
    echo "ALERT: Error rate is $ERROR_RATE%"
    # Send alert (email, Slack, PagerDuty, etc.)
fi
```

## Troubleshooting

### Service Not Responding

1. Check health endpoint:
```bash
curl http://localhost:8179/health
```

2. Check container logs:
```bash
docker compose -f docker-compose.prod.yml logs kite-services
```

3. Check metrics:
```bash
curl http://localhost:8179/metrics
```

### High Error Rate

1. Check last error:
```bash
curl http://localhost:8179/health?detailed=true | jq '.last_error'
```

2. Search logs for errors:
```bash
grep ERROR logs/kite_services.log | tail -20
```

3. Check specific endpoint:
```bash
cat logs/kite_services.log | jq 'select(.url | contains("/api/market/quotes")) | select(.status_code >= 400)'
```

### Performance Issues

1. Check average response time:
```bash
curl http://localhost:8179/metrics | jq '.performance.average_response_time_ms'
```

2. Find slow endpoints:
```bash
cat logs/kite_services.log | jq 'select(.process_time_ms > 500) | {url, process_time_ms}'
```

3. Check top endpoints:
```bash
curl http://localhost:8179/metrics | jq '.top_endpoints'
```

## Production Checklist

- [ ] Log level set to INFO or WARNING
- [ ] Log format set to JSON
- [ ] Log rotation configured
- [ ] Health endpoint accessible
- [ ] Metrics endpoint accessible
- [ ] Request IDs enabled
- [ ] Error tracking working
- [ ] Log aggregation configured (if applicable)
- [ ] Alerts configured
- [ ] Log retention policy set
