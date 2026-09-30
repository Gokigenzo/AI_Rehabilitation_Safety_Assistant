# AI_FOR_OLDER — MODULE AUDIT REPORT
**Giai đoạn:** Phase 0 — Audit & System Assessment  
**Thời gian:** 2026-09-29  
**Người thực hiện:** Senior AI/Software Engineer  

---

## 1. TỔNG QUAN HỆ THỐNG HIỆN TẠI

Hệ thống `AI_for_older` bao gồm 8 module độc lập nằm trong thư mục `modules/`:
1. `modules/face` — Hệ thống nhận diện khuôn mặt, tuổi, giới tính, quản lý database khuôn mặt và người lạ.
2. `modules/emotion` — Nhận diện cảm xúc dựa trên MediaPipe FaceMesh và mạng nơ-ron PyTorch.
3. `modules/fall` — Giám sát ngã, tư thế (đứng, ngồi, nằm) tích hợp YOLOv8 + MediaPipe, kèm module cảm xúc YOLO11 ONNX (`qingxu`).
4. `modules/gesture` — Nhận diện cử chỉ tay (MediaPipe Tasks + TFLite).
5. `modules/medication` — Quản lý lịch uống thuốc, nhắc việc, voice engine, FastAPI backend và React frontend.
6. `modules/memory` — Nền tảng trò chơi nhận thức và hỗ trợ trí nhớ (mã nguồn Flutter/Dart trong file nén).
7. `modules/rehabilitation` — Giám sát phục hồi chức năng và đếm số lần tập (Sit-to-stand, Arm raises, March steps) bằng MediaPipe Pose.
8. `modules/voice` — Trợ lý giọng nói ngoại tuyến cho người cao tuổi sử dụng Vosk ASR + pyttsx3 TTS + Tkinter GUI.

Môi trường host:
- Hệ điều hành: Linux (Ubuntu 24.04 LTS / x86_64)
- Python hệ thống: Python 3.12.3
- Trạng thái thư viện hiện tại: Chưa cài đặt các gói AI/Computer Vision (PyQt5/PyQt6, OpenCV, MediaPipe, PyTorch, Ultralytics, Vosk...) trong môi trường hệ thống. Cần tạo môi trường ảo (venv) cho quá trình chạy và tích hợp ở Phase 1.

---

## 2. AUDIT CHI TIẾT TỪNG MODULE

### 2.1. Module Face (`modules/face`)

- **Thư mục:** `modules/face/`
- **Entry Point:** `main.py`
- **Cách chạy:**
  ```bash
  python main.py --input 0          # Chạy camera trực tiếp
  python main.py --database         # Quản lý cơ sở dữ liệu khuôn mặt
  python main.py --review-unknown   # Đánh giá khuôn mặt chưa xác định
  ```
- **Python version:** Python 3.8+ (tương thích Python 3.12).
- **Dependencies:** `numpy==2.4.3`, `opencv-contrib-python==4.13.0.92` (yêu cầu `opencv-contrib` vì sử dụng `cv2.face.LBPHFaceRecognizer`).
- **Model:**
  - Face Detection: `models/opencv_face_detector.pbtxt` và `models/opencv_face_detector_uint8.pb` (TensorFlow frozen graph).
  - Age Detection: `models/age_deploy.prototxt` và `models/age_net.caffemodel` (Caffe).
  - Gender Detection: `models/gender_deploy.prototxt` và `models/gender_net.caffemodel` (Caffe).
  - Recognition: OpenCV LBPH Face Recognizer huấn luyện trên dữ liệu cục bộ `face_database.pkl`.
