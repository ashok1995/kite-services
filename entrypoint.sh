#!/bin/bash
# Kite Services Entrypoint
# ========================
# Handles both dev and prod startup.

set -e

echo "🚀 Kite Services - ${ENVIRONMENT:-development}"
echo "   Port: ${SERVICE_PORT:-8079}"
echo "   Debug: ${DEBUG:-true}"
echo "   Log Level: ${LOG_LEVEL:-INFO}"

# Create required directories
mkdir -p /app/logs /app/data

# Kite credentials: prefer token file (prod) over KITE_API_KEY (legacy)
if [ -n "${KITE_TOKEN_FILE}" ] && [ -f "${KITE_TOKEN_FILE}" ]; then
    echo "✅ Kite token file found: ${KITE_TOKEN_FILE}"
elif [ -z "${KITE_API_KEY}" ]; then
    echo "⚠️  No KITE_API_KEY and no token file — set KITE_TOKEN_FILE or mount kite-credentials"
fi

# Set Python path
export PYTHONPATH=/app/src

# Graceful shutdown handler
cleanup() {
    echo "🛑 Shutting down..."
    kill -TERM "$child" 2>/dev/null
    wait "$child"
    echo "✅ Shutdown complete"
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start the application
echo "🎯 Starting server on port ${SERVICE_PORT:-8079}..."
exec "$@"
