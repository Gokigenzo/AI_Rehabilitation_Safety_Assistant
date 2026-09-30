# AI_FOR_OLDER — MVP Integration & UI Execution Guide

## 0. Mục tiêu

Xây dựng **MVP có thể chạy và demo được trong thời gian ngắn** cho đề tài:

> Hệ Thống AI phân tích đánh giá và hỗ trợ qua giám sát cho người phục hồi chức năng bệnh.

Repository hiện tại đã có các module độc lập:

```text
AI_for_older/
└── modules/
    ├── emotion/
    ├── face/
    ├── fall/
    ├── gesture/
    ├── medication/
    ├── memory/
    ├── rehabilitation/
    └── voice/
```

### Nguyên tắc quan trọng

1. **Không refactor lớn** source code của các repo hiện có.
2. Không viết lại model/pipeline nếu module đã chạy được.
3. Mỗi module được coi như một **black box**.
4. Chỉ tạo lớp adapter/launcher mỏng để:
   - khởi động module;
   - truyền input cần thiết;
   - lấy kết quả;
   - lưu kết quả vào thư mục dùng chung.
5. Ưu tiên:
   **chạy được → tích hợp được → giao diện demo được → mới tối ưu**.
6. Không cố biến tất cả module thành một architecture thống nhất.
7. Nếu một module có UI riêng, giữ UI đó nếu việc tích hợp sâu không cần thiết.
8. Module nào có dependency xung đột thì được phép dùng virtual environment riêng.
9. Không làm microservice, Docker, message queue hoặc database phức tạp cho MVP nếu chưa cần.
10. Mọi thay đổi phải tối thiểu và dễ rollback.

---

# 1. Phạm vi chức năng bắt buộc

Hệ thống MVP phải thể hiện được các nhóm chức năng chính của báo cáo:

### A. Giám sát sức khỏe

- Nhận diện người dùng.
- Nhận diện cảm xúc.
- Nhận diện tư thế:
  - đứng;
  - ngồi;
  - nằm.
- Theo dõi thời gian ngồi/nằm.
- Cảnh báo khi thời gian vượt ngưỡng.
- Phát hiện dấu hiệu choáng/nguy cơ ngã.
- Ghi video khi phát hiện sự kiện nguy hiểm.
- Cảnh báo người nhà qua email.

### B. Phục hồi chức năng

Hỗ trợ/giám sát các bài tập:

- vỗ tay;
- đi bộ tại chỗ;
- vươn vai;
- xoay cổ;
- co duỗi chân.

Cần hiển thị tối thiểu:

- tên bài tập;
- số lần thực hiện;
- số lần đúng/sai nếu module hỗ trợ;
- điểm;
- trạng thái bài tập.

### C. Hỗ trợ trí nhớ

- Quản lý kế hoạch.
- Nhắc việc.
- Lưu vị trí đồ vật.
- Nhận diện/điều khiển bằng giọng nói.
- Điều khiển bằng cử chỉ.
- Trò chơi trí nhớ.
- Hiển thị điểm và lịch sử chơi.

### D. Nhắc uống thuốc

- Thêm thuốc.
- Tên thuốc.
- Thời gian uống.
- Nhắc bằng giọng nói.
- Mở camera xác nhận.
- Ghi nhận đã uống/chưa uống.
- Nếu chưa uống sau khoảng thời gian cấu hình:
  - nhắc lại;
  - ghi cảnh báo;
  - gửi email người nhà.
- Lưu lịch sử uống thuốc.

### E. Báo cáo

Cuối ngày cần tổng hợp:

- thời gian đứng/ngồi/nằm;
- cảm xúc;
- hoạt động/phục hồi chức năng;
- thuốc;
- cảnh báo;
- hoạt động trí nhớ.

Sau đó tạo báo cáo và có khả năng gửi email người nhà.

---

# 2. Kiến trúc MVP

Không ghép code các repo thành một codebase duy nhất.

Dùng kiến trúc:

```text
                         ┌───────────────────────┐
                         │      main.py          │
                         │   PyQt5 Dashboard     │
                         └───────────┬───────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
      Face Module              Health Monitor             Rehab Module
      modules/face/            emotion + pose             modules/
                                + fall                     rehabilitation/
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │    Shared Data      │
                          │ JSON + recordings   │
                          └──────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
      Medication                  Voice                     Memory
      modules/                    modules/                  modules/
      medication/                 voice/                    memory/
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                              Report / Alerts
```

