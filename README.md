# HỆ THỐNG AI PHÂN TÍCH ĐÁNH GIÁ VÀ HỖ TRỢ QUA GIÁM SÁT CHO NGƯỜI PHỤC HỒI CHỨC NĂNG

Hệ thống MVP tích hợp toàn diện 8 phân hệ AI độc lập nhằm hỗ trợ chăm sóc sức khỏe, phục hồi chức năng và đồng hành cùng người cao tuổi, người bệnh đang trong giai đoạn phục hồi.

---

## 1. Tổng quan & Kiến trúc Hệ thống

Hệ thống được thiết kế theo kiến trúc **Adapter mỏng (Thin Adapters)** và **Trạng thái dùng chung (Shared Data Hub)**, coi các module AI chuyên sâu như các hộp đen (black-box) độc lập mà không can thiệp sâu vào mã nguồn gốc của từng module:

```text
                                  ┌───────────────────────────┐
                                  │      main.py (PyQt5)      │
                                  │   AI Care Dashboard GUI   │
                                  └─────────────┬─────────────┘
                                                │
         ┌────────────────────────┬─────────────┼─────────────┬────────────────────────┐
         │                        │             │             │                        │
         ▼                        ▼             ▼             ▼                        ▼
    Face Module             Health Monitor  Rehab Module  Voice & Gesture         Medication &
    (modules/face)          (modules/fall)  (modules/     (modules/voice &        Memory Hub
                            (modules/       rehab)         modules/gesture)       (services/)
                            emotion)            │             │                        │
         │                        │             │             │                        │
         └────────────────────────┴─────────────┼─────────────┴────────────────────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  Shared Data Hub    │
                                     │  (shared/ results,  │
                                     │   data, alerts,     │
                                     │   recordings, rpts) │
                                     └──────────┬──────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │ Daily Reports & Email │
                                    │ (services/report_svc) │
                                    └───────────────────────┘
```

### Nguyên tắc cốt lõi:
- **Trọng tài Camera (Camera Arbitration):** Chỉ cho phép duy nhất một module chiếm quyền truy cập camera tại một thời điểm, tránh xung đột phần cứng.
- **Giao diện thân thiện người cao tuổi (Elder-Friendly UI):** Font chữ lớn (15–20px), màu tương phản cao, nút bấm lớn dễ thao tác, bảng điều khiển phân nhóm rõ ràng.
- **Độ tin cậy & Phục hồi lỗi (Fault Tolerance):** Lỗi ở bất kỳ một module AI nào không làm sập ứng dụng chính (`DashboardWindow`).
- **Giao tiếp phi cơ sở dữ liệu (Decoupled Shared State):** Dữ liệu truyền tải và lưu trữ dưới dạng chuẩn JSON (`shared/data/`, `shared/results/`, `shared/alerts/`).

---

## 2. Các phân hệ chức năng (8 Modules)

| Phân hệ | Thư mục mã nguồn | Chức năng chính | Output dùng chung |
|---|---|---|---|
| **1. Khuôn mặt (Face)** | `modules/face/` | Đăng ký hồ sơ bệnh nhân, nhận diện danh tính khi bước vào khu vực giám sát. | `shared/data/patient.json`, `shared/results/face.json` |
| **2. Cảm xúc (Emotion)** | `modules/emotion/` & `modules/fall/qingxu/` | Đánh giá sắc thái cảm xúc (Vui vẻ, Bình thường, Buồn bã, Lo âu) qua YOLO11 ONNX & ExpressionNet. | `shared/results/emotion.json` |
| **3. Tư thế & Té ngã (Pose & Fall)** | `modules/fall/deidao/` | Theo dõi thời gian Đứng / Ngồi / Nằm; cảnh báo ngồi quá lâu (>60p); phát hiện té ngã và lưu video sự kiện. | `shared/results/pose.json`, `shared/results/fall.json`, `shared/recordings/` |
| **4. Phục hồi chức năng (Rehabilitation)** | `modules/rehabilitation/` | Hướng dẫn và đếm số lần tập 5 bài tập: Vươn vai, Vỗ tay, Đi bộ tại chỗ, Xoay cổ, Co duỗi chân. Chấm điểm động tác. | `shared/results/rehabilitation.json` |
| **5. Cử chỉ tay (Gesture)** | `modules/gesture/` | Nhận diện cử chỉ MediaPipe: 4 ngón (Mở trợ lý giọng nói), 2 ngón (Mở trò chơi trí nhớ), Nắm tay (Xem kế hoạch), Ngón cái (Xác nhận). | `shared/results/gesture.json` |
| **6. Giọng nói (Voice)** | `modules/voice/` | Nhận diện giọng nói tiếng Việt offline (Vosk STT) & Đọc tiếng Việt (pyttsx3 TTS). Xử lý khẩu lệnh khẩn cấp (`EMERGENCY_VOICE`). | `shared/results/voice.json` |
| **7. Quản lý Thuốc (Medication)** | `modules/medication/` | Quản lý danh mục thuốc, lịch uống thuốc hàng ngày, xác nhận uống thuốc qua Camera kèm ảnh chụp bằng chứng, cảnh báo bỏ lỡ liều. | `shared/data/medication.json`, `shared/results/medication.json` |
| **8. Trí nhớ & Định vị (Memory)** | `modules/memory/` | Quản lý kế hoạch hoạt động, tìm kiếm vị trí đồ vật thường dùng (kính, điện thoại, chìa khóa, sổ khám), trò chơi trí nhớ (Sequence Recall, Memory Matrix). | `shared/data/plans.json`, `shared/data/objects.json`, `shared/results/memory.json` |

