# app/api/routes.py

from fastapi import APIRouter, UploadFile, File
from app.models.qwen_detector import QwenFoodDetector as IngredientDetector
from app.services.nutrition import NutritionService
import tempfile

router = APIRouter()

# викликаємо новий детектор
detector = IngredientDetector(model_dir="models/qwen2.5-vl-7b-instruct")
nutrition = NutritionService()

@router.post("/detect/")
async def detect_ingredients(image: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await image.read())
        tmp_path = tmp.name

    # QwenFoodDetector.detect повертає dict {"ingredients": [...]}
    raw = detector.detect(tmp_path)
    enriched = nutrition.enrich_ingredients(raw["ingredients"])
    return enriched
