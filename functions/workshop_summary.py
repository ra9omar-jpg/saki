"""Functions 7 & 12: Workshop summary — from structured data or raw media (audio/image/text)."""
import json
import logging
import base64
from datetime import datetime, date
import anthropic
from database.db import db
from database.models import WorkshopSession, MarketingTaskRecord, TeamMember, MediaWorkshopDraft
from ai.message_generator import generate_rani_dm, generate_group_message
from functions.group_config import labels_to_codes, code_to_whatsapp_id, code_to_label
import integrations.whatsapp as wa
from config import config

logger = logging.getLogger(__name__)
_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_SUMMARY_SYSTEM = (
    "Du er Saki, AI-assistent for Sakeena. Lav et kort workshop-referat baseret på det du modtager.\n"
    "Inkluder:\n"
    "- Vigtigste emner diskuteret\n"
    "- Beslutninger truffet\n"
    "- Action items med ansvarlig person\n"
    "- Næste skridt\n"
    "Skriv på dansk. Maksimalt 200 ord. Ingen emojis."
)


# ── Function 7: Structured workshop summary (from meeting data) ─────────────

def draft_workshop_summary(session_id: int) -> str:
    session = db.session.get(WorkshopSession, session_id)
    if not session:
        raise ValueError(f"WorkshopSession {session_id} not found")

    records = MarketingTaskRecord.query.filter_by(session_id=session_id).all()
    delivered = [r for r in records if r.was_delivered is True]
    not_delivered = [r for r in records if r.was_delivered is False]

    def member_name(r):
        m = db.session.get(TeamMember, r.member_id)
        return m.name if m else "Ukendt"

    data = {
        "Dato": str(session.date),
        "Team": session.team,
        "Fuldført": "\n".join(f"{member_name(r)}: {r.task_description}" for r in delivered) or "Ingen",
        "Ikke fuldført": "\n".join(f"{member_name(r)}: {r.task_description}" for r in not_delivered) or "Ingen",
    }

    context = "Lav et kort workshopoversigt til teamet. Rani godkender det inden det sendes."
    summary_text = generate_group_message(context, data, use_reminder=True)

    session.summary_text = summary_text
    db.session.commit()
    return summary_text


def send_summary_to_rani_for_approval(session_id: int) -> None:
    session = db.session.get(WorkshopSession, session_id)
    if not session or not session.summary_text:
        return
    text = generate_rani_dm(
        f"Bed Rani godkende denne workshopoversigt inden den sendes til teamet:\n\n"
        f"{session.summary_text}\n\nSvar 'godkendt' for at sende den."
    )
    wa.send_to_rani(text)


def handle_rani_approval(session_id: int, platform: str = "whatsapp") -> None:
    session = db.session.get(WorkshopSession, session_id)
    if not session or not session.summary_text:
        return

    if platform == "whatsapp":
        if session.team == "marketing":
            wa.send_to_marketing_group(session.summary_text)
        elif session.team == "rd":
            wa.send_to_rd_group(session.summary_text)
        else:
            wa.send_to_marketing_group(session.summary_text)
            wa.send_to_rd_group(session.summary_text)
    else:
        import integrations.teams as teams
        if session.team == "marketing":
            teams.send_to_marketing_channel(session.summary_text)
        elif session.team == "rd":
            teams.send_to_rd_channel(session.summary_text)
        else:
            teams.send_to_marketing_channel(session.summary_text)
            teams.send_to_rd_channel(session.summary_text)

    session.summary_approved = True
    session.is_completed = True
    db.session.commit()


# ── Function 12: Media-based workshop summary (audio / image / text) ────────

def handle_rani_media(media_type: str, media_id: str, caption: str = "") -> None:
    """
    Called when Rani sends audio, image, or a document to Saki.
    Processes it and accumulates material in the pending MediaWorkshopDraft.
    When processing is done, sends summary to Rani and asks which group.
    """
    extracted_text = ""

    try:
        if media_type == "audio":
            extracted_text = _transcribe_audio(media_id)
        elif media_type == "image":
            extracted_text = _extract_from_image(media_id, caption)
        elif media_type == "document":
            extracted_text = caption or "(dokument uden tekst)"
        else:
            return
    except Exception as e:
        logger.error("Media-behandling fejlede (%s): %s", media_type, e)
        wa.send_to_rani(f"Kunne ikke behandle {media_type}-filen. Prøv igen eller send som tekst. Saki")
        return

    if not extracted_text:
        wa.send_to_rani("Ingen tekst fundet i filen. Send indholdet som tekstbesked. Saki")
        return

    # Find or create an open draft (accumulate multiple files)
    draft = MediaWorkshopDraft.query.filter_by(status="awaiting_group_selection").order_by(
        MediaWorkshopDraft.created_at.desc()
    ).first()

    if draft and (datetime.utcnow() - draft.created_at).total_seconds() < 3600:
        materials = json.loads(draft.raw_materials_json or "[]")
        materials.append(extracted_text)
        draft.raw_materials_json = json.dumps(materials)
    else:
        draft = MediaWorkshopDraft(raw_materials_json=json.dumps([extracted_text]))
        db.session.add(draft)

    db.session.flush()

    # Generate summary
    combined = "\n\n---\n\n".join(json.loads(draft.raw_materials_json))
    summary = _generate_summary(combined)
    draft.summary_text = summary
    db.session.commit()

    wa.send_to_rani(
        f"Her er mit referat:\n\n{summary}\n\n"
        f"Hvilken gruppe skal dette sendes til? "
        f"(Marketing, R&D, Eksperter, Lærere — eller flere ad gangen) Saki"
    )


def handle_rani_group_selection(text: str) -> bool:
    """
    Check if Rani is replying with group selection for a pending MediaWorkshopDraft.
    Returns True if a draft was found and handled.
    """
    draft = MediaWorkshopDraft.query.filter_by(status="awaiting_group_selection").order_by(
        MediaWorkshopDraft.created_at.desc()
    ).first()

    if not draft:
        return False

    codes = labels_to_codes(text)
    if not codes:
        return False

    sent_to = []
    for code in codes:
        group_id = code_to_whatsapp_id(code)
        if group_id:
            wa.send_to_group(group_id, draft.summary_text)
            sent_to.append(code_to_label(code))

    if sent_to:
        draft.status = "sent"
        draft.selected_groups_json = json.dumps(codes)
        db.session.commit()
        wa.send_to_rani(f"Sendt til: {', '.join(sent_to)}. Saki")
        return True

    return False


def _transcribe_audio(media_id: str) -> str:
    if not config.WHISPER_API_KEY:
        return "(Whisper API ikke konfigureret — transskription ikke mulig)"
    try:
        import openai
        audio_bytes = wa.download_media(media_id)
        client = openai.OpenAI(api_key=config.WHISPER_API_KEY)
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.ogg", audio_bytes, "audio/ogg"),
            language="da",
        )
        return transcript.text
    except Exception as e:
        logger.error("Whisper-transskription fejlede: %s", e)
        raise


def _extract_from_image(media_id: str, caption: str = "") -> str:
    image_bytes = wa.download_media(media_id)
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    prompt = (
        "Dette er et billede fra et møde (whiteboard, noter eller lignende). "
        "Udtræk al tekst og punkter du kan se. Oversæt til dansk hvis nødvendigt."
    )
    if caption:
        prompt += f"\n\nRani's kommentar: {caption}"
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return response.content[0].text.strip()


def _generate_summary(combined_text: str) -> str:
    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=_SUMMARY_SYSTEM,
            messages=[{"role": "user", "content": combined_text}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error("_generate_summary fejlede: %s", e)
        return combined_text[:800]
