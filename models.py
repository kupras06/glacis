import uuid

from sqlalchemy import JSON, TIMESTAMP, Column, Float, String
from sqlalchemy.sql import func

from db import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_hash = Column(String, unique=True, index=True)
    payload = Column(JSON)
    received_at = Column(TIMESTAMP, server_default=func.now())


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_hash = Column(String, index=True)
    event_type = Column(String)
    status = Column(String)
    sub_status = Column(String, nullable=True)
    occurred_at = Column(TIMESTAMP)
    entity_keys = Column(JSON)
    location = Column(String, nullable=True)
    confidence = Column(Float)
    created_at = Column(TIMESTAMP, server_default=func.now())