- **Input:** Camera stream (`0`), video file, hoặc ảnh tĩnh qua tham số `--input`.
- **Output:** Frame OpenCV vẽ bounding box, tên, tuổi, giới tính, độ tin cậy; thư mục `unknown_faces/`, `saved_frames/`, log file `face_recognition.log`.
- **Camera usage:** Có sử dụng camera webcam thông qua `cv2.VideoCapture`. Được giải phóng đúng chuẩn (`cap.release()`, `cv2.destroyAllWindows()`) khi kết thúc.
- **UI hiện tại:** Cửa sổ OpenCV (`cv2.imshow`) và CLI interactive menu nếu không truyền tham số.
- **Database:** Pickle file cục bộ `face_database.pkl`.
- **File kết quả:** `face_database.pkl`, `face_recognition.log`.
- **Gọi bằng subprocess:** Rất thuận lợi (`subprocess.Popen([sys.executable, "main.py", "--input", "0"])`).
- **Cần sửa source không:** Không.
- **Đề xuất Adapter (`FaceAdapter`):**
  - Khởi chạy tiến trình nhận diện hoặc đăng ký khuôn mặt qua launcher subprocess.
  - Đồng bộ người dùng được nhận diện vào `shared/results/face.json` và cập nhật `shared/state.json`.

---

### 2.2. Module Emotion (`modules/emotion`)

- **Thư mục:** `modules/emotion/`
- **Entry Point:** `main.py`
- **Cách chạy:**
  ```bash
  python main.py
  ```
- **Python version:** Python 3.8+ (tương thích 3.10 - 3.12).
- **Dependencies:** `opencv-python`, `mediapipe`, `torch`, `numpy`, `pandas`, `scikit-learn`, `matplotlib`, `joblib`, `pytest`.
- **Model:**
  - `ExpressionNet` (mạng nơ-ron MLP PyTorch, đầu vào 63 điểm mốc đặc trưng chuẩn hóa từ MediaPipe FaceMesh 468 landmarks, 5 phân lớp: `Neutral`, `Happy`, `Sad`, `Angry`, `Surprised`).
  - **Lưu ý quan trọng:** File trọng số huấn luyện `models/expression_net.pth` chưa có sẵn trong thư mục repo `modules/emotion`.
  - **Giải pháp tối ưu:** Trong repo `modules/fall/qingxu/` đã có sẵn file mô hình nhận diện cảm xúc `best.onnx` (YOLO11 Face Emotion) hoàn chỉnh và kiểm thử tốt!
- **Input:** Webcam stream (mặc định camera index 0).
- **Output:** Frame hiển thị cảm xúc kèm thanh xác suất / độ tin cậy.
- **Camera usage:** Có sử dụng webcam qua `cv2.VideoCapture(0)`. Có lệnh giải phóng camera khi thoát.
- **UI hiện tại:** Cửa sổ OpenCV GUI.
- **Database:** Không.
- **File kết quả:** Chưa có tự động xuất file JSON.
- **Gọi bằng subprocess:** Có thể gọi trực tiếp.
- **Cần sửa source không:** Không sửa code gốc.
- **Đề xuất Adapter (`EmotionAdapter`):**
  - Tích hợp linh hoạt: Có thể khởi chạy `main.py` (sau khi nạp checkpoint) hoặc tái sử dụng model `best.onnx` từ module `qingxu` (vốn đã có sẵn bộ suy luận ONNX rất nhẹ và nhanh).
  - Trích xuất cảm xúc hiện tại và ghi định kỳ vào `shared/results/emotion.json`.

---

### 2.3. Module Fall & Health Monitoring (`modules/fall`)

- **Thư mục:** `modules/fall/`
  - Chứa 2 thư mục con: `deidao/` (Hệ thống phát hiện ngã & tư thế) và `qingxu/` (Mô hình nhận diện cảm xúc YOLO11).
- **Entry Point:**
  - Fall app: `modules/fall/deidao/main.py`
  - Fall detection engine: `modules/fall/deidao/detector.py` (`DetectionThread`)
  - Emotion model inference: `modules/fall/qingxu/app.py`
- **Cách chạy:**
  ```bash
  cd modules/fall/deidao && python main.py
  # Hoặc kiểm tra riêng model cảm xúc:
  cd modules/fall/qingxu && python app.py
  ```
