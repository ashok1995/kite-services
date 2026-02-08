# 🔐 **Token Status API Documentation**

## **Kite Connect Token & Yahoo Finance Status Monitoring**

---

## 📊 **Overview**

The Token Status API provides endpoints for monitoring the health of your Kite Connect authentication and Yahoo Finance connection. Perfect for integrating into your existing UI to track service status and handle token expiration.

### **🎯 Key Features:**
- **Real-time token validation** with Kite Connect API
- **Yahoo Finance connection testing** 
- **Token refresh URL generation** when expired
- **UI-friendly JSON responses** for easy integration
- **Comprehensive status overview** for dashboards

---

## 🚀 **Available Endpoints**

### **Base URL:** `http://localhost:8079/api/token`

| **Endpoint** | **Method** | **Purpose** | **Response Time** |
|--------------|------------|-------------|-------------------|
| `/status` | GET | Token & connection status | ~500ms |
| `/refresh-info` | GET | Token refresh information | ~50ms |
| `/comprehensive` | GET | Complete status for UI | ~500ms |
| `/health-check` | GET | Service health check | ~10ms |

---

## 📊 **Endpoint Details**

### **1. 🔍 Token Status - `GET /api/token/status`**

**Purpose:** Check current status of Kite Connect token and Yahoo Finance connection

#### **Response Model:**
```json
{
  "kite_token_valid": false,
  "kite_token_expires_at": "2025-09-19T15:30:00",
  "kite_token_masked": "Un7k...3S3k",
  "yahoo_finance_available": true,
  "last_checked": "2025-09-19T09:27:33.653325+00:00",
  "needs_refresh": true
}
```

#### **Field Descriptions:**
- **`kite_token_valid`** - Whether the Kite Connect token is currently valid
- **`kite_token_expires_at`** - Estimated token expiry time (daily expiration)
- **`kite_token_masked`** - Masked token for security (first 4 + last 4 chars)
- **`yahoo_finance_available`** - Whether Yahoo Finance API is accessible
- **`last_checked`** - Timestamp of the status check
- **`needs_refresh`** - Whether token refresh is required

#### **Usage Example:**
```javascript
// Check token status
const response = await fetch('http://localhost:8079/api/token/status');
const status = await response.json();

if (status.needs_refresh) {
    console.log('Token needs refresh!');
    // Handle token refresh logic
}
```

---

### **2. 🔄 Token Refresh Info - `GET /api/token/refresh-info`**

**Purpose:** Get information for refreshing expired Kite Connect token

#### **Response Model:**
```json
{
  "needs_refresh": true,
  "login_url": "https://kite.zerodha.com/connect/login?api_key=your_key&v=3",
  "callback_url": "http://localhost:8079/auth/callback",
  "instructions": "Step-by-step refresh instructions..."
}
```

#### **Field Descriptions:**
- **`needs_refresh`** - Whether token refresh is required
- **`login_url`** - Kite Connect login URL for getting new token
- **`callback_url`** - Callback URL to configure in Kite Connect app
- **`instructions`** - Detailed refresh instructions

#### **Usage Example:**
```javascript
// Get refresh information
const response = await fetch('http://localhost:8079/api/token/refresh-info');
const refreshInfo = await response.json();

if (refreshInfo.needs_refresh && refreshInfo.login_url) {
    // Show refresh UI with login link
    window.open(refreshInfo.login_url, '_blank');
}
```

---

### **3. 📋 Comprehensive Status - `GET /api/token/comprehensive`**

**Purpose:** Complete status information optimized for UI integration

#### **Response Model:**
```json
{
  "timestamp": "2025-09-19T09:27:43.924939+00:00",
  "service": "kite-services",
  "environment": "development",
  "port": "8079",
  "status": {
    "kite_connect": {
      "token_valid": false,
      "token_masked": "Un7k...3S3k",
      "expires_at": null,
      "needs_refresh": true
    },
    "yahoo_finance": {
      "available": true,
      "status": "connected"
    }
  },
  "refresh_info": {
    "login_url": "https://kite.zerodha.com/connect/login?api_key=your_key&v=3",
    "callback_url": "http://localhost:8079/auth/callback",
    "instructions": "Refresh instructions..."
  }
}
```

