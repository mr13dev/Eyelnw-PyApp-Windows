# 🤝 Eyelnw — Phase 1 Project Handoff Document

> **Project Name:** Eyelnw (Eye + ล้นหลาม + Investigation)  
> **Target OS:** Windows 11 / Windows 10  
> **Primary Language:** Python 3.12 (รองรับ Python 3.10+)  
> **Status:** Phase 1 Foundation & Pipeline Complete (Core Engine, GUI, Reporting, Multi-modal Matching)

---

## 1. System Overview (ภาพรวมระบบ)

**Eyelnw** คือระบบ AI ตรวจจับ ค้นหา และวิเคราะห์ยานพาหนะเป้าหมาย (เช่น รถที่ถูกโจรกรรม หรือรถต้องสงสัย) จากคลิปวิดีโอจากกล้องวงจรปิด (CCTV) โดยอัตโนมัติ เพื่อช่วยลดภาระงานของเจ้าหน้าที่และผู้เสียหายที่ต้องนั่งเปิดดูวิดีโอย้อนหลังหลายสิบชั่วโมง

### 🎯 หัวใจและกระบวนการทำงานหลัก (Core Workflow)

```
[Target Vehicle Photos] + [Metadata (Plate/Color/Brand)]
                   │
                   ▼
       [1. Target Feature Profile]
 (ResNet-50 Embeddings + HSV Color Histogram + Keypoints)
                   │
                   ▼
       [2. CCTV Video Ingestion]
        (MP4, AVI, MKV, MOV, FLV)
                   │
                   ▼
     [3. Smart Frame Skipping Engine] ───► ข้ามเฟรมอัจฉริยะตาม FPS เพื่อความรวดเร็ว
                   │
                   ▼
     [4. YOLOv8 Vehicle Detection] ───► ค้นหา Car, Bus, Truck, Motorcycle
                   │
                   ▼
 [5. Multi-Modal Matching Engine] ───► คำนวณคะแนนถ่วงน้ำหนักรวม:
      ├─ Deep Feature Similarity (ResNet-50 Cosine Sim) : 40%
      ├─ Color Profile Similarity (HSV Histogram)       : 25%
      ├─ Local Keypoint Descriptors (ORB Feature Match) : 25%
      └─ License Plate Recognition (EasyOCR Thai/Eng)   : 10% (+Bonus)
                   │
                   ▼
  [6. Motion Tracking & Clustering] ───► ตรวจจับทิศทาง (L->R, R->L, เข้า/ออก) + รวมช่วงเวลา
                   │
                   ▼
        [7. Output Generation]
      ├─ Interactive Modern HTML Report (พร้อมสถิติ ไทม์ไลน์ และคะแนน)
      ├─ High-Resolution Annotated Screenshots (กรอบ Bounding Box)
      ├─ Short Video Evidence Clips (ตัดเฉพาะช่วงที่พบพร้อม Padding หน้า-หลัง)
      └─ Structured JSON Data (`results.json`)
```

---

## 2. Tech Stack & Dependencies

### 🛠️ เทคโนโลยีหลัก

| ประเภท | เครื่องมือ / เทคโนโลยี | คำอธิบายและบทบาทหน้าที่ |
|---|---|---|
| **Language** | Python 3.12 | ภาษาหลักของทั้งระบบ |
| **Object Detection** | Ultralytics YOLOv8 (`yolov8n`, `yolov8s`, `yolov8m`) | ตรวจจับและระบุตำแหน่งของยานพาหนะทุกคันในเฟรม |
| **Deep Learning** | PyTorch & Torchvision (`ResNet-50`) | ดึง Deep Feature Embeddings สำหรับเปรียบเทียบรูปทรงและอัตลักษณ์รถ |
| **Computer Vision** | OpenCV (`cv2`) | ถอดรหัสวิดีโอ, คำนวณ HSV Color Histogram, สกัด ORB Keypoints, วาด Annotation |
| **OCR Engine** | EasyOCR | ตรวจจับและอ่านตัวอักษรป้ายทะเบียนรถภาษาไทยและอังกฤษ |
| **GUI Framework** | CustomTkinter + Pillow | Desktop GUI สไตล์ Dark Mode ที่ทันสมัย รองรับ Multi-threading และ Drag & Drop |
| **Media Processing** | MoviePy (`moviepy`) | ตัดคลิปวิดีโอหลักฐานสั้นๆ เฉพาะช่วงเวลาที่ตรวจพบ |
| **Report Engine** | Jinja2 Template Engine | เรนเดอร์หน้ารายงาน HTML Report สวยงามพร้อมเปิดในเว็บเบราว์เซอร์ |
| **Similarity Metrics** | Scikit-learn & NumPy | คำนวณ Cosine Similarity และการจัดการ Vector Arrays |

