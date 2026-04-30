# AI Webhook Ingestion Service

A backend service that ingests arbitrary vendor webhook JSON payloads, classifies the event (Shipment / Invoice / Unclassified) using LLMs, normalizes the data to canonical internal schemas, and persists the result for downstream systems.

This repository contains a reference implementation and an architecture-first design to handle noisy, duplicate, and out-of-order webhooks from many vendors.

Goals
- Accept any JSON webhook and acknowlege quickly (sub-second)
- Use an LLM to classify and normalize vendor payloads into canonical schemas
- Be resilient to duplicate payloads and out-of-order event arrival
- Preserve an append-only audit trail for every inbound webhook

Contents
- `src/` - application source code (API, worker, normalization pipeline)
- `docs/ARCHITECTURE.md` - system architecture and design decisions
- `prompts/` - canonical LLM prompt templates and examples
- `schemas/` - JSON Schema definitions for normalized objects
- `samples/` - sample vendor payloads and Postman/Insomnia collections
- `tasks.md` - project backlog and GitHub-issues-ready tasks
- `docker-compose.yml` - development compose file (if present)

Quickstart (local, without Docker)
1. Ensure you have Python 3.10+ (or preferred runtime), virtualenv/poetry, Postgres, and Redis available.
2. Create virtual environment and install dependencies (example using poetry):

   ```bash
   poetry install
   ```

3. Configure environment variables (see Configuration below). Run migrations and start services:

   ```bash
   # run DB migrations (example)
   alembic upgrade head

   # start app (example using uvicorn)
   uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

   # start worker
   python -m src.worker
   ```

Configuration (recommended env vars)
- `DATABASE_URL` - Postgres connection string (e.g. `postgresql://user:pass@localhost:5432/webhooks`)
- `REDIS_URL` - Redis connection string for queue/locks
- `LLM_PROVIDER` - Identifier of LLM provider (`openai`, `anthropic`, etc.)
- `OPENAI_API_KEY` - API key for OpenAI (if used)
- `QUEUE_TYPE` - `redis` or `sqla` (Postgres-backed queue)
- `LOG_LEVEL` - `INFO` / `DEBUG`
- `HMAC_SECRETS` - (optional) per-vendor HMAC secrets mapping for signature verification

Endpoints
- `POST /webhooks` - Accepts arbitrary JSON payloads. Returns a `receipt_id` and immediate acknowledgement. Example response:

  ```json
  {"status": "accepted", "receipt_id": "raw_01F..."}
  ```

High-level workflow
1. Ingest: `POST /webhooks` receives JSON; we persist the raw payload to an append-only `raw_payloads` table and enqueue a processing job.
2. Processing (worker): Job loads raw payload, optionally applies vendor fast-path rules, otherwise calls the LLM wrapper to classify and normalize into a strict JSON Schema.
3. Persistence: Normalized object is validated and inserted into `normalized_events`. The `entities` table stores the current computed state for that shipment/invoice. All updates append to `event_history` for auditability.

Operational considerations
- Sub-second ack: The endpoint returns quickly after ensuring a durable write or enqueue.
- Deduplication: Use `vendor_event_id` when present, otherwise `payload_hash` and heuristics. Cache LLM results for duplicate suppression.
- Out-of-order events: `occurred_at` is used to order events; the state machine recomputes `entities.current_state` deterministically when earlier events arrive.
- Concurrency control: Use per-entity locks (DB advisory locks or Redis locks) when mutating entity state.
- Retries & DLQ: Worker retries transient failures and pushes to a dead-letter queue after exhausting retries.

Testing
- Unit tests: `pytest` (core logic and state machine)
- Integration: a lightweight test harness spins up a mock LLM and local Postgres/Redis to run E2E flows
- Load testing: recommended tools `k6` or `locust` for webhook burst simulations

Prompts & LLM
- Prompts live in `prompts/` and must instruct the model to output strict JSON that conforms to the `schemas/` definitions.
- Use explicit examples and ask the model to include a `confidence` field and a `canonical_state` value when applicable.

Developer tools
- `scripts/replay_raw.py` - replay raw payloads for reprocessing (by id or time range)
- `scripts/vendor_simulator.py` - send Appendix payloads in order/out-of-order/duplicates

Where to find more
- Architecture decisions: `docs/ARCHITECTURE.md`
- Project backlog/tasks: `tasks.md`

Roadmap & production readiness
See `docs/ARCHITECTURE.md` for the roadmap and tradeoffs. Short-term priorities are:
1. Persistent raw storage + durable queue
2. Basic LLM wrapper and prompt templates
3. Deterministic state machine + out-of-order handling
4. Observability (metrics + traces) and DLQ

Contributing
Please read `CONTRIBUTING.md` (if present). This project uses GitHub issues (see `tasks.md`) for tasks and prioritization. Create a branch per issue and open PRs against `main`.

License
MIT
