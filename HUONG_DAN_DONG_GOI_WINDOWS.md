# HƯỚNG DẪN ĐÓNG GÓI & CÀI ĐẶT ỨNG DỤNG TRÊN WINDOWS (.EXE)
## AI Rehabilitation & Safety Assistant — Windows Packaging & Distribution Guide

Hệ thống đã được trang bị đầy đủ công cụ và kịch bản tự động để đóng gói thành tệp thực thi `.exe` và bộ cài đặt trọn gói (`Setup_AI_Rehab_Safety_Assistant.exe`) dành riêng cho Windows 10/11 (64-bit).

---

## ⚠️ NGUYÊN LÝ KỸ THUẬT QUAN TRỌNG

> **Lưu ý:** Hệ điều hành hiện tại bạn đang lập trình là **Linux (Ubuntu)**.
> Các thư viện Trí tuệ Nhân tạo và Thị giác Máy tính cốt lõi của dự án (`PyQt5`, `opencv-python`, `torch`, `mediapipe`) sử dụng các thư viện nhị phân C++ (DLL trên Windows vs `.so` trên Linux).
> Do đó, theo nguyên lý của PyInstaller, việc đóng gói thành file `.exe` chạy trên Windows **cần được thực hiện trên môi trường Windows** (hoặc qua máy ảo Windows trên GitHub Actions).

Hệ thống đã được chuẩn bị sẵn **3 phương thức đóng gói và triển khai hoàn toàn tự động**:

---

## CÁCH 1: KHỞI CHẠY TỰ ĐỘNG BẰNG 1-CLICK TRÊN MÁY TÍNH WINDOWS
*(Cách nhanh nhất để người dùng Windows chạy ngay không cần cài đặt phức tạp)*

1. Sao chép toàn bộ thư mục dự án `AI_for_older` sang máy tính Windows.
2. Nhấp đúp chuột vào tệp:
   ```
   Setup_and_Run_Windows.bat
   ```
3. Kịch bản sẽ tự động:
   - Kiểm tra Python trên máy Windows.
   - Tự tạo môi trường ảo `.venv` độc lập.
   - Tự cài đặt đầy đủ các thư viện từ `requirements.txt`.
   - Tự cấu hình biến môi trường và khởi chạy giao diện ứng dụng.

---

## CÁCH 2: ĐÓNG GÓI THÀNH FILE .EXE VÀ BỘ CÀI ĐẶT TRÊN WINDOWS

Khi bạn đang ở trên máy tính Windows và muốn xuất ra file `.exe` thành phẩm:

### Bước 1: Biên dịch bằng PyInstaller (1-Click)
Nhấp đúp vào tệp:
```
build_windows_exe.bat
```
Kịch bản sẽ tự động chạy lệnh PyInstaller với cấu hình tối ưu tại `AI_Rehab_Safety_Assistant.spec`, tự động nhúng:
- Toàn bộ mô hình nhận diện khuôn mặt (`opencv_face_detector_uint8.pb`, `.pbtxt`).
- Mô hình PyTorch cảm xúc (`expression_net.pth`).
- Đồ thị sinh học và mạng MediaPipe Pose & FaceMesh.
- Font chữ tiếng Việt Windows (`Arial`, `Segoe UI`, `Tahoma`).

Sau khi chạy xong, ứng dụng `.exe` hoàn chỉnh sẽ nằm tại thư mục:
```
dist\AI_Rehab_Safety_Assistant\AI_Rehab_Safety_Assistant.exe
```

### Bước 2: Tạo bộ cài đặt tự động (Setup Installer .exe)
Nếu bạn muốn tạo một file cài đặt duy nhất giống như các phần mềm chuyên nghiệp (nhấp đúp là hiện cửa sổ Wizard "Next -> Next -> Install" và tự tạo icon ra màn hình Desktop):

1. Tải phần mềm miễn phí **Inno Setup** tại: [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
2. Mở tệp kịch bản đã soạn sẵn trong dự án:
   ```
   installer_setup.iss
   ```
3. Nhấn nút **Build / Compile** (hoặc phím tắt `Ctrl + F9`).
4. Inno Setup sẽ tạo ra một file duy nhất:
   ```
   release_installer\Setup_AI_Rehab_Safety_Assistant_v3.0.exe
   ```
👉 Người dùng chỉ cần gửi file `Setup_AI_Rehab_Safety_Assistant_v3.0.exe` này cho bất kỳ ai dùng Windows 10/11. Họ chỉ cần nhấp đúp là ứng dụng tự cài vào máy, tạo icon Desktop và chạy ngay lập tức!

---

## CÁCH 3: TỰ ĐỘNG ĐÓNG GÓI BẰNG GITHUB ACTIONS (KHÔNG CẦN MÁY WINDOWS)
*(Cách tối ưu nhất nếu bạn chỉ có máy tính Linux hiện tại)*

Dự án đã tích hợp sẵn kịch bản CI/CD đám mây tại:  
`.github/workflows/build_windows_exe.yml`

1. Đẩy mã nguồn dự án lên GitHub:
   ```bash
   git add .
   git commit -m "Add Windows EXE packaging scripts"
   git push origin main
   ```
2. Vào mục **Actions** trên giao diện GitHub Repository của bạn.
3. Chọn workflow **"Build Windows EXE & Installer"** và bấm **"Run workflow"**.
4. GitHub sẽ cấp một máy ảo Windows bản quyền miễn phí, tự động tải các thư viện, chạy PyInstaller và Inno Setup.
5. Sau khi hoàn thành (khoảng 4-6 phút), bạn sẽ thấy 2 tệp thành phẩm trong phần **Artifacts** để tải về trực tiếp:
   - `Setup_AI_Rehab_Safety_Assistant_v3.0.zip` (Bộ cài đặt tự động).
   - `AI_Rehab_Safety_Assistant_Portable_Windows.zip` (Bản portable giải nén là chạy).

---

## TỔNG KẾT DANH MỤC CÁC TỆP ĐÃ TẠO

| Tệp tin | Vai trò |
|---|---|
| `AI_Rehab_Safety_Assistant.spec` | Tệp đặc tả cấu hình PyInstaller chuyên dụng cho Windows (nhúng đầy đủ models, hidden imports, fonts). |
| `build_windows_exe.bat` | Kịch bản 1-click biên dịch dự án thành `.exe` trên máy tính Windows. |
| `installer_setup.iss` | Kịch bản Inno Setup để tạo bộ cài đặt duy nhất `Setup_...exe` có biểu tượng Desktop và gỡ cài đặt. |
| `Setup_and_Run_Windows.bat` | Kịch bản 1-click tự động cài thư viện và khởi chạy ngay lập tức trên mọi máy Windows. |
| `.github/workflows/build_windows_exe.yml` | Kịch bản tự động biên dịch Windows `.exe` trên đám mây GitHub Actions. |
| `config.py` & `core/drawing_utils.py` | Đã nâng cấp tương thích $100\%$ với Windows fonts và cơ chế `sys.frozen` của PyInstaller. |
