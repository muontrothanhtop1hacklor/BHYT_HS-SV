@echo off
chcp 65001 >nul
echo ========================================================
echo BƯỚC 1: SINH DỮ LIỆU BHYT THEO SCRIPT 1 (VÒNG ĐỜI H1-H10)
echo ========================================================
echo.
echo Đang sinh dữ liệu vào data/bhyt_data...
python scripts/gen_bhyt_script1.py --persons 200000 --chunk 100000 --seed 42 --out data/bhyt_data
echo.
echo ========================================================
echo HOÀN THÀNH SINH DỮ LIỆU SCRIPT 1
echo Kết quả gồm:
echo   - data/bhyt_data/DM_BHXH.csv & DM_BHXH.parquet
echo   - data/bhyt_data/ST_INTHE_DTL/*.parquet
echo   - data/bhyt_data/SCENARIO/*.parquet (đáp án kỳ vọng)
echo ========================================================
pause
