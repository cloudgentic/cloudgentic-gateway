"""System management endpoints (self-hosted only)."""

import asyncio
import logging
import os
import signal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import get_settings
from app.core.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

GATEWAY_CONTAINERS = [
    "gateway-web",
    "gateway-worker",
    "gateway-db",
    "gateway-redis",
    "gateway-api",  # Stop ourselves last
]


@router.post("/system/shutdown")
async def shutdown_gateway(request: Request, user=Depends(get_current_user)):
    """Shut down the entire Gateway stack.

    Self-hosted only. Requires admin authentication.
    """
    settings = get_settings()

    if settings.deployment_mode == "cloud":
        raise HTTPException(
            status_code=403,
            detail="Shutdown is not available in cloud mode",
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "Shutdown initiated by user=%s from ip=%s",
        user.id,
        client_ip,
    )

    docker_socket = "/var/run/docker.sock"

    if os.path.exists(docker_socket):
        async def _shutdown_via_socket():
            await asyncio.sleep(1)  # Let HTTP response send first
            transport = httpx.AsyncHTTPTransport(uds=docker_socket)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://docker"
            ) as client:
                for name in GATEWAY_CONTAINERS:
                    try:
                        resp = await client.post(
                            f"/containers/{name}/stop",
                            params={"t": 10},
                        )
                        if resp.status_code in (204, 304):
                            logger.info("Stopped container %s", name)
                        else:
                            logger.warning(
                                "Failed to stop %s: %s", name, resp.status_code
                            )
                    except Exception as exc:
                        logger.warning("Error stopping %s: %s", name, exc)

        asyncio.get_event_loop().create_task(_shutdown_via_socket())
        return {
            "status": "shutting_down",
            "message": "Gateway is shutting down. All services will stop momentarily.",
        }

    # Fallback: no Docker socket — send SIGTERM to self
    async def _shutdown_sigterm():
        await asyncio.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.get_event_loop().create_task(_shutdown_sigterm())
    return {
        "status": "shutting_down",
        "message": "Gateway API is shutting down.",
    }
