# Backend — สรุปงานที่ทำไปแล้ว (Member 3)

> อัปเดตล่าสุด: 14 ก.ย. 2026 · branch `feature/backend` · commit ล่าสุด `3d9e555`
> เอกสารนี้ไว้ให้เพื่อนในทีมอ่านว่า backend ตอนนี้เป็นยังไง มีอะไรเปลี่ยนบ้าง และต้องแก้ฝั่งตัวเองยังไง

---

## 🚨 อ่านตรงนี้ก่อน — ของที่เปลี่ยนแล้วกระทบคนอื่น

ถ้าเคยเขียนโค้ดยิง API ไว้แล้ว **4 อย่างนี้พังแน่นอน** ต้องแก้:

| # | เปลี่ยนอะไร | เดิม | ตอนนี้ | กระทบใคร |
|---|---|---|---|---|
| 1 | **ต้องมี token** | ยิง API ได้เลย | ทุก `/api/candidates/*` ต้องแนบ `Authorization: Bearer <jwt>` ไม่งั้น `401` | Member 1, 2 |
| 2 | **`candidate_id`** | UUID `"11111111-1111-..."` | เลขรัน 7 หลัก `"0000001"` | Member 1, 2 |
| 3 | **field ใหม่ `upload_status`** | ไม่มี | มีทุก candidate — `Not Uploaded` / `Processing` / `Done` / `Failed` | Member 1, 2 |
| 4 | **upload หลายไฟล์** | field ชื่อ `file` คืน candidate 1 คน | field ชื่อ **`files`** (list) คืน `{created[], failed[], count}` | Member 2 |

`shared-contracts/schema.json` กับ `mock-candidates.json` อัปเดตให้ตรงหมดแล้ว — **ดึงไฟล์ใหม่ไปใช้ได้เลย**

---

## ⚠️ ข้อควรระวัง: โค้ดยังไม่เคยรันเลยสักครั้ง

พูดตรง ๆ ครับ — **เขียนเสร็จแต่ยังไม่ได้เทส** เพราะ:
- เครื่องผมไม่มี Python (ยังลงไม่ได้)
- Docker Desktop / WSL2 บนเครื่องผมพัง — `pip install` ตอน build container **segfault** แบบสุ่ม (ลองแล้ว 5 รอบ error คนละแบบทุกครั้ง) เป็นปัญหาที่ตัว VM ไม่ใช่โค้ด
- ส่วน Azure Blob ก็ยังไม่เคยต่อกับ Storage Account จริง

**ใครมี Python ในเครื่องช่วยรันให้หน่อยได้ไหมครับ:**
```bash
cd backend
pip install -r requirements.txt
pytest -q
```
มี test อยู่ 15 เคส ถ้าผ่านหมดผมสบายใจขึ้นเยอะ ถ้าพังตรงไหนบอกได้เลยเดี๋ยวแก้ให้

---

## วิธีรัน

### Docker (ง่ายสุด ไม่ต้องลง Python)
```bash
docker compose up --build
```
- API: http://localhost:8000 · Swagger UI (ลองยิง API ได้ในเว็บเลย): http://localhost:8000/docs
- มีข้อมูล mock 9 คนใส่ให้อัตโนมัติ ไม่ต้องตั้ง `.env` อะไรเลย
- ล้างข้อมูลเริ่มใหม่: `docker compose down -v`

### Python ตรง ๆ (แก้โค้ดแล้วเห็นผลเร็วกว่า)
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  /  macOS-Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## ใช้ API ยังไง

### 1. ขอ token ก่อน (ทำครั้งเดียว เก็บไว้ใช้)

```bash
curl -X POST localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"password123"}'
```
```json
{ "data": { "access_token": "eyJhbGci...", "token_type": "bearer" }, "error": null }
```

บัญชีเดียว `admin` / `password123` (เปลี่ยนได้ที่ `.env`) token อยู่ได้ 8 ชั่วโมง

### 2. เอา token ไปแนบทุก request

```bash
curl localhost:8000/api/candidates -H "Authorization: Bearer eyJhbGci..."
```

ฝั่ง JS:
```js
const res = await fetch(`${API}/api/candidates`, {
  headers: { Authorization: `Bearer ${token}` }
});
```

### 3. Endpoint ทั้งหมด

