"""Function 14: 'Saki, lav en to do' — extract action items from recent group chat."""
import logging
from datetime import datetime, timedelta
import anthropic
from config import config
from database.models import IncomingMessage

logger = logging.getLogger(__name__)
_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_SYSTEM = (
    "Du er Saki, AI-assistent for Sakeena. Du læser en gruppe-samtale og laver en liste over:\n"
    "- Konkrete opgaver (med ansvarlig person hvis nævnt, ellers 'åben')\n"
    "- Beslutninger der er truffet\n"
    "- Åbne spørgsmål der mangler svar\n"
    "Maksimalt 8 punkter. Kun dansk. Ingen forklaring — kun listen.\n"
    "Format: '- [opgave] ([ansvarlig])'"
)

_TRIGGERS = ("lav en to do", "lav to do", "lav en todo", "make to-do", "make todo", "lav opgaveliste")


def is_todo_request(text: str) -> bool:
    t = text.lower()
    return any(trigger in t for trigger in _TRIGGERS)


def generate_todo(platform: str, group_id: str) -> str:
    cutoff = datetime.utcnow() - timedelta(hours=config.TODO_LOOKBACK_HOURS)
    messages = (
        IncomingMessage.query
        .filter(
            IncomingMessage.platform == platform,
            IncomingMessage.group_id == group_id,
            IncomingMessage.received_at >= cutoff,
        )
        .order_by(IncomingMessage.received_at.asc())
        .all()
    )

    if not messages:
        return "Ingen samtale fundet de seneste timer. Saki"

    conversation = "\n".join(
        f"[{m.received_at.strftime('%H:%M')}] {m.content}"
        for m in messages
    )

    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Samtale:\n{conversation}"}],
        )
        items = response.content[0].text.strip()
        return f"Baseret på jeres samtale:\n{items}\n\nSaki"
    except Exception as e:
        logger.error("generate_todo fejlede: %s", e)
        return "Kunne ikke generere to-do liste nu. Prøv igen. Saki"