---

## 3. Cấu trúc Thư mục

```text
AI_for_older/
│
├── main.py                  # Điểm khởi chạy chính của Dashboard PyQt5
├── demo.py                  # Script chạy demo tổng thể tự động hoặc từng bước (Phase 13)
├── config.py                # Cấu hình ngưỡng thời gian, camera index, email SMTP, đường dẫn
├── requirements.txt         # Danh mục thư viện Python bắt buộc
├── README.md                # Tài liệu hướng dẫn sử dụng và kiến trúc
├── .env.example             # Mẫu cấu hình biến môi trường (SMTP credentials)
│
├── app/                     # Ứng dụng giao diện PyQt5
│   ├── dashboard.py         # Cửa sổ Dashboard chính, bảng giám sát, dialog bài tập, thuốc, trí nhớ
│   ├── router.py            # Bộ điều phối nghiệp vụ giữa giao diện và các dịch vụ AI
│   ├── launcher.py          # Khởi động và giám sát tiến trình con, camera arbitrator
│   └── state.py             # Đồng bộ trạng thái giao diện định kỳ
│
├── adapters/                # Các adapter mỏng giao tiếp với 8 modules
│   ├── face_adapter.py
│   ├── emotion_adapter.py
│   ├── fall_adapter.py
│   ├── rehabilitation_adapter.py
│   ├── gesture_adapter.py
│   ├── voice_adapter.py
│   ├── medication_adapter.py
│   └── memory_adapter.py
│
├── services/                # Các dịch vụ cốt lõi
│   ├── alert_service.py     # Quản lý, phân loại mức độ và lưu trữ cảnh báo an toàn
│   ├── medication_service.py# Kiểm tra lịch thuốc, xác nhận camera, kích hoạt cảnh báo
│   ├── memory_service.py    # Tìm vị trí đồ vật, logic trò chơi trí nhớ, kế hoạch
│   ├── report_service.py    # Tổng hợp dữ liệu ngày và xuất báo cáo JSON & Markdown
│   ├── email_service.py     # Gửi cảnh báo té ngã, nhắc thuốc và báo cáo qua SMTP
│   └── state_service.py     # Quản lý file trạng thái tổng thể shared/state.json
│
├── shared/                  # Thư mục dữ liệu trao đổi giữa các phân hệ
│   ├── data/                # Dữ liệu tĩnh/nghiệp vụ (bệnh nhân, thuốc, kế hoạch, đồ vật)
│   ├── results/             # Kết quả phân tích mới nhất của các module AI
│   ├── alerts/              # Nhật ký cảnh báo an toàn (alerts.json)
│   ├── recordings/          # Video sự kiện té ngã và ảnh bằng chứng uống thuốc
│   └── reports/             # Báo cáo sức khỏe hàng ngày (JSON + Markdown)
│
├── tests/                   # Bộ kiểm thử tích hợp tự động (73 tests)
│   ├── test_adapters.py
│   ├── test_alert.py
│   ├── test_launcher.py
│   ├── test_phase6_integration.py
│   ├── test_phase7_rehabilitation.py
│   ├── test_phase8_voice_gesture.py
│   ├── test_phase9_medication.py
│   ├── test_phase10_memory.py
│   ├── test_phase11_12_alerts_report.py
│   ├── test_phase13_demo.py
│   ├── test_report.py
│   └── test_state.py
│
└── modules/                 # 8 repository AI gốc (giữ nguyên độc lập)
    ├── face/
    ├── emotion/
    ├── fall/
    ├── gesture/
    ├── medication/
    ├── memory/
    ├── rehabilitation/
    └── voice/
```

---

## 4. Hướng dẫn Cài đặt & Chuẩn bị Môi trường

### 4.1. Yêu cầu hệ thống
- Hệ điều hành: Linux (Ubuntu 20.04/22.04/24.04), Windows 10/11 hoặc macOS.
- Python: Phiên bản **3.10**, **3.11** hoặc **3.12**.
- Thiết bị ngoại vi: Webcam/USB Camera, Microphone & Loa.

