# MCP Server Template

A scaffold template for building MCP (Model Context Protocol) servers using the [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp) framework.

## Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- AWS CLI configured with access to CodeArtifact (for installing dependencies from CodeArtifact)

> **Note**: Docker is only required for CI/CD deployment workflows, not for local development.

## Installation

### Installation Prerequisites

The installer script itself only requires **Python 3.11+** (uses only Python standard library, no external packages needed).

However, to complete the installation, you also need:
- **Git** installed (for initializing the repository)
- **Network connectivity** to GitHub (for downloading the template)
- **Write permissions** in the directory where you'll run the script

The installer will also check for:
- **AWS CLI** (warning only - required later for CodeArtifact access, but not needed during installation)

The installer will automatically check these prerequisites before proceeding.

### Option 1: Quick Install (Recommended)

Install directly from GitHub with a single command. You can use either command-line arguments (recommended) or interactive prompts.

> **Important**: Run the script from the **parent directory** where you want to create the service. For example:
> - To create `/git/mcp-my-service/`, run the script from `/git/` directory
> - The script will create `mcp-{service-name}/` in the current working directory

#### Direct Installation with Arguments (Recommended)

The simplest way - directly download and execute with parameters:

```bash
# Navigate to the parent directory where you want to create the service
cd /git

# Run the installer
curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py | python3 - \
  --service-name document-processor \
  --tool-name document_processor \
  --yes
```

Command-line options:
- `--service-name`: Service name (must start with a letter, lowercase letters/numbers/hyphens only)
- `--tool-name`: Initial tool name (must start with a letter, lowercase letters/numbers/underscores only)
- `--yes` or `-y`: Skip confirmation prompt (recommended for non-interactive mode)
- `--skip-env-check`: Skip environment prerequisites check (not recommended)

#### Interactive Mode

If you prefer to answer prompts interactively, download the script first:

```bash
# Navigate to the parent directory where you want to create the service
cd /git

# Download and run interactively
curl -sSL https://raw.githubusercontent.com/OxSci-AI/oxsci-mcp-scaffold/main/install.py > install.py
python3 install.py
```

The script will:
1. **Check environment prerequisites** (Python 3.11+, Git, network connectivity)
2. **Show current directory** and confirm where the service will be created
3. **Prompt for service name** (e.g., `document-processor` - will create `mcp-document-processor` directory)
4. **Prompt for tool name** (e.g., `document_processor` - will create the initial tool file and configure it)

> **Note**: If you try to use the pipe method without arguments, you'll get an `EOFError` because stdin is redirected. Always provide `--service-name` and `--tool-name` when using the pipe method.

The installer will:
1. Verify environment prerequisites (Python 3.11+, Git, network)
2. Download the latest scaffold template from GitHub
3. Create a new project directory with all files configured
4. Initialize a git repository
5. Set up the tool structure and configuration files

### Option 2: Manual Setup

If you prefer to clone the repository first:

```bash
# Clone the repository
git clone https://github.com/OxSci-AI/oxsci-mcp-scaffold.git
cd oxsci-mcp-scaffold

# Run setup script
python setup.py
```

The setup script will prompt you for:
- Service name (will create `mcp-{service-name}` directory)
- Tool name (will create the initial tool file and configure it)

## Quick Start

After installation, navigate to your new service directory:

```bash
cd mcp-{your-service-name}
```

### 1. Configure AWS CodeArtifact

Before installing dependencies, configure access to the private package repository:

```bash
# Make the script executable (if not already)
chmod +x entrypoint-dev.sh

# Run the configuration script (valid for 12 hours)
./entrypoint-dev.sh
```

> **Note**: The authentication token expires after 12 hours. Re-run this script when needed.

### 2. Install Dependencies

```bash
poetry install
```

### 3. Development

#### Run Server Locally

```bash
poetry run uvicorn app.core.main:app --reload --port 8060
```

Access the server at: http://localhost:8060
- API documentation: http://localhost:8060/docs
- Tool discovery: http://localhost:8060/tools/discover
- Tool list: http://localhost:8060/tools/list

#### Test Your Tools

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

## Project Structure

```
mcp-{service-name}/
├── .github/
│   └── workflows/
│       └── docker-builder.yml    # CI/CD workflow for building and deploying
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Service configuration
│   │   └── main.py               # FastAPI application entry point
│   └── tools/
│       ├── __init__.py           # Import tools here
│       ├── example_tool.py       # Example tool implementation
│       └── tool_template.py      # Comprehensive tool template (disabled)
├── tests/
│   └── test_example.py           # Example tests
├── .vscode/
│   └── extensions.json           # Recommended VS Code extensions
├── Dockerfile                     # Multi-stage Docker build
├── entrypoint-dev.sh             # CodeArtifact configuration script
├── install.py                    # Installer script (for creating new services)
├── setup.py                      # Setup script (for local setup)
├── pyproject.toml                # Project dependencies and configuration
└── README.md                      # This file
```

## Tool Development

### Creating a New Tool

1. Create a new file in `app/tools/` (e.g., `my_tool.py`)
2. Define Request/Response models using Pydantic
3. Use the `@oma_tool` decorator to register the tool
4. Implement the tool logic

**Basic Example:**

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

**Refer to `app/tools/tool_template.py` for a comprehensive example with:**
- Multiple parameter types (required, optional, with constraints)
- Custom validators
- Context chaining
- Error handling
- Detailed documentation

### Registering Your Tool

Import your tool in `app/tools/__init__.py`:

```python
from . import my_tool  # noqa: F401
```

### Restart the Server

The tool will be automatically discovered and available at `/tools/my_tool`

### Tool Discovery Behavior

- **`enable=True`** (default): Tool appears in `/tools/discover` (agents can find it)
- **`enable=False`**: Tool does NOT appear in `/tools/discover` but still appears in `/tools/list` with status "disabled"

## Configuration

Service configuration is managed through environment variables. See `app/core/config.py` for available options.

Key environment variables:

- `SERVICE_PORT`: Port to run the service (default: 8060)
- `ENV`: Environment (development/test/production)
- `LOG_LEVEL`: Logging level

For production deployments, use environment variables or AWS SSM parameters (managed by `oxsci-shared-core`).

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

## Deployment

### Building Docker Image

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

Example agent MCP configuration:

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

3. Remember to revert to the published version before committing:

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

## Tools and Frameworks

This template integrates:

- **FastAPI**: Web framework for building APIs
- **oxsci-oma-mcp**: MCP protocol implementation and tool router
- **oxsci-shared-core**: Shared utilities and configuration (optional)

## Related Projects

- [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp): MCP protocol package
- [oxsci-oma-core](https://github.com/OxSci-AI/oxsci-oma-core): OMA agent framework
- [oxsci-shared-core](https://github.com/OxSci-AI/oxsci-shared-core): Shared utilities

## License

© 2025 OxSci.AI. All rights reserved.
