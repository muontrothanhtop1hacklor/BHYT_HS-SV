@echo off
chcp 65001 >nul
echo ===================================================================
echo CHẠY TOÀN BỘ WORKFLOW BÀI TUẦN 1 Ý 1 (CV 835/QLT)
echo ===================================================================
echo.
echo [1/3] Làm sạch dữ liệu và cách ly dòng bẩn (Tầng Silver)...
python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Xây dựng tầng Silver thất bại!
    pause
    exit /b 1
)

echo.
echo [2/3] Xây dựng Báo cáo tổng hợp tầng Gold (Phương pháp Global DuckDB SQL)...
python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Xây dựng tầng Gold thất bại!
    pause
    exit /b 1
)

echo.
echo [3/3] Đối soát kết quả độc lập (nếu có file trong ket_qua_cua_ban)...
python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results
echo.
echo ===================================================================
echo HOÀN TẤT TOÀN BỘ WORKFLOW BÀI TUẦN 1 Ý 1
echo ===================================================================
pause
