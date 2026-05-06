import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .auth import require_admin, NotAuthenticated, not_authenticated_handler
from .config import settings
from .db import init_db
from .routes import analyze, health, stats, history, login


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
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
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=60 * 60 * 24 * 7,  # 7 days
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(NotAuthenticated, not_authenticated_handler)

# Public routes
app.include_router(analyze.router)
app.include_router(health.router)
app.include_router(login.router)

# Protected routes
app.include_router(stats.router, dependencies=[Depends(require_admin)])
app.include_router(history.router, dependencies=[Depends(require_admin)])

@app.get("/")
async def root(_=Depends(require_admin)):
    return RedirectResponse(url="/stats/dashboard", status_code=302)


# Test page (protected)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/test")
    async def test_page(_=Depends(require_admin)):
        return FileResponse(str(static_dir / "index.html"))
