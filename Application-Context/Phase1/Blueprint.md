# 🔍 Eyelnw — Blueprint แผนพัฒนาโปรแกรมตรวจจับรถจากคลิป CCTV

> **ชื่อโปรเจกต์:** Eyelnw (Eye + ล้นหลาม + Investigation)
> **เป้าหมาย:** ช่วยผู้ใช้ค้นหารถที่ถูกขโมยจากคลิป CCTV โดยอัตโนมัติ ลดเวลาและทรัพยากรในการนั่งดูคลิปด้วยตนเอง
> **แพลตฟอร์ม:** Windows 11
> **ภาษาหลัก:** Python 3.10+

---

## 📋 สารบัญ

1. [ภาพรวมโปรแกรม](#1-ภาพรวมโปรแกรม)
2. [ฟีเจอร์หลัก](#2-ฟีเจอร์หลัก)
3. [สถาปัตยกรรมระบบ](#3-สถาปัตยกรรมระบบ)
4. [เทคโนโลยีที่ใช้](#4-เทคโนโลยีที่ใช้)
5. [โครงสร้างไฟล์โปรเจกต์](#5-โครงสร้างไฟล์โปรเจกต์)
6. [ขั้นตอนการทำงาน (Pipeline)](#6-ขั้นตอนการทำงาน-pipeline)
7. [รายละเอียดแต่ละโมดูล](#7-รายละเอียดแต่ละโมดูล)
8. [การออกแบบ UI](#8-การออกแบบ-ui)
9. [รูปแบบรายงานผลลัพธ์](#9-รูปแบบรายงานผลลัพธ์)
10. [แผนพัฒนาเป็นเฟส](#10-แผนพัฒนาเป็นเฟส)
11. [ข้อจำกัดและข้อพิจารณา](#11-ข้อจำกัดและข้อพิจารณา)
12. [วิธีติดตั้งและใช้งาน](#12-วิธีติดตั้งและใช้งาน)

---

## 1. ภาพรวมโปรแกรม

### ปัญหาที่แก้

- รถถูกขโมยแต่ไม่รู้ว่าเมื่อไหร่ ใครเอาไป
- มีคลิป CCTV จำนวนมาก แต่ไม่มีเวลานั่งดูทั้งหมด
- ต้องการเบาะแสเพื่อใช้ในการแจ้งความและติดตามจับ

### วิธีแก้

โปรแกรมจะ **สแกนคลิป CCTV อัตโนมัติ** โดยผู้ใช้เพียงแค่:
1. แนบรูปรถที่ตามหา (หลายๆ รูป หลายๆ มุม)
2. เลือกไฟล์วิดีโอ CCTV
3. กด **"เริ่มค้นหา"**
4. รอรับ **รายงานเบาะแส** พร้อมช่วงเวลาและภาพหน้าจอ

### ผลลัพธ์ที่ได้

| ข้อมูล | รายละเอียด |
|--------|------------|
| ⏱️ ช่วงเวลาที่พบ | Timestamp ในคลิปที่ตรวจพบรถเป้าหมาย |
| 📸 ภาพหน้าจอ | ภาพตัดจากเฟรมที่พบรถ พร้อมกรอบสี่เหลี่ยมล้อมรอบ |
| 📊 ค่าความเชื่อมั่น | เปอร์เซ็นต์ความมั่นใจว่าเป็นรถคันเดียวกัน |
| 🎬 คลิปตัด | ตัดเฉพาะช่วงที่พบรถเป้าหมายออกมาเป็นคลิปสั้นๆ |
| 🚗 ทิศทาง | ทิศทางการเคลื่อนที่ของรถ (ซ้าย/ขวา/เข้า/ออก) |
| 📝 รายงาน HTML | รายงานสรุปพร้อมรูปภาพ สามารถพิมพ์หรือส่งต่อได้ |

---

## 2. ฟีเจอร์หลัก

### 2.1 การรับข้อมูลรถเป้าหมาย (Target Input)

- ✅ รองรับการแนบรูปรถหลายๆ รูป (แนะนำ 3-10 รูป)
- ✅ รองรับหลายมุมมอง: ด้านหน้า, ด้านข้าง, ด้านหลัง, มุมเฉียง, มุมสูง (คล้ายมุม CCTV)
- ✅ รองรับรูปแบบไฟล์: JPG, PNG, BMP, WEBP
- ✅ ผู้ใช้สามารถระบุข้อมูลเพิ่มเติม: สี, ยี่ห้อ, รุ่น, ทะเบียน (ถ้ามี)

### 2.2 การประมวลผลวิดีโอ (Video Processing)

- ✅ รองรับไฟล์วิดีโอ: MP4, AVI, MKV, MOV, FLV
- ✅ รองรับหลายไฟล์พร้อมกัน (Batch Processing)
- ✅ ข้ามเฟรมอัจฉริยะ — ไม่ต้องวิเคราะห์ทุกเฟรม ลดเวลาประมวลผล
- ✅ รองรับวิดีโอ CCTV ที่มีความละเอียดต่างๆ (360p ถึง 4K)
- ✅ แสดง Progress Bar ระหว่างประมวลผล

### 2.3 การตรวจจับและจับคู่รถ (Detection & Matching)

- ✅ ตรวจจับรถทุกคันในเฟรม (YOLOv8 Object Detection)
- ✅ จับคู่รถที่ตรวจพบกับรูปอ้างอิง (Feature Matching + Color Analysis)
- ✅ วิเคราะห์สีรถ (Color Histogram Matching)
- ✅ เปรียบเทียบรูปร่าง/โครงสร้างรถ (Deep Feature Embedding)
- ✅ ตรวจจับทะเบียน OCR (ถ้ามองเห็นชัด)
- ✅ ค่าความเชื่อมั่น (Confidence Score) สำหรับทุกการจับคู่

### 2.4 รายงานผลลัพธ์ (Report)

- ✅ รายงาน HTML พร้อมรูปภาพ — เปิดดูในเบราว์เซอร์ได้ทันที
- ✅ ตัดคลิปสั้นเฉพาะช่วงที่พบ
- ✅ บันทึกภาพหน้าจอพร้อมกรอบล้อมรถ
- ✅ เรียงลำดับตามเวลา
- ✅ กรองตามค่าความเชื่อมั่น (เช่น เอาเฉพาะ ≥70%)

### 2.5 ส่วนติดต่อผู้ใช้ (GUI)

- ✅ หน้าจอใช้งานง่าย ลาก-วาง (Drag & Drop) ได้
- ✅ แสดงตัวอย่างรูปรถที่แนบ
- ✅ แสดงตัวอย่างเฟรมวิดีโอ
- ✅ แสดงความคืบหน้าแบบ Real-time
- ✅ สามารถหยุด/หยุดชั่วคราว/ดำเนินต่อ ได้

---

## 3. สถาปัตยกรรมระบบ

```
┌─────────────────────────────────────────────────────────────┐
│                    🖥️ GUI Layer (CustomTkinter)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ หน้าแนบรูป │  │ หน้าเลือก │  │ หน้าสแกน  │  │ หน้ารายงาน │  │
│  │ รถเป้าหมาย │  │  วิดีโอ   │  │ + Progress│  │  ผลลัพธ์   │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────┬─────┘  │
│        │              │             │               │        │
└────────┼──────────────┼─────────────┼───────────────┼────────┘
         │              │             │               │
┌────────┼──────────────┼─────────────┼───────────────┼────────┐
│        ▼              ▼             ▼               ▼        │
│               ⚙️ Core Engine (Python Backend)                │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │ Target Loader  │  │ Video Scanner  │  │ Report Generator │  │
│  │ (โหลดรูป+      │  │ (สแกนวิดีโอ    │  │ (สร้างรายงาน     │  │
│  │  สร้าง Feature) │  │  ตรวจจับรถ)    │  │  HTML + คลิปสั้น) │  │
│  └───────┬───────┘  └───────┬───────┘  └────────┬─────────┘  │
│          │                  │                    │            │
│  ┌───────┴──────────────────┴────────────────────┴─────────┐ │
│  │              🧠 AI/ML Pipeline                            │ │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐  │ │
│  │  │ YOLOv8   │ │ Feature   │ │ Color    │ │ OCR       │  │ │
│  │  │ Detector │ │ Matcher   │ │ Analyzer │ │ (ทะเบียน)  │  │ │
│  │  └──────────┘ └───────────┘ └──────────┘ └───────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. เทคโนโลยีที่ใช้

### 4.1 ภาษาและ Runtime

| เทคโนโลยี | เวอร์ชัน | วัตถุประสงค์ |
|-----------|---------|-------------|
| Python | 3.10+ | ภาษาหลักในการพัฒนา |
| pip | latest | จัดการ Package |

### 4.2 AI/ML Libraries

| Library | วัตถุประสงค์ |
|---------|-------------|
| **ultralytics (YOLOv8)** | ตรวจจับรถในเฟรมวิดีโอ (Object Detection) |
| **OpenCV (cv2)** | ประมวลผลภาพและวิดีโอ, Feature Matching, Color Analysis |
| **torch (PyTorch)** | Backend สำหรับ YOLOv8 และ Deep Feature Extraction |
| **torchvision** | Pre-trained models สำหรับ Feature Embedding (ResNet/EfficientNet) |
| **easyocr** | อ่านทะเบียนรถ (OCR) |
| **scikit-learn** | คำนวณ Similarity, Clustering ผลลัพธ์ |
| **numpy** | การคำนวณ Array |

### 4.3 GUI & Utility

| Library | วัตถุประสงค์ |
|---------|-------------|
| **customtkinter** | สร้างหน้าจอ GUI ที่ทันสมัย |
| **Pillow (PIL)** | จัดการรูปภาพ |
| **Jinja2** | สร้าง HTML Report |
| **moviepy** | ตัดคลิปวิดีโอสั้น |
| **tqdm** | แสดง Progress Bar |

### 4.4 ทำไมถึงเลือกเทคโนโลยีเหล่านี้

**YOLOv8** — เป็นโมเดลตรวจจับวัตถุที่เร็วและแม่นยำที่สุดในปัจจุบัน สามารถตรวจจับ "car" ได้ในทุกสภาพแสง รองรับ GPU เพื่อเร่งความเร็ว

**Feature Matching (ORB/SIFT + Deep Embedding)** — ใช้ 2 วิธีร่วมกัน:
1. Feature แบบดั้งเดิม (ORB/SIFT) จับคู่จุดเด่นบนตัวรถ
2. Deep Feature (ResNet) สร้าง Embedding ของรูปรถเพื่อเปรียบเทียบ Similarity

ใช้ 2 วิธีรวมกันเพื่อให้แม่นยำมากขึ้น

**CustomTkinter** — GUI ที่สวยงามกว่า Tkinter ปกติ ติดตั้งง่าย ไม่ต้องใช้เว็บเบราว์เซอร์

---

## 5. โครงสร้างไฟล์โปรเจกต์

```
Eyelnw/
├── 📄 Blueprint.md              # ไฟล์แผนพัฒนานี้
├── 📄 requirements.txt          # รายการ Library ที่ต้องติดตั้ง
├── 📄 README.md                 # คู่มือการใช้งาน
├── 📄 main.py                   # จุดเริ่มต้นโปรแกรม (Entry Point)
│
├── 📁 gui/                      # ส่วน GUI
│   ├── __init__.py
│   ├── app.py                   # หน้าจอหลัก (Main Window)
│   ├── target_panel.py          # แผงแนบรูปรถเป้าหมาย
│   ├── video_panel.py           # แผงเลือกวิดีโอ CCTV
│   ├── scan_panel.py            # แผงแสดงความคืบหน้าการสแกน
│   ├── result_panel.py          # แผงแสดงผลลัพธ์
│   └── widgets.py               # UI Components ที่ใช้ซ้ำ
│
├── 📁 core/                     # ส่วนประมวลผลหลัก
│   ├── __init__.py
│   ├── target_loader.py         # โหลดและเตรียมรูปรถเป้าหมาย
│   ├── video_scanner.py         # สแกนวิดีโอเฟรมต่อเฟรม
│   ├── detector.py              # ตรวจจับรถด้วย YOLOv8
│   ├── matcher.py               # จับคู่รถที่ตรวจพบกับรถเป้าหมาย
│   ├── color_analyzer.py        # วิเคราะห์สีรถ
│   ├── feature_extractor.py     # สร้าง Feature Embedding
│   ├── ocr_reader.py            # อ่านทะเบียนรถ
│   └── motion_tracker.py        # ติดตามทิศทางการเคลื่อนที่
│
├── 📁 report/                   # ส่วนสร้างรายงาน
│   ├── __init__.py
│   ├── generator.py             # สร้างรายงาน HTML
│   ├── clip_cutter.py           # ตัดคลิปสั้น
│   └── templates/
│       └── report_template.html # Template สำหรับรายงาน HTML
│
├── 📁 models/                   # โมเดล AI (จะดาวน์โหลดอัตโนมัติ)
│   └── .gitkeep
│
├── 📁 output/                   # ผลลัพธ์ที่สร้างจากการสแกน
│   └── .gitkeep
│
├── 📁 assets/                   # ไอคอนและทรัพยากร GUI
│   └── icon.ico
│
└── 📁 utils/                    # Utility Functions
    ├── __init__.py
    ├── config.py                # ค่าตั้งค่าโปรแกรม
    ├── logger.py                # บันทึก Log
    └── helpers.py               # ฟังก์ชันช่วยเหลือทั่วไป
```

---

## 6. ขั้นตอนการทำงาน (Pipeline)

### 6.1 ขั้นตอนโดยละเอียด

#### Step 1: โหลดรูปรถเป้าหมาย (Target Loading)
```
Input: รูปรถ 3-10 รูป (หลายมุม)
Process:
  1. โหลดรูปทั้งหมด
  2. สำหรับแต่ละรูป:
     a. Resize เป็นขนาดมาตรฐาน (224x224 สำหรับ Deep Feature)
     b. สร้าง Color Histogram (HSV Color Space)
     c. สร้าง ORB/SIFT Keypoints
     d. สร้าง Deep Embedding ผ่าน ResNet50 (ตัด FC layer ออก)
  3. รวม Feature ทุกรูปเป็น "Target Profile"
     - เฉลี่ย Embedding vectors
     - รวม Keypoints
     - เฉลี่ย Color Histogram
Output: Target Profile Object
```

#### Step 2: สแกนวิดีโอ (Video Scanning)
```
Input: ไฟล์วิดีโอ CCTV + Target Profile
Process:
  1. เปิดวิดีโอด้วย OpenCV
  2. อ่านข้อมูล: FPS, ความยาว, Resolution
  3. คำนวณ Frame Skip Rate:
     - ถ้า FPS = 30 → วิเคราะห์ทุกๆ 15 เฟรม (2 ครั้ง/วินาที)
     - ถ้า FPS = 25 → วิเคราะห์ทุกๆ 12 เฟรม
     - ผู้ใช้ปรับได้ (เร็วขึ้น vs แม่นยำขึ้น)
  4. วนอ่านเฟรม
  5. ส่งเฟรมไปยัง Detection Pipeline
Output: List of Detection Results
```

#### Step 3: ตรวจจับรถในเฟรม (Car Detection)
```
Input: เฟรมวิดีโอ
Process:
  1. ส่งเฟรมเข้า YOLOv8 (yolov8n.pt หรือ yolov8s.pt)
  2. กรองเฉพาะ class "car", "truck", "bus" (class 2, 5, 7 ใน COCO)
  3. กรอง Confidence >= 0.3
  4. สำหรับแต่ละ Bounding Box:
     a. Crop รูปรถออกมา
     b. ส่งไปขั้นตอนจับคู่
Output: List of Cropped Car Images + Bounding Boxes
```

#### Step 4: จับคู่รถ (Matching)
```
Input: Cropped Car Image + Target Profile
Process:
  1. Color Score (น้ำหนัก 25%):
     - คำนวณ HSV Histogram ของรถที่ตรวจพบ
     - เปรียบเทียบกับ Target ด้วย cv2.compareHist (Correlation)
  2. Feature Score (น้ำหนัก 25%):
     - สร้าง ORB Keypoints ของรถที่ตรวจพบ
     - จับคู่ด้วย BFMatcher + KNN
     - คำนวณ Good Match Ratio
  3. Deep Similarity Score (น้ำหนัก 40%):
     - สร้าง Embedding ผ่าน ResNet50
     - คำนวณ Cosine Similarity กับ Target Embedding
  4. OCR Bonus Score (น้ำหนัก 10%):
     - พยายามอ่านทะเบียน
     - ถ้าตรงกับทะเบียนที่ผู้ใช้ระบุ → +100%
  5. Combined Score = weighted average ของทุก score
Output: Combined Score (0.0 - 1.0)
```

#### Step 5: สร้างรายงาน (Report Generation)
```
Input: List of Detections (ที่ผ่าน Threshold)
Process:
  1. เรียงลำดับตามเวลา
  2. จัดกลุ่ม Detection ที่ใกล้กัน (ภายใน 5 วินาที → กลุ่มเดียว)
  3. สำหรับแต่ละกลุ่ม:
     a. เลือกภาพที่ Confidence สูงสุดเป็นตัวแทน
     b. ตัดคลิปสั้น (5 วินาทีก่อน - 5 วินาทีหลัง)
     c. วิเคราะห์ทิศทางการเคลื่อนที่
  4. สร้าง HTML Report ด้วย Jinja2
  5. บันทึกทั้งหมดไปยัง output/ folder
Output: HTML Report + Screenshots + Short Clips
```

---

## 7. รายละเอียดแต่ละโมดูล

### 7.1 `core/target_loader.py` — โหลดรูปรถเป้าหมาย

```python
class TargetProfile:
    """โปรไฟล์ของรถเป้าหมาย"""

    def __init__(self):
        self.images: list           # รูปต้นฉบับทั้งหมด
        self.color_histograms: list # Color Histograms (HSV)
        self.avg_histogram: np.array # เฉลี่ย Histogram
        self.keypoints: list        # ORB/SIFT Keypoints
        self.descriptors: list      # Feature Descriptors
        self.embeddings: list       # Deep Embeddings
        self.avg_embedding: np.array # เฉลี่ย Embedding
        self.plate_number: str      # ทะเบียนรถ (ถ้าระบุ)
        self.car_color: str         # สีรถ (ถ้าระบุ)
        self.car_brand: str         # ยี่ห้อรถ (ถ้าระบุ)

    def load_images(self, image_paths: list):
        """โหลดรูปทั้งหมดและสร้าง Feature"""
        pass

    def get_similarity(self, candidate_image) -> float:
        """คำนวณ Similarity กับรูปรถที่ตรวจพบ"""
        pass
```

**หน้าที่หลัก:**
- รับรูปรถจากผู้ใช้
- Preprocess: resize, normalize
- สร้าง Feature ทุกประเภท (Color, Keypoints, Embedding)
- จัดเก็บเป็น TargetProfile

### 7.2 `core/detector.py` — ตรวจจับรถด้วย YOLOv8

```python
class VehicleDetector:
    """ตรวจจับรถในเฟรมวิดีโอ"""

    def __init__(self, model_size='n'):  # 'n'=nano(เร็ว), 's'=small(แม่น)
        self.model = YOLO(f'yolov8{model_size}.pt')
        self.vehicle_classes = [2, 5, 7]  # car, bus, truck

    def detect(self, frame) -> list:
        """
        ตรวจจับรถทั้งหมดในเฟรม
        Returns: list of {bbox, confidence, class, cropped_image}
        """
        pass
```

**หน้าที่หลัก:**
- โหลด YOLOv8 model (ดาวน์โหลดอัตโนมัติครั้งแรก)
- ตรวจจับรถ, รถบรรทุก, รถบัส ในเฟรม
- ส่งคืน Bounding Box + Cropped Image

### 7.3 `core/matcher.py` — จับคู่รถ

```python
class VehicleMatcher:
    """จับคู่รถที่ตรวจพบกับรถเป้าหมาย"""

    def __init__(self, target_profile: TargetProfile):
        self.target = target_profile
        self.weights = {
            'color': 0.25,
            'feature': 0.25,
            'deep': 0.40,
            'ocr': 0.10
        }

    def match(self, candidate_image) -> MatchResult:
        """
        เปรียบเทียบรถที่ตรวจพบกับรถเป้าหมาย
        Returns: MatchResult with combined_score, individual_scores
        """
        pass
```

**หน้าที่หลัก:**
- รับรูป Crop ของรถที่ตรวจพบ
- คำนวณ Score จากทุกวิธี
- รวม Score ด้วย Weighted Average
- ส่งคืน MatchResult

### 7.4 `core/color_analyzer.py` — วิเคราะห์สี

```python
class ColorAnalyzer:
    """วิเคราะห์และเปรียบเทียบสีรถ"""

    def compute_histogram(self, image) -> np.array:
        """สร้าง HSV Color Histogram"""
        pass

    def compare_colors(self, hist1, hist2) -> float:
        """เปรียบเทียบ Histogram 2 ชุด → Score 0-1"""
        pass

    def get_dominant_color(self, image) -> str:
        """หาสีเด่นของรถ (เช่น ขาว, ดำ, แดง)"""
        pass
```

### 7.5 `core/feature_extractor.py` — สร้าง Deep Feature

```python
class FeatureExtractor:
    """สร้าง Deep Feature Embedding ด้วย ResNet50"""

    def __init__(self):
        self.model = None  # Lazy load
        self.transform = None

    def extract(self, image) -> np.array:
        """สร้าง Feature Vector 2048 มิติ"""
        pass

    def cosine_similarity(self, vec1, vec2) -> float:
        """คำนวณ Cosine Similarity"""
        pass
```

### 7.6 `core/video_scanner.py` — สแกนวิดีโอ

```python
class VideoScanner:
    """สแกนวิดีโอ CCTV เฟรมต่อเฟรม"""

    def __init__(self, detector, matcher, config):
        self.detector = detector
        self.matcher = matcher
        self.frame_skip = config.frame_skip  # ข้ามกี่เฟรม
        self.threshold = config.threshold    # Threshold ความเชื่อมั่น

    def scan(self, video_path, progress_callback=None) -> ScanResult:
        """
        สแกนวิดีโอทั้งไฟล์
        progress_callback: ฟังก์ชัน callback สำหรับอัพเดท UI
        Returns: ScanResult with list of detections
        """
        pass

    def scan_batch(self, video_paths, progress_callback=None) -> list:
        """สแกนหลายไฟล์"""
        pass
```

### 7.7 `core/ocr_reader.py` — อ่านทะเบียน

```python
class PlateReader:
    """อ่านทะเบียนรถด้วย OCR"""

    def __init__(self):
        self.reader = easyocr.Reader(['th', 'en'])

    def read_plate(self, car_image) -> str | None:
        """
        พยายามอ่านทะเบียนจากรูปรถ
        Returns: ข้อความทะเบียน หรือ None ถ้าอ่านไม่ได้
        """
        pass

    def match_plate(self, detected_plate, target_plate) -> float:
        """เปรียบเทียบทะเบียนที่อ่านได้กับทะเบียนเป้าหมาย"""
        pass
```

### 7.8 `core/motion_tracker.py` — ติดตามทิศทาง

```python
class MotionTracker:
    """ติดตามทิศทางการเคลื่อนที่ของรถ"""

    def track_direction(self, detections_group: list) -> str:
        """
        วิเคราะห์ทิศทางจากตำแหน่ง bbox หลายเฟรม
        Returns: "ซ้ายไปขวา", "ขวาไปซ้าย", "เข้ามา", "ออกไป", "หยุดนิ่ง"
        """
        pass
```

### 7.9 `report/generator.py` — สร้างรายงาน

```python
class ReportGenerator:
    """สร้างรายงาน HTML"""

    def generate(self, scan_results: list, output_dir: str):
        """
        สร้างรายงาน HTML พร้อมรูปภาพ
        Output files:
        - report.html
        - screenshots/
        - clips/
        """
        pass
```

---

## 8. การออกแบบ UI

### 8.1 หน้าจอหลัก — Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  🔍 Eyelnw — ตรวจจับรถจากคลิป CCTV              [─] [□] [✕]  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────── Tab 1: รถเป้าหมาย ─────────────────────────────────┐  │
│  │                                                             │  │
│  │  📷 ลากวางรูปรถที่นี่ หรือ คลิกเพื่อเลือก                   │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │  │
│  │  │ รูป 1 │ │ รูป 2 │ │ รูป 3 │ │ รูป 4 │ │  +   │              │  │
│  │  │ ด้านหน้า│ │ ด้านข้าง│ │ ด้านหลัง│ │ มุมสูง │ │      │              │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │  │
│  │                                                             │  │
│  │  ข้อมูลเพิ่มเติม (ไม่บังคับ):                                │  │
│  │  ทะเบียน: [กก 1234      ] สี: [ขาว ▼]                       │  │
│  │  ยี่ห้อ:  [Toyota        ] รุ่น: [Yaris       ]               │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────── Tab 2: วิดีโอ CCTV ────────────────────────────────┐  │
│  │                                                             │  │
│  │  📁 ลากวางไฟล์วิดีโอ หรือ คลิกเพื่อเลือก                    │  │
│  │  ┌──────────────────────────────────────────────┐           │  │
│  │  │ 📹 CCTV_Front_20240101.mp4    │ 2.3 GB │ ✕ │           │  │
│  │  │ 📹 CCTV_Back_20240101.mp4     │ 1.8 GB │ ✕ │           │  │
│  │  │ 📹 CCTV_Side_20240101.mp4     │ 2.1 GB │ ✕ │           │  │
│  │  └──────────────────────────────────────────────┘           │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────── ตั้งค่า ───────────────────────────────────────────┐  │
│  │  ความเร็ว: [●━━━━━━] เร็ว ←→ แม่นยำ                        │  │
│  │  Threshold: [0.60 ▼]  โมเดล: [YOLOv8n (เร็ว) ▼]            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ╔═══════════════════════════════════════════════════════════╗   │
│  ║              🔍 เริ่มค้นหา                                  ║   │
│  ╚═══════════════════════════════════════════════════════════╝   │
│                                                                  │
│  ┌─────── ความคืบหน้า ───────────────────────────────────────┐  │
│  │  ไฟล์: CCTV_Front_20240101.mp4  (1/3)                      │  │
│  │  ████████████████░░░░░░░░  65%  (01:23:45 / 02:08:00)      │  │
│  │  พบ: 3 ครั้ง  │  เวลาที่เหลือ: ~15 นาที                     │  │
│  │  [⏸ หยุดชั่วคราว]  [⏹ หยุด]                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 หน้าแสดงผลลัพธ์

```
┌──────────────────────────────────────────────────────────────────┐
│  📋 ผลการค้นหา — พบรถเป้าหมาย 5 ครั้ง                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  กรอง: [ทั้งหมด ▼]  เรียงตาม: [เวลา ▼]  Threshold: [≥60% ▼]   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ #1  📹 CCTV_Front.mp4  ⏱ 03:24:15  📊 87% ✅ สูง       │   │
│  │ ┌──────────────┐                                         │   │
│  │ │   [ภาพหน้าจอ]  │  🚗 ทิศทาง: ซ้ายไปขวา                │   │
│  │ │   พร้อมกรอบ    │  🎨 สี: ตรงกัน (ขาว)                   │   │
│  │ │   ล้อมรถ       │  📝 ทะเบียน: กก 12xx (บางส่วน)         │   │
│  │ └──────────────┘  [▶ ดูคลิป] [📁 เปิดโฟลเดอร์]           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ #2  📹 CCTV_Back.mp4   ⏱ 03:25:02  📊 72% ⚠️ ปานกลาง  │   │
│  │ ┌──────────────┐                                         │   │
│  │ │   [ภาพหน้าจอ]  │  🚗 ทิศทาง: เข้ามา                    │   │
│  │ │   พร้อมกรอบ    │  🎨 สี: ตรงกัน (ขาว)                   │   │
│  │ │   ล้อมรถ       │  📝 ทะเบียน: ไม่ชัด                    │   │
│  │ └──────────────┘  [▶ ดูคลิป] [📁 เปิดโฟลเดอร์]           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ═══════════════════════════════════════════════════════════     │
│  [📄 เปิดรายงาน HTML]  [📁 เปิดโฟลเดอร์ผลลัพธ์]  [🔄 สแกนใหม่] │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. รูปแบบรายงานผลลัพธ์

### 9.1 HTML Report Structure

รายงาน HTML จะมีเนื้อหาดังนี้:

```
📄 report.html
├── ส่วนหัว: ข้อมูลรถเป้าหมาย + รูปอ้างอิง
├── สรุป: พบกี่ครั้ง, จากกี่ไฟล์, ช่วงเวลา
├── Timeline: แสดงเป็นไทม์ไลน์
├── รายละเอียดแต่ละครั้ง:
│   ├── ภาพหน้าจอ (พร้อมกรอบล้อม)
│   ├── ข้อมูลเวลา
│   ├── ค่า Confidence
│   ├── ทิศทางการเคลื่อนที่
│   ├── ทะเบียน (ถ้าอ่านได้)
│   └── ลิงก์ไปคลิปสั้น
└── ส่วนท้าย: ข้อมูลการตั้งค่าที่ใช้สแกน
```

### 9.2 โครงสร้างโฟลเดอร์ Output

```
output/
└── scan_20240101_152030/          # ชื่อจาก วันที่_เวลา
    ├── report.html                # รายงานหลัก
    ├── screenshots/               # ภาพหน้าจอ
    │   ├── match_001_032415.jpg
    │   ├── match_002_032502.jpg
    │   └── ...
    ├── clips/                     # คลิปสั้น
    │   ├── clip_001_032415.mp4
    │   ├── clip_002_032502.mp4
    │   └── ...
    └── data/
        └── results.json           # ข้อมูลดิบ (JSON)
```

---

## 10. แผนพัฒนาเป็นเฟส

### Phase 1: Foundation 🏗️ (Core Engine)

**เฟสนี้เป็นหัวใจสำคัญ — ต้องทำให้ Detection + Matching ทำงานได้ถูกต้อง**

| ลำดับ | งาน | ไฟล์ | รายละเอียด |
|-------|------|------|-----------|
| 1.1 | ตั้งค่าโปรเจกต์ | `requirements.txt`, `config.py` | ติดตั้ง Dependencies ทั้งหมด |
| 1.2 | Target Loader | `core/target_loader.py` | โหลดรูป, สร้าง Feature Profile |
| 1.3 | Vehicle Detector | `core/detector.py` | ตรวจจับรถด้วย YOLOv8 |
| 1.4 | Color Analyzer | `core/color_analyzer.py` | วิเคราะห์และเปรียบเทียบสี |
| 1.5 | Feature Extractor | `core/feature_extractor.py` | สร้าง Deep Embedding |
| 1.6 | Vehicle Matcher | `core/matcher.py` | รวม Score ทุกวิธี |
| 1.7 | Video Scanner | `core/video_scanner.py` | สแกนวิดีโอ + ข้ามเฟรมอัจฉริยะ |
| 1.8 | ทดสอบ Pipeline | ทดสอบด้วยคลิปสั้น | ยืนยันว่าระบบทำงานได้ |

### Phase 2: Report & Output 📋

| ลำดับ | งาน | ไฟล์ | รายละเอียด |
|-------|------|------|-----------|
| 2.1 | Report Generator | `report/generator.py` | สร้างรายงาน HTML |
| 2.2 | HTML Template | `report/templates/` | ออกแบบ Template สวยงาม |
| 2.3 | Clip Cutter | `report/clip_cutter.py` | ตัดคลิปสั้นเฉพาะช่วงที่พบ |
| 2.4 | Motion Tracker | `core/motion_tracker.py` | วิเคราะห์ทิศทาง |

### Phase 3: GUI 🖥️

| ลำดับ | งาน | ไฟล์ | รายละเอียด |
|-------|------|------|-----------|
| 3.1 | Main Window | `gui/app.py` | โครงหน้าจอหลัก |
| 3.2 | Target Panel | `gui/target_panel.py` | Drag & Drop รูปรถ |
| 3.3 | Video Panel | `gui/video_panel.py` | เลือกไฟล์วิดีโอ |
| 3.4 | Scan Panel | `gui/scan_panel.py` | Progress + Control |
| 3.5 | Result Panel | `gui/result_panel.py` | แสดงผลลัพธ์ |
| 3.6 | Entry Point | `main.py` | รวมทุกส่วนเข้าด้วยกัน |

### Phase 4: OCR & Enhancement ✨

| ลำดับ | งาน | ไฟล์ | รายละเอียด |
|-------|------|------|-----------|
| 4.1 | OCR Reader | `core/ocr_reader.py` | อ่านทะเบียน |
| 4.2 | ปรับ Threshold อัตโนมัติ | `core/matcher.py` | Auto-calibrate |
| 4.3 | GPU Acceleration | ทั่วไป | ใช้ CUDA ถ้ามี GPU |
| 4.4 | Batch Processing | `core/video_scanner.py` | ประมวลผลหลายไฟล์ |

---

## 11. ข้อจำกัดและข้อพิจารณา

### 11.1 ข้อจำกัดทางเทคนิค

**ความแม่นยำขึ้นอยู่กับหลายปัจจัย:**
- คุณภาพกล้อง CCTV (ยิ่งชัดยิ่งแม่นยำ)
- แสงสว่าง (กลางคืนจะแม่นยำน้อยลง)
- มุมกล้อง (ถ้ามุมต่างจากรูปอ้างอิงมากจะแม่นยำน้อยลง)
- ขนาดรถในเฟรม (ถ้ารถอยู่ไกลมากจะตรวจจับยาก)
- รถสีเดียวกัน รุ่นเดียวกัน อาจถูกจับคู่ผิด (False Positive)

**ทรัพยากรเครื่อง:**
- ใช้ RAM ค่อนข้างมาก (~4-8 GB ขณะประมวลผล)
- ถ้ามี GPU (NVIDIA) จะเร็วขึ้น 5-10 เท่า
- วิดีโอยาว 24 ชั่วโมง อาจใช้เวลาสแกน 1-3 ชั่วโมง (ขึ้นอยู่กับเครื่อง)

### 11.2 คำแนะนำสำหรับผู้ใช้

**เพื่อผลลัพธ์ที่แม่นยำที่สุด:**
1. ใช้รูปรถอ้างอิงหลากหลายมุม (3-10 รูป)
2. ถ้ามีรูปจากมุมสูง (คล้ายมุม CCTV) จะช่วยได้มาก
3. ระบุทะเบียนรถเพื่อเพิ่มความแม่นยำ
4. เริ่มจาก Threshold 60% แล้วค่อยปรับ
5. ตรวจสอบผลลัพธ์ด้วยตาอีกครั้ง (โปรแกรมเป็นตัวช่วย ไม่ใช่คำตอบสุดท้าย)

### 11.3 ข้อพิจารณาทางกฎหมาย

- ผู้ใช้ต้องมีสิทธิ์เข้าถึงคลิป CCTV ที่ใช้
- ผลลัพธ์จากโปรแกรมเป็นเบาะแสเบื้องต้น ควรนำไปประกอบกับหลักฐานอื่น
- แนะนำให้ใช้รายงานเพื่อประกอบการแจ้งความ ไม่ใช่หลักฐานชี้ขาด

---

## 12. วิธีติดตั้งและใช้งาน

### 12.1 ความต้องการระบบ

| รายการ | ขั้นต่ำ | แนะนำ |
|--------|---------|-------|
| OS | Windows 10/11 | Windows 11 |
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| RAM | 8 GB | 16 GB |
| GPU | ไม่บังคับ (ใช้ CPU ได้) | NVIDIA GTX 1060+ (CUDA) |
| Storage | 5 GB (โปรแกรม + โมเดล) | SSD แนะนำ |
| Python | 3.10+ | 3.11 |

### 12.2 ขั้นตอนการติดตั้ง

```powershell
# 1. Clone โปรเจกต์ (หรือดาวน์โหลด)
cd d:\Universal\Eyelnw

# 2. สร้าง Virtual Environment
python -m venv venv
.\venv\Scripts\activate

# 3. ติดตั้ง Dependencies
pip install -r requirements.txt

# 4. รันโปรแกรม
python main.py
```

### 12.3 วิธีใช้งาน (Quick Start)

```
1. เปิดโปรแกรม → python main.py
2. Tab "รถเป้าหมาย" → ลากวางรูปรถที่ตามหา (แนะนำ 3-10 รูป)
3. กรอกข้อมูลเพิ่มเติม (ทะเบียน, สี, ยี่ห้อ) ถ้ามี
4. Tab "วิดีโอ CCTV" → ลากวางไฟล์วิดีโอ
5. ปรับตั้งค่า (ความเร็ว, Threshold) ถ้าต้องการ
6. กด "🔍 เริ่มค้นหา"
7. รอ... (แสดงความคืบหน้าตลอด)
8. ดูผลลัพธ์ → เปิดรายงาน HTML หรือดูในโปรแกรม
9. นำเบาะแสไปใช้ต่อ!
```

---

## 📌 สรุปภาพรวม

| หัวข้อ | รายละเอียด |
|--------|------------|
| **ชื่อ** | Eyelnw |
| **ภาษา** | Python 3.10+ |
| **AI Model** | YOLOv8 (Detection) + ResNet50 (Feature) + EasyOCR |
| **GUI** | CustomTkinter |
| **Output** | HTML Report + Screenshots + Short Clips + JSON |
| **แพลตฟอร์ม** | Windows 11 |
| **เฟส** | 4 เฟส (Foundation → Report → GUI → Enhancement) |
| **จุดเด่น** | ใช้ง่าย, หลายรูปหลายมุม, รายงานครบถ้วน, ตัดคลิปสั้นอัตโนมัติ |

---

> **พร้อมเริ่มพัฒนาแล้ว!** แนะนำให้เริ่มจาก Phase 1 (Core Engine) ก่อน เพราะเป็นหัวใจของโปรแกรม ถ้า Detection + Matching ทำงานได้ดี ส่วนอื่นๆ จะตามมาได้ง่าย
