from pipeline.dwell_time_analysis import calculate_dwell_time
from pipeline.entry_exit_counter import get_zone_event_type

def test_dwell_time():
    assert calculate_dwell_time(150, 0, 30) == 5.0

def test_zone_event_type():
    assert get_zone_event_type("billing", "CUSTOMER_POS_QUEUE") == "BILLING_QUEUE_JOIN"
    assert get_zone_event_type("entry", "GLASS_ENTRY_DOORWAY") == "ENTRY"
    assert get_zone_event_type("zone", "ANY_OTHER_ZONE") == "ZONE_ENTER"
    assert get_zone_event_type("CAM 1", "SOME_ZONE") == "ZONE_ENTER"
