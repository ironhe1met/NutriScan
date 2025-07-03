from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from PIL import Image
import io

from .models.classifier import FoodClassifier
from .models.detector import IngredientDetector
from .api.openfoodfacts import get_nutrition
from .utils.weight_estimation import estimate_weight

app = FastAPI()
classifier = FoodClassifier()
detector = IngredientDetector()

classifier.load()
detector.load()


class IngredientResult(BaseModel):
    name: str
    weight: float | None = None
    calories: float | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None


class AnalysisSummary(BaseModel):
    dish_type: str | None = None
    total_weight: float | None = None
    total_calories: float | None = None


class AnalysisResponse(BaseModel):
    ingredients: list[IngredientResult]
    summary: AnalysisSummary


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(image: UploadFile = File(...)):
    data = await image.read()
    img = Image.open(io.BytesIO(data))

    classification = classifier.predict(img)
    detections = detector.detect(img)

    results: list[IngredientResult] = []
    total_weight = 0.0
    total_calories = 0.0

    for det in detections:
        name = det.get("label", "ingredient")
        area = det.get("area", 0)
        weight = estimate_weight(area)
        info = await get_nutrition(name) or {}
        calories = info.get("calories")
        if calories is not None:
            total_calories += (calories / 100) * weight
        total_weight += weight
        results.append(
            IngredientResult(
                name=name,
                weight=weight,
                calories=calories,
                proteins=info.get("proteins"),
                fats=info.get("fats"),
                carbs=info.get("carbs"),
            )
        )

    return AnalysisResponse(
        ingredients=results,
        summary=AnalysisSummary(
            dish_type=classification,
            total_weight=total_weight,
            total_calories=total_calories,
        ),
    )
