import hashlib
import hmac
import functools
from flask import session, redirect, url_for
from config import config


def check_password(password: str) -> bool:
    given = hashlib.sha256(password.encode()).hexdigest()
    expected = hashlib.sha256(config.DASHBOARD_PASSWORD.encode()).hexdigest()
    return hmac.compare_digest(given, expected)


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("dashboard_logged_in"):
            return redirect(url_for("dashboard.login"))
        return f(*args, **kwargs)
    return decorated