#### **Perfect For:**
- **Dashboard widgets** showing service health
- **Status pages** with comprehensive information
- **Monitoring systems** that need all details in one call

---

### **4. ❤️ Health Check - `GET /api/token/health-check`**

**Purpose:** Simple health check for the token status service

#### **Response Model:**
```json
{
  "service": "token-status",
  "status": "healthy",
  "endpoints": [
    "GET /status - Token and connection status",
    "GET /refresh-info - Token refresh information", 
    "GET /comprehensive - Complete status with refresh info",
    "GET /health-check - Service health check"
  ]
}
```

---

## 🎨 **UI Integration Examples**

### **📱 React Component:**
```jsx
import React, { useState, useEffect } from 'react';

const TokenStatusWidget = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8079/api/token/comprehensive');
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Error checking status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading status...</div>;

  return (
    <div className="token-status-widget">
      <h3>Service Status</h3>
      
      <div className={`status-item ${status.status.kite_connect.token_valid ? 'healthy' : 'error'}`}>
        <span>Kite Connect:</span>
        <span>{status.status.kite_connect.token_valid ? '✅ Connected' : '❌ Token Expired'}</span>
      </div>
      
      <div className={`status-item ${status.status.yahoo_finance.available ? 'healthy' : 'error'}`}>
        <span>Yahoo Finance:</span>
        <span>{status.status.yahoo_finance.available ? '✅ Available' : '❌ Unavailable'}</span>
      </div>
      
      {status.refresh_info?.login_url && (
        <div className="refresh-section">
          <p>Token expired. <a href={status.refresh_info.login_url} target="_blank">Get new token</a></p>
        </div>
      )}
    </div>
  );
};
```

### **🌐 Vanilla JavaScript:**
```javascript
class TokenStatusMonitor {
  constructor(containerId, apiBase = 'http://localhost:8079') {
    this.container = document.getElementById(containerId);
    this.apiBase = apiBase;
    this.autoRefresh = false;
    this.refreshInterval = null;
  }

  async checkStatus() {
    try {
      const response = await fetch(`${this.apiBase}/api/token/comprehensive`);
      const data = await response.json();
      this.updateUI(data);
    } catch (error) {
      this.showError(error.message);
    }
  }

  updateUI(data) {
    const kiteStatus = data.status.kite_connect.token_valid ? '✅ Valid' : '❌ Expired';
    const yahooStatus = data.status.yahoo_finance.available ? '✅ Available' : '❌ Unavailable';
    
    this.container.innerHTML = `
      <div class="status-panel">
        <h3>Token Status</h3>
        <div>Kite Connect: ${kiteStatus}</div>
        <div>Yahoo Finance: ${yahooStatus}</div>
        ${data.refresh_info?.login_url ? 
          `<a href="${data.refresh_info.login_url}" target="_blank" class="refresh-btn">Refresh Token</a>` : 
          ''
        }
      </div>
    `;
  }

  startAutoRefresh(intervalMs = 30000) {
    this.autoRefresh = true;
    this.refreshInterval = setInterval(() => this.checkStatus(), intervalMs);
  }

  stopAutoRefresh() {
    this.autoRefresh = false;
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }
}

// Usage
const monitor = new TokenStatusMonitor('status-container');
monitor.checkStatus();
monitor.startAutoRefresh();
```

### **🐍 Python Integration:**
```python
import requests
import time
from typing import Dict, Any

class KiteTokenMonitor:
    def __init__(self, api_base: str = "http://localhost:8079"):
        self.api_base = api_base
    
    def check_status(self) -> Dict[str, Any]:
        """Check comprehensive token status"""
        response = requests.get(f"{self.api_base}/api/token/comprehensive")
        return response.json()
    
    def is_token_valid(self) -> bool:
        """Quick check if token is valid"""
        status = self.check_status()
        return status["status"]["kite_connect"]["token_valid"]
    
    def get_refresh_url(self) -> str:
        """Get token refresh URL if needed"""
        response = requests.get(f"{self.api_base}/api/token/refresh-info")
        data = response.json()
        return data.get("login_url", "")
    
    def monitor_continuously(self, check_interval: int = 30):
        """Monitor token status continuously"""
        while True:
            try:
                status = self.check_status()
                kite_valid = status["status"]["kite_connect"]["token_valid"]
                yahoo_available = status["status"]["yahoo_finance"]["available"]
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Kite: {'✅' if kite_valid else '❌'} | "
                      f"Yahoo: {'✅' if yahoo_available else '❌'}")
                
                if not kite_valid:
                    refresh_url = self.get_refresh_url()
                    if refresh_url:
                        print(f"⚠️ Token expired! Refresh at: {refresh_url}")
                
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("Monitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(check_interval)

# Usage
monitor = KiteTokenMonitor()
print("Token valid:", monitor.is_token_valid())
# monitor.monitor_continuously()  # Uncomment for continuous monitoring
```

