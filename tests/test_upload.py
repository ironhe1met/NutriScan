import pytest
from httpx import AsyncClient
from pathlib import Path

from app.main import app

@pytest.mark.asyncio
async def test_upload(tmp_path):
    image_path = Path(__file__).parent / 'assets' / 'test.jpg'
    async with AsyncClient(app=app, base_url='http://test') as ac:
        with image_path.open('rb') as f:
            response = await ac.post('/upload/', files={'image': ('test.jpg', f, 'image/jpeg')})
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == 'Image received'
    assert data['filename'] == 'test.jpg'
    saved_file = Path('tmp') / 'test.jpg'
    assert saved_file.exists()
    saved_file.unlink()