| Method | Path | ได้อะไร |
|---|---|---|
| `POST` | `/api/auth/login` | `{username, password}` → token |
| `GET` | `/api/candidates` | list แบบย่อ + **filter/search** (ดูข้างล่าง) |
| `GET` | `/api/candidates/{id}` | ข้อมูลเต็มของคนเดียว |
| `PUT` | `/api/candidates/{id}` | แก้ข้อมูล (ส่ง schema เต็มมา เขียนทับ) |
| `DELETE` | `/api/candidates/{id}` | ลบ/ยกเลิก (มีเงื่อนไข ดูข้างล่าง) |
| `POST` | `/api/candidates/upload` | อัป CV หลายไฟล์พร้อมกัน |
| `GET` | `/api/candidates/{id}/resume-url` | ขอลิงก์เปิดไฟล์ CV |
| `GET` | `/health` | เช็คว่า API ยังมีชีวิต (ไม่ต้องใช้ token) |

**ทุก response หน้าตาเหมือนกันหมด:**
```json
สำเร็จ  { "data": <ข้อมูล>, "error": null }
พัง     { "data": null, "error": "ข้อความบอกสาเหตุ" }
```
`400` ไฟล์ผิด/ข้อมูลไม่ผ่าน · `401` ไม่มี token หรือ token หมดอายุ · `404` ไม่เจอ id · `500` พังไม่คาดคิด

---

## ฟีเจอร์ใหม่แต่ละตัว

### 🔍 Filter + Search (`GET /api/candidates`)

ต่อ query string ได้เลย ผสมกันได้หมด:

| param | ทำอะไร | ตัวอย่าง |
|---|---|---|
| `status` | กรองตาม HR status (ตรงตัว) | `?status=Hired` |
| `applied_position` | กรองตามตำแหน่ง (ตรงตัว) | `?applied_position=Data Engineer` |
| `min_experience` | ประสบการณ์ ≥ | `?min_experience=3` |
| `max_experience` | ประสบการณ์ ≤ | `?max_experience=8` |
| `q` | ค้นหา — ชื่อ, email, candidate_id, ชื่อ skill, ชื่อ tool | `?q=airflow` |

```
GET /api/candidates?status=Review&min_experience=5&q=python
```
→ คนที่ status = Review **และ** ประสบการณ์ ≥ 5 ปี **และ** มีคำว่า python อยู่ที่ไหนสักที่

> `q` ค้นแบบไม่สนตัวพิมพ์เล็กใหญ่ และค้นถึงใน `tools` ด้วย เช่น `?q=fastapi` ก็เจอ

### 📤 อัปโหลดหลายไฟล์ (`POST /api/candidates/upload`)

field ชื่อ **`files`** ใส่ซ้ำได้หลายอัน (เดิมชื่อ `file` อันเดียว)

```js
const fd = new FormData();
for (const f of selectedFiles) fd.append('files', f);   // <-- 'files' ไม่ใช่ 'file'

const res = await fetch(`${API}/api/candidates/upload`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },        // อย่าใส่ Content-Type เอง
  body: fd,
});
```

ได้กลับมา:
```json
{
  "data": {
    "created": [ { ...candidate เต็ม... }, { ... } ],
    "failed":  [ { "filename": "งานเก่า.txt", "error": "Unsupported file type '.txt'. Allowed: .pdf, .docx" } ],
    "count": 2
  },
  "error": null
}
```

- รับแค่ `.pdf` กับ `.docx` ไฟล์ละไม่เกิน 10 MB
- **ไฟล์เสียแค่ตัวเอง** ไฟล์อื่นในชุดเดียวกันยังอัปได้ปกติ → ต้องอ่าน `failed[]` มาโชว์ user ด้วยนะครับ
- ถ้าพังหมดทั้งชุด → `400`

### 🔢 candidate_id เป็นเลขรัน 7 หลัก

`"0000001"`, `"0000002"`, ... เรียงตามลำดับที่เข้ามา (เดิมเป็น UUID)

- **เป็น string นะครับ ไม่ใช่ number** — เลข 0 ข้างหน้าสำคัญ อย่าเผลอ `parseInt`
- ข้อมูล mock 9 คนเปลี่ยนเป็น `0000001`–`0000009` แล้ว

### 🗑️ ลบ / ยกเลิกอัปโหลด (`DELETE /api/candidates/{id}`)

ผูกกับ **`upload_status`** (สถานะไฟล์) ไม่ใช่ `status` (สถานะ HR):

| `upload_status` | หมายความว่า | ลบได้ไหม |
|---|---|---|
| `Not Uploaded` | ยังไม่ได้อัปไฟล์เลย | ✅ ลบได้ |
| `Processing` | **กำลังอัป/กำลังประมวลผลอยู่** | ❌ `400` |
| `Done` | เสร็จเรียบร้อย | ✅ ลบได้ |
| `Failed` | อัปแล้วแต่สกัดข้อมูลไม่สำเร็จ | ✅ ลบได้ |

