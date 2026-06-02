import cv2
import numpy as np
import supervision as sv
import json
import os
import uuid
from datetime import datetime

from pipeline.camera_zones import CAMERA_ZONES, CAMERA_METADATA
from pipeline.detect_people import load_detector
from pipeline.track_people import load_tracker
from pipeline.dwell_time_analysis import calculate_dwell_time
from pipeline.entry_exit_counter import get_zone_event_type
from pipeline.heatmap_generator import HeatmapGenerator
from pipeline.anomaly_detector import AnomalyDetector
from pipeline.emit import flush_events

API_INGEST_URL = "http://127.0.0.1:8000/events/ingest"
STORE_ID = "STORE_BLR_002"

def main():
    print("Loading YOLOv8 model...")
    model = load_detector()

    videos_dir = "data/videos"
    supported_formats = (".mp4", ".avi", ".mov")

    video_files = [
        f for f in os.listdir(videos_dir)
        if f.lower().endswith(supported_formats)
    ]

    if not video_files:
        print("No videos found.")
        return

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    colors = [sv.Color(255, 0, 0), sv.Color(0, 255, 0), sv.Color(0, 0, 255), sv.Color(255, 255, 0), sv.Color(255, 0, 255), sv.Color(0, 255, 255), sv.Color(255, 165, 0)]

    event_batch = []
    
    def emit_batch():
        nonlocal event_batch
        flush_events(event_batch, API_INGEST_URL)
        event_batch = []

    heatmap_gen = HeatmapGenerator()
    anomaly_det = AnomalyDetector()

    for video_file in video_files:
        input_video_path = os.path.join(videos_dir, video_file)
        camera_id = os.path.splitext(video_file)[0]

        print("\n" + "=" * 60)
        print(f"PROCESSING CAMERA: {camera_id}")
        print("=" * 60)

        if camera_id not in CAMERA_ZONES:
            print(f"No zones configured for {camera_id}")
            continue

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            print(f"Cannot open video: {video_file}")
            continue

        orig_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        orig_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        scale_percent = 80
        scale_factor = scale_percent / 100.0
        frame_width = int(orig_width * scale_factor)
        frame_height = int(orig_height * scale_factor)

        output_path = f"data/outputs/zone_tracking_output_{camera_id}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        zone_polygons = CAMERA_ZONES[camera_id]
        metadata = CAMERA_METADATA.get(camera_id, {"purpose": "default", "is_staff_default": False})
        is_staff_default = metadata["is_staff_default"]

        polygon_zones = {}
        polygon_annotators = {}

        for idx, (zone_name, polygon) in enumerate(zone_polygons.items()):
            scaled_polygon = (polygon * scale_factor).astype(np.int32)
            polygon_zones[zone_name] = sv.PolygonZone(polygon=scaled_polygon, triggering_anchors=(sv.Position.BOTTOM_CENTER,))
            polygon_annotators[zone_name] = sv.PolygonZoneAnnotator(zone=polygon_zones[zone_name], color=colors[idx % len(colors)], thickness=2, text_thickness=1, text_scale=0.4)

        tracker = load_tracker()
        current_person_zones = {}
        person_entry_frames = {}
        frame_count = 0
        session_counters = {}

        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                frame = cv2.resize(frame, (frame_width, frame_height))
                frame_count += 1

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
                    vis_id = f"VIS_{camera_id}_{tracker_id}"

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
                                "store_id": STORE_ID,
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
                            event_type = get_zone_event_type(camera_id, detected_zone)

                            session_counters[tracker_id] += 1
                            event_batch.append({
                                "event_id": str(uuid.uuid4()),
                                "store_id": STORE_ID,
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
                
                annotated_frame = heatmap_gen.generate(annotated_frame, detections)

                cv2.imshow(f"Tracking - {camera_id}", annotated_frame)
                out.write(annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Error processing {camera_id}: {e}")
        finally:
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            emit_batch()

    print("\n" + "=" * 60 + "\nALL CAMERAS PROCESSED SUCCESSFULLY\n" + "=" * 60)

if __name__ == "__main__":
    main()
