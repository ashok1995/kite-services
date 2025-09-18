"""
Kite Services - Main Application Entry Point
===========================================

Independent service for market context, intelligent trading decisions,
position tracking, and stop-loss/target management.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from core.logging_config import setup_logging, get_logger
# from core.database import init_database, close_database  # Not implemented yet
from core.service_manager import ServiceManager
from api import market_routes, trading_routes, position_routes, websocket_routes


# Initialize settings and logging
settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Kite Services...")
    
    try:
        # Initialize database (placeholder)
        # await init_database()
        # logger.info("✅ Database initialized")
        
        # Initialize service manager
        service_manager = ServiceManager()
        await service_manager.initialize()
        app.state.service_manager = service_manager
        logger.info("✅ Service manager initialized")
        
        # Store settings in app state
        app.state.settings = settings
        
        logger.info(f"🎯 Kite Services started successfully on port {settings.service.port}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Kite Services: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🛑 Shutting down Kite Services...")
        
        if hasattr(app.state, 'service_manager'):
            await app.state.service_manager.cleanup()
            logger.info("✅ Service manager cleaned up")
        
        # await close_database()
        # logger.info("✅ Database connections closed")
        
        logger.info("👋 Kite Services shut down complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Kite Services",
        description="Independent Market Context & Intelligent Trading Service",
        version=settings.service.version,
        lifespan=lifespan,
        docs_url="/docs" if settings.service.debug else None,
        redoc_url="/redoc" if settings.service.debug else None,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI):
    """Setup application middleware."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.service.cors_origins,
        allow_credentials=True,
        allow_methods=settings.service.cors_methods,
        allow_headers=settings.service.cors_headers,
    )
    
    # Trusted host middleware
    if not settings.service.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", settings.service.host]
        )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # Process request
        response = await call_next(request)
        
        # Log request
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            "HTTP Request",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        return response


def setup_routes(app: FastAPI):
    """Setup application routes."""
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        service_manager = getattr(app.state, 'service_manager', None)
        
        if service_manager:
            health_status = await service_manager.get_health_status()
            return {
                "status": "healthy",
                "service": settings.service.name,
                "version": settings.service.version,
                "environment": settings.service.environment,
                "services": health_status
            }
        else:
            return {
                "status": "starting",
                "service": settings.service.name,
                "version": settings.service.version,
                "environment": settings.service.environment,
            }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.service.name,
            "version": settings.service.version,
            "environment": settings.service.environment,
            "docs_url": "/docs" if settings.service.debug else None,
            "health_url": "/health",
            "api_prefix": "/api"
        }
    
    # Include API routes
    app.include_router(market_routes.router, prefix="/api/market", tags=["Market"])
    app.include_router(trading_routes.router, prefix="/api/trading", tags=["Trading"])
    app.include_router(position_routes.router, prefix="/api/positions", tags=["Positions"])
    app.include_router(websocket_routes.router, prefix="/ws", tags=["WebSocket"])


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            extra={
                "method": request.method,
                "url": str(request.url),
                "exception": str(exc),
                "exception_type": type(exc).__name__,
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.service.debug else "An unexpected error occurred",
                "type": type(exc).__name__ if settings.service.debug else "ServerError",
            }
        )


# Create application instance
app = create_app()


async def main():
    """Main application runner."""
    
    # Configure uvicorn
    config = uvicorn.Config(
        app=app,
        host=settings.service.host,
        port=settings.service.port,
        workers=1,  # Single worker for WebSocket support
        log_level=settings.logging.level.lower(),
        access_log=True,
        reload=settings.service.debug,
        reload_dirs=["src"] if settings.service.debug else None,
    )
    
    # Create and run server
    server = uvicorn.Server(config)
    
    try:
        logger.info(f"🚀 Starting Kite Services on {settings.service.host}:{settings.service.port}")
        await server.serve()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down Kite Services...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
