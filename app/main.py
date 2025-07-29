from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path

app = FastAPI()
TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)

@app.post("/upload/")
async def upload_image(image: UploadFile = File(...)):
    file_path = TMP_DIR / image.filename
    with file_path.open("wb") as buffer:
        buffer.write(await image.read())
    return JSONResponse(content={"message": "Image received", "filename": image.filename})
