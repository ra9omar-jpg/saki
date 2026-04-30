"""Function 18: Handle 1-on-1 private messages to Saki from team members."""
import logging
from database.models import TeamMember, Task
import integrations.whatsapp as wa
from ai.message_generator import generate_message
from config import config

logger = logging.getLogger(__name__)

_PRIVATE_RULES = (
    "Dette er en privat besked fra et teammedlem. "
    "Besvar kun faktuelle spørgsmål om deadlines, opgaver og workshop-tider. "
    "Afslør ALDRIG admin-funktioner, kontrol-kommandoer eller indstillinger. "
    "Træf ingen beslutninger."
)


_DECISION_KEYWORDS = (
    "godkend", "approve", "ændr deadline",
    "beslut", "kan jeg", "må jeg", "tilladelse",
)

_ADMIN_KEYWORDS = (
    "indstillinger", "settings", "kontrol", "kommando",
    "pause", "shutdown", "hemmelig", "admin",
)


def handle_direct_message(from_number: str, text: str) -> None:
    member = TeamMember.query.filter_by(whatsapp_number=from_number).first()

    context = ""
    if member:
        tasks = Task.query.filter_by(assigned_to_id=member.id, status="in_progress").limit(3).all()
        context = f"\nMedlem: {member.name} ({member.team}-team)"
        if tasks:
            context += f"\nAktive opgaver: {', '.join(t.title for t in tasks)}"

    if _is_admin_question(text):
        reply = "Det er ikke noget jeg kan hjælpe med her. Saki"
    elif _needs_rani(text):
        sender = member.name if member else from_number
        wa.send_to_rani(f"{sender} skriver: \"{text[:200]}\". Saki")
        reply = f"Det skal {config.RANI_NAME} tage stilling til. Jeg giver besked videre. Saki"
    else:
        prompt = f"{_PRIVATE_RULES}\n\nMedlem skriver privat:{context}\n\nBesked: {text}"
        reply = generate_message(prompt, include_reminder=False)

    wa.send_message(from_number, reply)


def _needs_rani(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _DECISION_KEYWORDS)


def _is_admin_question(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _ADMIN_KEYWORDS)
