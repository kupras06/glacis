import hashlib
import json

from celery_app import celery_app
from db import SessionLocal, ensure_tables_exist
from llm import processor
from models import NormalizedEvent

ensure_tables_exist()


def compute_hash(payload: dict):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@celery_app.task(bind=True, max_retries=3)
def process_event(self, payload):
    db = SessionLocal()
    try:
        event_hash = compute_hash(payload)

        # Check if already normalized
        existing = db.query(NormalizedEvent).filter_by(event_hash=event_hash).first()
        if existing:
            return "duplicate"
        print(f"Event hash: {event_hash}")
        classification = processor.classify(payload)
        print(f"Classification: {classification}")
        payload["event_type"] = classification
        normalized = processor.normalize(payload)
        print(f"Normalized: {normalized}")

        event = NormalizedEvent(
            event_hash=event_hash,
            event_type=classification,
            status=normalized.get("status"),
            sub_status=normalized.get("sub_status"),
            occurred_at=normalized.get("occurred_at"),
            entity_keys=normalized.get("entity_keys"),
            location=normalized.get("location"),
            confidence=normalized.get("confidence", 0.5),
        )

        print(f"Normalized event: {normalized}")
        print(f"Normalized event: {event}")
        db.add(event)
        db.commit()

        return "processed"

    except Exception as e:
        print("\n\nError", e)
        db.rollback()
        raise self.retry(exc=e, countdown=2)

    finally:
        db.close()
