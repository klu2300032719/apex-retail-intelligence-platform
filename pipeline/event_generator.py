import cv2
import numpy as np
import supervision as sv
import json
import os
import uuid
import argparse
from datetime import datetime

from pipeline.camera_zones import get_store_config, generate_proportional_zones
from pipeline.detect_people import load_detector
from pipeline.track_people import load_tracker
from pipeline.dwell_time_analysis import calculate_dwell_time
from pipeline.entry_exit_counter import get_zone_event_type
from pipeline.heatmap_generator import HeatmapGenerator
from pipeline.emit import flush_events

API_INGEST_URL = "http://127.0.0.1:8000/events/ingest"

def process_camera(model, store_id, camera_file, camera_id, input_video_path, config, dev_mode=False):
    print("\n" + "=" * 60)
    print(f"PROCESSING CAMERA: {store_id} | {camera_id}{' [DEV MODE ENABLED]' if dev_mode else ''}")
    print("=" * 60)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Cannot open video: {input_video_path}")
        return

    orig_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    orig_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    scale_percent = 80
    scale_factor = scale_percent / 100.0
    frame_width = int(orig_width * scale_factor)
    frame_height = int(orig_height * scale_factor)

    os.makedirs("data/output", exist_ok=True)
    output_path = f"data/output/{store_id}_{camera_id}_tracking.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    camera_purpose = config.get("purpose", "zone")
    is_staff_default = config.get("is_staff_default", False)
    
    # Generate generic zones if none provided in config
    if "zones" in config:
        raw_zones = config["zones"]
    else:
        raw_zones = generate_proportional_zones(camera_purpose, orig_width, orig_height, camera_id)

    polygon_zones = {}
    polygon_annotators = {}
    colors = [sv.Color(255, 0, 0), sv.Color(0, 255, 0), sv.Color(0, 0, 255), sv.Color(255, 255, 0), sv.Color(255, 0, 255)]

    for idx, (zone_name, polygon) in enumerate(raw_zones.items()):
        scaled_polygon = (polygon * scale_factor).astype(np.int32)
        polygon_zones[zone_name] = sv.PolygonZone(polygon=scaled_polygon, triggering_anchors=(sv.Position.BOTTOM_CENTER,))
        polygon_annotators[zone_name] = sv.PolygonZoneAnnotator(zone=polygon_zones[zone_name], color=colors[idx % len(colors)], thickness=2, text_thickness=1, text_scale=0.4)

    tracker = load_tracker()
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    heatmap_gen = HeatmapGenerator()

    current_person_zones = {}
    person_entry_frames = {}
    frame_count = 0
    session_counters = {}
    event_batch = []

    def emit_batch():
        nonlocal event_batch
        if event_batch:
            flush_events(event_batch, API_INGEST_URL)
            event_batch = []

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            if dev_mode and frame_count > (fps * 60):  # Stop after 60 seconds in dev mode
                print(f"--> Dev mode: Stopping early at 60 seconds for {camera_id}")
                break
                
            frame_count += 1
            if dev_mode and frame_count % 3 != 0:
                continue  # Skip 2 out of 3 frames in dev mode for speed

            frame = cv2.resize(frame, (frame_width, frame_height))

            results = model(frame, classes=[0], conf=0.35, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = tracker.update_with_detections(detections)

            labels = []
            zone_results = {z_name: z.trigger(detections=detections) for z_name, z in polygon_zones.items()}

            for i in range(len(detections)):
                tracker_id = detections.tracker_id[i] if detections.tracker_id is not None else None
                if tracker_id is None:
                    continue

                tracker_id = int(tracker_id)
                confidence = float(detections.confidence[i])
                vis_id = f"VIS_{store_id}_{camera_id}_{tracker_id}"

                detected_zone = None
                for zone_name in polygon_zones.keys():
                    if zone_results[zone_name][i]:
                        detected_zone = zone_name
                        break

                previous_zone = current_person_zones.get(tracker_id)
                
                if tracker_id not in session_counters:
                    session_counters[tracker_id] = 1

                if previous_zone != detected_zone:
                    if previous_zone is not None:
                        entry_frame = person_entry_frames.get((tracker_id, previous_zone), frame_count)
                        dwell_time = calculate_dwell_time(frame_count, entry_frame, fps)
                        
                        session_counters[tracker_id] += 1
                        event_batch.append({
                            "event_id": str(uuid.uuid4()),
                            "store_id": store_id,
                            "camera_id": camera_id,
                            "visitor_id": vis_id,
                            "event_type": "ZONE_EXIT",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "zone_id": previous_zone,
                            "dwell_ms": int(dwell_time * 1000),
                            "is_staff": is_staff_default,
                            "confidence": round(confidence, 2),
                            "metadata": { "session_seq": session_counters[tracker_id] }
                        })

                    if detected_zone is not None:
                        person_entry_frames[(tracker_id, detected_zone)] = frame_count
                        event_type = get_zone_event_type(camera_purpose, detected_zone)

                        session_counters[tracker_id] += 1
                        event_batch.append({
                            "event_id": str(uuid.uuid4()),
                            "store_id": store_id,
                            "camera_id": camera_id,
                            "visitor_id": vis_id,
                            "event_type": event_type,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "zone_id": detected_zone,
                            "dwell_ms": 0,
                            "is_staff": is_staff_default,
                            "confidence": round(confidence, 2),
                            "metadata": { "session_seq": session_counters[tracker_id], "queue_depth": 0 if event_type == "BILLING_QUEUE_JOIN" else None }
                        })

                    current_person_zones[tracker_id] = detected_zone
                    
                    if len(event_batch) >= 100:
                        emit_batch()

                labels.append(f"ID:{tracker_id}")

            annotated_frame = frame.copy()
            for zone_name, annotator in polygon_annotators.items():
                annotated_frame = annotator.annotate(scene=annotated_frame, label=zone_name)

            annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
            
            # For robustness, try rendering heatmap overlay
            try:
                annotated_frame = heatmap_gen.generate(annotated_frame, detections)
            except Exception:
                pass

            if out is not None:
                out.write(annotated_frame)

    except Exception as e:
        print(f"Error processing {camera_id}: {e}")
    finally:
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        emit_batch()


def main():
    parser = argparse.ArgumentParser(description="YOLOv8 Detection Pipeline")
    parser.add_argument("--dev-mode", action="store_true", help="Run in fast mode (60s limit, frame skip, no video output)")
    args = parser.parse_args()

    print("Loading YOLOv8 model...")
    model = load_detector()

    base_videos_dir = "data/videos"
    supported_formats = (".mp4", ".avi", ".mov")

    if not os.path.exists(base_videos_dir):
        print(f"Directory not found: {base_videos_dir}")
        return

    # Scan for store directories
    store_dirs = [d for d in os.listdir(base_videos_dir) if os.path.isdir(os.path.join(base_videos_dir, d))]

    if not store_dirs:
        print(f"No store directories found inside {base_videos_dir}.")
        return

    for store_id in store_dirs:
        store_path = os.path.join(base_videos_dir, store_id)
        video_files = [f for f in os.listdir(store_path) if f.lower().endswith(supported_formats)]

        store_config = get_store_config(store_id)
        
        for video_file in video_files:
            input_video_path = os.path.join(store_path, video_file)
            camera_id = os.path.splitext(video_file)[0]
            
            # Infer purpose roughly if not in config
            camera_config = store_config.get(camera_id, {})
            if "purpose" not in camera_config:
                c_lower = camera_id.lower()
                if "entry" in c_lower: camera_config["purpose"] = "entry"
                elif "billing" in c_lower: camera_config["purpose"] = "billing"
                else: camera_config["purpose"] = "zone"
                camera_config["is_staff_default"] = False

            process_camera(model, store_id, video_file, camera_id, input_video_path, camera_config, args.dev_mode)

    print("\n" + "=" * 60 + "\nALL STORES AND CAMERAS PROCESSED SUCCESSFULLY\n" + "=" * 60)

if __name__ == "__main__":
    main()