---

# 3. Cấu trúc thư mục cần tạo

Không di chuyển các repo hiện tại.

Tạo thêm:

```text
AI_for_older/
│
├── main.py
├── config.py
├── README.md
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── launcher.py
│   ├── state.py
│   └── router.py
│
├── adapters/
│   ├── __init__.py
│   ├── face_adapter.py
│   ├── emotion_adapter.py
│   ├── fall_adapter.py
│   ├── gesture_adapter.py
│   ├── medication_adapter.py
│   ├── memory_adapter.py
│   ├── rehabilitation_adapter.py
│   └── voice_adapter.py
│
├── shared/
│   ├── data/
│   │   ├── patient.json
│   │   ├── medication.json
│   │   ├── plans.json
│   │   └── objects.json
│   │
│   ├── results/
│   │   ├── face.json
│   │   ├── emotion.json
│   │   ├── pose.json
│   │   ├── fall.json
│   │   ├── rehabilitation.json
│   │   ├── medication.json
│   │   ├── voice.json
│   │   ├── gesture.json
│   │   └── memory.json
│   │
│   ├── alerts/
│   │   └── alerts.json
│   │
│   ├── recordings/
│   │   └── ...
│   │
│   └── reports/
│       └── ...
│
├── services/
│   ├── report_service.py
│   ├── alert_service.py
│   ├── email_service.py
│   ├── medication_service.py
│   └── state_service.py
│
├── tests/
│
└── modules/
    ├── emotion/
    ├── face/
    ├── fall/
    ├── gesture/
    ├── medication/
    ├── memory/
    ├── rehabilitation/
    └── voice/
```

---

# 4. Quy tắc đối với các repo trong `modules/`

Agent phải coi:

```text
modules/face/
modules/emotion/
modules/fall/
...
```

là **third-party/local modules**.

### Không được tự ý:

- đổi architecture;
- đổi model;
- đổi dataset;
- viết lại training pipeline;
- đổi thuật toán chính;
- chuyển framework;
- xóa code cũ;
- gộp source code giữa các repo.

### Chỉ được sửa khi cần:

- entry point;
- đường dẫn file;
- camera index;
- output path;
- import path;
- tham số inference;
- thêm một hàm `run()`/CLI wrapper;
- xuất kết quả ra JSON;
- sửa lỗi runtime bắt buộc để module chạy.

Nếu cần thay đổi lớn, ưu tiên tạo:

```text
adapters/<module>_adapter.py
```

thay vì sửa sâu repo gốc.

---

# 5. Adapter pattern

Mỗi module phải có một adapter rất mỏng.

Ví dụ:

```python
class FaceAdapter:
    def start(self):
        ...

    def stop(self):
        ...

    def get_result(self):
        ...
```

Hoặc nếu module chỉ chạy bằng script:

```python
import subprocess


def launch_face():
    return subprocess.Popen(
        ["python", "main.py"],
        cwd="modules/face",
    )
```

Không ép tất cả module phải có cùng API nếu việc đó khiến phải refactor repo.

---

# 6. Cơ chế giao tiếp giữa các module

MVP sử dụng file JSON.

Không cần database chung.

Ví dụ:

```text
shared/results/rehabilitation.json
```

```json
{
  "patient_id": "patient_001",
  "exercise": "sit_to_stand",
  "repetitions": 12,
  "correct": 10,
  "incorrect": 2,
  "score": 83.3,
  "timestamp": "2026-09-29T20:30:00"
}
```

Fall:

```json
{
  "patient_id": "patient_001",
  "event": "fall",
  "confidence": 0.94,
  "timestamp": "2026-09-29T20:35:00",
  "video": "shared/recordings/fall_001.mp4"
}
```

Medication:

```json
{
  "patient_id": "patient_001",
  "medicine": "Medicine A",
  "scheduled_time": "20:00",
  "status": "taken",
  "timestamp": "2026-09-29T20:02:10"
}
```

Dashboard chỉ đọc các file này.

---

# 7. Shared State

Tạo một `shared/state.json`:

```json
{
  "patient_id": "patient_001",
  "name": "",
  "current_emotion": "",
  "current_pose": "",
  "sitting_seconds": 0,
  "lying_seconds": 0,
  "fall_risk": false,
  "medication_status": "",
  "last_update": ""
}
```

