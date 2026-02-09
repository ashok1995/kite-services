# Token Management Guide

## Overview

The Kite Services application supports **file-based token management** that allows you to update the access token daily without restarting the service. The service automatically watches the token file and reloads the token when it's updated.

## Token File Location

**Default Location**: `kite_token.json` (in project root)

You can customize the location using the `KITE_TOKEN_FILE` environment variable.

## Token File Format

The token file supports two formats:

### Format 1: JSON Object (Recommended)

```json
{
  "access_token": "your_access_token_here",
  "user_id": "AB1234",
  "user_name": "John Doe",
  "updated_at": "2026-02-08T12:00:00"
}
```

### Format 2: Plain Text

Just the access token as a string:

```
your_access_token_here
```

## Updating the Token

### Method 1: Update Token File Directly

1. **Edit the token file**:
   ```bash
   # Edit kite_token.json
   nano kite_token.json
   # or
   vim kite_token.json
   ```

2. **Update the access_token field**:
   ```json
   {
     "access_token": "new_token_here",
     "updated_at": "2026-02-08T12:00:00"
   }
   ```

3. **Save the file** - The service will automatically detect the change and reload the token!

### Method 2: Use API Endpoint

```bash
# Update token via API
curl -X PUT "http://localhost:8179/api/auth/token?access_token=YOUR_NEW_TOKEN" \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "status": "authenticated",
  "access_token": "YOUR_NEW_TOKEN",
  "user_id": "AB1234",
  "user_name": "John Doe",
  "message": "Token updated successfully"
}
```

### Method 3: Generate New Token via Login

```bash
# Generate new token from request token
curl -X POST "http://localhost:8179/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "request_token": "YOUR_REQUEST_TOKEN",
    "api_secret": "YOUR_API_SECRET"
  }'
```

This will:
1. Generate a new access token
2. Save it to `kite_token.json`
3. Update the service automatically

## Daily Token Update Workflow

### Recommended Daily Process

1. **Get new request token** from Kite Connect login
2. **Generate access token** using the API:
   ```bash
   curl -X POST "http://localhost:8179/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "request_token": "NEW_REQUEST_TOKEN",
       "api_secret": "YOUR_API_SECRET"
     }'
   ```

3. **Or manually update the file**:
   ```bash
   # SSH to production server
   ssh root@203.57.85.72
   
   # Edit token file
   cd /opt/kite-services
   nano kite_token.json
   
   # Update access_token field
   # Save and exit
   ```

4. **Verify token is loaded**:
   ```bash
   curl http://localhost:8179/api/auth/status
   ```

### Automated Daily Update Script

Create a script to automate daily token updates:

```bash
#!/bin/bash
# update_kite_token.sh

# Get new request token (you need to implement this)
REQUEST_TOKEN=$(get_request_token_from_kite)

# Update via API
curl -X POST "http://localhost:8179/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_token\": \"$REQUEST_TOKEN\",
    \"api_secret\": \"$KITE_API_SECRET\"
  }"

echo "✅ Token updated"
```

Add to crontab for daily updates:
```bash
# Update token daily at 9:00 AM
0 9 * * * /path/to/update_kite_token.sh
```

## How It Works

1. **Service Startup**:
   - Service loads token from `kite_token.json` on startup
   - If file doesn't exist, falls back to environment variables

2. **File Watching**:
   - Service watches `kite_token.json` for changes
   - When file is modified, automatically reloads the token

3. **Token Reload**:
   - New token is loaded from file
   - Kite client is updated with new token
   - No service restart required!

## Verification

### Check Token Status

```bash
curl http://localhost:8179/api/auth/status
```

**Response**:
```json
{
  "status": "authenticated",
  "authenticated": true,
  "user_id": "AB1234",
  "user_name": "John Doe",
  "message": "Token is valid and active"
}
```

### Check Service Logs

```bash
# View logs to see token reload
docker compose -f docker-compose.prod.yml logs -f kite-services | grep -i token
```

You should see:
```
✅ Token loaded from kite_token.json
🔄 Token file updated, reloading Kite client...
✅ Kite client token updated
```

## Troubleshooting

### Token Not Loading

1. **Check file exists**:
   ```bash
   ls -la kite_token.json
   ```

2. **Check file permissions**:
   ```bash
   chmod 644 kite_token.json
   ```

3. **Check file format**:
   ```bash
   cat kite_token.json | python3 -m json.tool
   ```

### Token Not Updating

1. **Check file watcher is running**:
   - Check service logs for "Started watching token file"

2. **Verify file change**:
   - Make sure you're editing the correct file
   - Check file modification time: `stat kite_token.json`

3. **Manual reload**:
   - Use API endpoint to update: `PUT /api/auth/token`

### Service Not Detecting Changes

1. **Check file path**:
   - Default: `kite_token.json` in project root
   - Custom: Set `KITE_TOKEN_FILE` environment variable

2. **Check file watcher logs**:
   ```bash
   docker compose logs kite-services | grep -i "watching\|token"
   ```

## Security Best Practices

1. **File Permissions**:
   ```bash
   chmod 600 kite_token.json  # Only owner can read/write
   ```

2. **Don't Commit Token File**:
   - Token file is in `.gitignore`
   - Never commit tokens to Git

3. **Use Environment Variables in Production**:
   - For initial setup, use environment variables
   - Then switch to file-based updates

4. **Rotate Tokens Regularly**:
   - Update token daily
   - Use automated scripts for consistency

## Environment Variables

- `KITE_TOKEN_FILE`: Custom path to token file (default: `kite_token.json`)
- `KITE_ACCESS_TOKEN`: Fallback token from environment (used if file not found)

## API Endpoints

- `PUT /api/auth/token?access_token=TOKEN` - Update token via API
- `POST /api/auth/login` - Generate new token from request token
- `GET /api/auth/status` - Check current token status

## Example: Complete Daily Update

```bash
#!/bin/bash
# Daily token update script

# 1. Get new request token (from Kite Connect login)
REQUEST_TOKEN="your_request_token_here"

# 2. Generate and save new access token
curl -X POST "http://localhost:8179/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_token\": \"$REQUEST_TOKEN\",
    \"api_secret\": \"$KITE_API_SECRET\"
  }" | jq .

# 3. Verify token is working
curl http://localhost:8179/api/auth/status | jq .

echo "✅ Daily token update complete"
```

---

**The service automatically reloads tokens when the file is updated - no restart needed!** 🚀
