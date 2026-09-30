# AI REHABILITATION & SAFETY ASSISTANT
## Hệ Thống Trợ Lý Phục Hồi Chức Năng & Giám Sát An Toàn Thông Minh

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![MediaPipe](https://img.shields.io/badge/AI-MediaPipe%20Pose%20%26%20Mesh-orange.svg)](https://developers.google.com/mediapipe)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch%20ExpressionNet-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dự án Nghiên cứu Khoa học Kỹ thuật: **Hệ thống Trí tuệ Nhân tạo Thị giác Máy tính (Edge AI) Cục bộ** hỗ trợ người cao tuổi tập luyện vật lý trị liệu / phục hồi chức năng tại nhà, đồng thời giám sát an toàn 24/7 và tự động gửi cảnh báo khẩn cấp qua Gmail tới người thân khi xảy ra sự cố té ngã.

---

## 🎯 4 PHÂN HỆ AI CỐT LÕI (FINAL MVP SCOPE)

```
                            ┌───────────────────────────────────────────────┐
                            │    AI REHABILITATION & SAFETY ASSISTANT       │
                            │           (PyQt5 Unified Dashboard)           │
                            └───────────────────────┬───────────────────────┘
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 │                                                                     │
                 ▼ (Chế độ Monitor)                                                    ▼ (Chế độ Rehab)
  ┌───────────────────────────────┐                                     ┌───────────────────────────────┐
  │ 1. NHẬN DIỆN KHUÔN MẶT        │                                     │ 3. PHỤC HỒI CHỨC NĂNG (CORE)  │
  │ • OpenCV DNN + CLAHE + LBPH   │                                     │ • MediaPipe Pose 33 Landmarks │
  │ • Tự nạp User ID & Caregiver  │                                     │ • Máy trạng thái FSM 3 bài tập│
  ├───────────────────────────────┤                                     │ • Đếm nhịp & Chấm điểm Form   │
  │ 2. NHẬN DIỆN CẢM XÚC          │                                     └───────────────────────────────┘
  │ • 3 trạng thái: Vui, Thường,  │
  │   Buồn (FACS Biomechanics)    │
  │ • Lọc mượt Deque N=8          │
  ├───────────────────────────────┤
  │ 4. GIÁM SÁT AN TOÀN & NGÃ     │
  │ • Động học cơ thể (Kinematics)│
  │ • Xác thực thời gian (3s FSM) │
  │ • Gửi Gmail kèm ảnh hiện trường│
  └───────────────────────────────┘
```

1. **Nhận diện Khuôn mặt (Face Recognition):** Nhận diện danh tính người cao tuổi, nạp thông số tập luyện và tự động liên kết hồ sơ Gmail của người giám hộ.
2. **Nhận diện Cảm xúc (Emotion Recognition):** Đánh giá 3 trạng thái tâm lý lâm sàng (*Bình thường*, *Vui vẻ*, *Buồn bã*) bằng động học cơ mặt (FACS Biomechanics) kết hợp bộ lọc thời gian Deque $N=8$ triệt tiêu $78.6\%$ rung giật frame.
3. **Phục hồi Chức năng (Rehabilitation Engine - Trọng tâm AI):** Máy trạng thái hữu hạn (FSM) cho 3 bài tập (*Nâng tay qua đầu*, *Đứng lên ngồi xuống*, *Nâng cao đùi*), đếm nhịp chu kỳ chuẩn xác và chấm điểm phong độ Form Score ($0 - 100\%$).
4. **Giám sát An toàn & Phát hiện Ngã (Fall Detection):** Phân tích động học tư thế (Pose Kinematics) kết hợp bộ xác thực thời gian đa tầng (Temporal Verification FSM: $\text{NORMAL} \to \text{SUSPECTED} \to \text{CONFIRMING} \to \text{FALL\_CONFIRMED} \to \text{COOLDOWN}$), triệt tiêu $100\%$ báo động giả khi cúi người nhặt đồ.

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY (CROSS-PLATFORM)

### 1. Chuẩn bị môi trường (Linux / Windows / macOS)
```bash
git clone https://github.com/Gokigenzo/AI_Rehabilitation_Safety_Assistant.git
cd AI_Rehabilitation_Safety_Assistant

# Tạo môi trường ảo
python3 -m venv .venv            # Trên Linux / macOS
# python -m venv .venv           # Trên Windows

# Kích hoạt môi trường ảo
source .venv/bin/activate        # Trên Linux / macOS
# .venv\Scripts\activate         # Trên Windows

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Khởi chạy Ứng dụng Giao diện Chính (PyQt5)
- **Trên Linux / macOS:**
  ```bash
  PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python main.py
  ```
- **Trên Windows (Command Prompt hoặc PowerShell):**
  ```cmd
  set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
  python main.py
  ```

### 3. Chạy Kịch bản Mô phỏng Đầy đủ (Demo Walkthrough)
```bash
# Mô phỏng quy trình 6 bước khép kín từ đăng ký, nhận diện đến cảnh báo ngã
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python demo.py

# Hoặc mô phỏng riêng sự cố ngã và kích hoạt gửi email khẩn cấp
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python simulate_fall_alert.py
```

### 4. Chạy Toàn Bộ Unit Test Suite (37 Tests - 100% Pass)
```bash
QT_QPA_PLATFORM=offscreen PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python -m unittest discover -s tests -p "test_*.py"
```

---

## 📊 KẾT QUẢ THỰC NGHIỆM KHOA HỌC (BENCHMARK)

Chi tiết kế hoạch thực nghiệm, chỉ số đánh giá và câu hỏi phản biện khoa học tại [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md).

| Phân hệ AI | Thước đo Học thuật | Kết quả Đạt được |
|---|---|---|
| **Face Recognition** | Detection + ROI CLAHE Latency / Throughput | **15.25 ms** (**65.6 FPS**) |
| **Emotion Recognition** | 3-State Accuracy / Macro F1-Score | **100.0%** / **F1 = 1.000** (**0.21 ms**) |
| **Rehabilitation Engine** | Real-time Throughput (Arm Raise / Sit-to-Stand / Marching) | **33.3 - 38.2 FPS** |
| **Fall Detection** | Kinematics Latency / False Alarm Rate on Bending | **26.90 ms** (**37.2 FPS**) / **0.0%** |

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```
AI_Rehabilitation_Safety_Assistant/
├── adapters/                        # Clean Adapter Layer (Face, Emotion, Rehab, Fall)
├── app/                             # PyQt5 Unified Dashboard & Navigation
├── core/                            # CameraManager Singleton & UTF-8 Vietnamese Rendering
├── data/                            # Persistent Runtime Data (users, fall_events, sessions)
├── docs/                            # EXPERIMENT_PLAN.md & RESTRUCTURE_AUDIT.md
├── modules/                         # Core AI Logic (Face, Emotion, Rehab, Fall)
├── services/                        # UserService, EmailService, FallMonitor, StateService
├── shared/                          # Shared State JSON & Baseline Cache
├── tests/                           # 37 Unit Tests (100% Pass)
├── main.py                          # Main GUI Entry Point
├── demo.py                          # Complete 6-Step Competition Walkthrough
└── simulate_fall_alert.py           # Live Fall Alert Simulation Script
```

---

## 📜 BẢN QUYỀN & GIẤY PHÉP

Dự án được phát triển phục vụ mục đích nghiên cứu khoa học và cộng đồng, phân phối theo giấy phép MIT License.