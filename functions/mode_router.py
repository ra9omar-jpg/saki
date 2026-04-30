"""
Saki mode routing: test / shadow / live.

test   — only sends to TEST_GROUPS, real groups are silently blocked
shadow — generates messages but sends drafts to Rani instead of real groups
live   — sends directly to real groups

All calls to send_to_group() in integrations/whatsapp.py pass through here.
"""
import logging
from config import config

logger = logging.getLogger(__name__)

VALID_MODES = ("test", "shadow", "live")


def get_current_mode() -> str:
    try:
        from database.models import get_saki_state
        return get_saki_state().mode or "test"
    except Exception:
        return "test"  # Fail safe — never accidentally go live


def set_mode(new_mode: str) -> None:
    if new_mode not in VALID_MODES:
        raise ValueError(f"Ugyldig mode: {new_mode}")
    from database.models import get_saki_state
    from database.db import db
    state = get_saki_state()
    old_mode = state.mode
    state.mode = new_mode
    db.session.commit()
    logger.info("MODE CHANGE: %s → %s", old_mode, new_mode)


def route_group_message(group_id: str, body: str) -> str:
    """
    Route a group message based on current mode.
    Returns the sent message ID (or empty string if not sent directly).
    """
    mode = get_current_mode()

    if mode == "test":
        if _is_test_group(group_id):
            logger.info("mode=test: sending to test group %s", group_id)
            return _send_direct(group_id, body)
        else:
            logger.info("mode=test: BLOCKED send to real group %s", group_id)
            return ""

    elif mode == "shadow":
        logger.info("mode=shadow: drafting to Rani instead of group %s", group_id)
        _send_shadow_draft(group_id, body)
        return ""

    else:  # live
        logger.info("mode=live: sending to real group %s", group_id)
        return _send_direct(group_id, body)


def _is_test_group(group_id: str) -> bool:
    test_groups = [
        config.TEST_WHATSAPP_GROUP_RD,
        config.TEST_WHATSAPP_GROUP_MARKETING,
        config.TEST_WHATSAPP_GROUP_TEACHERS,
        config.TEST_WHATSAPP_GROUP_EXPERTISE,
    ]
    return group_id in [g for g in test_groups if g]


def _send_shadow_draft(group_id: str, body: str) -> None:
    from functions.group_config import whatsapp_id_to_code, code_to_label
    import integrations.whatsapp as wa
    code = whatsapp_id_to_code(group_id)
    group_label = code_to_label(code) if code else group_id
    wa.send_to_rani(
        f"[SHADOW – {group_label}]\n"
        f"Saki har lavet denne besked. Send den manuelt fra din gamle telefon:\n\n"
        f"{body}"
    )


def _send_direct(group_id: str, body: str) -> str:
    from integrations.whatsapp import _send_to_group_raw
    return _send_to_group_raw(group_id, body)
