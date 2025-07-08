from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.models.detector import IngredientDetector
import shutil
import tempfile

router = APIRouter()

detector = IngredientDetector("models/yolov8x-seg.pt")

@router.post("/detect/")
async def detect_ingredients(image: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(image.file, tmp)
        tmp_path = tmp.name

    result = detector.detect(tmp_path)
    return JSONResponse(content={"ingredients": result})
