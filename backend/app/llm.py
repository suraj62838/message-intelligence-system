import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VALID_CATEGORIES = {
    "Action Required",
    "Meeting or Event",
    "Personal Information",
    "General Information",
    "Promotional",
    "Sensitive Information",
}

SYSTEM = """You are the classification engine for a privacy-first message intelligence system.

Classify every supplied message into exactly one category:

- Action Required: a request, instruction, task, or deadline
- Meeting or Event: meeting, appointment, interview, event, or scheduled activity
- Personal Information: personal preference/profile information
- General Information: ordinary informational update
- Promotional: marketing, offers, discounts, rewards, subscriptions
- Sensitive Information: credentials, authentication secrets, payment details,
  private identifiers, private contact/address details, or other sensitive data

For every input message return:
- message_id
- category
- confidence from 0 to 1
- short reason

Never invent facts.
Do not infer dates, times, people, or deadlines.
Masked values such as ****** must remain masked.

Return ONLY JSON in this form:
{
  "results": [
    {
      "message_id": "MSG_001",
      "category": "Action Required",
      "confidence": 0.94,
      "reason": "The sender asks the user to complete a task."
    }
  ]
}
"""


def classify_batch_with_groq(messages: list[dict]):
    if not GROQ_API_KEY:
        return []

    try:
        client = Groq(api_key=GROQ_API_KEY)

        user_content = json.dumps(
            messages,
            ensure_ascii=False
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)

        results = parsed.get("results", [])

        if not isinstance(results, list):
            return []

        cleaned = []

        for item in results:
            if not isinstance(item, dict):
                continue

            if item.get("category") not in VALID_CATEGORIES:
                continue

            try:
                confidence = float(item.get("confidence", 0))
            except (TypeError, ValueError):
                continue

            confidence = max(0.0, min(1.0, confidence))

            cleaned.append({
                "message_id": str(item.get("message_id")),
                "category": item["category"],
                "confidence": confidence,
                "reason": str(
                    item.get("reason", "Classified by Groq.")
                ),
            })

        return cleaned

    except Exception as exc:
        print("GROQ ERROR:", repr(exc))
        return []
