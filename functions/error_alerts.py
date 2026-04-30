"""Function 16: Alerts to Rani when Saki encounters errors."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def alert_rani(function_name: str, error: Exception, retry_info: str = "") -> None:
    try:
        from functions.notify import notify_rani
        timestamp = datetime.utcnow().strftime("%d/%m %H:%M")
        retry_str = f" {retry_info}" if retry_info else ""
        msg = (
            f"FEJL: {function_name} fejlede kl. {timestamp}. "
            f"{type(error).__name__}.{retry_str} Saki"
        )
        notify_rani(msg)
    except Exception as nested:
        logger.error("alert_rani fejlede selv: %s", nested)


def alert_critical(function_name: str, error: Exception) -> None:
    """Critical failure — pause Saki and require Rani to send 'wake_up' to resume."""
    try:
        from functions.notify import notify_rani
        from database.models import get_saki_state
        from database.db import db

        timestamp = datetime.utcnow().strftime("%d/%m %H:%M")
        msg = (
            f"KRITISK FEJL: {function_name} kl. {timestamp}. "
            f"{type(error).__name__}. Saki er sat på pause. Send 'wake_up' for at bekræfte. Saki"
        )
        notify_rani(msg)

        state = get_saki_state()
        state.is_paused = True
        db.session.commit()
    except Exception as nested:
        logger.error("alert_critical fejlede selv: %s", nested)
