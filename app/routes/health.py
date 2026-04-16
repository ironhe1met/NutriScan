from fastapi import APIRouter

from ..providers.registry import list_providers

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "providers": list_providers(),
    }
