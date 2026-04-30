# Sakeena AI Hub — Dashboard V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a password-protected web dashboard on `/agents/saki/` that lets Rani control Saki, manage the team, and view reports — without opening Telegram.

**Architecture:** Flask Blueprint (`dashboard/`) registered on the existing Railway app. Server-side Jinja2 templates with TailwindCSS via CDN. Session-based auth with hashed password. All pages share the same SQLite database already used by Saki. URL structure `/agents/saki/` is designed to expand to `/agents/<other-agent>/` in the future.

**Tech Stack:** Flask, Jinja2, TailwindCSS (CDN Play), Flask sessions, SQLAlchemy (existing), Python 3.12, Railway

---

## File Structure

```
dashboard/
  __init__.py              # Blueprint definition
  auth.py                  # login_required decorator + check_password
  routes.py                # All page routes and POST handlers
  templates/
    dashboard/
      base.html            # Sidebar layout + flash messages
      login.html           # Login page
      index.html           # Overview (status, quick stats)
      control.html         # Saki control (mode, pause, broadcast, confirmations)
      team.html            # Team list + add member form
      articles.html        # Article review queue
      engagement.html      # Weekly engagement report

config.py                  # Add DASHBOARD_PASSWORD
webhook/app.py             # Register dashboard blueprint
```

---

## Task 1: Config + Blueprint scaffold

**Files:**
- Modify: `config.py`
- Create: `dashboard/__init__.py`
- Modify: `webhook/app.py`

- [ ] **Step 1: Add DASHBOARD_PASSWORD to config.py**

Find the line `SECRET_KEY = os.environ.get(...)` in `config.py` and add directly below it:

```python
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "sakeena2026")
```

- [ ] **Step 2: Create dashboard/__init__.py**

```python
from flask import Blueprint

bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/agents",
    template_folder="templates",
)

from dashboard import routes  # noqa: E402,F401
from dashboard import auth    # noqa: E402,F401
```

- [ ] **Step 3: Create dashboard/auth.py (scaffold only — full implementation in Task 2)**

```python
import hashlib
import functools
from flask import session, redirect, url_for
from config import config


def check_password(password: str) -> bool:
    given = hashlib.sha256(password.encode()).hexdigest()
    expected = hashlib.sha256(config.DASHBOARD_PASSWORD.encode()).hexdigest()
    return given == expected


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("dashboard_logged_in"):
            return redirect(url_for("dashboard.login"))
        return f(*args, **kwargs)
    return decorated
```

- [ ] **Step 4: Create dashboard/routes.py (scaffold only — pages added in later tasks)**

```python
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
```

- [ ] **Step 5: Register blueprint in webhook/app.py**

Inside `create_app()`, just before `return app`, add:

```python
    from dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
```

- [ ] **Step 6: Verify app still starts**

```bash
cd "/Users/Sara/Desktop/ranis fil/saki" && python -c "from webhook.app import create_app; app = create_app(); print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add config.py dashboard/__init__.py dashboard/auth.py dashboard/routes.py webhook/app.py
git commit -m "feat: add dashboard blueprint scaffold with auth"
```

---

## Task 2: Base HTML layout + login page

**Files:**
- Create: `dashboard/templates/dashboard/base.html`
- Create: `dashboard/templates/dashboard/login.html`

- [ ] **Step 1: Create templates directory**

```bash
mkdir -p "/Users/Sara/Desktop/ranis fil/saki/dashboard/templates/dashboard"
```

- [ ] **Step 2: Create base.html**

