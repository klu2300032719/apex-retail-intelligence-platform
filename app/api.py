from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import logging
from app.database import get_db

router = APIRouter()
logger = logging.getLogger("IntelligenceAPI")

class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: Optional[int] = None

class DetectionEvent(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: int = 0
    is_staff: bool = False
    confidence: float
    metadata: Optional[EventMetadata] = None

@router.post("/events/ingest")
def ingest_events(events: List[DetectionEvent], conn: sqlite3.Connection = Depends(get_db)):
    if len(events) > 500:
        raise HTTPException(status_code=400, detail={"error": "Batch size exceeds 500 limit"})
        
    cursor = conn.cursor()
    
    inserted = 0
    errors = 0
    
    for ev in events:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO ingest_events 
                (event_id, store_id, camera_id, visitor_id, event_type, timestamp, zone_id, dwell_ms, is_staff, confidence, queue_depth, sku_zone, session_seq)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ev.event_id, ev.store_id, ev.camera_id, ev.visitor_id, ev.event_type, 
                ev.timestamp, ev.zone_id, ev.dwell_ms, ev.is_staff, ev.confidence,
                ev.metadata.queue_depth if ev.metadata else None,
                ev.metadata.sku_zone if ev.metadata else None,
                ev.metadata.session_seq if ev.metadata else None
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            errors += 1
            
    conn.commit()
    conn.close()
    
    logger.info(f'{{"event_count": {len(events)}, "inserted": {inserted}, "errors": {errors}}}')
    
    return {
        "status": "success",
        "received": len(events),
        "inserted": inserted,
        "errors": errors
    }
