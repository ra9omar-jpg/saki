"""Function 3: R&D Monday status updates."""
from datetime import datetime, date, timedelta
from database.db import db
from database.models import StatusUpdate, TeamMember, Task
from ai.message_generator import generate_group_message, generate_rani_dm
import integrations.whatsapp as wa
import integrations.teams as teams
import integrations.planner as planner
from functions.pre_send_confirmation import request_rani_confirmation
from config import config


def request_monday_status_send() -> None:
    request_rani_confirmation(
        message_type="monday_status_rd",
        description="den ugentlige mandagsstatus til R&D-teamet om opgavefremskridt",
    )


def send_monday_status_request(platform: str = "whatsapp") -> None:
    """Send status request to R&D team with their tasks listed."""
    planner.sync_tasks_to_db(config.PLANNER_PLAN_ID_RD, _get_app_context())

    rd_members = TeamMember.query.filter_by(team="rd", is_active=True).all()
    task_lines = []
    for member in rd_members:
        tasks = Task.query.filter_by(assigned_to_id=member.id).all()
        active = [t for t in tasks if t.status not in ("done",)]
        if active:
            task_names = ", ".join(t.title[:40] for t in active)
            task_lines.append(f"{member.name}: {task_names}")

    if not task_lines:
        task_summary = "Ingen aktive opgaver fundet i Planner."
    else:
        task_summary = "\n".join(task_lines)

    context = "Send en mandagsstatus-forespørgsel til R&D-teamet. Bed hvert medlem skrive én linje: Færdig / Halvvejs / Ikke startet / Blokeret af [hvad]."
    text = generate_group_message(context, {"Opgaver denne uge": task_summary})

    if platform == "whatsapp":
        wa.send_to_rd_group(text)
    else:
        teams.send_to_rd_channel(text)

    _record_status_request_sent()


def send_tuesday_reminder(platform: str = "whatsapp") -> None:
    rd_members = TeamMember.query.filter_by(team="rd", is_active=True).all()
    week_of = _this_monday()

    responded_ids = {
        s.member_id
        for s in StatusUpdate.query.filter_by(week_of=week_of).all()
    }
    non_responders = [m for m in rd_members if m.id not in responded_ids]
    if not non_responders:
        return

    names = ", ".join(m.name for m in non_responders)
    context = "Send en venlig tirsdagspåmindelse til R&D-teamet om at svare på mandagsstatus."
    text = generate_group_message(context, {"Mangler svar fra": names}, use_reminder=False)

    if platform == "whatsapp":
        wa.send_to_rd_group(text)
    else:
        teams.send_to_rd_channel(text)


def send_wednesday_flag_to_rani(platform: str = "whatsapp") -> None:
    rd_members = TeamMember.query.filter_by(team="rd", is_active=True).all()
    week_of = _this_monday()

    responded_ids = {
        s.member_id
        for s in StatusUpdate.query.filter_by(week_of=week_of).all()
    }
    non_responders = [m for m in rd_members if m.id not in responded_ids]
    if not non_responders:
        return

    names = ", ".join(m.name for m in non_responders)
    text = generate_rani_dm(
        f"Send Rani en besked om at følgende R&D-medlemmer ikke har svaret på ugens statusopdatering: {names}"
    )
    wa.send_to_rani(text)


def send_weekly_status_summary_to_rani(week_of: date = None) -> None:
    if not week_of:
        week_of = _this_monday()

    updates = StatusUpdate.query.filter_by(week_of=week_of).all()
    lines = []
    for u in updates:
        member = TeamMember.query.get(u.member_id)
        if not member:
            continue
        task = Task.query.get(u.task_id) if u.task_id else None
        task_name = task.title[:40] if task else "ukendt opgave"
        lines.append(f"- {member.name} ({task_name}): {u.status_text}")

    summary = "\n".join(lines) if lines else "Ingen statusopdateringer denne uge."
    text = generate_rani_dm(
        f"Send Rani en oversigt over R&D-teamets ugentlige statusopdateringer:\n{summary}"
    )
    wa.send_to_rani(text)


def record_status_update(member_id: int, task_id: int | None, status_text: str) -> None:
    week_of = _this_monday()
    existing = StatusUpdate.query.filter_by(member_id=member_id, week_of=week_of).first()
    if existing:
        existing.status_text = status_text
        existing.submitted_at = datetime.utcnow()
        existing.task_id = task_id
    else:
        u = StatusUpdate(
            member_id=member_id,
            task_id=task_id,
            status_text=status_text,
            week_of=week_of,
        )
        db.session.add(u)
    db.session.commit()


def _this_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def _record_status_request_sent() -> None:
    pass


def _get_app_context():
    from flask import current_app
    return current_app._get_current_object().app_context()
