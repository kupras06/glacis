
# AI Webhook Ingestion Service

A backend service that ingests arbitrary vendor webhooks, classifies them (Shipment / Invoice / Unclassified), normalizes them into a standard schema using an LLM, and stores the results.

---

## Goals

* Accept any JSON webhook and respond quickly (<200ms)
* Normalize messy vendor data into a clean internal format
* Handle duplicate and out-of-order events
* Maintain an append-only audit log

---

## Architecture (High Level)

1. **Ingestion API**

   * Accepts webhook (`POST /webhook`)
   * Stores raw payload
   * Enqueues processing job

2. **Worker**

   * Classifies event using LLM
   * Normalizes payload into canonical schema
   * Stores normalized event

3. **Storage**

   * Raw events (append-only)
   * Normalized events
   * Optional derived state (latest status per entity)

---

## Quickstart (using uv)

### 1. Install dependencies

```bash
uv sync
```

---

### 2. Set environment variables

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/webhooks
export REDIS_URL=redis://localhost:6379/0
export LLM_PROVIDER=ollama
```

---

### 3. Run services

```bash
# start API
uv run uvicorn src.app.main:app --reload

# start worker
uv run python -m src.worker
```

---

## API

### POST /webhooks

Accepts any JSON payload.

Response:

```json
{
  "status": "accepted",
  "receipt_id": "..."
}
```

---

## Key Design Decisions

* **Async processing** → fast webhook acknowledgment
* **Append-only storage** → full audit + replay capability
* **LLM for normalization** → handles unknown vendor formats
* **Deterministic state** → derived from ordered events

---

## Handling Real-World Issues

* **Duplicates** → hash-based deduplication
* **Out-of-order events** → ordered by `occurred_at`
* **LLM failures** → retries + fallback
* **Invalid JSON from LLM** → safe parsing + repair

---

## LLM Support

The system is **model-agnostic**:

* Local: Ollama (default)
* Cloud: OpenAI, Gemini, DeepSeek

Prompts enforce:

* strict JSON output
* canonical status mapping
* confidence scoring

---

## Future Improvements

* Schema validation + strict enforcement
* Human-in-the-loop for low-confidence events
* Streaming pipeline (Kafka)
* Metrics & tracing (observability)

---

## Summary

This system treats all incoming webhooks as **immutable events** and builds a reliable pipeline that transforms unstructured vendor data into structured, actionable insights.
