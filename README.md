# MCP Server Template

A scaffold project for building MCP (Model Context Protocol) servers using [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp).

## Features

- FastAPI-based MCP server
- Built-in tool router with automatic discovery
- Example tool implementation
- Docker support
- CI/CD workflow for deployment (template ready)

## Quick Start

### 1. Setup

```bash
# Clone this repository
git clone https://github.com/your-org/your-mcp-server.git
cd your-mcp-server

# Configure CodeArtifact access
./entrypoint-dev.sh

# Install dependencies
poetry install
```

### 2. Run Locally

```bash
# Start the server
poetry run python -m app.core.main

# Or with uvicorn directly
poetry run uvicorn app.core.main:app --host 0.0.0.0 --port 8060 --reload
```

The server will start at `http://localhost:8060`

### 3. Test the API

**Check server status:**
```bash
curl http://localhost:8060/
```

**Discover available tools:**
```bash
curl http://localhost:8060/tools/discover
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

## Project Structure

```
.
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration
│   │   └── main.py            # FastAPI application
│   └── tools/
│       ├── __init__.py         # Import tools here
│       └── example_tool.py     # Example tool implementation
├── tests/                      # Test files
├── .github/
│   └── workflows/
│       └── docker-builder.yml  # CI/CD workflow (template)
├── Dockerfile                  # Docker configuration
├── pyproject.toml             # Poetry dependencies
├── entrypoint-dev.sh          # CodeArtifact setup script
└── README.md
```

## Creating New Tools

### 1. Create a new tool file in `app/tools/`

```python
# app/tools/my_tool.py
from fastapi import Depends
from pydantic import BaseModel, Field
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext


class MyToolRequest(BaseModel):
    param1: str = Field(..., description="Parameter description")


class MyToolResponse(BaseModel):
    result: str = Field(..., description="Result description")


@oma_tool(
    description="My custom tool",
    version="1.0.0",
)
async def my_tool(
    request: MyToolRequest,
    context: IMCPToolContext = Depends(require_context),
) -> MyToolResponse:
    # Your tool implementation
    result = f"Processed: {request.param1}"
    return MyToolResponse(result=result)
```

### 2. Import in `app/tools/__init__.py`

```python
from . import my_tool  # noqa: F401
```

### 3. Restart the server

The tool will be automatically discovered and available at `/tools/my_tool`

## Configuration

Edit `app/core/config.py` to customize:

- Service name
- Environment variables
- External service URLs

For production deployments, use environment variables or AWS SSM parameters.

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test types
poetry run pytest -m unit
poetry run pytest -m integration
```

## Docker

### Build

```bash
docker build -t my-mcp-server:latest .
```

### Run

```bash
docker run -p 8060:8060 \
  -e ENV=production \
  -e SERVICE_NAME=my-mcp-server \
  my-mcp-server:latest
```

## Deployment

The project includes a GitHub Actions workflow template for automated deployment:

1. Update `pyproject.toml` with your service name
2. Configure AWS credentials in GitHub secrets
3. Push to main branch or create a tag to trigger deployment

```bash
# Deploy using gh cli
gh workflow run docker-builder.yml \
  --field deploy_to_test=true \
  --field pump_version=patch
```

## Integration with OMA Core

If you're building tools for an OMA agent service:

1. Deploy your MCP server
2. Register it in the agent's MCP configuration
3. Tools will be automatically discovered and available to agents

Example MCP configuration:
```yaml
mcp_servers:
  my_mcp_server:
    enabled: true
    base_url: "https://my-mcp-server.example.com"
    description: "Custom tools for my agent"
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

### External Service Integration

Use `oxsci-shared-core` for calling other services:

```bash
poetry add oxsci-shared-core --source oxsci-ca
```

```python
from oxsci_shared_core.auth import ServiceClient

service_client = ServiceClient("my-mcp-server")
data = await service_client.call_service(
    target_service_url="https://data-service.example.com",
    method="GET",
    endpoint="/data/items"
)
```

## Related Projects

- [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp): MCP protocol package
- [oxsci-oma-core](https://github.com/OxSci-AI/oxsci-oma-core): OMA framework
- [oxsci-shared-core](https://github.com/OxSci-AI/oxsci-shared-core): Shared utilities

## License

Proprietary - OxSci.AI
