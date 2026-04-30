"""Function 8: Article review workflow for R&D team."""
from datetime import datetime, date, timedelta
from database.db import db
from database.models import ArticleReview, TeamMember
from ai.message_generator import generate_group_message, generate_rani_dm
import integrations.whatsapp as wa
import integrations.planner as planner
from config import config


def sync_articles_from_planner() -> int:
    """Pull tasks from Planner 'Ready for Review' bucket and add to review queue."""
    tasks = planner.get_tasks_in_bucket(
        config.PLANNER_PLAN_ID_RD,
        config.PLANNER_BUCKET_READY_FOR_REVIEW,
    )
    added = 0
    for task in tasks:
        existing = ArticleReview.query.filter_by(planner_task_id=task["id"]).first()
        if not existing:
            details = planner.get_task_details(task["id"])
            link = _extract_link(details)
            review = ArticleReview(
                planner_task_id=task["id"],
                title=task.get("title", "Unavngivet artikel"),
                article_link=link,
                status="waiting",
                week_requested=_this_monday(),
            )
            db.session.add(review)
            added += 1
    db.session.commit()
    return added


def send_weekly_review_request(platform: str = "whatsapp") -> None:
    waiting = ArticleReview.query.filter_by(status="waiting").all()
    if not waiting:
        return

    articles_str = "\n".join(
        f"Artikel {i+1} – {a.title} – {a.article_link or 'link i Planner'}"
        for i, a in enumerate(waiting)
    )
    context = "Send en ugentlig reviewforespørgsel til ekspertteamet med en liste over artikler der venter på review. Bed dem skrive artikelnummeret de vil tage."
    text = generate_group_message(context, {"Artikler": articles_str})

    if platform == "whatsapp":
        wa.send_to_expertise_group(text)
    elif platform == "telegram":
        import integrations.telegram as tg
        tg.send_to_expertise_group(text)
    else:
        import integrations.teams as teams
        teams.send_to_expertise_channel(text)

    for a in waiting:
        a.unclaimed_ping_count += 1
    db.session.commit()


def handle_article_claim(member_id: int, article_number: int) -> None:
    """Called when a reviewer claims an article by number in the group."""
    waiting = ArticleReview.query.filter_by(status="waiting").all()
    idx = article_number - 1
    if idx < 0 or idx >= len(waiting):
        return

    article = waiting[idx]

    has_pending = ArticleReview.query.filter_by(
        claimed_by_id=member_id, status="claimed"
    ).first()
    if has_pending:
        member = db.session.get(TeamMember, member_id)
        if member:
            text = generate_rani_dm(
                f"Giv Rani besked om at {member.name} har prøvet at tage en ny artikel til review, men stadig har en afventende review der ikke er leveret."
            )
            wa.send_to_rani(text)
        return

    deadline = datetime.utcnow() + timedelta(days=config.ARTICLE_REVIEW_DAYS)
    article.claimed_by_id = member_id
    article.claimed_at = datetime.utcnow()
    article.deadline = deadline
    article.status = "claimed"
    db.session.commit()

    _send_private_claim_confirmation(member_id, article, deadline)


def _send_private_claim_confirmation(member_id: int, article: ArticleReview, deadline: datetime) -> None:
    member = db.session.get(TeamMember, member_id)
    if not member:
        return
    context = f"Send en privat besked til {member.name} om at bekræfte at de har taget artiklen '{article.title}' til review. Deadline er {deadline.strftime('%d/%m/%Y')}. Inkluder et link og en kort islamisk påmindelse om kvalitet og ansvar."
    text = generate_group_message(
        context,
        {
            "Artikel": article.title,
            "Link": article.article_link or "Se Planner",
            "Deadline": deadline.strftime("%d/%m/%Y"),
        },
        use_reminder=True,
    )
    if member.whatsapp_number:
        wa.send_to_member(member.whatsapp_number, text)


