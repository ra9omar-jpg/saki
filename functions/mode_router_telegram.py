"""
Telegram mode routing: test / shadow / live.
Mirrors functions/mode_router.py for Telegram group IDs.
"""
import logging
from config import config

logger = logging.getLogger(__name__)


def route_group_message_telegram(group_id: str, body: str) -> str:
    from functions.mode_router import get_current_mode
    mode = get_current_mode()

    if mode == "test":
        if _is_test_group(group_id):
            logger.info("mode=test: sending to Telegram test group %s", group_id)
            return _send_direct(group_id, body)
        logger.info("mode=test: BLOCKED Telegram send to real group %s", group_id)
        return ""

    elif mode == "shadow":
        logger.info("mode=shadow: drafting to Rani instead of Telegram group %s", group_id)
        _send_shadow_draft(group_id, body)
        return ""

    else:  # live
        logger.info("mode=live: sending to Telegram real group %s", group_id)
        return _send_direct(group_id, body)


def _is_test_group(group_id: str) -> bool:
    test_groups = [
        config.TEST_TELEGRAM_GROUP_RD,
        config.TEST_TELEGRAM_GROUP_MARKETING,
        config.TEST_TELEGRAM_GROUP_TEACHERS,
        config.TEST_TELEGRAM_GROUP_EXPERTISE,
    ]
    return group_id in [g for g in test_groups if g]


def _send_shadow_draft(group_id: str, body: str) -> None:
    from functions.group_config import telegram_id_to_code, code_to_label
    import integrations.whatsapp as wa
    code = telegram_id_to_code(group_id)
    group_label = code_to_label(code) if code else group_id
    wa.send_to_rani(
        f"[SHADOW/TELEGRAM – {group_label}]\n"
        f"Saki har lavet denne besked. Send den manuelt:\n\n{body}"
    )


def _send_direct(group_id: str, body: str) -> str:
    from integrations.telegram import _send_to_group_raw
    return _send_to_group_raw(group_id, body)
