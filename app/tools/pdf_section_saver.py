"""
PDF Section Saver Tool

A tool that demonstrates proper UTF-8 encoding when saving PDF sections
to an external data service. This solves the Latin-1 encoding issue.
"""

from fastapi import Depends
from pydantic import BaseModel, Field
from oxsci_oma_mcp import oma_tool, require_context, IMCPToolContext
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ==================== Models ====================


class PDFSectionRequest(BaseModel):
    """Request model for saving PDF sections"""

    paper_id: str = Field(..., description="Paper ID")
    section_title: str = Field(..., description="Section title (may contain Unicode)")
    section_content: str = Field(..., description="Section content (may contain Unicode)")
    section_order: int = Field(..., description="Section order number")
    data_service_url: str = Field(
        ...,
        description="Data service base URL (e.g., https://data-service.example.com)"
    )


class PDFSectionResponse(BaseModel):
    """Response model for PDF section saving"""

    success: bool = Field(..., description="Whether the save was successful")
    section_id: Optional[str] = Field(None, description="Created section ID")
    error: Optional[str] = Field(None, description="Error message if failed")
    encoding_used: str = Field(..., description="Encoding used for the request")


# ==================== Tool Definition ====================


@oma_tool(
    description="Save PDF section to data service with proper UTF-8 encoding",
    version="1.0.0",
)
async def pdf_section_saver(
    request: PDFSectionRequest,
    context: IMCPToolContext = Depends(require_context),
) -> PDFSectionResponse:
    """
    Save PDF section to external data service with correct UTF-8 encoding.

    This tool demonstrates the CORRECT way to handle Unicode content:
    - Explicitly use UTF-8 encoding
    - Set proper Content-Type headers
    - Handle encoding errors gracefully

    Features:
    - Supports Unicode characters (e.g., \u201c, \u2705)
    - Proper error handling for encoding issues
    - Logs encoding details for debugging
    """
    user_id = context.get_shared_data("user_id", "unknown")

    logger.info(
        f"Saving PDF section for paper {request.paper_id}, "
        f"order {request.section_order}, user {user_id}"
    )

    # Prepare the payload
    payload = {
        "paper_id": request.paper_id,
        "title": request.section_title,
        "content": request.section_content,
        "order": request.section_order,
        "user_id": user_id,
    }

    # Log encoding info for debugging
    logger.info(f"Section title: {request.section_title}")
    logger.info(f"Title encoded as UTF-8: {request.section_title.encode('utf-8')}")

    try:
        # ========== CRITICAL: Proper UTF-8 Encoding ==========
        # Use httpx with explicit UTF-8 encoding
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{request.data_service_url}/api/sections",
                json=payload,  # httpx automatically uses UTF-8 for json parameter
                headers={
                    "Content-Type": "application/json; charset=utf-8",  # Explicit UTF-8
                    "Accept": "application/json",
                },
                timeout=30.0,
            )

            # Check response status
            response.raise_for_status()

            # Parse response
            response_data = response.json()
            section_id = response_data.get("id") or response_data.get("section_id")

            logger.info(f"Successfully saved section {section_id}")

            # Store result in context for tool chaining
            context.set_shared_data("last_saved_section_id", section_id)
            context.set_shared_data("last_saved_paper_id", request.paper_id)

            return PDFSectionResponse(
                success=True,
                section_id=section_id,
                error=None,
                encoding_used="utf-8",
            )

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"Failed to save section: {error_msg}")

        return PDFSectionResponse(
            success=False,
            section_id=None,
            error=error_msg,
            encoding_used="utf-8",
        )

    except UnicodeEncodeError as e:
        error_msg = f"Encoding error: {str(e)}"
        logger.error(f"Unicode encoding failed: {error_msg}")

        return PDFSectionResponse(
            success=False,
            section_id=None,
            error=error_msg,
            encoding_used="utf-8-failed",
        )

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error: {error_msg}", exc_info=True)

        return PDFSectionResponse(
            success=False,
            section_id=None,
            error=error_msg,
            encoding_used="utf-8",
        )


# ==================== Alternative: Using requests library ==========

"""
If you need to use the 'requests' library instead of httpx, here's how:

import requests
import json

# WRONG WAY (causes Latin-1 encoding):
response = requests.post(url, data=json.dumps(payload))

# CORRECT WAY:
response = requests.post(
    url,
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    headers={'Content-Type': 'application/json; charset=utf-8'}
)

# OR (even better):
response = requests.post(
    url,
    json=payload,  # requests automatically uses UTF-8 when you use 'json' parameter
    headers={'Content-Type': 'application/json; charset=utf-8'}
)
"""
