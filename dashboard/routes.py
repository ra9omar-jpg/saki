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
    return render_template("dashboard/index.html", active="index")


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
