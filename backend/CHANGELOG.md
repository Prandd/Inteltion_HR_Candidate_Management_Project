# Backend — สรุปงานที่ทำไปแล้ว (Member 3)

> อัปเดตล่าสุด: 30 ก.ย. 2026 · branch `feature/backend` · รอบ 5 (ต่อจากรอบ 4)
> เอกสารนี้ไว้ให้เพื่อนในทีมอ่านว่า backend ตอนนี้เป็นยังไง มีอะไรเปลี่ยนบ้าง และต้องแก้ฝั่งตัวเองยังไง

---

## 🚨 รอบ 5 — ของที่เปลี่ยนแล้วกระทบคนอื่น

`shared-contracts/schema.json` **bump เป็น v2.3.0** (additive ล้วน ไม่ breaking) + ไฟล์ contract ใหม่ 2 ไฟล์

| # | เปลี่ยนอะไร | รายละเอียด | กระทบใคร |
|---|---|---|---|
| 1 | **candidate มี owner แล้ว** 🆕 | field ใหม่ `owner_account_id` / `owner_name` — ใครอัป CV ขึ้นมาคนแรกเป็นเจ้าของ record นั้น | Member 1, 2 |
| 2 | **โอนความเป็นเจ้าของได้** 🆕 | `POST /api/candidates/{id}/transfer-ownership` — เจ้าของเดิม หรือ admin เท่านั้นที่โอนได้ | Member 1, 2 |
| 3 | **คะแนนจากเครื่องมือ SQL test ภายนอก** 🆕 | `POST/GET /api/candidates/{id}/sql-test-score(s)` — เก็บ `score` (ตัวเลข) + `raw_payload` (อะไรก็ได้ที่ส่งมาเพิ่ม เก็บไว้เผื่อ) | Member 1, 2 (ถ้าจะโชว์คะแนนนี้ใน UI) |
| 4 | **comment path เดิม `/candidates/comments/{id}` ใช้ได้แล้ว** 🆕 | เพิ่ม alias ให้ตรงกับที่ `feature/frontend-update` เรียกอยู่จริง (ของเดิม `/comments/{id}` ยังใช้ได้เหมือนเดิม ทั้งคู่ทำงานเหมือนกันทุกอย่าง) | Member 1 |

> **เรื่อง owner สำคัญที่สุดรอบนี้** — กติกาคือ **"ใครอัป CV คนนั้นเป็นเจ้าของ"** ตั้งครั้งเดียวตอนสร้าง
> record แล้ว **ไม่เปลี่ยนเองอัตโนมัติ** ไม่ว่าจะอัป CV ซ้ำกี่ครั้ง หรือมีคนอื่นกด "อัปเดต" ทับก็ตาม
> จะเปลี่ยนได้ทางเดียวคือ endpoint โอนสิทธิ์ข้างบน และ **ต้องเป็นเจ้าของเดิมหรือ admin เท่านั้นที่กดได้**
> (คนที่กำลังจะรับโอนกดรับเองไม่ได้ — ต้องให้อีกฝ่ายหรือ admin เป็นคนโอนมาให้)

### 🆕 ข้อ 1-2 ละเอียด — ระบบ Ownership

- **ตั้งตอนสร้างเท่านั้น**: candidate ใหม่ทุกตัว (อัปตรง ๆ หรือกด "create-new" จาก pending-upload)
  ได้ `owner_account_id` = คนที่อัปไฟล์นั้นขึ้นมา **คนแรกที่อัป ไม่ใช่คนที่กด "create-new" ทีหลัง**
  ถ้า pending-upload ค้างไว้หลายวันแล้วมีอีกคนมากด resolve เจ้าของยังเป็นคนอัปตอนแรกอยู่ดี
- **อัปซ้ำ/resolve เป็น "update" ไม่แตะ owner เด็ดขาด** — เข้าชุดเดียวกับ `status`/`applied_position`
  ที่การอัป CV ทับไม่มีสิทธิ์ไปยุ่ง
- **โอนสิทธิ์**: `POST /api/candidates/{id}/transfer-ownership` body `{new_owner_account_id, reason?}`
  - อนุญาต: เจ้าของปัจจุบัน หรือ `admin` เท่านั้น → คนอื่นโดน `403`
  - **คนที่กำลังจะรับโอนกดเองไม่ได้** แม้จะเป็น target ก็ตาม (การโอนต้องมาจากอีกฝั่งเสมอ ไม่ใช่ self-grant)
  - `404` ถ้า `new_owner_account_id` ไม่มีจริง, `400` ถ้าบัญชีนั้นถูกปิดใช้งานอยู่ หรือเป็นเจ้าของอยู่แล้ว
- **ประวัติเต็ม**: ทุกครั้งที่ตั้ง/โอน owner จะมี row ใน `ownership_history` เสมอ (แม้แต่ตอนสร้าง candidate
  ครั้งแรกก็มี row แรกที่ `from_owner_account_id = null`) → ดูได้ที่ `GET /api/candidates/{id}/ownership-history`
- **filter "งานของฉัน"**: `GET /api/candidates?owner_account_id=<id>` — เอาค่าจาก `owner_account_id`
  ที่ list เดิมส่งมาให้อยู่แล้วมาใส่ query ได้เลย
- **candidate เก่าก่อนรอบ 5**: migration `0005` backfill owner ให้อัตโนมัติจาก `status_history`
  แถวแรกสุดของแต่ละ candidate (= คนที่สร้างตอนอัปครั้งแรก) ถ้า candidate ไหนไม่มี `status_history`
  เลย (แทบไม่มีในทางปฏิบัติ) จะ fallback ไปที่ admin ที่เก่าแก่ที่สุดที่ยัง active อยู่

### 🆕 ข้อ 3 ละเอียด — คะแนนจากเครื่องมือ SQL test ภายนอก

ทีมยังไม่ล็อก contract ของเครื่องมือตัวนี้ (รู้แค่ว่าเป็นระบบ/เครื่องมือแยกออกมาต่างหาก) เลยออกแบบให้
**กันความเสี่ยงไว้ก่อน** แทนที่จะเดา shape:

- `score` (ตัวเลข ต้อง finite เท่านั้น — ส่ง `Infinity`/`NaN` มาจะโดน `400` ทันที ไม่ยักไปพังตอน response)
  เป็น field เดียวที่ "ชัวร์แล้ว" ว่าต้องมี
- `raw_payload` เก็บทุกอย่างอื่นที่ส่งมาแบบ verbatim (เป็น JSON object เก็บได้ทุก shape) ไว้กันข้อมูลหาย
  ถ้า contract จริงของเครื่องมือนั้นมี field มากกว่านี้ — พอรู้ shape จริงแล้วค่อยมาทำ column แยกทีหลังได้
- **ไม่ทับกัน** — อัปคะแนนกี่ครั้งก็ได้ต่อ candidate หนึ่งตัว ทุกครั้งเป็น row ใหม่ ไม่มีการ overwrite
  ของเก่า → `GET .../sql-test-scores` คืนมาทุกอันเรียงใหม่สุดก่อน
- auth เหมือน endpoint อื่นทุกอัน (ต้อง login) — ยังไม่มี credential แบบ machine-to-machine
  แยกให้เครื่องมือภายนอกยิงเข้ามาเอง (ยังไม่มีใครถามเรื่องนี้ ถ้าต้องการต้องคุยเพิ่ม)

> 🐛 **เจอบั๊กจริงตอนเขียนเทสของฟีเจอร์นี้**: ส่ง `score: Infinity` เข้ามาแล้วระบบ validate ไม่ผ่านตามที่ควร
> (`400`) แต่ตัว **error handler เองดันพังไปด้วย** (`500` แทน) เพราะ Starlette's `JSONResponse` กับ
> FastAPI's validation-error payload ทั้งคู่ปฏิเสธ `NaN`/`Infinity` ในตัว JSON เอง แล้ว error message
> ของเราดันฝัง raw value ที่ส่งมาไว้ในนั้นด้วย → แก้ด้วย sanitizer (`_json_safe` ใน `main.py`) แปลง
> ค่าที่ไม่ finite เป็น string ก่อนส่งกลับ มีเทส regression กันไว้แล้ว

