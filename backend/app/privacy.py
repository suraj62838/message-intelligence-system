import re
from typing import Tuple, List, Dict

# Privacy is applied locally BEFORE any text can be sent to an external model.
# Patterns intentionally favor masking over preserving potentially sensitive values.

PATTERNS = [
    ("one_time_password", re.compile(
        r"(\b(?:OTP|one[- ]time password)\s*(?:is|:|=)\s*)([A-Za-z0-9_-]{4,12})",
        re.I
    )),
    ("password", re.compile(
        r"(\bpassword\s*(?:is|:|=)\s*)([^\s,.;!?]+)",
        re.I
    )),
    ("pin", re.compile(
        r"(\bPIN\s*(?:is|:|=)\s*)([0-9A-Za-z_-]{4,12})",
        re.I
    )),
    ("authentication_token", re.compile(
        r"(\b(?:temporary\s+)?(?:access|auth|authentication|bearer)\s+token\s*(?:is|:|=)\s*)([A-Za-z0-9._~+/=-]{8,})",
        re.I
    )),
    ("api_key", re.compile(
        r"(\b(?:API|secret)\s+key\s*(?:is|:|=)\s*)([A-Za-z0-9._~+/=-]{8,})",
        re.I
    )),
    ("card_number", re.compile(
        r"(\b(?:card|credit card|debit card)\s*(?:number\s*)?(?:is|:|=)\s*)([0-9][0-9 -]{7,24})",
        re.I
    )),
    ("bank_account_number", re.compile(
        r"(\b(?:bank\s+account|account)\s*(?:number\s*)?(?:is|:|=)\s*)([0-9][0-9 -]{5,24})",
        re.I
    )),
    ("identification_number", re.compile(
        r"(\b(?:identification|ID|passport|national ID)\s*(?:number\s*)?(?:is|:|=)\s*)([A-Za-z0-9-]{5,24})",
        re.I
    )),
    ("email_address", re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.I
    )),
    ("phone_number", re.compile(
        r"(\b(?:phone|mobile|contact|call)\s*(?:number|me)?\s*(?:is|at|on|:)\s*)(\+?[0-9][0-9 ()-]{7,}[0-9])",
        re.I
    )),
    ("private_address", re.compile(
        r"(\b(?:home|private|residential)\s+address\s*(?:is|:|=)\s*)(.+?)(?=$|[.!?\n])",
        re.I
    )),
    ("ip_address", re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )),
]

SENSITIVE_HIGH = {
    "one_time_password",
    "password",
    "pin",
    "authentication_token",
    "api_key",
    "card_number",
    "bank_account_number",
    "identification_number",
}

SENSITIVE_MEDIUM = {
    "email_address",
    "phone_number",
    "private_address",
    "ip_address",
}


def detect_and_mask(text: str) -> Tuple[str, List[Dict]]:
    """
    Local privacy firewall.

    Returns:
      masked_text: safe-to-display and safe-to-send representation
      detections: structured privacy findings

    The raw value matched by a pattern is NEVER included in detections.
    """
    masked = str(text)
    detections = []
    seen = set()

    for typ, pattern in PATTERNS:
        if not pattern.search(masked):
            continue

        if typ in SENSITIVE_HIGH:
            risk = "high"
            action = "do_not_store"
            replacement = "******"
        else:
            risk = "medium"
            action = "ask_for_confirmation"
            replacement = "******"

        if typ in {"email_address", "ip_address"}:
            masked = pattern.sub(replacement, masked)
        elif typ == "phone_number":
            masked = pattern.sub(lambda m: m.group(1) + replacement, masked)
        else:
            masked = pattern.sub(
                lambda m: m.group(1) + replacement
                if m.lastindex
                else replacement,
                masked
            )

        if typ not in seen:
            detections.append({
                "sensitivity_type": typ,
                "risk": risk,
                "masked_text": masked,
                "recommended_action": action,
            })
            seen.add(typ)

    return masked, detections


def privacy_audit(text: str) -> Dict:
    masked, detections = detect_and_mask(text)
    return {
        "raw_text_used_externally": False,
        "masked_text": masked,
        "detected": bool(detections),
        "detections": detections,
    }
