def get_zone_event_type(camera_purpose, detected_zone):
    """Dynamically classify event types based on camera purpose and zone name."""
    zone_upper = detected_zone.upper()
    if camera_purpose == "billing" and "QUEUE" in zone_upper:
        return "BILLING_QUEUE_JOIN"
    elif camera_purpose == "entry" and "ENTRY" in zone_upper:
        return "ENTRY"
    return "ZONE_ENTER"
