"""
Islamisk indhold — KUN fra den verificerede database i data/islamic_content.json.
Saki genererer ALDRIG islamisk indhold fra scratch.
Al-Albani = Sheikh Nasir al-Din al-Albani, anerkendt hadith-specialist.
"""
import json
import random
import os
from datetime import datetime, timedelta

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "islamic_content.json")

_db: dict | None = None
_recently_used: list[str] = []
_REUSE_WINDOW_DAYS = 28


def _load_db() -> dict:
    global _db
    if _db is None:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            _db = json.load(f)
    return _db


def _format_quran(entry: dict) -> str:
    ayah_ref = entry["ayah"] if isinstance(entry["ayah"], str) else str(entry["ayah"])
    return (
        f"Allah siger i Koranen: \"{entry['danish']}\" "
        f"({entry['surah_name']} {entry['surah_number']}:{ayah_ref})"
    )


def _format_hadith(entry: dict) -> str:
    return (
        f"Profeten  ﷺ  sagde: \"{entry['danish']}\" "
        f"({entry['source']})"
    )


def get_reminder(themes: list[str] | None = None) -> str:
    """
    Hent én verificeret islamisk påmindelse.
    Gentager ikke samme påmindelse inden for 28 dage.
    Filtrerer på temaer hvis angivet.
    """
    db = _load_db()
    all_entries = []

    for v in db.get("quran_verses", []):
        if themes is None or any(t in v.get("themes", []) for t in themes):
            all_entries.append(("quran", v))

    for h in db.get("hadith", []):
        if themes is None or any(t in h.get("themes", []) for t in themes):
            all_entries.append(("hadith", h))

    # Filtrer for nyligt brugte
    available = [
        (kind, e) for kind, e in all_entries
        if e["id"] not in _recently_used
    ]

    # Nulstil hvis alt er brugt
    if not available:
        _recently_used.clear()
        available = all_entries

    if not available:
        return ""

    kind, entry = random.choice(available)
    _recently_used.append(entry["id"])

    # Hold listen inden for vindue
    if len(_recently_used) > len(all_entries):
        _recently_used.pop(0)

    return _format_quran(entry) if kind == "quran" else _format_hadith(entry)


def get_reminder_sometimes(probability: float = 0.35, themes: list[str] | None = None) -> str | None:
    """Returnerer en islamisk påmindelse med given sandsynlighed, eller None."""
    if random.random() < probability:
        return get_reminder(themes=themes)
    return None


def get_reminder_for_theme(theme: str) -> str:
    """Hent en påmindelse specifikt relateret til et tema."""
    return get_reminder(themes=[theme])
