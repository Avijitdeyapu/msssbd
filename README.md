# এম. সুমন স্মৃতি সংঘ: ওয়েবসাইট ও ম্যানেজমেন্ট সিস্টেম

```
msss-project/
├── docs/        ← ৭টি ওয়েবসাইট পেজ (index, memorial, blood-donors, committee, activities, finance, contact)
├── backend/     ← FastAPI সার্ভার + অ্যাডমিন প্যানেল (backend/README.md দেখুন)
└── README.md
```

## পেজ গুলো দেখবেন কীভাবে
`docs/index.html` ডাবল ক্লিক করলেই ব্রাউজারে খুলবে। এখন ফর্ম ও তথ্য সব **নমুনা (ডেমো)**।

## ব্যাকএন্ড চালানো
`backend/README.md` এর ধাপগুলো অনুসরণ করুন।
অ্যাডমিন প্যানেল: http://127.0.0.1:8000/admin/

## GitHub Pages এ ওয়েবসাইট দেখানো (বিনামূল্যে)
Repository → Settings → Pages → Branch: `main` এবং folder: `/docs` → Save।
কিছুক্ষণ পর `https://<আপনার-ইউজারনেম>.github.io/<রিপো-নাম>/` এ সাইট দেখা যাবে।
(মনে রাখবেন: GitHub Pages শুধু `docs` এর পেজ দেখায়। ব্যাকএন্ড আলাদা জায়গায় চালাতে হবে।)

## ভুলেও GitHub এ তুলবেন না
`.env` ফাইল (পাসওয়ার্ড ও গোপন কী থাকে) এবং `*.db` (সদস্য ও দাতার আসল তথ্য)। এগুলো `.gitignore` এ বাদ দেওয়া আছে।
