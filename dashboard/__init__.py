from flask import Blueprint

bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/agents",
    template_folder="templates",
)

from dashboard import routes  # noqa: E402,F401
