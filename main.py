import hashlib
import json

from fastapi import FastAPI
from pydantic import RootModel

from db import SessionLocal
from models import RawEvent
from worker import process_event

app = FastAPI()


def compute_hash(payload: dict):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class RequestBody(RootModel):
    root: dict


@app.post("/webhook")
async def ingest(body: RequestBody):
    db = SessionLocal()
    payload = body.model_dump()
    try:
        event_hash = compute_hash(body.model_dump())

        # Idempotency check (raw events)
        existing = db.query(RawEvent).filter_by(event_hash=event_hash).first()
        if existing:
            return {"status": "duplicate", "event_hash": event_hash}

        # Store raw event (source of truth)
        raw_event = RawEvent(event_hash=event_hash, payload=payload)
        db.add(raw_event)
        db.commit()

        # Push to async worker (non-blocking)
        process_event.delay(payload)

        # Fast ACK
        return {"status": "accepted", "event_hash": event_hash}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
