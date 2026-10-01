# 🤝 Eyelnw — Phase 2 Project Handoff Document

> **Project Name:** Eyelnw (Eye + ล้นหลาม + Investigation)  
> **Version:** v1.1.0  
> **Target OS:** Windows 11 / Windows 10 (64-bit)  
> **Primary Language:** Python 3.12 (รองรับ Python 3.10+)  
> **Status:** Phase 2 Fine-Tuning & Feature Expansion Complete (Motorcycle Detection Tuning, Centralized Report Index, Persistent Settings, Abort Clip Cutting)  
> **Reference:** [Blueprint Implement Phase 2](file:///d:/Universal/Eyelnw/Application-Context/Phase2/Blueprint_Implement_Phase2.md) | [Phase 1 Handoff](file:///d:/Universal/Eyelnw/Application-Context/Phase1/HANDOFF.md)

---

## 1. System Overview (ภาพรวมระบบและเป้าหมาย Phase 2)

ใน **Phase 2**, โปรเจกต์ **Eyelnw** มุ่งเน้นการปรับจูนความแม่นยำ (Fine-Tuning) และขยายฟีเจอร์อำนวยความสะดวกในการใช้งานจริง (Feature Expansion) โดยยังคงรักษาโครงสร้างหลักที่แข็งแรงของ Phase 1 ไว้ครบถ้วน และไม่ส่งผลกระทบต่อความเข้ากันได้ย้อนหลัง (Backward Compatibility)

### 🎯 4 เสาหลักที่พัฒนาสำเร็จใน Phase 2

```
                           ┌────────────────────────────────────────┐
                           │            Eyelnw v1.1.0               │
                           │   Phase 2: Fine-Tuning & Expansion     │
                           └──────────────────┬─────────────────────┘
                                              │
         ┌───────────────────┬────────────────┴───────────────────┬───────────────────┐
         ▼                   ▼                                    ▼                   ▼
 ┌───────────────┐   ┌───────────────┐                    ┌───────────────┐   ┌───────────────┐
 │   Feature 1   │   │   Feature 2   │                    │   Feature 3   │   │   Feature 4   │
 │   ปรับจูน     │   │   หน้ารวม     │                    │  บันทึกการ    │   │  ปุ่มหยุด     │
 │  มอเตอร์ไซค์  │   │  ประวัติสแกน  │                    │   ตั้งค่า     │   │  ตัดคลิป      │
 │  (Motorcycle) │   │ (Index HTML)  │                    │  (Settings)   │   │ (Abort Clips) │
 └───────────────┘   └───────────────┘                    └───────────────┘   └───────────────┘
  • Min BBox 16px     • output/index.html                  • settings.json     • ไม่รอนาน
  • Conf Boost -0.05  • ค้นหา/กรองข้อมูล                   • โหลดค่าอัตโนมัติ  • เก็บภาพ+คลิปเดิม
  • Skin Masking      • จัดเรียงตามผล/วัน                  • ปุ่มรีเซ็ตค่า     • สร้าง Report ได้
  • ResNet-50 60%     • ปุ่มเปิดใน GUI                     • รองรับข้ามเซสชัน  • ปุ่มเปิดตามสถานะ
  • Crop Upscaling
```

---

## 2. รายละเอียดฟีเจอร์ที่พัฒนาใน Phase 2

### 🛵 Feature 1: ปรับปรุงการตรวจจับมอเตอร์ไซค์ (Motorcycle Detection Fine-Tuning)
จากปัญหาใน Phase 1 ที่มอเตอร์ไซค์มีขนาด Bounding Box เล็ก มีคนขับบดบังตัวรถ และมีพื้นที่สีน้อย ทำให้คะแนนการ Match ด้อยกว่ารถยนต์ Phase 2 จึงได้แก้ไขแบบครบวงจร:
1. **เกณฑ์ขนาดขั้นต่ำตามประเภทรถ (Class-specific Min Size):**
   - ใน `core/detector.py`: ลดเกณฑ์ Bounding Box สำหรับมอเตอร์ไซค์ (`class_id = 3`) ลงเหลือ `16×16 px` (รถยนต์ทั่วไปคงเดิมที่ `24×24 px`) ช่วยให้ตรวจจับมอเตอร์ไซค์ที่แล่นอยู่ระยะไกลได้
2. **ปรับแต่ง Confidence Boost:**
   - เพิ่ม `motorcycle_conf_boost = -0.05` ใน `VehicleDetector.detect()` เพื่อเพิ่มโอกาสดักจับมอเตอร์ไซค์ที่กล้อง CCTV มักให้คะแนนความมั่นใจต่ำกว่ารถเก๋ง
3. **การตัดภาพแบบเน้นตัวรถและกรองสีผิวคนขี่ (Skin-Tone Masking):**
   - ใน `core/color_analyzer.py`: เพิ่มโหมด `is_motorcycle` ให้ Crop แคบลง 40% ตรงกลางโครงรถ และสร้าง Mask กรองช่วงสีผิว (`Hue 0-25`, `Sat 30-200`, `Val 60-255`) ออกจากการคำนวณ HSV Histogram
4. **โครงสร้างน้ำหนักคะแนนตามประเภทรถ (Class-Specific Matching Weights):**
   - ใน `core/matcher.py`: กำหนด `WEIGHT_PROFILES` แยกชัดเจน:
     - **รถยนต์ (Car):** Deep Feature 40%, Color 25%, Keypoints 25%, OCR 10%
     - **มอเตอร์ไซค์ (Motorcycle):** Deep Feature เพิ่มเป็น **60%** (รูปทรงตัวรถสำคัญสุด), Color ลดเหลือ **15%**, Keypoints ลดเหลือ **15%**, OCR 10%
5. **Candidate Crop Upscaling:**
   - ฟังก์ชัน `_preprocess_candidate()` ขยายขนาดภาพ Crop ที่เล็กกว่า `112×112 px` ด้วย Bicubic Interpolation ก่อนส่งเข้า ResNet-50 เพื่อไม่ให้ Feature Vector ผิดเพี้ยน
6. **ส่งต่อ `vehicle_class_id` ตลอด Pipeline:**
   - ปรับใน `core/video_scanner.py` ให้ส่ง `vehicle_class_id` เข้าสู่ฟังก์ชัน `matcher.match()` ทุกการตรวจจับ

---

### 📚 Feature 2: ระบบบันทึก Report HTML + หน้า Index รวมศูนย์ (Centralized Report Index)
แก้ปัญหาที่ผู้ใช้ต้องเปิดหาโฟลเดอร์ผลลัพธ์ย้อนหลังทีละโฟลเดอร์:
1. **โมดูล `ReportIndexGenerator` (`report/index_generator.py`):**
   - สแกนโฟลเดอร์ `output/scan_*` ทั้งหมด ค้นหาไฟล์ `report.html` และดึงสรุปเมตาดาต้าจาก `data/results.json`
   - รวบรวมข้อมูล: ทะเบียนรถ, สี, ยี่ห้อ, จำนวนคลิป, เวลาที่ใช้สแกน, จำนวนครั้งที่พบ, ค่าความเชื่อมั่นสูงสุด
2. **Template หน้า Index สไตล์ Modern Dark Mode (`report/templates/index_template.html`):**
   - ดีไซน์สวยงามตามหลัก UX/UI ของระบบ โทนสีเดียวกับ Report ย่อย
   - มี **ช่องค้นหาแบบ Real-time** (ค้นหาตามป้ายทะเบียน, ยี่ห้อ, สี, หรือวันที่)
   - มี **ตัวเลือกจัดเรียง** (เรียงตามวันที่ล่าสุด, วันที่เก่าสุด, จำนวนครั้งที่พบมากสุด, ค่าความเชื่อมั่นสูงสุด)
   - ปุ่มกด **"📄 เปิดรายงาน"** ลิงก์ตรงสู่ `report.html` ของแต่ละรอบการสแกน
3. **อัปเดตอัตโนมัติ:**
   - ทุกครั้งที่การสแกนเสร็จสิ้น `ReportGenerator.generate_report()` จะเรียกสร้างหรือรีเฟรชหน้า `output/index.html` ทันที
4. **ปุ่มทางลัดบน GUI:**
   - เพิ่มปุ่มสีม่วงเด่นชัด `📚 ดูรายงานทั้งหมด` ในแถบด้านบนของ `gui/result_panel.py` คลิกเดียวเปิดหน้า `output/index.html` บนเบราว์เซอร์ทันที

---

### ⚙️ Feature 3: บันทึกค่าตั้งค่าข้ามเซสชัน (Persistent Settings)
แก้ปัญหาที่ต้องตั้งค่าโมเดลและ Threshold ใหม่ทุกครั้งที่เปิดโปรแกรม:
1. **ตัวจัดการการตั้งค่า `SettingsManager` (`utils/settings.py`):**
   - จัดเก็บค่าในไฟล์ `settings.json` ที่ Root Directory
   - ค่าที่บันทึก: `model_choice`, `match_threshold`, `scan_speed`, `enable_clip_cutting`, `target_color`
   - มีระบบ Fallback คืนค่า `DEFAULT_SETTINGS` อัตโนมัติหากไฟล์ยังไม่ถูกสร้างหรือเกิดความเสียหาย
2. **การผูกค่าเข้ากับ GUI (`gui/scan_panel.py` & `gui/app.py`):**
   - เมื่อเปิดแอปพลิเคชัน วิดเจ็ตทั้งหมดจะกู้คืนค่าล่าสุดที่ผู้ใช้เคยตั้งไว้โดยอัตโนมัติ
   - เมื่อกดเริ่มการสแกน ระบบจะบันทึกสถานะปัจจุบันลง `settings.json`
3. **ปุ่มคืนค่าเริ่มต้น (`🔄 รีเซ็ตค่าเริ่มต้น`):**
   - เพิ่มปุ่มในแถบตั้งค่าของ ScanPanel สำหรับรีเซ็ตทุกค่ากลับเป็นค่ามาตรฐานจากโรงงาน
4. **ความปลอดภัยของ Git:**
   - เพิ่ม `settings.json` ใน `.gitignore` เพื่อไม่ให้การตั้งค่าส่วนตัวติดไปกับ Git Commit

---

### ⏭️ Feature 4: ปุ่มหยุดตัดคลิปกลางคัน (Abort Clip Cutting)
แก้ปัญหาการรอนานในขั้นตอนการตัดคลิปวิดีโอหลักฐานจำนวนมาก:
1. **กลไก Abort Flag ใน `ReportGenerator` (`report/generator.py`):**
   - เพิ่ม Flag `self._abort_clips` พร้อมเมธอด `abort_clip_cutting()`
   - วนลูปตัดคลิปทีละรายการ หาก Flag ถูกยกขึ้น จะข้ามการตัดคลิปที่เหลือทั้งหมด
2. **ไม่สูญเสียข้อมูลหลักฐาน (Safe Data Preservation):**
   - **คลิปที่ตัดเสร็จแล้วก่อนกดหยุด:** บันทึกและแนบลงในรายงานตามปกติ
   - **คลิปที่ยังตัดไม่ถึง:** ข้ามการตัดวิดีโอ แต่ยังคงบันทึกภาพนิ่งความละเอียดสูง (Screenshots) และตารางสถิติลงรายงาน HTML ได้สมบูรณ์
   - หน้ารายงาน HTML จะแสดงปุ่ม "🎬 ดูคลิปสั้น" เฉพาะเหตุการณ์ที่มีไฟล์คลิปจริง ส่วนเหตุการณ์อื่นจะแสดงเฉพาะปุ่ม "📸 ดูภาพขนาดเต็ม"
3. **ปุ่มควบคุมบน ScanPanel (`gui/scan_panel.py`):**
   - เพิ่มปุ่มสีส้มทอง `⏭ หยุดตัดคลิป`
   - ปุ่มจะถูกปิดการใช้งาน (Disabled) ในขั้นตอนการสแกนวิดีโอปกติ และจะเปิดใช้งาน (Enabled) อัตโนมัติทันทีที่เข้าสู่กระบวนการตัดคลิปวิดีโอ
4. **Callback แจ้งความคืบหน้า:**
   - ส่ง `clip_progress_callback(current, total, group_id)` อัปเดต Progress Bar และข้อความสถานะ `✂️ กำลังตัดคลิป #X (Y/Z)` แบบเรียลไทม์

---

## 3. สรุปไฟล์ที่สร้างใหม่และแก้ไขใน Phase 2

### 📁 ไฟล์ที่สร้างใหม่ (New Files)
| ไฟล์ | หมวดหมู่ | คำอธิบาย |
|---|---|---|
| [`utils/settings.py`](file:///d:/Universal/Eyelnw/utils/settings.py) | Utils | ตัวจัดการ Persistent Settings บันทึกและอ่านไฟล์ `settings.json` |
| [`report/index_generator.py`](file:///d:/Universal/Eyelnw/report/index_generator.py) | Report | ตัวสร้างหน้ารวมรายงานผล `output/index.html` พร้อมอ่าน `results.json` |
| [`report/templates/index_template.html`](file:///d:/Universal/Eyelnw/report/templates/index_template.html) | Template | หน้าเว็บ Jinja2 หน้ารวมรายงาน ค้นหา และจัดเรียงผลลัพธ์ |
| [`tests/test_phase2.py`](file:///d:/Universal/Eyelnw/tests/test_phase2.py) | Tests | ชุดทดสอบ Unit & Integration Test สำหรับ 4 ฟีเจอร์ของ Phase 2 (11 Test cases) |
| [`Application-Context/Phase2/HANDOFF.md`](file:///d:/Universal/Eyelnw/Application-Context/Phase2/HANDOFF.md) | Docs | เอกสารสรุปการส่งมอบงาน Phase 2 ฉบับนี้ |

### ✏️ ไฟล์ที่แก้ไข (Modified Files)
| ไฟล์ | ฟีเจอร์ | รายละเอียดการแก้ไข |
|---|---|---|
| [`core/detector.py`](file:///d:/Universal/Eyelnw/core/detector.py) | #1 | เพิ่ม `MIN_SIZE` (16x16 px สำหรับมอเตอร์ไซค์) และ `motorcycle_conf_boost` |
| [`core/color_analyzer.py`](file:///d:/Universal/Eyelnw/core/color_analyzer.py) | #1 | เพิ่มพารามิเตอร์ `is_motorcycle`, Center Crop แคบลง 40%, กรอง Skin-Tone |
| [`core/matcher.py`](file:///d:/Universal/Eyelnw/core/matcher.py) | #1 | เพิ่ม `WEIGHT_PROFILES`, ฟังก์ชัน `_preprocess_candidate()` Upscale ภาพเล็ก |
| [`core/video_scanner.py`](file:///d:/Universal/Eyelnw/core/video_scanner.py) | #1 | ส่ง `vehicle_class_id=v["class_id"]` ไปยัง `matcher.match()` |
| [`report/generator.py`](file:///d:/Universal/Eyelnw/report/generator.py) | #2, #4 | เพิ่ม `abort_clip_cutting()`, `clip_progress_callback` และสร้าง `index.html` |
| [`gui/scan_panel.py`](file:///d:/Universal/Eyelnw/gui/scan_panel.py) | #3, #4 | เชื่อม Settings, เพิ่มปุ่ม `🔄 รีเซ็ตค่าเริ่มต้น`, ปุ่ม `⏭ หยุดตัดคลิป` |
| [`gui/result_panel.py`](file:///d:/Universal/Eyelnw/gui/result_panel.py) | #2 | เพิ่มปุ่ม `📚 ดูรายงานทั้งหมด` เปิดหน้า `output/index.html` |
| [`gui/app.py`](file:///d:/Universal/Eyelnw/gui/app.py) | #2, #3, #4 | จัดการอินสแตนซ์ `SettingsManager`, ผูก Callback Progress และ Abort |
| [`utils/helpers.py`](file:///d:/Universal/Eyelnw/utils/helpers.py) | Robustness | ทำ Safe import `cv2` เพื่อให้ฟังก์ชันแปลงเวลาใช้งานได้อิสระ |
| [`.gitignore`](file:///d:/Universal/Eyelnw/.gitignore) | Maintenance | เพิ่ม `settings.json` ไม่ให้บันทึกลง Git Repository |

---

## 4. โครงสร้างโฟลเดอร์ล่าสุด (Project Tree)

```
Eyelnw/
├── .gitignore
├── Application-Context/
│   ├── Phase1/
│   │   ├── Blueprint.md
│   │   └── HANDOFF.md
│   └── Phase2/
│       ├── Blueprint_Implement_Phase2.md  # พิมพ์เขียวรายละเอียด Phase 2
│       └── HANDOFF.md                     # เอกสารส่งมอบ Phase 2 นี้
├── assets/
│   └── icon.ico
├── core/
│   ├── color_analyzer.py                  # [Phase 2] รองรับมอเตอร์ไซค์ & Skin Masking
│   ├── detector.py                        # [Phase 2] ปรับ Min BBox 16px & Conf Boost
│   ├── feature_extractor.py
│   ├── matcher.py                         # [Phase 2] WEIGHT_PROFILES & Upscale Preprocess
│   ├── motion_tracker.py
│   ├── ocr_reader.py
│   ├── target_loader.py
│   └── video_scanner.py                   # [Phase 2] ส่ง vehicle_class_id
├── gui/
│   ├── app.py                             # [Phase 2] ควบคุม Settings & Abort Pipeline
│   ├── result_panel.py                    # [Phase 2] เพิ่มปุ่มเปิดหน้า Index
│   ├── scan_panel.py                      # [Phase 2] เพิ่มปุ่มรีเซ็ต และปุ่มหยุดตัดคลิป
│   ├── target_panel.py
│   ├── video_panel.py
│   └── widgets.py
├── models/
│   └── .gitkeep
├── output/
│   ├── .gitkeep
│   ├── index.html                         # [Phase 2] ★ หน้ารวมประวัติรายงานสแกนทั้งหมด
│   └── scan_YYYYMMDD_HHMMSS/              # โฟลเดอร์ผลการสแกนแต่ละครั้ง
│       ├── clips/                         # คลิปวิดีโอสั้น
│       ├── data/
│       │   └── results.json
│       ├── report.html                    # หน้ารายงานของรอบนั้นๆ
│       ├── screenshots/
│       └── target/
├── report/
│   ├── clip_cutter.py
│   ├── generator.py                       # [Phase 2] รองรับ Abort Clips & Auto-Index
│   ├── index_generator.py                 # [Phase 2] ★ สแกนผลลัพธ์และสร้าง index.html
│   └── templates/
│       ├── index_template.html            # [Phase 2] ★ เทมเพลตหน้ารวมประวัติสแกน
│       └── report_template.html
├── tests/
│   ├── test_phase2.py                     # [Phase 2] ★ ชุดทดสอบฟีเจอร์ Phase 2 (11 tests)
│   └── test_pipeline.py                   # ชุดทดสอบ Pipeline ของ Phase 1
├── utils/
│   ├── config.py
│   ├── helpers.py                         # [Phase 2] ปรับปรุง Safe import
│   ├── logger.py
│   └── settings.py                        # [Phase 2] ★ ตัวจัดการ Persistent Settings
├── main.py
├── requirements.txt
└── README.md
```

---

## 5. วิธีการทดสอบและรันระบบ (Testing & Execution)

### 🧪 รันชุดทดสอบ Phase 2
ทดสอบความถูกต้องของตรรกะ Persistent Settings, หน้ารวม Index HTML, Abort Clip Cutting, เกณฑ์ Bounding Box มอเตอร์ไซค์, และการ Upscale:
```powershell
python tests/test_phase2.py
```
**ผลลัพธ์ที่คาดหวัง:**
```text
Ran 11 tests in 0.085s
OK
```

### 🚀 รันโปรแกรม Eyelnw GUI
```powershell
python main.py
```
**ขั้นตอนทดสอบฟีเจอร์ใหม่ใน GUI:**
1. **ทดสอบ Persistent Settings:**
   - ปรับเกณฑ์ Threshold เป็น `70%`, ปรับความเร็วเป็น `ละเอียด`
   - ปิดโปรแกรมแล้วเปิดใหม่ → ตรวจสอบว่าค่ายังคงเป็น `70%` และ `ละเอียด`
   - กดปุ่ม `🔄 รีเซ็ตค่าเริ่มต้น` → ตรวจสอบว่าค่าวิดเจ็ตกลับเป็น `60%` และ `สมดุล`
2. **ทดสอบปุ่มหยุดตัดคลิป (Abort Clip Cutting):**
   - แนบรูปรถและวิดีโอ เริ่มการสแกนโดยเปิดสวิตช์ตัดคลิป
   - เมื่อเข้าสู่ขั้นตอนการตัดคลิป ปุ่ม `⏭ หยุดตัดคลิป` จะเปิดใช้งาน
   - กดปุ่ม `⏭ หยุดตัดคลิป` → ระบบจะข้ามคลิปที่เหลือทันที และเปิดหน้าผลลัพธ์พร้อมสร้างรายงาน HTML ได้อย่างปลอดภัย
3. **ทดสอบหน้ารวมรายงาน (Report Index):**
   - ในหน้าผลลัพธ์ กดปุ่ม `📚 ดูรายงานทั้งหมด` บนมุมขวาบน
   - เบราว์เซอร์จะเปิดหน้า `output/index.html` สามารถค้นหาป้ายทะเบียนและเรียงลำดับรายงานย้อนหลังได้ทันที

---

## 6. ข้อเสนอแนะสำหรับการพัฒนาใน Phase ถัดไป (Phase 3 Recommendations)

1. **AI Vehicle Re-Identification (Re-ID Model):**
   - พัฒนาโมเดล Re-ID เฉพาะทาง (เช่น OSNet หรือ FastReID) เสริมการทำงานของ ResNet-50 เพื่อให้จำแนกรถรุ่นเดียวกัน สีเดียวกัน แต่คนละคันได้อย่างแม่นยำยิ่งขึ้น
2. **ปรับปรุง Thai License Plate Recognition (Thai LPR):**
   - เทรนโมเดลตรวจจับป้ายทะเบียนเฉพาะจุด (Two-Stage YOLOv8-Plate Detection) ก่อนส่งเข้า OCR เพื่อให้อ่านป้ายทะเบียนมอเตอร์ไซค์ที่มักมีขนาดเล็กหรือติดใต้บังโคลนได้ดียิ่งขึ้น
3. **Export Report เป็น PDF ในคลิกเดียว:**
   - เพิ่มปุ่มพิมพ์รายงานหรือดาวน์โหลดเป็นไฟล์ PDF จากหน้า `report.html` หรือหน้า `index.html` เพื่อส่งเป็นเอกสารเบาะแสให้สถานีตำรวจได้สะดวกรวดเร็วยิ่งขึ้น
4. **Multi-Camera Timeline Synchronization:**
   - ในกรณีที่สแกนฟุตเทจจากกล้องวงจรปิดหลายจุดพร้อมกัน สามารถวาดแผนผังไทม์ไลน์เปรียบเทียบเวลา (Timeline Map) เพื่อติดตามเส้นทางหลบหนีของยานพาหนะตามลำดับกล้อง
