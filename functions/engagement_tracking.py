"""Function 6: Engagement tracking and weekly insights for Rani."""
from datetime import date, timedelta
from database.db import db
from database.models import EngagementRecord, TeamMember, PollResponse, StatusUpdate, Poll
from ai.message_generator import generate_rani_dm
import integrations.whatsapp as wa


def update_engagement_poll_response(member_id: int, week_of: date = None) -> None:
    record = _get_or_create(member_id, week_of or _this_monday())
    record.poll_responded = True
    db.session.commit()


def update_engagement_status_response(member_id: int, week_of: date = None) -> None:
    record = _get_or_create(member_id, week_of or _this_monday())
    record.status_update_responded = True
    db.session.commit()


def update_engagement_workshop_attended(member_id: int, week_of: date = None) -> None:
    record = _get_or_create(member_id, week_of or _this_monday())
    record.workshop_attended = True
    db.session.commit()


def increment_message_count(member_id: int, week_of: date = None) -> None:
    record = _get_or_create(member_id, week_of or _this_monday())
    record.messages_sent_count = (record.messages_sent_count or 0) + 1
    db.session.commit()


def send_weekly_engagement_report() -> None:
    week_of = _this_monday()
    members = TeamMember.query.filter_by(is_active=True).all()

    reliable = []
    silent = []
    disengaged = []

    for member in members:
        records = (
            EngagementRecord.query.filter_by(member_id=member.id)
            .order_by(EngagementRecord.week_of.desc())
            .limit(4)
            .all()
        )
        if not records:
            continue

        avg_score = _compute_score(records)
        latest = records[0] if records else None

        if avg_score >= 0.75:
            reliable.append(f"{member.name} ({member.team})")
        elif avg_score <= 0.25:
            disengaged.append(f"{member.name} ({member.team}) — score {int(avg_score*100)}%")
        elif latest and latest.messages_sent_count == 0 and not latest.poll_responded:
            silent.append(f"{member.name} ({member.team})")

    report_parts = []
    if reliable:
        report_parts.append(f"Paalidelige denne uge: {', '.join(reliable)}")
    if silent:
        report_parts.append(f"Stille/inaktive: {', '.join(silent)}")
    if disengaged:
        report_parts.append(f"Tegn på frafald (lav engagement de seneste 4 uger): {', '.join(disengaged)}")

    if not report_parts:
        report_parts.append("Ingen bemærkelsesværdige mønstre denne uge.")

    summary = "\n".join(report_parts)
    text = generate_rani_dm(
        f"Send Rani den ugentlige engagementsoversigt for alle teams:\n{summary}"
    )
    wa.send_to_rani(text)


def _compute_score(records: list[EngagementRecord]) -> float:
    if not records:
        return 0.0
    scores = []
    for r in records:
        s = 0
        if r.poll_responded:
            s += 1
        if r.status_update_responded:
            s += 1
        if r.workshop_attended:
            s += 1
        if r.messages_sent_count and r.messages_sent_count > 0:
            s += 1
        scores.append(s / 4)
    return sum(scores) / len(scores)


def _get_or_create(member_id: int, week_of: date) -> EngagementRecord:
    record = EngagementRecord.query.filter_by(member_id=member_id, week_of=week_of).first()
    if not record:
        record = EngagementRecord(member_id=member_id, week_of=week_of)
        db.session.add(record)
        db.session.flush()
    return record


def _this_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())
