import pytest
from unittest.mock import patch


class TestShutdownEndpoint:
    async def test_shutdown_returns_200_for_admin(self, client, admin_token):
        with patch("app.api.v1.endpoints.system.get_settings") as mock_settings:
            mock_settings.return_value.deployment_mode = "self-hosted"
            with patch("os.path.exists", return_value=False):
                with patch("os.kill"):
                    response = await client.post(
                        "/api/v1/system/shutdown",
                        headers={"Authorization": f"Bearer {admin_token}"},
                    )
                    assert response.status_code == 200
                    assert response.json()["status"] == "shutting_down"

    async def test_shutdown_blocked_in_cloud_mode(self, client, admin_token):
        with patch("app.api.v1.endpoints.system.get_settings") as mock_settings:
            mock_settings.return_value.deployment_mode = "cloud"
            response = await client.post(
                "/api/v1/system/shutdown",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 403

    async def test_shutdown_requires_auth(self, client):
        response = await client.post("/api/v1/system/shutdown")
        assert response.status_code in (401, 403)

    async def test_shutdown_requires_admin_role(self, client, user_token):
        response = await client.post(
            "/api/v1/system/shutdown",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
