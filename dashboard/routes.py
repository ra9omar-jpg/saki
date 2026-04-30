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
    return render_template("dashboard/control.html", active="control")


@bp.route("/saki/team")
@login_required
def team():
    return render_template("dashboard/team.html", active="team")


@bp.route("/saki/articles")
@login_required
def articles():
    return render_template("dashboard/articles.html", active="articles")


@bp.route("/saki/engagement")
@login_required
def engagement():
    return render_template("dashboard/engagement.html", active="engagement")
