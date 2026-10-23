@echo off
chcp 65001 > nul
echo =========================================================================
echo CHAY TOAN BO WORKFLOW BAI TUAN 2 Y 2 - CV 835/QLT
echo HSSV tham gia 10/2024, van tham gia 07/2026, gian doan >= 3 thang
echo =========================================================================

echo.
echo [BUOC 1/4] Chay kiem thu don vi logic chuoi thoi gian...
python -m pytest bai_tuan2_y2_hssv_gian_doan/p3_gold/test_timeline_gaps.py -v
if errorlevel 1 (
    echo [LOI] Kiem thu don vi khong dat!
    pause
    exit /b 1
)

echo.
echo [BUOC 2/4] Xay dung bao cao tang Gold Y 2 (Method Chunk)...
python -m bai_tuan2_y2_hssv_gian_doan.p3_gold.build_gold_y2 --method chunk --threads 4
if errorlevel 1 (
    echo [LOI] Build Gold Y 2 khong thanh cong!
    pause
    exit /b 1
)

echo.
echo [BUOC 3/4] Kiem tra bat bien du lieu tang Gold Y 2...
python -m pytest bai_tuan2_y2_hssv_gian_doan/p3_gold/test_gold_y2_invariants.py -v
if errorlevel 1 (
    echo [LOI] Kiem tra bat bien du lieu Gold khong dat!
    pause
    exit /b 1
)

echo.
echo [BUOC 4/4] Kiem chung doc lap SQL va doi soat...
python -m bai_tuan2_y2_hssv_gian_doan.p4_doi_soat.verify_sql_duckdb_y2
if errorlevel 1 (
    echo [LOI] Kiem chung doc lap SQL khong thanh cong!
    pause
    exit /b 1
)

echo.
echo =========================================================================
echo HOAN TAT TOAN BO WORKFLOW TUAN 2 Y 2 THANH CONG!
echo Ket qua chi tiet: data/output/gold_y2/20241001_20260731_gap3m/
echo =========================================================================
pause
