import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

BloodGroup = Literal["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
Status = Literal["pending", "approved", "rejected"]
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def clean_phone(v: str) -> str:
    v = re.sub(r"[\s\-]", "", v.translate(BN_DIGITS))
    if v.startswith("+88"):
        v = v[3:]
    elif v.startswith("88") and len(v) == 13:
        v = v[2:]
    if not re.fullmatch(r"01[3-9]\d{8}", v):
        raise ValueError("মোবাইল নম্বর সঠিক নয়")
    return v


class In(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- পাবলিক ফর্ম ----------
class DonorIn(In):
    name: str = Field(min_length=2, max_length=60)
    blood_group: BloodGroup
    area: str = Field(min_length=2, max_length=60)
    phone: str
    last_donation: Optional[date] = None
    consent: bool

    @field_validator("blood_group", mode="before")
    @classmethod
    def _bg(cls, v):
        return v.replace("−", "-").strip().upper() if isinstance(v, str) else v

    @field_validator("phone")
    @classmethod
    def _ph(cls, v):
        return clean_phone(v)

    @field_validator("consent")
    @classmethod
    def _consent(cls, v):
        if not v:
            raise ValueError("তালিকায় নাম দেখানোর সম্মতি দিতে হবে")
        return v

    @field_validator("last_donation")
    @classmethod
    def _ld(cls, v):
        if v and v > date.today():
            raise ValueError("তারিখ ভবিষ্যতের হতে পারে না")
        return v


class VolunteerIn(In):
    name: str = Field(min_length=2, max_length=60)
    phone: str
    email: Optional[str] = Field(default=None, max_length=80)
    age: int = Field(ge=16, le=80)
    address: str = Field(min_length=2, max_length=100)
    interests: list[str] = Field(default_factory=list, max_length=8)
    availability: str = Field(default="", max_length=40)
    about: Optional[str] = Field(default=None, max_length=300)

    @field_validator("phone")
    @classmethod
    def _ph(cls, v):
        return clean_phone(v)

    @field_validator("email")
    @classmethod
    def _em(cls, v):
        if v and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("ইমেইল সঠিক নয়")
        return v or None

    @field_validator("interests")
    @classmethod
    def _int(cls, v):
        return [i[:30] for i in v]


class MessageIn(In):
    name: str = Field(min_length=2, max_length=60)
    contact: str = Field(min_length=3, max_length=80)
    subject: str = Field(max_length=60)
    body: str = Field(min_length=5, max_length=600)


class TributeIn(In):
    name: str = Field(min_length=2, max_length=60)
    body: str = Field(min_length=5, max_length=400)


# ---------- পাবলিক আউটপুট ----------
class DonorPublic(BaseModel):
    id: int
    name: str
    blood_group: str
    area: str
    phone: str
    available: bool


class TributePublic(Out):
    id: int
    name: str
    body: str
    created_at: datetime


class NewsPublic(Out):
    id: int
    title: str
    body: str
    created_at: datetime


class MemberOut(Out):
    id: int
    name: str
    role: str
    group: str
    phone: Optional[str]
    photo_url: Optional[str]
    sort_order: int


# ---------- অ্যাডমিন ----------
class StatusIn(In):
    status: Status


class NewsIn(In):
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=10000)
    published: bool = False


class NewsOut(Out):
    id: int
    title: str
    body: str
    published: bool
    created_at: datetime


class MemberIn(In):
    name: str = Field(min_length=2, max_length=60)
    role: str = Field(min_length=2, max_length=60)
    group: Literal["leadership", "executive", "advisor"]
    phone: Optional[str] = None
    photo_url: Optional[str] = Field(default=None, max_length=300)
    sort_order: int = 0

    @field_validator("phone")
    @classmethod
    def _ph(cls, v):
        return clean_phone(v) if v else None


class TxIn(In):
    date: date
    title: str = Field(min_length=2, max_length=120)
    kind: Literal["income", "expense"]
    amount: int = Field(gt=0, le=100_000_000)


class TxOut(Out):
    id: int
    date: date
    title: str
    kind: str
    amount: int


class UserIn(In):
    email: str = Field(max_length=120)
    name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=100)
    role: Literal["admin", "editor"] = "editor"


class UserOut(Out):
    id: int
    email: str
    name: str
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
