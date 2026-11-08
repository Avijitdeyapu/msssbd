from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_admin
from ..models import BloodDonor, Member, Message, News, Transaction, Tribute, User, Volunteer
from ..schemas import (MemberIn, MemberOut, NewsIn, NewsOut, StatusIn, TxIn, TxOut, UserIn,
                       UserOut)
from ..security import hash_password

# সব অ্যাডমিন রুটে লগইন লাগবে
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_user)])

MODERATED = {"donors": BloodDonor, "volunteers": Volunteer, "tributes": Tribute}


def _dict(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _get(db: Session, Model, item_id: int):
    obj = db.get(Model, item_id)
    if not obj:
        raise HTTPException(404, "পাওয়া যায়নি")
    return obj


# ---------- অনুমোদন: দাতা / স্বেচ্ছাসেবক / শ্রদ্ধাঞ্জলি ----------
@router.get("/review/{kind}")
def review_list(kind: str, status: Optional[str] = "pending", db: Session = Depends(get_db)):
    Model = MODERATED.get(kind)
    if not Model:
        raise HTTPException(404, "অজানা তালিকা")
    stmt = select(Model).order_by(Model.id.desc()).limit(300)
    if status in ("pending", "approved", "rejected"):
        stmt = stmt.where(Model.status == status)
    return [_dict(o) for o in db.scalars(stmt).all()]


@router.patch("/review/{kind}/{item_id}")
def review_set(kind: str, item_id: int, data: StatusIn, db: Session = Depends(get_db)):
    Model = MODERATED.get(kind)
    if not Model:
        raise HTTPException(404, "অজানা তালিকা")
    obj = _get(db, Model, item_id)
    obj.status = data.status
    db.commit()
    return _dict(obj)


@router.delete("/review/{kind}/{item_id}", status_code=204)
def review_delete(kind: str, item_id: int, db: Session = Depends(get_db)):
    Model = MODERATED.get(kind)
    if not Model:
        raise HTTPException(404, "অজানা তালিকা")
    db.delete(_get(db, Model, item_id))
    db.commit()


# ---------- যোগাযোগের বার্তা ----------
@router.get("/messages")
def messages(db: Session = Depends(get_db)):
    return [_dict(o) for o in db.scalars(select(Message).order_by(Message.id.desc()).limit(300)).all()]


@router.patch("/messages/{item_id}/read")
def message_read(item_id: int, db: Session = Depends(get_db)):
    m = _get(db, Message, item_id)
    m.is_read = True
    db.commit()
    return _dict(m)


@router.delete("/messages/{item_id}", status_code=204)
def message_delete(item_id: int, db: Session = Depends(get_db)):
    db.delete(_get(db, Message, item_id))
    db.commit()


# ---------- সাধারণ CRUD: সংবাদ, কমিটি (সব স্টাফ) ও আর্থিক হিসাব (শুধু অ্যাডমিন) ----------
def crud(path: str, Model, In, Out, guard=None):
    deps = [Depends(guard)] if guard else []

    @router.get(f"/{path}", response_model=list[Out], dependencies=deps)
    def list_all(db: Session = Depends(get_db)):
        return db.scalars(select(Model).order_by(Model.id.desc()).limit(500)).all()

    @router.post(f"/{path}", response_model=Out, status_code=201, dependencies=deps)
    def create(data: In, db: Session = Depends(get_db)):
        obj = Model(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.put(f"/{path}/{{item_id}}", response_model=Out, dependencies=deps)
    def update(item_id: int, data: In, db: Session = Depends(get_db)):
        obj = _get(db, Model, item_id)
        for k, v in data.model_dump().items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete(f"/{path}/{{item_id}}", status_code=204, dependencies=deps)
    def remove(item_id: int, db: Session = Depends(get_db)):
        db.delete(_get(db, Model, item_id))
        db.commit()


crud("news", News, NewsIn, NewsOut)
crud("committee", Member, MemberIn, MemberOut)
crud("finance", Transaction, TxIn, TxOut, guard=require_admin)


# ---------- ব্যবহারকারী (শুধু অ্যাডমিন) ----------
@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(data: UserIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "এই ইমেইল আগে থেকেই আছে")
    u = User(email=email, name=data.name, role=data.role, password_hash=hash_password(data.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()
