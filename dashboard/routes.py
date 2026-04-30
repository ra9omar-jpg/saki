from flask import render_template, redirect, url_for, request, flash, session
from dashboard import bp
from dashboard.auth import login_required, check_password


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if check_password(request.form.get("password", "")):
            session["dashboard_logged_in"] = True
            return redirect(url_for("dashboard.index"))
        flash("Forkert adgangskode.", "error")
    return render_template("dashboard/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("dashboard_logged_in", None)
    return redirect(url_for("dashboard.login"))


@bp.route("/saki/")
@login_required
def index():
    from database.models import get_saki_state, IncomingMessage, ArticleReview, StatusUpdate, TeamMember
    from datetime import date, timedelta

    state = get_saki_state()

    unanswered = IncomingMessage.query.filter(
        IncomingMessage.is_question == True,
        IncomingMessage.answered_at == None,
        IncomingMessage.escalated_to_rani_at == None,
    ).count()

    articles_waiting = ArticleReview.query.filter_by(status="waiting").count()
    articles_overdue = ArticleReview.query.filter_by(status="overdue").count()

    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    total_rd = TeamMember.query.filter_by(team="rd", is_active=True).count()
    responded_this_week = StatusUpdate.query.filter_by(week_of=this_monday).count()
    missing_status = max(0, total_rd - responded_this_week)

    mode_labels = {
        "test": ("Test", "bg-blue-100 text-blue-700"),
        "shadow": ("Shadow", "bg-yellow-100 text-yellow-700"),
        "live": ("Live", "bg-green-100 text-green-700"),
    }
    mode_label, mode_color = mode_labels.get(state.mode, (state.mode, "bg-gray-100 text-gray-700"))

    return render_template(
        "dashboard/index.html",
        active="index",
        state=state,
        mode_label=mode_label,
        mode_color=mode_color,
        unanswered=unanswered,
        articles_waiting=articles_waiting,
        articles_overdue=articles_overdue,
        missing_status=missing_status,
    )


@bp.route("/saki/control")
@login_required
def control():
    from database.models import get_saki_state, RaniConfirmation
    state = get_saki_state()
    pending_confirmations = RaniConfirmation.query.filter_by(confirmed_at=None).order_by(
        RaniConfirmation.requested_at.asc()
    ).all()
    return render_template(
        "dashboard/control.html",
        active="control",
        state=state,
        pending_confirmations=pending_confirmations,
    )


@bp.route("/saki/control/mode", methods=["POST"])
@login_required
def set_mode():
    mode = request.form.get("mode", "")
    if mode in ("test", "shadow", "live"):
        from functions.mode_router import set_mode as do_set_mode
        do_set_mode(mode)
        flash(f"Tilstand skiftet til: {mode}", "success")
    else:
        flash("Ugyldig tilstand.", "error")
    return redirect(url_for("dashboard.control"))


@bp.route("/saki/control/pause", methods=["POST"])
@login_required
def quick_pause():
    from functions.control_menu import handle_quick_pause
    handle_quick_pause()
    flash("Saki er sat på pause i 5 timer.", "success")
    return redirect(url_for("dashboard.control"))


@bp.route("/saki/control/wakeup", methods=["POST"])
@login_required
def wake_up():
    from functions.control_menu import _wake_up
    _wake_up()
    flash("Saki er aktiv igen.", "success")
    return redirect(url_for("dashboard.control"))


@bp.route("/saki/control/broadcast", methods=["POST"])
@login_required
def broadcast():
    from functions.group_config import label_to_code, code_to_whatsapp_id, code_to_telegram_id, code_to_label
    import integrations.telegram as tg
    import integrations.whatsapp as wa

    group_label = request.form.get("group", "")
    message = request.form.get("message", "").strip()
    if not message:
        flash("Besked må ikke være tom.", "error")
        return redirect(url_for("dashboard.control"))

    code = label_to_code(group_label)
    if not code:
        flash(f"Gruppe '{group_label}' ikke fundet.", "error")
        return redirect(url_for("dashboard.control"))

    tg_id = code_to_telegram_id(code)
    if tg_id:
        tg.send_to_group(tg_id, message)
    else:
        wa_id = code_to_whatsapp_id(code)
        if wa_id:
            wa.send_to_group(wa_id, message)

    flash(f"Besked sendt til {code_to_label(code)}.", "success")
    return redirect(url_for("dashboard.control"))


@bp.route("/saki/control/confirm/<int:conf_id>", methods=["POST"])
@login_required
def approve_confirmation(conf_id):
    from database.models import RaniConfirmation
    from database.db import db
    from datetime import datetime
    conf = db.session.get(RaniConfirmation, conf_id)
    if conf and not conf.confirmed_at:
        conf.confirmed_at = datetime.utcnow()
        conf.scheduled_time = datetime.utcnow()
        db.session.commit()
        flash("Besked er godkendt og sendes inden for 5 minutter.", "success")
    return redirect(url_for("dashboard.control"))


@bp.route("/saki/team")
@login_required
def team():
    from database.models import TeamMember, EngagementRecord
    from datetime import date, timedelta
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.team, TeamMember.name).all()
    engagement = {
        r.member_id: r
        for r in EngagementRecord.query.filter_by(week_of=this_monday).all()
    }
    return render_template("dashboard/team.html", active="team", members=members, engagement=engagement)


