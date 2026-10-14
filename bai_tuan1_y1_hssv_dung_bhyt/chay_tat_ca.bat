@echo off
chcp 65001 >nul
echo ===================================================================
echo CHẠY TOÀN BỘ WORKFLOW BÀI TUẦN 1 Ý 1 (CV 835/QLT)
echo ===================================================================
echo.
echo [1/4] Sinh dữ liệu theo Script 1 (H1-H10)...
python common/data_gen/gen_bhyt_script1.py --persons 200000 --chunk 100000 --seed 42 --out data/bhyt_data
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Sinh dữ liệu thất bại!
    pause
    exit /b 1
)

echo.
echo [2/4] Chạy Pipeline Bạn A...
python -m bai_tuan1_y1_hssv_dung_bhyt.p4_giai_phap_a_b.dev_a.pipeline_dev_a
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Pipeline Bạn A thất bại!
    pause
    exit /b 1
)

echo.
echo [3/4] Chạy Pipeline Bạn B...
python -m bai_tuan1_y1_hssv_dung_bhyt.p4_giai_phap_a_b.dev_b.pipeline_dev_b
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Pipeline Bạn B thất bại!
    pause
    exit /b 1
)

echo.
echo [4/4] Đối soát độc lập giữa Bạn A, Bạn B và Kịch bản kỳ vọng SCENARIO...
python -m bai_tuan1_y1_hssv_dung_bhyt.p5_doi_soat.compare_results
echo.
echo ===================================================================
echo HOÀN TẤT TOÀN BỘ WORKFLOW BÀI TUẦN 1 Ý 1
echo ===================================================================
pause
