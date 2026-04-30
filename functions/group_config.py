"""
Stable internal code names for groups and buckets.
When display names change, only update env vars — code never breaks.
"""
from config import config

_WHATSAPP_GROUPS = {
    "GROUP_RD_MAIN":           lambda: config.WHATSAPP_GROUP_RD,
    "GROUP_MARKETING_CORE":    lambda: config.WHATSAPP_GROUP_MARKETING,
    "GROUP_TEACHERS":          lambda: config.WHATSAPP_GROUP_TEACHERS,
    "GROUP_EXPERTISE_REVIEW":  lambda: config.WHATSAPP_GROUP_EXPERTISE_REVIEW,
    "GROUP_COMMUNITY":         lambda: config.WHATSAPP_GROUP_COMMUNITY,
}

_TEAMS_CHANNELS = {
    "GROUP_RD_MAIN":           lambda: config.TEAMS_CHANNEL_RD,
    "GROUP_MARKETING_CORE":    lambda: config.TEAMS_CHANNEL_MARKETING,
    "GROUP_EXPERTISE_REVIEW":  lambda: config.TEAMS_CHANNEL_EXPERTISE_REVIEW,
    "GROUP_TEACHERS":          lambda: config.TEAMS_CHANNEL_TEACHERS,
}

_TELEGRAM_GROUPS = {
    "GROUP_RD_MAIN":           lambda: config.TELEGRAM_GROUP_RD,
    "GROUP_MARKETING_CORE":    lambda: config.TELEGRAM_GROUP_MARKETING,
    "GROUP_TEACHERS":          lambda: config.TELEGRAM_GROUP_TEACHERS,
    "GROUP_EXPERTISE_REVIEW":  lambda: config.TELEGRAM_GROUP_EXPERTISE_REVIEW,
    "GROUP_COMMUNITY":         lambda: config.TELEGRAM_GROUP_COMMUNITY,
}

_PLANNER_BUCKETS = {
    "BUCKET_TODO":         lambda: config.PLANNER_BUCKET_TODO,
    "BUCKET_IN_PROGRESS":  lambda: config.PLANNER_BUCKET_IN_PROGRESS,
    "BUCKET_READY_REVIEW": lambda: config.PLANNER_BUCKET_READY_FOR_REVIEW,
    "BUCKET_APPROVED":     lambda: config.PLANNER_BUCKET_APPROVED,
    "BUCKET_DONE":         lambda: config.PLANNER_BUCKET_DONE,
}

GROUP_LABELS = {
    "GROUP_RD_MAIN":           "R&D-gruppen",
    "GROUP_MARKETING_CORE":    "Marketing-gruppen",
    "GROUP_TEACHERS":          "Lærere-gruppen",
    "GROUP_EXPERTISE_REVIEW":  "Ekspertise Review-gruppen",
    "GROUP_COMMUNITY":         "Sakeena Community",
}

_ALIASES = {
    "rd": "GROUP_RD_MAIN",
    "r&d": "GROUP_RD_MAIN",
    "rd_team": "GROUP_RD_MAIN",
    "marketing": "GROUP_MARKETING_CORE",
    "lærere": "GROUP_TEACHERS",
    "teachers": "GROUP_TEACHERS",
    "ekspert": "GROUP_EXPERTISE_REVIEW",
    "eksperter": "GROUP_EXPERTISE_REVIEW",
    "expertise": "GROUP_EXPERTISE_REVIEW",
    "community": "GROUP_COMMUNITY",
    "sakeena": "GROUP_COMMUNITY",
}


def label_to_code(label: str) -> str | None:
    label_lower = label.lower().strip()
    if label_lower in _ALIASES:
        return _ALIASES[label_lower]
    for code, lbl in GROUP_LABELS.items():
        if label_lower in lbl.lower():
            return code
    return None


def labels_to_codes(text: str) -> list[str]:
    """Parse multiple group names from a single reply, e.g. 'marketing og rd'."""
    found = []
    text_lower = text.lower()
    if "alle" in text_lower or "all" in text_lower:
        return list(_WHATSAPP_GROUPS.keys())
    for alias, code in _ALIASES.items():
        if alias in text_lower and code not in found:
            found.append(code)
    return found


def code_to_whatsapp_id(code: str) -> str | None:
    fn = _WHATSAPP_GROUPS.get(code)
    try:
        return fn() if fn else None
    except Exception:
        return None


def whatsapp_id_to_code(whatsapp_id: str) -> str | None:
    for code, fn in _WHATSAPP_GROUPS.items():
        try:
            if fn() == whatsapp_id:
                return code
        except Exception:
            pass
    return None


def code_to_label(code: str) -> str:
    return GROUP_LABELS.get(code, code)


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


def bucket_id_for(bucket_code: str) -> str | None:
    fn = _PLANNER_BUCKETS.get(bucket_code)
    try:
        return fn() if fn else None
    except Exception:
        return None
