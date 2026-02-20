"""
SalesEcho AI - Main FastAPI Application
Enterprise-ready Call-to-CRM automation with Hebrew/English support
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
import subprocess
import shutil

# Import config first to ensure .env is loaded
from app.core.config import settings
from app.core.database import connect_db, disconnect_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and accessible in system PATH.
    
    Returns:
        True if FFmpeg is available, False otherwise
    
    Raises:
        SystemExit: If FFmpeg is not found (prevents server startup)
    """
    # First, check if ffmpeg command exists in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not ffmpeg_path:
        logger.critical(
            "FFmpeg is not installed or not found in system PATH. "
            "SalesEcho AI requires FFmpeg for audio pre-processing. "
            "Please install FFmpeg before starting the server. "
            "See README.md for installation instructions."
        )
        raise SystemExit(
            "CRITICAL: FFmpeg is required but not found. "
            "Install FFmpeg and ensure it's in your system PATH. "
            "See README.md for installation instructions."
        )
    
    # Verify FFmpeg is executable and get version
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        
        # Extract version info from output
        version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
        logger.info(f"FFmpeg found: {ffmpeg_path}")
        logger.info(f"FFmpeg version: {version_line}")
        
        return True
        
    except subprocess.CalledProcessError:
        logger.critical(
            "FFmpeg is installed but failed to execute. "
            "Please verify FFmpeg installation and permissions."
        )
        raise SystemExit(
            "CRITICAL: FFmpeg execution failed. "
            "Verify installation and permissions."
        )
    except subprocess.TimeoutExpired:
        logger.critical("FFmpeg version check timed out.")
        raise SystemExit("CRITICAL: FFmpeg version check timed out.")
    except FileNotFoundError:
        # This shouldn't happen if shutil.which found it, but handle it anyway
        logger.critical("FFmpeg command not found in PATH.")
        raise SystemExit(
            "CRITICAL: FFmpeg not found in PATH. "
            "Install FFmpeg and ensure it's accessible."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting SalesEcho AI application...")
    
    # Check for required system dependencies
    try:
        logger.info("Checking system dependencies...")
        check_ffmpeg_installed()
        logger.info("System dependencies check passed")
    except SystemExit:
        # Re-raise SystemExit to prevent server startup
        raise
    except Exception as e:
        logger.critical(f"System dependency check failed: {e}")
        raise SystemExit(f"CRITICAL: System dependency check failed: {e}")
    
    # Database connection
    try:
        await connect_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down SalesEcho AI application...")
    try:
        await disconnect_db()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="SalesEcho AI",
    description="Call-to-CRM automation engine with Hebrew/English support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow frontend and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "SalesEcho AI",
            "version": "1.0.0",
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        content={
            "message": "SalesEcho AI API",
            "docs": "/docs",
            "health": "/health",
        }
    )


# Import API routes
from app.api.v1.meetings import router as meetings_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.settings import router as settings_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.clients import router as clients_router
from app.api.v1.billing import router as billing_router
from app.api.v1.users import router as users_router
from app.api.v1.manager_analytics import router as manager_analytics_router

# Include routers
app.include_router(meetings_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(settings_router, prefix="/api/v1", tags=["Settings"])
app.include_router(feedback_router, prefix="/api/v1", tags=["Feedback"])
app.include_router(clients_router, prefix="/api/v1", tags=["Clients"])
app.include_router(billing_router, prefix="/api/v1", tags=["Billing"])
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
app.include_router(manager_analytics_router, prefix="/api/v1", tags=["Manager Analytics"])