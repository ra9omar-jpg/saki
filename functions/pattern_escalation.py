"""Function 17: Explicit escalation rules for members who miss repeatedly."""
import logging
from datetime import date, timedelta
from database.models import TeamMember, EngagementRecord, ArticleReview
import integrations.whatsapp as wa
from config import config

logger = logging.getLogger(__name__)


def check_status_update_patterns() -> None:
    """Flag R&D members missing Monday status updates consecutively."""
    for member in TeamMember.query.filter_by(is_active=True, team="rd").all():
        misses = _consecutive_status_misses(member.id)
        _escalate(member, misses, "mandagsopdateringer")


def check_article_review_patterns() -> None:
    """Flag reviewers who claim articles but consistently don't deliver."""
    for member in TeamMember.query.filter_by(is_active=True).all():
        pending = ArticleReview.query.filter_by(
            claimed_by_id=member.id, status="claimed"
        ).count()
        if pending >= config.MISS_SECOND_NOTIFY:
            wa.send_to_rani(
                f"{member.name} har {pending} reviews der ikke er leveret. "
                f"De er udelukket fra nye reviewanmodninger indtil de leverer. Saki"
            )


def _consecutive_status_misses(member_id: int) -> int:
    today = date.today()
    streak = 0
    for w in range(1, 6):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=w)
        rec = EngagementRecord.query.filter_by(member_id=member_id, week_of=week_start).first()
        if rec and rec.status_update_responded:
            break
        elif rec:
            streak += 1
    return streak


def _escalate(member: TeamMember, misses: int, activity: str) -> None:
    if misses == config.MISS_THIRD_ALERT:
        wa.send_to_rani(
            f"{member.name} har misset {misses} {activity} i træk. "
            f"Måske en samtale er nødvendig. Saki"
        )
    elif misses == config.MISS_SECOND_NOTIFY:
        wa.send_to_rani(f"{member.name} har misset {misses} {activity} i træk. Saki")
