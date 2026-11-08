import os
from pathlib import Path


def _load_env() -> None:
    p = Path(__file__).resolve().parent.parent / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY .env ফাইলে দিন (কমপক্ষে ৩২ অক্ষর)। README দেখুন।")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./msss.db").strip()
# Supabase দেয় postgresql:// (বা postgres://); SQLAlchemy তে psycopg ড্রাইভার নাম লাগে
for _p in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(_p):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(_p):]
        break
IS_POSTGRES = DATABASE_URL.startswith("postgresql")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
TOKEN_MINUTES = int(os.environ.get("TOKEN_MINUTES", "480"))
DONATION_GAP_DAYS = 90  # শেষ রক্তদানের পর কত দিন পর আবার দিতে পারবেন
