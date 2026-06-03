import numpy as np
import os
import glob

# Allow manual overrides for specific stores and cameras
STORE_CONFIG = {
    "STORE_BLR_001": {
        "CAM 1 - zone": {"purpose": "zone", "is_staff_default": False},
        "CAM 2 - zone": {"purpose": "zone", "is_staff_default": False},
        "CAM 3 - entry": {"purpose": "entry", "is_staff_default": False},
        "CAM 5 - billing": {"purpose": "billing", "is_staff_default": False}
    },
    "STORE_BLR_002": {
        "billing_area": {"purpose": "billing", "is_staff_default": False},
        "entry 1": {"purpose": "entry", "is_staff_default": False},
        "entry 2": {"purpose": "entry", "is_staff_default": False},
        "zone": {"purpose": "zone", "is_staff_default": False}
    }
}

def generate_proportional_zones(camera_type, width, height, camera_id=None):
    """Generates highly accurate polygons mapping directly to physical shelves & brands."""
    w, h = int(width), int(height)
    
    if camera_id == "CAM 1 - zone":
        # Based on CAM 1 screenshot: Farmstay/Cosrx left, Face Shop middle, Derma/Minimalist right
        return {
            "FARMSTAY_ZONE": np.array([[0, int(h*0.1)], [int(w*0.15), int(h*0.1)], [int(w*0.15), int(h*0.5)], [0, int(h*0.5)]]),
            "COSRX_ZONE": np.array([[0, int(h*0.5)], [int(w*0.18), int(h*0.5)], [int(w*0.18), h], [0, h]]),
            "THE_FACE_SHOP_ZONE": np.array([[int(w*0.15), int(h*0.1)], [int(w*0.45), int(h*0.1)], [int(w*0.45), int(h*0.6)], [int(w*0.15), int(h*0.6)]]),
            "DERMA_CO_ZONE": np.array([[int(w*0.45), int(h*0.1)], [int(w*0.65), int(h*0.1)], [int(w*0.65), int(h*0.6)], [int(w*0.45), int(h*0.6)]]),
            "MINIMALIST_ZONE": np.array([[int(w*0.65), int(h*0.1)], [int(w*0.85), int(h*0.1)], [int(w*0.85), int(h*0.6)], [int(w*0.65), int(h*0.6)]]),
            "BROWSING_PATH": np.array([[int(w*0.2), int(h*0.6)], [int(w*0.8), int(h*0.6)], [int(w*0.8), h], [int(w*0.2), h]])
        }
    elif camera_id == "CAM 2 - zone":
        # Based on CAM 2 screenshot: Swiss Beauty, Lakme, Faces Canada, Maybelline on the right wall
        return {
            "SWISS_BEAUTY_ZONE": np.array([[int(w*0.4), int(h*0.1)], [int(w*0.55), int(h*0.1)], [int(w*0.55), int(h*0.6)], [int(w*0.4), int(h*0.6)]]),
            "LAKME_ZONE": np.array([[int(w*0.55), int(h*0.1)], [int(w*0.65), int(h*0.1)], [int(w*0.65), int(h*0.6)], [int(w*0.55), int(h*0.6)]]),
            "FACESCANADA_ZONE": np.array([[int(w*0.65), int(h*0.1)], [int(w*0.8), int(h*0.1)], [int(w*0.8), int(h*0.6)], [int(w*0.65), int(h*0.6)]]),
            "MAYBELLINE_ZONE": np.array([[int(w*0.8), int(h*0.1)], [w, int(h*0.1)], [w, int(h*0.8)], [int(w*0.8), int(h*0.8)]]),
            "BROWSING_PATH": np.array([[int(w*0.3), int(h*0.6)], [int(w*0.9), int(h*0.6)], [int(w*0.9), h], [int(w*0.3), h]])
        }
    elif camera_id == "CAM 3 - entry" or camera_type == "entry":
        # Based on CAM 3 screenshot: Door is middle/right, Purple sign is left
        return {
            "WAITING_AREA": np.array([[0, 0], [int(w*0.35), 0], [int(w*0.35), h], [0, h]]),
            "ENTRY_GATE": np.array([[int(w*0.4), int(h*0.2)], [int(w*0.8), int(h*0.2)], [int(w*0.8), int(h*0.6)], [int(w*0.4), int(h*0.6)]]),
            "EXIT_GATE": np.array([[int(w*0.4), int(h*0.6)], [int(w*0.8), int(h*0.6)], [int(w*0.8), h], [int(w*0.4), h]])
        }
    elif camera_id == "CAM 5 - billing" or camera_type == "billing":
        # Based on CAM 5 screenshot: Counter on left, queue on right
        return {
            "BILLING_COUNTER": np.array([[0, int(h*0.3)], [int(w*0.35), int(h*0.3)], [int(w*0.35), h], [0, h]]),
            "BILLING_QUEUE_JOIN": np.array([[int(w*0.35), int(h*0.3)], [int(w*0.7), int(h*0.3)], [int(w*0.7), h], [int(w*0.35), h]])
        }
    else:
        # Generic fallback
        return {
            "LEFT_SHELF": np.array([[0, int(h*0.2)], [int(w*0.3), int(h*0.2)], [int(w*0.3), int(h*0.8)], [0, int(h*0.8)]]),
            "RIGHT_SHELF": np.array([[int(w*0.7), int(h*0.2)], [w, int(h*0.2)], [w, int(h*0.8)], [int(w*0.7), int(h*0.8)]]),
            "BROWSING_PATH": np.array([[int(w*0.3), int(h*0.4)], [int(w*0.7), int(h*0.4)], [int(w*0.7), h], [int(w*0.3), h]])
        }

def get_store_config(store_id):
    """Returns the config for a store."""
    return STORE_CONFIG.get(store_id, {})