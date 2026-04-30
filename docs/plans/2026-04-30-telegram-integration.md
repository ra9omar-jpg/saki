# Saki — Telegram Integration Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Telegram as a third messaging platform so Rani can test all Saki functionality through Telegram groups immediately, while WhatsApp Meta business verification is pending. When WhatsApp is approved later, both run simultaneously without re-engineering.

**Architecture:** Mirror the existing WhatsApp/Teams two-platform pattern exactly. One new integration file, one new webhook route, small edits to existing files. Zero changes to business logic inside `functions/`.

**Tech stack addition:** Raw `requests` to `api.telegram.org` — no new library. Same pattern as `integrations/whatsapp.py`.

---

## File map

| Action | Path | Notes |
|--------|------|-------|
| CREATE | `integrations/telegram.py` | Mirror of `whatsapp.py` — send_message, send_to_group, send_to_rani |
| MODIFY | `config.py` | Add TELEGRAM_BOT_TOKEN, RANI_TELEGRAM_ID, group IDs |
| MODIFY | `webhook/app.py` | Add `/webhook/telegram/<secret>` route + parsers |
| CREATE | `functions/mode_router_telegram.py` | Test/shadow/live routing for Telegram |
| MODIFY | `functions/group_config.py` | Add _TELEGRAM_GROUPS map + lookup functions |
| MODIFY | `functions/question_monitor.py` | Add telegram branch to _send_to_group + _group_label |
| MODIFY | `database/models.py` | Add telegram_chat_id to TeamMember, sender_telegram_id to IncomingMessage |
| MODIFY | `.env.example` | Document all new Telegram env vars |

---

## Task 1 — Add Telegram config vars

**File:** `config.py` — add after `RANI_TEAMS_USER_ID`:

```python
# Telegram Bot API
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

# Telegram Group IDs (negative integers as strings)
TELEGRAM_GROUP_MARKETING = os.environ.get("TELEGRAM_GROUP_MARKETING", "")
TELEGRAM_GROUP_RD = os.environ.get("TELEGRAM_GROUP_RD", "")
TELEGRAM_GROUP_EXPERTISE_REVIEW = os.environ.get("TELEGRAM_GROUP_EXPERTISE_REVIEW", "")
TELEGRAM_GROUP_TEACHERS = os.environ.get("TELEGRAM_GROUP_TEACHERS", "")
TELEGRAM_GROUP_COMMUNITY = os.environ.get("TELEGRAM_GROUP_COMMUNITY", "")

# Rani's Telegram user ID (integer as string, e.g. "123456789")
RANI_TELEGRAM_ID = os.environ.get("RANI_TELEGRAM_ID", "")

# Test Telegram groups
TEST_TELEGRAM_GROUP_RD = os.environ.get("TEST_TELEGRAM_GROUP_RD", "")
TEST_TELEGRAM_GROUP_MARKETING = os.environ.get("TEST_TELEGRAM_GROUP_MARKETING", "")
TEST_TELEGRAM_GROUP_TEACHERS = os.environ.get("TEST_TELEGRAM_GROUP_TEACHERS", "")
TEST_TELEGRAM_GROUP_EXPERTISE = os.environ.get("TEST_TELEGRAM_GROUP_EXPERTISE", "")
```

---

## Task 2 — Create `integrations/telegram.py`

**File:** `integrations/telegram.py` (ny fil)

