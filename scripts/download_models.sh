#!/bin/bash
mkdir -p models
mkdir -p app/assets

echo "⬇️ Завантаження classifier.pt..."
wget -O models/classifier.pt https://huggingface.co/dwililiya/food101-model-classification/resolve/main/pytorch_model.bin

echo "⬇️ Завантаження labels_food101.json..."
wget -O app/assets/labels_food101.json https://huggingface.co/dwililiya/food101-model-classification/resolve/main/label2id.json

echo "✅ Завантаження завершено"