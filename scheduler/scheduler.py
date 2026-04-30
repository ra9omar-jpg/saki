import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("Europe/Copenhagen")
_scheduler = BackgroundScheduler(timezone=TIMEZONE)


def start(app):
    """Start all scheduled jobs."""

    # === MONDAY: R&D status request ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _monday_status_request),
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=TIMEZONE),
        id="monday_status_request", replace_existing=True,
    )

    # === TUESDAY: R&D status reminder ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _tuesday_status_reminder),
        trigger=CronTrigger(day_of_week="tue", hour=18, minute=0, timezone=TIMEZONE),
        id="tuesday_status_reminder", replace_existing=True,
    )

    # === WEDNESDAY: Flag non-responders to Rani ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _wednesday_flag),
        trigger=CronTrigger(day_of_week="wed", hour=9, minute=0, timezone=TIMEZONE),
        id="wednesday_flag", replace_existing=True,
    )

    # === WEEKLY POLL: Ask Rani timing every Monday ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _weekly_poll_request),
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=30, timezone=TIMEZONE),
        id="weekly_poll_request", replace_existing=True,
    )

    # === POLL REMINDERS: Check every hour ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _poll_reminder_check),
        trigger=CronTrigger(minute=0, timezone=TIMEZONE),
        id="poll_reminder_check", replace_existing=True,
    )

    # === ARTICLE REVIEW: Weekly request on Sundays ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _article_review_weekly),
        trigger=CronTrigger(day_of_week="sun", hour=10, minute=0, timezone=TIMEZONE),
        id="article_review_weekly", replace_existing=True,
    )

    # === ARTICLE REMINDERS: Daily check ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _article_deadline_check),
        trigger=CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="article_deadline_check", replace_existing=True,
    )

    # === ARTICLE UNCLAIMED PING: Every Wednesday ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _article_unclaimed_ping),
        trigger=CronTrigger(day_of_week="wed", hour=10, minute=0, timezone=TIMEZONE),
        id="article_unclaimed_ping", replace_existing=True,
    )

    # === ARTICLE ESCALATE: Weekly on Saturday ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _article_escalate),
        trigger=CronTrigger(day_of_week="sat", hour=10, minute=0, timezone=TIMEZONE),
        id="article_escalate", replace_existing=True,
    )

    # === QUESTION MONITOR: Every 30 minutes ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _question_monitor),
        trigger=CronTrigger(minute="0,30", timezone=TIMEZONE),
        id="question_monitor", replace_existing=True,
    )

    # === ENGAGEMENT REPORT: Every Friday ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _engagement_report),
        trigger=CronTrigger(day_of_week="fri", hour=17, minute=0, timezone=TIMEZONE),
        id="engagement_report", replace_existing=True,
    )

    # === MARKETING PATTERN REPORT: Every Friday ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _marketing_pattern_report),
        trigger=CronTrigger(day_of_week="fri", hour=17, minute=30, timezone=TIMEZONE),
        id="marketing_pattern_report", replace_existing=True,
    )

    # === PATTERN ESCALATION: Every Wednesday (Function 17) ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _pattern_escalation_check),
        trigger=CronTrigger(day_of_week="wed", hour=11, minute=0, timezone=TIMEZONE),
        id="pattern_escalation_check", replace_existing=True,
    )

    # === PAUSE AUTO-RESUME: Every 15 minutes (Function 11) ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _resume_pause_check, skip_if_paused=False),
        trigger=CronTrigger(minute="0,15,30,45", timezone=TIMEZONE),
        id="resume_pause_check", replace_existing=True,
    )

    # === PLANNER SYNC: Every 15 minutes ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _planner_sync),
        trigger=CronTrigger(minute="0,15,30,45", timezone=TIMEZONE),
        id="planner_sync", replace_existing=True,
    )

    # === CONFIRMED MESSAGE DISPATCHER: Every 5 minutes (BUG 6) ===
    _scheduler.add_job(
        func=lambda: _with_app(app, _dispatch_approved_confirmations),
        trigger=CronTrigger(minute="*/5", timezone=TIMEZONE),
        id="dispatch_approved_confirmations", replace_existing=True,
    )

    _scheduler.start()


def stop():
    if _scheduler.running:
        _scheduler.shutdown()


