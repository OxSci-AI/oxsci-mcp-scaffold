"""
MCP Server Configuration

Inherits from oxsci_shared_core.config.BaseConfig for standard configuration management.
Add MCP-server-specific configurations here.
"""

try:
    from oxsci_shared_core.config import base_config as config
except ImportError:
    # Fallback for development without shared-core
    from pydantic_settings import BaseSettings

    class Config(BaseSettings):
        SERVICE_NAME: str = "mcp-server-template"
        ENV: str = "local"

    config = Config()
