"""Function 2: Weekly workshop availability polls."""
from datetime import datetime, date, timedelta
from database.db import db
from database.models import Poll, PollResponse, TeamMember, OutgoingMessage
from ai.message_generator import generate_group_message
from ai.islamic_reminders import get_reminder_sometimes
import integrations.whatsapp as wa
import integrations.teams as teams
from functions.pre_send_confirmation import request_rani_confirmation
from config import config


def request_weekly_poll_send() -> None:
    """Step 1: Ask Rani when to send the weekly poll."""
    request_rani_confirmation(
        message_type="weekly_poll",
        description="den ugentlige tilgængelighedspoll for den kommende workshop",
    )


def send_weekly_poll(platform: str = "whatsapp") -> Poll:
    """Step 2: Send the poll after Rani confirms timing."""
    week_start = _this_monday()
    reminder = get_reminder_sometimes(0.4)

    context = "Send en poll til alle frivillige og spørg hvornår de er tilgængelige for den kommende workshop denne uge. Variation i sproget er vigtigt."
    data = {"Uge": str(week_start)}
    text = generate_group_message(context, data, use_reminder=reminder is not None)

    poll = Poll(
        week_start=week_start,
        question_text=text,
        platform=platform,
        sent_at=datetime.utcnow(),
        closes_at=datetime.utcnow() + timedelta(hours=48),
    )

    if platform == "whatsapp":
        poll.group_id = f"{config.WHATSAPP_GROUP_MARKETING}|{config.WHATSAPP_GROUP_RD}"
        wa.send_to_marketing_group(text)
        wa.send_to_rd_group(text)
    else:
        poll.group_id = f"{config.TEAMS_CHANNEL_MARKETING}|{config.TEAMS_CHANNEL_RD}"
        teams.send_to_marketing_channel(text)
        teams.send_to_rd_channel(text)

    db.session.add(poll)
    db.session.commit()
    return poll


def send_poll_reminder(poll_id: int, reminder_type: str) -> None:
    """Send 24h or 12h reminder to non-responders."""
    poll = Poll.query.get(poll_id)
    if not poll or poll.is_closed:
        return

    responded_ids = {r.member_id for r in poll.responses}
    non_responders = TeamMember.query.filter(
        TeamMember.is_active == True,
        ~TeamMember.id.in_(responded_ids),
    ).all()

    if not non_responders:
        return

    names = ", ".join(m.name for m in non_responders)
    hours = "24" if reminder_type == "24h" else "12"
    context = f"Send en venlig påmindelse til dem der ikke har svaret på ugens tilgængelighedspoll. Der er {hours} timer tilbage."
    text = generate_group_message(context, {"Ikke svaret endnu": names})

    if poll.platform == "whatsapp":
        wa.send_to_marketing_group(text)
        wa.send_to_rd_group(text)
    else:
        teams.send_to_marketing_channel(text)
        teams.send_to_rd_channel(text)

    if reminder_type == "24h":
        poll.reminder_sent_24h = True
    else:
        poll.reminder_sent_12h = True
    db.session.commit()


def close_poll_and_report(poll_id: int) -> None:
    poll = Poll.query.get(poll_id)
    if not poll:
        return

    responses = PollResponse.query.filter_by(poll_id=poll_id).all()
    summary_lines = []
    for r in responses:
        member = TeamMember.query.get(r.member_id)
        if member:
            summary_lines.append(f"- {member.name}: {r.response_text}")

    summary = "\n".join(summary_lines) if summary_lines else "Ingen svar modtaget."
    text = generate_group_message(
        "Send Rani en oversigt over svarene på ugens tilgængelighedspoll.",
        {"Svar": summary},
        use_reminder=False,
    )
    wa.send_to_rani(text)

    poll.is_closed = True
    db.session.commit()


def record_poll_response(poll_id: int, member_id: int, response_text: str) -> None:
    existing = PollResponse.query.filter_by(poll_id=poll_id, member_id=member_id).first()
    if existing:
        existing.response_text = response_text
        existing.responded_at = datetime.utcnow()
    else:
        r = PollResponse(
            poll_id=poll_id,
            member_id=member_id,
            response_text=response_text,
        )
        db.session.add(r)
    db.session.commit()


def get_active_poll() -> Poll | None:
    return Poll.query.filter_by(is_closed=False).order_by(Poll.sent_at.desc()).first()


def _this_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())