### ข้อ 4 ละเอียด — comment path alias

`feature/frontend-update` เรียก `PUT`/`DELETE` ที่ `/candidates/comments/{id}` (มี prefix `/candidates`)
ส่วน backend ของจริงคือ `/comments/{id}` — เพิ่ม route คู่ขนานให้ทำงานเหมือนกันทุกกติกา (ownership check,
soft delete ทุกอย่างเหมือนเดิม) ไม่ต้องเลือกฝั่งใดฝั่งหนึ่ง เป็นแค่ alias ไม่ใช่ endpoint ใหม่

---

## 🚨 รอบ 4 — ของที่เปลี่ยนแล้วกระทบคนอื่น

`shared-contracts/schema.json` **bump เป็น v2.2.0** แล้ว มีไฟล์ contract ใหม่เพิ่มอีก 4 ไฟล์ — ดึงไปใหม่ทั้งโฟลเดอร์ได้เลย

| # | เปลี่ยนอะไร | เดิม | ตอนนี้ | กระทบใคร |
|---|---|---|---|---|
| 1 | **status `CV rejected` เปลี่ยนชื่อ** | `"CV rejected"` | **`"Rejected"`** | Member 1, 2 + ทุกคนที่มี DB |
| 2 | **login คืน `account` มาด้วย** | `{access_token, token_type}` | เพิ่ม `account: {account_id, username, full_name, role, ...}` — **ต้องเก็บไว้** | Member 1, 2 |
| 3 | **บัญชีอยู่ใน database แล้ว** | `admin`/`password123` ตัวเดียวจาก `.env` | ตาราง `hr_accounts` หลายคน แต่ละคนมีรหัสผ่าน hash แยก + มี `GET /api/auth/me` | Member 1, 2 |
| 4 | **comment ย้ายออกจาก candidate** | field `hr_comment` / `line_manager_comment` เขียนผ่าน `PUT` ได้ | ตาราง `comment_logs` แยก มี endpoint ของตัวเอง — **2 field เดิมกลายเป็น read-only** เขียนไปก็ไม่เข้า | Member 1, 2 |
| 5 | **upload response เพิ่ม `updated[]`** | `{created[], failed[], count}` | `{created[], updated[], failed[], count}` — อัป CV ซ้ำคนเดิมจะไป `updated[]` ไม่ใช่ `created[]` | **Member 2** |
| 6 | **upload response เพิ่ม `needs_review[]`** 🆕 | ซ้ำแบบไม่ชัวร์ → สร้างคนใหม่เงียบ ๆ | **หยุดถาม** ให้ HR เลือก "อัปเดต" หรือ "สร้างใหม่" | **Member 2** |
| 7 | **field ใหม่ 2 ตัวใน candidate** | ไม่มี | `before_rejected_status` (read-only) กับ `possible_duplicate_of` (read-only) | Member 1, 2 |

> **ข้อ 5 สำคัญที่สุดสำหรับ Member 2** — ถ้า UI ยังอ่านแค่ `created[]` อยู่ ตอน HR อัป CV ทับคนเดิม
> หน้าจอจะขึ้นว่า "เพิ่ม 0 คน" ทั้งที่ข้อมูลถูกเขียนทับไปแล้ว ต้องแยกให้เห็นว่า
> "เพิ่มใหม่ 1 คน, อัปเดตของเดิม 2 คน"

> **ข้อ 6 ก็สำคัญไม่แพ้กัน** — ไฟล์ที่อยู่ใน `needs_review[]` **ยังไม่ได้เข้า database เลย**
> ถ้า UI ไม่ขึ้น prompt ให้ HR เลือก CV ใบนั้นจะหายไปเฉย ๆ ไม่มีใครรู้

### 🆕 ข้อ 6 ละเอียด — ระบบถามก่อนเมื่อเจอ "อาจจะซ้ำ"

ตอนนี้ระบบตัดสินใจ 3 ทางแทนที่จะเป็น 2:

| เจออะไร | ทำอะไร |
|---|---|
| **email ตรงเป๊ะ** (ตัดช่องว่าง+พิมพ์เล็ก) | อัปเดตคนเดิมอัตโนมัติ เหมือนเดิม |
| **ไม่ตรงอะไรเลย** | สร้างคนใหม่อัตโนมัติ เหมือนเดิม |
| **ไม่ตรง email แต่เบอร์โทรตรง หรือ ชื่อ+ตำแหน่งตรง** 🆕 | **หยุด ไม่สร้าง ไม่ทับ** → เข้าคิวรอ HR ตัดสิน |

**ทำไมถึงไม่เดาเอง:** ทั้ง 2 ทางผิดได้หมด — สร้างคนใหม่ทั้งที่เป็นคนเดิม = มี 2 record ซ้ำ /
อัปเดตทับทั้งที่เป็นคนละคน = ข้อมูลของอีกคนหายถาวร undo ไม่ได้ มีแต่คนเท่านั้นที่ตอบได้ว่าอันไหน

**API ใหม่ 4 ตัว:**

| Method | Path | ทำอะไร |
|---|---|---|
| `GET` | `/api/pending-uploads` | คิวที่รอตัดสิน (เก่าสุดก่อน) |
| `POST` | `/api/pending-uploads/{id}/update` | "คนเดิม" → merge เข้า candidate ที่มีอยู่ |
| `POST` | `/api/pending-uploads/{id}/create-new` | "คนละคน" → สร้าง candidate ใหม่ |
| `DELETE` | `/api/pending-uploads/{id}` | "ไม่เอาทั้งคู่" → ทิ้งไฟล์ |

**ถ้าเจอว่าซ้ำกับหลายคนพร้อมกัน ระบบไม่ถามว่าคนไหน** — `update` จะเลือก
**คนที่ `updated_at` ใหม่สุด** ให้เอง (= คนที่ HR กำลังทำงานด้วยอยู่) เพราะถ้าอัปทีละ 20 ไฟล์
แล้วถามว่า "เอาคนไหนใน 3 คนนี้" ทุกไฟล์ คนก็จะกดผ่าน ๆ โดยไม่อ่าน

**การ์ดกันพลาด:**
- resolve ซ้ำ (เช่นเปิด 2 แท็บ) → `409` บอกว่าใครจัดการไปแล้วและลงที่ candidate ไหน
- กด `update` แต่ candidate ที่แนะนำถูกลบไปหมดแล้ว → `409` พร้อมบอกให้ใช้ `create-new` แทน
- `DELETE` เก็บ record การตัดสินใจไว้เป็น audit **แต่ลบ bytes ของ CV ทิ้ง** (PDPA — ไฟล์ที่เราตัดสินใจไม่เก็บ ก็ไม่ควรถืออยู่)

### 🔴 ข้อ 1 ละเอียด — status `CV rejected` → `Rejected`

ทีมตัดสินแล้วว่า 2 ชื่อนี้หมายถึงอย่างเดียวกัน → **ใช้ชื่อสั้นกว่า**
ส่วนคำถาม "ถูกปฏิเสธตอนขั้นไหน" ตอบด้วย `before_rejected_status` แทน

**ทุกคนต้องแก้:**

- **Lane A / Lane B** — string `"CV rejected"` ที่ hardcode ไว้ทุกที่ (คอลัมน์ Kanban, ตัวกรอง, ป้ายสถานะ)
  → เปลี่ยนไป `import { CANDIDATE_STATUSES, isRejected } from 'shared-contracts/status.ts'`
  จะได้ไม่ต้องไล่แก้มืออีกถ้ามีรอบหน้า
