from fastapi import APIRouter, UploadFile, File
from app.utils.file_utils import save_image

router = APIRouter()

@router.post("/upload/")
async def upload_image(image: UploadFile = File(...)):
    file_path = save_image(image)
    return {"message": "Image received", "filename": file_path}