```html
<!DOCTYPE html>
<html lang="da">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Sakeena AI Hub{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
<div class="flex min-h-screen">

  <!-- Sidebar -->
  <aside class="w-56 bg-slate-800 text-white flex flex-col shrink-0">
    <div class="px-6 py-5 border-b border-slate-700">
      <p class="text-xs text-slate-400 uppercase tracking-widest mb-1">Sakeena</p>
      <h1 class="text-base font-bold leading-tight">AI Hub</h1>
    </div>

    <div class="px-3 py-2 border-b border-slate-700">
      <p class="px-3 py-1 text-xs text-slate-500 uppercase tracking-widest">Saki</p>
      <nav class="mt-1 space-y-0.5">
        <a href="{{ url_for('dashboard.index') }}"
           class="block px-3 py-2 rounded text-sm {% if active == 'index' %}bg-slate-600 text-white{% else %}text-slate-300 hover:bg-slate-700{% endif %}">
          Oversigt
        </a>
        <a href="{{ url_for('dashboard.control') }}"
           class="block px-3 py-2 rounded text-sm {% if active == 'control' %}bg-slate-600 text-white{% else %}text-slate-300 hover:bg-slate-700{% endif %}">
          Kontrol
        </a>
        <a href="{{ url_for('dashboard.team') }}"
           class="block px-3 py-2 rounded text-sm {% if active == 'team' %}bg-slate-600 text-white{% else %}text-slate-300 hover:bg-slate-700{% endif %}">
          Team
        </a>
        <a href="{{ url_for('dashboard.articles') }}"
           class="block px-3 py-2 rounded text-sm {% if active == 'articles' %}bg-slate-600 text-white{% else %}text-slate-300 hover:bg-slate-700{% endif %}">
          Artikel-review
        </a>
        <a href="{{ url_for('dashboard.engagement') }}"
           class="block px-3 py-2 rounded text-sm {% if active == 'engagement' %}bg-slate-600 text-white{% else %}text-slate-300 hover:bg-slate-700{% endif %}">
          Engagement
        </a>
      </nav>
    </div>

    <div class="flex-1"></div>

    <div class="px-3 pb-4">
      <a href="{{ url_for('dashboard.logout') }}"
         class="block px-3 py-2 rounded text-sm text-slate-400 hover:bg-slate-700">
        Log ud
      </a>
    </div>
  </aside>

  <!-- Main content -->
  <main class="flex-1 p-8 overflow-auto">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="mb-4 px-4 py-3 rounded-md text-sm
          {% if category == 'error' %}bg-red-100 text-red-700 border border-red-200
          {% else %}bg-green-100 text-green-700 border border-green-200{% endif %}">
          {{ message }}
        </div>
      {% endfor %}
    {% endwith %}

    {% block content %}{% endblock %}
  </main>

</div>
</body>
</html>
```

- [ ] **Step 3: Create login.html**

```html
<!DOCTYPE html>
<html lang="da">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Log ind — Sakeena AI Hub</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-800 min-h-screen flex items-center justify-center">
<div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm">
  <div class="mb-6 text-center">
    <p class="text-xs text-gray-400 uppercase tracking-widest mb-1">Sakeena</p>
    <h1 class="text-xl font-bold text-gray-800">AI Hub</h1>
  </div>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="mb-4 px-3 py-2 rounded text-sm bg-red-100 text-red-700">{{ message }}</div>
    {% endfor %}
  {% endwith %}

  <form method="POST">
    <label class="block text-sm font-medium text-gray-700 mb-1">Adgangskode</label>
    <input type="password" name="password" autofocus required
           class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500 mb-4">
    <button type="submit"
            class="w-full bg-slate-800 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-slate-700">
      Log ind
    </button>
  </form>
</div>
</body>
</html>
```

- [ ] **Step 4: Test login page loads**

Start app locally (or check Railway after deploy — test now against Railway):

```bash
curl -s "https://upbeat-passion-production-a78d.up.railway.app/agents/login" | grep -c "Log ind"
```

Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add dashboard/templates/
git commit -m "feat: add base layout and login page"
```

---

## Task 3: Overview page

**Files:**
- Modify: `dashboard/routes.py`
- Create: `dashboard/templates/dashboard/index.html`

- [ ] **Step 1: Add index route to dashboard/routes.py**

Add after the `logout` route:

```python
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
```

- [ ] **Step 2: Create dashboard/templates/dashboard/index.html**

```html
{% extends "dashboard/base.html" %}
{% block title %}Oversigt — Sakeena AI Hub{% endblock %}

{% block content %}
<h2 class="text-2xl font-bold text-gray-800 mb-6">Oversigt</h2>

<!-- Status banner -->
<div class="bg-white rounded-xl border border-gray-200 p-5 mb-6 flex items-center gap-4">
  {% if state.is_shutdown %}
    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700">Shutdown</span>
    <p class="text-sm text-gray-600">Saki er lukket ned. Gå til Kontrol for at vække den.</p>
  {% elif state.is_paused %}
    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-700">På pause</span>
    <p class="text-sm text-gray-600">
      Saki er på pause
      {% if state.paused_until %} til kl. {{ state.paused_until.strftime('%H:%M') }}{% endif %}.
    </p>
  {% else %}
    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">Aktiv</span>
    <p class="text-sm text-gray-600">Saki kører normalt.</p>
  {% endif %}

  <span class="ml-auto inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {{ mode_color }}">
    {{ mode_label }}
  </span>