@bp.route("/saki/team/add", methods=["POST"])
@login_required
def add_member():
    from database.models import TeamMember
    from database.db import db
    name = request.form.get("name", "").strip()
    team_name = request.form.get("team", "")
    role = request.form.get("role", "member")
    telegram_chat_id = request.form.get("telegram_chat_id", "").strip() or None

    if not name or team_name not in ("rd", "marketing"):
        flash("Navn og gyldigt team er påkrævet.", "error")
        return redirect(url_for("dashboard.team"))

    member = TeamMember(
        name=name,
        team=team_name,
        role=role,
        telegram_chat_id=telegram_chat_id,
    )
    db.session.add(member)
    db.session.commit()
    flash(f"{name} er tilføjet til {team_name}-teamet.", "success")
    return redirect(url_for("dashboard.team"))


@bp.route("/saki/team/<int:member_id>/deactivate", methods=["POST"])
@login_required
def deactivate_member(member_id):
    from database.models import TeamMember
    from database.db import db
    member = db.session.get(TeamMember, member_id)
    if member:
        member.is_active = False
        db.session.commit()
        flash(f"{member.name} er deaktiveret.", "success")
    return redirect(url_for("dashboard.team"))


@bp.route("/saki/articles")
@login_required
def articles():
    from database.models import ArticleReview, TeamMember
    all_articles = ArticleReview.query.order_by(ArticleReview.week_requested.desc()).limit(50).all()
    members = {m.id: m for m in TeamMember.query.all()}
    return render_template("dashboard/articles.html", active="articles",
                           articles=all_articles, members=members)


@bp.route("/saki/articles/<int:article_id>/complete", methods=["POST"])
@login_required
def complete_article(article_id):
    from database.models import ArticleReview
    from database.db import db
    from datetime import datetime
    article = db.session.get(ArticleReview, article_id)
    if article:
        article.status = "completed"
        article.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f"'{article.title[:40]}' markeret som færdig.", "success")
    return redirect(url_for("dashboard.articles"))


@bp.route("/saki/engagement")
@login_required
def engagement():
    from database.models import TeamMember, EngagementRecord
    from datetime import date, timedelta
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.team, TeamMember.name).all()
    records = {
        r.member_id: r
        for r in EngagementRecord.query.filter_by(week_of=this_monday).all()
    }
    return render_template("dashboard/engagement.html", active="engagement",
                           members=members, records=records, week=this_monday)
