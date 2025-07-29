from pathlib import Path
import base64

from app.image_utils import image_to_base64


def test_image_to_base64():
    img = Path(__file__).parent / 'assets' / 'test.jpg'
    result = image_to_base64(str(img))
    assert result.startswith('data:image/jpeg;base64,')
    prefix, encoded = result.split(',', 1)
    decoded = base64.b64decode(encoded)
    assert len(decoded) > 0
