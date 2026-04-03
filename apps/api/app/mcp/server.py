"""MCP server exposing gateway capabilities as tools for AI agents."""
from fastmcp import FastMCP

mcp = FastMCP(
    "CloudGentic Gateway",
    description="Secure bridge between AI agents and external user accounts",
)


@mcp.tool()
async def gmail_send(
    api_key: str,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
) -> dict:
    """Send an email via Gmail through a connected Google account."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "gmail",
                "action": "send",
                "params": {"to": to, "subject": subject, "body": body, "cc": cc},
            },
        )
        return response.json()


@mcp.tool()
async def gmail_search(
    api_key: str,
    query: str,
    max_results: int = 10,
) -> dict:
    """Search Gmail messages."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "gmail",
                "action": "search",
                "params": {"query": query, "max_results": max_results},
            },
        )
        return response.json()


@mcp.tool()
async def gmail_read(api_key: str, message_id: str) -> dict:
    """Read a specific Gmail message."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "gmail",
                "action": "read",
                "params": {"message_id": message_id},
            },
        )
        return response.json()


@mcp.tool()
async def calendar_list_events(
    api_key: str,
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 10,
) -> dict:
    """List calendar events."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "calendar",
                "action": "list",
                "params": {"time_min": time_min, "time_max": time_max, "max_results": max_results},
            },
        )
        return response.json()


@mcp.tool()
async def calendar_create_event(
    api_key: str,
    summary: str,
    start: dict,
    end: dict,
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
) -> dict:
    """Create a calendar event."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "calendar",
                "action": "create",
                "params": {
                    "summary": summary, "start": start, "end": end,
                    "description": description, "location": location,
                    "attendees": attendees,
                },
            },
        )
        return response.json()


@mcp.tool()
async def drive_list_files(
    api_key: str,
    query: str | None = None,
    max_results: int = 10,
) -> dict:
    """List files in Google Drive."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "drive",
                "action": "list",
                "params": {"query": query, "max_results": max_results},
            },
        )
        return response.json()


@mcp.tool()
async def drive_read_file(api_key: str, file_id: str) -> dict:
    """Read file metadata from Google Drive."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8421/api/v1/agent/execute",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "provider": "google",
                "service": "drive",
                "action": "read",
                "params": {"file_id": file_id},
            },
        )
        return response.json()