```python
"""
Telegram Bot API integration for Saki.
Direct HTTP calls to api.telegram.org — same pattern as integrations/whatsapp.py.
"""
import logging
import requests
from config import config

logger = logging.getLogger(__name__)
_BASE_URL = "https://api.telegram.org/bot{token}"


def _api_url(method: str) -> str:
    return f"{_BASE_URL.format(token=config.TELEGRAM_BOT_TOKEN)}/{method}"


def send_message(chat_id: str, text: str) -> str:
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — message not sent")
        return ""
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(_api_url("sendMessage"), json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return str(data.get("result", {}).get("message_id", ""))
    except requests.HTTPError as e:
        logger.error("Telegram sendMessage HTTP error: %s — %s", e, e.response.text if e.response else "")
        raise
    except Exception as e:
        logger.error("Telegram sendMessage error: %s", e)
        raise


def send_to_group(group_id: str, text: str) -> str:
    from functions.mode_router_telegram import route_group_message_telegram
    return route_group_message_telegram(group_id, text)


def _send_to_group_raw(group_id: str, text: str) -> str:
    return send_message(group_id, text)


def send_to_rani(text: str) -> str:
    if not config.RANI_TELEGRAM_ID:
        logger.warning("RANI_TELEGRAM_ID not set")
        return ""
    return send_message(config.RANI_TELEGRAM_ID, text)


def send_to_member(telegram_chat_id: str, text: str) -> str:
    return send_message(telegram_chat_id, text)


def send_to_marketing_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_MARKETING, text)


def send_to_rd_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_RD, text)


def send_to_expertise_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_EXPERTISE_REVIEW, text)


def send_to_teachers_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_TEACHERS, text)


def send_to_community_group(text: str) -> str:
    return send_to_group(config.TELEGRAM_GROUP_COMMUNITY, text)
```

---

## Task 3 — Database models

**File:** `database/models.py`

I `TeamMember` — tilføj efter `teams_user_id`:
```python
telegram_chat_id = db.Column(db.String(30), unique=True)
```

I `IncomingMessage` — tilføj efter `sender_teams_id`:
```python
sender_telegram_id = db.Column(db.String(30))
```

I `/api/members` POST i `webhook/app.py` — tilføj til member-oprettelse:
```python
telegram_chat_id=data.get("telegram_chat_id"),
```

---

## Task 4 — Create `functions/mode_router_telegram.py`

**File:** `functions/mode_router_telegram.py` (ny fil)

```python
"""
Telegram mode routing: test / shadow / live.
Mirrors functions/mode_router.py for Telegram group IDs.
"""
import logging
from config import config

logger = logging.getLogger(__name__)


def route_group_message_telegram(group_id: str, body: str) -> str:
    from functions.mode_router import get_current_mode
    mode = get_current_mode()

    if mode == "test":
        if _is_test_group(group_id):
            return _send_direct(group_id, body)
        logger.info("mode=test: BLOCKED Telegram send to real group %s", group_id)
        return ""

    elif mode == "shadow":
        _send_shadow_draft(group_id, body)
        return ""

    else:  # live
        return _send_direct(group_id, body)


def _is_test_group(group_id: str) -> bool:
    test_groups = [
        config.TEST_TELEGRAM_GROUP_RD,
        config.TEST_TELEGRAM_GROUP_MARKETING,
        config.TEST_TELEGRAM_GROUP_TEACHERS,
        config.TEST_TELEGRAM_GROUP_EXPERTISE,
    ]
    return group_id in [g for g in test_groups if g]


def _send_shadow_draft(group_id: str, body: str) -> None:
    from functions.group_config import telegram_id_to_code, code_to_label
    import integrations.whatsapp as wa
    code = telegram_id_to_code(group_id)
    group_label = code_to_label(code) if code else group_id
    wa.send_to_rani(
        f"[SHADOW/TELEGRAM – {group_label}]\n"
        f"Saki har lavet denne besked. Send den manuelt:\n\n{body}"
    )


def _send_direct(group_id: str, body: str) -> str:
    from integrations.telegram import _send_to_group_raw
    return _send_to_group_raw(group_id, body)
```

---

## Task 5 — Extend `functions/group_config.py`

Tilføj `_TELEGRAM_GROUPS` map og to nye funktioner:

```python
_TELEGRAM_GROUPS = {
    "GROUP_RD_MAIN":           lambda: config.TELEGRAM_GROUP_RD,
    "GROUP_MARKETING_CORE":    lambda: config.TELEGRAM_GROUP_MARKETING,
    "GROUP_TEACHERS":          lambda: config.TELEGRAM_GROUP_TEACHERS,
    "GROUP_EXPERTISE_REVIEW":  lambda: config.TELEGRAM_GROUP_EXPERTISE_REVIEW,
    "GROUP_COMMUNITY":         lambda: config.TELEGRAM_GROUP_COMMUNITY,
}


def code_to_telegram_id(code: str) -> str | None:
    fn = _TELEGRAM_GROUPS.get(code)
    try:
        return fn() if fn else None
    except Exception:
        return None


def telegram_id_to_code(telegram_id: str) -> str | None:
    for code, fn in _TELEGRAM_GROUPS.items():
        try:
            if fn() == telegram_id:
                return code
        except Exception:
            pass
    return None
```

