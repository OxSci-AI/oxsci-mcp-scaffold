# Tool Development Guide

This guide covers how to develop, configure, and deploy MCP tools using the oxsci-oma-mcp framework.

## Table of Contents

- [Creating a New Tool](#creating-a-new-tool)
- [Tool Registration](#tool-registration)
- [Tool Discovery Behavior](#tool-discovery-behavior)
- [Authentication Forwarding](#authentication-forwarding)
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
from fastapi import Depends, Request
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
    request: MyToolRequest,  # Business parameters (Pydantic model)
    context: IMCPToolContext = Depends(require_context),
    fastapi_request: Request = None,  # Optional: FastAPI Request for auth forwarding
) -> MyToolResponse:
    """
    Tool implementation.

    Args:
        request: Tool request parameters
        context: MCP context for accessing shared data
        fastapi_request: Optional FastAPI Request object for authentication forwarding

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

**Note**: The `fastapi_request` parameter is optional and automatically injected by the framework. Include it only when your tool needs to call downstream services with authentication.

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

## Authentication Forwarding

### Overview

When your tool needs to call downstream services (e.g., data-service, llm-service), you should forward the caller's authentication to maintain the security context throughout the request chain.

### How It Works

The `fastapi_request: Request` parameter is automatically injected with the FastAPI Request object, which contains authentication headers from the caller (user token or service token).

### Example: Tool with Authentication Forwarding

```python
from fastapi import Depends, Request
from pydantic import BaseModel, Field
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext
from oxsci_shared_core.auth_service import ServiceClient
from app.core.config import config


class ProcessDocumentRequest(BaseModel):
    """Request model for document processing"""
    document_id: str = Field(..., description="Document ID to process")
    options: dict = Field(default_factory=dict, description="Processing options")


class ProcessDocumentResponse(BaseModel):
    """Response model for document processing"""
    result: str = Field(..., description="Processing result")
    metadata: dict = Field(..., description="Document metadata")


@oma_tool(
    description="Process document with data service integration",
    version="1.0.0",
    enable=True
)
async def process_document(
    request: ProcessDocumentRequest,
    context: IMCPToolContext = Depends(require_context),
    fastapi_request: Request = None  # Auto-injected for auth forwarding
) -> ProcessDocumentResponse:
    """
    Process document by calling data service with authentication forwarding.

    The fastapi_request parameter contains authentication info from the caller
    and is automatically forwarded to downstream services.
    """
    # Initialize service client
    service_client = ServiceClient(config.SERVICE_NAME)

    # Call data service with authentication forwarding
    # The user_request parameter ensures auth tokens are passed through
    doc_data = await service_client.call_service(
        target_service_url=config.DATA_SERVICE_URL,
        method="GET",
        endpoint=f"/documents/{request.document_id}",
        user_request=fastapi_request  # ✅ Forward authentication
    )

    # Process the document
    result = f"Processed document: {doc_data['title']}"

    # Store in context for tool chaining
    context.set_shared_data("last_doc_id", request.document_id)

    return ProcessDocumentResponse(
        result=result,
        metadata=doc_data.get("metadata", {})
    )
```

### Authentication Flow

```
1. Caller → POST /tools/process_document (with Authorization header)
2. tool_router → Receives request with authentication in fastapi_request
3. tool_router → Injects fastapi_request into tool function
4. Tool → Calls service_client.call_service(..., user_request=fastapi_request)
5. ServiceClient → Forwards authentication to downstream service
6. Downstream Service → Validates and processes with original auth context
```

### Benefits

✅ **Seamless auth propagation** across service boundaries
✅ **No manual token extraction** required
✅ **Maintains security context** throughout the request chain
✅ **Supports both user and service tokens**
✅ **Complies with Oxsci.AI development standards**

### Important Notes

- The `fastapi_request` parameter is **optional** and only needed when calling downstream services
- The parameter is **automatically injected** by the framework
- The parameter name can be anything, but `fastapi_request` is recommended for clarity
- The parameter is **excluded from tool schema** (not visible in `/tools/discover`)

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

#### Using DataServiceClient (Recommended - oxsci-oma-mcp >= 0.2.0)

For calling the data service, use the injected `IDataServiceClient` from `oxsci-oma-mcp` for simplified and consistent API calls:

```python
from fastapi import Depends
from oxsci_oma_mcp import (
    oma_tool,
    require_context,
    IMCPToolContext,
    IDataServiceClient,
    require_data_service,
)

@oma_tool(description="Example tool using DataServiceClient")
async def my_tool(
    request: MyToolRequest,
    context: IMCPToolContext = Depends(require_context),
    data_service: IDataServiceClient = Depends(require_data_service)
) -> MyToolResponse:
    # ✅ RECOMMENDED: Use injected IDataServiceClient
    # Simple GET request
    data = await data_service.call(
        method="GET",
        endpoint="/documents/123"
    )

    # GET with query parameters
    sections = await data_service.call(
        method="GET",
        endpoint="/article_structured_contents/overviews/{overview_id}/sections",
        path_params={"overview_id": "some_id"},
        query_params={"user_id": "user123"}
    )

    # POST with JSON body
    created = await data_service.call(
        method="POST",
        endpoint="/documents",
        json_data={"title": "New Document", "content": "..."}
    )

    return MyToolResponse(data=data)
```

**Benefits of IDataServiceClient:**

✅ **Automatic injection** - Provided by oxsci-oma-mcp, no manual setup needed
✅ **Pre-configured** - DATA_SERVICE_URL automatically loaded from config
✅ **Authentication auto-forwarded** - No need to pass user_request
✅ **Single instance per request** - Reused across multiple calls in same tool
✅ **Clean API** - Only specify method and endpoint
✅ **Less boilerplate** - Reduces code by ~60% compared to manual ServiceClient
✅ **Consistent pattern** - Same injection pattern as require_context

**How it works:**

1. The `tool_router` in oxsci-oma-mcp automatically creates a `DataServiceClient` at the start of each request
2. It reads `DATA_SERVICE_URL` and `SERVICE_NAME` from your config
3. It passes the FastAPI Request object for authentication forwarding
4. The client is stored in a ContextVar and injected via `require_data_service()`
5. After request completion, the client is automatically cleaned up

**Requirements:**

- oxsci-oma-mcp >= 0.2.0 (includes IDataServiceClient)
- `DATA_SERVICE_URL` configured in your config
- `SERVICE_NAME` configured in your config

#### Using ServiceClient Directly (For Other Services)

For services other than data service, use ServiceClient with authentication forwarding:

```python
from fastapi import Request, Depends
from oxsci_shared_core.auth_service import ServiceClient
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext
from app.core.config import config

@oma_tool(description="Example tool calling other services")
async def my_tool(
    request: MyToolRequest,
    context: IMCPToolContext = Depends(require_context),
    fastapi_request: Request = None  # Required for auth forwarding
) -> MyToolResponse:
    # Initialize service client
    service_client = ServiceClient(config.SERVICE_NAME)

    # ✅ CORRECT: Forward authentication
    data = await service_client.call_service(
        target_service_url=config.LLM_SERVICE_URL,  # Or other service URL
        method="GET",
        endpoint="/models",
        user_request=fastapi_request  # ✅ Forward auth
    )

    # ❌ INCORRECT: Don't call services without auth forwarding
    # This will fail authentication on downstream services
    # data = await service_client.call_service(
    #     target_service_url=config.LLM_SERVICE_URL,
    #     method="GET",
    #     endpoint="/models"
    # )

    return MyToolResponse(data=data)
```

**Key Points:**

- **For data service**: Use `DataServiceClient` with `Depends(require_data_service)` (recommended)
- **For other services**: Use `ServiceClient` with `fastapi_request: Request = None` parameter
- **Always** pass `user_request=fastapi_request` to `service_client.call_service()` when using ServiceClient directly
- This ensures authentication tokens (user or service) are properly forwarded
- Failing to forward auth will result in 401/403 errors from downstream services

### Best Practices

1. **Request/Response Models**: Always define clear Pydantic models with descriptions
   ```python
   class MyToolRequest(BaseModel):
       param: str = Field(..., description="Clear description")
   ```

2. **Data Service Calls**: Use the injected `IDataServiceClient` from oxsci-oma-mcp for cleaner code
   ```python
   from oxsci_oma_mcp import IDataServiceClient, require_data_service

   @oma_tool(...)
   async def my_tool(
       request: MyToolRequest,
       context: IMCPToolContext = Depends(require_context),
       data_service: IDataServiceClient = Depends(require_data_service)
   ):
       # Clean and simple - no need for ServiceClient creation or auth forwarding
       data = await data_service.call(
           method="GET",
           endpoint="/documents/123"
       )
   ```

3. **Other Service Calls**: Always include `fastapi_request: Request = None` when calling non-data services
   ```python
   @oma_tool(...)
   async def my_tool(
       request: MyToolRequest,
       context: IMCPToolContext = Depends(require_context),
       fastapi_request: Request = None  # Required for service calls
   ):
       service_client = ServiceClient(config.SERVICE_NAME)
       await service_client.call_service(
           target_service_url=config.LLM_SERVICE_URL,
           ...,
           user_request=fastapi_request  # Forward auth
       )
   ```

3. **Error Handling**: Use appropriate exception handling and return meaningful errors
   - Don't catch `HTTPException` - let them propagate to maintain HTTP status codes
   - Handle business logic errors appropriately
   ```python
   try:
       data = await service_client.call_service(...)
   except HTTPException:
       raise  # Re-raise HTTP exceptions to preserve status codes
   except Exception as e:
       logger.error(f"Tool error: {e}")
       raise
   ```

4. **Context Usage**: Leverage the MCP context for sharing data between tools in a chain
   ```python
   # Store data for next tools
   context.set_shared_data("result", my_result)
   # Read data from previous tools
   prev_result = context.get_shared_data("result", default=None)
   ```

5. **Testing**: Write tests for your tools before deploying
   - Unit tests for tool logic
   - Integration tests for service calls
   - Mock downstream services appropriately

6. **Documentation**: Keep your tool descriptions clear and accurate for agent discovery
   - Write clear `description` in `@oma_tool`
   - Add comprehensive docstrings
   - Use descriptive Field descriptions

7. **Versioning**: Use semantic versioning for your tools
   - Increment PATCH for bug fixes
   - Increment MINOR for new features
   - Increment MAJOR for breaking changes

8. **Parameter Naming**: Follow consistent naming conventions
   - `request`: For Pydantic business parameters
   - `context`: For MCP context (use `Depends(require_context)`)
   - `fastapi_request`: For FastAPI Request object (optional, for auth forwarding)

## Related Projects

- [oxsci-oma-mcp](https://github.com/OxSci-AI/oxsci-oma-mcp): MCP protocol package
- [oxsci-oma-core](https://github.com/OxSci-AI/oxsci-oma-core): OMA agent framework
- [oxsci-shared-core](https://github.com/OxSci-AI/oxsci-shared-core): Shared utilities