Nếu module có kết quả realtime, adapter cập nhật state.

Dashboard đọc state theo chu kỳ.

Không cần realtime event bus cho MVP.

---

# 8. Dashboard chính

Sử dụng **PyQt5** để bám sát báo cáo.

Giao diện cần đơn giản, chữ lớn, dễ thao tác.

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│              AI CARE & REHABILITATION SYSTEM                 │
│                  Hệ thống hỗ trợ người dùng                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  👤 NGƯỜI DÙNG                                               │
│  Tên: Nguyễn Văn A                                           │
│  Trạng thái: Đang được giám sát                              │
│                                                              │
├──────────────────────┬───────────────────────────────────────┤
│  GIÁM SÁT            │  TRÍ NHỚ & TƯƠNG TÁC                  │
│                      │                                       │
│ [Nhận diện]          │ [Trợ lý giọng nói]                    │
│ [Cảm xúc]            │ [Cử chỉ tay]                          │
│ [Tư thế]             │ [Kế hoạch]                             │
│ [Nguy cơ ngã]        │ [Định vị đồ vật]                       │
│ [Camera giám sát]    │ [Trò chơi trí nhớ]                     │
│                      │                                       │
├──────────────────────┼───────────────────────────────────────┤
│  PHỤC HỒI            │  THUỐC & BÁO CÁO                      │
│                      │                                       │
│ [Bài tập]            │ [Quản lý thuốc]                       │
│ [Vỗ tay]             │ [Lịch uống thuốc]                     │
│ [Đi bộ tại chỗ]      │ [Lịch sử uống thuốc]                  │
│ [Vươn vai]           │ [Cảnh báo]                             │
│ [Xoay cổ]            │ [Báo cáo cuối ngày]                   │
│ [Co duỗi chân]       │                                       │
│                      │                                       │
└──────────────────────┴───────────────────────────────────────┘
```

---

# 9. Dashboard — màn hình chính

Hiển thị realtime:

```text
Người dùng: Nguyễn Văn A

Emotion:
😊 Bình thường

Pose:
🪑 Ngồi

Thời gian ngồi:
01:23:14

Thời gian nằm:
00:35:21

Fall Risk:
🟢 Bình thường

Medication:
🟢 Đã uống thuốc 20:00

Exercise:
12 lần

Alerts:
0
```

Không tự động đưa ra chẩn đoán y khoa.

Chỉ hiển thị trạng thái/cảnh báo theo logic của hệ thống.

---

# 10. Module Face

Kết nối:

```text
Dashboard
   ↓
Face Adapter
   ↓
modules/face/
```

Chức năng:

- đăng ký khuôn mặt;
- nhận diện người dùng;
- hiển thị tên;
- Unknown nếu không nhận diện được.

Có màn hình:

```text
┌──────────────────────────────┐
│ ĐĂNG KÝ NGƯỜI DÙNG           │
├──────────────────────────────┤
│ Tên: [________________]      │
│                              │
│        CAMERA                │
│                              │
│ [Chụp ảnh] [Đăng ký]         │
└──────────────────────────────┘
```

Không thay đổi thuật toán face recognition của repo nếu không cần.

---

# 11. Module Emotion

Màn hình:

```text
┌──────────────────────────────┐
│ GIÁM SÁT CẢM XÚC             │
├──────────────────────────────┤
│                              │
│        CAMERA                │
│                              │
│ Cảm xúc hiện tại:            │
│ 😊 Bình thường               │
│                              │
│ Lịch sử cảm xúc:             │
│ ────────────────             │
│                              │
└──────────────────────────────┘
```

Lưu kết quả theo timestamp.

Mục đích của module là theo dõi trạng thái cảm xúc theo mô tả trong báo cáo, không coi kết quả là chẩn đoán tâm lý.

---

# 12. Module Pose

Cần thể hiện:

```text
Đứng
Ngồi
Nằm
```

Theo dõi:

```text
sitting_time
lying_time
standing_time
```

Logic:

```python
if pose == "sitting":
    sitting_time += delta_time

elif pose == "lying":
    lying_time += delta_time

elif pose == "standing":
    standing_time += delta_time
