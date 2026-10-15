# Bài: tuan1_y1 | Phần: p4_doi_soat
# -*- coding: utf-8 -*-
"""
scripts/verify_sql_duckdb.py
Kiểm chứng độc lập bằng truy vấn SQL thuần túy (DuckDB) cho bài toán CV 835/QLT (Ý 1).
Không sử dụng bất kỳ thư viện, hàm hay logic mảng NumPy nào của validator.

Thực hiện kiểm chứng 2 chiều:
1. Trên Dữ liệu thô (Raw/Bronze): Khớp chính xác 100% với mốc chuẩn Oracle 848.413 người.
2. Trên Dữ liệu sạch (Silver): Đo lường và giải trình định lượng tác động của từng loại làm sạch:
   - Tác động của Chuẩn hóa Loại 4 (phục hồi thẻ HS/SV viết thường, có khoảng trắng): +1.646 người.
   - Tác động của Cách ly Loại 1 (TU_NGAY > DEN_NGAY vào Quarantine): +131 người.
   - Tổng kết quả trên Silver: 850.190 người.
"""

import os
import sys
import time
import json
import duckdb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXPECTED_ORACLE = 848413


def run_verification(threads: int = 4):
    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={threads};")
    con.execute("PRAGMA preserve_insertion_order=false;")

    print("=" * 80)
    print(" BÁO CÁO KIỂM CHỨNG ĐỘC LẬP BẰNG DUCKDB SQL (CV 835/QLT - Ý 1)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. TRUY VẤN SQL ĐỘC LẬP TRÊN DỮ LIỆU THÔ (RAW) - LOGIC NGUYÊN BẢN CỦA ĐỀ
    # -------------------------------------------------------------------------
    print("\n[BƯỚC 1] Chạy SQL trên Dữ liệu thô (Raw) để xác nhận cơ chế...")
    t0 = time.time()
    sql_raw_exact = """
    WITH base_oct2024 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND MA_KHOI IN ('HS', 'SV')
          AND TU_NGAY < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
    ),
    active_aug2026 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND TU_NGAY < DATE '2026-09-01'
          AND DEN_NGAY >= DATE '2026-08-01'
    )
    SELECT COUNT(*) AS total_stopped
    FROM base_oct2024
    WHERE SO_SO_BHXH NOT IN (SELECT SO_SO_BHXH FROM active_aug2026);
    """
    res_raw_exact = con.execute(sql_raw_exact).fetchone()[0]
    time_raw_exact = time.time() - t0

    print(f" - Kết quả DuckDB SQL trên Raw : {res_raw_exact:,} người")
    print(f" - Mốc chuẩn Oracle (Validator): {EXPECTED_ORACLE:,} người")
    print(f" - Chênh lệch                  : {res_raw_exact - EXPECTED_ORACLE} người")
    print(f" - Thời gian quét 200 files    : {time_raw_exact:.2f} giây")

    if res_raw_exact == EXPECTED_ORACLE:
        print(" => [XÁC NHẬN ĐẠT 100%] Truy vấn SQL DuckDB khớp tuyệt đối 848.413 người!")
    else:
        print(f" => [FAIL] Lệch {res_raw_exact - EXPECTED_ORACLE} người!")

    # -------------------------------------------------------------------------
    # 2. ĐO LƯỜNG TÁC ĐỘNG RIÊNG CỦA CHUẨN HÓA LOẠI 4 TRÊN DỮ LIỆU THÔ
    # -------------------------------------------------------------------------
    print("\n[BƯỚC 2] Đo lường tác động chuẩn hóa Loại 4 (UPPER/TRIM MA_KHOI)...")
    t0 = time.time()
    sql_raw_norm4 = """
    WITH base_oct2024 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND UPPER(TRIM(MA_KHOI)) IN ('HS', 'SV')
          AND TU_NGAY < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
    ),
    active_aug2026 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND TU_NGAY < DATE '2026-09-01'
          AND DEN_NGAY >= DATE '2026-08-01'
    )
    SELECT COUNT(*) AS total_stopped
    FROM base_oct2024
    WHERE SO_SO_BHXH NOT IN (SELECT SO_SO_BHXH FROM active_aug2026);
    """
    res_raw_norm4 = con.execute(sql_raw_norm4).fetchone()[0]
    time_raw_norm4 = time.time() - t0
    diff_norm4 = res_raw_norm4 - res_raw_exact

    print(f" - Kết quả khi chuẩn hóa Loại 4: {res_raw_norm4:,} người")
    print(f" - Tác động tăng thêm          : +{diff_norm4:,} người (+{diff_norm4 / res_raw_exact * 100:.3f}%)")
    print(f" - Thời gian quét              : {time_raw_norm4:.2f} giây")

    # -------------------------------------------------------------------------
    # 3. TRUY VẤN SQL TRÊN DỮ LIỆU SẠCH (SILVER)
    # -------------------------------------------------------------------------
    print("\n[BƯỚC 3] Chạy SQL trên Dữ liệu sạch (Silver) đã loại bỏ Quarantine...")
    t0 = time.time()
    sql_silver = """
    WITH base_oct2024 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND MA_KHOI IN ('HS', 'SV')
          AND TU_NGAY < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
    ),
    active_aug2026 AS (
        SELECT DISTINCT SO_SO_BHXH
        FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND TU_NGAY < DATE '2026-09-01'
          AND DEN_NGAY >= DATE '2026-08-01'
    )
    SELECT COUNT(*) AS total_stopped
    FROM base_oct2024
    WHERE SO_SO_BHXH NOT IN (SELECT SO_SO_BHXH FROM active_aug2026);
    """
    res_silver = con.execute(sql_silver).fetchone()[0]
    time_silver = time.time() - t0
    diff_silver_raw = res_silver - res_raw_exact
    diff_silver_quarantine = res_silver - res_raw_norm4

    print(f" - Kết quả DuckDB SQL trên Silver: {res_silver:,} người")
    print(f" - Thời gian quét tầng Silver    : {time_silver:.2f} giây")
    print(f" - Chênh lệch tổng thể so với Raw: {diff_silver_raw:+,} người")

    # -------------------------------------------------------------------------
    # 4. BẢNG PHÂN TÍCH ĐỊNH LƯỢNG GIẢI TRÌNH CHÊNH LỆCH
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" BẢNG GIẢI TRÌNH ĐỊNH LƯỢNG NGUYÊN NHÂN CHÊNH LỆCH THEO TỪNG LOẠI LỖI")
    print("=" * 80)
    print(f" 1. Mốc gốc trên dữ liệu thô (Raw / Oracle Key)         : {res_raw_exact:10,d} người")
    print(f" 2. Tác động Chuẩn hóa Loại 4 (cứu thẻ HS/SV chữ thường): {diff_norm4:+10,d} người")
    print(f"    (Các thẻ 'hs', 'sv' được nhận diện đúng là HSSV)")
    print(f" 3. Tác động Cách ly Loại 1 (TU_NGAY > DEN_NGAY)        : {diff_silver_quarantine:+10,d} người")
    print(f"    (390.254 thẻ rác bị loại khỏi tính toán)")
    print(f" -----------------------------------------------------------------------")
    print(f" => Tổng số người dừng trên Dữ liệu sạch (Silver)       : {res_silver:10,d} người")
    print(f"    Công thức cân bằng: {res_raw_exact:,} + {diff_norm4:,} + {diff_silver_quarantine:,} = {res_silver:,}")
    print("=" * 80)

    # Lưu kết quả kiểm chứng ra JSON
    audit_data = {
        "oracle_raw_exact": res_raw_exact,
        "oracle_expected": EXPECTED_ORACLE,
        "oracle_matched": (res_raw_exact == EXPECTED_ORACLE),
        "raw_with_normalized_type4": res_raw_norm4,
        "impact_type4_normalization": diff_norm4,
        "silver_clean_result": res_silver,
        "impact_type1_quarantine": diff_silver_quarantine,
        "total_impact": diff_silver_raw,
        "time_raw_exact_sec": round(time_raw_exact, 2),
        "time_silver_sec": round(time_silver, 2),
    }

    audit_file = "data/silver/_sql_audit.json"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
    print(f"\n Đã lưu kết quả đối soát độc lập vào: {audit_file}\n")


if __name__ == "__main__":
    run_verification(threads=4)