def _with_app(app, fn, skip_if_paused=True):
    with app.app_context():
        try:
            if skip_if_paused:
                from functions.control_menu import is_saki_active
                if not is_saki_active():
                    return
            fn()
        except Exception as e:
            logger.error("Scheduler-fejl i %s: %s", fn.__name__, e, exc_info=True)
            try:
                from functions.error_alerts import alert_rani
                alert_rani(fn.__name__, e, "Forsøger igen næste kørsel.")
            except Exception:
                pass


def _monday_status_request():
    from functions.monday_status import request_monday_status_send
    request_monday_status_send()


def _tuesday_status_reminder():
    from functions.monday_status import send_tuesday_reminder
    send_tuesday_reminder(platform=_active_platform())


def _wednesday_flag():
    from functions.monday_status import send_wednesday_flag_to_rani
    send_wednesday_flag_to_rani()


def _weekly_poll_request():
    from functions.weekly_polls import request_weekly_poll_send
    request_weekly_poll_send()


def _poll_reminder_check():
    from functions.weekly_polls import send_poll_reminder, get_active_poll, close_poll_and_report
    from datetime import datetime, timedelta
    poll = get_active_poll()
    if not poll or poll.is_closed:
        return
    now = datetime.utcnow()
    if poll.closes_at:
        time_left = poll.closes_at - now
        if not poll.reminder_sent_24h and time_left <= timedelta(hours=24):
            send_poll_reminder(poll.id, "24h")
        elif not poll.reminder_sent_12h and time_left <= timedelta(hours=12):
            send_poll_reminder(poll.id, "12h")
        if time_left <= timedelta(0):
            close_poll_and_report(poll.id)


def _article_review_weekly():
    from functions.article_review import sync_articles_from_planner, send_weekly_review_request
    sync_articles_from_planner()
    send_weekly_review_request(platform=_active_platform())


def _article_deadline_check():
    from functions.article_review import send_deadline_reminders, check_overdue_reviews, check_pattern_non_delivery
    send_deadline_reminders()
    check_overdue_reviews()
    check_pattern_non_delivery()


def _article_unclaimed_ping():
    from functions.article_review import ping_unclaimed_articles
    ping_unclaimed_articles(platform=_active_platform())


def _article_escalate():
    from functions.article_review import escalate_unclaimed_to_rani
    escalate_unclaimed_to_rani()


def _question_monitor():
    from functions.question_monitor import check_unanswered_questions
    check_unanswered_questions()


def _engagement_report():
    from functions.engagement_tracking import send_weekly_engagement_report
    send_weekly_engagement_report()


def _marketing_pattern_report():
    from functions.marketing_tracking import generate_weekly_pattern_report
    generate_weekly_pattern_report()


def _pattern_escalation_check():
    from functions.pattern_escalation import check_status_update_patterns, check_article_review_patterns
    check_status_update_patterns()
    check_article_review_patterns()


def _resume_pause_check():
    from functions.control_menu import check_and_resume_pause
    check_and_resume_pause()


def _planner_sync():
    from integrations.planner import sync_tasks_to_db
    from config import config
    sync_tasks_to_db(config.PLANNER_PLAN_ID_RD)
    sync_tasks_to_db(config.PLANNER_PLAN_ID_MARKETING)


def _active_platform() -> str:
    from config import config
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN not in ("pending", ""):
        return "telegram"
    return "whatsapp"


def _dispatch_approved_confirmations():
    from database.models import RaniConfirmation
    from database.db import db
    from datetime import datetime
    now = datetime.utcnow()
    pending = RaniConfirmation.query.filter(
        RaniConfirmation.confirmed_at.isnot(None),
        RaniConfirmation.is_sent == False,
        RaniConfirmation.scheduled_time.isnot(None),
        RaniConfirmation.scheduled_time <= now,
    ).all()
    for conf in pending:
        try:
            _execute_confirmation(conf.message_type)
            conf.is_sent = True
        except Exception as e:
            logger.error("Dispatch fejlede for %s: %s", conf.message_type, e)
    db.session.commit()


def _execute_confirmation(message_type: str) -> None:
    platform = _active_platform()
    if message_type == "monday_status_rd":
        from functions.monday_status import send_monday_status_request
        send_monday_status_request(platform=platform)
    elif message_type == "weekly_poll":
        from functions.weekly_polls import send_weekly_poll
        send_weekly_poll(platform=platform)
    elif message_type == "weekly_review":
        from functions.article_review import sync_articles_from_planner, send_weekly_review_request
        sync_articles_from_planner()
        send_weekly_review_request(platform=platform)