</div>

<!-- Stats grid -->
<div class="grid grid-cols-2 gap-4 mb-6">
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <p class="text-3xl font-bold text-gray-800">{{ unanswered }}</p>
    <p class="text-sm text-gray-500 mt-1">Ubesvarede spørgsmål</p>
  </div>
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <p class="text-3xl font-bold text-gray-800">{{ missing_status }}</p>
    <p class="text-sm text-gray-500 mt-1">Mangler ugentlig status</p>
  </div>
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <p class="text-3xl font-bold {% if articles_waiting > 0 %}text-yellow-600{% else %}text-gray-800{% endif %}">{{ articles_waiting }}</p>
    <p class="text-sm text-gray-500 mt-1">Artikler venter på reviewer</p>
  </div>
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <p class="text-3xl font-bold {% if articles_overdue > 0 %}text-red-600{% else %}text-gray-800{% endif %}">{{ articles_overdue }}</p>
    <p class="text-sm text-gray-500 mt-1">Forsinkede reviews</p>
  </div>
</div>

<!-- Quick links -->
<div class="bg-white rounded-xl border border-gray-200 p-5">
  <h3 class="text-sm font-semibold text-gray-700 mb-3">Hurtige handlinger</h3>
  <div class="flex gap-3">
    <a href="{{ url_for('dashboard.control') }}"
       class="px-4 py-2 bg-slate-800 text-white text-sm rounded-md hover:bg-slate-700">
      Gå til Kontrol
    </a>
    <a href="{{ url_for('dashboard.articles') }}"
       class="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50">
      Se artikel-kø
    </a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/routes.py dashboard/templates/dashboard/index.html
git commit -m "feat: add overview page with live status stats"
```

---

## Task 4: Saki control page

**Files:**
- Modify: `dashboard/routes.py`
- Create: `dashboard/templates/dashboard/control.html`

- [ ] **Step 1: Add control routes to dashboard/routes.py**

Add after the `index` route:

```python
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
    from config import config

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
```

- [ ] **Step 2: Create dashboard/templates/dashboard/control.html**

```html
{% extends "dashboard/base.html" %}
{% block title %}Kontrol — Sakeena AI Hub{% endblock %}

{% block content %}
<h2 class="text-2xl font-bold text-gray-800 mb-6">Saki-kontrol</h2>

<div class="grid grid-cols-2 gap-6 mb-6">

  <!-- Mode -->
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Tilstand</h3>
    <p class="text-xs text-gray-500 mb-3">Nuværende: <strong>{{ state.mode }}</strong></p>
    <form method="POST" action="{{ url_for('dashboard.set_mode') }}" class="flex gap-2">
      <select name="mode" class="flex-1 border border-gray-300 rounded-md text-sm px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500">
        <option value="test" {% if state.mode == 'test' %}selected{% endif %}>Test</option>
        <option value="shadow" {% if state.mode == 'shadow' %}selected{% endif %}>Shadow</option>
        <option value="live" {% if state.mode == 'live' %}selected{% endif %}>Live</option>
      </select>
      <button type="submit" class="px-4 py-1.5 bg-slate-800 text-white text-sm rounded-md hover:bg-slate-700">
        Skift
      </button>
    </form>
  </div>

  <!-- Pause / Wake up -->
  <div class="bg-white rounded-xl border border-gray-200 p-5">
    <h3 class="text-sm font-semibold text-gray-700 mb-3">Pause</h3>
    {% if state.is_paused or state.is_shutdown %}
      <p class="text-xs text-gray-500 mb-3">
        {% if state.is_shutdown %}Saki er lukket ned.{% else %}
        På pause til {{ state.paused_until.strftime('%H:%M') if state.paused_until else '?' }}.{% endif %}
      </p>
      <form method="POST" action="{{ url_for('dashboard.wake_up') }}">
        <button type="submit" class="px-4 py-1.5 bg-green-600 text-white text-sm rounded-md hover:bg-green-700">
          Vågn op
        </button>
      </form>
    {% else %}
      <p class="text-xs text-gray-500 mb-3">Saki er aktiv.</p>
      <form method="POST" action="{{ url_for('dashboard.quick_pause') }}">
        <button type="submit" class="px-4 py-1.5 bg-yellow-500 text-white text-sm rounded-md hover:bg-yellow-600">
          Pause 5 timer
        </button>
      </form>
    {% endif %}
  </div>