---

## 🔧 **Configuration**

### **Environment Variables:**
```bash
# Required for token validation
KITE_API_KEY=your_kite_api_key
KITE_ACCESS_TOKEN=your_access_token
KITE_API_SECRET=your_api_secret

# Optional
SERVICE_PORT=8079
ENVIRONMENT=development
```

### **Service Configuration:**
- **Development:** `http://localhost:8079/api/token/*`
- **Production:** `http://localhost:8179/api/token/*`

---

## 📊 **Response Codes**

| **Code** | **Status** | **Description** |
|----------|------------|-----------------|
| 200 | Success | Status retrieved successfully |
| 500 | Error | Service error (check logs) |
| 404 | Not Found | Endpoint not available |

---

## 🎯 **Use Cases**

### **📊 Perfect For:**

#### **1. Trading Dashboard Status Widget:**
```javascript
// Show token status in trading dashboard
const statusWidget = document.getElementById('token-status');
const status = await fetch('/api/token/status').then(r => r.json());

statusWidget.innerHTML = `
  <div class="status ${status.kite_token_valid ? 'green' : 'red'}">
    Kite: ${status.kite_token_valid ? 'Connected' : 'Disconnected'}
  </div>
`;
```

#### **2. Automated Monitoring:**
```python
# Check token status before trading operations
def ensure_token_valid():
    response = requests.get('http://localhost:8079/api/token/status')
    status = response.json()
    
    if not status['kite_token_valid']:
        refresh_url = requests.get('http://localhost:8079/api/token/refresh-info').json()
        raise Exception(f"Token expired! Refresh at: {refresh_url['login_url']}")
    
    return True
```

#### **3. System Health Monitoring:**
```bash
# Health check script for monitoring systems
curl -s "http://localhost:8079/api/token/comprehensive" | \
  jq -r '"Kite: " + (.status.kite_connect.token_valid | tostring) + 
         " | Yahoo: " + (.status.yahoo_finance.available | tostring)'
```

---

## 🎉 **Benefits**

### **✅ For Your UI:**
- **Real-time status** updates for better UX
- **Proactive token management** before expiration
- **Visual indicators** for service health
- **Automated refresh workflows**

### **✅ For Your Operations:**
- **Reduced downtime** from expired tokens
- **Automated monitoring** integration
- **Clear error messaging** for troubleshooting
- **Consistent API responses** for reliable parsing

---

## 🔗 **Live Example**

### **📱 Interactive UI:**
Open the included `ui_integration_example.html` in your browser to see a live example of token status monitoring with:

- **Real-time status indicators** (green/red dots)
- **Auto-refresh functionality** (30-second intervals)
- **Token refresh links** when expired
- **Responsive design** for all screen sizes

### **🧪 Quick Test:**
```bash
# Test all endpoints
curl "http://localhost:8079/api/token/status"
curl "http://localhost:8079/api/token/refresh-info"  
curl "http://localhost:8079/api/token/comprehensive"
curl "http://localhost:8079/api/token/health-check"
```

---

## 🎯 **Integration Ready!**

**Your Token Status API is:**

✅ **UI-Friendly** - Perfect JSON responses for frontend integration  
✅ **Real-Time** - Live token validation with Kite Connect  
✅ **Comprehensive** - All status information in structured format  
✅ **Reliable** - Error handling and fallback mechanisms  
✅ **Documented** - Complete examples for all major frameworks  

**🚀 Perfect for building professional trading applications with robust token management!**
