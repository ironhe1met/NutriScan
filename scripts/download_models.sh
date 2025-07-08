#!/bin/bash
set -e

mkdir -p models

echo "⬇️ Завантаження моделі YOLOv8x-seg..."
wget -O models/yolov8x-seg.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x-seg.pt

echo "✅ Завантаження завершено"
