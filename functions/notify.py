"""Unified Rani notification — Telegram-first, WhatsApp fallback."""
import logging
from config import config

logger = logging.getLogger(__name__)


def notify_rani(text: str) -> None:
    if config.RANI_TELEGRAM_ID:
        try:
            import integrations.telegram as tg
            tg.send_to_rani(text)
            return
        except Exception as e:
            logger.warning("Telegram notify_rani fejlede: %s — forsøger WhatsApp", e)
    try:
        import integrations.whatsapp as wa
        wa.send_to_rani(text)
    except Exception as e:
        logger.error("WhatsApp notify_rani fejlede: %s", e)
