import os
import json
import pytest
from pipeline.export_logs import export_logs

def test_export_logs_creates_file_and_matches_schema(tmp_path):
    # Use an empty DB path to simulate empty DB but create file
    test_db = tmp_path / "test_db.sqlite3"
    test_output = tmp_path / "final_events.jsonl"
    
    # We will create a small db to test mapping
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute('''
        CREATE TABLE ingest_events (
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
    conn.execute('''
        INSERT INTO ingest_events 
        (event_id, store_id, camera_id, visitor_id, event_type, timestamp, zone_id, dwell_ms, is_staff, confidence)
        VALUES 
        ('E1', 'ST1', 'CAM1', 'VIS1', 'ENTRY', '2026-06-03T10:20:11Z', 'Z1', 1000, 0, 0.95)
    ''')
    conn.commit()
    conn.close()
    
    # Run export
    export_logs(db_path=str(test_db), output_path=str(test_output))
    
    # Validate file exists
    assert os.path.exists(test_output)
    
    # Validate contents
    with open(test_output, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        
        # Validate valid JSON per line
        data = json.loads(lines[0])
        
        # Validate schema mapping matches
        assert data["id_token"] == "VIS1"
        assert data["store_code"] == "ST1"
        assert data["event_timestamp"] == "2026-06-03T10:20:11Z"
        assert data["confidence_score"] == 0.95
        assert data["zone_id"] == "Z1"
        
        # Validate demographic placeholders exist
        assert "gender_pred" in data
        assert data["gender_pred"] == "unknown"
        assert "age_pred" in data
        assert "age_bucket" in data
