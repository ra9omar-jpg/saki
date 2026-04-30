"""
WhatsApp Business Cloud API (Meta) — officiel integration.
Dokumentation: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
import requests
from config import config

_BASE_URL = "https://graph.facebook.com/v20.0"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def send_message(to: str, body: str) -> str:
    """
    Send en tekstbesked via Meta WhatsApp Cloud API.
    `to` er et telefonnummer uden whatsapp:-prefix, fx '4512345678'.
    Returnerer message ID fra Meta.
    """
    to_clean = to.replace("whatsapp:", "").replace("+", "").strip()

    url = f"{_BASE_URL}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_clean,
        "type": "text",
        "text": {"body": body},
    }
    r = requests.post(url, json=payload, headers=_headers(), timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("messages", [{}])[0].get("id", "")


def send_to_group(group_id: str, body: str) -> str:
    """
    Mode-aware group send. Routes through mode_router:
    test → only test groups, shadow → draft to Rani, live → direct.
    """
    from functions.mode_router import route_group_message
    return route_group_message(group_id, body)


def _send_to_group_raw(group_id: str, body: str) -> str:
    """Direct send bypassing mode checks — only called by mode_router."""
    return send_message(group_id, body)


def send_to_rani(body: str) -> str:
    if not config.WHATSAPP_ACCESS_TOKEN or config.WHATSAPP_ACCESS_TOKEN in ("pending", ""):
        import integrations.telegram as tg
        return tg.send_to_rani(body)
    return send_message(config.RANI_WHATSAPP, body)


def send_to_member(whatsapp_number: str, body: str) -> str:
    return send_message(whatsapp_number, body)


def send_to_marketing_group(body: str) -> str:
    return send_to_group(config.WHATSAPP_GROUP_MARKETING, body)


def send_to_rd_group(body: str) -> str:
    return send_to_group(config.WHATSAPP_GROUP_RD, body)


def send_to_expertise_group(body: str) -> str:
    return send_to_group(config.WHATSAPP_GROUP_EXPERTISE_REVIEW, body)


def send_to_teachers_group(body: str) -> str:
    return send_to_group(config.WHATSAPP_GROUP_TEACHERS, body)


def send_to_community_group(body: str) -> str:
    return send_to_group(config.WHATSAPP_GROUP_COMMUNITY, body)


def download_media(media_id: str) -> bytes:
    """Download a media file from WhatsApp by its media_id."""
    url = f"{_BASE_URL}/{media_id}"
    r = requests.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    download_url = r.json().get("url", "")
    r2 = requests.get(download_url, headers=_headers(), timeout=60)
    r2.raise_for_status()
    return r2.content


def mark_as_read(message_id: str) -> None:
    """Marker en modtaget besked som læst (viser blå flueben)."""
    url = f"{_BASE_URL}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    try:
        requests.post(url, json=payload, headers=_headers(), timeout=10)
    except Exception:
        pass
