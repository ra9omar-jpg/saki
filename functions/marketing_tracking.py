"""Function 4: Marketing task tracking — opening vs closing meeting comparison."""
from datetime import datetime, date
from database.db import db
from database.models import WorkshopSession, MarketingTaskRecord, TeamMember
from ai.message_generator import generate_rani_dm, generate_group_message
import integrations.whatsapp as wa


def open_workshop_session(team: str = "marketing") -> WorkshopSession:
    session = WorkshopSession(
        date=date.today(),
        team=team,
        opening_recorded_at=datetime.utcnow(),
    )
    db.session.add(session)
    db.session.commit()
    return session


def record_opening_assignments(session_id: int, assignments: list[dict]) -> None:
    """assignments = [{"member_id": int, "task_description": str}]"""
    for a in assignments:
        record = MarketingTaskRecord(
            session_id=session_id,
            member_id=a["member_id"],
            task_description=a["task_description"],
            assigned_at_opening=datetime.utcnow(),
            claimed_week_independent=a.get("claimed_week_independent", False),
        )
        db.session.add(record)
    db.session.commit()


def record_closing_deliveries(session_id: int, delivered_member_ids: list[int]) -> None:
    session = db.session.get(WorkshopSession, session_id)
    if not session:
        return

    records = MarketingTaskRecord.query.filter_by(session_id=session_id).all()
    for record in records:
        if record.member_id in delivered_member_ids:
            record.was_delivered = True
            record.delivered_at_closing = datetime.utcnow()
        else:
            record.was_delivered = False
    session.closing_recorded_at = datetime.utcnow()
    db.session.commit()

    _report_discrepancies_to_rani(session_id)


def _report_discrepancies_to_rani(session_id: int) -> None:
    records = MarketingTaskRecord.query.filter_by(session_id=session_id).all()
    not_delivered = [r for r in records if r.was_delivered is False]

    if not not_delivered:
        msg = generate_rani_dm(
            "Fortæl Rani at alle i Marketing-teamet leverede deres opgaver ved lukkemødet i dag."
        )
    else:
        lines = []
        for r in not_delivered:
            member = db.session.get(TeamMember, r.member_id)
            if not member:
                continue
            lines.append(f"{member.name}: {r.task_description}")
        discrepancy_text = "\n".join(lines)
        msg = generate_rani_dm(
            f"Fortæl Rani at følgende opgaver IKKE blev leveret ved lukkemødet:\n{discrepancy_text}"
        )

    wa.send_to_rani(msg)


def generate_weekly_pattern_report() -> None:
    """Identify members who consistently don't deliver or only work in workshops."""
    from sqlalchemy import func

    all_records = MarketingTaskRecord.query.all()
    member_stats: dict[int, dict] = {}

    for r in all_records:
        mid = r.member_id
        if mid not in member_stats:
            member_stats[mid] = {
                "total": 0,
                "delivered": 0,
                "claimed_week": 0,
                "delivered_workshop_only": 0,
            }
        member_stats[mid]["total"] += 1
        if r.was_delivered:
            member_stats[mid]["delivered"] += 1
        if r.claimed_week_independent:
            member_stats[mid]["claimed_week"] += 1
            if not r.was_delivered:
                member_stats[mid]["delivered_workshop_only"] += 1

    patterns = []
    for mid, stats in member_stats.items():
        if stats["total"] < 3:
            continue
        member = db.session.get(TeamMember, mid)
        if not member:
            continue
        delivery_rate = stats["delivered"] / stats["total"]
        week_claim_no_deliver = stats["delivered_workshop_only"]

        if delivery_rate < 0.5:
            patterns.append(f"{member.name}: leverer kun {int(delivery_rate*100)}% af opgaver")
        if week_claim_no_deliver >= 2:
            patterns.append(
                f"{member.name}: siger 'jeg arbejder i løbet af ugen' men leverer sjældent"
            )

    if not patterns:
        return

    summary = "\n".join(f"- {p}" for p in patterns)
    text = generate_rani_dm(
        f"Send Rani en ugentlig mønsteroversigt for Marketing-teamet:\n{summary}"
    )
    wa.send_to_rani(text)
