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
from datetime import datetime
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
from core.database import init_database, close_database
from core.service_manager import ServiceManager, set_service_manager
# Import consolidated API modules
from api import auth, market_data, analysis, trading, analysis_enhanced, quick_opportunities


# Initialize settings and logging
settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Kite Services...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("✅ Database initialized")
        
        # Initialize service manager
        service_manager = ServiceManager()
        await service_manager.initialize()
        app.state.service_manager = service_manager
        set_service_manager(service_manager)  # Set global instance
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
        
        await close_database()
        logger.info("✅ Database connections closed")
        
        logger.info("👋 Kite Services shut down complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Kite Services - Consolidated API",
        description="""
        **Ultra-Minimal Trading API with 8 Endpoints**
        
        🔐 **Authentication** (2 endpoints)
        - POST /api/auth/login - Complete authentication flow
        - GET /api/auth/status - Authentication status
        
        📊 **Market Data** (3 endpoints)  
        - POST /api/market/data - Universal market data
        - GET /api/market/status - Market status & health
        - GET /api/market/instruments - Available instruments
        
        🧠 **Analysis** (2 endpoints)
        - POST /api/analysis/context - Complete market context
        - POST /api/analysis/intelligence - Stock intelligence
        
        💼 **Trading** (1 endpoint)
        - GET /api/trading/status - Portfolio & positions
        
        **Consolidated from 60+ endpoints into 8 focused endpoints**
        """,
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
    
    # Request logging middleware with request IDs and metrics
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        from core.logging_config import set_request_id, get_request_id
        from core.monitoring import get_metrics_collector
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or set_request_id()
        set_request_id(request_id)
        
        start_time = asyncio.get_event_loop().time()
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            process_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                "HTTP Request Error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": round(process_time, 4),
                    "client_ip": request.client.host if request.client else None,
                },
                exc_info=True
            )
            raise
        
        # Calculate metrics
        process_time = asyncio.get_event_loop().time() - start_time
        duration_ms = process_time * 1000
        
        # Record metric
        metrics = get_metrics_collector()
        await metrics.record_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request
        log_level = "error" if response.status_code >= 500 else "warning" if response.status_code >= 400 else "info"
        getattr(logger, log_level)(
            "HTTP Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        return response


def setup_routes(app: FastAPI):
    """Setup application routes."""
    
    # Health check endpoint with detailed monitoring
    @app.get("/health")
    async def health_check(detailed: bool = False):
        """Health check endpoint with optional detailed metrics."""
        from core.monitoring import get_metrics_collector
        
        # Get service manager from app state
        service_manager = app.state.service_manager if hasattr(app.state, 'service_manager') else None
        
        # Basic health
        health_data = {
            "status": "healthy",
            "service": settings.service.name,
            "version": settings.service.version,
            "environment": settings.service.environment,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add service status
        if service_manager:
            try:
                health_status = await service_manager.get_health_status()
                health_data["services"] = health_status
            except Exception as e:
                logger.warning(f"Could not get service health status: {e}")
                health_data["services"] = {"services": {}, "error": str(e)}
        
        # Add detailed metrics if requested
        if detailed:
            metrics = get_metrics_collector()
            service_health = await metrics.get_health()
            health_data.update({
                "uptime_seconds": round(service_health.uptime_seconds, 2),
                "total_requests": service_health.total_requests,
                "successful_requests": service_health.successful_requests,
                "failed_requests": service_health.failed_requests,
                "average_response_time_ms": service_health.average_response_time_ms,
                "error_rate_percent": service_health.error_rate,
                "last_error": service_health.last_error,
                "last_error_time": service_health.last_error_time.isoformat() if service_health.last_error_time else None,
            })
            health_data["status"] = service_health.status
        
        return health_data
    
    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Get application metrics."""
        from core.monitoring import get_metrics_collector
        
        metrics = get_metrics_collector()
        summary = await metrics.get_metrics_summary()
        health = await metrics.get_health()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(health.uptime_seconds, 2),
            "status": health.status,
            "requests": {
                "total": summary["total_requests"],
                "per_minute": summary["requests_per_minute"],
                "successful": health.successful_requests,
                "failed": health.failed_requests,
            },
            "performance": {
                "average_response_time_ms": summary["average_response_time_ms"],
                "error_rate_percent": summary["error_rate_percent"],
            },
            "top_endpoints": summary["top_endpoints"],
            "status_codes": summary["status_code_distribution"],
        }
    
    # Health check endpoint (backward compatibility)
    @app.get("/health/quick")
    async def health_check_quick():
        """Quick health check endpoint."""
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
    
    # Metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Get application metrics for monitoring."""
        from core.monitoring import get_metrics_collector
        
        metrics = get_metrics_collector()
        summary = await metrics.get_metrics_summary()
        health = await metrics.get_health()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(health.uptime_seconds, 2),
            "status": health.status,
            "requests": {
                "total": summary["total_requests"],
                "per_minute": summary["requests_per_minute"],
                "successful": health.successful_requests,
                "failed": health.failed_requests,
            },
            "performance": {
                "average_response_time_ms": summary["average_response_time_ms"],
                "error_rate_percent": summary["error_rate_percent"],
            },
            "top_endpoints": summary["top_endpoints"],
            "status_codes": summary["status_code_distribution"],
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
            "metrics_url": "/metrics",
            "api_prefix": "/api"
        }
    
    # Include consolidated API routes (5 modules, 9+ endpoints total)
    app.include_router(auth.router, prefix="/api")
    app.include_router(market_data.router, prefix="/api") 
    app.include_router(analysis.router, prefix="/api")
    app.include_router(analysis_enhanced.router, prefix="/api")  # Enhanced hierarchical context
    app.include_router(quick_opportunities.router, prefix="/api")  # Quick money-making opportunities
    app.include_router(trading.router, prefix="/api")


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        from core.logging_config import get_request_id
        from core.monitoring import get_metrics_collector
        
        request_id = get_request_id()
        
        # Record error in metrics
        try:
            metrics = get_metrics_collector()
            await metrics.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=500,
                duration_ms=0.0
            )
        except Exception:
            pass  # Don't fail if metrics fail
        
        logger.error(
            "Unhandled exception",
            extra={
                "request_id": request_id,
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
