@echo off
chcp 65001 >nul
title ĐÓNG GÓI ỨNG DỤNG AI REHABILITATION & SAFETY ASSISTANT (.EXE)
echo ==============================================================================
echo   CÔNG CỤ ĐÓNG GÓI TỰ ĐỘNG THÀNH FILE .EXE CHẠY TRÊN WINDOWS
echo   AI REHABILITATION & SAFETY ASSISTANT — PHIÊN BẢN 3.0 (FINAL MVP)
echo ==============================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo Vui lòng cài đặt Python 3.10, 3.11 hoặc 3.12 từ https://www.python.org/
    echo Chú ý tích chọn: "Add Python to PATH" khi cài đặt.
    pause
    exit /b 1
)

echo [1/5] Kiểm tra phiên bản Python...
python --version

:: 2. Khởi tạo môi trường ảo chuyên biệt cho đóng gói
echo.
echo [2/5] Tạo môi trường ảo .venv_build...
if not exist ".venv_build" (
    python -m venv .venv_build
)

call .venv_build\Scripts\activate.bat

:: 3. Cài đặt các thư viện phụ thuộc
echo.
echo [3/5] Cập nhật pip và cài đặt thư viện cần thiết...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

:: 4. Tiến hành đóng gói bằng PyInstaller
echo.
echo [4/5] Đang tiến hành biên dịch ứng dụng thành tệp .exe...
echo Quá trình này có thể mất từ 2-4 phút tùy theo tốc độ CPU...
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
pyinstaller --clean --noconfirm AI_Rehab_Safety_Assistant.spec

if %errorlevel% neq 0 (
    echo.
    echo [LỖI] Quá trình biên dịch PyInstaller thất bại!
    echo Vui lòng kiểm tra lại log bên trên.
    pause
    exit /b 1
)

:: 5. Hoàn tất thư mục phân phối
echo.
echo [5/5] Hoàn tất và cấu hình thư mục phát hành...
if not exist "dist\AI_Rehab_Safety_Assistant\data" (
    mkdir "dist\AI_Rehab_Safety_Assistant\data\users"
    mkdir "dist\AI_Rehab_Safety_Assistant\data\fall_events"
    mkdir "dist\AI_Rehab_Safety_Assistant\data\sessions"
    mkdir "dist\AI_Rehab_Safety_Assistant\logs"
)

copy .env.example "dist\AI_Rehab_Safety_Assistant\.env" >nul 2>nul

:: Tạo shortcut khởi chạy nhanh bên trong thư mục dist
echo @echo off > "dist\AI_Rehab_Safety_Assistant\CHAY_UNG_DUNG.bat"
echo set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python >> "dist\AI_Rehab_Safety_Assistant\CHAY_UNG_DUNG.bat"
echo start "" "AI_Rehab_Safety_Assistant.exe" >> "dist\AI_Rehab_Safety_Assistant\CHAY_UNG_DUNG.bat"

echo.
echo ==============================================================================
echo   ✓ ĐÓNG GÓI THÀNH CÔNG!
echo ==============================================================================
echo Tệp thực thi .exe hoàn thiện đã được tạo tại thư mục:
echo   --> dist\AI_Rehab_Safety_Assistant\AI_Rehab_Safety_Assistant.exe
echo.
echo Bạn có thể nén thư mục "dist\AI_Rehab_Safety_Assistant" để gửi cho người khác,
echo hoặc sử dụng Inno Setup với file "installer_setup.iss" để tạo bộ cài đặt duy nhất!
echo ==============================================================================
echo.
pause
