"""
MCP Server Configuration

Inherits from oxsci_shared_core.config.BaseConfig for standard configuration management.
Add MCP-server-specific configurations here.
"""

from oxsci_shared_core.config import BaseConfig


class Config(BaseConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    SERVICE_PORT: int = 8060


config = Config()