```

Có cấu hình:

```text
MAX_SITTING_TIME
MAX_LYING_TIME
```

Nếu vượt ngưỡng:

```text
⚠ Bạn đã ngồi quá lâu.
Hãy vận động nhẹ.
```

---

# 13. Module Fall / Dizziness

Đây là module ưu tiên cao.

Bám sát logic báo cáo:

- độ nghiêng đầu;
- cân bằng vai;
- chuyển động/trọng tâm cơ thể;
- yêu cầu dấu hiệu bất thường xuất hiện liên tục trước khi cảnh báo;
- ghi video khoảng 10 giây;
- gửi email cảnh báo;
- cảnh báo khi không phát hiện người dùng quá ngưỡng.

Nếu repo `fall` đã có logic tương ứng, giữ nguyên.

Nếu chưa có, chỉ thêm wrapper/logic nhỏ bên ngoài.

MVP event:

```text
FALL_DETECTED
NO_PERSON
DIZZINESS_RISK
```

Khi có event:

```text
Fall
 ↓
Save video
 ↓
Write alerts.json
 ↓
Email caregiver
 ↓
Dashboard notification
```

---

# 14. Module Rehabilitation

Màn hình:

```text
┌────────────────────────────────────┐
│ PHỤC HỒI CHỨC NĂNG                 │
├────────────────────────────────────┤
│ Chọn bài tập:                      │
│                                    │
│ [ Vỗ tay ]                         │
│ [ Đi bộ tại chỗ ]                  │
│ [ Vươn vai ]                       │
│ [ Xoay cổ ]                        │
│ [ Co duỗi chân ]                   │
│                                    │
│ Số lần: 12                         │
│ Đúng: 10                           │
│ Sai: 2                             │
│ Điểm: 83%                          │
│                                    │
│ [ Bắt đầu ] [ Dừng ]               │
└────────────────────────────────────┘
```

Không cần tích hợp sâu vào pose system nếu repo rehabilitation đã có pipeline riêng.

Khi kết thúc bài:

```text
rehabilitation.json
```

được cập nhật.

---

# 15. Module Gesture

Bám sát báo cáo:

- cử chỉ 4 ngón → kích hoạt nghe giọng nói;
- 2 ngón → mở trò chơi trí nhớ;
- nắm tay → nhắc kế hoạch chưa hoàn thành.

Adapter chỉ cần chuyển:

```text
Gesture
   ↓
Command
   ↓
Dashboard / Voice / Memory
```

Ví dụ:

```python
if gesture == "FOUR_FINGERS":
    launch_voice()

elif gesture == "TWO_FINGERS":
    open_memory_game()

elif gesture == "FIST":
    show_pending_plans()
```

Nếu repo gesture dùng tên class khác, tạo mapping trong adapter.

---

# 16. Module Voice

Bám sát:

```text
Speech
 ↓
Speech-to-Text
 ↓
Command / Intent
 ↓
Action
 ↓
Text-to-Speech
```

Các command MVP:

```text
"Nhắc tôi uống thuốc..."
"Thuốc của tôi là gì?"
"Tôi phải làm gì hôm nay?"
"Đồ vật ... ở đâu?"
"Mở trò chơi trí nhớ"
"Nhắc kế hoạch chưa hoàn thành"
```

Không cần xây NLP phức tạp.

Có thể dùng command matching đơn giản nếu repo voice đã có sẵn.

---

# 17. Module Memory

Tạo các màn hình:

```text
TRÍ NHỚ
├── Kế hoạch
├── Đồ vật
├── Trò chơi
└── Lịch sử
```

### Kế hoạch

```text
[Thêm kế hoạch]

Tên:
Thời gian:
Mô tả:

[Save]
```

### Định vị đồ vật

```text
Điện thoại → Bàn phòng khách
Chìa khóa  → Ngăn kéo
Kính       → Bàn cạnh giường
```

### Trò chơi

```text
[Memory Matrix]
[Family Memory]
```

Nếu repo memory đã có game, gọi trực tiếp repo.

Không cần viết lại game.

---

# 18. Module Medication

Màn hình:

```text
┌────────────────────────────────────┐
│ QUẢN LÝ THUỐC                      │
├────────────────────────────────────┤
│ Thuốc: [________________]           │
│ Giờ:   [08:00]                     │
│                                    │
│ [Thêm thuốc]                       │
│                                    │
│ Lịch hôm nay:                      │
│                                    │
│ 08:00  Medicine A   ✓              │
│ 12:00  Medicine B   ✓              │
│ 20:00  Medicine C   ?              │
└────────────────────────────────────┘
```

Đến giờ:

```text
Medication Scheduler
        ↓