### 📦 รายการใน `requirements.txt`
```text
ultralytics>=8.0.0
opencv-python>=4.8.0
torch>=2.2.0
torchvision>=0.17.0
scikit-learn>=1.3.0
numpy>=1.24.0
customtkinter>=5.2.0
Pillow>=10.0.0
Jinja2>=3.1.0
moviepy>=1.0.3
tqdm>=4.66.0
easyocr>=1.7.0
```

---

## 3. Environment Setup (วิธีตั้งค่ารัน Local)

### 💻 ความต้องการของระบบ (System Requirements)
- **ระบบปฏิบัติการ:** Windows 10 / Windows 11 (64-bit)
- **Python:** Version 3.10 ขึ้นไป (แนะนำ Python 3.12)
- **GPU (ทางเลือก):** NVIDIA GeForce รองรับ CUDA (มีระบบตรวจจับอัตโนมัติ หากไม่มีการ์ดจอจะ Fallback ไปใช้ CPU โดยอัตโนมัติ)
- **พื้นที่ว่าง:** ขั้นต่ำ 5 GB (สำหรับ Virtual Environment, Weights ของโมเดล และ Cache)

### ⚙️ ขั้นตอนการติดตั้ง (Installation Steps)

1. **เปิด PowerShell หรือ Terminal เข้าสู่โฟลเดอร์โปรเจกต์:**
   ```powershell
   cd d:\Universal\Eyelnw
   ```

2. **สร้างและเปิดใช้งาน Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **ติดตั้ง PyTorch (ตามฮาร์ดแวร์ของคุณ):**
   - *กรณีใช้ GPU (NVIDIA CUDA):*
     ```powershell
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
     ```
   - *กรณีใช้ CPU ล้วน:*
     ```powershell
     pip install torch torchvision
     ```

4. **ติดตั้ง Dependencies ทั้งหมด:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **ตรวจสอบไฟล์โมเดลใน `models/`:**
   ระบบมีโมเดล YOLOv8 (`yolov8n.pt`, `yolov8s.pt`, `yolov8m.pt`) เตรียมพร้อมไว้ในโฟลเดอร์ `models/` แล้ว หากไม่มี ระบบจะดาวน์โหลดให้อัตโนมัติในครั้งแรกที่รัน

### 🚀 วิธีการรันโปรแกรม

#### แบบที่ 1: รันผ่านหน้าต่าง Graphic UI (แนะนำสำหรับการใช้งานทั่วไป)
```powershell
python main.py
```
*การใช้งาน:*
1. แท็บ **"รถเป้าหมาย"**: เลือกหรือลากวางรูปรถเป้าหมาย (แนะนำ 3-10 รูป หลากมุม) พร้อมระบุข้อมูลเพิ่มเติม (ทะเบียน, ยี่ห้อ, สี)
2. แท็บ **"วิดีโอ CCTV"**: เพิ่มไฟล์คลิปวิดีโอที่ต้องการค้นหา (รองรับหลายไฟล์)
3. ปรับค่า Threshold และ Model Size ตามต้องการ แล้วกด **"🔍 เริ่มค้นหา"**
4. เมื่อเสร็จสิ้น สามารถคลิกเปิดดูรายงาน HTML และคลิปหลักฐานได้ทันที

#### แบบที่ 2: รันผ่าน Command Line (CLI Headless Mode สำหรับ Server / Automation)
```powershell
# รันแบบเต็มรูปแบบ (ตรวจจับ + บันทึกภาพ + ตัดคลิปสั้น + รายงาน HTML)
python main.py --cli --target "C:\path\to\target_car.jpg" --videos "C:\cctv\cam1.mp4" --threshold 0.60

# รันแบบความเร็วสูงสุดโดยไม่ตัดคลิปสั้น (บันทึกเฉพาะภาพแคปและรายงาน HTML)
python main.py --cli --target "C:\path\to\target_car.jpg" --videos "C:\cctv\cam1.mp4" --no-clips
```

#### แบบที่ 3: รัน End-to-End Pipeline Integration Test
ตรวจสอบความพร้อมของระบบทั้งหมด (สร้างภาพและคลิปจำลอง ทดสอบ TargetLoader, Detector, Matcher, Scanner, Report):
```powershell
python tests/test_pipeline.py
```

---

## 4. Folder Structure (โครงสร้างโฟลเดอร์)

