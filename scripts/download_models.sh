#!/bin/bash
set -e

mkdir -p models/qwen2.5-vl-7b-instruct

echo "⬇️ Завантаження Qwen2.5-VL-7B-Instruct..."

# Індекс шардів
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/model.safetensors.index.json

# 5 файлів ваг (shards)
for i in {1..5}; do
  wget -c -P models/qwen2.5-vl-7b-instruct \
    https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/model-$(printf "%05d" $i)-of-00005.safetensors
done

# Конфіг та токенайзер
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/config.json
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/tokenizer.json
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/merges.txt
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/vocab.json

# Додатковий файл для ImageProcessor
wget -c -P models/qwen2.5-vl-7b-instruct \
  https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/preprocessor_config.json

echo "✅ Завантаження Qwen2.5-VL-7B-Instruct завершено"