ถ้าลบไม่ได้จะได้:
```json
{ "data": null, "error": "Cannot cancel/delete file in current status" }
```

> **`status` กับ `upload_status` คนละเรื่องกันนะครับ**
> `status` = ขั้นตอน HR (`New` → `Review` → `Assessment` → `Interview` → `Hired` / `CV rejected` ...)
> `upload_status` = สถานะไฟล์ (`Not Uploaded` → `Processing` → `Done` / `Failed`)
> ปุ่มลบให้ดู `upload_status` การ์ด/ป้ายสถานะใน dashboard ให้ดู `status`

### 📎 ขอลิงก์ไฟล์ CV (`GET /api/candidates/{id}/resume-url`)

```json
{ "data": { "resume_url": "http://localhost:8000/files/0000010/cv.pdf", "filename": "cv.pdf" }, "error": null }
```

**เวลาจะเปิดไฟล์ให้ยิง endpoint นี้ทุกครั้ง อย่า cache ค่า `resume_url` ที่ติดมากับ candidate ไว้นาน ๆ** — ตอนขึ้น Azure จริงลิงก์จะเป็นแบบมีวันหมดอายุ (1 ชม.) ถ้า cache ไว้จะเปิดไม่ขึ้น

### ☁️ Azure Blob Storage

เตรียมโค้ดรอไว้แล้ว สลับด้วย environment variable ตัวเดียว:

- **ไม่ตั้งค่า** (ตอนนี้) → เก็บไฟล์ลง disk ในเครื่อง เสิร์ฟที่ `/files/...` — ไม่ต้องทำอะไร
- **ตั้ง `AZURE_STORAGE_CONNECTION_STRING`** → สลับไปเก็บบน Azure อัตโนมัติ ไม่ต้องแก้โค้ดสักบรรทัด

รายละเอียดสำหรับคนที่จะ deploy:
- container ชื่อตาม `AZURE_STORAGE_CONTAINER_NAME` (default `resumes`) สร้างให้เองถ้ายังไม่มี
- **container เป็น private** เพราะ resume เป็นข้อมูลส่วนบุคคล (PDPA) → ลิงก์ที่ได้เป็น SAS หมดอายุใน 60 นาที
- ถ้าต่อ Azure ไม่ได้ (key ผิด/เน็ตหลุด) จะ **fallback กลับมาใช้ disk ในเครื่อง** ไม่ทำให้ API ล่มทั้งระบบ
- **ไม่มี credential ฝังในโค้ดเลย** มาจาก `.env` อย่างเดียว (ซึ่ง git ไม่เก็บอยู่แล้ว)

---

## ประวัติงาน 3 รอบ

### รอบ 1 — `7a58615` วางโครง backend
- FastAPI + SQLite + เก็บไฟล์ลง disk
- CRUD ครบ + response envelope + CORS + error handling
- `shared-contracts/schema.json` + `mock-candidates.json` (9 คน ครอบคลุมทุก status)
- mock `extract_candidate()` แทนของ Member 4 ไปก่อน + Docker compose
- **ทำไม:** ให้ frontend 2 lane เริ่มงานได้ทันทีโดยไม่ต้องรอ LLM เสร็จ

### รอบ 2 — `fa2b19a` Task extension 5 ข้อ
- ✅ Login + JWT ป้องกันทุก endpoint
- ✅ อัปโหลดหลายไฟล์พร้อมกัน
- ✅ candidate_id เป็นเลขรัน 7 หลัก
- ✅ ลบแบบมีเงื่อนไข + เพิ่ม field `upload_status`
- ✅ Filter + search 5 แบบ
- **ทำไม:** ทำตามสเปกที่ได้รับเพิ่ม

### รอบ 3 — `3d9e555` Azure Blob + แก้บั๊ก
- เพิ่ม `AzureBlobStorage` สลับด้วย env var, SAS link, fallback อัตโนมัติ
- 🐛 **แก้บั๊ก:** endpoint `GET /api/candidates/{id}/resume-url` **หายไปจากโค้ด** — ตอนรอบ 2 ผมเขียนไฟล์ `routers/candidates.py` ใหม่ทั้งไฟล์แล้วลืมใส่กลับ ตอนนี้ใส่คืนแล้ว
- **ทำไม:** เตรียมพร้อม deploy จริง + ไม่ให้ credential หลุดเข้า git

