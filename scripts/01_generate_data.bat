@echo off
chcp 65001 >nul
echo ========================================================
echo BƯỚC 1: SINH DỮ LIỆU BHYT 200M DÒNG (CV 835/QLT)
echo ========================================================
echo.
echo Đang sinh 20.000.000 người (~200 triệu dòng) vào data/bhyt_data...
python scripts/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
echo.
echo ========================================================
echo BƯỚC 2: KIỂM TRA DỮ LIỆU & XUẤT ĐÁP ÁN THAM CHIẾU
echo ========================================================
python scripts/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
echo.
pause
