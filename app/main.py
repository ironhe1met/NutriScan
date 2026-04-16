import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .auth import require_admin
from .db import init_db
from .routes import analyze, health, stats, history


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logging.getLogger("nutriscan").info("NutriScan v2 started")
    yield
    logging.getLogger("nutriscan").info("NutriScan v2 shutting down")


app = FastAPI(
    title="NutriScan API",
    description="AI food analysis — multi-provider (Anthropic, OpenAI, Google)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (mobile apps use these)
app.include_router(analyze.router)
app.include_router(health.router)

# Protected routes (admin panel)
app.include_router(stats.router, dependencies=[Depends(require_admin)])
app.include_router(history.router, dependencies=[Depends(require_admin)])

# Test page (protected)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root(_=Depends(require_admin)):
        return FileResponse(str(static_dir / "index.html"))
