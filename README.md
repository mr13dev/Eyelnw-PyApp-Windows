# 🔍 Eyelnw (Eye + ล้นหลาม + Investigation)

> **ระบบ AI ตรวจจับและค้นหารถที่ถูกขโมยจากคลิป CCTV อัตโนมัติสำหรับ Windows 11**

[![License: MIT](https://badgen.net/badge/License/MIT/yellow)](LICENSE)
[![Python 3.12](https://badgen.net/badge/Python/3.12+/blue?icon=python)](https://www.python.org/downloads/)
[![YOLOv8](https://badgen.net/badge/YOLO/v8/orange)](https://docs.ultralytics.com/)
[![PyTorch CUDA](https://badgen.net/badge/PyTorch/CUDA%20RTX%205060%20Ti/green)](https://pytorch.org/)
[![CustomTkinter](https://badgen.net/badge/GUI/CustomTkinter/purple)](https://github.com/TomSchimansky/CustomTkinter)

---

## 📋 คุณสมบัติเด่น (Features)

1. **รองรับรูปรถอ้างอิงหลายมุมมอง (Multi-Angle Reference)**
   - แนบภาพรถเป้าหมายได้หลายมุม (หน้ารถ, ข้างรถ, ท้ายรถ, มุมสูงเฉียงแบบ CCTV)
   - สร้าง Target Profile แบบผสมผสาน (Consolidated Feature Profile)

2. **ระบบวิเคราะห์และจับคู่หลายมิติ (Multi-Modal Matching Engine)**
   - 🧠 **Deep Feature Embedding (ResNet50)**: เทียบโครงสร้างและลักษณะจำเพาะของตัวรถด้วย Cosine Similarity (น้ำหนัก 40%)
   - 🎨 **Color Profile Analysis (HSV Histogram)**: วิเคราะห์โทนสีรถจริง ตัดปัจจัยเงาและแสงจ้า (น้ำหนัก 25%)
   - 🔍 **ORB Keypoints & Descriptors**: ตรวจจับจุดเอกลักษณ์ ลวดลาย และชุดแต่ง (น้ำหนัก 25%)
   - 📝 **License Plate OCR**: ตรวจจับและอ่านป้ายทะเบียนรถ (น้ำหนัก 10% / โบนัสความมั่นใจสูง)

3. **สแกนวิดีโออัจฉริยะ (Smart Frame Skipping)**
   - ข้ามเฟรมอัตโนมัติตามค่า FPS เพื่อสแกนวิดีโอความยาวหลายชั่วโมงได้อย่างรวดเร็ว
   - รองรับไฟล์ MP4, AVI, MKV, MOV, FLV, WMV
   - รองรับ Batch Processing สแกนพร้อมกันหลายกล้อง

4. **ตรวจจับทิศทางการเคลื่อนที่ (Motion Tracker)**
   - วิเคราะห์ทิศทาง: ซ้ายไปขวา, ขวาไปซ้าย, มุ่งหน้าเข้ามา, เคลื่อนที่ออกไป, จอดนิ่ง

5. **รายงานเบาะแสอัตโนมัติ (Automated Intelligence Report)**
   - 📄 **HTML Report**: รายงานหน้าเดียวพร้อมภาพ สถิติ ไทม์ไลน์ และกราฟแท่งคะแนนความเชื่อมั่น
   - 🎬 **Short Clips**: ตัดคลิปสั้นช่วงที่พบรถเป้าหมายอัตโนมัติ
   - 📸 **Annotated Screenshots**: บันทึกภาพเฟรมที่ดีที่สุดพร้อมกรอบสี่เหลี่ยมล้อมรอบรถ
   - 📊 **JSON Data**: บันทึกข้อมูลเชิงลึกสำหรับนำไปประมวลผลต่อ

---

## 🏗️ สถาปัตยกรรมระบบ (Project Architecture)

```
Eyelnw/
├── Blueprint.md              # แผนพัฒนาระบบ
├── requirements.txt          # รายการ Library
├── README.md                 # คู่มือการใช้งานนี้
├── main.py                   # จุดเริ่มต้นโปรแกรม (GUI / CLI)
│
├── gui/                      # ส่วนติดต่อผู้ใช้ CustomTkinter
│   ├── __init__.py
│   ├── app.py                # หน้าต่างหลักของโปรแกรม
│   ├── target_panel.py       # แผงแนบรูปรถเป้าหมายและกรอกข้อมูล
│   ├── video_panel.py        # แผงเลือกไฟล์วิดีโอ CCTV
│   ├── scan_panel.py         # แผงตั้งค่าและแถบแสดงความคืบหน้า
│   ├── result_panel.py       # แผงแสดงผลลัพธ์และปุ่มเปิดรายงาน
│   └── widgets.py            # การ์ดและ UI Components ย่อย
│
├── core/                     # กลไกประมวลผลและปัญญาประดิษฐ์
│   ├── __init__.py
│   ├── target_loader.py      # โหลดรูปอ้างอิงและสร้าง TargetProfile
│   ├── detector.py           # ตรวจจับรถในเฟรมด้วย YOLOv8
│   ├── matcher.py            # จับคู่และคำนวณคะแนนความเชื่อมั่น
│   ├── color_analyzer.py     # วิเคราะห์สีรถด้วย HSV Histogram
│   ├── feature_extractor.py  # ดึง Deep Embedding ด้วย ResNet50
│   ├── motion_tracker.py     # คำนวณทิศทางการเคลื่อนที่ของรถ
│   ├── ocr_reader.py         # อ่านป้ายทะเบียนรถด้วย OCR
│   └── video_scanner.py      # วนสแกนวิดีโอและรวมกลุ่มเหตุการณ์ (Clustering)
│
├── report/                   # ส่วนสร้างรายงานและตัดคลิป
│   ├── __init__.py
│   ├── clip_cutter.py        # ตัดคลิปสั้นและบันทึกภาพถ่าย
│   ├── generator.py          # สร้างรายงาน HTML และไฟล์ JSON
│   └── templates/
│       └── report_template.html
│
├── models/                   # เก็บโมเดล YOLOv8 (.pt)
├── output/                   # บันทึกผลลัพธ์การสแกน (scan_YYYYMMDD_HHMMSS/)
└── utils/                    # ฟังก์ชันช่วยเหลือและตั้งค่า
    ├── __init__.py
    ├── config.py             # การตั้งค่าระบบและการตรวจจับ GPU
    ├── logger.py             # บันทึกเหตุการณ์
    └── helpers.py            # การแปลงเวลาและวาดกรอบ
```

---

## 🚀 วิธีติดตั้งและเริ่มต้นใช้งาน (Quick Start)

### 1. ความต้องการของระบบ
- **OS:** Windows 10 / Windows 11
- **Python:** 3.10 ขึ้นไป (แนะนำ 3.12)
- **GPU:** NVIDIA GeForce (รองรับ RTX 50-Series Blackwell และ RTX 30/40 พร้อม CUDA 13.0+) หรือรันผ่าน CPU

### 2. วิธีรันโปรแกรมผ่าน GUI
```powershell
# 1. เข้าสู่โฟลเดอร์โปรเจกต์
cd d:\Universal\Eyelnw

# 2. เรียกใช้งาน Virtual Environment
.\venv\Scripts\activate

# 3. รันโปรแกรมหลัก
python main.py
```

### 3. วิธีใช้งานผ่าน Command Line (CLI Mode)
สำหรับการประมวลผลแบบอัตโนมัติหรือไม่มีหน้าจอ:
```powershell
# สแกนพร้อมตัดคลิปสั้น
python main.py --cli --target "C:\path\to\target_car.jpg" --videos "C:\cctv\cam1.mp4" "C:\cctv\cam2.mp4" --threshold 0.60

# สแกนแบบไม่ตัดคลิปสั้น (บันทึกเฉพาะภาพหน้าจอและรายงาน HTML เพื่อความเร็วสูงสุด)
python main.py --cli --target "C:\path\to\target_car.jpg" --videos "C:\cctv\cam1.mp4" --no-clips
```

---

## 💡 คำแนะนำเพื่อความแม่นยำสูงสุด
1. แนบรูปรถเป้าหมาย 3-10 รูปจากหลายมุมมอง (หน้ารถ, ข้างรถ, ท้ายรถ, และมุมสูง)
2. หากทราบป้ายทะเบียนหรือยี่ห้อ ให้ระบุในช่องข้อมูลเพิ่มเติม
3. เริ่มต้นค้นหาด้วยค่า Threshold แนะนำที่ **60%** แล้วปรับเพิ่มขึ้นหากมีผลลัพธ์ซ้ำซ้อน
