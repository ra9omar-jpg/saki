"""Functions 10, 11, 15: Secret-code control menu, quick pause, manual broadcast."""
import json
import logging
from datetime import datetime, timedelta
from database.db import db
from database.models import get_saki_state, ArticleReview
from functions.group_config import label_to_code, code_to_whatsapp_id, code_to_label
from functions.notify import notify_rani
import integrations.whatsapp as wa
from config import config

logger = logging.getLogger(__name__)

_MENU = (
    "Hej {name}. Her er hvad jeg kan gøre for dig:\n"
    "\n— TILSTAND —\n"
    "- set_mode test / shadow / live – skift tilstand\n"
    "- current_mode – vis nuværende tilstand\n"
    "\n— GRUPPER —\n"
    "- pause [gruppenavn] – stop beskeder til en gruppe\n"
    "- resume [gruppenavn] – start beskeder igen\n"
    "- broadcast [gruppenavn] [besked] – send en besked til en gruppe nu\n"
    "\n— SYSTEM —\n"
    "- stop_islamic_reminders / start_islamic_reminders – tænd/sluk påmindelser\n"
    "- change_time [gruppenavn] [HH:MM] – ændr planlagt tidspunkt\n"
    "- status – hvem mangler at svare og hvad er stuck\n"
    "- shutdown – nødstop\n"
    "- wake_up – genaktiver efter shutdown\n"
    "- settings – vis nuværende indstillinger\n"
    "- check_now – synkroniser Planner nu\n"
    "\n— TEST (kun i test-tilstand) —\n"
    "- test_status_update – trigger mandagsopdatering nu\n"
    "- test_poll – trigger ugentlig poll nu\n"
    "- test_review_request – trigger artikel-reviewanmodning nu\n"
    "- force_draft – send næste kladde til Rani nu (shadow-tilstand)\n"
    "\n- help – vis denne menu igen\n"
    "Saki"
)


def handle_secret_code() -> None:
    """Show control menu and activate command mode for 10 minutes."""
    state = get_saki_state()
    state.rani_command_mode_until = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    notify_rani(_MENU.format(name=config.RANI_NAME))


def handle_quick_pause() -> None:
    """Function 11: 'Saki!!!' — silence all outgoing messages for 5 hours."""
    state = get_saki_state()
    state.is_paused = True
    state.paused_until = datetime.utcnow() + timedelta(hours=5)
    db.session.commit()
    resume_time = (datetime.utcnow() + timedelta(hours=5)).strftime("%H:%M")
    notify_rani(
        f"Forstået, {config.RANI_NAME}. Jeg er stille i 5 timer. Jeg vågner kl. {resume_time}. Saki"
    )


def is_rani_in_command_mode() -> bool:
    try:
        state = get_saki_state()
        return bool(
            state.rani_command_mode_until
            and datetime.utcnow() < state.rani_command_mode_until
        )
    except Exception:
        return False


def handle_control_command(command: str) -> None:
    """Parse and execute a control command sent by Rani."""
    parts = command.strip().split(maxsplit=2)
    cmd = parts[0].lower() if parts else ""

    if cmd in ("help", "hjælp"):
        handle_secret_code()
    elif cmd == "set_mode" and len(parts) >= 2:
        _set_mode(parts[1])
    elif cmd == "current_mode":
        _show_current_mode()
    elif cmd == "pause" and len(parts) >= 2:
        _pause_group(parts[1])
    elif cmd == "resume" and len(parts) >= 2:
        _resume_group(parts[1])
    elif cmd == "stop_islamic_reminders":
        _toggle_reminders(False)
    elif cmd == "start_islamic_reminders":
        _toggle_reminders(True)
    elif cmd == "broadcast" and len(parts) >= 3:
        _broadcast(parts[1], parts[2])
    elif cmd == "status":
        _send_status()
    elif cmd == "shutdown":
        _shutdown()
    elif cmd == "wake_up":
        _wake_up()
    elif cmd == "settings":
        _send_settings()
    elif cmd == "check_now":
        _check_now()
    elif cmd == "change_time" and len(parts) >= 3:
        notify_rani(
            f"change_time noteret: {parts[1]} kl. {parts[2]}. "
            f"Kontakt Sara for at ændre det permanent. Saki"
        )
    elif cmd == "test_status_update":
        _test_trigger("status_update")
    elif cmd == "test_poll":
        _test_trigger("poll")
    elif cmd == "test_review_request":
        _test_trigger("review_request")
    elif cmd == "force_draft":
        _force_draft()
    else:
        notify_rani("Kommando ikke genkendt. Skriv 'help' for alle kommandoer. Saki")


