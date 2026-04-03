from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, api_keys, accounts, rules, audit, agent, health,
    providers, security, anomalies, webhooks, notifications, agents,
    audit_export,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(audit_export.router, prefix="/audit", tags=["audit"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(security.router, prefix="/security", tags=["security"])
api_router.include_router(anomalies.router, prefix="/security/anomalies", tags=["anomalies"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