---

## Task 6 — Add `/webhook/telegram` route to `webhook/app.py`

**6a — Route inde i `create_app()`** (efter Teams-route):

```python
@app.route("/webhook/telegram/<secret>", methods=["POST"])
def telegram_webhook(secret: str):
    if secret != config.TELEGRAM_WEBHOOK_SECRET:
        abort(403)
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "ignored"}), 200
    try:
        with app.app_context():
            _process_telegram_webhook(body)
    except Exception as e:
        logger.error("Telegram webhook behandlingsfejl: %s", e, exc_info=True)
    return jsonify({"status": "ok"}), 200
```

**6b — Parser-funktioner** (bund af filen):

```python
def _process_telegram_webhook(body: dict) -> None:
    message = body.get("message")
    if not message:
        return
    _handle_telegram_message(message)


def _handle_telegram_message(msg: dict) -> None:
    sender = msg.get("from", {})
    chat = msg.get("chat", {})
    text = msg.get("text", "").strip()
    sender_id = str(sender.get("id", ""))
    chat_id = str(chat.get("id", ""))
    chat_type = chat.get("type", "")

    if not text or not sender_id:
        return

    is_rani = sender_id == config.RANI_TELEGRAM_ID.strip()

    if is_rani and chat_type == "private":
        _handle_rani_private_reply(text)
        return

    if chat_type in ("group", "supergroup"):
        from functions.control_menu import is_saki_active
        if not is_saki_active():
            return

        from database.models import TeamMember
        from functions.question_monitor import process_incoming_message
        from functions.engagement_tracking import increment_message_count

        member = TeamMember.query.filter_by(telegram_chat_id=sender_id).first()
        process_incoming_message("telegram", chat_id, sender_id, text)
        if member:
            increment_message_count(member.id)

        from functions.introduction import is_introduction_request, generate_introduction
        if is_introduction_request(text):
            import integrations.telegram as tg
            tg.send_to_group(chat_id, generate_introduction(chat_id))
            return

        from functions.todo_generator import is_todo_request, generate_todo
        if is_todo_request(text):
            import integrations.telegram as tg
            tg.send_to_group(chat_id, generate_todo("telegram", chat_id))
            return

        _check_if_status_update(text, member, chat_id)
        _check_if_poll_response(text, member, chat_id)
        _check_if_article_claim(text, member, chat_id)
```

**6c — Udvid gruppe-guards** i `_check_if_status_update` og `_check_if_article_claim`:

```python
# _check_if_status_update:
_rd_groups = (config.WHATSAPP_GROUP_RD, config.TEAMS_CHANNEL_RD, config.TELEGRAM_GROUP_RD)
if group_id not in _rd_groups:
    return

# _check_if_article_claim:
_expertise_groups = (config.WHATSAPP_GROUP_EXPERTISE_REVIEW, config.TEAMS_CHANNEL_EXPERTISE_REVIEW, config.TELEGRAM_GROUP_EXPERTISE_REVIEW)
if group_id not in _expertise_groups:
    return
```

---

## Task 7 — Extend `functions/question_monitor.py`

Tilføj `telegram`-gren i `process_incoming_message`:
```python
elif platform == "telegram":
    msg.sender_telegram_id = sender_identifier
```

Tilføj `telegram`-gren i `_send_to_group`:
```python
elif platform == "telegram":
    import integrations.telegram as tg
    tg.send_to_group(group_id, text)
```

Tilføj Telegram-gruppe-labels i `_group_label`:
```python
config.TELEGRAM_GROUP_MARKETING: "Telegram Marketing-gruppen",
config.TELEGRAM_GROUP_RD: "Telegram R&D-gruppen",
config.TELEGRAM_GROUP_EXPERTISE_REVIEW: "Telegram Ekspertreviewgruppen",
config.TELEGRAM_GROUP_TEACHERS: "Telegram Lærere-gruppen",
```

---

## Task 8 — Update `.env.example`