- **ใครมี `backend/data/dev.db` อยู่** → `alembic upgrade head`
  (migration `0002` ไล่แก้ค่าให้เองทั้ง `candidates.status`, `before_rejected_status` และ `status_history`)
  หรือจะลบ DB ทิ้งแล้ว seed ใหม่ก็ได้

> ถ้าลืม migrate จะรู้ทันที — **app ไม่ยอมขึ้น** แล้วฟ้องว่า row ไหนถือค่าเก่าอยู่ พร้อมบอกให้รัน alembic
> (startup assertion ของ F6) ไม่ใช่พังเงียบ ๆ แบบที่สเปกกลัว

> 📌 **บันทึกไว้:** ตอนแรกผมทักไปว่าสเปกอ้างผิด เพราะ `schemas.py` กับ `schema.json` ใช้ enum
> ชุดเดียวกันเป๊ะมาตั้งแต่รอบ 1 — ที่ไม่ตรงกันคือ *ระหว่างเอกสาร* ไม่ใช่ระหว่างโค้ด
> พอทีมยืนยันว่าตั้งใจเปลี่ยนชื่อจริง ก็เปลี่ยนให้แล้ว แต่ทำเป็น **breaking change ที่ประกาศชัด +
> มี migration** ไม่ใช่แก้ `schema.json` เงียบ ๆ แล้วให้คนอื่นไปเจอเอง

### งานอื่นของ F6 (enum มีที่มาที่เดียว) ทำครบแล้ว

- enum มีที่มาที่เดียวคือ `schema.json` → backend โหลดจากไฟล์นั้นตอน start (`app/statuses.py`)
  ไม่มี string literal กระจายตาม router แล้ว
- `shared-contracts/status.ts` **generate จากไฟล์เดียวกัน** ให้ Member 1/2 `import` ไปใช้
  (regenerate: `cd backend && python scripts/gen_frontend_types.py`)
- ตอน start ถ้ามี candidate ตัวไหนใน DB ถือ status นอก enum → **app ไม่ยอมขึ้น** ฟ้องทันที
- `GET /health` คืน list ของ status ทั้งหมดมาให้ด้วย

---

## ✅ สถานะการทดสอบ (30 ก.ย. 2026 — รอบ 5)

**เทสผ่านหมดแล้วครับ** รันจริงบน Python 3.11.9 (Windows):

```
127 passed in 2.41s
```

(รอบ 4 มี 104 เคส รอบนี้เพิ่ม `test_ownership.py` + `test_sql_test_scores.py` +
alias เทสใน `test_comments.py` รวมเป็น 127) เวลาลดลงมากเพราะลด bcrypt cost เฉพาะตอนเทส
(ดูหัวข้อ "เรื่องเครื่องที่ใช้ dev" ข้างล่าง — เกี่ยวกับปัญหา RAM ของเครื่อง ไม่ใช่การลดความปลอดภัยจริง)

migration `0005` (ownership + sql_test_scores) ก็เทสแยกต่างหากด้วย: สร้าง DB จำลองแบบ round-4 จริง
(รัน alembic 0001-0004 จริง ไม่ใช่ `create_all()` ที่จะมี column รอบ 5 ติดมาด้วยเงียบ ๆ) ใส่ข้อมูลจำลอง
แล้วรัน `upgrade head` เช็คว่า backfill owner ถูกต้อง + `downgrade` กลับได้สะอาด — ผ่านหมด

(รอบ 3 มี 15 เคส รอบ 4 มี 104 เคส) นอกจาก `pytest` ยังยืนยันของอื่นด้วย:

| เทสอะไร | ผล |
|---|---|
| `pytest` ทั้งชุด 104 เคส | ✅ |
| **Alembic migration ทั้ง 4 ตัว บน DB รูปแบบรอบ 3 จริง** | ✅ ตาราง/column ใหม่ครบ, `CV rejected` → `Rejected`, `email_normalized` backfill ถูก, **ลบ email ซ้ำแล้วใส่ unique index ได้**, `downgrade base` กลับได้ |
| unique index กันซ้ำได้จริง | ✅ insert email ซ้ำ → `IntegrityError` / email ว่าง (NULL) หลายตัวยังอยู่ได้ |
| **ต่อ Azure Blob จริง** | ✅ อัปไฟล์ขึ้น container `resumes` ได้จริง, SAS link เปิดได้ (200), ไม่มี SAS เปิดไม่ได้ (409 = private จริง) |
| **บูตจริงด้วย `uvicorn`** (ไม่ใช่แค่ TestClient) | ✅ |
| `/health` | ✅ คืน `azure_blob` + account + status enum ครบ 9 ค่า |
| login → ได้ JWT + `account` | ✅ |
| อัป CV ซ้ำไฟล์เดิม → อัปเดตไม่สร้างใหม่ + เก็บ version | ✅ v1, v2 |
| คนละคนจริง ๆ → ไม่โดนเตือนผิด ๆ | ✅ `needs_review=0` |
| backfill comment เก่าเข้า `comment_logs` | ✅ 10 comment จาก seed |
| `scripts/gen_frontend_types.py` | ✅ generate `status.ts` ตรงกับ contract |

### 🐛 เจอบั๊กตอนเทส แล้วแก้แล้ว

**บั๊กจริง 1 ตัว — log `STORAGE:` ตอน start ไม่เคยขึ้นเลย**
`build_storage()` ทำงานตอน *import* ซึ่งเกิดก่อน `logging.basicConfig()` ใน `main.py`
แปลว่าบรรทัด `STORAGE: LocalDisk path=...` ถูกกลืนหายไปทุกครั้ง — ซึ่งทำลายจุดประสงค์ของ F1 ทั้งหมด
(ที่ทำมาเพื่อไม่ให้ deploy ผิดเงียบ ๆ) ย้ายไปเรียกใน lifespan แทน + เพิ่มเทสกันไว้แล้ว
**เห็นบั๊กนี้ได้เฉพาะตอนบูตจริงเท่านั้น** `pytest` จับไม่ได้เพราะ TestClient ตั้ง logging ไว้ให้อยู่แล้ว

(อีก 1 อันเป็นบั๊กในเทสเอง — helper `_post()` ชนกันเองตอนส่ง `candidate_id` ซ้ำ ไม่ใช่บั๊กของ product)

### ⚠️ ที่ยังไม่ได้เทส

| เรื่อง | สถานะ |
|---|---|
| ~~Azure Blob กับ Storage Account จริง~~ | ✅ **เสร็จแล้ว** — ใช้ account `mockinteltionhr` (Azure for Students) ต่อจริงและอัปไฟล์ผ่านแล้ว |
| Docker build | ⚠️ เครื่องนี้ไม่มี Docker — ยังไม่มีใครยืนยันว่าขึ้นได้ |
| ต่อกับ LLM ตัวจริงของ Member 4 | ❌ ยังใช้ mock (แก้ import บรรทัดเดียว) |
| PDPA: ตาราง hard-purge ของ comment ที่ soft-delete แล้ว | ❌ ยังไม่มีใครเคาะ policy |

### 🖥️ เรื่องเครื่องที่ใช้ dev — อ่านหน่อยครับ สำคัญ

ตอนรันเทสซ้ำ ๆ 12 รอบ เจอว่า **process Python ตายกลางคัน ~1 ใน 12 รอบ** โดยไม่เกี่ยวกับโค้ด
ไล่ดู Windows Event Log แล้วได้ข้อสรุปชัดเจน:

```
Faulting application: python.exe   Faulting module: python311.dll   0xC0000005 (ACCESS_VIOLATION)
fault offset: 0x50a65 / 0x78476 / 0xeffde / 0x4807b   <-- คนละที่ทุกครั้ง
```