def send_deadline_reminders() -> None:
    cutoff = datetime.utcnow() + timedelta(days=config.ARTICLE_REMINDER_DAYS_BEFORE)
    due_soon = ArticleReview.query.filter(
        ArticleReview.status == "claimed",
        ArticleReview.deadline <= cutoff,
        ArticleReview.reminder_sent == False,
    ).all()

    for article in due_soon:
        member = db.session.get(TeamMember, article.claimed_by_id)
        if not member:
            continue
        context = f"Send {member.name} en venlig påmindelse om at deadline for review af artiklen '{article.title}' er om {config.ARTICLE_REMINDER_DAYS_BEFORE} dage."
        text = generate_group_message(context, use_reminder=False)
        if member.whatsapp_number:
            wa.send_to_member(member.whatsapp_number, text)
        article.reminder_sent = True
    db.session.commit()


def check_overdue_reviews() -> None:
    now = datetime.utcnow()
    overdue = ArticleReview.query.filter(
        ArticleReview.status == "claimed",
        ArticleReview.deadline < now,
    ).all()

    for article in overdue:
        article.status = "overdue"
        member = db.session.get(TeamMember, article.claimed_by_id)
        if member:
            text = generate_rani_dm(
                f"Giv Rani besked om at {member.name} ikke leverede reviewet af '{article.title}' til deadline. Artiklen er nu markeret som forsinket."
            )
            wa.send_to_rani(text)
    db.session.commit()


def check_pattern_non_delivery() -> None:
    """Flag reviewers who repeatedly claim but don't deliver."""
    members = TeamMember.query.filter_by(is_active=True).all()
    for member in members:
        overdue_count = ArticleReview.query.filter_by(
            claimed_by_id=member.id, status="overdue"
        ).count()
        if overdue_count >= 2:
            text = generate_rani_dm(
                f"Fortæl Rani at {member.name} har {overdue_count} uleverede reviewanmodninger og bør kontaktes. Saki tildeler ikke nye artikler til vedkommende endnu."
            )
            wa.send_to_rani(text)


def ping_unclaimed_articles(platform: str = "whatsapp") -> None:
    """3-day follow-up ping for still-unclaimed articles."""
    three_days_ago = date.today() - timedelta(days=3)
    unclaimed = ArticleReview.query.filter(
        ArticleReview.status == "waiting",
        ArticleReview.week_requested <= three_days_ago,
        ArticleReview.unclaimed_ping_count == 1,
    ).all()

    if not unclaimed:
        return

    articles_str = "\n".join(f"- {a.title}" for a in unclaimed)
    context = "Send en blid påmindelse om at disse artikler stadig mangler en reviewer. Bed teamet tage en."
    text = generate_group_message(context, {"Artikler uden reviewer": articles_str}, use_reminder=False)

    if platform == "whatsapp":
        wa.send_to_expertise_group(text)
    elif platform == "telegram":
        import integrations.telegram as tg
        tg.send_to_expertise_group(text)

    for a in unclaimed:
        a.unclaimed_ping_count = 2
    db.session.commit()


def escalate_unclaimed_to_rani() -> None:
    """After 6 days unclaimed, escalate to Rani."""
    six_days_ago = date.today() - timedelta(days=6)
    unclaimed = ArticleReview.query.filter(
        ArticleReview.status == "waiting",
        ArticleReview.week_requested <= six_days_ago,
        ArticleReview.unclaimed_ping_count >= 2,
    ).all()

    if not unclaimed:
        return

    titles = ", ".join(a.title for a in unclaimed)
    text = generate_rani_dm(
        f"Fortæl Rani at disse artikler stadig ikke har en reviewer efter 6 dage og har brug for hans opmærksomhed: {titles}"
    )
    wa.send_to_rani(text)

    for a in unclaimed:
        a.unclaimed_ping_count = 99
    db.session.commit()


def mark_article_completed(planner_task_id: str, feedback: str = None) -> None:
    article = ArticleReview.query.filter_by(planner_task_id=planner_task_id).first()
    if not article:
        return
    article.status = "completed"
    article.completed_at = datetime.utcnow()
    if feedback:
        article.feedback_text = feedback
    db.session.commit()


def _extract_link(task_details: dict) -> str | None:
    refs = task_details.get("references", {})
    for url in refs:
        return url
    return None


def _this_monday() -> date:
    from datetime import timedelta
    today = date.today()
    return today - timedelta(days=today.weekday())