- **Python version:** Python 3.8 - 3.12.
- **Dependencies:** `PyQt6`, `opencv-python`, `numpy`, `Pillow`, `torch`, `ultralytics`, `mediapipe`, `pygame`, `PyMySQL`, `requests`.
- **Model:**
  - Fall & Posture: YOLOv8 (`yolov8n.pt` phát hiện người) + MediaPipe Pose (xác định tọa độ vai và hông, tính góc nghiêng thân người `torso_aci`).
  - Phân loại tư thế:
    * Góc < 20°: Đứng (`站立 (Normal)`)
    * Góc > ngưỡng (50°): Nằm (`平躺 (Lying)`)
    * Giữa các khoảng và thay đổi đột ngột: Ngã (`跌倒中 (Falling)`)
  - Emotion: `modules/fall/qingxu/best.onnx` (YOLO11 Face Emotion).
- **Input:** Webcam (camera 0) hoặc file video thử nghiệm.
- **Output:**
  - Cảnh báo âm thanh qua `pygame.mixer` với `alarm.mp3`.
  - Video bằng chứng sự kiện ngã ~10 giây lưu tại `modules/fall/deidao/result/dusme_*.mp4`.
  - Thông báo Webhook / Feishu (có thể cấu hình lại gửi Email người nhà).
  - Ghi sự kiện vào cơ sở dữ liệu.
- **Camera usage:** Có, `cv2.VideoCapture` trong `DetectionThread`. Được giải phóng an toàn khi dừng thread.
- **UI hiện tại:** Giao diện PyQt6 đầy đủ (camera live stream, trạng thái tư thế, đếm số lần ngã, log sự kiện).
- **Database:** MySQL database `fall_detector_db`.
  - **Lỗi / Rủi ro đã phát hiện:** Code gốc trong `modules/fall/deidao/main.py` có đoạn kiểm tra bắt buộc:
    ```python
    if not init_database():
        sys.exit(1)
```
    Nếu máy tính chạy thi không có MySQL Server chạy tại `localhost` với mật khẩu `231006410`, chương trình sẽ crash ngay lập tức (`sys.exit(1)`).
- **File kết quả:** Video ngã tại `deidao/result/`.
- **Gọi bằng subprocess:** Có thể gọi GUI của module hoặc gọi trực tiếp engine `DetectionThread`.
- **Cần sửa source không:** Không sửa trực tiếp file gốc nếu có thể bọc qua adapter.
- **Đề xuất Adapter (`FallAdapter`):**
  - Adapter cung cấp cơ chế khởi động `DetectionThread` độc lập hoặc mock/bypass kết nối MySQL nếu MySQL không sẵn sàng, lưu sự kiện ngã trực tiếp vào `shared/alerts/alerts.json` và video clip vào `shared/recordings/`.
  - Đồng bộ thông tin tư thế (`standing`, `sitting`, `lying`) vào `shared/results/pose.json` và `shared/results/fall.json`.

---

### 2.4. Module Gesture (`modules/gesture`)

- **Thư mục:** `modules/gesture/`
- **Entry Point:**
  - Rule-based detector: `modules/gesture/src/main/hand_simple.py`
  - Machine Learning classifier: `modules/gesture/src/main/hand_ml.py`
- **Cách chạy:**
  ```bash
  python src/main/hand_simple.py
  # Hoặc:
  python src/main/hand_ml.py
  ```
- **Python version:** Python 3.9 - 3.12.
- **Dependencies:** `opencv-python==4.13.0.92`, `mediapipe==0.10.35`, `ai-edge-litert==2.1.4` (hoặc `tflite-runtime`), `numpy==2.4.4`, `absl-py==2.4.0`.
- **Model:**
  - MediaPipe Tasks Hand Landmarker: `src/main/hand_landmarker.task`.
  - TFLite Gesture Classifier: `src/main/gesture_classifier.tflite`.
- **Input:** Webcam stream (`cv2.VideoCapture(0)`).
- **Output:** Cửa sổ OpenCV vẽ khung xương bàn tay và tên cử chỉ phát hiện được.
- **Camera usage:** Có sử dụng webcam. Giải phóng camera khi người dùng đóng cửa sổ.
- **UI hiện tại:** Cửa sổ OpenCV.
- **Database:** Không.
- **File kết quả:** Không có sẵn.
- **Gọi bằng subprocess:** Có thể gọi độc lập bằng subprocess.
- **Cần sửa source không:** Không.
- **Đề xuất Adapter (`GestureAdapter`):**
  - Bọc quy trình nhận diện cử chỉ bàn tay. Ánh xạ các cử chỉ theo đúng yêu cầu dự án:
    * 4 ngón mở: Kích hoạt nghe trợ lý giọng nói (`Voice Assistant`)
    * 2 ngón (V-sign): Mở trò chơi trí nhớ (`Memory Game`)
    * Nắm tay (Fist / 0 ngón giơ): Hiển thị kế hoạch / việc cần làm chưa hoàn thành
  - Xuất sự kiện cử chỉ vào `shared/results/gesture.json` để Dashboard kích hoạt hành động tương ứng.

