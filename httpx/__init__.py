from fastapi.testclient import TestClient

class AsyncClient:
    def __init__(self, app=None, base_url=None):
        self.client = TestClient(app)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, url, files=None):
        return self.client.post(url, files=files)
