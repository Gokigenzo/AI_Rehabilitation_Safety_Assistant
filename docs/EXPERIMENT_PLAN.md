# KẾ HOẠCH THỰC NGHIỆM VÀ ĐÁNH GIÁ KHOA HỌC
## AI Rehabilitation & Safety Assistant — Comprehensive Experiment & Benchmarking Plan

**Dự án:** Trợ lý Phục hồi Chức năng và Cảnh báo An toàn Thông minh cho Người cao tuổi  
**Mục tiêu:** Báo cáo khoa học & Kịch bản thực nghiệm tham gia Cuộc thi Khoa học Kỹ thuật Học sinh / Sinh viên  
**Phiên bản hệ thống:** v3.0 (Final Science Competition MVP)  
**Ngày lập kế hoạch:** 30/09/2026  

---

## 1. MỤC TIÊU NGHIÊN CỨU & THỰC NGHIỆM (OBJECTIVES)

Nghiên cứu tập trung giải quyết bài toán chăm sóc và bảo vệ sức khỏe người cao tuổi tại nhà bằng Thị giác Máy tính cục bộ (Edge AI) với 4 module tích hợp khép kín:
1. **Nhận diện Khuôn mặt (Face Recognition):** Nhận diện danh tính người cao tuổi để cá nhân hóa thông số tập luyện và tự động liên kết với hồ sơ người giám hộ tương ứng.
2. **Nhận diện Cảm xúc (Emotion Recognition):** Phân tích trạng thái tâm lý lâm sàng (3 cảm xúc: Bình thường, Vui vẻ, Buồn bã) trước và trong khi tập luyện thông qua động học cơ mặt (FACS Biomechanics).
3. **Phục hồi Chức năng (Rehabilitation Engine - Trọng tâm AI):** Đo lường động học góc khớp giải phẫu qua máy trạng thái hữu hạn (FSM) cho 3 bài tập vận động, đếm số chu kỳ tập (reps), phát hiện lỗi sai tư thế và chấm điểm phong độ (Form Score 0 - 100%).
4. **Giám sát An toàn & Phát hiện Ngã (Fall Detection):** Phân tích động học tư thế (Pose Kinematics) kết hợp bộ xác thực thời gian đa tầng (Temporal Verification FSM) nhằm phát hiện kịp thời sự cố ngã khẩn cấp, loại trừ triệt để báo động giả khi cúi người/ngồi ghế, chụp ảnh bằng chứng và tự động gửi cảnh báo khẩn cấp tới Gmail người thân.

---

## 2. KỊCH BẢN THỬ NGHIỆM & BỘ DỮ LIỆU ĐÁNH GIÁ (DATASET & TEST SCENARIOS)

### 2.1. Module Nhận diện Khuôn mặt (Face Recognition)
- **Tập mẫu:** 15 người tham gia thử nghiệm (10 người cao tuổi 65 - 82 tuổi, 5 người trẻ giả lập người lạ/unregistered).
- **Kịch bản kiểm thử:**
  - *Khoảng cách camera:* $0.6\text{m}$, $1.2\text{m}$, $2.0\text{m}$.
  - *Điều kiện ánh sáng:*
    - Ánh sáng tự nhiên tiêu chuẩn: $300 - 500\text{ lux}$
    - Ánh sáng yếu phòng ngủ: $50 - 100\text{ lux}$
    - Ánh sáng ngược / đèn chiếu lệch bên: $600\text{ lux}$
  - *Góc nghiêng khuôn mặt (Head Pose Yaw/Pitch):* $0^\circ$ (trực diện), $\pm 15^\circ$, $\pm 30^\circ$.
  - *Kịch bản Người lạ (Unregistered Intruder / Unknown):* Thử nghiệm với người chưa đăng ký để kiểm tra tỷ lệ từ chối sai (FAR).

