"""
MCP Tools Package

Import all your tool modules here to ensure they are registered with @oma_tool.

Example:
    from . import example_tool  # noqa: F401
    from . import another_tool  # noqa: F401
"""

# Import your tools here
# Note: tool_router will auto-import this module when tools are discovered/executed
from . import tool_template  # noqa: F401 (enable=False - for reference only)
from . import example_data_service_tool  # noqa: F401 (enable=False - DataServiceClient example)
