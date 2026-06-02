#!/bin/bash
# One command to process all clips → events
echo "Starting Detection Pipeline..."
python pipeline/event_generator.py
echo "Detection Pipeline Finished."