### 2.2. Module Nhận diện Cảm xúc (Emotion Recognition - 3 Trạng thái Cốt lõi)
- **3 Phân lớp:**
  - **Bình thường (Neutral):** Khuôn mặt thả lỏng khi nghỉ ngơi hoặc lắng nghe hướng dẫn.
  - **Vui vẻ (Happy):** Cười mỉm hoặc cười tươi (kích hoạt cơ gò má lớn Zygomaticus Major - AU12).
  - **Buồn bã (Sad):** Hạ khóe miệng (Depressor Anguli Oris - AU15) và nhăn đầu lông mày (AU1/4).
- **Kiểm thử ổn định thời gian (Temporal Stability):**
  - So sánh đầu ra tức thời (Raw Frame-by-frame) với đầu ra qua bộ lọc **Sliding Window Deque ($N=8$)**.
  - Đo độ lệch chuẩn nhấp nháy chuyển trạng thái (State Flickering Frequency).

### 2.3. Module Phục hồi Chức năng (Rehabilitation Engine)
Đánh giá trên 3 bài tập vận động chuẩn y khoa:
1. **Nâng tay qua đầu (Arm Raise):**
   - Đếm nhịp (Repetition Counting): 10 lần thực hiện đúng, 5 lần cố tình nâng chưa đủ độ cao ($< 142^\circ$).
   - Phát hiện lỗi: Gập khuỷu tay ($< 130^\circ$), lệch hai tay ($> 25^\circ$), hạ tay quá nhanh ($< 0.35\text{s}$).
2. **Đứng lên ngồi xuống (Sit-to-Stand):**
   - Đếm nhịp: 10 lần đứng lên - ngồi xuống hoàn chỉnh.
   - Phát hiện lỗi: Đứng chưa thẳng gối ($< 162^\circ$), gập thân người quá sâu ra trước ($> 45^\circ$).
3. **Nâng cao đùi tại chỗ (Marching):**
   - Đếm nhịp: 20 bước luân phiên trái - phải.
   - Phát hiện lỗi: Đùi nâng chưa đạt tầm ngang hông ($y_{\text{knee}} \ge y_{\text{hip}} + 0.18$), bước không đều.

### 2.4. Module Phát hiện Ngã & An toàn (Fall Detection & Safety)
- **Kịch bản Ngã Thật (True Positive Scenarios):**
  - Ngã sấp về phía trước (Forward Fall) lên đệm an toàn.
  - Ngã ngửa ra sau (Backward Fall).
  - Ngã nghiêng sang một bên (Lateral Fall).
  - Ngã từ tư thế ngồi trượt xuống sàn (Slip & Slide Fall).
- **Kịch bản Sinh hoạt Hàng ngày (Negative Scenarios - Kiểm tra Báo động Giả):**
  - Đứng yên, vươn người, quay người.
  - Ngồi xuống ghế, ngồi xếp bằng.
  - Đi lại qua lại trước ống kính camera.
  - **Cúi nhặt đồ vật trên sàn (Picking up object / Bending):** Thân gập sâu ($> 50^\circ$) nhưng hai chân thẳng giữ hông cao $\rightarrow$ **Yêu cầu 0% báo động giả**.
- **Xác thực Cửa sổ Thời gian (Temporal Verification Window):**
  - Thử nghiệm độ trễ cửa sổ $T_{\text{confirm}} = 3.0\text{ giây}$.
  - Người thử nghiệm giả vờ ngã rồi tự đứng dậy sau 1.5 giây $\rightarrow$ Hệ thống tự động phục hồi `NORMAL`, hủy bỏ trạng thái `SUSPECTED` mà không gửi email.
  - Người thử nghiệm nằm yên trên sàn quá $3.0\text{ giây}$ $\rightarrow$ Xác nhận `FALL_CONFIRMED` $\rightarrow$ Lưu snapshot và gửi email.

### 2.5. Hệ thống Cảnh báo Khẩn cấp qua Gmail (Emergency Alert System)
- Kiểm thử độ trễ gửi email qua SMTP: Thời gian từ khi kích hoạt `FALL_CONFIRMED` đến khi hòm thư người giám hộ nhận được thông báo.
- Kiểm tra tính đầy đủ của nội dung: Thông tin người gặp nạn, thời gian chính xác, hướng dẫn cấp cứu và tệp ảnh chụp hiện trường đính kèm.
- Kiểm tra cơ chế chống thư rác (Cooldown Cooldown 15 giây).
- Kiểm tra tính chịu lỗi (Fault-tolerance): Rút dây mạng hoặc ngắt Internet $\rightarrow$ Ứng dụng ghi nhận cảnh báo nội bộ, camera và giao diện tiếp tục hoạt động $100\%$ không bị treo/crash.

