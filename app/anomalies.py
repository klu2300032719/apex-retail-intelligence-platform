from fastapi import APIRouter, Depends
import sqlite3
from app.database import get_db

router = APIRouter()

@router.get("/stores/{store_id}/anomalies")
def get_anomalies(store_id: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT category as severity, insight_text as suggested_action FROM ai_insights WHERE store_id=?", (store_id,))
        raw = cursor.fetchall()
        anomalies = []
        for r in raw:
            anomalies.append({
                "type": r['severity'],
                "suggested_action": r['suggested_action']
            })
    except:
        anomalies = []
        
    conn.close()
    
    return {
        "store_id": store_id,
        "active_anomalies": anomalies
    }
