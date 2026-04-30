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


@bp.route("/logout")
def logout():
    session.pop("dashboard_logged_in", None)
    return redirect(url_for("dashboard.login"))
