"""
Saki introducerer sig kun når nogen tagger den og beder om en introduktion.
Saki tier stille når den tilføjes til en gruppe.
"""
import logging
from config import config

logger = logging.getLogger(__name__)

_INTRO_TRIGGERS = (
    "hvem er du", "who are you",
    "introducer dig", "introduce yourself",
    "hvad er du", "fortæl om dig selv",
    "hvad kan du", "what can you do",
    "hvad laver du",
    "præsenter dig",
)

_SAKI_MENTIONS = (
    "saki",
    f"@{config.WHATSAPP_PHONE_NUMBER.replace('+', '')}",
)


def is_introduction_request(text: str) -> bool:
    """
    Returnerer True hvis beskeden tagger Saki OG beder om en introduktion.
    Kræver BEGGE dele — Saki svarer ikke på generelle spørgsmål i gruppen.
    """
    text_lower = text.lower()
    saki_mentioned = any(mention in text_lower for mention in _SAKI_MENTIONS)
    if not saki_mentioned:
        return False
    return any(trigger in text_lower for trigger in _INTRO_TRIGGERS)


def generate_introduction(group_id: str = "") -> str:
    """
    Genererer en islamisk introduktion til Saki.
    Bruger én verificeret islamisk påmindelse fra databasen.
    """
    from ai.islamic_reminders import get_reminder
    reminder = get_reminder(themes=["excellence", "work", "sincerity"])

    # Beskriv hvad Saki kan i denne gruppe
    group_capabilities = _group_capabilities(group_id)

    lines = [
        "Assalamu alaykum wa rahmatullahi wa barakatuh.",
        "",
        "Jeg hedder Saki og er en AI-assistent bygget til at hjælpe med at koordinere "
        "Sakeenas frivillige teams. Jeg er ikke et menneske — jeg er et digitalt værktøj "
        "der arbejder på vegne af Rani.",
        "",
        f"Hvad jeg kan hjælpe med her:{group_capabilities}",
        "",
    ]

    if reminder:
        lines.append(reminder)
        lines.append("")

    lines.append("Saki")
    return "\n".join(lines)


def _group_capabilities(group_id: str) -> str:
    """Returner en kort liste over hvad Saki gør i denne specifikke gruppe."""
    from config import config

    if group_id in (config.WHATSAPP_GROUP_RD, config.TEAMS_CHANNEL_RD):
        return (
            "\n- Sende ugentlige statusopdateringer om opgaver\n"
            "- Rykke for svar\n"
            "- Lave en to-do liste fra en samtale (skriv 'Saki, lav en to do')\n"
            "- Besvare spørgsmål om deadlines og opgaver"
        )
    elif group_id in (config.WHATSAPP_GROUP_MARKETING, config.TEAMS_CHANNEL_MARKETING):
        return (
            "\n- Tracke opgaver fra åbnings- og afslutningsmøder\n"
            "- Sende ugentlige workshop-polls\n"
            "- Lave en to-do liste fra en samtale (skriv 'Saki, lav en to do')\n"
            "- Besvare spørgsmål om deadlines og kampagner"
        )
    elif group_id == config.WHATSAPP_GROUP_EXPERTISE_REVIEW:
        return (
            "\n- Sende ugentlige lister over artikler der venter på review\n"
            "- Sende private beskeder til reviewere med links og deadlines\n"
            "- Rykke for svar inden deadline"
        )
    elif group_id == config.WHATSAPP_GROUP_TEACHERS:
        return (
            "\n- Sende påmindelser om kurser\n"
            "- Holde styr på undervisningsplan og materiale\n"
            "- Sende opfølgning efter kurser"
        )
    else:
        return (
            "\n- Holde styr på opgaver og deadlines\n"
            "- Rykke for svar\n"
            "- Lave en to-do liste fra en samtale (skriv 'Saki, lav en to do')"
        )
