import numpy as np

CAMERA_METADATA = {
    "CAM 1": {"purpose": "skincare_browsing_analytics", "is_staff_default": False},
    "CAM 2": {"purpose": "cosmetics_interaction_analytics", "is_staff_default": False},
    "CAM 3": {"purpose": "store_traffic_intelligence", "is_staff_default": False},
    "CAM 4": {"purpose": "operational_analytics", "is_staff_default": True},
    "CAM 5": {"purpose": "conversion_queue_analytics", "is_staff_default": False}
}# ALL COORDINATES ARE FINE-TUNED TO ALIGN PRECISELY WITH YOUR VISUAL OUTPUT
CAMERA_ZONES = {

    # =====================================================
    # CAM 1 — SKINCARE ANALYTICS
    # =====================================================

    "CAM 1": {

        "FARMSTAY_WALL_SHELF": np.array([
            [0, 120],
            [160, 120],
            [160, 420],
            [0, 420]
        ]),

        "THE_FACE_SHOP_SHELF": np.array([
            [165, 115],
            [420, 115],
            [420, 430],
            [165, 430]
        ]),

        "DERMA_CO_SHELF": np.array([
            [425, 110],
            [700, 110],
            [700, 430],
            [425, 430]
        ]),

        "MINIMALIST_SHELF": np.array([
            [705, 105],
            [1040, 105],
            [1040, 430],
            [705, 430]
        ]),

        "AQUALOGICA_SHELF": np.array([
            [1045, 100],
            [1275, 100],
            [1275, 430],
            [1045, 430]
        ]),

        "CENTER_CIRCULAR_PODIUM": np.array([
            [500, 560],
            [760, 560],
            [760, 720],
            [500, 720]
        ]),

        "RIGHT_ISLAND_COUNTER": np.array([
            [840, 480],
            [1120, 480],
            [1120, 760],
            [840, 760]
        ]),

        "CUSTOMER_BROWSING_PATH": np.array([
            [350, 420],
            [1250, 420],
            [1250, 760],
            [350, 760]
        ])
    },

    # =====================================================
    # CAM 2 — COSMETICS ANALYTICS
    # =====================================================

    "CAM 2": {

        "ALPS_WALL_SHELF": np.array([
            [80, 120],
            [250, 120],
            [250, 420],
            [80, 420]
        ]),

        "SWISS_BEAUTY_SHELF": np.array([
            [255, 120],
            [470, 120],
            [470, 420],
            [255, 420]
        ]),

        "LAKME_SHELF": np.array([
            [620, 120],
            [870, 120],
            [870, 420],
            [620, 420]
        ]),

        "FACESCANADA_SHELF": np.array([
            [875, 120],
            [1090, 120],
            [1090, 420],
            [875, 420]
        ]),

        "MAYBELLINE_SHELF": np.array([
            [1095, 120],
            [1275, 120],
            [1275, 420],
            [1095, 420]
        ]),

        "CENTER_GONDOLA_TABLE": np.array([
            [260, 420],
            [650, 420],
            [650, 760],
            [260, 760]
        ]),

        "CUSTOMER_TESTING_AREA": np.array([
            [0, 420],
            [250, 420],
            [250, 760],
            [0, 760]
        ]),

        "COSMETICS_BROWSING_PATH": np.array([
            [650, 420],
            [1280, 420],
            [1280, 760],
            [650, 760]
        ])
    },

    # =====================================================
    # CAM 3 — ENTRY / EXIT ANALYTICS
    # =====================================================

    "CAM 3": {

        "OUTSIDE_WALKWAY": np.array([
            [1020, 0],
            [1280, 0],
            [1280, 760],
            [1020, 760]
        ]),

        "ENTRY_GATE": np.array([
            [720, 240],
            [1040, 240],
            [1040, 470],
            [720, 470]
        ]),

        "EXIT_GATE": np.array([
            [720, 470],
            [1040, 470],
            [1040, 700],
            [720, 700]
        ]),

        "WAITING_AREA": np.array([
            [0, 300],
            [300, 300],
            [300, 760],
            [0, 760]
        ]),

        "PROMOTIONAL_STAND": np.array([
            [250, 0],
            [520, 0],
            [520, 320],
            [250, 320]
        ])
    },

    # =====================================================
    # CAM 4 — STOCKROOM / STAFF
    # =====================================================

    "CAM 4": {

        "PACKAGE_STORAGE": np.array([
            [0, 0],
            [280, 0],
            [280, 300],
            [0, 300]
        ]),

        "STAFF_WORKSPACE": np.array([
            [700, 0],
            [1280, 0],
            [1280, 420],
            [700, 420]
        ]),

        "INVENTORY_SHELF": np.array([
            [250, 150],
            [520, 150],
            [520, 560],
            [250, 560]
        ]),

        "MOVEMENT_AREA": np.array([
            [0, 300],
            [720, 300],
            [720, 760],
            [0, 760]
        ])
    },

    # =====================================================
    # CAM 5 — BILLING / CONVERSION
    # =====================================================

    "CAM 5": {

        "BILLING_COUNTER": np.array([
            [0, 180],
            [220, 180],
            [220, 620],
            [0, 620]
        ]),

        "QUEUE_WAITING_AREA": np.array([
            [220, 120],
            [420, 120],
            [420, 620],
            [220, 620]
        ]),

        "PRODUCT_PICKUP_ZONE": np.array([
            [0, 0],
            [300, 0],
            [300, 170],
            [0, 170]
        ]),

        "DISPLAY_STAND": np.array([
            [260, 520],
            [470, 520],
            [470, 760],
            [260, 760]
        ]),

        "BACKROOM_ACCESS": np.array([
            [720, 120],
            [1280, 120],
            [1280, 760],
            [720, 760]
        ])
    }
}