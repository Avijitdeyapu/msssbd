from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL, IS_POSTGRES

if IS_POSTGRES:
    # prepare_threshold=None: Supabase এর pooler এর সাথে নিরাপদে কাজ করে
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=5,
                           connect_args={"prepare_threshold": None})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def secure_tables() -> None:
    """Supabase এ টেবিল ডিফল্টে পাবলিক Data API দিয়ে পড়া যায়। RLS চালু করলে
    শুধু আমাদের সার্ভার (সরাসরি DB সংযোগ) ডাটা পড়তে পারে, বাইরের কেউ পারে না।"""
    if not IS_POSTGRES:
        return
    with engine.begin() as conn:
        for name in Base.metadata.tables:  # নামগুলো আমাদের নিজের মডেল থেকে
            conn.execute(text(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY'))
