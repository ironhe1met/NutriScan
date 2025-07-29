from pathlib import Path
import base64

def image_to_base64(image_path: str) -> str:
    """Зчитує зображення і повертає base64-рядок з префіксом для GPT-4o."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {image_path}")

    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/jpeg;base64,{b64}"