---

## 3. CHỈ SỐ ĐÁNH GIÁ KHOA HỌC (EVALUATION METRICS)

$$\begin{aligned}
\text{Precision} &= \frac{TP}{TP + FP} \\
\text{Recall (Sensitivity)} &= \frac{TP}{TP + FN} \\
\text{F1-Score} &= 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} \\
\text{Accuracy} &= \frac{TP + TN}{TP + TN + FP + FN} \\
\text{False Positive Rate (FPR)} &= \frac{FP}{FP + TN}
\end{aligned}$$

### Bảng Chỉ tiêu Đo lường Dự kiến và Ngưỡng Chấp nhận:

| Module / Tính năng | Chỉ số (Metric) | Ngưỡng Mục tiêu Khoa học | Ý nghĩa Y sinh / Khoa học |
|---|---|---|---|
| **Face Recognition** | Accuracy / Recall | $\ge 95.0\%$ | Đảm bảo nhận đúng người bệnh để lấy đúng email người thân |
| **Face Recognition** | False Match Rate (FMR) | $< 3.0\%$ | Tránh gán nhầm dữ liệu người tập cho người lạ |
| **Emotion Recognition** | Macro F1-Score | $\ge 90.0\%$ | Đánh giá chính xác trạng thái tâm lý người bệnh |
| **Emotion Smoothing** | Flicker Variance Reduction | $> 70.0\%$ | Khử hiện tượng nhảy cảm xúc thất thường giữa các khung hình |
| **Rehabilitation Reps** | Repetition Accuracy | $\ge 90.0\%$ | Đếm nhịp vận động tin cậy cho bài tập phục hồi |
| **Rehabilitation Form** | Biomechanical Accuracy | $\ge 92.0\%$ | Bắt chính xác góc lệch sinh học và lỗi kỹ thuật |
| **Fall Detection** | True Fall Sensitivity (Recall) | $\ge 95.0\%$ | Bắt buộc không được bỏ sót bất kỳ ca ngã thật nào |
| **Fall Detection** | False Alarm Rate (Bending/Sitting) | $< 2.0\%$ | Người già cúi nhặt đồ không bị gửi thư báo động giả |
| **Emergency Email** | Dispatch Latency | $< 3.0\text{ giây}$ | Gửi báo động nhanh nhất có thể tới người giám hộ |
| **Pipeline Latency** | System FPS | $\ge 30.0\text{ FPS}$ | Xử lý thời gian thực trơn tru trên camera HD 720p/VGA |

---

## 4. THIẾT LẬP PHẦN CỨNG & QUY TRÌNH THỰC NGHIỆM (HARDWARE SETUP & PROTOCOL)

### 4.1. Cấu hình Phần cứng Thử nghiệm
- **Thiết bị:** Laptop ASUS TUF Gaming / Asus Vivobook phổ thông (Intel Core i5/i7 thế hệ 12/13, 16GB RAM, Ubuntu 24.04 LTS / Linux x86_64).
- **Camera:** Webcam tích hợp sẵn (Integrated HD Camera 720p @ 30 FPS) hoặc Webcam ngoài USB (Logitech C920 1080p).
- **Góc đặt Camera:** Đặt camera ngang tầm ngực người bệnh (độ cao $0.9\text{m} - 1.2\text{m}$), cách vị trí tập $1.8\text{m} - 2.5\text{m}$ để thu trọn vẹn toàn bộ cơ thể từ đầu đến gót chân.

