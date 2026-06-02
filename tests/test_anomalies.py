# PROMPT: "Generate a pytest file to test the anomalies endpoint. Ensure it safely handles empty queries and returns the active anomalies."
# CHANGES MADE: Extracted this test from the monolithic test suite.

import pytest
from fastapi.testclient import TestClient
import sqlite3
import os

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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingest_events (
            event_id TEXT PRIMARY KEY
        )
    ''')
    # Create the anomalies table if needed for this test
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_insights (
            category TEXT,
            insight_text TEXT
        )
    ''')
    conn.execute('DELETE FROM ai_insights')
    
    # Insert dummy anomaly
    conn.execute('INSERT INTO ai_insights (category, insight_text) VALUES (?, ?)', ("CRITICAL", "High Queue Depth"))
    conn.commit()
    conn.close()
    yield
    conn = override_get_db()
    conn.execute('DELETE FROM ai_insights')
    conn.commit()
    conn.close()

def test_get_anomalies():
    res = client.get("/stores/STORE_001/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert "active_anomalies" in data
    assert len(data["active_anomalies"]) == 1
    assert data["active_anomalies"][0]["type"] == "CRITICAL"
    assert data["active_anomalies"][0]["suggested_action"] == "High Queue Depth"
