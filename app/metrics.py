from fastapi import APIRouter, Depends
import sqlite3
from app.database import get_db

router = APIRouter()

@router.get("/stores/{store_id}/metrics")
def get_metrics(store_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as v FROM ingest_events WHERE store_id=? AND is_staff=0", (store_id,))
    unique_v = cursor.fetchone()['v']
    
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as c FROM ingest_events WHERE store_id=? AND event_type='PURCHASE_CONVERTED'", (store_id,))
    convs = cursor.fetchone()['c']
    
    conv_rate = (convs / unique_v * 100) if unique_v > 0 else 0.0
    
    cursor.execute("SELECT AVG(dwell_ms) as avg_d FROM ingest_events WHERE store_id=? AND event_type='ZONE_DWELL' AND is_staff=0", (store_id,))
    avg_d = cursor.fetchone()['avg_d'] or 0.0
    
    conn.close()
    
    return {
        "store_id": store_id,
        "unique_visitors": unique_v,
        "conversion_rate": round(conv_rate, 2),
        "avg_dwell_ms": int(avg_d),
        "queue_depth": 0, 
        "abandonment_rate": 0.0
    }

@router.get("/stores/{store_id}/heatmap")
def get_heatmap(store_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT zone_id, COUNT(DISTINCT visitor_id) as sessions, AVG(dwell_ms) as avg_dwell
        FROM ingest_events 
        WHERE store_id=? AND zone_id IS NOT NULL AND is_staff=0
        GROUP BY zone_id
    """, (store_id,))
    
    rows = cursor.fetchall()
    
    total_sessions = sum(r['sessions'] for r in rows)
    data_conf = True if total_sessions >= 20 else False
    
    heatmap = []
    if rows:
        max_sess = max(r['sessions'] for r in rows)
        for r in rows:
            heatmap.append({
                "zone_id": r['zone_id'],
                "intensity_0_100": round((r['sessions']/max_sess)*100, 1) if max_sess > 0 else 0,
                "avg_dwell_ms": int(r['avg_dwell'] or 0)
            })
            
    conn.close()
    
    return {
        "store_id": store_id,
        "data_confidence": data_conf,
        "heatmap": heatmap
    }
