"""
MCP Server Main Application

FastAPI application that serves MCP tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from oxsci_oma_mcp import tool_router
from oxsci_shared_core import default_router

from app.core.config import config

# Create FastAPI app
app = FastAPI(
    title=f"{config.SERVICE_NAME} MCP Server",
    description="MCP Server built with oxsci-oma-mcp",
    version=config.SERVICE_VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include MCP tool router (auto-imports app.tools for @oma_tool registration)
app.include_router(tool_router)

# Include shared core default router (provides / and /health endpoints)
app.include_router(default_router)
