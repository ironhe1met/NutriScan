# app/api/routes.py

from fastapi import APIRouter, UploadFile, File
from app.models.detector import IngredientDetector
from app.services.nutrition import NutritionService
import tempfile

router = APIRouter()

detector = IngredientDetector()
nutrition = NutritionService()

@router.post("/detect/")
async def detect_ingredients(image: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await image.read())
        tmp_path = tmp.name

    raw = detector.detect(tmp_path)
    enriched = nutrition.enrich_ingredients(raw["ingredients"])

    return enriched