**bug ของซอฟต์แวร์จะพังที่ offset เดิมทุกครั้ง** การพังคนละที่ทุกรอบแบบนี้คืออาการของ memory corruption
และไม่ได้เกิดแค่กับ Python — ใน log 14 วันย้อนหลังมี process อื่นพังแบบเดียวกันเพียบ:

| process ที่พัง | module |
|---|---|
| MicrosoftEdgeUpdate.exe | ntdll.dll (5 ครั้ง) |
| mscorsvw.exe | clr.dll (3 ครั้ง) |
| ProvTool.exe / DrvInst.exe | ntdll.dll |
| powershell.exe | clr.dll |
| **MsMpEng.exe (Windows Defender เอง)** | mpengine.dll |

เมื่อ Windows Defender, ntdll, .NET CLR และ driver installer พังกันหมด → **เป็นปัญหาระดับฮาร์ดแวร์
เกือบแน่นอนว่าเป็น RAM** (หรือ XMP/overclock ที่ไม่นิ่ง) ไม่ใช่ปัญหาของโปรเจกต์นี้

> อันนี้น่าจะเป็นคำอธิบายของเรื่อง **"Docker บนเครื่องผมพัง ลอง 6 รอบ error คนละแบบทุกครั้ง reboot ก็ไม่หาย"**
> ที่เขียนไว้ตั้งแต่รอบ 3 ด้วย — ไม่ใช่ WSL2 เพี้ยน แต่เป็นเครื่อง

**ควรทำ:** รัน `mdsched.exe` (Windows Memory Diagnostic) หรือ MemTest86 · ลองถอดแรมมาเสียบใหม่ ·
ถ้าเปิด XMP/EXPO ใน BIOS อยู่ให้ลองปิดดู

**ผลต่อการอ่านผลเทส:** ถ้าเทสแดงบนเครื่องนี้ ให้ดู exit code ก่อน —
`1` = เทสพังจริง ต้องแก้ · `-1073741819` / `-1073740791` = เครื่องพัง รันใหม่
(จาก 12 รอบล่าสุด: ผ่านสะอาด 11, เทสพังจริง **0**, เครื่องพัง 1)

### วิธีรันเทสเอง