### 4.2. Quy trình Thực hiện Đo đạc Thực nghiệm (Step-by-Step Protocol)
1. **Hiệu chuẩn môi trường:** Đo độ rọi sáng phòng bằng máy Lux Meter ($350 \pm 50\text{ lux}$).
2. **Khởi tạo dữ liệu người dùng:** Đăng ký 3 người cao tuổi và cấu hình địa chỉ Gmail người giám hộ.
3. **Thực hiện bài kiểm tra Phục hồi chức năng:**
   - Mỗi người thực hiện lần lượt 3 hiệp (mỗi hiệp 10 lần) cho 3 bài tập: Nâng tay, Đứng ngồi, Nâng đùi.
   - Chuyên gia/Trọng tài đếm tay độc lập làm Ground Truth.
4. **Thực hiện bài kiểm tra An toàn & Ngã:**
   - Thực hiện 10 lần động tác cúi nhặt đồ vật, buộc dây giày (Bending).
   - Thực hiện 10 lần động tác ngồi xuống - đứng lên từ ghế (Sitting).
   - Thực hiện 15 lần động tác ngã có đệm đỡ (5 lần ngã trước, 5 lần ngã sau, 5 lần ngã nghiêng).
   - Đo thời gian kích hoạt FSM và thời gian gửi email.
5. **Ghi nhật ký và phân tích:** Tự động trích xuất các tệp `evaluation_benchmark.json` và bảng nhật ký `event.json` trong thư mục `data/fall_events/`.

---

## 5. KỊCH BẢN TRÌNH DIỄN KHOA HỌC (COMPETITION DEMO SCRIPT - 3 PHÚT)

### 5.1. Phân bổ Thời gian Trình diễn Trước Ban Giám Khảo (3-Minute Live Walkthrough)

| Mốc thời gian | Nội dung Trình bày & Hành động | Trọng tâm Nhấn mạnh với Giám khảo |
|---|---|---|
| **00:00 - 00:30** | **Đăng ký Người bệnh & Người giám hộ**<br/>Mở hộp thoại Đăng ký, nhập ID, Tên cụ già và Gmail người giám hộ. Chụp 5 ảnh khuôn mặt căn chỉnh ROI. | Tính chuẩn mực dữ liệu y tế, chuẩn hóa 15% padding, liên kết hồ sơ gia đình trực tiếp tại biên (Edge). |
| **00:30 - 01:00** | **Nhận diện Tức thì & Đo lường Tâm lý**<br/>Người dùng đứng trước webcam $\rightarrow$ Khung nhận diện Xanh lục hiện tên bệnh nhân. Cười nhẹ $\rightarrow$ Huy hiệu Vui vẻ (94%). | Thuật toán LBPH + CLAHE chống nhiễu sáng; giải thuật FACS Biomechanics kết hợp Deque làm mượt thời gian. |
| **01:00 - 01:45** | **Huấn luyện viên Phục hồi Chức năng (Core AI)**<br/>Chọn bài tập *Nâng tay qua đầu* $\rightarrow$ Thực hiện 3 động tác chuẩn (HUD báo góc vai $158^\circ$), sau đó cố tình gập khuỷu tay $\rightarrow$ HUD cảnh báo lỗi kỹ thuật. | Động cơ MediaPipe Pose 33 điểm, máy trạng thái FSM đếm nhịp chính xác và chấm điểm định lượng sinh học (Form Score). |
| **01:45 - 02:45** | **Cao trào: Giám sát An toàn & Xử lý Tình huống Ngã Khẩn cấp**<br/>1. Thử nghiệm cúi nhặt bút rơi trên sàn $\rightarrow$ Hệ thống nhận diện `Cúi người (BENDING)`, KHÔNG báo động giả.<br/>2. Diễn viên nằm sụp xuống đệm sàn $\rightarrow$ Trạng thái chuyển: `NORMAL` $\to$ `SUSPECTED` (tỉ lệ AR > 1.2, góc nghiêng $85^\circ$) $\to$ `CONFIRMING (3s)` $\to$ `FALL_CONFIRMED`.<br/>3. Chuông báo động hú vang, màn hình nhấp nháy đỏ, chụp snapshot.<br/>4. Mở Gmail người giám hộ trên điện thoại/máy tính $\rightarrow$ Email cảnh báo khẩn cấp kèm ảnh hiện trường vừa gửi tới! | **Đột phá:** Phân tích động học loại trừ hoàn toàn báo động giả; cửa sổ xác thực thời gian 3.0s loại bỏ trường hợp tự đứng dậy; gửi email tự động không độ trễ. |
| **02:45 - 03:00** | **Kết luận & Tiềm năng Ứng dụng**<br/>Tóm tắt: Hệ thống chạy hoàn toàn Offline/Local trên máy tính thông thường (35+ FPS), bảo vệ người già 24/7. | Chi phí $0 đồng phần cứng bổ sung (dùng webcam sẵn có), bảo mật quyền riêng tư tuyệt đối, ứng dụng thiết thực cho xã hội già hóa. |

