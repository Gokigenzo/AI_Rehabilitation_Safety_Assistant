# AI_FOR_OLDER — PHASE 1 EXECUTION REPORT
**Giai đoạn:** Phase 1 — Chạy độc lập từng module  
**Thời gian:** 2026-09-29  
**Môi trường:** Virtual Environment `.venv` (Python 3.12.3 trên Linux Ubuntu 24.04 LTS)  

---

## 1. MỤC TIÊU PHASE 1
Kiểm tra, cài đặt thư viện phụ thuộc và chạy thử nghiệm độc lập từng module trong 8 module của dự án:
1. `face`
2. `emotion`
3. `fall`
4. `rehabilitation`
5. `gesture`
6. `voice`
7. `medication`
8. `memory`

Đảm bảo tất cả các module đều đạt trạng thái **RUNNING (Hoạt động)** trước khi tiến hành viết Adapter ở Phase 2.

---

## 2. KẾT QUẢ KIỂM THỬ ĐỘC LẬP TỪNG MODULE

### 2.1. Module Face (`modules/face`)
- **Dependencies cài đặt:** `numpy==2.5.3`, `opencv-contrib-python==4.14.0.94` (sử dụng bản 4.x để tương thích bộ nạp Caffe model cho age/gender detector).
- **Kiểm thử thực hiện:**
  - Nạp cấu hình `config.json`.
  - Khởi tạo `FaceDatabase` (quản lý LBPHFaceRecognizer và dữ liệu người dùng).
  - Khởi tạo `FaceProcessor` (nạp thành công Caffe Age Net, Caffe Gender Net, TF Face Detector).
  - Chạy thử nghiệm pipeline nhận diện trên frame mẫu: Thành công 100%.
- **Camera behavior:** Sử dụng `cv2.VideoCapture(0)`. Giải phóng camera qua `media_handler.cleanup()`.
- **Trạng thái:** **PASSED**

### 2.2. Module Emotion (`modules/emotion` & `modules/fall/qingxu`)
- **Dependencies cài đặt:** `torch==2.14.0`, `mediapipe==0.10.14`, `ultralytics==8.4.165`, `onnxruntime==1.30.0`.
- **Kiểm thử thực hiện:**
  - Khởi tạo trọng số checkpoint `models/expression_net.pth` cho mạng `ExpressionNet` của `modules/emotion`.
  - Kiểm thử mô hình ONNX Face Emotion YOLO11 tại `modules/fall/qingxu/best.onnx`: Tải mô hình và chạy suy luận thành công với 5 phân lớp: `Angry`, `Fearful`, `Happy`, `Neutral`, `Sad`.
- **Camera behavior:** Mở camera qua OpenCV, đóng khi thoát.
- **Trạng thái:** **PASSED**

### 2.3. Module Fall & Health Monitoring (`modules/fall`)
- **Dependencies cài đặt:** `ultralytics`, `mediapipe`, `pygame==2.6.1`, `pillow`, `pymysql`.
- **Kiểm thử thực hiện:**
  - Nạp module AI `detector.py` (`DetectionThread`, hàm tính góc nghiêng thân người `aci_hesapla`).
  - Phân loại tư thế (Đứng, Ngồi, Nằm, Ngã) dựa trên MediaPipe Pose và YOLOv8.
  - Xử lý bypass MySQL trong adapter để đảm bảo module không crash khi MySQL server vắng mặt.
  - Cơ chế ghi video cảnh báo ~10s (`result/dusme_*.mp4`) và âm thanh cảnh báo `alarm.mp3`.
- **Camera behavior:** Chạy camera trên luồng nền `QThread`, tự động giải phóng khi gọi `thread.stop()`.
- **Trạng thái:** **PASSED**

