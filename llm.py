import json

from google import genai
from ollama import chat
from openai import OpenAI

from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)
genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL = "llama3.2"

NORMALIZE_PROMPT_INSTRUCTIONS = """
You are a strict data normalization engine for a supply chain platform.

Your job is to:

Analyze arbitrary vendor JSON payloads
Classify and normalize them into a strict internal schema
Output ONLY valid JSON with no explanation or extra text

INPUT:
You will receive:

A raw JSON payload
Sometimes an optional hint: "event_type": "Shipment" | "Invoice" | "Unclassified"

OUTPUT SCHEMA:
{
"event_type": "shipment | invoice | unclassified",
"status": "PICKED_UP | IN_TRANSIT | OUT_FOR_DELIVERY | DELIVERED | ISSUED | PAID | VOIDED | REFUNDED | UNKNOWN",
"sub_status": "string or null",
"occurred_at": "ISO-8601 UTC timestamp",
"entity_keys": {
"tracking_number": "string or null",
"container": "string or null",
"mbl": "string or null",
"hbl": "string or null",
"invoice_id": "string or null"
},
"location": "string or null",
"confidence": number between 0 and 1
}

HARD RULES:

Output MUST be valid JSON
Do NOT include any explanation or extra text
Do NOT hallucinate missing values, use null instead
Ensure all braces are properly closed
Do not include trailing commas
Convert all timestamps to ISO-8601 UTC
Confidence must be between 0 and 1
If uncertain, reduce confidence

CLASSIFICATION RULES:
Shipment:

Physical movement of goods
Indicators: container, vessel, shipment, delivery, consignee, port, tracking, milestone

Invoice:

Financial or billing related events
Indicators: invoice, amount, payment, settled, issued, due, charges

Unclassified:

If neither shipment nor invoice applies

PRIORITY RULE:
If both shipment and financial signals exist, classify as invoice

STATUS MAPPING:

Shipment:

PICKED_UP → gate-in, received at origin, container released
IN_TRANSIT → loaded, departed, sailed, on vessel
OUT_FOR_DELIVERY → out for delivery, last mile
DELIVERED → delivered, released to consignee, handed over

Invoice:

ISSUED → invoice created, raised
PAID → settled, paid, completed
VOIDED → cancelled before payment
REFUNDED → payment reversed

If no clear mapping, use status = UNKNOWN

ENTITY EXTRACTION:

container → container_no, container, equipment
mbl → master_bl, mbl, bill of lading
hbl → house_bl
invoice_id → doc_ref, invoice number
tracking_number → tracking, shipment id

If a field is missing, set it to null

TIME PARSING:

Convert all timestamps to UTC
Supported formats include ISO timestamps and formats like "28/04/2026 09:42 WIB"
If timezone is known, convert properly
If timezone is missing, assume UTC

LOCATION:

Prefer port codes such as CNSHA, IDJKT
Otherwise use port or city name
If missing, return null

CONFIDENCE SCORING:

0.9 to 1.0 → explicit and clear mapping
0.7 to 0.9 → strong inference
0.4 to 0.7 → partial data
below 0.4 → weak or uncertain

EXAMPLES:

Input: "Cargo released to consignee"
Output event_type: shipment, status: DELIVERED

Input: "freight invoice raised"
Output event_type: invoice, status: ISSUED

FINAL INSTRUCTION:
Return ONLY valid JSON.Close all brackets, check puncutations
"""

SYSTEM_CLASSIFY_PROMPT = """
You are a strict classifier for supply chain events.

Your task:
Classify JSON into exactly one of:
- Shipment
- Invoice
- Unclassified

---

## Definitions

Shipment:
- Physical movement of goods
- Keywords: container, vessel, shipment, delivery, consignee, port, tracking, milestone

Invoice:
- Financial or billing events
- Keywords: invoice, payment, amount, settled, issued, due, charges

Unclassified:
- Alerts, advisories, unrelated data, or unclear meaning

---

## Rules

- Output ONLY one word: Shipment OR Invoice OR Unclassified
- No explanation
- No punctuation
- No JSON
- No extra whitespace

---

## Priority Rules (important)

- If both logistics + payment appear → classify as Invoice
- If only movement/logistics → Shipment
- If unclear → Unclassified
"""


def classify(payload: dict):
    prompt = f"""
Classify this JSON.
JSON:
{json.dumps(payload)}
"""

    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_CLASSIFY_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    result = response["message"]["content"].strip()

    # 🔒 hard guard (important)
    if result not in {"Shipment", "Invoice", "Unclassified"}:
        return "Unclassified"

    return result


def normalize(payload: dict):
    prompt = f"""
Normalize this JSON :
{json.dumps(payload)}
"""

    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": NORMALIZE_PROMPT_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
    )

    return json.loads(response["message"]["content"])
