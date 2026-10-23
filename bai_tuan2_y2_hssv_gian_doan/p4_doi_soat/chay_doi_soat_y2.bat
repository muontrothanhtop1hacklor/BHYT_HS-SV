@echo off
chcp 65001 > nul
echo =========================================================================
echo DOI SOAT VA KIEM CHUNG BAI TOAN Y 2 - CV 835/QLT
echo =========================================================================

echo [1/2] Kiem chung doc lap bang truy van DuckDB SQL thuan tuy...
python -m bai_tuan2_y2_hssv_gian_doan.p4_doi_soat.verify_sql_duckdb_y2
if errorlevel 1 (
    echo [LOI] Kiem chung SQL khong thanh cong!
    pause
    exit /b 1
)

echo.
echo [2/2] Doi soat ket qua voi file cua ban cung lam...
python -m bai_tuan2_y2_hssv_gian_doan.p4_doi_soat.compare_results_y2

echo.
echo =========================================================================
echo HOAN TAT DOI SOAT Y 2
echo =========================================================================
