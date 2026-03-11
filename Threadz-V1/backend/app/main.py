import contextlib
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, Base
from . import auth, designs, products, orders
from .config import settings, validate_secrets
from .ssl_config import setup_ssl_and_security, get_ssl_context
from .sentry_config import sentry_manager
from .security_hardening import security_middleware, security_hardening
from .rate_limiter_redis import rate_limit_middleware, initialize_rate_limiter
from .queue import start_queue_processor

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate secrets on startup
    try:
        validate_secrets()
        print("✅ All secrets validated successfully")
    except ValueError as e:
        print(f"❌ Secret validation failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize services
    await initialize_rate_limiter()
    await start_queue_processor()
    
    # Setup tables on startup (only for SQLite/development)
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created (SQLite)")
    
    # Initialize Sentry
    if sentry_manager.enabled:
        print("✅ Sentry error tracking enabled")
    
    print(f"🚀 Threadz API starting in {settings.ENVIRONMENT} mode")
    yield
    print("🛑 Threadz API shutting down")

app = FastAPI(
    title="Threadz Custom Fashion Platform", 
    version=settings.VERSION,
    lifespan=lifespan,
    description="API for creating custom clothing designs with AI generation",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Setup security and SSL middleware
setup_ssl_and_security(app)

# Add security middleware
app.middleware("http")(security_middleware)
app.middleware("http")(rate_limit_middleware)

# Add CORS with security best practices
allowed_origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(designs.router)
app.include_router(products.router)
app.include_router(orders.router)

# Static files
os.makedirs("uploads/designs", exist_ok=True)
app.mount("/api/v1/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint with system status"""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "sentry_enabled": sentry_manager.enabled,
        "security_headers": True,
        "rate_limiting": True
    }

@app.get("/", tags=["Root"])
@limiter.limit("50/minute")
async def root(request: Request):
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_url": "/health",
        "security": {
            "headers_enabled": True,
            "rate_limiting": True,
            "input_validation": True,
            "virus_scanning": security_hardening.clamav_scanner is not None
        }
    }

@app.get("/api/v1/security/info", tags=["Security"])
@limiter.limit("10/minute")
async def security_info(request: Request):
    """Get security configuration info"""
    return {
        "security_headers": security_hardening.get_security_headers(),
        "rate_limits": {
            "auth": "5/minute",
            "upload": "10/hour", 
            "ai_generation": "5/5minutes",
            "api": "100/hour",
            "payment": "10/5minutes"
        },
        "input_validation": {
            "enabled": True,
            "max_lengths": {
                "text": 10000,
                "name": 255,
                "email": 254,
                "prompt": 1000
            }
        },
        "file_security": {
            "virus_scanning": security_hardening.clamav_scanner is not None,
            "image_validation": True,
            "max_file_size": settings.MAX_FILE_SIZE
        }
    }

# Global exception handler for Sentry
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with Sentry tracking"""
    sentry_manager.capture_exception(exc, {
        "request_method": request.method,
        "request_url": str(request.url),
        "client_ip": request.client.host if request.client else None
    })
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Security event logging
@app.middleware("http")
async def security_logging_middleware(request: Request, call_next):
    """Log security events"""
    # Log suspicious requests
    suspicious_patterns = [
        "admin", "config", "env", "secret", "key", "password", "token"
    ]
    
    path_lower = request.url.path.lower()
    if any(pattern in path_lower for pattern in suspicious_patterns):
        security_hardening.log_security_event("suspicious_request", {
            "path": request.url.path,
            "method": request.method,
            "ip": request.client.host if request.client else None
        })
    
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    
    # Get SSL context if available
    ssl_context = get_ssl_context()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        ssl_certfile=ssl_context.get("ssl_certfile") if ssl_context else None,
        ssl_keyfile=ssl_context.get("ssl_keyfile") if ssl_context else None,
        log_level="info" if not settings.DEBUG else "debug",
        workers=1 if settings.DEBUG else 4,
        access_log=True
    )
