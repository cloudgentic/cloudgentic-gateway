"""MCP server exposing gateway capabilities as tools for AI agents."""
import os

import httpx
from fastmcp import FastMCP

GATEWAY_URL = os.environ.get("API_URL", "http://localhost:8421")

mcp = FastMCP(
    "CloudGentic Gateway",
    description="Secure bridge between AI agents and external user accounts",
)


async def _execute(api_key: str, provider: str, service: str, action: str, params: dict) -> dict:
    """Call the gateway agent/execute endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"provider": provider, "service": service, "action": action, "params": params},
        )
        return response.json()


@mcp.tool()
async def gmail_send(api_key: str, to: str, subject: str, body: str, cc: str | None = None) -> dict:
    """Send an email via Gmail through a connected Google account."""
    return await _execute(api_key, "google", "gmail", "send", {"to": to, "subject": subject, "body": body, "cc": cc})


@mcp.tool()
async def gmail_search(api_key: str, query: str, max_results: int = 10) -> dict:
    """Search Gmail messages."""
    return await _execute(api_key, "google", "gmail", "search", {"query": query, "max_results": max_results})


@mcp.tool()
async def gmail_read(api_key: str, message_id: str) -> dict:
    """Read a specific Gmail message."""
    return await _execute(api_key, "google", "gmail", "read", {"message_id": message_id})


@mcp.tool()
async def calendar_list_events(api_key: str, time_min: str | None = None, time_max: str | None = None, max_results: int = 10) -> dict:
    """List calendar events."""
    return await _execute(api_key, "google", "calendar", "list", {"time_min": time_min, "time_max": time_max, "max_results": max_results})


@mcp.tool()
async def calendar_create_event(api_key: str, summary: str, start: dict, end: dict, description: str | None = None, location: str | None = None, attendees: list[str] | None = None) -> dict:
    """Create a calendar event."""
    return await _execute(api_key, "google", "calendar", "create", {"summary": summary, "start": start, "end": end, "description": description, "location": location, "attendees": attendees})


@mcp.tool()
async def drive_list_files(api_key: str, query: str | None = None, max_results: int = 10) -> dict:
    """List files in Google Drive."""
    return await _execute(api_key, "google", "drive", "list", {"query": query, "max_results": max_results})


@mcp.tool()
async def drive_read_file(api_key: str, file_id: str) -> dict:
    """Read file metadata from Google Drive."""
    return await _execute(api_key, "google", "drive", "read", {"file_id": file_id})