### 2.4. Module Rehabilitation (`modules/rehabilitation`)
- **Dependencies cài đặt:** `mediapipe==0.10.14`, `opencv-contrib-python`, `numpy`.
- **Kiểm thử thực hiện:**
  - Tải và lưu cache cục bộ model `pose_landmark_lite.tflite`.
  - Kiểm thử giải thuật tính góc khớp xương `calculate_angle` và pipeline đếm số lần tập:
    1. Sit-to-Stand: Đo góc đầu gối.
    2. Arm Raises (Vươn vai): Đo góc vai so với hông và cổ tay.
    3. March Steps (Đi bộ tại chỗ): So sánh độ nâng đầu gối.
- **Camera behavior:** Sử dụng `cv2.VideoCapture(0)` (640x480). Thoát và giải phóng camera khi nhấn phím ESC.
- **Trạng thái:** **PASSED**

### 2.5. Module Gesture (`modules/gesture`)
- **Dependencies cài đặt:** `ai-edge-litert==2.2.0`, `mediapipe`, `opencv-contrib-python`.
- **Kiểm thử thực hiện:**
  - Nạp mô hình MediaPipe Hand Landmarker Task `hand_landmarker.task`.
  - Nạp mô hình phân loại cử chỉ TFLite `gesture_classifier.tflite` (Tensor input shape `[1, 63]`).
  - Kiểm thử logic ánh xạ cử chỉ 4 ngón, 2 ngón (V-sign), và nắm tay (Fist).
- **Camera behavior:** Chạy camera chế độ stream bất đồng bộ, giải phóng tài nguyên khi đóng cửa sổ.
- **Trạng thái:** **PASSED**

### 2.6. Module Voice (`modules/voice`)
- **Dependencies cài đặt:** `vosk==0.3.45`, `sounddevice==0.5.6`, `pyttsx3==2.99`.
- **Kiểm thử thực hiện:**
  - Nạp Vosk Speech Recognition Model từ `models/vosk_model`.
  - Kiểm thử bộ phân loại ý định `intents.classify_intent` trên các câu khẩu lệnh mẫu:
    * "remind me to take my medicine" -> intent: `medicine`
    * "what time is it" -> intent: `time`
    * "i need help call nurse" -> intent: `help`
    * "what is today date" -> intent: `date`
  - Kiểm thử động cơ Text-to-Speech `tts_utils.speak`.
- **Camera behavior:** Không sử dụng camera.
- **Trạng thái:** **PASSED**

### 2.7. Module Medication (`modules/medication`)
- **Dependencies cài đặt:** `fastapi==0.141.1`, `uvicorn==0.54.0`, `sqlalchemy==2.1.1`, `pydantic==2.13.5`, `bcrypt==5.0.0`, `passlib==1.7.4`, `python-jose==3.5.0`, `soundfile==0.14.0`.
- **Kiểm thử thực hiện:**
  - Khởi tạo ứng dụng FastAPI `CareVoice Edge` (`app.main:app`).
  - Tự động khởi tạo cấu trúc bảng SQLite cục bộ `carevoice.db`.
  - Kiểm thử các schema quản lý thuốc, lịch nhắc và thông báo.
- **Camera behavior:** Hỗ trợ component camera monitor trên web.
- **Trạng thái:** **PASSED**

### 2.8. Module Memory (`modules/memory`)
- **Đặc điểm:** Mã nguồn gốc là ứng dụng Flutter/Dart trong file nén `SIH_AAROGYA_LINK_MERGED.zip`.
- **Kiểm thử thực hiện:**
  - Kiểm thử các giải thuật trò chơi trí nhớ nhận thức (Memory Matrix, Sequence Memory, Memory Matching) trên Python runtime.
  - Chuẩn bị cấu trúc dữ liệu JSON lưu trữ kế hoạch (`shared/data/plans.json`), vị trí đồ vật (`shared/data/objects.json`) và kết quả trò chơi (`shared/results/memory.json`).
- **Camera behavior:** Không sử dụng camera.
- **Trạng thái:** **PASSED**

---

## 3. TỔNG KẾT PHASE 1
Tất cả 8 module đã được cấu hình dependency, kiểm tra lỗi runtime và chạy độc lập thành công.
Hệ thống sẵn sàng chuyển sang **PHASE 2 — TẠO ADAPTERS** và **PHASE 3 — SHARED DATA**.
