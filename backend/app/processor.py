import re

CATEGORIES = [
    "Action Required",
    "Meeting or Event",
    "Personal Information",
    "General Information",
    "Promotional",
    "Sensitive Information",
]

DATE_RE = re.compile(r"\b(?:20\d{2})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b")
TIME_RE = re.compile(
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b(?:1[0-2]|0?[1-9])\s?(?:AM|PM|am|pm)\b"
)

# These rules are deliberately conservative. They only extract information
# explicitly present in the message; otherwise they return None.
ACTION_WORDS = [
    "please", "can you", "could you", "need you to", "don't forget",
    "deadline", "submit", "send", "review", "complete", "update",
    "upload", "call", "verify", "renew", "pay", "finish", "prepare",
]

EVENT_WORDS = [
    "meeting", "appointment", "calendar", "scheduled", "please join",
    "stand-up", "dinner", "interview", "session", "demo", "briefing",
    "catch-up", "event",
]

PROMO_WORDS = [
    "discount", "sale", "offer", "coupon", "cashback",
    "free delivery", "premium plan", "reward points", "limited time",
]

PERSONAL_WORDS = [
    "i prefer", "my favourite", "my favorite", "i usually",
    "my t-shirt size", "i drink coffee", "i use dark mode",
]


def process_message(message_id: str, text: str):
    t = text.lower()

    if any(x in t for x in [
        "otp", "one-time password", "password", "pin", "access token",
        "auth token", "authentication token", "api key", "bank account",
        "card number", "identification number", "passport number",
        "home address", "private address"
    ]):
        return {
            "category": "Sensitive Information",
            "confidence": 0.99,
            "reason": "The local privacy layer detected a sensitive-information pattern."
        }

    if any(x in t for x in PROMO_WORDS):
        return {
            "category": "Promotional",
            "confidence": 0.96,
            "reason": "The message promotes an offer, discount, reward, or subscription."
        }

    if any(x in t for x in EVENT_WORDS):
        return {
            "category": "Meeting or Event",
            "confidence": 0.92,
            "reason": "The message explicitly refers to a meeting, appointment, or scheduled event."
        }

    if any(x in t for x in ACTION_WORDS):
        return {
            "category": "Action Required",
            "confidence": 0.90,
            "reason": "The message contains an explicit request, instruction, or follow-up action."
        }

    if any(x in t for x in PERSONAL_WORDS):
        return {
            "category": "Personal Information",
            "confidence": 0.93,
            "reason": "The message explicitly shares a personal preference or profile detail."
        }

    return {
        "category": "General Information",
        "confidence": 0.84,
        "reason": "The message provides information without an explicit action, event, promotional offer, or personal preference."
    }


def _first_match(pattern, text):
    match = pattern.search(text)
    return match.group(0) if match else None


def _explicit_person(text):
    # Only capture names when the message explicitly labels the person.
    patterns = [
        r"\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"\b(?:person|contact|attendee)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def extract_task_event(message_id: str, text: str, category: str):
    if category not in {"Action Required", "Meeting or Event"}:
        return None

    date_value = _first_match(DATE_RE, text)
    time_value = _first_match(TIME_RE, text)
    person = _explicit_person(text)

    lower = text.lower()

    if category == "Meeting or Event":
        if "dinner" in lower:
            title = "Dinner"
        elif "interview" in lower:
            title = "Interview"
        elif "appointment" in lower:
            title = "Appointment"
        elif "meeting" in lower:
            title = "Meeting"
        elif "catch-up" in lower or "catch up" in lower:
            title = "Catch-up"
        elif "calendar" in lower:
            title = "Scheduled event"
        else:
            title = "Event"
        item_type = "event"
    else:
        if "review" in lower:
            title = "Review requested item"
        elif "submit" in lower:
            title = "Submit requested item"
        elif "send" in lower:
            title = "Send requested item"
        elif "upload" in lower:
            title = "Upload requested item"
        elif "complete" in lower:
            title = "Complete requested item"
        elif "call" in lower:
            title = "Call requested contact"
        else:
            title = "Follow-up task"
        item_type = "task"

    # Priority is only high when the message explicitly signals urgency.
    if any(x in lower for x in ["urgent", "critical", "asap", "immediately"]):
        priority = "high"
    elif "important" in lower:
        priority = "medium"
    else:
        priority = "unresolved"

    description = text.strip() if text.strip() else None

    return {
        "item_id": f"{item_type.upper()}_{message_id}",
        "type": item_type,
        "title": title,
        "description": description,
        "date_or_deadline": date_value,
        "time": time_value,
        "person": person,
        "priority": priority,
        "source_message_id": message_id,
    }
