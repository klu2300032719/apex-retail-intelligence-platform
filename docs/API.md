# Intelligence API Documentation

## Overview
The API is split into isolated routing modules to match enterprise standards:
- `app/api.py`: Ingestion logic
- `app/metrics.py`: Standard metrics queries
- `app/funnel.py`: Funnel tracking
- `app/anomalies.py`: Real-time anomalies
- `app/health.py`: Status checks

## Endpoints
- `POST /events/ingest`: Takes a batch of DetectionEvents
- `GET /stores/{store_id}/metrics`: Store summary KPIs
- `GET /stores/{store_id}/funnel`: Dropoff tracking
- `GET /stores/{store_id}/heatmap`: Intensity coordinates
- `GET /stores/{store_id}/anomalies`: active AI insights
- `GET /health`: Platform sync status