---

## 6. PHƯƠNG ÁN DỰ PHÒNG CHO TRÌNH DIỄN (FALLBACK CONTINGENCY PLAN)

1. **Sự cố mất kết nối Internet thoại hội trường:**
   - Dịch vụ email `EmailService` hoạt động hoàn toàn thread-safe không đồng bộ. Khi mất mạng, email sẽ báo lỗi nhẹ nhàng trong log, hệ thống **tuyệt đối không bao giờ crash**.
   - Ảnh bằng chứng và hồ sơ `event.json` vẫn được ghi đầy đủ vào ổ cứng tại `data/fall_events/fall_.../`. Giám khảo có thể trực tiếp mở thư mục bằng chứng để thẩm định.
2. **Webcam phần cứng gặp sự cố chập chờn:**
   - `CameraManager` Singleton tự động phát hiện lỗi ngắt luồng và kích hoạt `Simulation Mode` (chuỗi khung hình động học sinh học chuẩn 30 FPS).
3. **Kịch bản Demo tự động một lệnh:**
   - Chạy lệnh: `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python .venv/bin/python demo.py` để trình diễn tuần tự tự động toàn bộ 6 bước với đầy đủ số liệu mô phỏng chuẩn xác.

---

## 7. CÂU HỎI PHẢN BIỆN TRỌNG TÂM CỦA GIÁM KHẢO & LỜI ĐÁP HỌC THUẬT

- **Câu hỏi 1: Tại sao hệ thống không dùng cảm biến đeo tay (Smartwatch / Gia tốc kế) mà dùng Camera AI?**
  - *Trả lời:* Người cao tuổi thường xuyên quên sạc pin, quên đeo vòng tay hoặc cảm thấy khó chịu khi đi ngủ/tắm. Thị giác máy tính là giải pháp giám sát thụ động (Zero-burden / Non-invasive), không đòi hỏi người già phải nhớ bất kỳ thao tác nào.
- **Câu hỏi 2: Làm sao hệ thống phân biệt được một người cố tình nằm xuống ngủ hoặc cúi nhặt đồ với một ca ngã nguy hiểm?**
  - *Trả lời:* Hệ thống kết hợp 3 lớp bảo vệ động học: (1) Chiều cao cẳng chân so với hông: Khi cúi người, hai chân vẫn thẳng và chịu lực ($y_{\text{ankles}} - y_{\text{hips}} \ge 0.20$), hông vẫn ở tầm cao; (2) Tốc độ sụp đổ trọng tâm cơ thể; (3) Máy trạng thái xác thực thời gian (Temporal Verification FSM): Nếu người nằm thư giãn, họ cử động bình thường; nếu ngã bất tỉnh, họ nằm bất động tại sàn vượt quá ngưỡng $3.0\text{ giây}$.
- **Câu hỏi 3: Độ bảo mật hình ảnh của người cao tuổi được xử lý như thế nào?**
  - *Trả lời:* Toàn bộ mô hình thị giác AI (OpenCV Face, ExpressionNet, MediaPipe Pose) chạy $100\%$ cục bộ trên CPU máy tính tại gia đình, không truyền luồng video lên bất kỳ đám mây (Cloud) nào. Chỉ khi nào sự cố ngã khẩn cấp được xác thực, đúng 1 bức ảnh chụp tại khoảnh khắc đó mới được gửi mã hóa TLS tới hộp thư Gmail của người thân đã đăng ký.
