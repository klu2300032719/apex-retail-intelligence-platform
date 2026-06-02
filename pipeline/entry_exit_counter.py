def get_zone_event_type(camera_id, detected_zone):
    if camera_id == "CAM 5" and detected_zone == "CUSTOMER_POS_QUEUE":
        return "BILLING_QUEUE_JOIN"
    elif camera_id == "CAM 3" and detected_zone == "GLASS_ENTRY_DOORWAY":
        return "ENTRY"
    return "ZONE_ENTER"
