"""
Example MCP Tool

This is a template for creating MCP tools using the @oma_tool decorator.
"""

from fastapi import Depends
from pydantic import BaseModel, Field
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext


# ==================== Models ====================


class ExampleToolRequest(BaseModel):
    """Example tool request model"""

    input_text: str = Field(..., description="Input text to process")
    uppercase: bool = Field(False, description="Convert to uppercase")


class ExampleToolResponse(BaseModel):
    """Example tool response model"""

    result: str = Field(..., description="Processed result")
    length: int = Field(..., description="Length of result")


# ==================== Tool Definition ====================


@oma_tool(
    description="Example tool that processes input text",
    version="1.0.0",
)
async def example_tool(
    request: ExampleToolRequest,
    context: IMCPToolContext = Depends(require_context),
) -> ExampleToolResponse:
    """
    Example tool implementation

    Features:
    - Process input text
    - Optionally convert to uppercase
    - Store result in context for tool chaining
    """
    # Access context data
    user_id = context.get_shared_data("user_id", "unknown")

    # Process the input
    result = request.input_text
    if request.uppercase:
        result = result.upper()

    # Add processing note
    result = f"[User: {user_id}] {result}"

    # Update context for next tool
    context.set_shared_data("last_result", result)
    context.set_shared_data("last_length", len(result))

    # Return response
    return ExampleToolResponse(result=result, length=len(result))