def check_and_resume_pause() -> None:
    """Called by scheduler — auto-resume after 5-hour quick pause expires."""
    try:
        state = get_saki_state()
        if state.is_paused and state.paused_until and datetime.utcnow() >= state.paused_until:
            state.is_paused = False
            state.paused_until = None
            db.session.commit()
            notify_rani("Jeg er aktiv igen. Saki")
    except Exception as e:
        logger.error("check_and_resume_pause fejlede: %s", e)


def is_saki_active() -> bool:
    """Returns False if Saki is globally paused or shutdown."""
    try:
        state = get_saki_state()
        if state.is_shutdown:
            return False
        if state.is_paused and state.paused_until:
            if datetime.utcnow() < state.paused_until:
                return False
            state.is_paused = False
            state.paused_until = None
            db.session.commit()
        return True
    except Exception:
        return True


def is_group_paused(group_code: str) -> bool:
    try:
        state = get_saki_state()
        return group_code in json.loads(state.paused_groups_json or "[]")
    except Exception:
        return False


def _pause_group(group_label: str) -> None:
    code = label_to_code(group_label)
    if not code:
        notify_rani(f"Gruppe '{group_label}' ikke fundet. Prøv: rd, marketing, lærere, ekspert. Saki")
        return
    state = get_saki_state()
    paused = json.loads(state.paused_groups_json or "[]")
    if code not in paused:
        paused.append(code)
    state.paused_groups_json = json.dumps(paused)
    db.session.commit()
    notify_rani(f"Beskeder til {code_to_label(code)} er sat på pause. Skriv 'resume {group_label}' for at genoptage. Saki")


def _resume_group(group_label: str) -> None:
    code = label_to_code(group_label)
    if not code:
        notify_rani(f"Gruppe '{group_label}' ikke fundet. Saki")
        return
    state = get_saki_state()
    paused = json.loads(state.paused_groups_json or "[]")
    if code in paused:
        paused.remove(code)
    state.paused_groups_json = json.dumps(paused)
    db.session.commit()
    notify_rani(f"Beskeder til {code_to_label(code)} er genoptaget. Saki")


def _toggle_reminders(enabled: bool) -> None:
    state = get_saki_state()
    state.islamic_reminders_enabled = enabled
    db.session.commit()
    status = "aktiveret" if enabled else "deaktiveret"
    notify_rani(f"Islamiske påmindelser er nu {status}. Saki")


def _broadcast(group_label: str, message: str) -> None:
    code = label_to_code(group_label)
    group_id = code_to_whatsapp_id(code) if code else None
    if not group_id:
        notify_rani(f"Gruppe '{group_label}' ikke fundet. Saki")
        return
    wa.send_to_group(group_id, f"{message}\n\nSaki")
    notify_rani(f"Sendt til {code_to_label(code)}. Saki")


def _shutdown() -> None:
    state = get_saki_state()
    state.is_shutdown = True
    db.session.commit()
    notify_rani("Saki er lukket ned. Send 'wake_up' for at genaktivere. Saki")


def _wake_up() -> None:
    state = get_saki_state()
    state.is_shutdown = False
    state.is_paused = False
    state.paused_until = None
    db.session.commit()
    notify_rani("Saki er aktiv igen. Klar til at hjælpe. Saki")


