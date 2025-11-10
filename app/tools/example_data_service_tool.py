"""
Example tool demonstrating DataServiceClient usage

This tool shows how to use the injected DataServiceClient from oxsci-oma-mcp
to call data service endpoints with minimal boilerplate code.

Note: IDataServiceClient and require_data_service are provided by oxsci-oma-mcp >= 0.2.0
"""

from fastapi import Depends
from pydantic import BaseModel, Field

from oxsci_oma_mcp import (
    oma_tool,
    require_context,
    IMCPToolContext,
    IDataServiceClient,
    require_data_service,
)


class ExampleDataServiceRequest(BaseModel):
    """Request model for example_data_service_tool"""

    overview_id: str = Field(
        ..., description="Overview ID to fetch sections from data service"
    )
    user_id: str = Field(default=None, description="Optional user ID for filtering")


class ExampleDataServiceResponse(BaseModel):
    """Response model for example_data_service_tool"""

    overview_id: str = Field(..., description="Overview ID that was fetched")
    sections: list = Field(..., description="List of sections from data service")
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the operation"
    )


@oma_tool(
    description="Example tool demonstrating DataServiceClient usage with data service integration",
    version="1.0.0",
    enable=False,  # Set to True to enable this tool
)
async def example_data_service_tool(
    request: ExampleDataServiceRequest,
    context: IMCPToolContext = Depends(require_context),
    data_service: IDataServiceClient = Depends(require_data_service),
) -> ExampleDataServiceResponse:
    """
    Example tool demonstrating simplified data service calls using DataServiceClient.

    This tool shows:
    - How to inject IDataServiceClient via Depends(require_data_service)
    - How to make clean API calls without boilerplate code
    - How authentication is automatically forwarded
    - How to handle responses from data service

    Comparison with old pattern:
        OLD:
            service_client = ServiceClient(f"{config.SERVICE_NAME}-get_sections")
            sections = await service_client.call_service(
                target_service_url=config.DATA_SERVICE_URL,
                method="GET",
                endpoint=f"/article_structured_contents/overviews/{overview_id}/sections",
                timeout=30,
                query_params={**({"user_id": user_id} if user_id else {})},
            )

        NEW:
            sections = await data_service.call(
                method="GET",
                endpoint=f"/article_structured_contents/overviews/{overview_id}/sections",
                query_params={"user_id": user_id} if user_id else {},
            )

    Args:
        request: Tool request parameters
        context: MCP context for accessing shared data (auto-injected by tool_router)
        data_service: Data service client (auto-injected by tool_router)

    Returns:
        ExampleDataServiceResponse with sections data and metadata

    Example:
        POST /tools/example_data_service_tool
        {
            "arguments": {
                "overview_id": "overview_123",
                "user_id": "user_456"
            },
            "context": {}
        }
    """
    # Get user_id from request or context
    user_id = request.user_id or context.get_shared_data("user_id", None)

    # ==================== Clean and Simple Data Service Call ====================
    # No need to:
    # - Create ServiceClient
    # - Pass target_service_url
    # - Pass user_request for authentication
    # All handled automatically by DataServiceClient!

    try:
        sections = await data_service.call(
            method="GET",
            endpoint=f"/article_structured_contents/overviews/{request.overview_id}/sections",
            query_params={"user_id": user_id} if user_id else {},
            timeout=30,
        )
    except Exception as e:
        # Handle error (endpoint might not exist in your data service)
        sections = []
        metadata = {
            "error": str(e),
            "note": "This is a demonstration tool. Adjust the endpoint to match your data service API.",
        }
    else:
        metadata = {
            "overview_id": request.overview_id,
            "user_id": user_id,
            "section_count": len(sections) if isinstance(sections, list) else 0,
        }

    # ==================== Store in context for tool chaining ====================
    context.set_shared_data("last_overview_id", request.overview_id)
    context.set_shared_data("last_sections", sections)

    # ==================== Return response ====================
    return ExampleDataServiceResponse(
        overview_id=request.overview_id, sections=sections, metadata=metadata
    )


# ==================== Benefits Summary ====================
"""
Benefits of using IDataServiceClient (from oxsci-oma-mcp):

✅ **Automatic Injection**: No manual client creation
✅ **Pre-configured**: DATA_SERVICE_URL auto-loaded from config
✅ **Auth Forwarding**: Authentication automatically passed through
✅ **Single Instance**: Reused across multiple calls in same request
✅ **Clean API**: Only specify method and endpoint
✅ **Less Code**: Reduces boilerplate by ~60%
✅ **Consistent Pattern**: Same as require_context from oxsci-oma-mcp

Code Reduction Example:
    Before: 6 lines to make a data service call
    After:  3 lines to make the same call
    Reduction: 50% less code, 100% clearer intent
"""