</div>

<!-- Broadcast -->
<div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
  <h3 class="text-sm font-semibold text-gray-700 mb-3">Send broadcast</h3>
  <form method="POST" action="{{ url_for('dashboard.broadcast') }}" class="space-y-3">
    <div class="flex gap-3">
      <select name="group" class="border border-gray-300 rounded-md text-sm px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500">
        <option value="rd">R&D</option>
        <option value="marketing">Marketing</option>
        <option value="ekspert">Ekspertise Review</option>
        <option value="lærere">Lærere</option>
      </select>
    </div>
    <textarea name="message" rows="3" placeholder="Skriv din besked..."
              class="w-full border border-gray-300 rounded-md text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-500 resize-none"></textarea>
    <button type="submit" class="px-4 py-2 bg-slate-800 text-white text-sm rounded-md hover:bg-slate-700">
      Send nu
    </button>
  </form>
</div>

<!-- Pending confirmations -->
{% if pending_confirmations %}
<div class="bg-white rounded-xl border border-gray-200 p-5">
  <h3 class="text-sm font-semibold text-gray-700 mb-3">Ventende godkendelser</h3>
  <table class="w-full text-sm">
    <thead>
      <tr class="text-left text-gray-500 border-b border-gray-100">
        <th class="pb-2 font-medium">Type</th>
        <th class="pb-2 font-medium">Beskrivelse</th>
        <th class="pb-2 font-medium">Anmodet</th>
        <th class="pb-2"></th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-50">
      {% for conf in pending_confirmations %}
      <tr class="py-2">
        <td class="py-2 text-gray-600">{{ conf.message_type }}</td>
        <td class="py-2 text-gray-600">{{ conf.description[:60] }}{% if conf.description|length > 60 %}…{% endif %}</td>
        <td class="py-2 text-gray-400 text-xs">{{ conf.requested_at.strftime('%d/%m %H:%M') }}</td>
        <td class="py-2 text-right">
          <form method="POST" action="{{ url_for('dashboard.approve_confirmation', conf_id=conf.id) }}" class="inline">
            <button type="submit" class="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700">
              Send nu
            </button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
<div class="bg-white rounded-xl border border-gray-200 p-5">
  <p class="text-sm text-gray-400">Ingen ventende godkendelser.</p>
</div>
{% endif %}

