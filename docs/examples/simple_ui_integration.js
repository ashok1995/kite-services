/**
 * Simple Kite Token Manager for UI Integration
 *
 * Clean, minimal solution for token management in your existing UI
 */

class SimpleKiteTokenManager {
    constructor(apiBase = 'http://localhost:8079') {
        this.apiBase = apiBase;
    }

    /**
     * Get callback URL for Kite Connect app configuration
     * @returns {Promise<string>} Callback URL
     */
    async getCallbackUrl() {
        const response = await fetch(`${this.apiBase}/api/token/callback-url`);
        const data = await response.json();
        return data.callback_url;
    }

    /**
     * Check if token needs refresh
     * @returns {Promise<Object>} Token status
     */
    async checkTokenStatus() {
        const response = await fetch(`${this.apiBase}/api/token/status`);
        return await response.json();
    }

    /**
     * Submit request token to get access token
     * @param {string} requestToken - Request token from callback URL
     * @returns {Promise<Object>} Access token data
     */
    async submitRequestToken(requestToken) {
        const response = await fetch(`${this.apiBase}/api/token/submit-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_token: requestToken
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.detail || 'Failed to generate access token');
        }

        return data;
    }

    /**
     * Extract request token from callback URL
     * @param {string} callbackUrl - Full callback URL
     * @returns {string} Request token
     */
    extractRequestToken(callbackUrl) {
        try {
            const url = new URL(callbackUrl);
            const token = url.searchParams.get('request_token');

            if (!token) {
                throw new Error('No request_token found in URL');
            }

            return token;
        } catch (error) {
            throw new Error('Invalid callback URL: ' + error.message);
        }
    }

    /**
     * Get Kite Connect login URL
     * @returns {Promise<string>} Login URL
     */
    async getLoginUrl() {
        const response = await fetch(`${this.apiBase}/api/token/refresh-info`);
        const data = await response.json();
        return data.login_url;
    }
}

/**
 * Simple UI Functions - Ready to use in your existing UI
 */

// Check if token is valid
async function isKiteTokenValid(apiBase = 'http://localhost:8079') {
    try {
        const manager = new SimpleKiteTokenManager(apiBase);
        const status = await manager.checkTokenStatus();
        return status.token_valid;
    } catch (error) {
        console.error('Error checking token:', error);
        return false;
    }
}

// Get callback URL for configuration
async function getKiteCallbackUrl(apiBase = 'http://localhost:8079') {
    try {
        const manager = new SimpleKiteTokenManager(apiBase);
        return await manager.getCallbackUrl();
    } catch (error) {
        console.error('Error getting callback URL:', error);
        return null;
    }
}

// Open Kite login in new window
async function openKiteLogin(apiBase = 'http://localhost:8079') {
    try {
        const manager = new SimpleKiteTokenManager(apiBase);
        const loginUrl = await manager.getLoginUrl();
        window.open(loginUrl, '_blank');
        return loginUrl;
    } catch (error) {
        console.error('Error opening login:', error);
        throw error;
    }
}

// Convert request token to access token
async function convertRequestToken(requestToken, apiBase = 'http://localhost:8079') {
    try {
        const manager = new SimpleKiteTokenManager(apiBase);
        return await manager.submitRequestToken(requestToken);
    } catch (error) {
        console.error('Error converting token:', error);
        throw error;
    }
}

// Extract request token from callback URL
function extractRequestTokenFromUrl(callbackUrl) {
    try {
        const manager = new SimpleKiteTokenManager();
        return manager.extractRequestToken(callbackUrl);
    } catch (error) {
        console.error('Error extracting token:', error);
        throw error;
    }
}

/**
 * Ready-to-use UI Components
 */

// Create a simple token status widget
function createTokenStatusWidget(containerId, apiBase = 'http://localhost:8079') {
    const container = document.getElementById(containerId);

    container.innerHTML = `
        <div id="token-widget" style="
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        ">
            <div id="token-status-display">Loading token status...</div>
            <button id="refresh-status-btn" style="
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 10px;
            ">
                🔄 Check Status
            </button>
        </div>
    `;

    const updateStatus = async () => {
        try {
            const status = await new SimpleKiteTokenManager(apiBase).checkTokenStatus();
            const statusColor = status.token_valid ? '#27ae60' : '#e74c3c';
            const statusText = status.token_valid ? '✅ Valid' : '❌ Expired';

            document.getElementById('token-status-display').innerHTML = `
                <div style="color: ${statusColor}; font-weight: bold;">
                    Kite Token: ${statusText}
                </div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    Token: ${status.token_masked || 'Not configured'}
                </div>
            `;
        } catch (error) {
            document.getElementById('token-status-display').innerHTML =
                '<div style="color: #e74c3c;">Error loading status</div>';
        }
    };

    document.getElementById('refresh-status-btn').onclick = updateStatus;
    updateStatus(); // Initial load
}

// Create a simple token refresh form
function createTokenRefreshForm(containerId, apiBase = 'http://localhost:8079') {
    const container = document.getElementById(containerId);

    container.innerHTML = `
        <div style="border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; background: white;">
            <h3>🔄 Refresh Kite Token</h3>

            <div style="margin: 15px 0;">
                <button id="open-login-btn" style="
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: bold;
                ">
                    🔗 Open Kite Login
                </button>
            </div>

            <div style="margin: 15px 0;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                    Request Token:
                </label>
                <input type="text" id="request-token-input" placeholder="Paste request token here..." style="
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #e9ecef;
                    border-radius: 4px;
                    box-sizing: border-box;
                ">
            </div>

            <button id="submit-token-btn" style="
                background: #27ae60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
            ">
                ✅ Generate Access Token
            </button>

            <div id="refresh-result" style="margin-top: 15px;"></div>
        </div>
    `;

    const manager = new SimpleKiteTokenManager(apiBase);

    document.getElementById('open-login-btn').onclick = async () => {
        try {
            await openKiteLogin(apiBase);
            document.getElementById('refresh-result').innerHTML =
                '<div style="color: #3498db; padding: 10px; background: #e8f4fd; border-radius: 4px;">Login page opened! After login, paste the request token above.</div>';
        } catch (error) {
            document.getElementById('refresh-result').innerHTML =
                `<div style="color: #e74c3c; padding: 10px; background: #fadbd8; border-radius: 4px;">Error: ${error.message}</div>`;
        }
    };

    document.getElementById('submit-token-btn').onclick = async () => {
        const requestToken = document.getElementById('request-token-input').value.trim();
        const resultDiv = document.getElementById('refresh-result');

        if (!requestToken) {
            resultDiv.innerHTML = '<div style="color: #e74c3c;">Please enter a request token</div>';
            return;
        }

        try {
            const tokenData = await manager.submitRequestToken(requestToken);

            resultDiv.innerHTML = `
                <div style="color: #27ae60; padding: 15px; background: #d5f4e6; border-radius: 4px;">
                    <h4>✅ Success!</h4>
                    <p><strong>User:</strong> ${tokenData.user_name} (${tokenData.email})</p>
                    <p><strong>Access Token:</strong></p>
                    <div style="background: #2c3e50; color: white; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; font-size: 12px;">
                        ${tokenData.access_token}
                    </div>
                    <p><strong>Next:</strong> Update KITE_ACCESS_TOKEN and restart service</p>
                </div>
            `;

            // Clear input
            document.getElementById('request-token-input').value = '';

        } catch (error) {
            resultDiv.innerHTML =
                `<div style="color: #e74c3c; padding: 10px; background: #fadbd8; border-radius: 4px;">Error: ${error.message}</div>`;
        }
    };
}

/**
 * Usage Examples:
 */

/*
// Example 1: Check token status
const isValid = await isKiteTokenValid();
if (!isValid) {
    console.log('Token needs refresh');
}

// Example 2: Get callback URL
const callbackUrl = await getKiteCallbackUrl();
console.log('Configure this URL:', callbackUrl);

// Example 3: Open login page
await openKiteLogin();

// Example 4: Convert request token
const tokenData = await convertRequestToken('qQDXpFOTSBW59mcej7cmRmM0xtBWA1Iw'); // pragma: allowlist secret
console.log('New access token:', tokenData.access_token);

// Example 5: Create status widget
createTokenStatusWidget('status-container');

// Example 6: Create refresh form
createTokenRefreshForm('refresh-container');
*/

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SimpleKiteTokenManager,
        isKiteTokenValid,
        getKiteCallbackUrl,
        openKiteLogin,
        convertRequestToken,
        extractRequestTokenFromUrl,
        createTokenStatusWidget,
        createTokenRefreshForm
    };
}

if (typeof window !== 'undefined') {
    window.SimpleKiteTokenManager = SimpleKiteTokenManager;
    window.isKiteTokenValid = isKiteTokenValid;
    window.getKiteCallbackUrl = getKiteCallbackUrl;
    window.openKiteLogin = openKiteLogin;
    window.convertRequestToken = convertRequestToken;
    window.extractRequestTokenFromUrl = extractRequestTokenFromUrl;
    window.createTokenStatusWidget = createTokenStatusWidget;
    window.createTokenRefreshForm = createTokenRefreshForm;
}
