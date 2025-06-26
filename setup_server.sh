#!/bin/bash
# Setup script for NutriScan server
set -e

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # встановлюємо залежності фіксованих версій
python scripts/download_weights.py
python run.py
