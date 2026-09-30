@echo off
chcp 65001 >nul
title AI REHABILITATION & SAFETY ASSISTANT — KHỞI CHẠY HỆ THỐNG
color 0B

echo ==============================================================================
echo     HỆ THỐNG TRỢ LÝ PHỤC HỒI CHỨC NĂNG & AN TOÀN NGƯỜI CAO TUỔI (AI CARE)
echo     Phiên bản: v3.0 (Tương thích Windows 10/11 x64)
echo ==============================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [CẢNH BÁO] Không tìm thấy Python trong biến môi trường PATH!
    echo Vui lòng tải và cài đặt Python 3.10 / 3.11 / 3.12 từ: https://www.python.org/
    echo LƯU Ý QUAN TRỌNG: Hãy tích chọn vào ô "[x] Add Python to PATH" khi cài đặt!
    echo.
    pause
    exit /b 1
)

:: 2. Khởi tạo môi trường ảo độc lập nếu chưa có
if not exist ".venv" (
    echo [1/3] Đang tạo môi trường ảo Python (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [LỖI] Không thể tạo môi trường ảo!
        pause
        exit /b 1
    )
    echo [2/3] Đang tự động cài đặt các thư viện cần thiết...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo   ✓ Đã hoàn tất cài đặt thư viện!
) else (
    call .venv\Scripts\activate.bat
)

:: 3. Tạo các thư mục dữ liệu nếu chưa có
if not exist "data\users" mkdir "data\users"
if not exist "data\fall_events" mkdir "data\fall_events"
if not exist "data\sessions" mkdir "data\sessions"
if not exist "logs" mkdir "logs"
if not exist ".env" (
    if exist ".env.example" copy .env.example .env >nul
)

:: 4. Cấu hình biến môi trường và Khởi chạy ứng dụng
echo.
echo [3/3] Đang khởi chạy giao diện AI Rehabilitation & Safety Assistant...
echo   • Camera: Bắt đầu dò tìm webcam...
echo   • AI Engine: Nạp mô hình Nhận diện mặt, Cảm xúc FACS, Khung xương Pose...
echo   • Giám sát An toàn: Kích hoạt bộ lọc phát hiện ngã...
echo.

set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
set MPLCONFIGDIR=%TEMP%\matplotlib-cache

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [THÔNG BÁO] Ứng dụng đã dừng với mã lỗi: %errorlevel%
    echo Vui lòng kiểm tra nhật ký chi tiết tại: logs\app.log
    pause
)