{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/routes.py dashboard/templates/dashboard/control.html
git commit -m "feat: add Saki control page (mode, pause, broadcast, confirmations)"
```

---

## Task 5: Team management page

**Files:**
- Modify: `dashboard/routes.py`
- Create: `dashboard/templates/dashboard/team.html`

- [ ] **Step 1: Add team routes to dashboard/routes.py**

```python
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
```

- [ ] **Step 2: Create dashboard/templates/dashboard/team.html**

```html
{% extends "dashboard/base.html" %}
{% block title %}Team — Sakeena AI Hub{% endblock %}

{% block content %}
<h2 class="text-2xl font-bold text-gray-800 mb-6">Team</h2>

<!-- Add member form -->
<div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
  <h3 class="text-sm font-semibold text-gray-700 mb-3">Tilføj nyt medlem</h3>
  <form method="POST" action="{{ url_for('dashboard.add_member') }}" class="flex gap-3 flex-wrap">
    <input type="text" name="name" placeholder="Navn" required
           class="border border-gray-300 rounded-md text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500 w-40">
    <select name="team" class="border border-gray-300 rounded-md text-sm px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500">
      <option value="rd">R&D</option>
      <option value="marketing">Marketing</option>
    </select>
    <select name="role" class="border border-gray-300 rounded-md text-sm px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500">
      <option value="member">Medlem</option>
      <option value="lead">Lead</option>
      <option value="admin">Admin</option>
    </select>
    <input type="text" name="telegram_chat_id" placeholder="Telegram ID (valgfrit)"
           class="border border-gray-300 rounded-md text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-500 w-44">
    <button type="submit" class="px-4 py-1.5 bg-slate-800 text-white text-sm rounded-md hover:bg-slate-700">
      Tilføj
    </button>
  </form>
</div>

<!-- Member table -->
<div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50">
      <tr class="text-left text-gray-500 text-xs uppercase tracking-wide">
        <th class="px-5 py-3 font-medium">Navn</th>
        <th class="px-5 py-3 font-medium">Team</th>
        <th class="px-5 py-3 font-medium">Rolle</th>
        <th class="px-5 py-3 font-medium">Status denne uge</th>
        <th class="px-5 py-3 font-medium">Telegram ID</th>
        <th class="px-5 py-3"></th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for m in members %}
      {% set eng = engagement.get(m.id) %}
      <tr>
        <td class="px-5 py-3 font-medium text-gray-800">{{ m.name }}</td>
        <td class="px-5 py-3 text-gray-500">{{ m.team }}</td>
        <td class="px-5 py-3 text-gray-500">{{ m.role }}</td>
        <td class="px-5 py-3">
          {% if eng and eng.status_update_responded %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">Svaret</span>
          {% else %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-500">Mangler</span>
          {% endif %}
        </td>
        <td class="px-5 py-3 text-gray-400 text-xs font-mono">{{ m.telegram_chat_id or '—' }}</td>
        <td class="px-5 py-3 text-right">
          <form method="POST" action="{{ url_for('dashboard.deactivate_member', member_id=m.id) }}"
                onsubmit="return confirm('Deaktiver {{ m.name }}?')">
            <button type="submit" class="text-xs text-red-500 hover:text-red-700">Deaktiver</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/routes.py dashboard/templates/dashboard/team.html
git commit -m "feat: add team management page with add/deactivate"
```

---

## Task 6: Article review page

**Files:**
- Modify: `dashboard/routes.py`
- Create: `dashboard/templates/dashboard/articles.html`

- [ ] **Step 1: Add article routes to dashboard/routes.py**

```python
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
```

- [ ] **Step 2: Create dashboard/templates/dashboard/articles.html**

```html
{% extends "dashboard/base.html" %}
{% block title %}Artikel-review — Sakeena AI Hub{% endblock %}

{% block content %}
<h2 class="text-2xl font-bold text-gray-800 mb-6">Artikel-review</h2>

<div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50">
      <tr class="text-left text-gray-500 text-xs uppercase tracking-wide">
        <th class="px-5 py-3 font-medium">Titel</th>
        <th class="px-5 py-3 font-medium">Status</th>
        <th class="px-5 py-3 font-medium">Reviewer</th>
        <th class="px-5 py-3 font-medium">Deadline</th>
        <th class="px-5 py-3"></th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for a in articles %}
      <tr>
        <td class="px-5 py-3">
          {% if a.article_link %}
            <a href="{{ a.article_link }}" target="_blank" class="text-blue-600 hover:underline">{{ a.title[:50] }}</a>
          {% else %}
            <span class="text-gray-800">{{ a.title[:50] }}</span>
          {% endif %}
        </td>
        <td class="px-5 py-3">
          {% if a.status == 'waiting' %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-700">Venter</span>
          {% elif a.status == 'claimed' %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700">Taget</span>
          {% elif a.status == 'overdue' %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-red-100 text-red-700">Forsinket</span>
          {% elif a.status == 'completed' %}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">Færdig</span>
          {% endif %}
        </td>
        <td class="px-5 py-3 text-gray-500">
          {% if a.claimed_by_id and members.get(a.claimed_by_id) %}
            {{ members[a.claimed_by_id].name }}
          {% else %}
            —
          {% endif %}
        </td>
        <td class="px-5 py-3 text-gray-500 text-xs">
          {% if a.deadline %}{{ a.deadline.strftime('%d/%m/%Y') }}{% else %}—{% endif %}
        </td>
        <td class="px-5 py-3 text-right">
          {% if a.status in ('claimed', 'overdue') %}
          <form method="POST" action="{{ url_for('dashboard.complete_article', article_id=a.id) }}">
            <button type="submit" class="text-xs text-green-600 hover:text-green-800">Marker færdig</button>
          </form>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
      {% if not articles %}
      <tr><td colspan="5" class="px-5 py-8 text-center text-gray-400">Ingen artikler i køen.</td></tr>
      {% endif %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/routes.py dashboard/templates/dashboard/articles.html
git commit -m "feat: add article review queue page"
```

---

## Task 7: Engagement report page

**Files:**
- Modify: `dashboard/routes.py`
- Create: `dashboard/templates/dashboard/engagement.html`

- [ ] **Step 1: Add engagement route to dashboard/routes.py**

```python
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
```

- [ ] **Step 2: Create dashboard/templates/dashboard/engagement.html**

```html
{% extends "dashboard/base.html" %}
{% block title %}Engagement — Sakeena AI Hub{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-6">
  <h2 class="text-2xl font-bold text-gray-800">Engagement</h2>
  <span class="text-sm text-gray-400">Uge startende {{ week.strftime('%d/%m/%Y') }}</span>
</div>

<div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50">
      <tr class="text-left text-gray-500 text-xs uppercase tracking-wide">
        <th class="px-5 py-3 font-medium">Navn</th>
        <th class="px-5 py-3 font-medium">Team</th>
        <th class="px-5 py-3 font-medium text-center">Status svaret</th>
        <th class="px-5 py-3 font-medium text-center">Poll svaret</th>
        <th class="px-5 py-3 font-medium text-center">Beskeder</th>
        <th class="px-5 py-3 font-medium text-center">Artikler taget</th>
        <th class="px-5 py-3 font-medium text-center">Artikler færdige</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for m in members %}
      {% set r = records.get(m.id) %}
      <tr>
        <td class="px-5 py-3 font-medium text-gray-800">{{ m.name }}</td>
        <td class="px-5 py-3 text-gray-500">{{ m.team }}</td>
        <td class="px-5 py-3 text-center">
          {% if r and r.status_update_responded %}✅{% else %}<span class="text-gray-300">—</span>{% endif %}
        </td>
        <td class="px-5 py-3 text-center">
          {% if r and r.poll_responded %}✅{% else %}<span class="text-gray-300">—</span>{% endif %}
        </td>
        <td class="px-5 py-3 text-center text-gray-600">{{ r.messages_sent_count if r else 0 }}</td>
        <td class="px-5 py-3 text-center text-gray-600">{{ r.articles_claimed if r else 0 }}</td>
        <td class="px-5 py-3 text-center text-gray-600">{{ r.articles_completed if r else 0 }}</td>
      </tr>
      {% endfor %}
      {% if not members %}
      <tr><td colspan="7" class="px-5 py-8 text-center text-gray-400">Ingen aktive medlemmer.</td></tr>
      {% endif %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/routes.py dashboard/templates/dashboard/engagement.html
git commit -m "feat: add weekly engagement report page"
```

---

## Task 8: Deploy + Railway env var

**Files:**
- Railway environment variable

- [ ] **Step 1: Set DASHBOARD_PASSWORD on Railway**

```bash
cd "/Users/Sara/Desktop/ranis fil/saki" && railway variables set DASHBOARD_PASSWORD=<vælg-et-stærkt-kodeord>
```

Replace `<vælg-et-stærkt-kodeord>` with Rani's chosen password. Example (DO NOT use this exact one):
```
railway variables set DASHBOARD_PASSWORD=Sakeena2026Rani!
```

- [ ] **Step 2: Push to GitHub and deploy**

```bash
git push origin main && railway up --detach
```

- [ ] **Step 3: Wait for deploy and verify health**

```bash
until curl -sf "https://upbeat-passion-production-a78d.up.railway.app/health" >/dev/null; do sleep 5; done && echo "Klar"
```

Expected: `Klar`

- [ ] **Step 4: Verify login page loads**

```bash
curl -s "https://upbeat-passion-production-a78d.up.railway.app/agents/login" | grep -c "Log ind"
```

Expected: `1`

- [ ] **Step 5: Open in browser and test login**

Open: `https://upbeat-passion-production-a78d.up.railway.app/agents/login`

Test:
1. Log ind med den valgte adgangskode → skal lande på Oversigt
2. Oversigt skal vise status-panel og 4 tal
3. Kontrol-side skal vise mode-dropdown og pause-knap
4. Log ud → skal gå tilbage til login

- [ ] **Step 6: Final commit (if any last-minute fixes)**

```bash
git add -p  # Only if there are remaining changes
git commit -m "fix: post-deploy adjustments"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Login med adgangskode → Task 1 + 2
- [x] Dashboard med live status → Task 3
- [x] Saki-kontrol (mode, pause, broadcast, godkendelser) → Task 4
- [x] Team-administration (tilføj, deaktiver, engagement) → Task 5
- [x] Artikel-review kø (se status, marker færdig) → Task 6
- [x] Engagement-rapport → Task 7
- [x] `/agents/saki/` URL-struktur til fremtidige agenter → Alle tasks

**Placeholder scan:** Ingen TBD, TODO eller "implement later" i planen.

**Type consistency:** `db.session.get(Model, id)` bruges konsekvent. `login_required` dekorator matches korrekt på alle POST-routes.

---

*Plan gemt: 30. april 2026 — Sakeena AI Hub V1*