---

### 2.5. Module Medication (`modules/medication`)

- **Thư mục:** `modules/medication/`
- **Entry Point:**
  - Backend: `modules/medication/backend/app/main.py` (FastAPI app)
  - Frontend: `modules/medication/frontend/` (React + Vite + Tailwind CSS)
  - Script tổng thể: `modules/medication/scripts/start_all.bat`
- **Cách chạy:**
  ```bash
  # Khởi chạy backend:
  uvicorn app.main:app --port 8000
  # Khởi chạy frontend (nếu cần web UI):
  npm run dev
  ```
- **Python version:** Python 3.9 - 3.12.
- **Dependencies:** `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `pydantic-settings`, `pyttsx3`, `sounddevice`, `soundfile`, `requests`, `loguru`, `apscheduler`.
- **Model:** Vosk model cho nhận diện giọng nói / quy tắc NLP cho nhắc thuốc.
- **Input:** HTTP API request, cấu hình lịch uống thuốc, microphone.
- **Output:** Cơ sở dữ liệu SQLite `carevoice.db`, âm thanh TTS nhắc thuốc, bản tin thông báo (Email, Telegram, NTFY).
- **Camera usage:** Có hỗ trợ qua web component `PatientCameraMonitor.tsx`.
- **UI hiện tại:** Web UI React hiện đại + Swagger API Docs tại `http://localhost:8000/docs`.
- **Database:** Có, SQLite cục bộ (`carevoice.db`) thông qua SQLAlchemy.
- **File kết quả:** Dữ liệu lưu trong `carevoice.db`.
- **Gọi bằng subprocess:** Khởi động backend FastAPI qua `subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", ...])`.
- **Cần sửa source không:** Không.
- **Đề xuất Adapter (`MedicationAdapter`):**
  - Cung cấp phương thức quản lý danh sách thuốc, thiết lập giờ uống, xác nhận trạng thái (Đã uống / Bỏ lỡ).
  - Tích hợp với `services/medication_service.py` để đồng bộ dữ liệu vào `shared/data/medication.json` và `shared/results/medication.json`.
  - Tự động phát cảnh báo `MISSED_MEDICATION` nếu quá hạn uống thuốc.

---

### 2.6. Module Memory (`modules/memory`)

- **Thư mục:** `modules/memory/`
- **Tài nguyên hiện có:** `SIH_AAROGYA_LINK_MERGED.zip` (Chứa toàn bộ mã nguồn Flutter/Dart của ứng dụng Aarogya Link dành cho người cao tuổi) và `README.md` (Tài liệu chi tiết về trò chơi trí nhớ, cơ chế tính điểm, quản lý kế hoạch).
- **Entry Point:** Ứng dụng nguồn là Flutter (`lib/main.dart`).
- **Cách chạy:** Ứng dụng nguồn chạy qua Flutter SDK (`flutter run`). Môi trường Linux hiện tại không cài đặt Flutter/Dart SDK.
- **Python version:** N/A (Mã nguồn dự án là Dart).
- **Dependencies:** Flutter SDK, Dart 3.x, Hive DB.
- **Model:** Rule-based adaptive difficulty scoring và MediaPipe Face (trong client Flutter).
- **Input / Output:** Màn hình trò chơi trí nhớ (Sequence memory, Pattern completion, Memory matching), Kế hoạch hàng ngày, Định vị đồ vật, Điểm số đánh giá suy giảm nhận thức.
- **Camera usage:** Chụp ảnh kích thích trí nhớ gia đình.
- **UI hiện tại:** Flutter mobile/tablet interface.
- **Database:** Hive Embedded DB.
- **Đánh giá & Giải pháp tích hợp MVP:**
  - Vì mục tiêu đề tài là chạy ứng dụng máy tính trên nền tảng PyQt5 thống nhất và không ép cài đặt toolchain Flutter nặng nề:
  - Tích hợp module Memory trực tiếp vào PyQt5 Dashboard theo đúng đặc tả của `AI_for_older_MVP_INTEGRATION_GUIDE.md`:
    1. Quản lý kế hoạch nhắc nhở (`shared/data/plans.json`).
    2. Định vị trí đồ vật thường dùng (`shared/data/objects.json`: Kính, Chìa khóa, Điện thoại,...).
    3. Trò chơi trí nhớ tương tác (Memory Game: ma trận trí nhớ / lật thẻ bài theo đúng logic của Aarogya Link).
    4. Ghi nhận điểm số và lịch sử vào `shared/results/memory.json`.
