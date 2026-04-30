"""Function 5 & 13: Smart unanswered question monitor — one reminder, then escalate."""
from datetime import datetime, timedelta
from database.db import db
from database.models import IncomingMessage, TeamMember
from ai.message_generator import generate_rani_dm
import integrations.whatsapp as wa
import integrations.teams as teams
from config import config

_ONE_REMINDER_TEXT = "Der blev stillet et spørgsmål tidligere. Kan nogen hjælpe? Saki"


def process_incoming_message(platform: str, group_id: str, sender_identifier: str, content: str) -> None:
    from ai.message_generator import classify_as_question
    is_q = classify_as_question(content)

    msg = IncomingMessage(
        platform=platform,
        group_id=group_id,
        content=content,
        received_at=datetime.utcnow(),
        is_question=is_q,
    )
    if platform == "whatsapp":
        msg.sender_whatsapp = sender_identifier
    elif platform == "telegram":
        msg.sender_telegram_id = sender_identifier
    else:
        msg.sender_teams_id = sender_identifier

    db.session.add(msg)
    db.session.commit()


def check_unanswered_questions() -> None:
    """Run every 30 min. ONE group reminder, then escalate to Rani after 24h."""
    reminder_cutoff = datetime.utcnow() - timedelta(hours=config.UNANSWERED_QUESTION_HOURS)
    abandon_cutoff = datetime.utcnow() - timedelta(hours=config.QUESTION_ABANDONED_NOTIFY_HOURS)

    unanswered = IncomingMessage.query.filter(
        IncomingMessage.is_question == True,
        IncomingMessage.answered_at == None,
        IncomingMessage.escalated_to_rani_at == None,
        IncomingMessage.received_at <= reminder_cutoff,
    ).all()

    for msg in unanswered:
        if _is_active_conversation(msg):
            continue  # Natural discussion happening — stay silent

        if not msg.reminder_sent_at:
            _send_one_reminder(msg)
        elif msg.received_at <= abandon_cutoff:
            _escalate_to_rani(msg)


def mark_question_answered(msg_id: int) -> None:
    msg = db.session.get(IncomingMessage, msg_id)
    if msg:
        msg.answered_at = datetime.utcnow()
        db.session.commit()


def _is_active_conversation(msg: IncomingMessage) -> bool:
    """Return True if 2+ other messages appeared in the group after this question."""
    subsequent = IncomingMessage.query.filter(
        IncomingMessage.group_id == msg.group_id,
        IncomingMessage.platform == msg.platform,
        IncomingMessage.received_at > msg.received_at,
        IncomingMessage.id != msg.id,
    ).count()
    return subsequent >= 2


def _send_one_reminder(msg: IncomingMessage) -> None:
    _send_to_group(msg.platform, msg.group_id, _ONE_REMINDER_TEXT)
    msg.reminder_sent_at = datetime.utcnow()
    db.session.commit()


def _escalate_to_rani(msg: IncomingMessage) -> None:
    group_label = _group_label(msg.group_id)
    text = generate_rani_dm(
        f"Fortæl Rani at et spørgsmål i {group_label} er gået ubesvaret i over "
        f"{config.QUESTION_ABANDONED_NOTIFY_HOURS} timer: '{msg.content[:200]}'"
    )
    wa.send_to_rani(text)
    msg.escalated_to_rani_at = datetime.utcnow()
    db.session.commit()


def _send_to_group(platform: str, group_id: str, text: str) -> None:
    if platform == "whatsapp":
        wa.send_to_group(group_id, text)
    elif platform == "telegram":
        import integrations.telegram as tg
        tg.send_to_group(group_id, text)
    else:
        teams.send_channel_message(group_id, text)


def _group_label(group_id: str) -> str:
    labels = {
        config.WHATSAPP_GROUP_MARKETING: "Marketing-gruppen",
        config.WHATSAPP_GROUP_RD: "R&D-gruppen",
        config.WHATSAPP_GROUP_EXPERTISE_REVIEW: "Ekspertreviewgruppen",
        config.WHATSAPP_GROUP_TEACHERS: "Lærere-gruppen",
        config.WHATSAPP_GROUP_COMMUNITY: "Sakeena Community",
        config.TEAMS_CHANNEL_MARKETING: "Teams Marketing-kanalen",
        config.TEAMS_CHANNEL_RD: "Teams R&D-kanalen",
        config.TELEGRAM_GROUP_MARKETING: "Telegram Marketing-gruppen",
        config.TELEGRAM_GROUP_RD: "Telegram R&D-gruppen",
        config.TELEGRAM_GROUP_EXPERTISE_REVIEW: "Telegram Ekspertreviewgruppen",
        config.TELEGRAM_GROUP_TEACHERS: "Telegram Lærere-gruppen",
    }
    return labels.get(group_id, "gruppen")
