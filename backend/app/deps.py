import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    uid = decode_token(token)
    user = db.get(User, uid) if uid else None
    if not user or not user.is_active:
        raise HTTPException(401, "লগইন করুন", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "এই কাজের অনুমতি শুধু অ্যাডমিনের")
    return user


_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(max_hits: int, per_seconds: int = 3600):
    """সহজ রেট লিমিট (একটি সার্ভার প্রসেসের জন্য)। প্রক্সির পেছনে চালালে README দেখুন।"""

    def dep(request: Request) -> None:
        key = f"{request.url.path}:{request.client.host if request.client else 'x'}"
        q, t = _hits[key], time.time()
        while q and t - q[0] > per_seconds:
            q.popleft()
        if len(q) >= max_hits:
            raise HTTPException(429, "অনেকবার চেষ্টা হয়েছে, কিছুক্ষণ পরে আবার চেষ্টা করুন")
        q.append(t)

    return dep