Voice Reminder
        ↓
Camera Verification
        ↓
Taken / Not Taken
        ↓
History
        ↓
Alert nếu bỏ thuốc
```

Bám sát yêu cầu báo cáo về xác nhận bằng camera và gửi email nếu người dùng không uống.

---

# 19. Alert System

Tạo:

```text
services/alert_service.py
```

Các loại:

```python
FALL
DIZZINESS
NO_PERSON
MISSED_MEDICATION
LONG_SITTING
LONG_LYING
```

Mỗi alert:

```json
{
  "type": "FALL",
  "severity": "HIGH",
  "patient_id": "patient_001",
  "timestamp": "...",
  "message": "...",
  "evidence": "shared/recordings/fall_001.mp4",
  "email_sent": true
}
```

Dashboard hiển thị alert gần nhất.

---

# 20. Email

Tạo:

```text
services/email_service.py
```

Không hard-code password.

Dùng `.env`:

```text
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USERNAME=
EMAIL_PASSWORD=
CAREGIVER_EMAIL=
```

Hỗ trợ:

```text
Fall alert + video
Missed medication
Daily report
```

Nếu chưa cấu hình email:

- không crash app;
- ghi log;
- hiển thị `Email service unavailable`;
- vẫn lưu alert locally.

---

# 21. Daily Report

Tạo:

```text
services/report_service.py
```

Thu thập:

```text
Face
Emotion
Pose
Exercise
Medication
Memory
Alerts
```

Tạo báo cáo:

```text
BÁO CÁO CUỐI NGÀY

Người dùng:
Ngày:

1. Hoạt động
- Thời gian đứng:
- Thời gian ngồi:
- Thời gian nằm:

2. Cảm xúc
- Bình thường:
- Vui:
- Buồn:

3. Phục hồi chức năng
- Bài tập:
- Số lần:
- Điểm:

4. Thuốc
- Đã uống:
- Bỏ thuốc:

5. Cảnh báo
- Fall:
- Dizziness:
- No person:

6. Trí nhớ
- Kế hoạch:
- Trò chơi:
- Điểm:

7. Nhận xét/tóm tắt
```

Sau đó gửi email cho người nhà.

Nếu phần phân tích bằng API không khả dụng, vẫn phải tạo báo cáo thống kê cơ bản từ dữ liệu đã lưu.

---

# 22. Camera strategy

Đây là điểm cần ưu tiên cho MVP.

Không cố để tất cả module mở webcam cùng lúc.

Mặc định:

```text
Dashboard
   ↓
User chọn chức năng
   ↓
Chỉ module đó sử dụng camera
   ↓
Module kết thúc
   ↓
Camera release
```

Đặc biệt:

```python
cap.release()
cv2.destroyAllWindows()
```

phải được đảm bảo khi module dừng.

Nếu một module giữ camera, dashboard phải báo:

```text
Camera đang được sử dụng bởi: Fall Detection
```

Không mở thêm camera.

---

# 23. Launcher

Tạo:

```text
app/launcher.py
```

Ví dụ:

```python
import subprocess
import sys


def launch_module(module_dir, entry_point="main.py"):
    return subprocess.Popen(
        [sys.executable, entry_point],
        cwd=module_dir,
    )
