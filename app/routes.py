import json
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

from app.services.image_utils import image_to_base64
from app.services.openai_client import analyze_image_base64

router = APIRouter()

UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/analyze/")
async def analyze_image(image: UploadFile = File(...)):
    # Зберегти файл тимчасово
    ext = Path(image.filename).suffix
    temp_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / temp_filename

    with file_path.open("wb") as f:
        f.write(await image.read())

    # Конвертація в base64
    image_base64 = image_to_base64(str(file_path))

    # Аналіз через OpenAI
    result = analyze_image_base64(image_base64)

    # Спроба обробити JSON
    parsed_json = None
    if isinstance(result, str):
        try:
            # Якщо відповідь GPT містить Markdown-блок "```json ... ```"
            result_clean = result.strip().removeprefix("```json").removesuffix("```")
            parsed_json = json.loads(result_clean)
        except Exception as e:
            return JSONResponse(content={
                "raw_response": result,
                "error": f"❌ Не вдалося розпарсити JSON: {str(e)}"
            })

    # Очистити тимчасовий файл
    file_path.unlink(missing_ok=True)

    return JSONResponse(content=parsed_json or {"raw_response": result})
