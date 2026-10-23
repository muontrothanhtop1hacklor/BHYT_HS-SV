@echo off
chcp 65001 >nul
echo ===================================================================
echo KỊCH BẢN SINH DỮ LIỆU BHYT 200M DÒNG (CV 835/QLT)
echo ===================================================================
echo Công cụ: common/data_gen/gen_bhyt.py (Numba Engine)
echo.
echo Nhập số người tham gia BHYT cần sinh:
echo   [1] 20.000 người  (Chạy thử nghiệm nhanh, ~200k dòng thẻ)
echo   [2] 200.000 người (Mẫu trung bình, ~2 triệu dòng thẻ)
echo   [3] 20.000.000 người (Quy mô chuẩn đồ án, ~200 triệu dòng thẻ)
echo.
set /p opt="Nhập lựa chọn (1, 2 hoặc 3, mặc định 1): "
if "%opt%"=="" set opt=1

set PERSONS=20000
set CHUNK=10000
if "%opt%"=="2" (
    set PERSONS=200000
    set CHUNK=50000
)
if "%opt%"=="3" (
    set PERSONS=20000000
    set CHUNK=100000
)

echo.
echo --- ĐANG TIẾN HÀNH SINH DỮ LIỆU (%PERSONS% người) ---
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons %PERSONS% --chunk-persons %CHUNK% --workers 4
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Sinh dữ liệu thất bại!
    pause
    exit /b 1
)

echo.
echo --- TIẾN HÀNH KIỂM TRA DỮ LIỆU VÀ XUẤT ĐÁP ÁN THAM CHIẾU ---
python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
if %ERRORLEVEL% NEQ 0 (
    echo [CẢNH BÁO] Kiểm tra dữ liệu có cảnh báo hoặc lỗi.
)

echo.
echo ===================================================================
echo [HOÀN TẤT] Dữ liệu đã được lưu tại data/bhyt_data
echo ===================================================================
pause
