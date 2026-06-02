import sqlite3
import logging
from fastapi import HTTPException

logger = logging.getLogger("IntelligenceAPI")

def get_db():
    db_path = "store_analytics.db"
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        
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
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=503, detail={"error": "Database unavailable", "reason": str(e)})