- **Đề xuất Adapter (`MemoryAdapter`):**
  - Đóng vai trò cầu nối dữ liệu đọc/ghi kế hoạch, danh mục đồ vật và kết quả trò chơi trí nhớ, kết nối trực tiếp với Dashboard PyQt5.

---

### 2.7. Module Rehabilitation (`modules/rehabilitation`)

- **Thư mục:** `modules/rehabilitation/`
- **Entry Point:** `care.py`
- **Cách chạy:**
  ```bash
  python care.py
  ```
- **Python version:** Python 3.8 - 3.12 (hoàn toàn tương thích Python 3.12).
- **Dependencies:** `mediapipe==0.10.14`, `opencv-python==4.9.0.80`, `numpy==1.26.4`, `protobuf==4.25.3`.
- **Model:** MediaPipe Pose (`mp.solutions.pose`, `model_complexity=0`).
- **Logic bài tập:**
  - Sit-to-Stand: Đo góc gập gối (`knee_angle`) giữa hông, đầu gối và mắt cá chân. Góc < 95° là ngồi ("down"), góc > 165° là đứng lên ("up").
  - Arm Raises (Vươn vai): Đo góc vai trái/phải (`shoulder_angle`) với hông và cổ tay. Góc > 150° giữ trên 0.5s và hạ xuống tính 1 rep.
  - March Steps (Đi bộ tại chỗ): So sánh độ cao tương đối giữa đầu gối trái và đầu gối phải (`lk.y` vs `rk.y`).
- **Input:** Webcam stream (độ phân giải 640x480).
- **Output:** Cửa sổ OpenCV "AfterCare Functional Monitor" hiển thị các khớp xương và số lần thực hiện các bài tập.
- **Camera usage:** Có sử dụng webcam (`cv2.VideoCapture(0)`). Thoát và giải phóng camera khi nhấn phím ESC (`cap.release()`, `cv2.destroyAllWindows()`).
- **UI hiện tại:** Cửa sổ OpenCV GUI.
- **Database:** Không.
- **File kết quả:** Chưa có file JSON xuất tự động.
- **Gọi bằng subprocess:** Rất thuận lợi (`python care.py`).
- **Cần sửa source không:** Không.
- **Đề xuất Adapter (`RehabilitationAdapter`):**
  - Hỗ trợ khởi chạy các bài tập phục hồi chức năng tương ứng theo lựa chọn trên Dashboard: Vỗ tay, Đi bộ tại chỗ, Vươn vai, Xoay cổ, Co duỗi chân.
  - Thu thập số lần tập, số lần đúng/sai, tính điểm số hoàn thành và ghi vào `shared/results/rehabilitation.json`.

---

### 2.8. Module Voice (`modules/voice`)

- **Thư mục:** `modules/voice/`
- **Entry Point:** `main.py`
- **Cách chạy:**
  ```bash
  python main.py
  ```
