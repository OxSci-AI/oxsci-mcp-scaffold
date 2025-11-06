"""
Tool Template - Comprehensive MCP Tool Example

This is a complete template file for creating new MCP tools using the @oma_tool decorator.
Copy this file and modify it to create your own tools.

Key Concepts:
- Request/Response models with proper validation using Pydantic
- Context injection for accessing shared data across tool chains
- Proper parameter types (required, optional, default values)
- Error handling and validation
- Tool chaining through context.set_shared_data / get_shared_data

When to use enable=False:
- During development (tool not ready for production)
- For internal/debug tools that shouldn't be exposed to agents
- Tools that are disabled but kept for reference

Effect of enable=False:
- Tool will NOT appear in /tools/discover (agent tool discovery)
- Tool WILL appear in /tools/list (complete tool inventory)
- Tool can still be executed directly via POST /tools/{tool_name}
"""

from typing import Optional, List
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext


# ==================== Request/Response Models ====================


class ToolTemplateRequest(BaseModel):
    """
    Request model for tool_template

    Demonstrates different parameter types and validation patterns.
    """

    # Required parameter - must be provided
    input_text: str = Field(
        ...,  # ... means required
        description="Input text to process",
        min_length=1,
        max_length=10000,
    )

    # Optional parameter with default value
    uppercase: bool = Field(
        default=False,
        description="Convert to uppercase if True",
    )

    # Optional parameter that can be None
    prefix: Optional[str] = Field(
        default=None,
        description="Optional prefix to add to result",
        max_length=100,
    )

    # Parameter with constraints
    repeat_count: int = Field(
        default=1,
        description="Number of times to repeat the text",
        ge=1,  # greater than or equal to 1
        le=10,  # less than or equal to 10
    )

    # List parameter with default empty list
    tags: List[str] = Field(
        default_factory=list,
        description="Optional tags to attach (max 20 items)",
    )

    # Custom validator example (Pydantic V2 style)
    @field_validator("input_text")
    @classmethod
    def validate_input_text(cls, v: str) -> str:
        """Custom validation for input_text"""
        if not v or v.isspace():
            raise ValueError("Input text cannot be empty or whitespace only")
        return v.strip()


class ToolTemplateResponse(BaseModel):
    """
    Response model for tool_template

    Always define clear response structure for better API documentation.
    """

    result: str = Field(
        ...,
        description="Processed result text",
    )

    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata about the processing",
    )

    length: int = Field(
        ...,
        description="Length of the result text",
    )

    processing_info: dict = Field(
        default_factory=dict,
        description="Information about how the text was processed",
    )


# ==================== Tool Definition ====================


@oma_tool(
    description="Template tool demonstrating comprehensive MCP tool patterns and best practices",
    version="1.0.0",
    enable=False,  # Set to False during development or to disable from agent discovery
)
async def tool_template(
    request: ToolTemplateRequest,
    context: IMCPToolContext = Depends(require_context),
) -> ToolTemplateResponse:
    """
    Comprehensive tool template implementation.

    This tool demonstrates:
    - Different parameter types (required, optional, with defaults)
    - Context usage for tool chaining
    - Proper error handling
    - Metadata tracking
    - Business logic implementation

    Context Usage:
    - Use context.get_shared_data(key, default) to read data from previous tools
    - Use context.set_shared_data(key, value) to pass data to next tools
    - Context is shared across all tools in a single execution chain

    Args:
        request: Tool request parameters (automatically validated by Pydantic)
        context: MCP context for accessing shared data across tool chains

    Returns:
        ToolTemplateResponse with processed result and metadata

    Raises:
        HTTPException: If processing fails (e.g., validation errors, business logic errors)

    Example Usage:
        POST /tools/tool_template
        {
            "arguments": {
                "input_text": "Hello World",
                "uppercase": true,
                "prefix": ">> ",
                "repeat_count": 2,
                "tags": ["example", "demo"]
            },
            "context": {
                "user_id": "user123",
                "session_id": "session456"
            }
        }
    """

    # ==================== 1. Access Context Data ====================
    # Get data from previous tools in the chain (if any)
    # Always provide a default value to handle the case when the key doesn't exist
    user_id = context.get_shared_data("user_id", "anonymous")
    previous_result = context.get_shared_data("last_result", None)
    execution_count = context.get_shared_data("execution_count", 0)

    # ==================== 2. Business Logic / Processing ====================
    # Start with input text (already validated by Pydantic)
    result = request.input_text

    # Apply uppercase transformation if requested
    if request.uppercase:
        result = result.upper()

    # Add prefix if provided
    if request.prefix:
        result = f"{request.prefix}{result}"

    # Repeat the text if repeat_count > 1
    if request.repeat_count > 1:
        result = " ".join([result] * request.repeat_count)

    # Example: If there was a previous result in the chain, append it
    if previous_result:
        result = f"{result}\n[Previous: {previous_result}]"

    # ==================== 3. Build Metadata ====================
    metadata = {
        "processed_by": user_id,
        "tags": request.tags,
        "uppercase_applied": request.uppercase,
        "prefix_applied": request.prefix is not None,
        "repeat_count": request.repeat_count,
        "has_previous_result": previous_result is not None,
    }

    processing_info = {
        "original_text": request.input_text,
        "original_length": len(request.input_text),
        "result_length": len(result),
        "transformations": [],
    }

    # Track what transformations were applied
    if request.uppercase:
        processing_info["transformations"].append("uppercase")
    if request.prefix:
        processing_info["transformations"].append(f"prefix: {request.prefix}")
    if request.repeat_count > 1:
        processing_info["transformations"].append(f"repeated {request.repeat_count}x")

    # ==================== 4. Update Context for Next Tools ====================
    # Store results that might be useful for subsequent tools in the chain
    context.set_shared_data("last_result", result)
    context.set_shared_data("last_length", len(result))
    context.set_shared_data("execution_count", execution_count + 1)
    context.set_shared_data("last_tool", "tool_template")

    # Store tags for potential filtering by later tools
    if request.tags:
        context.set_shared_data("last_tags", request.tags)

    # ==================== 5. Return Response ====================
    return ToolTemplateResponse(
        result=result,
        metadata=metadata,
        length=len(result),
        processing_info=processing_info,
    )


# ==================== Additional Examples ====================

"""
Example 1: Simple text processing
POST /tools/tool_template
{
    "arguments": {
        "input_text": "hello world"
    },
    "context": {}
}
Response: {"result": "hello world", "length": 11, ...}

Example 2: Complex transformation
POST /tools/tool_template
{
    "arguments": {
        "input_text": "test",
        "uppercase": true,
        "prefix": ">> ",
        "repeat_count": 3,
        "tags": ["important", "demo"]
    },
    "context": {
        "user_id": "user123"
    }
}
Response: {"result": ">> TEST >> TEST >> TEST", "length": 23, ...}

Example 3: Tool chaining (this tool can read data from previous tools)
If previous tool stored data in context, this tool can access it:
- context.get_shared_data("last_result") - get previous result
- context.get_shared_data("user_preferences") - get user settings
- etc.

Tool Discovery:
- With enable=True: Tool appears in /tools/discover (agents can find it)
- With enable=False: Tool does NOT appear in /tools/discover
- Always appears in /tools/list regardless of enable flag
- Can still be executed via POST /tools/tool_template regardless of enable flag
"""
