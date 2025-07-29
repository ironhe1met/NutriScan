from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import uvicorn

from .image_utils import image_to_base64
from .openai_client import analyze_image_base64
from .parser import parse_openai_response

app = FastAPI()

UPLOAD_DIR = Path('tmp')
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post('/upload/')
async def upload_image(image: UploadFile = File(...)):
    file_location = UPLOAD_DIR / image.filename
    with open(file_location, 'wb') as f:
        content = await image.read()
        f.write(content)
    return {"message": "Image received", "filename": image.filename}


@app.post('/analyze/')
async def analyze_image(image: UploadFile = File(...)):
    """Accept an image, send to GPT-4 Vision and return parsed JSON."""
    file_location = UPLOAD_DIR / image.filename
    with open(file_location, 'wb') as f:
        content = await image.read()
        f.write(content)

    img_b64 = image_to_base64(str(file_location))
    raw = analyze_image_base64(img_b64)
    result = parse_openai_response(raw["raw_response"])
    return result

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
