from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.image_utils import image_to_base64
from app.services.openai_client import analyze_image_base64
from app.logger import logger
from pathlib import Path
import uuid

router = APIRouter()

@router.post("/analyze/")
async def analyze_image(image: UploadFile = File(...)):
    try:
        # Сохранение во временный файл
        ext = Path(image.filename).suffix or ".jpg"
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        file_path = tmp_dir / f"{uuid.uuid4().hex}{ext}"

        with open(file_path, "wb") as f:
            f.write(await image.read())

        logger.info(f"🖼️ Получено изображение: {file_path.name}")

        # Конвертация в base64
        image_b64 = image_to_base64(str(file_path))

        # Отправка в OpenAI
        result = analyze_image_base64(image_b64)

        logger.info("✅ Ответ от GPT получен")

        # Удаление временного файла
        file_path.unlink(missing_ok=True)

        if not isinstance(result, dict):
            raise ValueError("Ожидался словарь от OpenAI")

        return {"data": result, "error": None}

    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
