# এম. সুমন স্মৃতি সংঘ: Backend (FastAPI + SQLite)

## চালানোর নিয়ম
```bash
cd msss-backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # Windows: copy .env.example .env
python -c "import secrets;print(secrets.token_urlsafe(48))"   # যা আসবে .env এর SECRET_KEY= এর পর বসান

python -m app.seed                # প্রথম অ্যাডমিন বানান
uvicorn app.main:app --reload     # চালু করুন
```
**অ্যাডমিন প্যানেল:** http://127.0.0.1:8000/admin/ (seed এ দেওয়া ইমেইল ও পাসওয়ার্ড দিয়ে লগইন)

API পরীক্ষার জন্য: http://127.0.0.1:8000/docs (সব API এখানে দেখে পরীক্ষা করা যায়)।
অ্যাডমিন API পরীক্ষা করতে /docs এ ডানদিকের **Authorize** বাটনে ইমেইল ও পাসওয়ার্ড দিন।

## অ্যাডমিন প্যানেলে কী করা যায়
- ড্যাশবোর্ডে নতুন দাতা, স্বেচ্ছাসেবক, শ্রদ্ধাঞ্জলি ও অপঠিত বার্তার সংখ্যা
- দাতা, স্বেচ্ছাসেবক, শ্রদ্ধাঞ্জলি: অনুমোদন, বাতিল বা মোছা
- বার্তা পড়া ও মোছা
- সংবাদ ও কমিটি যোগ, সম্পাদনা, মোছা
- আর্থিক এন্ট্রি ও ব্যবহারকারী তৈরি (**শুধু অ্যাডমিন রোল**)

## কোন পেজ কোন API ডাকবে
| পেজ | API |
|---|---|
| রক্তদাতা | `GET /api/donors?blood_group=A%2B&q=...&available_only=true`, `POST /api/donors` |
| স্বেচ্ছাসেবক | `POST /api/volunteers` |
| যোগাযোগ | `POST /api/messages` |
| স্মৃতিচারণ | `GET/POST /api/tributes` |
| সংবাদ | `GET /api/news` |
| কমিটি | `GET /api/committee` |
| আর্থিক হিসাব | `GET /api/finance/summary`, `GET /api/finance/transactions?kind=income` |

ধ্যান দিন: রক্তের গ্রুপে `+` চিহ্ন URL এ পাঠাতে `encodeURIComponent("A+")` ব্যবহার করুন, নইলে `+` স্পেস হয়ে যায়।

## অ্যাডমিন (লগইন লাগবে)
- `POST /api/auth/login` (ইমেইল ও পাসওয়ার্ড), যা `access_token` দেয়। এরপর প্রতি অনুরোধে `Authorization: Bearer <token>`
- দাতা/স্বেচ্ছাসেবক/শ্রদ্ধাঞ্জলি অনুমোদন: `GET /api/admin/review/{donors|volunteers|tributes}?status=pending`, `PATCH .../{id}` body `{"status":"approved"}`
- বার্তা: `GET /api/admin/messages`
- সংবাদ, কমিটি: `/api/admin/news`, `/api/admin/committee` (GET, POST, PUT, DELETE)
- আর্থিক হিসাব: `/api/admin/finance` (**শুধু admin** রোল)
- ইউজার: `POST /api/admin/users` (**শুধু admin**), রোল: `admin` বা `editor`

## নিরাপত্তা যা করা আছে
- পাসওয়ার্ড scrypt দিয়ে হ্যাশ, লগইনে টাইমিং সুরক্ষা ও রেট লিমিট
- দাতা, স্বেচ্ছাসেবক ও শ্রদ্ধাঞ্জলি **admin অনুমোদন ছাড়া** পাবলিকে আসে না
- দাতার সম্মতি (consent) ছাড়া ফর্মই নেওয়া হয় না
- ফর্মে মোবাইল নম্বর (বাংলাদেশি ফরম্যাট) ও দৈর্ঘ্য যাচাই, ফর্ম জমায় রেট লিমিট
- CORS শুধু `.env` এ দেওয়া ফ্রন্টএন্ড ঠিকানার জন্য

## অনলাইনে দেওয়ার আগে
- SQLite ছোট সংগঠনের জন্য ঠিক আছে; হোস্টিংয়ে ডিস্ক স্থায়ী না হলে `DATABASE_URL` এ PostgreSQL দিন (`pip install psycopg[binary]`)
- রেট লিমিট মেমরিতে থাকে। Nginx/Render-এর মতো প্রক্সির পেছনে চালালে সব ব্যবহারকারীর IP এক দেখাতে পারে, তখন `uvicorn --proxy-headers` ব্যবহার করুন
- HTTPS ছাড়া চালাবেন না, আর `.env` কখনো GitHub এ তুলবেন না
