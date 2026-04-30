# Tasks

This file lists concise, actionable tasks for the assessment. Tasks are grouped by top-level deliverables and kept minimal.

Deliverable: Project setup & developer DX
- Create repository skeleton: `src/`, `prompts/`, `schemas/`, `samples/`, `docs/`, `scripts/`.
- Add linters and `pre-commit` config.
- Add a CI workflow to run linters and a smoke build.
- Add `docker-compose.yml` for local dev (app, worker, Postgres, Redis).
- Add `.env.example` and simple run instructions in `README.md`.

Deliverable: Ingestion & persistence
- Implement `POST /webhooks` that accepts arbitrary JSON and returns a `receipt_id`.
- Persist raw payloads to `raw_payloads` table (id, received_at, headers, body, payload_hash, vendor_event_id).
- Enqueue a processing job referencing `raw_payload_id` to a durable queue (Redis/SQS/Postgres-backed).
- Add `scripts/send_samples.py` to post Appendix sample payloads.

Deliverable: Worker & LLM normalization
- Implement a worker that dequeues jobs and processes them with retry/backoff.
- Implement an `llm_client` wrapper (provider via env, timeout, retries).
- Add prompt templates: `prompts/classify.txt`, `prompts/normalize_shipment.txt`, `prompts/normalize_invoice.txt` (2 examples each).
- Validate LLM output against JSON schemas; on repeated failure persist as `unclassified` and record `llm_metadata`.
- Cache LLM results keyed by `payload_hash` (TTL ~24h) to avoid duplicate calls.

Deliverable: Normalized schemas & state machine
- Define `schemas/shipment.json` and `schemas/invoice.json` with required fields: `entity_type`, `entity_id`, `vendor_event_id`, `canonical_state`, `occurred_at`, `confidence`, `metadata`.
- Add `normalized_events`, `entities`, and append-only `event_history` tables.
- Implement a deterministic state machine that reduces chronological events into `entities.current_state` and supports recompute when older events arrive.
- Implement entity matching heuristics (container number, BL, invoice ref) and emit `match_confidence`.
- Use per-entity locking when applying events (DB advisory locks or Redis locks).

Deliverable: Resiliency & data integrity
- Deduplicate on `vendor_event_id` (when present) or `payload_hash` with a short TTL cache.
- Implement retry/backoff and a DLQ that stores diagnostics and LLM responses for manual review.
- Ensure durability before acknowledging webhooks (persist or durable enqueue before returning success).

Deliverable: Load testing
- Create load scripts (k6 or locust) to simulate bursts, duplicates, and out-of-order events.
- Record baseline metrics (p95 ack latency, throughput) in `docs/perf.md`.

Deliverable: Observability & runbook
- Structured JSON logs including correlation ids (`receipt_id`, `raw_payload_id`, `entity_id`).
- Expose Prometheus metrics: `webhook_ack_latency_seconds`, `llm_calls_total`, `dlq_size`.
- Add `docs/RUNBOOK.md` with short steps: LLM outage, DLQ inspection, replay raw payloads.

Deliverable: Security & compliance
- HMAC signature verification per-vendor (configurable).
- Provide `.env.example` and notes on secrets management; do not commit secrets.
- Small PII redaction utility for logs/exports.

Deliverable: Tooling
- `scripts/replay_raw.py` to re-enqueue raw payloads by id or time range.
- `scripts/vendor_simulator.py` to send Appendix payloads in-order, out-of-order, and as duplicates.

(End of file)
