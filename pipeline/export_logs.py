import sqlite3
import json
import os
from datetime import datetime

# Demographic fields are placeholder metadata because the challenge dataset provides anonymized blurred faces.
DEFAULT_GENDER_PRED = "unknown"
DEFAULT_AGE_PRED = 30
DEFAULT_AGE_BUCKET = "25-34"

def export_logs(db_path="store_analytics.db", output_path="data/events/final_events.jsonl"):
    print(f"Exporting logs from {db_path} to {output_path}...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating empty file to avoid crash.")
        # If no DB yet, write an empty JSONL
        with open(output_path, "w", encoding="utf-8") as f:
            pass
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingest_events'")
        if not cursor.fetchone():
            print("Table 'ingest_events' does not exist. Writing empty log.")
            with open(output_path, "w", encoding="utf-8") as f:
                pass
            return
            
        cursor.execute("SELECT * FROM ingest_events")
        rows = cursor.fetchall()
        
        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                row_dict = dict(row)
                
                # Transform internal schema -> official challenge schema
                # visitor_id -> id_token
                # store_id -> store_code
                # timestamp -> event_timestamp
                # confidence -> confidence_score
                
                event = {
                    "id_token": row_dict.get("visitor_id", "UNKNOWN_VISITOR"),
                    "store_code": row_dict.get("store_id", "UNKNOWN_STORE"),
                    "camera_id": row_dict.get("camera_id", "UNKNOWN_CAMERA"),
                    "event_timestamp": row_dict.get("timestamp") or datetime.utcnow().isoformat() + "Z",
                    "event_type": row_dict.get("event_type", "unknown"),
                    "zone_id": row_dict.get("zone_id", ""),  # Match official schema exact key 'zone_id'
                    "confidence_score": row_dict.get("confidence", 0.0),
                    "is_staff": bool(row_dict.get("is_staff", False)),
                    "dwell_ms": row_dict.get("dwell_ms", 0),
                    # Demographic Placeholders
                    "gender_pred": DEFAULT_GENDER_PRED,
                    "age_pred": DEFAULT_AGE_PRED,
                    "age_bucket": DEFAULT_AGE_BUCKET
                }
                
                # Additional fields to handle queue metadata if any
                queue_depth = row_dict.get("queue_depth")
                if queue_depth is not None:
                    event["queue_depth"] = queue_depth
                
                # Write one valid JSON object per line, no trailing commas, utf-8
                f.write(json.dumps(event) + "\n")
                
        print(f"Export completed successfully. {len(rows)} events written.")
        
    except Exception as e:
        print(f"Error during export: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    export_logs()