```

Nếu module có environment riêng:

```python
subprocess.Popen(
    [
        "modules/fall/.venv/bin/python",
        "main.py",
    ],
    cwd="modules/fall",
)
```

Launcher phải:

- start;
- stop;
- kiểm tra process;
- không mở duplicate instance;
- xử lý module crash;
- báo lỗi dễ hiểu.

---

# 24. Không dùng database phức tạp cho MVP

Ưu tiên:

```text
JSON
CSV
local recordings
```

Chỉ dùng database nếu một module đã có sẵn database và việc bỏ nó sẽ gây lỗi.

Mục tiêu là giảm integration work.

---

# 25. Quy trình Agent phải thực hiện

Agent **không được làm tất cả một lần**.

Thực hiện theo thứ tự:

## Phase 1 — Audit

Kiểm tra từng repo:

```text
face
emotion
fall
gesture
medication
memory
rehabilitation
voice
```

Với mỗi repo ghi:

```text
entry point:
dependencies:
camera usage:
input:
output:
UI:
model:
Python version:
known errors:
```

Tạo:

```text
docs/MODULE_AUDIT.md
```

Không sửa code trong phase này.

---

## Phase 2 — Chạy độc lập

Chạy từng module.

Thứ tự:

```text
1. face
2. emotion
3. fall
4. rehabilitation
5. gesture
6. voice
7. medication
8. memory
```

Mỗi module phải đạt:

```text
RUNNING
```

trước khi tích hợp.

---

## Phase 3 — Adapter

Tạo:

```text
adapters/
```

Chỉ viết adapter cần thiết.

Không refactor repo.

---

## Phase 4 — Shared output

Tạo:

```text
shared/results/
shared/alerts/
shared/recordings/
shared/reports/
```

Chuẩn hóa output bằng JSON.

---

## Phase 5 — Dashboard

Tạo PyQt5 dashboard.

Trước tiên chỉ cần nút:

```text
Face
Emotion
Fall
Rehabilitation
Gesture
Voice
Medication
Memory
```

Mỗi nút gọi module tương ứng.

---

## Phase 6 — Integration

Kết nối:

```text
Fall → Alert
Medication → Alert
Exercise → Report
Emotion → Report
Pose → Report
Memory → Report
```

---

## Phase 7 — Demo Flow

Tạo một demo hoàn chỉnh:

```text
Start System
      ↓
Register Patient
      ↓
Start Monitoring
      ↓
Recognize Person
      ↓
Detect Emotion/Pose
      ↓
Exercise
      ↓
Medication Reminder
      ↓
Memory Interaction
      ↓
Simulate/Detect Alert
      ↓
Daily Report
      ↓
Email
```

---

# 26. MVP Acceptance Criteria

## Dashboard

- [ ] PyQt5 mở được.
- [ ] Hiển thị tên người dùng.
- [ ] Có đủ các nhóm chức năng.
- [ ] Các nút mở được module tương ứng.
- [ ] Không crash khi module không chạy.

## Face

- [ ] Registration hoạt động.
- [ ] Recognition hoạt động.
- [ ] Unknown hoạt động.

## Emotion

- [ ] Camera chạy.
- [ ] Có kết quả emotion.
- [ ] Lưu timestamp.

## Pose

- [ ] Standing.
- [ ] Sitting.
- [ ] Lying.
- [ ] Có timer.

## Fall

- [ ] Có kết quả nguy cơ.
- [ ] Có alert.
- [ ] Có recording.
- [ ] Có email nếu cấu hình.

## Rehabilitation

- [ ] Chọn bài tập.
- [ ] Camera chạy.
- [ ] Đếm repetition.
- [ ] Có score/result.

## Gesture

- [ ] Detect gesture.
- [ ] Gesture → action.

## Voice

- [ ] Speech-to-text.
- [ ] Command.
- [ ] TTS.

## Memory

- [ ] Plan.
- [ ] Object location.
- [ ] Memory game.
- [ ] Score/history.

## Medication

- [ ] Add medicine.
- [ ] Schedule.
- [ ] Reminder.
- [ ] Verification.
- [ ] History.
- [ ] Missed medication alert.

## Report

- [ ] Generate daily report.
- [ ] Save report.
- [ ] Email report.

---

# 27. Error handling

Không để lỗi một module làm chết toàn hệ thống.

Ví dụ:

```text
Fall module crash
      ↓
Dashboard vẫn chạy
      ↓
Hiển thị:
"Fall module unavailable"
```

Tương tự:

```text
Voice unavailable
Memory vẫn chạy.
```

Mọi lỗi cần ghi vào:

```text
logs/
└── app.log
```

Dùng `logging`, không dùng `print()` cho logic chính.

---

# 28. Config

Tạo:

```text
config.py
```

Quản lý:

```python
CAMERA_INDEX = 0

MAX_SITTING_MINUTES = 60
MAX_LYING_MINUTES = 120

FALL_RECORD_SECONDS = 10
NO_PERSON_TIMEOUT = 300

MEDICATION_GRACE_PERIOD = 300

EMAIL_ENABLED = False
```

Không hard-code các giá trị này trong adapter.

---

# 29. .env

Tạo:

```text
.env
```

Ví dụ:

```text
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
CAREGIVER_EMAIL=

