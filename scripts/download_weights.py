import requests
from pathlib import Path

from nutriscan.models.classifier import MODEL_URL as CLASSIFIER_URL
from nutriscan.models.detector import WEIGHTS_URL as DETECTOR_URL

WEIGHTS_DIR = Path("weights")
WEIGHTS_DIR.mkdir(exist_ok=True)


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"{dest} вже існує, пропускаємо завантаження")
        return
    print(f"Завантаження {url} до {dest}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)


def main() -> None:
    download(CLASSIFIER_URL, WEIGHTS_DIR / "classifier.pt")
    download(DETECTOR_URL, WEIGHTS_DIR / "detector.pt")


if __name__ == "__main__":
    main()
