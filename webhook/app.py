"""
Webhook handler for Saki.
WhatsApp: Meta WhatsApp Business Cloud API (GET verification + POST events).
Teams: Microsoft Bot Framework.
"""
import hashlib
import hmac
import logging
from flask import Flask, request, jsonify, abort
from config import config
from database.db import db, init_db

logger = logging.getLogger(__name__)

VALID_TEAMS = {"rd", "marketing"}
VALID_ROLES = {"member", "lead", "admin"}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    init_db(app)

    # ── Health ──────────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "name": "Saki"})

    # ── WhatsApp: webhook verification ───────────────────────────
    @app.route("/webhook/whatsapp", methods=["GET"])
    def whatsapp_verify():
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
            return challenge, 200
        abort(403)

    # ── WhatsApp: incoming messages ──────────────────────────────
    @app.route("/webhook/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        raw_body = request.get_data()
        if not _verify_whatsapp_signature(raw_body, request.headers.get("X-Hub-Signature-256", "")):
            logger.warning("WhatsApp webhook: ugyldig signatur afvist")
            abort(403)

        body = request.get_json(silent=True)
        if not body:
            return jsonify({"status": "ignored"}), 200

        try:
            with app.app_context():
                _process_meta_webhook(body)
        except Exception as e:
            logger.error("Webhook behandlingsfejl: %s", e, exc_info=True)

        return jsonify({"status": "ok"}), 200

    # ── Teams: incoming messages ─────────────────────────────────
    @app.route("/webhook/teams", methods=["POST"])
    def teams_webhook():
        data = request.get_json(silent=True)
        if not data:
            abort(400)
        if data.get("type") != "message":
            return jsonify({"status": "ignored"})

        channel_id = data.get("channelData", {}).get("channel", {}).get("id", "")
        sender_id = data.get("from", {}).get("aadObjectId", "")
        body = data.get("text", "").strip()

        with app.app_context():
            _handle_teams_message(channel_id=channel_id, sender_id=sender_id, body=body)

        return jsonify({"status": "ok"})

    # ── Telegram: incoming messages ──────────────────────────────
    @app.route("/webhook/telegram/<secret>", methods=["POST"])
    def telegram_webhook(secret: str):
        if not config.TELEGRAM_WEBHOOK_SECRET or secret != config.TELEGRAM_WEBHOOK_SECRET:
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

    # ── Workshop API ─────────────────────────────────────────────
    @app.route("/api/workshop/open", methods=["POST"])
    def workshop_open():
        data = request.get_json(silent=True) or {}
        team = data.get("team", "marketing")
        with app.app_context():
            from functions.marketing_tracking import open_workshop_session
            session = open_workshop_session(team)
        return jsonify({"session_id": session.id})

    @app.route("/api/workshop/close", methods=["POST"])
    def workshop_close():
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        delivered_ids = data.get("delivered_member_ids", [])
        with app.app_context():
            from functions.marketing_tracking import record_closing_deliveries
            from functions.workshop_summary import draft_workshop_summary, send_summary_to_rani_for_approval
            record_closing_deliveries(session_id, delivered_ids)
            draft_workshop_summary(session_id)
            send_summary_to_rani_for_approval(session_id)
        return jsonify({"status": "summary_sent_to_rani"})

    @app.route("/api/workshop/approve", methods=["POST"])
    def workshop_approve():
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        platform = data.get("platform", "whatsapp")
        with app.app_context():
            from functions.workshop_summary import handle_rani_approval
            handle_rani_approval(session_id, platform)
        return jsonify({"status": "summary_posted"})

    # ── Members API ──────────────────────────────────────────────
    @app.route("/api/members", methods=["GET"])
    def list_members():
        from database.models import TeamMember
        members = TeamMember.query.filter_by(is_active=True).all()
        return jsonify([
            {"id": m.id, "name": m.name, "team": m.team, "role": m.role}
            for m in members
        ])

    @app.route("/api/members", methods=["POST"])
    def add_member():
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        team = data.get("team", "")
        role = data.get("role", "member")

        if not name:
            return jsonify({"error": "name er påkrævet"}), 400
        if team not in VALID_TEAMS:
            return jsonify({"error": f"team skal være en af: {', '.join(VALID_TEAMS)}"}), 400
        if role not in VALID_ROLES:
            return jsonify({"error": f"role skal være en af: {', '.join(VALID_ROLES)}"}), 400

        from database.models import TeamMember
        member = TeamMember(
            name=name,
            whatsapp_number=data.get("whatsapp_number"),
            teams_user_id=data.get("teams_user_id"),
            telegram_chat_id=data.get("telegram_chat_id"),
            team=team,
            role=role,
        )
        db.session.add(member)
        db.session.commit()
        return jsonify({"id": member.id, "name": member.name})

    from dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app


# ── Meta webhook parser ────────────────────────────────────────────

def _process_meta_webhook(body: dict) -> None:
    if body.get("object") != "whatsapp_business_account":
        return
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            for msg in value.get("messages", []):
                _handle_meta_message(msg, value)


def _handle_meta_message(msg: dict, value: dict) -> None:
    msg_type = msg.get("type", "")

    # Saki tier stille når den tilføjes til en gruppe — system-beskeder ignoreres
    if msg_type == "system":
        return

    from_number = msg.get("from", "")
    msg_id = msg.get("id", "")

    from integrations.whatsapp import mark_as_read
    mark_as_read(msg_id)

    is_rani = from_number == config.RANI_WHATSAPP.replace("whatsapp:", "").replace("+", "").strip()

    if is_rani:
        _handle_rani_message(msg, msg_type)
        return

    # Non-Rani messages
    if msg_type != "text":
        return

    text = msg.get("text", {}).get("body", "").strip()
    if not text:
        return

    group_id = _detect_group(from_number, value)

    from database.models import TeamMember
    member = TeamMember.query.filter_by(whatsapp_number=from_number).first()

    if group_id:
        _handle_group_message(from_number, text, group_id, member)
    else:
        # Direct 1-on-1 message from a team member (Function 18)
        from functions.direct_message import handle_direct_message
        handle_direct_message(from_number, text)


def _handle_rani_message(msg: dict, msg_type: str) -> None:
    """Route all messages from Rani to the correct handler."""
    # Media messages → workshop summary generator (Function 12)
    if msg_type in ("audio", "image", "document"):
        media_data = msg.get(msg_type, {})
        media_id = media_data.get("id", "")
        caption = media_data.get("caption", "") or msg.get("caption", "")
        if media_id:
            from functions.workshop_summary import handle_rani_media
            handle_rani_media(msg_type, media_id, caption)
        return

    if msg_type != "text":
        return

    text = msg.get("text", {}).get("body", "").strip()
    if not text:
        return

    _handle_rani_private_reply(text)


def _handle_group_message(from_number: str, text: str, group_id: str, member) -> None:
    """Handle a message in a group chat (not from Rani)."""
    from functions.control_menu import is_saki_active
    if not is_saki_active():
        return

    from functions.question_monitor import process_incoming_message
    from functions.engagement_tracking import increment_message_count

    process_incoming_message("whatsapp", group_id, from_number, text)
    if member:
        increment_message_count(member.id)

    # Introduktionsanmodning — kun hvis nogen tagger Saki og spørger "hvem er du?"
    from functions.introduction import is_introduction_request, generate_introduction
    if is_introduction_request(text):
        import integrations.whatsapp as wa
        intro = generate_introduction(group_id)
        wa.send_to_group(group_id, intro)
        return

    # "Saki, lav en to do" — anyone in any group can trigger this (Function 14)
    from functions.todo_generator import is_todo_request, generate_todo
    if is_todo_request(text):
        import integrations.whatsapp as wa
        todo = generate_todo("whatsapp", group_id)
        wa.send_to_group(group_id, todo)
        return

    _check_if_status_update(text, member, group_id)
    _check_if_poll_response(text, member, group_id)
    _check_if_article_claim(text, member, group_id)


# ── Rani-håndtering ────────────────────────────────────────────────

def _handle_rani_private_reply(body: str) -> None:
    body_stripped = body.strip()
    body_lower = body_stripped.lower()

    # Quick pause — highest priority (Function 11)
    if body_stripped == config.SAKI_QUICK_PAUSE_TRIGGER:
        from functions.control_menu import handle_quick_pause
        handle_quick_pause()
        return

    # Secret code → show control menu (Function 10)
    if config.SAKI_SECRET_CODE and body_stripped == config.SAKI_SECRET_CODE:
        from functions.control_menu import handle_secret_code
        handle_secret_code()
        return

    # Command mode — Rani is sending a control command (Function 10)
    from functions.control_menu import is_rani_in_command_mode, handle_control_command
    if is_rani_in_command_mode():
        handle_control_command(body_stripped)
        return

    # wake_up always works regardless of pause/shutdown state
    if body_lower == "wake_up":
        from functions.control_menu import _wake_up
        _wake_up()
        return

    # Workshop summary group selection (Function 12)
    from functions.workshop_summary import handle_rani_group_selection
    if handle_rani_group_selection(body_stripped):
        return

    # Workshop approval
    if "godkendt" in body_lower or "godkend" in body_lower:
        from database.models import WorkshopSession
        pending = WorkshopSession.query.filter_by(
            summary_approved=False, is_completed=False
        ).filter(WorkshopSession.summary_text.isnot(None)).order_by(
            WorkshopSession.date.desc()
        ).first()
        if pending:
            from functions.workshop_summary import handle_rani_approval
            handle_rani_approval(pending.id)
        return

    # Time confirmation for a pending scheduled message
    from database.models import RaniConfirmation
    pending_conf = RaniConfirmation.query.filter_by(confirmed_at=None).order_by(
        RaniConfirmation.requested_at.asc()
    ).first()
    if pending_conf:
        from functions.pre_send_confirmation import handle_rani_time_reply
        handle_rani_time_reply(pending_conf.id, body_stripped, pending_conf.pending_message_id or 0)


# ── Teams-håndtering ───────────────────────────────────────────────

def _handle_teams_message(channel_id: str, sender_id: str, body: str) -> None:
    from functions.control_menu import is_saki_active
    if not is_saki_active():
        return

    from database.models import TeamMember
    from functions.question_monitor import process_incoming_message
    from functions.engagement_tracking import increment_message_count

    member = TeamMember.query.filter_by(teams_user_id=sender_id).first()
    process_incoming_message("teams", channel_id, sender_id, body)
    if member:
        increment_message_count(member.id)

    from functions.introduction import is_introduction_request, generate_introduction
    if is_introduction_request(body):
        import integrations.teams as teams_int
        intro = generate_introduction(channel_id)
        teams_int.send_channel_message(channel_id, intro)
        return

    from functions.todo_generator import is_todo_request, generate_todo
    if is_todo_request(body):
        import integrations.teams as teams_int
        todo = generate_todo("teams", channel_id)
        teams_int.send_channel_message(channel_id, todo)
        return

    _check_if_status_update(body, member, channel_id)
    _check_if_poll_response(body, member, channel_id)
    _check_if_article_claim(body, member, channel_id)


# ── Besked-type detektorer ────────────────────────────────────────

def _check_if_status_update(body: str, member, group_id: str) -> None:
    if not member:
        return
    _rd_groups = (config.WHATSAPP_GROUP_RD, config.TEAMS_CHANNEL_RD, config.TELEGRAM_GROUP_RD)
    if group_id not in _rd_groups:
        return
    keywords = ("færdig", "halvvejs", "ikke startet", "blokeret", "done", "halfway", "blocked")
    if any(kw in body.lower() for kw in keywords):
        from functions.monday_status import record_status_update
        from functions.engagement_tracking import update_engagement_status_response
        record_status_update(member.id, None, body)
        update_engagement_status_response(member.id)


def _check_if_poll_response(body: str, member, group_id: str) -> None:
    if not member:
        return
    from functions.weekly_polls import get_active_poll, record_poll_response
    from functions.engagement_tracking import update_engagement_poll_response
    poll = get_active_poll()
    if poll and not poll.is_closed:
        time_keywords = ("mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag",
                         "kl.", "kan", "ikke", "alle", "passer")
        if any(kw in body.lower() for kw in time_keywords):
            record_poll_response(poll.id, member.id, body)
            update_engagement_poll_response(member.id)


def _check_if_article_claim(body: str, member, group_id: str) -> None:
    if not member:
        return
    _expertise_groups = (config.WHATSAPP_GROUP_EXPERTISE_REVIEW, config.TEAMS_CHANNEL_EXPERTISE_REVIEW, config.TELEGRAM_GROUP_EXPERTISE_REVIEW)
    if group_id not in _expertise_groups:
        return
    import re
    match = re.search(r'\b(\d+)\b', body)
    if match:
        from functions.article_review import handle_article_claim
        handle_article_claim(member.id, int(match.group(1)))


# ── Group detection ───────────────────────────────────────────────

def _detect_group(from_number: str, value: dict) -> str | None:
    messages = value.get("messages", [])
    for m in messages:
        if m.get("from") == from_number:
            recipient = m.get("context", {}).get("recipient_id", "")
            if recipient:
                return recipient

    from database.models import TeamMember
    member = TeamMember.query.filter_by(whatsapp_number=from_number).first()
    if member:
        group_map = {
            "marketing": config.WHATSAPP_GROUP_MARKETING,
            "rd": config.WHATSAPP_GROUP_RD,
        }
        return group_map.get(member.team)
    return None


# ── Telegram webhook parser ───────────────────────────────────────

def _process_telegram_webhook(body: dict) -> None:
    message = body.get("message")
    if not message:
        logger.error("DEBUG Telegram: ingen message i body: %s", body)
        return
    logger.error("DEBUG Telegram: besked modtaget fra chat_id=%s type=%s tekst=%r",
                 message.get("chat", {}).get("id"), message.get("chat", {}).get("type"),
                 message.get("text", "")[:50])
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

    elif chat_type == "private":
        _handle_telegram_private_message(sender_id, text, sender)


def _handle_telegram_private_message(sender_id: str, text: str, sender: dict) -> None:
    """Handle a private DM to the bot from a non-Rani user on Telegram (Function 18)."""
    from database.models import TeamMember, Task
    from ai.message_generator import generate_message
    from functions.direct_message import _is_admin_question, _needs_rani
    import integrations.telegram as tg

    logger.info("DM modtaget fra sender_id=%s first_name=%s tekst=%r", sender_id, sender.get("first_name"), text)

    member = TeamMember.query.filter_by(telegram_chat_id=sender_id).first()

    context = ""
    if member:
        tasks = Task.query.filter_by(assigned_to_id=member.id, status="in_progress").limit(3).all()
        context = f"\nMedlem: {member.name} ({member.team}-team)"
        if tasks:
            context += f"\nAktive opgaver: {', '.join(t.title for t in tasks)}"

    _PRIVATE_RULES = (
        "Dette er en privat besked fra et teammedlem. "
        "Besvar kun faktuelle spørgsmål om deadlines, opgaver og workshop-tider. "
        "Afslør ALDRIG admin-funktioner, kontrol-kommandoer eller indstillinger. "
        "Træf ingen beslutninger."
    )

    if _is_admin_question(text):
        reply = "Det er ikke noget jeg kan hjælpe med her. Saki"
    elif _needs_rani(text):
        sender_name = member.name if member else sender.get("first_name", sender_id)
        tg.send_to_rani(f"{sender_name} skriver: \"{text[:200]}\". Saki")
        reply = "Det skal Rani tage stilling til. Jeg giver besked videre. Saki"
    else:
        prompt = f"{_PRIVATE_RULES}\n\nMedlem skriver privat:{context}\n\nBesked: {text}"
        reply = generate_message(prompt, include_reminder=False)

    tg.send_message(sender_id, reply)


# ── Signature verification ────────────────────────────────────────

def _verify_whatsapp_signature(raw_body: bytes, signature_header: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        config.WHATSAPP_APP_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)
