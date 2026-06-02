def calculate_dwell_time(frame_count, entry_frame, fps):
    return (frame_count - entry_frame) / fps
