"""
Position API Routes (Placeholder)
=================================

Placeholder for position-related routes.
These will be implemented in the main stocks-recommendation-service.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def position_status():
    """Position service status."""
    return {
        "message": "Position tracking is handled by the main stocks-recommendation-service",
        "redirect_to": "http://localhost:8000/api/positions"
    }
