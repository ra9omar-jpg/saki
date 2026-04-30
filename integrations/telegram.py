"""
Telegram Bot API integration for Saki.
Direct HTTP calls to api.telegram.org — same pattern as integrations/whatsapp.py.
"""
import logging
import requests
from config import config

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.telegram.org/bot{token}"


def _api_url(method: str) -> str:
    return f"{_BASE_URL.format(token=config.TELEGRAM_BOT_TOKEN)}/{method}"


def send_message(chat_id: str, text: str) -> str:
    """
    Send a text message to any chat_id (user or group).
    Telegram group IDs are negative integers, e.g. '-1001234567890'.
    Returns the Telegram message_id as a string, or "" on failure.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — message not sent")
        return ""
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(_api_url("sendMessage"), json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return str(data.get("result", {}).get("message_id", ""))
    except requests.HTTPError as e:
        logger.error("Telegram sendMessage HTTP error: %s — %s", e, e.response.text if e.response else "")
        raise
    except Exception as e:
        logger.error("Telegram sendMessage error: %s", e)
        raise


def send_to_group(group_id: str, text: str) -> str:
    from functions.mode_router_telegram import route_group_message_telegram
    return route_group_message_telegram(group_id, text)


def _send_to_group_raw(group_id: str, text: str) -> str:
    """Direct send bypassing mode checks — only called by mode_router_telegram."""
    return send_message(group_id, text)


def send_to_rani(text: str) -> str:
    if not config.RANI_TELEGRAM_ID:
        logger.warning("RANI_TELEGRAM_ID not set — Rani DM not sent via Telegram")
        return ""
    return send_message(config.RANI_TELEGRAM_ID, text)


def send_to_member(telegram_chat_id: str, text: str) -> str:
    return send_message(telegram_chat_id, text)


def send_to_marketing_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_MARKETING, text)


def send_to_rd_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_RD, text)


def send_to_expertise_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_EXPERTISE_REVIEW, text)


def send_to_teachers_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_TEACHERS, text)


def send_to_community_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_COMMUNITY, text)
