# Privacy and Assignment Compliance

## Privacy pipeline

1. The CSV is uploaded to the local FastAPI application.
2. Sensitive-looking values are detected locally.
3. Values such as OTPs, passwords, PINs, tokens, card/account numbers, IDs,
   email addresses, phone numbers, private addresses, and IP addresses are masked.
4. Only the masked message is eligible for Groq classification.
5. Raw message text is never included in the Groq payload.
6. The local privacy layer takes precedence over an LLM classification when it
   detects sensitive information.
7. The application stores the masked message for display.

## Chronological processing

Messages are processed with:

`ORDER BY timestamp ASC, message_id ASC`

This provides deterministic chronological processing and a stable tie-breaker.

## No guessing

Task/event extraction only records a date, time, or person when it is explicitly
present in the message. Missing values are returned as `null` or `unresolved`.

Priority is only marked high when the message explicitly contains strong urgency
such as "urgent", "critical", "ASAP", or "immediately".

## AI development disclosure

AI development tools may be used during implementation for coding assistance and
debugging. The submitted application itself does not rely completely on an
external AI service: local privacy detection, masking, rule-based fallback
classification, storage, and validation are implemented in the application.

Groq is used as an optional classification aid after the local privacy layer.
