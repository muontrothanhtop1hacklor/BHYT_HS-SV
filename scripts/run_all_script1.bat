@echo off
chcp 65001 >nul
echo ===================================================================
echo CHẠY TOÀN BỘ WORKFLOW DÙNG CHUNG DỮ LIỆU SCRIPT 1
echo ===================================================================
echo.
echo [1/4] Sinh dữ liệu theo Script 1...
python scripts/gen_bhyt_script1.py --persons 200000 --chunk 100000 --seed 42 --out data/bhyt_data
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Sinh dữ liệu thất bại!
    pause
    exit /b 1
)

echo.
echo [2/4] Chạy Pipeline Bạn A...
python -c "from src.pipelines.pipeline_dev_a import run_pipeline_dev_a; run_pipeline_dev_a()"
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Pipeline Bạn A thất bại!
    pause
    exit /b 1
)

echo.
echo [3/4] Chạy Pipeline Bạn B...
python -c "from src.pipelines.pipeline_dev_b import run_pipeline_dev_b; run_pipeline_dev_b()"
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Pipeline Bạn B thất bại!
    pause
    exit /b 1
)

echo.
echo [4/4] Đối soát độc lập giữa Bạn A, Bạn B và Kịch bản kỳ vọng SCENARIO...
python -c "from src.reconciliation.compare_results import reconcile; reconcile()"
echo.
echo ===================================================================
echo HOÀN TẤT KIỂM THỬ DÙNG CHUNG DỮ LIỆU SCRIPT 1
echo ===================================================================
pause
