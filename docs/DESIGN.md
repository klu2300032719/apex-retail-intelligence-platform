# Intelligence Platform Architecture

## System Architecture

The Retail Store Intelligence system is composed of three interconnected layers that take raw CCTV video feeds and convert them into actionable retail metrics:

1. **Detection Layer (`event_generator.py`)**
   - Ingests raw video clips representing various camera angles (e.g., Entry, Main Floor, Billing).
   - Downscales video resolution by 80% to maintain inference speed without losing spatial relationships.
   - Utilizes YOLOv8 (nano) coupled with ByteTrack for high-speed object detection and tracking.
   - Transforms hardcoded pixel polygons into scaled intersection zones, mapping tracks directly into defined physical spaces.
   - Pushes grouped JSON payloads containing `DetectionEvent` objects to the Intelligence API.

2. **Intelligence API Layer (`api.py`)**
   - A FastAPI application responsible for capturing the real-time event stream.
   - Exposes `POST /events/ingest` which buffers events directly into an SQLite data store using `INSERT OR IGNORE` via UUIDs for rigid idempotency.
   - Exposes RESTful aggregations (Metrics, Funnel, Heatmap, Anomalies) by performing SQL operations strictly on `ingest_events` to compute the North Star Metric (Conversion Rate) dynamically.

3. **Dashboard Layer (`dashboard.py`)**
   - Provides a live enterprise Command Center.
   - Polls the API's SQLite tables and dynamically updates synthetic real-time metrics using Plotly and Streamlit.

## AI-Assisted Decisions

1. **Schema Refactoring (Agreed & Accepted)**
   - **Initial thought:** I originally structured the pipeline to write line-by-line `jsonl` files natively inside `event_generator.py`.
   - **AI Suggestion:** The AI pointed out that writing directly to JSONL breaks the decoupling rule in a distributed system, and strongly suggested transitioning to a UUID-driven JSON push schema with a FastAPI `/events/ingest` buffer. 
   - **Decision:** I completely agreed. Refactoring the Event Schema to emit batches of HTTP payloads with idempotency allowed for a massive improvement in data reliability.

2. **FastAPI File Structure (Adopted)**
   - **Initial thought:** I initially thought about keeping the API monolithic (`api.py`) to reduce file count.
   - **AI Suggestion:** The AI pointed out that for enterprise hiring challenges, matching the grading rubric's suggested micro-architecture (`app/models.py`, `app/metrics.py`, etc.) is critical for displaying a scalable mindset.
   - **Decision:** I completely agreed and separated the API into distinct routing modules under the `app/` directory to ensure perfect compliance with the challenge suggestion.
