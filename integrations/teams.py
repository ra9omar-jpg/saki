import threading
import time
import requests
import msal
from config import config

_REQUEST_TIMEOUT = 15  # sekunder

_token_lock = threading.Lock()
_token_cache = {"token": None, "expires_at": 0}


def _get_access_token() -> str:
    with _token_lock:
        if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
            return _token_cache["token"]

        app = msal.ConfidentialClientApplication(
            config.AZURE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{config.AZURE_TENANT_ID}",
            client_credential=config.AZURE_CLIENT_SECRET,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(f"Kunne ikke hente Teams-token: {result.get('error_description')}")

        _token_cache["token"] = result["access_token"]
        _token_cache["expires_at"] = time.time() + result.get("expires_in", 3600)
        return _token_cache["token"]


def _graph_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }


def send_channel_message(channel_id: str, body: str) -> dict:
    url = f"https://graph.microsoft.com/v1.0/teams/{config.TEAMS_GROUP_ID}/channels/{channel_id}/messages"
    payload = {"body": {"content": body, "contentType": "text"}}
    r = requests.post(url, json=payload, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def send_dm_to_user(teams_user_id: str, body: str) -> dict:
    headers = _graph_headers()
    chat_url = "https://graph.microsoft.com/v1.0/chats"
    chat_payload = {
        "chatType": "oneOnOne",
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{config.AZURE_CLIENT_ID}",
            },
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{teams_user_id}",
            },
        ],
    }
    r = requests.post(chat_url, json=chat_payload, headers=headers, timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    chat_id = r.json()["id"]

    msg_url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages"
    msg_payload = {"body": {"content": body, "contentType": "text"}}
    r2 = requests.post(msg_url, json=msg_payload, headers=headers, timeout=_REQUEST_TIMEOUT)
    r2.raise_for_status()
    return r2.json()


def send_to_rani(body: str) -> dict:
    return send_dm_to_user(config.RANI_TEAMS_USER_ID, body)


def send_to_marketing_channel(body: str) -> dict:
    return send_channel_message(config.TEAMS_CHANNEL_MARKETING, body)


def send_to_rd_channel(body: str) -> dict:
    return send_channel_message(config.TEAMS_CHANNEL_RD, body)


def send_to_expertise_channel(body: str) -> dict:
    return send_channel_message(config.TEAMS_CHANNEL_EXPERTISE_REVIEW, body)


def get_channel_messages(channel_id: str, top: int = 50) -> list[dict]:
    url = (
        f"https://graph.microsoft.com/v1.0/teams/{config.TEAMS_GROUP_ID}"
        f"/channels/{channel_id}/messages?$top={top}"
    )
    r = requests.get(url, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json().get("value", [])
