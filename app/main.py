from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import uvicorn

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

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