- **Python version:** Python 3.8 - 3.12.
- **Dependencies:** `sounddevice`, `vosk`, `pyttsx3`.
- **Model:** Vosk English ASR model (đã có sẵn trong thư mục `modules/voice/models/vosk_model`).
- **Input:** Microphone qua `sounddevice.RawInputStream` (16kHz, mono).
- **Output:** Nhận dạng giọng nói thành văn bản, phân loại ý định (Intents), phát âm thanh phản hồi qua `pyttsx3`.
- **Các Intent được hỗ trợ:**
  - `medicine`: Nhắc uống thuốc theo thời gian định sẵn.
  - `time`: Thông báo giờ hiện tại.
  - `date`: Thông báo ngày tháng.
  - `help`: Tình huống khẩn cấp, kích hoạt cảnh báo gọi y tá / người thân.
  - `lights_on` / `lights_off`: Điều khiển thiết bị mô phỏng.
- **Camera usage:** Không sử dụng camera.
- **UI hiện tại:** Tkinter GUI với khung hội thoại và các nút chức năng tiện lợi cho người cao tuổi.
- **Database:** Không.
- **File kết quả:** Chưa xuất file JSON.
- **Gọi bằng subprocess:** Rất thuận lợi (`python main.py`).
- **Cần sửa source không:** Không.
- **Đề xuất Adapter (`VoiceAdapter`):**
  - Mở rộng xử lý các khẩu lệnh theo tài liệu dự án: Nhắc thuốc, Xem kế hoạch, Tìm đồ vật, Mở game trí nhớ.
  - Kết nối tín hiệu hai chiều với Dashboard và ghi nhận tương tác vào `shared/results/voice.json`.

---

## 3. TỔNG KẾT BẢNG SO SÁNH CÁC MODULE

| Module | Entry Point | Model / AI Core | Camera | UI gốc | DB gốc | Trạng thái độc lập | Rủi ro chính / Lưu ý |
|---|---|---|:---:|---|---|:---:|---|
| **Face** | `modules/face/main.py` | Caffe + TF (OpenCV DNN) + LBPH | Có | OpenCV | Pickle | Sẵn sàng | Cần `opencv-contrib-python` |
| **Emotion** | `modules/emotion/main.py` | MediaPipe FaceMesh + PyTorch | Có | OpenCV | Không | Thiếu checkpoint | Dùng model ONNX YOLO11 từ `fall/qingxu` |
| **Fall** | `modules/fall/deidao/main.py` | YOLOv8 + MediaPipe Pose | Có | PyQt6 | MySQL | Rủi ro crash MySQL | Cần bypass/mock MySQL trong adapter |
| **Gesture** | `modules/gesture/src/main/hand_simple.py` | MediaPipe Landmarker + TFLite | Có | OpenCV | Không | Sẵn sàng | Cần `ai-edge-litert` / TFLite runtime |
| **Medication** | `modules/medication/backend/app/main.py` | Vosk + Rule NLP | Không | React Web | SQLite | Sẵn sàng | Chạy FastAPI backend subprocess |
| **Memory** | `modules/memory/SIH_AAROGYA_LINK_MERGED.zip` | Logic Games & MediaPipe Face | Không | Flutter | Hive | Mã Dart/Flutter | Tích hợp giao diện và logic vào PyQt5 |
| **Rehab** | `modules/rehabilitation/care.py` | MediaPipe Pose | Có | OpenCV | Không | Sẵn sàng | Bổ sung xuất kết quả JSON bài tập |
| **Voice** | `modules/voice/main.py` | Vosk ASR + pyttsx3 TTS | Không | Tkinter | Không | Sẵn sàng | Có sẵn model Vosk offline |

---

## 4. KẾ HOẠCH HÀNH ĐỘNG TIẾP THEO (PHASE 1)

1. Thiết lập môi trường ảo Python (`venv`) thống nhất cho dự án với đầy đủ các gói:
   - GUI: `PyQt5` (theo chuẩn thiết kế hệ thống trung tâm)
   - Thị giác máy tính: `opencv-contrib-python`, `mediapipe`, `ultralytics`, `torch`
   - Âm thanh: `sounddevice`, `vosk`, `pyttsx3`, `pygame`
   - Backend & Tiện ích: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-dotenv`
2. Chạy thử độc lập từng module theo đúng thứ tự ưu tiên:
   - `face` → `emotion` → `fall` → `rehabilitation` → `gesture` → `voice` → `medication` → `memory`
3. Kiểm tra camera resource management để đảm bảo giải phóng camera (`cap.release()`) tránh xung đột tài nguyên.
