@echo off
chcp 65001 >nul
echo ===================================================================
echo KỊCH BẢN SINH DỮ LIỆU BHYT 200M DÒNG (DÙNG CHUNG)
echo ===================================================================
echo Chọn phương thức sinh dữ liệu:
echo   [1] Sinh theo Script 1 (Vòng đời người H1-H10, kiểm chứng SCENARIO)
echo   [2] Sinh theo Script 2 (Numba + 20 triệu người ~200M thẻ, kiểm chứng CV 835)
echo.
set /p opt="Nhập lựa chọn (1 hoặc 2, mặc định 1): "
if "%opt%"=="" set opt=1

if "%opt%"=="1" (
    echo.
    echo --- ĐANG CHẠY SCRIPT 1 ---
    python common/data_gen/gen_bhyt_script1.py --persons 200000 --chunk 100000 --seed 42 --out data/bhyt_data
    if %ERRORLEVEL% NEQ 0 (
        echo [LỖI] Sinh dữ liệu Script 1 thất bại!
        pause
        exit /b 1
    )
    echo.
    echo [HOÀN TẤT SCRIPT 1] Dữ liệu đã lưu tại data/bhyt_data:
    echo   - DM_BHXH.csv & DM_BHXH.parquet
    echo   - ST_INTHE_DTL/*.parquet
    echo   - SCENARIO/*.parquet
) else (
    echo.
    echo --- ĐANG CHẠY SCRIPT 2 (20M người ~ 200M dòng) ---
    python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
    if %ERRORLEVEL% NEQ 0 (
        echo [LỖI] Sinh dữ liệu Script 2 thất bại!
        pause
        exit /b 1
    )
    echo.
    echo --- KIỂM TRA DỮ LIỆU VÀ XUẤT ĐÁP ÁN THAM CHIẾU ---
    python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
)

echo ===================================================================
pause
