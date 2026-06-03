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
    conn.commit()
    return conn

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    conn = override_get_db()
    conn.execute('DELETE FROM ingest_events')
    conn.commit()
    conn.close()
    yield
    conn = override_get_db()
    conn.execute('DELETE FROM ingest_events')
    conn.commit()
    conn.close()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "STALE_FEED"]

def test_event_ingest_idempotency():
    ev_id = str(uuid.uuid4())
    payload = [{
        "event_id": ev_id,
        "store_id": "STORE_001",
        "camera_id": "CAM_1",
        "visitor_id": "VIS_1",
        "event_type": "ENTRY",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95
    }]
    
    res1 = client.post("/events/ingest", json=payload)
    assert res1.status_code == 200
    assert res1.json()["inserted"] == 1
    
    # Second ingest of same ID should be ignored
    res2 = client.post("/events/ingest", json=payload)
    assert res2.status_code == 200
    assert res2.json()["inserted"] == 0