```
Eyelnw/
├── Application-Context/
│   └── Phase1/
│       ├── Blueprint.md         # แผนผังและสถาปัตยกรรมระบบฉบับละเอียด (Phase 1-4)
│       └── HANDOFF.md           # เอกสารส่งมอบงานฉบับสรุปนี้
├── assets/                      # ไอคอนและกราฟิกที่ใช้ในแอปพลิเคชัน
├── core/                        # กลไกประมวลผลและ AI Pipeline หลัก
│   ├── color_analyzer.py        # วิเคราะห์และเปรียบเทียบโทนสีด้วย HSV Color Histogram
│   ├── detector.py              # โมดูลตรวจจับประเภทยานพาหนะด้วย YOLOv8
│   ├── feature_extractor.py     # ดึง Deep Embedding Vector ด้วย ResNet-50
│   ├── matcher.py               # คำนวณคะแนน Multi-Modal Confidence Score รวมทุกมิติ
│   ├── motion_tracker.py        # วิเคราะห์เวกเตอร์ทิศทางการเคลื่อนที่ของรถ
│   ├── ocr_reader.py            # สกัดตัวอักษรและตรวจจับป้ายทะเบียนด้วย EasyOCR
│   ├── target_loader.py         # ประมวลผลภาพอ้างอิงและสร้าง Consolidated TargetProfile
│   └── video_scanner.py         # วนลูปอ่านวิดีโอ, ทำ Smart Frame Skip และรวมกลุ่มเหตุการณ์
├── gui/                         # ส่วนติดต่อผู้ใช้ CustomTkinter
│   ├── app.py                   # หน้าต่างหลักและควบคุม State การทำงาน
│   ├── target_panel.py          # ส่วนอัปโหลดรูปรถเป้าหมายและกรอกเมตาดาต้า
│   ├── video_panel.py           # ส่วนเลือกและจัดการรายการไฟล์วิดีโอ CCTV
│   ├── scan_panel.py            # ส่วนปรับพารามิเตอร์การสแกนและ Progress Bar
│   ├── result_panel.py          # ส่วนแสดงสรุปผลลัพธ์และปุ่มเปิดดูรายงาน
│   └── widgets.py               # UI Reusable Components (การ์ดแสดงผล, Badges)
├── models/                      # ที่เก็บ Weights ของโมเดลตรวจจับ (`yolov8n/s/m.pt`)
├── output/                      # จัดเก็บผลลัพธ์การสแกนแต่ละครั้ง (`scan_YYYYMMDD_HHMMSS/`)
│   ├── clips/                   # วิดีโอคลิปสั้นช่วงที่ตรวจพบ
│   ├── data/results.json        # ข้อมูลดิบเชิงสถิติและผลลัพธ์ในรูปแบบ JSON
│   ├── report.html              # รายงานสรุปหลักฐานแบบ HTML พร้อมเปิดในเบราว์เซอร์
│   └── screenshots/             # ภาพถ่ายหน้าจอความละเอียดสูงพร้อมกรอบไฮไลต์รถ
├── report/                      # ระบบประมวลผลรายงานและตัดต่อมีเดีย
│   ├── clip_cutter.py           # ฟังก์ชันตัดคลิปวิดีโอและเซฟภาพ Snapshot
│   ├── generator.py             # รวบรวมข้อมูลและเรนเดอร์ HTML/JSON Report
│   └── templates/
│       └── report_template.html # เทมเพลต Jinja2 สำหรับสร้างรายงานผลลัพธ์
├── tests/
│   └── test_pipeline.py         # สคริปต์ Integration Test ตรวจสอบกระบวนการทั้งหมด
├── utils/                       # โมดูลช่วยเหลือและตั้งค่าระบบ
│   ├── config.py                # Data Class กำหนดค่าคงที่, น้ำหนักคะแนน และเช็คสเปก GPU
│   ├── helpers.py               # ฟังก์ชันแปลงหน่วยเวลา, จัดการไฟล์ และวาด Annotation
│   └── logger.py                # ระบบบันทึก Log แสดงทั้งบน Console และไฟล์
├── main.py                      # จุดเริ่มต้นโปรแกรม (รองรับทั้งคำสั่ง GUI และ CLI)
├── requirements.txt             # รายการ Python Packages ที่จำเป็น
└── README.md                    # เอกสารแนะนำและคู่มือการใช้งานเบื้องต้น
```

---

## 5. Known Issues / สิ่งที่ต้องทำต่อ (Next Steps)

### ⚠️ ข้อจำกัดและประเด็นที่พบในปัจจุบัน (Known Issues)