def _send_status() -> None:
    waiting = ArticleReview.query.filter_by(status="waiting").count()
    overdue = ArticleReview.query.filter_by(status="claimed").filter(
        ArticleReview.deadline < datetime.utcnow()
    ).count()
    notify_rani(
        f"Artikler der venter på review: {waiting}\n"
        f"Overskyldne reviews: {overdue}\n"
        f"Saki"
    )


def _send_settings() -> None:
    state = get_saki_state()
    paused_groups = json.loads(state.paused_groups_json or "[]")
    paused_labels = [code_to_label(c) for c in paused_groups] or ["Ingen"]
    pause_info = "Nej"
    if state.is_paused and state.paused_until:
        pause_info = f"Ja (til {state.paused_until.strftime('%H:%M')})"
    notify_rani(
        f"Islamiske påmindelser: {'Til' if state.islamic_reminders_enabled else 'Fra'}\n"
        f"Global pause: {pause_info}\n"
        f"Shutdown: {'Ja' if state.is_shutdown else 'Nej'}\n"
        f"Grupper på pause: {', '.join(paused_labels)}\n"
        f"Saki"
    )


def _check_now() -> None:
    try:
        from integrations.planner import sync_tasks_to_db
        sync_tasks_to_db(config.PLANNER_PLAN_ID_RD)
        sync_tasks_to_db(config.PLANNER_PLAN_ID_MARKETING)
        notify_rani("Planner er synkroniseret. Saki")
    except Exception as e:
        notify_rani(f"Synkronisering fejlede: {type(e).__name__}. Saki")


def _set_mode(mode: str) -> None:
    from functions.mode_router import set_mode, VALID_MODES
    if mode not in VALID_MODES:
        notify_rani(f"Ugyldig tilstand '{mode}'. Vælg: test, shadow eller live. Saki")
        return
    set_mode(mode)
    _mode_labels = {"test": "test-tilstand", "shadow": "shadow-tilstand", "live": "live-tilstand"}
    notify_rani(f"Skift bekræftet. Jeg kører nu i {_mode_labels[mode]}. Saki")


def _show_current_mode() -> None:
    from functions.mode_router import get_current_mode
    mode = get_current_mode()
    descriptions = {
        "test": "test – sender kun til testgrupper",
        "shadow": "shadow – sender kladder til Rani i stedet for rigtige grupper",
        "live": "live – sender direkte til alle rigtige grupper",
    }
    notify_rani(f"Nuværende tilstand: {descriptions.get(mode, mode)}. Saki")


def _test_trigger(trigger_type: str) -> None:
    from functions.mode_router import get_current_mode
    mode = get_current_mode()
    if mode not in ("test", "shadow"):
        notify_rani("Test-kommandoer virker kun i test- eller shadow-tilstand. Saki")
        return
    try:
        if trigger_type == "status_update":
            from functions.monday_status import request_monday_status_send
            request_monday_status_send()
            notify_rani("Mandagsopdatering er sendt nu. Saki")
        elif trigger_type == "poll":
            from functions.weekly_polls import request_weekly_poll_send
            request_weekly_poll_send()
            notify_rani("Ugentlig poll er sendt nu. Saki")
        elif trigger_type == "review_request":
            from functions.article_review import sync_articles_from_planner, send_weekly_review_request
            sync_articles_from_planner()
            send_weekly_review_request()
            notify_rani("Artikel-reviewanmodning er sendt nu. Saki")
    except Exception as e:
        notify_rani(f"Test-trigger fejlede: {type(e).__name__}. Saki")


def _force_draft() -> None:
    from functions.mode_router import get_current_mode
    if get_current_mode() != "shadow":
        notify_rani("force_draft virker kun i shadow-tilstand. Saki")
        return
    try:
        from functions.monday_status import request_monday_status_send
        request_monday_status_send()
        notify_rani("Næste kladde er sendt til dig nu. Saki")
    except Exception as e:
        notify_rani(f"force_draft fejlede: {type(e).__name__}. Saki")
