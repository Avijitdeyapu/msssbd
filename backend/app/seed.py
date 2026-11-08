"""প্রথম অ্যাডমিন বানানোর স্ক্রিপ্ট:  python -m app.seed"""
from getpass import getpass

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import User
from .security import hash_password

Base.metadata.create_all(engine)
email = input("অ্যাডমিন ইমেইল: ").strip().lower()
name = input("নাম: ").strip()
pw = getpass("পাসওয়ার্ড (কমপক্ষে ১০ অক্ষর): ")
if len(pw) < 10 or not email or not name:
    raise SystemExit("ইমেইল, নাম দিন এবং পাসওয়ার্ড কমপক্ষে ১০ অক্ষর হতে হবে।")
with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == email)):
        raise SystemExit("এই ইমেইলে ইউজার আগে থেকেই আছে।")
    db.add(User(email=email, name=name, role="admin", password_hash=hash_password(pw)))
    db.commit()
print("অ্যাডমিন তৈরি হয়েছে। এবার: uvicorn app.main:app --reload")