```
# === TELEGRAM BOT API ===
# Opret en bot via @BotFather på Telegram. Du får en token som:
# 1234567890:ABCdefGHIjklMNOpqrSTUVwxyz
TELEGRAM_BOT_TOKEN=

# Hemmeligt suffiks til webhook-URL — vælg en lang tilfældig streng
TELEGRAM_WEBHOOK_SECRET=

# === TELEGRAM GRUPPE-IDS ===
# Tilføj Saki-botten til gruppen og send /start for at se gruppe-ID i logs
# Grupper bruger negative tal, f.eks. -1001234567890
# OBS: Botten skal være admin i gruppen for at modtage alle beskeder
TELEGRAM_GROUP_MARKETING=
TELEGRAM_GROUP_RD=
TELEGRAM_GROUP_EXPERTISE_REVIEW=
TELEGRAM_GROUP_TEACHERS=
TELEGRAM_GROUP_COMMUNITY=

# Ranis personlige Telegram bruger-ID (positivt tal)
# Find det ved at sende en besked til @userinfobot på Telegram
RANI_TELEGRAM_ID=

# === TEST TELEGRAM-GRUPPER ===
TEST_TELEGRAM_GROUP_RD=
TEST_TELEGRAM_GROUP_MARKETING=
TEST_TELEGRAM_GROUP_TEACHERS=
TEST_TELEGRAM_GROUP_EXPERTISE=
```

---

## Task 9 — Database migration

**Lokal SQLite (reset er OK i dev):**
```bash
rm "/Users/Sara/Desktop/ranis fil/saki/saki.db"
python -c "from webhook.app import create_app; app = create_app(); print('DB reset OK')"
```

**Railway PostgreSQL (kør én gang efter deploy):**
```sql
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(30) UNIQUE;
ALTER TABLE incoming_messages ADD COLUMN IF NOT EXISTS sender_telegram_id VARCHAR(30);
```

---

## Task 10 — Registrer webhook hos Telegram

Kør dette efter deploy til Railway (én gang):

```bash
curl -X POST \
  "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<railway-domain>/webhook/telegram/<TELEGRAM_WEBHOOK_SECRET>",
    "allowed_updates": ["message"]
  }'
```

Verificer:
```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

---

## Task 11 — Smoke test checklist

- [ ] Send besked i Telegram-testgruppe → Railway logs viser `_handle_telegram_message`
- [ ] Send "Hvem er du?" → Saki svarer med introduktion
- [ ] Send "Saki, lav en to do" → Saki svarer
- [ ] Send "Færdig med alt" i R&D-gruppe → ny række i `status_updates` DB
- [ ] `SAKI_MODE=test` → Saki sender KUN til testgrupper, ikke rigtige
- [ ] `SAKI_MODE=shadow` → Rani modtager `[SHADOW/TELEGRAM]` besked på WhatsApp
- [ ] POST til `/webhook/telegram/wrongsecret` → 403
- [ ] `TELEGRAM_BOT_TOKEN` mangler → app crasher ikke, logger warning

---

## Rækkefølge

```
Task 1 (config) → Task 2 (telegram.py) → Task 4 (mode_router_telegram)
Task 1 → Task 5 (group_config)
Task 3 (models) → Task 9 (migration)
Tasks 6+7 (webhook + question_monitor) — afhænger af Task 1+2+5
Task 8 (.env.example) — uafhængig
Task 10 (webhook registration) — kræver deploy
Task 11 (smoke tests) — kræver Task 10
```

---

## Vigtige faldgruber

- **Gruppe-ID som string:** Telegram grupper er negative integers (`-1001234567890`). Gem og sammenlign ALTID som `str` — ellers fejler lookups stille.
- **parse_mode:** Udelad `parse_mode` i `send_message` payload — Saki-beskeder er naturligt sprog, ikke HTML, og uescaped `<>` vil crashe Telegram API.
- **Bot skal være admin:** Telegram-bots der kun er almindelige members modtager ikke alle beskeder. Rani skal gøre Saki-botten til admin i alle grupper.
- **Rani-DMs via WhatsApp:** `_handle_rani_private_reply` sender acknowledge-beskeder tilbage via WhatsApp. Det er intentionelt — admin-kanalen forbliver på WhatsApp.