---

## ถึงแต่ละคน

### 🟦 Member 1 (Dashboard)
- ดึง `shared-contracts/mock-candidates.json` ไปใหม่ (id เปลี่ยนเป็น `0000001`)
- ตอนต่อ API จริง: login ขอ token ก่อน แล้วแนบ `Authorization: Bearer` ทุก request
- มี field ใหม่ `upload_status` เอาไปโชว์/ซ่อนปุ่มลบได้
- **filter/search ทำฝั่ง server ได้แล้ว** ไม่ต้อง filter ใน JS เอง ส่ง query param มาแทน จะเร็วกว่าเยอะตอนข้อมูลเยอะ

### 🟩 Member 2 (Upload + Edit)
- form field เปลี่ยนชื่อ `file` → **`files`** และ append ได้หลายไฟล์
- response เปลี่ยนเป็น `{created[], failed[], count}` — อย่าลืมอ่าน `failed[]` มาโชว์ว่าไฟล์ไหนไม่ผ่านเพราะอะไร
- ปุ่มลบ/ยกเลิก → เช็ค `upload_status` ถ้า `Processing` ให้ disable ไว้
- ตอนเปิดไฟล์ CV ยิง `GET /api/candidates/{id}/resume-url` ทุกครั้ง อย่า cache

### 🟨 Member 4 (LLM Extraction)
**ไม่ต้องแก้อะไรเลยครับ** ทุกอย่างที่เปลี่ยนเป็นเรื่องฝั่ง backend ล้วน ๆ

สัญญาเดิมยังเหมือนเดิมทุกตัวอักษร:
```python
extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict
```
- `candidate_id`, `location`, `status`, `upload_status` → **backend ใส่ให้เอง** ไม่ต้องส่งมา
- ตอนรวมงาน แค่แก้ import บรรทัดเดียวใน `app/routers/candidates.py`
- ขอฝากไว้ 2 อย่าง: (1) ทำ `llm-service/cv-parsing/` ให้เป็น package (ใส่ `__init__.py`) จะ import ง่ายกว่าเดิม (2) เพิ่ม dependency ของฝั่งนั้น (`pypdf`, `python-docx`, ฯลฯ) ลง `backend/requirements.txt` ด้วย

---

## ยังไม่ได้ทำ / รู้ไว้

| เรื่อง | สถานะ |
|---|---|
| รัน `pytest` ให้ผ่านจริง | ❌ **ยังไม่ได้ทำ** — ต้องทำก่อน merge เข้า main |
| ทดสอบกับ Azure Storage Account จริง | ❌ ยังไม่เคยลอง |
| ต่อกับ LLM ตัวจริงของ Member 4 | ❌ ยังใช้ mock อยู่ (แก้ import บรรทัดเดียว) |
| ย้ายไป Postgres | ยังเป็น SQLite (เขียน service ไว้ใน `docker-compose.yml` แล้ว comment ไว้) |
| `Processing` เป็นช่วงสั้นมาก | ตอนนี้สกัดข้อมูลแบบ sync เสร็จในคำขอเดียว → ปุ่ม cancel ตอน `Processing` แทบกดไม่ทัน ต้องทำเป็น background task ทีหลังถึงจะใช้งานได้จริง |
| สร้าง candidate เปล่า (draft) | ยังไม่มี endpoint จองค่า `Not Uploaded` ไว้เฉย ๆ |

---

## ไฟล์อยู่ไหนบ้าง

```
backend/
  app/
    main.py          FastAPI app, CORS, error envelope
    config.py        ตั้งค่าทั้งหมดจาก env (มี default ใช้ได้เลย)
    auth.py          JWT สร้าง/ตรวจ + ตัวกันทาง
    database.py      SQLAlchemy
    models_db.py     ตาราง candidates
    schemas.py       Pydantic = ตัวสัญญาจริงในโค้ด
    storage.py       LocalDisk / AzureBlob เลือกเองจาก env
    extraction.py    mock ของ Member 4
    seed.py          ใส่ข้อมูล mock ตอนเปิดครั้งแรก
    routers/
      auth.py        POST /api/auth/login
      candidates.py  ที่เหลือทั้งหมด
  tests/test_smoke.py   15 เคส (ยังไม่ได้รัน)
  .env.example          ตัวแปรทั้งหมดที่ตั้งได้
shared-contracts/
  schema.json           สัญญา JSON ของ candidate
  mock-candidates.json  ข้อมูลปลอม 9 คน
```

มีอะไรไม่ชัดทักได้เลยครับ 🙏
