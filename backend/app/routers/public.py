from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import DONATION_GAP_DAYS
from ..db import get_db
from ..deps import rate_limit
from ..models import BloodDonor, Member, Message, News, Transaction, Tribute, Volunteer
from ..schemas import (DonorIn, DonorPublic, MemberOut, MessageIn, NewsPublic, TributeIn,
                       TributePublic, TxOut, VolunteerIn)

router = APIRouter(prefix="/api", tags=["public"])
limit_forms = Depends(rate_limit(20))
GROUPS = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}


def _save(db: Session, obj):
    db.add(obj)
    db.commit()


# ---------- রক্তদাতা ----------
@router.get("/donors", response_model=list[DonorPublic])
def donors(blood_group: Optional[str] = None, q: Optional[str] = Query(None, max_length=40),
           available_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(BloodDonor).where(BloodDonor.status == "approved", BloodDonor.consent.is_(True))
    if blood_group:
        # URL এ "+" স্পেস হয়ে আসতে পারে, তাই ঠিক করে নিচ্ছি
        bg = blood_group.replace(" ", "+").replace("−", "-").strip().upper()
        if bg not in GROUPS:
            return []
        stmt = stmt.where(BloodDonor.blood_group == bg)
    if q:
        stmt = stmt.where(or_(BloodDonor.name.contains(q, autoescape=True),
                              BloodDonor.area.contains(q, autoescape=True)))
    out = []
    for d in db.scalars(stmt.order_by(BloodDonor.name)).all():
        ok = d.last_donation is None or (date.today() - d.last_donation).days >= DONATION_GAP_DAYS
        if available_only and not ok:
            continue
        out.append(DonorPublic(id=d.id, name=d.name, blood_group=d.blood_group,
                               area=d.area, phone=d.phone, available=ok))
    return out


@router.post("/donors", status_code=201, dependencies=[limit_forms])
def add_donor(data: DonorIn, db: Session = Depends(get_db)):
    _save(db, BloodDonor(**data.model_dump(), status="pending"))
    return {"message": "ধন্যবাদ! যাচাইয়ের পর আপনার নাম তালিকায় যুক্ত হবে।"}


# ---------- স্বেচ্ছাসেবক ----------
@router.post("/volunteers", status_code=201, dependencies=[limit_forms])
def add_volunteer(data: VolunteerIn, db: Session = Depends(get_db)):
    d = data.model_dump()
    d["interests"] = ",".join(d["interests"])
    _save(db, Volunteer(**d, status="pending"))
    return {"message": "ধন্যবাদ! আপনার আবেদন পাওয়া গেছে, আমরা যোগাযোগ করব।"}


# ---------- যোগাযোগ ----------
@router.post("/messages", status_code=201, dependencies=[limit_forms])
def add_message(data: MessageIn, db: Session = Depends(get_db)):
    _save(db, Message(**data.model_dump()))
    return {"message": "ধন্যবাদ! আপনার বার্তা পাওয়া গেছে।"}


# ---------- শ্রদ্ধাঞ্জলি ----------
@router.get("/tributes", response_model=list[TributePublic])
def tributes(db: Session = Depends(get_db)):
    return db.scalars(select(Tribute).where(Tribute.status == "approved")
                      .order_by(Tribute.id.desc()).limit(100)).all()


@router.post("/tributes", status_code=201, dependencies=[limit_forms])
def add_tribute(data: TributeIn, db: Session = Depends(get_db)):
    _save(db, Tribute(**data.model_dump(), status="pending"))
    return {"message": "ধন্যবাদ! অনুমোদনের পর আপনার শ্রদ্ধাঞ্জলি দেখা যাবে।"}


# ---------- সংবাদ ও কমিটি ----------
@router.get("/news", response_model=list[NewsPublic])
def news(db: Session = Depends(get_db)):
    return db.scalars(select(News).where(News.published.is_(True))
                      .order_by(News.id.desc()).limit(50)).all()


@router.get("/committee", response_model=list[MemberOut])
def committee(db: Session = Depends(get_db)):
    return db.scalars(select(Member).order_by(Member.sort_order, Member.id)).all()


# ---------- আর্থিক হিসাব (শুধু দেখা, ব্যক্তিগত তথ্য নেই) ----------
@router.get("/finance/summary")
def finance_summary(db: Session = Depends(get_db)):
    txs = db.scalars(select(Transaction)).all()
    income = sum(t.amount for t in txs if t.kind == "income")
    expense = sum(t.amount for t in txs if t.kind == "expense")
    since = date.today().replace(day=1)
    months = []
    for _ in range(6):
        months.append(since)
        since = (since - timedelta(days=1)).replace(day=1)
    months.reverse()
    agg = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in txs:
        agg[(t.date.year, t.date.month)][t.kind] += t.amount
    monthly = [{"month": f"{m.year}-{m.month:02d}", **agg[(m.year, m.month)]} for m in months]
    return {"income": income, "expense": expense, "balance": income - expense, "monthly": monthly}


@router.get("/finance/transactions", response_model=list[TxOut])
def finance_transactions(kind: Optional[str] = Query(None, pattern="^(income|expense)$"),
                         db: Session = Depends(get_db)):
    stmt = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(200)
    if kind:
        stmt = stmt.where(Transaction.kind == kind)
    return db.scalars(stmt).all()
