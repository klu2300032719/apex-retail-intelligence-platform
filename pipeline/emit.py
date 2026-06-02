import requests

def flush_events(event_batch, api_url):
    if not event_batch:
        return
    try:
        res = requests.post(api_url, json=event_batch, timeout=2.0)
        if res.status_code == 200:
            print(f"[API] Ingested batch of {len(event_batch)} events.")
        else:
            print(f"[API ERROR] {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[API ERROR] Connection failed: {e}")
