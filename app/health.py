from fastapi import APIRouter, Depends
import sqlite3
import datetime
from app.database import get_db

router = APIRouter()

@router.get("/health")
def health_check(conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    cursor.execute("SELECT store_id, MAX(timestamp) as last_ts FROM ingest_events GROUP BY store_id")
    rows = cursor.fetchall()
    
    store_lags = {}
    stale_warning = False
    now = datetime.datetime.utcnow()
    
    for r in rows:
        try:
            last_ts = datetime.datetime.fromisoformat(r['last_ts'].replace('Z', '+00:00'))
            lag_minutes = (now.timestamp() - last_ts.timestamp()) / 60.0
            if lag_minutes > 10:
                stale_warning = True
            store_lags[r['store_id']] = r['last_ts']
        except:
            pass

    conn.close()
    
    status = "healthy"
    if stale_warning:
        status = "STALE_FEED"
        
    return {
        "status": status,
        "last_events": store_lags
    }
