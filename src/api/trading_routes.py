"""
Trading API Routes (Placeholder)
================================

Placeholder for trading-related routes.
These will be implemented in the main stocks-recommendation-service.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def trading_status():
    """Trading service status."""
    return {
        "message": "Trading functionality is handled by the main stocks-recommendation-service",
        "redirect_to": "http://localhost:8000/api/trading"
    }
