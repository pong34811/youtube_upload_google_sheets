# 🎬 YouTube Upload via Google Sheets

ระบบอัปโหลดวิดีโอขึ้น YouTube อัตโนมัติ โดยอ่านข้อมูลจาก Google Sheets

## 📋 คุณสมบัติ

- อ่านข้อมูลวิดีโอจาก Google Sheets (title, description, tags, category, privacy)
- อัปโหลดวิดีโอแบบ Resumable Upload (รองรับไฟล์ใหญ่)
- ตั้ง Thumbnail อัตโนมัติ
- เพิ่มวิดีโอลง Playlist อัตโนมัติ
- รองรับ Scheduled Publish (ตั้งเวลาเผยแพร่)
- อัปเดตสถานะใน Sheet อัตโนมัติ (WAIT_UPLOAD → UPLOADING → UPLOADED / FAILED)
- บันทึก Video ID กลับไปใน Sheet

## 📊 Google Sheets Format

| Column | Field          | Description                              |
|--------|----------------|------------------------------------------|
| A      | state          | `WAIT_UPLOAD` / `UPLOADING` / `UPLOADED` / `FAILED` |
| B      | video_title    | ชื่อวิดีโอ                               |
| C      | description    | คำอธิบาย (รองรับ Markdown)              |
| D      | tags           | แท็กคั่นด้วยเครื่องหมายจุลภาค           |
| E      | categoryId     | YouTube Category ID (เช่น 20 = Gaming)   |
| F      | privacyStatus  | `private` / `unlisted` / `public`        |
| G      | publishAt      | วันเวลาที่จะเผยแพร่ (ISO 8601)          |
| H      | video_path     | Path เต็มของไฟล์วิดีโอ                  |
| I      | thumbnail_path | Path เต็มของไฟล์ Thumbnail (JPG/PNG)    |
| J      | playlistId     | YouTube Playlist ID (ถ้าต้องการ)         |
| K      | video_id       | (อัปเดตอัตโนมัติ) YouTube Video ID      |

## 🚀 Setup

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Console

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. เปิดใช้งาน APIs:
   - **YouTube Data API v3**
   - **Google Sheets API**
3. สร้าง OAuth 2.0 Client ID (Desktop App)
4. ดาวน์โหลด `client_secrets.json` ไว้ในโปรเจคนี้

### 3. Google Sheets Permission

Shared the spreadsheet (`1RJHqQASgP7U2bej9qnibKYVyBC_zpc6EpW33P1irCsU`) with the email address from your OAuth client, OR share it publicly as "Editor".

## 📖 Usage

```bash
# รันปกติ — อัปโหลดวิดีโอทั้งหมดที่มีสถานะ WAIT_UPLOAD
python upload.py

# Dry run — ดูตัวอย่างโดยไม่อัปโหลดจริง
python upload.py --dry
```

### ขั้นตอนการทำงาน

1. เริ่มโปรแกรม → เปิดเบราว์เซอร์ให้ Sign-in กับ Google
2. อ่าน Google Sheets หาแถวที่ `state = WAIT_UPLOAD`
3. สำหรับแต่ละแถว:
   - ตรวจสอบไฟล์วิดีโอ
   - อัปโหลดขึ้น YouTube (Resumable Upload)
   - ตั้ง Thumbnail
   - เพิ่มลง Playlist (ถ้ามี)
   - อัปเดตสถานะเป็น `UPLOADED`
   - บันทึก `video_id` กลับไปในคอลัมน์ K
4. แสดงสรุปผล

## ⚠️ Notes

- ไฟล์ `token.json` จะถูกสร้างหลัง Sign-in ครั้งแรก — **อย่าลบ** เพราะเก็บ session
- ถ้า `token.json` หมดอายุ โปรแกรมจะขอ Sign-in ใหม่อัตโนมัติ
- รองรับ path ไฟล์ Windows (เช่น `Z:\KT404\video\...`)
- ถ้า `publishAt` ถูกตั้งค่าและ `privacyStatus = private` วิดีโอจะถูกตั้งเวลาเผยแพร่อัตโนมัติ

## 📁 Project Structure

```
├── client_secrets.json   ← OAuth credentials (จาก Google Cloud)
├── token.json            ← Cached token (สร้างอัตโนมัติ)
├── requirements.txt      ← Python dependencies
├── config.py             ← Configuration constants
├── auth.py               ← OAuth2 authentication
├── upload.py             ← Main upload script
└── README.md
```
