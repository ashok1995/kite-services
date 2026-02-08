# 🚀 Production Deployment Guide

**Service:** Kite Trading Services  
**Version:** 1.0.0  
**Port:** 8179 (Production)

---

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Docker Deployment](#docker-deployment)
5. [Health Checks & Monitoring](#health-checks--monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## ✅ PREREQUISITES

### Required Software

- **Docker** >= 20.10
- **Docker Compose** >= 1.29
- **curl** (for health checks)

### Verify Installation

```bash
docker --version
docker-compose --version
```

---

## 🚀 QUICK START (5 Minutes)

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/kite-services
```

### Step 2: Configure Environment

```bash
# Copy production environment template
cp config/production.env .env

# Edit with your credentials
nano .env  # or vim .env
```

**Minimum required configuration:**
```bash
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
```

### Step 3: Deploy

```bash
# Make deployment script executable
chmod +x deploy-production.sh

# Run deployment
./deploy-production.sh
```

That's it! The service will be running on **port 8179**.

### Step 4: Verify

```bash
# Check health
curl http://localhost:8179/health

# Expected response:
# {"status":"healthy","service":"kite-services",...}
```

---

## ⚙️ CONFIGURATION

### Environment Variables Reference

#### **Service Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | production | Environment name |
| `SERVICE_PORT` | 8179 | Production port |
| `SERVICE_HOST` | 0.0.0.0 | Bind address |
| `DEBUG` | false | Debug mode (never true in prod) |
| `LOG_LEVEL` | INFO | Logging level |

#### **Kite API Credentials** (Required)

| Variable | Required | Description |
|----------|----------|-------------|
| `KITE_API_KEY` | ✅ Yes | Your Kite Connect API key |
| `KITE_API_SECRET` | ✅ Yes | Your Kite Connect API secret |
| `KITE_ACCESS_TOKEN` | No | Auto-generated via login |

#### **Redis Cache**

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | true | Enable caching |
| `REDIS_HOST` | redis | Redis hostname |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_MAX_CONNECTIONS` | 50 | Connection pool size |

#### **Performance Tuning**

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKERS` | 4 | Uvicorn workers |
| `WORKER_TIMEOUT` | 120 | Worker timeout (seconds) |
| `MAX_REQUESTS` | 1000 | Requests before worker restart |

#### **Cache TTLs** (seconds)

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL_PRIMARY_CONTEXT` | 60 | Primary context TTL |
| `CACHE_TTL_DETAILED_CONTEXT` | 300 | Detailed context TTL |
| `CACHE_TTL_INTRADAY_COMPOSITE` | 30 | Intraday context TTL |
| `CACHE_TTL_SWING_COMPOSITE` | 300 | Swing context TTL |
| `CACHE_TTL_LONGTERM_COMPOSITE` | 900 | Long-term context TTL |

---

## 🐳 DOCKER DEPLOYMENT

### Architecture

```
┌─────────────────────────────────────┐
│   Kite Trading Services (8179)      │
│   • FastAPI Application              │
│   • 4 Uvicorn Workers                │
│   • Health Checks Enabled            │
└─────────────────┬───────────────────┘
                  │
                  │ TCP
                  │
          ┌───────▼────────┐
          │  Redis (6379)   │
          │  • LRU Cache    │
          │  • 256MB Limit  │
          └─────────────────┘
```

### Deployment Commands

#### Deploy (First Time or Updates)

```bash
./deploy-production.sh
```

#### Stop Services

```bash
docker-compose -f docker-compose.production.yml down
```

#### Restart Services

```bash
docker-compose -f docker-compose.production.yml restart
```

#### View Logs

```bash
# Follow all logs
docker-compose -f docker-compose.production.yml logs -f

# Follow specific service
docker-compose -f docker-compose.production.yml logs -f kite-services

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100
```

#### Check Status

```bash
docker-compose -f docker-compose.production.yml ps
```

Expected output:
```
NAME                   STATUS              PORTS
kite-services-prod     Up 10 minutes       0.0.0.0:8179->8179/tcp
kite-redis-prod        Up 10 minutes       0.0.0.0:6379->6379/tcp
```

---

## 🏥 HEALTH CHECKS & MONITORING

### Health Endpoint

```bash
curl http://localhost:8179/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "cache_service": {"status": "running"},
    "kite_client": {"status": "running"},
    "yahoo_service": {"status": "running"}
  },
  "timestamp": "2025-10-14T01:00:00"
}
```

### Service-Specific Health Checks

```bash
# Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli ping
# Expected: PONG

# Kite Services
curl -f http://localhost:8179/health || echo "Service unhealthy"
```

### Monitoring Scripts

Create a monitoring script (`monitor-production.sh`):

```bash
#!/bin/bash

while true; do
  clear
  echo "=== Kite Services Production Monitor ==="
  echo ""
  echo "Services Status:"
  docker-compose -f docker-compose.production.yml ps
  echo ""
  echo "Health Check:"
  curl -s http://localhost:8179/health | jq '.status'
  echo ""
  echo "Redis Stats:"
  docker-compose -f docker-compose.production.yml exec -T redis redis-cli INFO stats | grep total_commands_processed
  echo ""
  sleep 5
done
```

---

## 🔧 TROUBLESHOOTING

### Issue: Service Won't Start

**Symptoms:**
```
ERROR: Cannot start service kite-services: ...
```

**Solutions:**

1. **Check Docker is running:**
   ```bash
   docker info
   ```

2. **Check port availability:**
   ```bash
   lsof -i :8179
   # If something is using the port, stop it
   ```

3. **Check logs:**
   ```bash
   docker-compose -f docker-compose.production.yml logs kite-services
   ```

4. **Verify environment variables:**
   ```bash
   cat .env | grep KITE_API_KEY
   ```

---

### Issue: Token Expired

**Symptoms:**
```json
{
  "error": "token_expired",
  "message": "Your Kite access token has expired..."
}
```

**Solution:**

```bash
# 1. Check token status
curl http://localhost:8179/api/auth/status

# 2. Refresh token (see TOKEN_REFRESH_GUIDE.md)
# Open in browser:
# https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY&v=3

# 3. Use request_token to generate access_token
curl -X POST http://localhost:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token": "YOUR_REQUEST_TOKEN"}'
```

---

### Issue: Slow Response Times

**Symptoms:** API calls take > 5 seconds

**Solutions:**

1. **Check cache status:**
   ```bash
   docker-compose -f docker-compose.production.yml exec redis redis-cli INFO stats
   ```

2. **Restart Redis:**
   ```bash
   docker-compose -f docker-compose.production.yml restart redis
   ```

3. **Check resource usage:**
   ```bash
   docker stats
   ```

4. **Increase workers (in .env):**
   ```bash
   WORKERS=8  # Increase from 4
   ```

---

### Issue: High Memory Usage

**Solution:**

1. **Restart services:**
   ```bash
   docker-compose -f docker-compose.production.yml restart
   ```

2. **Adjust Redis memory limit (in docker-compose.production.yml):**
   ```yaml
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

3. **Reduce cache TTLs (in .env):**
   ```bash
   CACHE_TTL_PRIMARY_CONTEXT=30  # Reduce from 60
   ```

---

## 🔄 MAINTENANCE

### Daily Tasks

#### Check Service Health
```bash
curl http://localhost:8179/health
```

#### Refresh Kite Token (Before 6:00 AM IST)
```bash
# Token expires daily at 6:00 AM IST
# Refresh proactively between 5:30-5:55 AM
```

### Weekly Tasks

#### Review Logs
```bash
# Check for errors
docker-compose -f docker-compose.production.yml logs --tail=1000 | grep ERROR

# Check for warnings
docker-compose -f docker-compose.production.yml logs --tail=1000 | grep WARN
```

#### Backup Data
```bash
# Backup token and database
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Monthly Tasks

#### Update Dependencies
```bash
# Pull latest Python packages
docker-compose -f docker-compose.production.yml build --no-cache

# Restart services
./deploy-production.sh
```

#### Clean Up Old Logs
```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 📊 PERFORMANCE BENCHMARKS

### Expected Performance (Production)

| Metric | Value |
|--------|-------|
| **Startup Time** | < 40 seconds |
| **Health Check Response** | < 50ms |
| **Primary Context (cached)** | < 100ms |
| **Full Context (cached)** | < 150ms |
| **Full Context (uncached)** | < 15s |
| **Memory Usage** | 1-2GB |
| **CPU Usage (idle)** | < 5% |
| **CPU Usage (load)** | < 50% |

### Optimization Checklist

- [ ] Redis caching enabled
- [ ] Appropriate number of workers (1-2 per CPU core)
- [ ] Cache TTLs optimized for your use case
- [ ] Logs not set to DEBUG in production
- [ ] Resource limits set in docker-compose
- [ ] Health checks configured

---

## 🔐 SECURITY CHECKLIST

### Pre-Production

- [ ] `.env` file not committed to git
- [ ] Strong, unique API credentials
- [ ] CORS configured for specific domains (not *)
- [ ] HTTPS enabled (if exposing to internet)
- [ ] Rate limiting enabled
- [ ] Non-root user in Docker container
- [ ] Latest security patches applied

### Production

- [ ] Firewall configured
- [ ] Only necessary ports exposed
- [ ] Regular backups configured
- [ ] Monitoring & alerting setup
- [ ] Incident response plan documented

---

## 📞 SUPPORT

### Quick Reference

| Resource | Location |
|----------|----------|
| **API Integration Guide** | `docs/API_INTEGRATION_GUIDE_PRODUCTION.md` |
| **Token Refresh Guide** | `TOKEN_REFRESH_GUIDE.md` |
| **Error Handling** | `GRACEFUL_TOKEN_EXPIRY_GUIDE.md` |
| **Caching Strategy** | `CACHE_STRATEGY_DETAILED.md` |

### Deployment Checklist

```
Pre-Deployment:
□ Docker installed and running
□ .env file configured with Kite credentials
□ Ports 8179 and 6379 available
□ Sufficient disk space (> 5GB)
□ Sufficient memory (> 2GB)

Deployment:
□ Run ./deploy-production.sh
□ Verify health endpoint responds
□ Check all services are running
□ Verify Redis connectivity
□ Test token status endpoint

Post-Deployment:
□ Monitor logs for errors
□ Refresh Kite token if needed
□ Test a sample API call
□ Set up monitoring/alerts
□ Document deployment date
```

---

**Status:** ✅ **PRODUCTION-READY**  
**Version:** 1.0.0  
**Last Updated:** October 14, 2025

