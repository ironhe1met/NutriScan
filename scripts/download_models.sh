#!/bin/bash
set -e

mkdir -p models

echo "⬇️ Завантаження моделі EfficientNet-B0 (Food-101)..."
wget -O models/classifier.pth \
  https://huggingface.co/dwililiya/food101-model-classification/resolve/main/best_model.pth

echo "✅ Завантаження завершено"
