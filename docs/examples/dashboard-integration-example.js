/**
 * Dashboard Integration Example for Kite Services
 * ================================================
 *
 * This example shows how to integrate the market sentiment endpoint
 * with your dashboard to display real-time index data.
 */

// Configuration
const KITE_SERVICES_URL = 'http://localhost:8079';

// Index name mapping (since API returns current_level as identifier)
const INDEX_NAMES = {
    '^NSEI': 'NIFTY 50',
    '^NSEBANK': 'BANK NIFTY',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^DJI': 'SENSEX'
};

/**
 * Fetch and update dashboard with market data
 */
async function updateMarketDashboard() {
    try {
        const response = await fetch(`${KITE_SERVICES_URL}/api/market-sentiment`);
        const data = await response.json();

        // Update each index on the dashboard
        data.indices.forEach(index => {
            const indexName = getIndexName(index.current_level);
            const price = index.current_level;
            const changePercent = index.daily_change_percent;
            const changeAmount = index.daily_change;

            // Update your dashboard elements
            updateDashboardElement(indexName, {
                price: price,
                change: changePercent,
                changeAmount: changeAmount,
                trend: index.overall_market_regime
            });
        });

        console.log('✅ Dashboard updated with latest market data');

    } catch (error) {
        console.error('❌ Failed to update dashboard:', error);
    }
}

/**
 * Map index identifier to display name
 */
function getIndexName(indexLevel) {
    // This is a simplified mapping - you might need more sophisticated logic
    if (indexLevel > 20000) return 'NIFTY 50';
    if (indexLevel > 50000) return 'BANK NIFTY';
    if (indexLevel > 2000) return 'S&P 500';
    if (indexLevel > 10000) return 'NASDAQ';
    return 'SENSEX';
}

/**
 * Update dashboard element (implement based on your dashboard structure)
 */
function updateDashboardElement(indexName, data) {
    // Example implementation - adapt to your dashboard structure
    const element = document.querySelector(`[data-index="${indexName}"]`);

    if (element) {
        // Update price
        const priceElement = element.querySelector('.price');
        if (priceElement) {
            priceElement.textContent = data.price.toLocaleString('en-IN');
        }

        // Update change
        const changeElement = element.querySelector('.change');
        if (changeElement) {
            const changeText = `${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%`;
            changeElement.textContent = changeText;
            changeElement.className = `change ${data.change >= 0 ? 'positive' : 'negative'}`;
        }

        // Update trend indicator
        const trendElement = element.querySelector('.trend');
        if (trendElement) {
            trendElement.textContent = data.trend;
            trendElement.className = `trend ${data.trend}`;
        }
    }
}

/**
 * Initialize dashboard with periodic updates
 */
function initializeDashboard() {
    // Initial load
    updateMarketDashboard();

    // Set up periodic updates (every 30 seconds)
    setInterval(updateMarketDashboard, 30000);

    console.log('🚀 Dashboard initialized with market data integration');
}

// Auto-initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}

// Export for manual use
window.updateMarketDashboard = updateMarketDashboard;
