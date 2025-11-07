# Tool Development Guide

This guide covers how to develop, configure, and deploy MCP tools using the oxsci-oma-mcp framework.

## Table of Contents

- [Creating a New Tool](#creating-a-new-tool)
- [Tool Registration](#tool-registration)
- [Tool Discovery Behavior](#tool-discovery-behavior)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Integration with OMA Agents](#integration-with-oma-agents)
- [Development Tips](#development-tips)

## Creating a New Tool

### Step-by-Step Process

1. Create a new file in `app/tools/` (e.g., `my_tool.py`)
2. Define Request/Response models using Pydantic
3. Use the `@oma_tool` decorator to register the tool
4. Implement the tool logic
5. Import the tool in `app/tools/__init__.py`

### Basic Example

```python
# app/tools/my_tool.py
from fastapi import Depends
from pydantic import BaseModel, Field
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext


class MyToolRequest(BaseModel):
    """Request model for my_tool"""
    input_text: str = Field(..., description="Input text to process")


class MyToolResponse(BaseModel):
    """Response model for my_tool"""
    result: str = Field(..., description="Processed result")


@oma_tool(
    description="My custom tool for text processing",
    version="1.0.0",
    enable=True,  # Set to False to disable from agent discovery
)
async def my_tool(
    request: MyToolRequest,
    context: IMCPToolContext = Depends(require_context),
) -> MyToolResponse:
    """
    Tool implementation.

    Args:
        request: Tool request parameters
        context: MCP context for accessing shared data

    Returns:
        MyToolResponse with processed result
    """
    # Access context data from previous tools
    user_id = context.get_shared_data("user_id", "anonymous")

    # Process the input
    result = f"[User: {user_id}] Processed: {request.input_text}"

    # Store result for next tools in chain
    context.set_shared_data("last_result", result)

    return MyToolResponse(result=result)
```

### Comprehensive Example

Refer to `app/tools/tool_template.py` in your project for a comprehensive example with:

- Multiple parameter types (required, optional, with constraints)
- Custom validators
- Context chaining
- Error handling
- Detailed documentation

## Tool Registration

After creating your tool, import it in `app/tools/__init__.py`:

```python
from . import my_tool  # noqa: F401
```

The tool will be automatically discovered and available at `/tools/my_tool` after server restart.

## Tool Discovery Behavior

The `enable` parameter in the `@oma_tool` decorator controls tool visibility:

- **`enable=True`** (default): Tool appears in `/tools/discover` (agents can find it)
- **`enable=False`**: Tool does NOT appear in `/tools/discover` but still appears in `/tools/list` with status "disabled"

This allows you to:
- Keep tools in development hidden from agents
- Temporarily disable tools without removing code
- Maintain internal-only tools

## Configuration

Service configuration is managed through environment variables. See `app/core/config.py` for available options.

### Key Environment Variables

- `SERVICE_PORT`: Port to run the service (default: 8060)
- `ENV`: Environment (development/test/production)
- `LOG_LEVEL`: Logging level

### Production Configuration

For production deployments, use environment variables or AWS SSM parameters (managed by `oxsci-shared-core`).

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test types
poetry run pytest -m unit
poetry run pytest -m integration
```

### Testing Your Tools

**Check server status:**
```bash
curl http://localhost:8060/
```

**Discover available tools:**
```bash
curl http://localhost:8060/tools/discover
```

**List all tools (including disabled ones):**
```bash
curl http://localhost:8060/tools/list
```

**Execute a tool:**
```bash
curl -X POST http://localhost:8060/tools/example_tool \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "input_text": "Hello World",
      "uppercase": true
    },
    "context": {
      "user_id": "user123"
    }
  }'
```

## Deployment

### CI/CD Workflow

The CI/CD workflow automatically builds and pushes Docker images when:

- Tags matching `v*` are pushed
- Manually triggered via workflow_dispatch

### Manual Deployment

```bash
# Build image
docker build -t your-mcp-server .

# Run container
docker run -p 8060:8060 \
  -e ENV=test \
  your-mcp-server
```

## Integration with OMA Agents

This MCP server can be integrated with OMA agent services to provide tools for agents:

1. **Deploy your MCP server** to a publicly accessible URL
2. **Register it in the agent's MCP configuration** (see oxsci-oma-core documentation)
3. **Tools will be automatically discovered** and available to agents via `/tools/discover`

### Example Agent MCP Configuration

```python
from oxsci_oma_core import AgentConfig

config = AgentConfig(
    mcp_servers={
        "my_mcp_server": {
            "enabled": True,
            "base_url": "https://my-mcp-server.example.com",
            "description": "Custom tools for document processing"
        }
    }
)
```

## Development Tips

### Local Development with oxsci-oma-mcp

To develop against a local version of oxsci-oma-mcp:

1. Edit `pyproject.toml`:

```toml
[tool.poetry.group.dev.dependencies]
oxsci-oma-mcp = { path = "../oxsci-oma-mcp", develop = true }
```

2. Run:

```bash
poetry lock
poetry install --with dev
```

3. **Important**: Remember to revert to the published version before committing:

```toml
[tool.poetry.dependencies]
oxsci-oma-mcp = { version = ">=0.1.0", source = "oxsci-ca" }
```

### External Service Integration

Use `oxsci-shared-core` for calling other services:

```python
from oxsci_shared_core.auth_service import ServiceClient

service_client = ServiceClient("my-mcp-server")
data = await service_client.call_service(
    target_service_url="https://data-service.example.com",
    method="GET",
    endpoint="/data/items"
)
```

### Best Practices

1. **Request/Response Models**: Always define clear Pydantic models with descriptions
2. **Error Handling**: Use appropriate exception handling and return meaningful errors
3. **Context Usage**: Leverage the MCP context for sharing data between tools in a chain
4. **Testing**: Write tests for your tools before deploying
5. **Documentation**: Keep your tool descriptions clear and accurate for agent discovery
6. **Versioning**: Use semantic versioning for your tools

## Related Projects

- [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp): MCP protocol package
- [oxsci-oma-core](https://github.com/OxSci-AI/oxsci-oma-core): OMA agent framework
- [oxsci-shared-core](https://github.com/OxSci-AI/oxsci-shared-core): Shared utilities
