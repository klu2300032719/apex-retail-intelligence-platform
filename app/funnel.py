from fastapi import APIRouter, Depends
import sqlite3
from app.database import get_db

router = APIRouter()

@router.get("/stores/{store_id}/funnel")
def get_funnel(store_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    # Entry
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as e FROM ingest_events WHERE store_id=? AND event_type='ENTRY' AND is_staff=0", (store_id,))
    entries = cursor.fetchone()['e']
    
    # Zone
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as z FROM ingest_events WHERE store_id=? AND event_type='ZONE_ENTER' AND is_staff=0", (store_id,))
    zones = cursor.fetchone()['z']
    
    # Billing Queue
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as q FROM ingest_events WHERE store_id=? AND event_type='BILLING_QUEUE_JOIN' AND is_staff=0", (store_id,))
    queue = cursor.fetchone()['q']
    
    # Purchase
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) as p FROM ingest_events WHERE store_id=? AND event_type='PURCHASE_CONVERTED' AND is_staff=0", (store_id,))
    purchases = cursor.fetchone()['p']
    
    conn.close()
    
    return {
        "store_id": store_id,
        "funnel": [
            {"stage": "Entry", "count": entries, "dropoff_pct": 0},
            {"stage": "Zone Visit", "count": zones, "dropoff_pct": round((1 - zones/entries)*100, 1) if entries > 0 else 0},
            {"stage": "Billing Queue", "count": queue, "dropoff_pct": round((1 - queue/zones)*100, 1) if zones > 0 else 0},
            {"stage": "Purchase", "count": purchases, "dropoff_pct": round((1 - purchases/queue)*100, 1) if queue > 0 else 0}
        ]
    }
