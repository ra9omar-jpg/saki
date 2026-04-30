"""Function 1: Pre-send confirmation to Rani before any group message goes out."""
from datetime import datetime
from database.db import db
from database.models import RaniConfirmation, OutgoingMessage
from ai.message_generator import generate_rani_dm
import integrations.whatsapp as wa


def request_rani_confirmation(message_type: str, description: str) -> RaniConfirmation:
    text = generate_rani_dm(
        f"Spørg Rani hvornår det passer ham at sende følgende besked ud: {description}"
    )
    wa.send_to_rani(text)

    confirmation = RaniConfirmation(
        message_type=message_type,
        description=description,
        requested_at=datetime.utcnow(),
    )
    db.session.add(confirmation)
    db.session.commit()
    return confirmation


def handle_rani_time_reply(confirmation_id: int, rani_reply: str, pending_message_id: int) -> None:
    """Called when Rani replies with a preferred time for sending a message."""
    from ai.message_generator import generate_rani_dm
    import re

    confirmation = RaniConfirmation.query.get(confirmation_id)
    if not confirmation:
        return

    # Ask Claude to parse a time from the reply
    from anthropic import Anthropic
    from config import config

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    parse_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        system="Udtræk dato og tidspunkt fra teksten. Returner i ISO 8601-format (YYYY-MM-DDTHH:MM). Returner kun tidspunktet, intet andet. Hvis du ikke kan finde et tidspunkt, returner 'ukendt'.",
        messages=[{"role": "user", "content": rani_reply}],
    )
    parsed = parse_response.content[0].text.strip()

    scheduled_time = None
    if parsed != "ukendt":
        try:
            scheduled_time = datetime.fromisoformat(parsed)
        except ValueError:
            scheduled_time = None

    confirmation.confirmed_at = datetime.utcnow()
    confirmation.scheduled_time = scheduled_time
    confirmation.pending_message_id = pending_message_id
    db.session.commit()

    if scheduled_time:
        msg = OutgoingMessage.query.get(pending_message_id)
        if msg:
            msg.scheduled_at = scheduled_time
            msg.approved_by_rani_at = datetime.utcnow()
            msg.is_approved = True
            db.session.commit()

    ack = generate_rani_dm(
        f"Bekræft over for Rani at beskeden er planlagt til {scheduled_time.strftime('%A kl. %H:%M') if scheduled_time else 'det tidspunkt han angav'}."
    )
    wa.send_to_rani(ack)


def get_pending_confirmations() -> list[RaniConfirmation]:
    return RaniConfirmation.query.filter_by(confirmed_at=None).all()
