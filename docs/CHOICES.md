# Architecture & Technical Choices

This document outlines the three primary architectural decisions made during the construction of the Retail Intelligence API, detailing the options considered, the AI assistance provided, and the final rationale.

## 1. Detection Model Selection

**The Goal:** Process heavily occluded, blurry retail footage efficiently and generate a bounding-box stream.

**Options Considered:**
1. **YOLOv8 (Ultralytics)**: High inference speed, robust out-of-the-box COCO weights.
2. **MediaPipe**: Extreme speed, lightweight, but tends to struggle heavily with partial occlusions (e.g. people behind retail shelves).
3. **RT-DETR**: High accuracy for complex scenes, but higher computational overhead.

**AI Suggestion & Iteration:**
I prompted an LLM to evaluate the trade-offs specifically regarding "partial occlusions and group entries." The AI recommended combining YOLOv8 with ByteTrack for trajectory momentum. It pointed out that while MediaPipe is faster, YOLOv8 handles upper-body only detections significantly better when customers are hidden behind billing counters.

**Final Choice:** YOLOv8 (nano) paired with `supervision`'s ByteTrack wrapper. The nano model allows for realtime/faster-than-realtime inference on CPU/edge devices, while ByteTrack preserves the `visitor_id` identity across missed frames caused by display shelving.

## 2. Event Schema Design Rationale

**The Goal:** Define a structured JSON schema capable of representing physical retail interactions that can be aggregated accurately by the API.

**Options Considered:**
1. **State-Based Schema**: Emitting the entire store state (all active IDs and their locations) every second.
2. **Delta-Based Event Schema**: Emitting distinct triggers only when a physical state changes (e.g., `ZONE_ENTER`, `ZONE_EXIT`).

**AI Suggestion & Iteration:**
I asked the AI to analyze the challenge's API queries (Funnel, Heatmap, Anomalies). The AI strongly suggested a Delta-Based Event Schema because calculating "Average Dwell Time" from a State-Based schema requires immense grouping overhead in SQLite. It suggested appending `dwell_ms` directly onto the `ZONE_EXIT` event.

**Final Choice:** Delta-Based Event Schema. By calculating `dwell_ms` inside the detection script (client-side) and appending it to `ZONE_EXIT` events, the API simply has to run `AVG(dwell_ms)` in SQLite, completely offloading the temporal math from the database layer and reducing storage by over 90%.

## 3. API Framework and Database Layer

**The Goal:** Build an idempotent, container-ready API that fulfills all challenge endpoints.

**Options Considered:**
1. **FastAPI + SQLite**: Async out of the box, incredibly fast, zero database setup overhead.
2. **Express.js + PostgreSQL**: Extremely scalable, standard for enterprise.
3. **Flask + SQLite**: Simple, but synchronous and lacks built-in Pydantic validation.

**AI Suggestion & Iteration:**
The AI pointed out that idempotency (`POST /events/ingest`) is trivial in SQLite using `INSERT OR IGNORE` combined with a UUID primary key. It recommended FastAPI over Flask because Pydantic models automatically validate the incoming event schema, immediately throwing a `422 Unprocessable Entity` for malformed events, which the challenge requires.

**Final Choice:** FastAPI + SQLite. This combination maximizes developer velocity. Pydantic ensures absolute schema strictness for the detection pipeline, and SQLite removes the need for a separate heavy Postgres container in `docker-compose.yml`, ensuring the evaluator's `docker compose up` command launches instantly without database networking failures.
