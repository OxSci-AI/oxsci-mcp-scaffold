"""
MCP Server Main Application

FastAPI application that serves MCP tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from oxsci_oma_mcp import tool_router

from app.core.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=f"{config.SERVICE_NAME} MCP Server",
    description="MCP Server built with oxsci-oma-mcp",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MCP tool router
app.include_router(tool_router)

# Import tools to trigger @oma_tool registration
# This ensures all tools are registered before the server starts
try:
    from app import tools  # noqa: F401

    logger.info("Tools module imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import tools module: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": config.SERVICE_NAME,
        "status": "running",
        "protocol": "oma-mcp",
        "endpoints": {
            "discover": "/tools/discover",
            "list": "/tools/list",
            "execute": "/tools/{tool_name}",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "environment": config.ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.core.main:app",
        host="0.0.0.0",
        port=8060,
        reload=True,
        log_level="info",
    )
