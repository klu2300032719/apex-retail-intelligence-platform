import pytest
from fastapi.testclient import TestClient
import sqlite3
import os
import uuid
import datetime

from app.main import app
from app.database import get_db

client = TestClient(app)
TEST_DB = "test_store_analytics.db"

def override_get_db():
    conn = sqlite3.connect(TEST_DB, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    conn = override_get_db()
    conn.execute('DROP TABLE IF EXISTS ingest_events')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingest_events (
            event_id TEXT PRIMARY KEY,
            store_id TEXT,
            camera_id TEXT,
            visitor_id TEXT,
            event_type TEXT,
            timestamp TEXT,
            zone_id TEXT,
            dwell_ms INTEGER,
            is_staff BOOLEAN,
            confidence REAL,
            queue_depth INTEGER,
            sku_zone TEXT,
            session_seq INTEGER
        )
    ''')
    conn.execute('DELETE FROM ingest_events')
    conn.commit()
    conn.close()
    yield
    conn = override_get_db()
    conn.execute('DELETE FROM ingest_events')
    conn.commit()
    conn.close()

def test_metrics_empty_store():
    res = client.get("/stores/STORE_UNKNOWN/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["unique_visitors"] == 0
    assert data["conversion_rate"] == 0.0

def test_funnel_with_zero_purchases():
    payload = [{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_001",
        "camera_id": "CAM_1",
        "visitor_id": "VIS_456",
        "event_type": "ENTRY",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.99
    }]
    client.post("/events/ingest", json=payload)
    
    res = client.get("/stores/STORE_001/funnel")
    assert res.status_code == 200
    funnel = res.json()["funnel"]
    assert funnel[0]["stage"] == "Entry"
    assert funnel[0]["count"] == 1
    assert funnel[-1]["stage"] == "Purchase"
    assert funnel[-1]["count"] == 0
    assert funnel[-1]["dropoff_pct"] == 0

def test_staff_exclusion():
    payload = [{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_001",
        "camera_id": "CAM_1",
        "visitor_id": "STAFF_1",
        "event_type": "ENTRY",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "dwell_ms": 0,
        "is_staff": True,
        "confidence": 0.99
    }]
    client.post("/events/ingest", json=payload)
    
    res = client.get("/stores/STORE_001/metrics")
    assert res.status_code == 200
    assert res.json()["unique_visitors"] == 0