1. **คุณภาพของฟุตเทจ CCTV และสภาพแวดล้อม (Environmental Factors):**
   - ในสภาพแสงน้อย (กลางคืน), มีเงาบังจัด, หรือสภาพอากาศฝนตก/หมอก ค่าความแม่นยำของ Color Histogram และ Feature Embedding อาจลดลง แนะนำให้ตั้ง Threshold เริ่มต้นที่ 0.50 - 0.55 สำหรับคลิปกลางคืน
   - หากรถมีขนาดเล็กมากในเฟรม (น้อยกว่า 50x50 พิกเซล) EasyOCR และ ResNet-50 อาจไม่สามารถดึงคุณลักษณะที่แม่นยำเพียงพอ
2. **ความเร็วในการตัดคลิปวิดีโอ (Clip Cutting Overhead):**
   - MoviePy ทำการ re-encode คลิปผ่าน CPU ซึ่งอาจใช้เวลานานหากพบเหตุการณ์จำนวนมาก หากต้องการสแกนความเร็วสูงสุดแนะนำให้เลือกปิดการตัดคลิปสั้น (`--no-clips` หรือติ๊กออกใน GUI) แล้วค่อยตรวจสอบจาก Screenshots
3. **การจับคู่รถรุ่นเดียวกันที่มีลักษณะคล้ายกัน (Intra-class Disambiguation):**
   - รถยนต์ที่เป็นรุ่นเดียวกัน ปีเดียวกัน และสีเดียวกัน (เช่น รถแท็กซี่ หรือรถสีขาวรุ่นยอดนิยม) คะแนนความคล้ายคลึงของ ResNet-50 อาจใกล้เคียงกัน ต้องอาศัย OCR หรือเอกลักษณ์เฉพาะ (รอยสติกเกอร์ รอยบุบ ชุดแต่ง) จาก ORB Descriptors มาช่วยจำแนก
4. **ความเข้ากันได้ของ GPU สถาปัตยกรรมใหม่:**
   - สำหรับการ์ดจอซีรีส์ใหม่ล่าสุด (เช่น RTX 50-Series Blackwell) จำเป็นต้องใช้ PyTorch ที่รองรับ CUDA 12.4/13.0+ มิฉะนั้นระบบ `get_optimal_device()` ใน `utils/config.py` จะ Fallback ไปทำงานบน CPU อัตโนมัติเพื่อป้องกันโปรแกรม Crash

---

### 🚀 สิ่งที่ต้องพัฒนาต่อ (Next Steps / Phase ต่อไป)

1. **โมเดล Vehicle Re-Identification (Re-ID) เฉพาะทาง:**
   - อัปเกรดจาก Backbone ทั่วไป (ResNet-50 ImageNet) ไปใช้โมเดล Vehicle Re-ID ที่ผ่านการ Fine-tune ด้วยชุดข้อมูลรถยนต์โดยเฉพาะ (เช่น VeRi-776 หรือ CityFlow) เพื่อเพิ่มความแม่นยำในการแยกแยะรถรุ่นเดียวกัน
2. **ปรับปรุง Thai License Plate Recognition (Thai LPR):**
   - ปัจจุบันใช้ EasyOCR แบบ Generic; สามารถพัฒนาโมเดลสองขั้นตอน (Two-stage Plate Detector เช่น YOLOv8-plate + Thai Character OCR Model) เพื่อให้ทนทานต่อป้ายทะเบียนที่เอียง มัว หรือเลอะโคลนได้ดียิ่งขึ้น
3. **Parallel Multi-Video Scanning (Multiprocessing / Async Workers):**
   - ปรับปรุงให้สามารถสแกนไฟล์วิดีโอจากหลายกล้องพร้อมกัน (Concurrent Workers) แทนการสแกนทีละไฟล์ (Sequential Loop) เมื่อใช้งานบนเครื่องที่มี CPU หลายคอร์หรือมี Multi-GPU
4. **การรองรับ Live RTSP / IP Camera Stream:**
   - ขยายขีดความสามารถจากการสแกนไฟล์วิดีโอย้อนหลัง ไปสู่การเชื่อมต่อ Stream สดผ่านโปรโตคอล RTSP จากกล้องวงจรปิด เพื่อส่งการแจ้งเตือนแบบ Real-time ทันทีที่พบรถเป้าหมายผ่านกล้อง
5. **ระบบ Export รายงานเป็น PDF:**
   - เพิ่มฟังก์ชันแปลงรายงาน HTML ออกมาเป็นเอกสาร PDF ในคลิกเดียว เพื่อความสะดวกในการแนบเอกสารส่งพนักงานสอบสวนหรือเจ้าหน้าที่ตำรวจ
