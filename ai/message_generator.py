import logging
import anthropic
from config import config
from ai.islamic_reminders import get_reminder_sometimes

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_FALLBACK_MESSAGE = "Tak for din besked. Vi vender tilbage hurtigst muligt.\n\nSaki"

SAKI_SYSTEM_PROMPT = """Du er Saki, en AI-assistent for den islamiske danske organisation Sakeena. Du hjælper med at koordinere frivillige i Marketing-teamet og R&D-teamet (Research & Development).

IDENTITET:
- Dit navn er Saki
- Du er en AI-assistent og identificerer dig altid som det, hvis nogen spørger
- Du kommunikerer KUN på dansk
- Din tone er varm, professionel og islamisk

BESKEDSREGLER (SKAL OVERHOLDES):
- Maksimalt 2-3 sætninger per besked
- Aldrig emojis
- Altid afslut med "Saki" på en ny linje
- Variere ordlyden i hver besked — aldrig to identiske beskeder
- Lejlighedsvis islamisk påmindelse fra Koranen eller autentisk Hadith (ikke i hver besked)
- Direkte og konkret — ingen unødvendige ord

DU MODTAGER:
En instruktion om, hvad beskeden skal indeholde og eventuelle data (navne, opgavetitler, links osv.)

DU RETURNERER:
Kun selve beskeden, klar til at sende. Intet andet."""


def generate_message(task_description: str, include_reminder: bool = None, reminder_text: str = None) -> str:
    reminder_instruction = ""
    if include_reminder is True and reminder_text:
        reminder_instruction = f"\n\nInkluder denne islamiske påmindelse naturligt i beskeden: {reminder_text}"
    elif include_reminder is False:
        reminder_instruction = "\n\nInkluder IKKE en islamisk påmindelse i denne besked."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=[
                {
                    "type": "text",
                    "text": SAKI_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": task_description + reminder_instruction,
                }
            ],
        )
        return response.content[0].text.strip()
    except anthropic.RateLimitError:
        logger.warning("Claude rate limit nået — bruger fallback-besked")
        return _FALLBACK_MESSAGE
    except anthropic.APIStatusError as e:
        logger.error("Claude API fejl %s: %s", e.status_code, e.message)
        return _FALLBACK_MESSAGE
    except Exception as e:
        logger.error("Uventet fejl i generate_message: %s", type(e).__name__)
        return _FALLBACK_MESSAGE


def generate_rani_dm(task_description: str) -> str:
    prompt = f"""Skriv en kort privat besked til Rani (organisationsleder) om følgende:
{task_description}

Beskeden skal være direkte og venlig. Afslut med "Saki"."""
    return generate_message(prompt, include_reminder=False)


def generate_group_message(context: str, data: dict = None, use_reminder: bool = False) -> str:
    """
    use_reminder=True  → always include (major scheduled messages only)
    use_reminder=False → never include (default for quick replies, confirmations, etc.)
    use_reminder=None  → 35% chance (kept for backwards compatibility)
    """
    reminder = None
    should_include = use_reminder

    if use_reminder is None:
        if _islamic_reminders_enabled():
            reminder = get_reminder_sometimes(probability=0.35)
            should_include = reminder is not None
        else:
            should_include = False
    elif use_reminder is True and not _islamic_reminders_enabled():
        should_include = False

    if should_include and not reminder:
        reminder = get_reminder_sometimes(probability=1.0)

    data_str = ""
    if data:
        data_str = "\n\nData at bruge i beskeden:\n" + "\n".join(f"- {k}: {v}" for k, v in data.items())

    prompt = f"Skriv en gruppebesked til Sakeenas frivillige om følgende:\n{context}{data_str}"
    return generate_message(prompt, include_reminder=should_include, reminder_text=reminder)


def _islamic_reminders_enabled() -> bool:
    try:
        from database.models import get_saki_state
        return get_saki_state().islamic_reminders_enabled
    except Exception:
        return True


def classify_as_question(message_text: str) -> bool:
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            system="Du afgør om en besked er et spørgsmål der venter på svar. Svar kun 'ja' eller 'nej'.",
            messages=[{"role": "user", "content": f"Er denne besked et ubesvaret spørgsmål?\n\n{message_text}"}],
        )
        return response.content[0].text.strip().lower().startswith("ja")
    except Exception as e:
        logger.error("classify_as_question fejlede: %s", type(e).__name__)
        return False


def identify_relevant_expert(question: str, members: list[dict]) -> str | None:
    if not members:
        return None

    members_str = "\n".join(f"- {m['name']} ({m['role']}, {m['team']})" for m in members)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system="Du identificerer hvem der bedst kan svare på et spørgsmål baseret på rolle og team. Returner kun personens navn, eller 'ingen' hvis ingen er relevant.",
            messages=[
                {
                    "role": "user",
                    "content": f"Spørgsmål: {question}\n\nTilgængelige teammedlemmer:\n{members_str}\n\nHvem bør svare?",
                }
            ],
        )
        result = response.content[0].text.strip()
        return None if result.lower() == "ingen" else result
    except Exception as e:
        logger.error("identify_relevant_expert fejlede: %s", type(e).__name__)
        return None
