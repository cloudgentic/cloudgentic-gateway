"""Google service proxy — executes Gmail, Calendar, Drive actions on behalf of users."""
import base64
from datetime import datetime, timezone
from email.mime.text import MIMEText

import httpx

from app.models.connected_account import ConnectedAccount
from app.providers.google.oauth import GoogleOAuth
from app.services.vault import get_access_token, get_refresh_token, store_tokens

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"
DRIVE_API = "https://www.googleapis.com/drive/v3"


class GoogleService:
    def __init__(self, account: ConnectedAccount, user_id: str):
        self.account = account
        self.user_id = user_id

    async def _get_token(self) -> str:
        """Get a valid access token, refreshing if expired."""
        if self.account.token_expires_at and self.account.token_expires_at < datetime.now(timezone.utc):
            refresh_token = get_refresh_token(self.account, self.user_id)
            if refresh_token:
                oauth = GoogleOAuth()
                new_tokens = await oauth.refresh_access_token(refresh_token)
                await store_tokens(self.account, new_tokens, self.user_id)
        return get_access_token(self.account, self.user_id)

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url,
                headers={"Authorization": f"Bearer {token}"},
                **kwargs,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def execute(self, service: str, action: str, params: dict) -> dict:
        """Route to the appropriate service handler."""
        handler = getattr(self, f"_{service}_{action}", None)
        if not handler:
            raise ValueError(f"Unknown action: {service}.{action}")
        return await handler(params)

    # --- Gmail ---

    async def _gmail_list(self, params: dict) -> dict:
        query = params.get("query", "")
        max_results = params.get("max_results", 10)
        return await self._request(
            "GET", f"{GMAIL_API}/users/me/messages",
            params={"q": query, "maxResults": max_results},
        )

    async def _gmail_read(self, params: dict) -> dict:
        message_id = params["message_id"]
        return await self._request("GET", f"{GMAIL_API}/users/me/messages/{message_id}")

    async def _gmail_send(self, params: dict) -> dict:
        msg = MIMEText(params["body"])
        msg["to"] = params["to"]
        msg["subject"] = params["subject"]
        if params.get("cc"):
            msg["cc"] = params["cc"]
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return await self._request(
            "POST", f"{GMAIL_API}/users/me/messages/send",
            json={"raw": raw},
        )

    async def _gmail_search(self, params: dict) -> dict:
        return await self._gmail_list(params)

    # --- Calendar ---

    async def _calendar_list(self, params: dict) -> dict:
        calendar_id = params.get("calendar_id", "primary")
        time_min = params.get("time_min")
        time_max = params.get("time_max")
        request_params = {"maxResults": params.get("max_results", 10), "singleEvents": True, "orderBy": "startTime"}
        if time_min:
            request_params["timeMin"] = time_min
        if time_max:
            request_params["timeMax"] = time_max
        return await self._request(
            "GET", f"{CALENDAR_API}/calendars/{calendar_id}/events",
            params=request_params,
        )

    async def _calendar_create(self, params: dict) -> dict:
        calendar_id = params.get("calendar_id", "primary")
        event = {
            "summary": params["summary"],
            "start": params["start"],
            "end": params["end"],
        }
        if params.get("description"):
            event["description"] = params["description"]
        if params.get("location"):
            event["location"] = params["location"]
        if params.get("attendees"):
            event["attendees"] = [{"email": e} for e in params["attendees"]]
        return await self._request(
            "POST", f"{CALENDAR_API}/calendars/{calendar_id}/events",
            json=event,
        )

    async def _calendar_delete(self, params: dict) -> dict:
        calendar_id = params.get("calendar_id", "primary")
        event_id = params["event_id"]
        return await self._request("DELETE", f"{CALENDAR_API}/calendars/{calendar_id}/events/{event_id}")

    # --- Drive ---

    async def _drive_list(self, params: dict) -> dict:
        request_params = {"pageSize": params.get("max_results", 10)}
        if params.get("query"):
            request_params["q"] = params["query"]
        return await self._request("GET", f"{DRIVE_API}/files", params=request_params)

    async def _drive_read(self, params: dict) -> dict:
        file_id = params["file_id"]
        return await self._request("GET", f"{DRIVE_API}/files/{file_id}", params={"fields": "*"})

    async def _drive_download(self, params: dict) -> dict:
        file_id = params["file_id"]
        token = await self._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DRIVE_API}/files/{file_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"alt": "media"},
            )
            response.raise_for_status()
            return {"content": base64.b64encode(response.content).decode(), "encoding": "base64"}