OPENAI_API_KEY=
```

Thêm:

```text
.env
```

vào `.gitignore`.

---

# 30. Testing

MVP không cần test toàn bộ repo.

Chỉ test integration code mới:

```text
tests/
├── test_launcher.py
├── test_state.py
├── test_alert.py
├── test_report.py
└── test_adapters.py
```

Test tối thiểu:

```text
JSON có ghi được không?
Adapter có start được không?
Alert có được tạo không?
Report có tạo được không?
Launcher có xử lý process không?
```

Không viết lại unit test cho source code của repo bên ngoài.

---

# 31. Quy tắc bảo toàn repo gốc

Mỗi module nên có:

```text
modules/fall/
├── ORIGINAL_REPO_CODE
└── ...
```

Nếu cần chỉnh sửa:

1. Git commit trước.
2. Sửa tối thiểu.
3. Test.
4. Nếu lỗi → revert.

Không xóa lịch sử repo.

---

# 32. Ưu tiên tính năng khi thiếu thời gian

Nếu deadline rất gần:

### Priority 1

```text
Face
Pose
Fall
Rehabilitation
Medication
Dashboard
```

### Priority 2

```text
Emotion
Voice
Gesture
```

### Priority 3

```text
Memory
Daily report nâng cao
```

Tuy nhiên dashboard vẫn phải có đầy đủ menu/chức năng để thể hiện phạm vi hệ thống.

---

# 33. Không được làm trong MVP

Không triển khai nếu không bắt buộc:

- Microservices.
- Docker.
- Kubernetes.
- Redis.
- Kafka.
- REST API giữa mọi module.
- Database server.
- Cloud deployment phức tạp.
- Rewrite toàn bộ model.
- Unified ML framework.
- Training lại tất cả model.
- Mobile app.
- Wearables.
- Long-term analytics tuần/tháng.
- Nutrition recommendation.

Đây là các hướng phát triển, không phải yêu cầu MVP cốt lõi.

---

# 34. Definition of Done

Project được coi là hoàn thành MVP khi:

```text
[✓] Dashboard mở được
[✓] Người dùng có thể chọn từng chức năng
[✓] Các repo hiện tại vẫn chạy được
[✓] Camera không bị tranh chấp nghiêm trọng
[✓] Face recognition chạy
[✓] Emotion chạy
[✓] Pose chạy
[✓] Fall detection chạy
[✓] Rehab chạy
[✓] Voice chạy
[✓] Gesture chạy
[✓] Medication chạy
[✓] Memory chạy
[✓] Alert hoạt động
[✓] Result được lưu
[✓] Daily report tạo được
[✓] Email có thể gửi khi cấu hình
[✓] Một module lỗi không làm crash dashboard
```

---

# 35. Prompt/Rule cho Agent

Agent phải tuân thủ:

> You are integrating an existing MVP from multiple independent repositories.
>
> Do NOT rewrite or refactor the existing modules unless absolutely necessary.
>
> Treat every directory under `modules/` as an independent black-box application.
>
> First audit each module, then run it independently, then create a minimal adapter.
>
> Prefer subprocess launching over deep source-code integration when possible.
>
> Prefer JSON files for cross-module communication.
>
> Use PyQt5 for the main application dashboard to match the project report.
>
> Preserve existing model pipelines and dependencies.
>
> Do not replace working implementations with new implementations.
>
> Do not introduce microservices, Docker, message queues, or complex databases unless explicitly required.
>
> If dependencies conflict, allow module-specific virtual environments.
>
> Never let one module failure crash the main dashboard.
>
> Every new integration change must be small, reversible, and tested.
>
> Prioritize MVP functionality and demo reliability over architectural elegance.
>
> Follow the feature requirements in this document and the project report.

---

# 36. Final implementation philosophy

Đây **không phải** production system.

Mục tiêu là:

```text
                 EXISTING REPOS
                      │
                      ▼
                   ADAPTER
                      │
                      ▼
                  DASHBOARD
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        RESULT      ALERT       REPORT
```

Càng ít sửa code gốc càng tốt.

**Nguyên tắc cuối cùng:**

> Nếu một chức năng đã chạy được trong repo gốc, hãy gọi nó — đừng viết lại nó.
>
> Nếu hai module không cần trao đổi dữ liệu trực tiếp, không ép chúng phải tích hợp sâu.
>
> Nếu có thể giải quyết bằng một adapter 30 dòng, không refactor 300 dòng.
>
> MVP trước, architecture sau.
