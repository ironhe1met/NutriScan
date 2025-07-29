import os
import io
import json
from unittest.mock import patch, MagicMock

import pytest

from app.openai_client import analyze_image_base64


def test_analyze_image_base64(monkeypatch):
    os.environ['OPENAI_API_KEY'] = 'test'
    dummy_base64 = 'data:image/jpeg;base64,dGVzdA=='
    fake_resp = {"choices": [{"message": {"content": "sample"}}]}
    fake_file = io.BytesIO(json.dumps(fake_resp).encode())
    mock = MagicMock()
    mock.__enter__.return_value = fake_file
    mock.__exit__.return_value = False
    with patch('urllib.request.urlopen', return_value=mock):
        result = analyze_image_base64(dummy_base64)
    assert result == {"raw_response": "sample"}

