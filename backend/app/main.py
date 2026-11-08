from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS
from .db import Base, engine
from .routers import admin, auth, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="এম. সুমন স্মৃতি সংঘ API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


app.include_router(public.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"ok": True}


# অ্যাডমিন প্যানেল: http://127.0.0.1:8000/admin/
_ADMIN = Path(__file__).resolve().parent.parent / "admin"
if _ADMIN.exists():
    app.mount("/admin", StaticFiles(directory=_ADMIN, html=True), name="admin")