### 4.2. Cài đặt môi trường ảo
```bash
# Di chuyển vào thư mục dự án
cd AI_for_older

# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate   # Linux/macOS
# hoặc: .venv\Scripts\activate  # Windows

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt
```

### 4.3. Cấu hình biến môi trường (Tùy chọn)
Sao chép `.env.example` thành `.env` để cấu hình gửi Email qua SMTP:
```bash
cp .env.example .env
```
Nội dung `.env`:
```ini
EMAIL_ENABLED=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
CAREGIVER_EMAIL=relative_email@gmail.com
```
*(Nếu chưa cấu hình Email, hệ thống vẫn hoạt động bình thường và ghi nhận lịch sử vào `shared/reports/` và `shared/alerts/` mà không bị gián đoạn).*

---

## 5. Hướng dẫn Chạy Hệ thống & Demo

### 5.1. Khởi động Giao diện Điều khiển Chính (PyQt5 GUI)
```bash
python main.py
```
Giao diện hiển thị:
- **Cột trái:** Thông tin bệnh nhân, Trạng thái cảm xúc thời gian thực, Đồng hồ thời gian tư thế Đứng/Ngồi/Nằm, Trạng thái kết nối Camera.
- **Khu vực trung tâm:** Các nút thao tác lớn theo 4 nhóm:
  1. *Giám sát sức khỏe:* Bắt đầu giám sát, Nhận diện khuôn mặt, Giả lập té ngã.
  2. *Phục hồi chức năng:* Chọn 5 bài tập (Vươn vai, Vỗ tay, Đi bộ, Xoay cổ, Co duỗi chân).
  3. *Hỗ trợ trí nhớ:* Xem kế hoạch, Tìm vị trí đồ vật, Trò chơi chuỗi trí nhớ & Ma trận ô nhớ.
  4. *Thuốc & Báo cáo:* Quản lý đơn thuốc, Xác nhận qua Camera, Xem nhật ký cảnh báo, Xuất & gửi báo cáo ngày.

### 5.2. Chạy Demo Tự động End-to-End Walkthrough (Khuyên dùng khi báo cáo)
```bash
python demo.py
```
Script sẽ tự động chạy toàn bộ 8 kịch bản mô phỏng từ Đăng ký, Nhận diện, Giám sát, Bài tập, Cử chỉ, Giọng nói, Uống thuốc, Trò chơi trí nhớ, đến Xuất báo cáo tổng kết với giao diện dòng lệnh màu sắc rõ ràng.

### 5.3. Chạy Demo Từng bước Tương tác
```bash
python demo.py --step
```
Dừng lại sau mỗi phân hệ để người thuyết trình giải thích kịch bản trước khi chuyển bước.

### 5.4. Chạy Demo và Mở Giao diện GUI ngay sau đó
```bash
python demo.py --gui
```

### 5.5. Chạy Toàn bộ Bộ Kiểm thử Tự động (73 Unit/Integration Tests)
```bash
AI_CARE_DISABLE_TTS=1 python -m unittest discover tests
```
Tất cả 73 bài kiểm tra sẽ hoàn thành trong khoảng 4–5 giây với kết quả `100% OK`.

---

## 6. Tiêu chí Nghiệm thu MVP (Acceptance Criteria)

- [x] **Dashboard:** Giao diện PyQt5 mở ổn định, hỗ trợ tiếng Việt, không bị crash khi tiến trình con gặp lỗi.
- [x] **Face:** Đăng ký thành công hồ sơ bệnh nhân, nhận diện chính xác danh tính.
- [x] **Emotion:** Phân loại cảm xúc và cập nhật liên tục vào `shared/results/emotion.json`.
- [x] **Pose & Fall:** Đếm thời gian ngồi/nằm/đứng, cảnh báo ngồi quá lâu, phát hiện té ngã và lưu file bằng chứng.
- [x] **Rehabilitation:** Giám sát 5 bài tập vật lý trị liệu, đếm repetition, chấm điểm phần trăm thực hiện đúng.
- [x] **Gesture:** Nhận diện 4 cử chỉ tay điều khiển hệ thống qua MediaPipe.
- [x] **Voice:** Tương tác giọng nói tiếng Việt offline qua Vosk STT và pyttsx3 TTS; cảnh báo khẩn cấp khi người dùng kêu cứu.
- [x] **Medication:** Lập lịch uống thuốc, chụp ảnh camera xác nhận liều uống, phát hiện và gửi cảnh báo khi quên thuốc.
- [x] **Memory:** Lưu trữ vị trí đồ vật, quản lý kế hoạch hàng ngày, 2 minigame rèn luyện trí nhớ.
- [x] **Alerts & Reports:** Tổng hợp đầy đủ mọi chỉ số trong ngày thành file JSON và Markdown; sẵn sàng gửi email người thân.
  