```bash
cd backend
python -m venv venv                # ถ้า venv เดิมพัง ลบทิ้งแล้วสร้างใหม่
venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

ถ้าฐานข้อมูล dev เดิมมีข้อมูลอยู่แล้ว ต้อง migrate ก่อน (ดูหัวข้อ Alembic ข้างล่าง)

---

## ฟีเจอร์รอบ 4

### 🔐 F2 — บัญชี HR หลายคน + login จริง

ตาราง `hr_accounts` — รหัสผ่าน hash ด้วย bcrypt **ไม่เคยเก็บ/log/คืน plaintext หรือ hash เลย**
(`HRAccountOut` ไม่ได้ประกาศ field นั้นไว้ตั้งแต่แรก จะหลุดออกไปทาง `model_dump()` ไม่ได้)

| Method | Path | ใคร |
|---|---|---|
| `POST` | `/api/auth/login` | ทุกคน → token + `account` |
| `GET` | `/api/auth/me` | คนที่ login แล้ว — **ต้องเรียกก่อนโชว์ปุ่มแก้/ลบ comment** |
| `POST` | `/api/auth/change-password` | ตัวเอง |
| `GET` `POST` | `/api/hr-accounts` | admin |
| `PUT` `DELETE` | `/api/hr-accounts/{id}` | admin — **DELETE = ปิดใช้งาน ไม่ได้ลบจริง** |
| `POST` | `/api/hr-accounts/{id}/reset-password` | admin |

- **role**: `admin` / `hr` / `line_manager` / `viewer` — เอาไปกำหนด comment_type อัตโนมัติด้วย
- **ลบ = soft delete** เพราะ `comment_logs` อ้างถึง account อยู่ ถ้าลบจริงประวัติ comment จะกำพร้า
- **ปิดบัญชีแล้วมีผลทันทีที่ request ถัดไป** ไม่ต้องรอ token หมดอายุ 8 ชม.
  (`get_current_account()` โหลดจาก DB ทุกครั้ง ไม่เชื่อ token เปล่า ๆ)
- **rate limit**: ผิดรหัส 5 ครั้งใน 15 นาทีต่อ username → `429` + header `Retry-After`
- **ข้อความ error เหมือนกันหมด** ไม่ว่าจะ "ไม่มี user นี้" / "รหัสผิด" / "บัญชีถูกปิด" — กันคนเดาว่ามี username ไหนอยู่จริง
- บัญชีแรกยัง seed จาก `.env` (`SEED_ADMIN_*`) แต่ **เฉพาะตอนตารางว่างเท่านั้น**
  และถ้ายังใช้รหัส default อยู่จะ log warning ตอน start

### 💬 F3 — `comment_logs` แยกตาราง

แต่ละ comment เป็น row ของตัวเอง มีคนเขียน มีเวลา แก้ได้ ลบได้

| Method | Path | กติกา |
|---|---|---|
| `GET` | `/api/candidates/{id}/comments` | ใครก็ได้ที่ login · `?comment_type=hr` · เรียง `commented_at` ใหม่→เก่า |
| `POST` | `/api/candidates/{id}/comments` | body: `{comment, comment_type?, commented_at?}` เท่านั้น ที่เหลือ server ใส่เอง |
| `PUT` | `/api/comments/{comment_id}` | **403 ถ้าไม่ใช่คนเขียน** (admin ก็แก้ของคนอื่นไม่ได้) |
| `DELETE` | `/api/comments/{comment_id}` | soft delete · **403 ถ้าไม่ใช่คนเขียน หรือ admin** |

**ทำไมมี 2 timestamp:** `commented_at` คือเวลาที่โชว์ **แก้ได้** (HR ย้อนวันที่คุยโทรศัพท์เมื่ออังคารที่แล้วได้)
ส่วน `created_at` / `updated_at` เป็นของ server **แก้ไม่ได้เด็ดขาด** เป็น audit trail จริง
ถ้าให้แก้ timestamp ได้หมด audit log ก็ไม่มีความหมาย — แยก 2 ตัวเลยได้ทั้งสองอย่าง
UI ให้โชว์ `commented_at` แล้วถ้า `is_edited` เป็น true ให้ขึ้นคำว่า "แก้ไขแล้ว"

**ทำไม snapshot ชื่อคนเขียน:** ถ้าเปลี่ยนชื่อหรือปิดบัญชีทีหลัง comment เก่าต้องยังขึ้นชื่อคนที่เขียนตอนนั้น
→ ให้ render `author_name` ที่ติดมากับ comment ไม่ใช่ join ไปเอาชื่อปัจจุบัน

**กติกาฝั่ง server ที่ frontend หลอกไม่ได้:**
- `author_account_id` / `author_name` มาจาก **JWT เท่านั้น** ส่งมาใน body ก็โดนทิ้ง
- `candidate_id` มาจาก URL เท่านั้น แก้ไม่ได้
- เช็กเจ้าของที่ server — **ซ่อนปุ่มใน UI ไม่นับเป็นการป้องกัน**
- `comment` ว่าง (หรือมีแต่ช่องว่าง) → `400`

**ของเดิมย้ายให้แล้ว:** `hr_comment` / `line_manager_comment` ที่มีข้อความอยู่ถูก backfill เข้า `comment_logs`
ให้อัตโนมัติตอน start ครั้งแรก 2 field เดิม **ยังอยู่ใน schema** แต่กลายเป็น read-only ที่ server คำนวณให้
(= ข้อความของ comment ล่าสุดของ type นั้น) → ของเดิมที่เขียนไว้ยังแสดงผลได้ ไม่พังทันที
**รอบหน้าจะลบ 2 field นี้ทิ้ง** ช่วยย้ายไปอ่านจาก `/comments` ด้วยนะครับ

### 📄 F4 — อัป CV ซ้ำคนเดิม = อัปเดต ไม่ใช่สร้างใหม่

**ตัดสินว่า "คนเดียวกัน" ยังไง:** ใช้ **email (ตัดช่องว่าง + พิมพ์เล็ก) ตรงกันเท่านั้น**
ถ้าไม่ตรง email แต่ยังดูคล้าย (เบอร์โทรตรง / ชื่อ+ตำแหน่งตรง) → **หยุดถาม HR** (ดูข้อ 6 ข้างบน)
ถ้าไม่ตรงอะไรเลย → สร้างคนใหม่

> **ไม่ merge อัตโนมัติจากชื่อคล้าย ๆ เด็ดขาด** — "สมชาย ใจดี" 2 คนถูกรวมกันเองเมื่อไหร่
> ประวัติของคนนึงหายถาวร undo ไม่ได้ ส่วนถ้าเดาผิดแล้ว HR ต้องกดรวมเอง แค่เสียเวลาคลิกเดียว

**ตอนนี้ email ห้ามซ้ำแล้วในระดับ database** — มี `UNIQUE INDEX` บน `email_normalized`
(migration `0003` ลบ candidate ที่ email ซ้ำทิ้งก่อน เก็บตัวที่เก่าที่สุดไว้) ถ้ามีอะไรพยายามสร้าง
email ซ้ำ จะได้ `409` ไม่ใช่ `500` ส่วน candidate ที่ไม่มี email เก็บเป็น `NULL` ไม่ใช่ `""`
เลยมีกี่คนก็ได้ไม่ชนกัน

**อัปซ้ำแล้วอะไรเปลี่ยน / อะไรไม่เปลี่ยน:**

| กลุ่ม | field | ผล |
|---|---|---|
| จาก CV | `full_name` `email` `phone` `summary` `skills` `experience` `experience_total` `education` `current_salary` `expected_salary` `extraction_confidence` `raw_text_snippet` | **เขียนทับ** |
| ไฟล์ | `resume_url` `resume_filename` `upload_status` | **เขียนทับ** (ของเก่าเก็บเป็น version) |
| ของ HR | `status` `before_rejected_status` `applied_position` `location` | **ไม่แตะ** |
| ตัวตน | `candidate_id` `created_at` | **ไม่แตะ** |
| comment | — | **ไม่แตะ โดยการออกแบบ** |

comment รอดโดยไม่ต้องมี logic merge เลยสักบรรทัด เพราะมันผูกกับ `candidate_id` ซึ่งไม่เปลี่ยน —
ถ้าเก็บ comment ไว้ใน candidate แล้วเขียน routine merge บั๊กตัวเดียวก็ลบโน้ต HR หายหมด
อันนี้เอา failure mode ออกไปเลย ไม่ใช่ไปนั่งกัน

**กันข้อมูลดีหาย:** ถ้า CV ใหม่สกัดได้ค่าว่างแต่ของเดิมมีค่าอยู่ → **ไม่เขียนทับ** และบันทึกลง log
(เช่น PDF สแกนที่อ่านไม่ออก) ส่วน `extraction_confidence` ต่ำ → ยังเขียนทับตามปกติ (ทีมเคาะแล้ว)
แต่มี change log ให้ HR ย้อนดูได้

**ไฟล์เก่าไม่ถูกทับ:** ทุกครั้งที่อัปจะเก็บเป็น version ใหม่ (`<candidate_id>/v1/`, `v2/`, ...)
- `GET /api/candidates/{id}/resume-versions` → ดู CV ทุกเวอร์ชัน
- `GET /api/candidates/{id}/resume-url?version=1` → ขอลิงก์ของเวอร์ชันที่ต้องการ (ไม่ใส่ = อันล่าสุด)

**บอก HR ว่าอะไรเปลี่ยน:** `GET /api/candidates/{id}/changes` → diff ระดับ field ทุกครั้งที่มีการแก้
(`source` = `reupload` / `manual_edit` / `reupload_skipped_empty`)

**อัปซ้ำคนที่ `Hired` หรือ `Rejected` แล้ว:** ทำได้ ข้อมูลอัปเดต status คงเดิม (ทีมเคาะแล้ว)

> ⚠️ **แก้ mock extraction ด้วย** — ของเดิมสุ่มผลลัพธ์ทุกครั้งที่เรียก แปลว่าอัปไฟล์เดิมซ้ำจะได้คนละคน
> ซึ่งทำให้ F4 ทั้งฟีเจอร์เทสไม่ได้และ demo ไม่ได้ ตอนนี้เป็น **pure function ของไฟล์**
> (seed = SHA-256 ของ bytes, email คำนวณจาก seed ตรง ๆ ไม่ได้สุ่ม) → ไฟล์เดิม = คนเดิมเสมอ
> **signature ไม่เปลี่ยน** การรวมงานกับ Member 4 ยังเป็นแก้ import บรรทัดเดียวเหมือนเดิม

### 🔄 F5 — `before_rejected_status` + ประวัติ status

จำไว้ว่าตอนโดนปฏิเสธ candidate อยู่ขั้นไหน → `GET`/list คืนมาให้ใช้ทำ badge "ถูกปฏิเสธตอนสัมภาษณ์"

- **read-only 100%** ส่งมาใน `PUT` ก็โดนทิ้ง ("ถ้า frontend set ได้ สักวันมันจะถูก set ผิด")
- เงื่อนไขผูกกับ **การเปลี่ยนสถานะ** ไม่ใช่ค่าปัจจุบัน — ไม่งั้น `PUT` ครั้งถัดไปที่แก้ field อื่นจะไป
  stamp ทับเป็น `"Rejected"` ทำลายค่าที่อุตส่าห์เก็บไว้ (มีเทสจับเคสนี้โดยเฉพาะ)
- ออกจากสถานะ rejected เมื่อไหร่ → ล้างเป็น `""`
- `POST /api/candidates/{id}/restore` → ย้อนกลับไปขั้นเดิมในคำสั่งเดียว
- `GET /api/candidates/{id}/status-history` → ประวัติการเปลี่ยน status ทั้งหมด ใครเปลี่ยน เมื่อไหร่ เพราะอะไร
  (ตัวนี้คือ audit log ที่ M3 ต้องการ ส่วน `before_rejected_status` เป็นแค่ค่าย่อไว้ให้ Kanban ไม่ต้อง join)

### ☁️ F1 — ย้ายไป Azure Blob ของเราเอง

**ส่วนที่เป็นโค้ด ทำแล้ว:**
- **กันอัปผิด account**: ตั้ง `AZURE_STORAGE_ACCOUNT_NAME` ไว้ ถ้า connection string ชี้ไป account อื่น
  → **app ไม่ยอมขึ้น** ฟ้องทันที (ดีกว่าขึ้นได้แล้วเขียน CV คนสมัครงานไป subscription ผิด)
- `ALLOW_COMPANY_STORAGE=false` เป็น default → จะใช้ account ของบริษัทต้องเปิดเอง
- **log ตอน start ให้เห็นชัด ๆ**: `STORAGE: AzureBlob account=... container=...` หรือ `STORAGE: LocalDisk path=...`
- **`GET /health` บอก account/container ที่ใช้อยู่** (ชื่อเท่านั้น ไม่มี key) — ทุกคนเช็กได้เองว่ายิงไป account ไหน
- fallback ไป local disk ยังอยู่ แต่ตอนนี้ **log WARNING ทุกครั้ง** ไม่เงียบ ๆ เหมือนเดิม
- container ยัง private + SAS 60 นาที (PDPA)
- `scripts/migrate_blobs.py` — ย้าย blob ข้าม account + แก้ path ใน DB (มี `--dry-run`)

**ส่วนที่ทำแทนไม่ได้ ต้องมีคนไปทำ:**
1. **provision Azure Storage Account + container จริง** ใน subscription ที่ทีมคุมเอง
2. เอา connection string ใส่ `.env` ของทุกคน
3. **ทดสอบ end-to-end กับ account จริงครั้งแรก** — ยังไม่เคยมีใครทำ และนี่คือส่วนที่ไม่เคยเทสใหญ่ที่สุดของ backend

---

## 🗄️ Alembic (ของใหม่ — สำคัญถ้ามี DB เดิมอยู่)

รอบ 4 เพิ่ม **6 ตาราง** (`hr_accounts`, `comment_logs`, `resume_versions`, `status_history`,
`candidate_change_log`, `pending_uploads`) + **3 column ใหม่** ใน `candidates`
+ **เปลี่ยนชื่อ status** + **unique index บน email**

รอบ 5 เพิ่มอีก **2 ตาราง** (`ownership_history`, `sql_test_scores`) + **1 column ใหม่**
(`candidates.owner_account_id`) — migration `0005` ยังทำ **backfill owner ให้ candidate เก่าทุกตัว
อัตโนมัติ** ด้วย (ดึงจาก `status_history` แถวแรกสุด) ไม่ต้องทำอะไรเพิ่มนอกจาก `alembic upgrade head`

มี migration 5 ตัว: `0001` ตารางใหม่ · `0002` เปลี่ยนชื่อ status · `0003` ลบ email ซ้ำ + unique index ·
`0004` ตาราง `pending_uploads` · `0005` ownership + sql_test_scores + backfill owner

- ตาราง**ใหม่**เกิดเองจาก `create_all` ตอน start → ไม่ต้องทำอะไร
- **column ใหม่, การเปลี่ยนชื่อ status, unique index ไม่เกิดเอง** ถ้ามีไฟล์ `dev.db` เดิมอยู่

| สถานการณ์ | ต้องทำ |
|---|---|
| มี `dev.db` จากรอบ 3 อยากเก็บข้อมูล | `alembic upgrade head` |
| ลบ `dev.db` ทิ้งแล้วเปิด app ใหม่ (create_all สร้างตารางให้ครบแล้ว) | `alembic stamp head` — บอก alembic ว่า DB นี้อยู่ revision ล่าสุดแล้ว **อย่าใช้ `upgrade`** มันจะพังเพราะตารางมีอยู่แล้ว |
| ไม่แคร์ข้อมูล dev | ลบ `backend/data/dev.db` แล้ว start ใหม่ (seed ให้เอง) |

```bash
cd backend
alembic upgrade head
```

> ⚠️ **`0003` ลบข้อมูลทิ้งจริง** — candidate ที่ email ซ้ำกันจะถูกลบให้เหลือตัวที่เก่าที่สุดตัวเดียว
> (พร้อม comment / version / history ของตัวที่ถูกลบ) ทีมเคาะแล้วว่าของซ้ำพวกนี้เป็น test data
> ไม่ใช่ข้อมูลจริง เลยลบให้สะอาดไปเลยแทนที่จะสร้างเครื่องมือ merge มารองรับข้อมูลที่ไม่มีใครต้องการ
> **`downgrade` เอา index ออกได้ แต่เอา row ที่ลบไปแล้วคืนไม่ได้**

> ยัง default เป็น SQLite เหมือนเดิม ยังไม่ย้าย Postgres รอบนี้ — Postgres ยัง comment ไว้
> ใน `docker-compose.yml` เหมือนเดิม สลับได้ด้วยการเปลี่ยน `DATABASE_URL` อย่างเดียว

---

## 📁 ไฟล์ contract ที่ต้องดึงไปใหม่

| ไฟล์ | สถานะ |
|---|---|
| `shared-contracts/schema.json` | **v2.3.0** — เพิ่ม `owner_account_id`/`owner_name` (additive, ไม่ breaking) |
| `shared-contracts/ownership-schema.json` | 🆕 `OwnershipHistory` + `transferRequest` + endpoint ทั้ง 2 ตัว |
| `shared-contracts/sql-test-score-schema.json` | 🆕 `SqlTestScore` + endpoint ทั้ง 2 ตัว (contract ของเครื่องมือจริงยังไม่ล็อก — อ่านหมายเหตุในไฟล์) |
| `backend/FRONTEND_CONTRACT_GAPS.md` | 🆕 สรุป 6 จุดที่ `feature/frontend-update` กับ backend คนละ contract กัน — ต้องให้ทีมเคาะ ไม่ใช่แก้เอง |
| `shared-contracts/pending-upload-schema.json` | คิวรอตัดสิน + endpoint ทั้ง 4 ตัว |
| `shared-contracts/hr-account-schema.json` | บัญชี HR + shape ของ login response |
| `shared-contracts/comment-log-schema.json` | comment + สรุป endpoint (path alias ใหม่ยังไม่อยู่ในนี้ ดู "ข้อ 4" ด้านบน) |
| `shared-contracts/status.ts` | **generate จาก schema.json** — `import` ไปใช้ อย่าพิมพ์ string status เอง |
| `shared-contracts/mock-comments.json` | comment ปลอม 13 อัน ทำ UI thread ได้เลยไม่ต้องรอ API |
| `shared-contracts/mock-candidates.json` | อัปเดต — status ใหม่ + field ใหม่ (ยังไม่มี owner เพราะเป็น mock ไม่ผ่าน backend จริง) |

> ⚠️ ไฟล์ JSON พวกนี้ **อย่าเซฟทับด้วย Notepad หรือ PowerShell `Set-Content`** บน Windows
> เพราะมันจะแอบใส่ BOM เข้าไปหน้าไฟล์ แล้ว `json.load()` ฝั่ง Python จะพังด้วย error
> `Expecting value: line 1 column 1` ที่อ่านไม่ออกเลยว่าเกิดจากอะไร
> (ตอนนี้ฝั่ง backend อ่านด้วย `utf-8-sig` แล้วเลยทนได้ แต่ฝั่ง JS/TS อาจไม่ทน)

regenerate `status.ts` ใหม่ได้ด้วย `cd backend && python scripts/gen_frontend_types.py`

---

## วิธีรัน

### Docker
```bash
docker compose up --build
```
API: http://localhost:8000 · Swagger UI: http://localhost:8000/docs · ล้างข้อมูล: `docker compose down -v`

### Python ตรง ๆ
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  /  macOS-Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### ขอ token
```bash
curl -X POST localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"password123"}'
```
```json
{ "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "account": { "account_id": "…", "username": "admin", "full_name": "Seed Admin", "role": "admin", "is_active": true }
}, "error": null }
```

---

## Endpoint ทั้งหมด (ถึงรอบ 5)

| Method | Path | ได้อะไร |
|---|---|---|
| `POST` | `/api/auth/login` | token + account |
| `GET` | `/api/auth/me` | ตัวเองเป็นใคร |
| `POST` | `/api/auth/change-password` | เปลี่ยนรหัสตัวเอง |
| `GET` `POST` | `/api/hr-accounts` | admin — list / สร้างบัญชี |
| `PUT` `DELETE` | `/api/hr-accounts/{id}` | admin — แก้ / ปิดใช้งาน |
| `POST` | `/api/hr-accounts/{id}/reset-password` | admin |
| `GET` | `/api/candidates` | list ย่อ + filter/search (🆕 รอบ 5: `?owner_account_id=`) |
| `GET` `PUT` `DELETE` | `/api/candidates/{id}` | ดู / แก้ / ลบ |
| `POST` | `/api/candidates/upload` | อัป CV หลายไฟล์ |
| `GET` | `/api/candidates/{id}/resume-url` | ลิงก์ CV (`?version=` ได้) |
| `GET` | `/api/candidates/{id}/resume-versions` | CV ทุกเวอร์ชัน |
| `GET` `POST` | `/api/candidates/{id}/comments` | comment |
| `PUT` `DELETE` | `/api/comments/{comment_id}` | แก้ / ลบ comment |
| `PUT` `DELETE` | `/api/candidates/comments/{comment_id}` | 🆕 alias ของบรรทัดบน (ตรงกับที่ `feature/frontend-update` เรียก) |
| `POST` | `/api/candidates/{id}/restore` | ย้อนจากสถานะ rejected |
| `GET` | `/api/candidates/{id}/status-history` | ประวัติ status |
| `GET` | `/api/candidates/{id}/changes` | diff ระดับ field |
| `POST` | `/api/candidates/{id}/transfer-ownership` | 🆕 โอนความเป็นเจ้าของ (เจ้าของเดิม/admin เท่านั้น) |
| `GET` | `/api/candidates/{id}/ownership-history` | 🆕 ประวัติเจ้าของทั้งหมด |
| `POST` | `/api/candidates/{id}/sql-test-score` | 🆕 บันทึกคะแนนจากเครื่องมือ SQL test ภายนอก |
| `GET` | `/api/candidates/{id}/sql-test-scores` | 🆕 คะแนนทั้งหมดของ candidate นี้ |
| `GET` | `/api/pending-uploads` | คิว CV ที่รอ HR ตัดสิน |
| `POST` | `/api/pending-uploads/{id}/update` | "คนเดิม" → merge เข้าคนที่มีอยู่ |
| `POST` | `/api/pending-uploads/{id}/create-new` | "คนละคน" → สร้างใหม่ |
| `DELETE` | `/api/pending-uploads/{id}` | "ไม่เอา" → ทิ้งไฟล์ |
| `GET` | `/health` | บอก storage backend + status enum ด้วย |

response envelope เหมือนเดิมทุกอัน: `{data, error}` · `400` ข้อมูลไม่ผ่าน · `401` token · `403` ไม่ใช่เจ้าของ/ไม่มีสิทธิ์ · `404` ไม่เจอ · `409` ซ้ำ · `429` login ถี่เกิน

---

## ถึงแต่ละคน

### 🟦 Member 1 (Dashboard)
- ดึง `shared-contracts/` ไปใหม่ทั้งโฟลเดอร์ — มีไฟล์ใหม่ 4 ไฟล์
- ⚠️ **`"CV rejected"` → `"Rejected"`** แก้ทุกที่ที่ hardcode ไว้
  แล้ว `import { CANDIDATE_STATUSES, isRejected } from 'shared-contracts/status.ts'` แทนการพิมพ์เอง
- `before_rejected_status` มาใน list แล้ว → ทำ badge "ถูกปฏิเสธตอน X" ได้เลย ไม่ต้องยิง API เพิ่ม
- comment thread: อ่านจาก `GET /api/candidates/{id}/comments` (มี `mock-comments.json` ให้ทำ UI ก่อนได้)
  - ปุ่มแก้/ลบ ให้เทียบ `author_account_id` กับ `account_id` จาก `GET /api/auth/me`
  - โชว์ `commented_at` และถ้า `is_edited` เป็น true ให้ขึ้น "แก้ไขแล้ว"
- `possible_duplicate_of` ไม่ว่าง = อาจซ้ำกับคนอื่น → ขึ้นป้ายเตือนให้ HR ดู
  (ตอนนี้จะมีค่าเฉพาะคนที่ HR กดยืนยันแล้วว่า "คนละคน" — ดูข้อ 6)
- ถ้าจะทำหน้ารวม "งานค้าง" ของ HR → `GET /api/pending-uploads` คือคิว CV ที่รอตัดสิน
- 🆕 **รอบ 5**: candidate ทุกตัวมี `owner_account_id` / `owner_name` แล้ว — ถ้าจะทำหน้า "งานของฉัน"
  ใช้ `GET /api/candidates?owner_account_id=<account_id ของตัวเอง>` ได้เลย
- 🆕 ปุ่ม "โอนให้คนอื่นดูแลต่อ" → `POST /api/candidates/{id}/transfer-ownership` (โชว์ปุ่มนี้เฉพาะ
  ตอน `owner_account_id` ตรงกับ `account_id` ของตัวเอง หรือ role ตัวเองเป็น `admin`)
- 🆕 ถ้าจะโชว์คะแนนจากเครื่องมือ SQL test → `GET /api/candidates/{id}/sql-test-scores`
  (list อาจว่างเปล่าถ้ายังไม่มีใครส่งคะแนนมา — ยังไม่มี UI ฝั่งไหนเขียนเข้าเลยตอนนี้)

### 🟩 Member 2 (Upload + Edit)
- ⚠️ **`"CV rejected"` → `"Rejected"`** ในตัวกรอง / dropdown แก้ status
- ⚠️ **response ของ upload เพิ่ม `updated[]`** — ต้องแยกให้ผู้ใช้เห็นว่าอันไหนเพิ่มใหม่ อันไหนเขียนทับของเดิม
  `count` = `created.length + updated.length`
- 🔴 **response ของ upload เพิ่ม `needs_review[]` ด้วย — อันนี้ต้องทำ UI เพิ่ม**
  ไฟล์ในนี้ **ยังไม่เข้า database** รอ HR ตัดสินก่อน ต้องขึ้น dialog ให้เลือก 2 ทาง:
  ```js
  for (const item of res.data.needs_review) {
    // โชว์ item.extracted_preview เทียบกับ item.duplicate_candidates
    // ปุ่ม "เป็นคนเดิม"  -> POST /api/pending-uploads/{item.pending_upload_id}/update
    // ปุ่ม "คนละคน"     -> POST /api/pending-uploads/{item.pending_upload_id}/create-new
    // ปุ่ม "ไม่เอาไฟล์นี้" -> DELETE /api/pending-uploads/{item.pending_upload_id}
  }
  ```
  **ถ้าไม่ทำ → CV ใบนั้นหายไปเฉย ๆ ไม่มีใครรู้** ถ้า user ปิด dialog ไปก่อน ยังตามเก็บได้ที่
  `GET /api/pending-uploads` (แนะนำมี badge ค้างไว้ว่ามีกี่ใบรออยู่)
- ตอนกด "เป็นคนเดิม" **ไม่ต้องส่งว่า candidate ไหน** — ถ้าซ้ำหลายคน server เลือกคนที่
  `updated_at` ใหม่สุดให้เอง
- **`hr_comment` / `line_manager_comment` เขียนผ่าน `PUT` ไม่ได้แล้ว** ส่งไปก็เงียบ ๆ ไม่เข้า
  ต้องเปลี่ยนไปใช้ `POST /api/candidates/{id}/comments`
- login แล้วเก็บ `account` ที่ติดมาด้วย
- `before_rejected_status` / `possible_duplicate_of` เป็น read-only ส่งใน `PUT` ก็โดนทิ้ง
- อยากดู CV เวอร์ชันเก่า → `GET /api/candidates/{id}/resume-versions`

### 🟨 Member 4 (LLM Extraction)
**ยังไม่ต้องแก้อะไรครับ** signature เดิมทุกตัวอักษร:
```python
extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict
```
- `hr_comment` / `line_manager_comment` ที่ฝั่งนั้นบังคับให้เป็น `""` อยู่แล้ว
  → **รอบหน้าที่ลบ 2 field นี้ทิ้ง ไม่กระทบเลย**
- ขอเพิ่มอย่างเดียว: ผลลัพธ์ควร **deterministic ตามไฟล์** (ไฟล์เดิม → email เดิม)
  เพราะ F4 ใช้ email ตัดสินว่าเป็นคนเดียวกัน ถ้าใช้ LLM ช่วยสกัด ขอ `temperature=0`
  หรือดึง email ด้วย regex ไปเลยจะนิ่งกว่า
- ยังฝากไว้เหมือนเดิม: ทำ `llm-service/cv-parsing/` เป็น package (`__init__.py`)
  + เพิ่ม dependency ลง `backend/requirements.txt`

---

## ประวัติงาน

### รอบ 5 — Ownership / SQL-test score / comment path alias (30 ก.ย. 2026)
- ระบบ ownership: `owner_account_id` ตั้งครั้งเดียวตอนสร้าง (ใครอัป CV คนแรกเป็นเจ้าของ),
  ไม่เปลี่ยนจากอัปซ้ำ/resolve pending-upload, โอนได้ทางเดียวคือ `transfer-ownership`
  (เจ้าของเดิม/admin เท่านั้น, ปฏิเสธการรับโอนด้วยตัวเอง), ประวัติเต็มใน `ownership_history`
- `sql_test_scores` — เก็บคะแนนจากเครื่องมือภายนอกที่ยังไม่ล็อก contract, `score` ต้อง finite,
  `raw_payload` เก็บของเดิมไว้เผื่อ, ไม่มีการ overwrite (ทุกครั้งเป็น row ใหม่)
- 🐛 แก้บั๊กจริง: ส่ง `score` เป็น `Infinity`/`NaN` ทำให้ **error handler เองพัง** (`500` แทน `400`)
  เพราะ Starlette/FastAPI ปฏิเสธ non-finite float ทั้งใน response และใน validation-error payload
  → เพิ่ม `_json_safe()` sanitizer ใน `main.py` + เทส regression
- comment path alias `/candidates/comments/{id}` ให้ตรงกับที่ `feature/frontend-update` เรียกจริง
- migration `0005`: เพิ่ม `ownership_history`, `sql_test_scores`, column `candidates.owner_account_id`
  + backfill owner ให้ candidate เก่าทุกตัวจาก `status_history` อัตโนมัติ
- 🐛 แก้บั๊ก (พบระหว่างเทส ไม่ใช่ของ product): เทสเคยยิงไปโดน Azure Blob จริง (`mockinteltionhr`)
  ทุกครั้งที่รันเทส เพราะ `conftest.py` ไม่ได้ override `AZURE_STORAGE_CONNECTION_STRING` เลย
  → บังคับเป็นค่าว่างในเทสแล้ว
- เขียน `FRONTEND_CONTRACT_GAPS.md` สรุป 6 จุดที่ contract ของ `feature/frontend-update` กับ backend
  ไม่ตรงกัน (login ไม่ได้ต่อ backend จริง, upload field/duplicate-flow คนละ shape,
  comment path/id-type/role-dropdown, status-history embed vs endpoint แยก) — รอทีมเคาะ
  แก้ไปแล้วเฉพาะจุดที่ปลอดภัยและไม่ต้องเถียง (comment path alias)
- contract v2.3.0 (`owner_account_id`/`owner_name`) — additive ไม่ breaking
- เทสเพิ่ม `test_ownership.py`, `test_sql_test_scores.py` รวมเป็น **127 เคส ผ่านหมด**

### รอบ 4 — HR accounts / comment_logs / re-upload / audit (18-19 ก.ย. 2026)
- F6 enum มีที่มาที่เดียว + assert ตอน start + generate TypeScript
  + **เปลี่ยนชื่อ `CV rejected` → `Rejected`** (contract v2.1.0, มี migration `0002`)
- F1 guardrail กัน account ผิด + `/health` + log ดัง ๆ + script ย้าย blob
- F2 ตาราง `hr_accounts` + bcrypt + `/me` + rate limit + soft delete
- F3 ตาราง `comment_logs` + 4 endpoint + backfill ของเดิม + 2 field เดิมเป็น read-only
- F5 `before_rejected_status` (ผูกกับ transition) + `status_history` + `/restore`
- F4 อัปซ้ำ = อัปเดต + merge policy เป็นตาราง + resume versioning + change log + `updated[]`
- **ต่อ Azure Blob จริงสำเร็จ** (`mockinteltionhr`) ทดสอบ end-to-end ครบ
- **คิวรอตัดสิน `pending_uploads`** — ซ้ำแบบไม่ชัวร์ → ถาม HR แทนที่จะเดา (contract v2.2.0)
- **`UNIQUE INDEX` บน email** + `409` แทน `500` ตอนชนกัน (migration `0003` ลบของซ้ำก่อน)
- Alembic 4 ตัว (`0001`-`0004`) + เทส 104 เคส **ผ่านหมด**
- 🐛 แก้บั๊ก: log `STORAGE:` ตอน start ไม่เคยขึ้น เพราะ `build_storage()` รันก่อน `logging.basicConfig()`

### รอบ 3 — `3d9e555` Azure Blob + แก้บั๊ก
- เพิ่ม `AzureBlobStorage` สลับด้วย env var, SAS link, fallback อัตโนมัติ
- 🐛 แก้บั๊ก: endpoint `GET /api/candidates/{id}/resume-url` หายไปจากโค้ดตอนรอบ 2 — ใส่คืนแล้ว

### รอบ 2 — `fa2b19a` Task extension 5 ข้อ
- Login + JWT, อัปโหลดหลายไฟล์, candidate_id เลขรัน 7 หลัก, ลบแบบมีเงื่อนไข + `upload_status`, filter/search

### รอบ 1 — `7a58615` วางโครง backend
- FastAPI + SQLite + เก็บไฟล์ลง disk, CRUD ครบ, response envelope, contract + mock 9 คน, mock extraction, Docker

---

## ไฟล์อยู่ไหนบ้าง

```
backend/
  app/
    main.py          FastAPI app, CORS, error envelope, /health, assert status ตอน start,
                      🆕 _json_safe() sanitizer กัน non-finite float พังตอน validation error
    config.py        ตั้งค่าทั้งหมดจาก env (🆕 bcrypt_rounds)
    statuses.py      status enum ที่มาที่เดียว (โหลดจาก schema.json)
    auth.py          JWT + get_current_account() + require_role()
    security.py      bcrypt + rate limiter
    database.py      SQLAlchemy
    models_db.py     candidates + 8 ตาราง (🆕 ownership_history, sql_test_scores)
    schemas.py       Pydantic = ตัวสัญญาจริงในโค้ด (🆕 ownership/sql-test schemas)
    services.py      merge policy / status transition / change log / dup logic
                      (🆕 owner_name_for, record_ownership_change, transfer_ownership,
                      assign_initial_owner, record_sql_test_score) ไม่มี HTTP
    storage.py       LocalDisk / AzureBlob + guardrail + versioned path
    extraction.py    mock ของ Member 4 (pure function ของไฟล์)
    seed.py          seed admin + mock candidates + backfill comment + 🆕 backfill owner
    routers/
      auth.py            login / me / change-password
      hr_accounts.py     จัดการบัญชี (admin)
      candidates.py      candidate + upload + versions + history + changes
                          + 🆕 transfer-ownership / ownership-history / sql-test-score(s)
      comments.py        comment_logs + 🆕 path alias `/candidates/comments/{id}`
      pending_uploads.py คิวรอตัดสิน create-or-update
  alembic/           migration 0001-0005 (🆕 0005 = ownership + sql_test_scores + backfill)
  scripts/
    migrate_blobs.py       ย้าย blob ข้าม Azure account
    gen_frontend_types.py  generate status.ts จาก schema.json
  tests/             127 เคส ผ่านหมด (🆕 test_ownership.py, test_sql_test_scores.py)
  FRONTEND_CONTRACT_GAPS.md  🆕 6 จุดที่ contract ฝั่ง frontend/backend ไม่ตรงกัน — รอทีมเคาะ
shared-contracts/
  schema.json                 v2.3.0
  ownership-schema.json       🆕
  sql-test-score-schema.json  🆕
  pending-upload-schema.json  
  hr-account-schema.json      
  comment-log-schema.json     
  status.ts                   generated
  mock-candidates.json        
  mock-comments.json          
```

มีอะไรไม่ชัดทักได้เลยครับ 🙏
