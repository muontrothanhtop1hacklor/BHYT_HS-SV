# -*- coding: utf-8 -*-
"""
scripts/build_gold.py
Xây dựng tầng Gold cho bài toán CV 835/QLT (Ý 1: HSSV dừng tham gia BHYT).

Đầu ra gồm 2 bảng chuẩn DDL (sql/ddl/03_output_tables.sql):
1. BC_HSSV_DUNG_THAM_GIA: Chi tiết từng cá nhân HSSV dừng tham gia
2. TK_DBHC_HSSV_DUNG_THAM_GIA: Tổng hợp theo 63 tỉnh/thành phố (quy đổi qua DM_BHXH)

Tính năng:
- Hỗ trợ tham số hóa toàn diện: base_start, chk_start, stop_def ('any' | 'hssv').
- Hỗ trợ 2 cách tính để benchmark công bằng:
  + Cách 1 (chunk): Chunk-based đa luồng (dựa vào cấu trúc dữ liệu người-trong-chunk)
  + Cách 2 (global): Global DuckDB SQL (tổng quát, không dựa vào phân vùng chunk)
- Cơ chế ghi Atomic, Idempotent và tính SHA-256 checksum so sánh.
- Giám sát RAM RSS cây tiến trình cha+con bằng psutil.
"""

import os
import sys
import time
import glob
import json
import hashlib
from datetime import datetime, date
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import os
import sys

# Đảm bảo import được module từ thư mục gốc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Đảm bảo UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.utils.resource_monitor import ProcessTreeMemoryMonitor


def get_file_sha256(filepath: str) -> str:
    """Tính mã băm SHA-256 của file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_gold_global(
    silver_pattern: str,
    dm_bhxh_path: str,
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-08-01",
    chk_next: str = "2026-09-01",
    report_date: str = "2026-08-10",
    stop_def: str = "any",
    threads: int = 4,
):
    """
    Cách 2: Tính Gold tổng quát bằng DuckDB SQL.
    Không phụ thuộc vào giả định mọi thẻ của 1 người nằm trong 1 chunk.
    """
    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={threads};")
    con.execute("PRAGMA preserve_insertion_order=false;")

    chk_filter = "TRANG_THAI = 1"
    if stop_def == "hssv":
        chk_filter += " AND MA_KHOI IN ('HS', 'SV')"

    sql = f"""
    -- 1. Tập thẻ hợp lệ giao tháng gốc của HSSV
    CREATE TEMPORARY TABLE base_cards AS
    SELECT
        SO_SO_BHXH,
        HO_TEN,
        NGAY_SINH,
        GIOI_TINH,
        SO_CMND,
        SO_THE_KCB AS SO_THE_KCB_GOC,
        MA_KHOI AS MA_KHOI_GOC,
        TU_NGAY AS TU_NGAY_GOC,
        DEN_NGAY AS DEN_NGAY_GOC,
        DM_BHXH_ID,
        MA_TINH,
        -- Điểm ưu tiên: SV ưu tiên hơn HS, DEN_NGAY lớn hơn ưu tiên hơn
        CASE WHEN MA_KHOI = 'SV' THEN 2 ELSE 1 END AS PRIORITY_SCORE
    FROM read_parquet('{silver_pattern}')
    WHERE TRANG_THAI = 1
      AND MA_KHOI IN ('HS', 'SV')
      AND TU_NGAY < DATE '{base_next}'
      AND DEN_NGAY >= DATE '{base_start}';

    -- 2. Tập người còn tham gia tại tháng kiểm tra
    CREATE TEMPORARY TABLE active_chk AS
    SELECT DISTINCT SO_SO_BHXH
    FROM read_parquet('{silver_pattern}')
    WHERE {chk_filter}
      AND TU_NGAY < DATE '{chk_next}'
      AND DEN_NGAY >= DATE '{chk_start}';

    -- 3. Chọn 1 thẻ đại diện duy nhất cho mỗi cá nhân dừng tham gia
    CREATE TEMPORARY TABLE bc_raw AS
    WITH ranked_cards AS (
        SELECT
            b.*,
            ROW_NUMBER() OVER (
                PARTITION BY b.SO_SO_BHXH
                ORDER BY b.PRIORITY_SCORE DESC, b.DEN_NGAY_GOC DESC, b.SO_THE_KCB_GOC ASC
            ) AS rn
        FROM base_cards b
        WHERE b.SO_SO_BHXH NOT IN (SELECT a.SO_SO_BHXH FROM active_chk a)
    )
    SELECT
        CAST(SO_SO_BHXH AS VARCHAR(10)) AS SO_SO_BHXH,
        CAST(HO_TEN AS VARCHAR(100)) AS HO_TEN,
        CAST(NGAY_SINH AS DATE) AS NGAY_SINH,
        CAST(GIOI_TINH AS SMALLINT) AS GIOI_TINH,
        CAST(SO_CMND AS VARCHAR(12)) AS SO_CMND,
        CAST(SO_THE_KCB_GOC AS VARCHAR(15)) AS SO_THE_KCB_GOC,
        CAST(MA_KHOI_GOC AS VARCHAR(10)) AS MA_KHOI_GOC,
        CAST(TU_NGAY_GOC AS DATE) AS TU_NGAY_GOC,
        CAST(DEN_NGAY_GOC AS DATE) AS DEN_NGAY_GOC,
        CAST(DM_BHXH_ID AS INTEGER) AS DM_BHXH_ID,
        CAST(MA_TINH AS VARCHAR(20)) AS MA_TINH,
        DATE '{base_start}' AS NGAY_GOC,
        DATE '{report_date}' AS NGAY_KIEM_TRA,
        CAST('{report_date} 08:00:00' AS TIMESTAMP) AS CREATED_AT
    FROM ranked_cards
    WHERE rn = 1
    ORDER BY SO_SO_BHXH ASC;

    -- 4. Bảng danh mục 63 tỉnh chuẩn
    CREATE TEMPORARY TABLE dm_tinh AS
    SELECT
        CAST(MA_DVI AS VARCHAR(20)) AS MA_TINH,
        CAST(TEN_DVI AS VARCHAR(200)) AS TEN_TINH
    FROM read_parquet('{dm_bhxh_path}')
    WHERE MA_CHA IS NULL OR MA_CHA = '';

    -- Bảng ánh xạ từ DM_BHXH_ID ra MA_TINH_QUY_DOI
    CREATE TEMPORARY TABLE dm_mapping AS
    SELECT
        ID AS DM_BHXH_ID,
        CAST(COALESCE(NULLIF(MA_CHA, ''), MA_DVI) AS VARCHAR(20)) AS MA_TINH_QUY_DOI
    FROM read_parquet('{dm_bhxh_path}');

    -- 5. Bảng thống kê địa bàn hành chính TK_DBHC
    CREATE TEMPORARY TABLE tk_raw AS
    WITH person_prov AS (
        SELECT
            bc.SO_SO_BHXH,
            bc.MA_KHOI_GOC,
            COALESCE(m.MA_TINH_QUY_DOI, LPAD(CAST(bc.MA_TINH AS VARCHAR), 2, '0')) AS MA_TINH_FINAL
        FROM bc_raw bc
        LEFT JOIN dm_mapping m ON bc.DM_BHXH_ID = m.DM_BHXH_ID
    ),
    agg_prov AS (
        SELECT
            MA_TINH_FINAL,
            COUNT(CASE WHEN MA_KHOI_GOC = 'HS' THEN 1 END) AS SO_LUONG_HS_DUNG,
            COUNT(CASE WHEN MA_KHOI_GOC = 'SV' THEN 1 END) AS SO_LUONG_SV_DUNG,
            COUNT(*) AS TONG_SO_NGUOI_DUNG
        FROM person_prov
        GROUP BY MA_TINH_FINAL
    )
    SELECT
        t.MA_TINH,
        t.TEN_TINH,
        COALESCE(a.SO_LUONG_HS_DUNG, 0) AS SO_LUONG_HS_DUNG,
        COALESCE(a.SO_LUONG_SV_DUNG, 0) AS SO_LUONG_SV_DUNG,
        COALESCE(a.TONG_SO_NGUOI_DUNG, 0) AS TONG_SO_NGUOI_DUNG,
        DATE '{report_date}' AS NGAY_BAO_CAO
    FROM dm_tinh t
    LEFT JOIN agg_prov a ON t.MA_TINH = a.MA_TINH_FINAL
    ORDER BY t.MA_TINH ASC;
    """

    con.execute(sql)
    df_bc = con.execute("SELECT * FROM bc_raw").df()
    df_tk = con.execute("SELECT * FROM tk_raw").df()

    return df_bc, df_tk


def compute_gold_chunk(
    silver_dir: str,
    dm_bhxh_path: str,
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-08-01",
    chk_next: str = "2026-09-01",
    report_date: str = "2026-08-10",
    stop_def: str = "any",
    threads: int = 4,
):
    """
    Cách 1: Tính Gold theo chunk (Chunk-based).
    Tận dụng giả định dữ liệu sinh: mọi thẻ của 1 người nằm cùng 1 chunk.
    Xử lý song song từng chunk bằng DuckDB rồi gộp.
    """
    silver_files = sorted(glob.glob(os.path.join(silver_dir, "part-*.parquet")))
    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={threads};")

    chk_filter = "TRANG_THAI = 1"
    if stop_def == "hssv":
        chk_filter += " AND MA_KHOI IN ('HS', 'SV')"

    # Đọc dm_bhxh
    con.execute(f"""
    CREATE TEMPORARY TABLE dm_tinh AS
    SELECT
        CAST(MA_DVI AS VARCHAR(20)) AS MA_TINH,
        CAST(TEN_DVI AS VARCHAR(200)) AS TEN_TINH
    FROM read_parquet('{dm_bhxh_path}')
    WHERE MA_CHA IS NULL OR MA_CHA = '';

    CREATE TEMPORARY TABLE dm_mapping AS
    SELECT
        ID AS DM_BHXH_ID,
        CAST(COALESCE(NULLIF(MA_CHA, ''), MA_DVI) AS VARCHAR(20)) AS MA_TINH_QUY_DOI
    FROM read_parquet('{dm_bhxh_path}');
    """)

    # Quét từng chunk và gộp vào bảng tạm
    con.execute("""
    CREATE TEMPORARY TABLE all_stopped_persons (
        SO_SO_BHXH VARCHAR(10),
        HO_TEN VARCHAR(100),
        NGAY_SINH DATE,
        GIOI_TINH SMALLINT,
        SO_CMND VARCHAR(12),
        SO_THE_KCB_GOC VARCHAR(15),
        MA_KHOI_GOC VARCHAR(10),
        TU_NGAY_GOC DATE,
        DEN_NGAY_GOC DATE,
        DM_BHXH_ID INTEGER,
        MA_TINH VARCHAR(20),
        NGAY_GOC DATE,
        NGAY_KIEM_TRA DATE,
        CREATED_AT TIMESTAMP
    );
    """)

    for fpath in silver_files:
        con.execute(f"""
        INSERT INTO all_stopped_persons
        WITH base_cards AS (
            SELECT
                SO_SO_BHXH,
                HO_TEN,
                NGAY_SINH,
                GIOI_TINH,
                SO_CMND,
                SO_THE_KCB AS SO_THE_KCB_GOC,
                MA_KHOI AS MA_KHOI_GOC,
                TU_NGAY AS TU_NGAY_GOC,
                DEN_NGAY AS DEN_NGAY_GOC,
                DM_BHXH_ID,
                MA_TINH,
                CASE WHEN MA_KHOI = 'SV' THEN 2 ELSE 1 END AS PRIORITY_SCORE
            FROM read_parquet('{fpath}')
            WHERE TRANG_THAI = 1
              AND MA_KHOI IN ('HS', 'SV')
              AND TU_NGAY < DATE '{base_next}'
              AND DEN_NGAY >= DATE '{base_start}'
        ),
        active_chk AS (
            SELECT DISTINCT SO_SO_BHXH
            FROM read_parquet('{fpath}')
            WHERE {chk_filter}
              AND TU_NGAY < DATE '{chk_next}'
              AND DEN_NGAY >= DATE '{chk_start}'
        ),
        ranked_cards AS (
            SELECT
                b.*,
                ROW_NUMBER() OVER (
                    PARTITION BY b.SO_SO_BHXH
                    ORDER BY b.PRIORITY_SCORE DESC, b.DEN_NGAY_GOC DESC, b.SO_THE_KCB_GOC ASC
                ) AS rn
            FROM base_cards b
            WHERE b.SO_SO_BHXH NOT IN (SELECT a.SO_SO_BHXH FROM active_chk a)
        )
        SELECT
            CAST(SO_SO_BHXH AS VARCHAR(10)),
            CAST(HO_TEN AS VARCHAR(100)),
            CAST(NGAY_SINH AS DATE),
            CAST(GIOI_TINH AS SMALLINT),
            CAST(SO_CMND AS VARCHAR(12)),
            CAST(SO_THE_KCB_GOC AS VARCHAR(15)),
            CAST(MA_KHOI_GOC AS VARCHAR(10)),
            CAST(TU_NGAY_GOC AS DATE),
            CAST(DEN_NGAY_GOC AS DATE),
            CAST(DM_BHXH_ID AS INTEGER),
            CAST(MA_TINH AS VARCHAR(20)),
            DATE '{base_start}',
            DATE '{report_date}',
            CAST('{report_date} 08:00:00' AS TIMESTAMP)
        FROM ranked_cards
        WHERE rn = 1;
        """)

    df_bc = con.execute("SELECT * FROM all_stopped_persons ORDER BY SO_SO_BHXH ASC").df()

    # Tính TK_DBHC
    sql_tk = f"""
    WITH person_prov AS (
        SELECT
            bc.SO_SO_BHXH,
            bc.MA_KHOI_GOC,
            COALESCE(m.MA_TINH_QUY_DOI, LPAD(CAST(bc.MA_TINH AS VARCHAR), 2, '0')) AS MA_TINH_FINAL
        FROM all_stopped_persons bc
        LEFT JOIN dm_mapping m ON bc.DM_BHXH_ID = m.DM_BHXH_ID
    ),
    agg_prov AS (
        SELECT
            MA_TINH_FINAL,
            COUNT(CASE WHEN MA_KHOI_GOC = 'HS' THEN 1 END) AS SO_LUONG_HS_DUNG,
            COUNT(CASE WHEN MA_KHOI_GOC = 'SV' THEN 1 END) AS SO_LUONG_SV_DUNG,
            COUNT(*) AS TONG_SO_NGUOI_DUNG
        FROM person_prov
        GROUP BY MA_TINH_FINAL
    )
    SELECT
        t.MA_TINH,
        t.TEN_TINH,
        COALESCE(a.SO_LUONG_HS_DUNG, 0) AS SO_LUONG_HS_DUNG,
        COALESCE(a.SO_LUONG_SV_DUNG, 0) AS SO_LUONG_SV_DUNG,
        COALESCE(a.TONG_SO_NGUOI_DUNG, 0) AS TONG_SO_NGUOI_DUNG,
        DATE '{report_date}' AS NGAY_BAO_CAO
    FROM dm_tinh t
    LEFT JOIN agg_prov a ON t.MA_TINH = a.MA_TINH_FINAL
    ORDER BY t.MA_TINH ASC;
    """
    df_tk = con.execute(sql_tk).df()
    return df_bc, df_tk


def save_gold_atomic(
    df_bc: pd.DataFrame,
    df_tk: pd.DataFrame,
    out_dir: str,
) -> dict:
    """
    Ghi dữ liệu Gold an toàn theo cơ chế Atomic Rename:
    - Ghi vào thư mục tạm .tmp_{timestamp}
    - Đổi tên atomic sang thư mục đích
    - Tính mã băm SHA-256 các file
    """
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)
    tmp_out_dir = out_dir + f".tmp_{int(time.time()*1000)}"
    os.makedirs(tmp_out_dir, exist_ok=True)

    bc_parquet_tmp = os.path.join(tmp_out_dir, "bc_hssv_dung_tham_gia.parquet")
    tk_csv_tmp = os.path.join(tmp_out_dir, "tk_dbhc_hssv_dung_tham_gia.csv")
    tk_parquet_tmp = os.path.join(tmp_out_dir, "tk_dbhc_hssv_dung_tham_gia.parquet")

    # Sắp xếp ổn định để đảm bảo tính Idempotent trùng checksum SHA-256
    df_bc = df_bc.sort_values("SO_SO_BHXH").reset_index(drop=True)
    df_tk = df_tk.sort_values("MA_TINH").reset_index(drop=True)

    # 1. Ghi BC Parquet (nén zstd)
    table_bc = pa.Table.from_pandas(df_bc, preserve_index=False)
    pq.write_table(table_bc, bc_parquet_tmp, compression="zstd", compression_level=1)

    # 2. Ghi TK CSV & Parquet
    df_tk.to_csv(tk_csv_tmp, index=False, encoding="utf-8")
    table_tk = pa.Table.from_pandas(df_tk, preserve_index=False)
    pq.write_table(table_tk, tk_parquet_tmp, compression="zstd", compression_level=1)

    # Hoán đổi atomic
    if os.path.exists(out_dir):
        # Trên Windows, nếu out_dir đã tồn tại, xóa bản cũ trước khi rename
        import shutil
        shutil.rmtree(out_dir)
    os.rename(tmp_out_dir, out_dir)

    bc_parquet = os.path.join(out_dir, "bc_hssv_dung_tham_gia.parquet")
    tk_csv = os.path.join(out_dir, "tk_dbhc_hssv_dung_tham_gia.csv")
    tk_parquet = os.path.join(out_dir, "tk_dbhc_hssv_dung_tham_gia.parquet")

    sha_bc = get_file_sha256(bc_parquet)
    sha_tk_csv = get_file_sha256(tk_csv)
    sha_tk_pq = get_file_sha256(tk_parquet)

    return {
        "bc_rows": len(df_bc),
        "tk_rows": len(df_tk),
        "bc_parquet_path": bc_parquet,
        "tk_csv_path": tk_csv,
        "tk_parquet_path": tk_parquet,
        "sha256_bc_parquet": sha_bc,
        "sha256_tk_csv": sha_tk_csv,
        "sha256_tk_parquet": sha_tk_pq,
        "bc_size_mb": round(os.path.getsize(bc_parquet) / (1024**2), 2),
        "tk_size_kb": round(os.path.getsize(tk_csv) / 1024, 2),
    }


def run_gold_pipeline(
    silver_dir: str = "data/silver/st_inthe_dtl",
    dm_bhxh_path: str = "data/bhyt_data/dm_bhxh.parquet",
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-08-01",
    chk_next: str = "2026-09-01",
    report_date: str = "2026-08-10",
    stop_def: str = "any",
    method: str = "both",
    threads: int = 4,
    base_out_dir: str = "data/output/gold",
):
    # --- PRE-FLIGHT VALIDATION (Kịch bản lỗi) ---
    if stop_def not in ("any", "hssv"):
        raise ValueError(f"Tham số stop_def='{stop_def}' không hợp lệ! Chỉ chấp nhận 'any' hoặc 'hssv'.")

    if base_start >= base_next:
        raise ValueError(f"Mốc thời gian gốc không hợp lệ: base_start ({base_start}) >= base_next ({base_next})!")

    if chk_start >= chk_next:
        raise ValueError(f"Mốc thời gian kiểm tra không hợp lệ: chk_start ({chk_start}) >= chk_next ({chk_next})!")

    if not os.path.exists(dm_bhxh_path):
        raise FileNotFoundError(f"Không tìm thấy file danh mục BHXH tại: {dm_bhxh_path}")

    silver_files = glob.glob(os.path.join(silver_dir, "part-*.parquet"))
    if not silver_files:
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu Silver Parquet nào trong: {silver_dir}")

    print("=" * 80)
    print(" KHỞI CHẠY PIPELINE TẦNG GOLD (CV 835/QLT - Ý 1)")
    print("=" * 80)
    print(f" Mốc gốc (base)       : {base_start} -> {base_next}")
    print(f" Mốc kiểm tra (chk)   : {chk_start} -> {chk_next}")
    print(f" Ngày báo cáo         : {report_date}")
    print(f" Định nghĩa dừng      : {stop_def}")
    print(f" Phương pháp tính     : {method}")
    print(f" Số luồng xử lý       : {threads}")
    print(f" Số chunks Silver     : {len(silver_files)}")
    print("-" * 80)
    print(f" Số luồng xử lý       : {threads}")
    print("-" * 80)

    # Khóa thư mục theo bộ tham số: YYYYMMDD_YYYYMMDD_stopdef
    param_tag = f"{base_start.replace('-', '')}_{chk_start.replace('-', '')}_{stop_def}"
    out_dir = os.path.join(base_out_dir, param_tag)
    silver_pattern = os.path.join(silver_dir, "part-*.parquet")

    results_benchmark = {}

    # 1. Chạy Cách 2: Global DuckDB SQL
    if method in ("global", "both"):
        print("\n--- [CÁCH 2: GLOBAL DUCKDB SQL (Không dựa vào giả định chunk)] ---")
        mon = ProcessTreeMemoryMonitor(interval_sec=0.1)
        mon.start()
        t0 = time.time()

        df_bc_global, df_tk_global = compute_gold_global(
            silver_pattern=silver_pattern,
            dm_bhxh_path=dm_bhxh_path,
            base_start=base_start,
            base_next=base_next,
            chk_start=chk_start,
            chk_next=chk_next,
            report_date=report_date,
            stop_def=stop_def,
            threads=threads,
        )

        el_global = time.time() - t0
        mem_global = mon.stop()

        print(f" Thời gian thực thi    : {el_global:.2f} giây")
        print(f" Số dòng BC_HSSV_...   : {len(df_bc_global):,}")
        print(f" Số tỉnh TK_DBHC_...   : {len(df_tk_global)}")
        print(f" RAM nền hệ thống      : {mem_global['baseline_sys_used_gb']} GB")
        print(f" RAM đỉnh hệ thống     : {mem_global['peak_sys_used_gb']} GB")
        print(f" RSS đỉnh cây tiến trình: {mem_global['peak_process_tree_rss_mb']} MB ({mem_global['peak_process_tree_rss_gb']} GB)")

        results_benchmark["global"] = {
            "elapsed_sec": round(el_global, 2),
            "bc_rows": len(df_bc_global),
            "tk_rows": len(df_tk_global),
            "peak_rss_mb": mem_global["peak_process_tree_rss_mb"],
            "peak_sys_gb": mem_global["peak_sys_used_gb"],
        }

    # 2. Chạy Cách 1: Chunk-based
    if method in ("chunk", "both"):
        print("\n--- [CÁCH 1: CHUNK-BASED (Dựa vào giả định mọi thẻ 1 người trong 1 chunk)] ---")
        mon = ProcessTreeMemoryMonitor(interval_sec=0.1)
        mon.start()
        t0 = time.time()

        df_bc_chunk, df_tk_chunk = compute_gold_chunk(
            silver_dir=silver_dir,
            dm_bhxh_path=dm_bhxh_path,
            base_start=base_start,
            base_next=base_next,
            chk_start=chk_start,
            chk_next=chk_next,
            report_date=report_date,
            stop_def=stop_def,
            threads=threads,
        )

        el_chunk = time.time() - t0
        mem_chunk = mon.stop()

        print(f" Thời gian thực thi    : {el_chunk:.2f} giây")
        print(f" Số dòng BC_HSSV_...   : {len(df_bc_chunk):,}")
        print(f" Số tỉnh TK_DBHC_...   : {len(df_tk_chunk)}")
        print(f" RAM nền hệ thống      : {mem_chunk['baseline_sys_used_gb']} GB")
        print(f" RAM đỉnh hệ thống     : {mem_chunk['peak_sys_used_gb']} GB")
        print(f" RSS đỉnh cây tiến trình: {mem_chunk['peak_process_tree_rss_mb']} MB ({mem_chunk['peak_process_tree_rss_gb']} GB)")

        results_benchmark["chunk"] = {
            "elapsed_sec": round(el_chunk, 2),
            "bc_rows": len(df_bc_chunk),
            "tk_rows": len(df_tk_chunk),
            "peak_rss_mb": mem_chunk["peak_process_tree_rss_mb"],
            "peak_sys_gb": mem_chunk["peak_sys_used_gb"],
        }

    # 3. So khớp đối chiếu 2 cách tính
    if method == "both":
        print("\n" + "=" * 80)
        print(" ĐỐI SOÁT TÍNH ĐÚNG ĐẮN GIỮA HAI CÁCH TÍNH (CHUNK vs GLOBAL)")
        print("=" * 80)
        diff_bc_len = abs(len(df_bc_global) - len(df_bc_chunk))
        diff_tk_len = abs(len(df_tk_global) - len(df_tk_chunk))

        # Sắp xếp ổn định trước khi so khớp chi tiết
        df_bc_global_sorted = df_bc_global.sort_values("SO_SO_BHXH").reset_index(drop=True)
        df_bc_chunk_sorted = df_bc_chunk.sort_values("SO_SO_BHXH").reset_index(drop=True)
        df_tk_global_sorted = df_tk_global.sort_values("MA_TINH").reset_index(drop=True)
        df_tk_chunk_sorted = df_tk_chunk.sort_values("MA_TINH").reset_index(drop=True)

        bc_match = df_bc_global_sorted["SO_SO_BHXH"].equals(df_bc_chunk_sorted["SO_SO_BHXH"])
        tk_match = df_tk_global_sorted["TONG_SO_NGUOI_DUNG"].equals(df_tk_chunk_sorted["TONG_SO_NGUOI_DUNG"])

        print(f" - Khớp số lượng dòng BC  : {len(df_bc_global):,} == {len(df_bc_chunk):,} (Lệch: {diff_bc_len})")
        print(f" - Khớp chi tiết mã BHXH  : {'100% TRÙNG KHỚP' if bc_match else 'KHÔNG KHỚP'}")
        print(f" - Khớp tổng số người tỉnh: {'100% TRÙNG KHỚP' if tk_match else 'KHÔNG KHỚP'}")

        if bc_match and tk_match:
            print(" => [PASS] Hai phương pháp tính độc lập cho kết quả GIỐNG NHAU HOÀN TOÀN!")
        else:
            print(" => [FAIL] Có sự sai lệch giữa hai cách tính!")

    # 4. Ghi file kết quả Atomic & Idempotent
    print("\n--- [GHI KẾT QUẢ ĐẦU RA TẦNG GOLD (ATOMIC RENAME)] ---")
    df_bc_final = df_bc_global if method in ("global", "both") else df_bc_chunk
    df_tk_final = df_tk_global if method in ("global", "both") else df_tk_chunk

    meta_save = save_gold_atomic(df_bc_final, df_tk_final, out_dir)
    print(f" Thư mục đích         : {out_dir}")
    print(f" BC Parquet           : {meta_save['bc_parquet_path']} ({meta_save['bc_size_mb']} MB)")
    print(f" SHA-256 BC Parquet   : {meta_save['sha256_bc_parquet']}")
    print(f" TK CSV               : {meta_save['tk_csv_path']} ({meta_save['tk_size_kb']} KB)")
    print(f" SHA-256 TK CSV       : {meta_save['sha256_tk_csv']}")

    # 5. Lưu manifest
    manifest_gold = {
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "base_start": base_start,
            "base_next": base_next,
            "chk_start": chk_start,
            "chk_next": chk_next,
            "report_date": report_date,
            "stop_def": stop_def,
        },
        "output_files": meta_save,
        "benchmarks": results_benchmark,
    }

    manifest_path = os.path.join(out_dir, "_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_gold, mf, indent=2, ensure_ascii=False)
    print(f" File Manifest        : {manifest_path}")
    print("=" * 80)

    return manifest_gold


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Gold layer for BHYT dataset")
    parser.add_argument("--silver", default="data/silver/st_inthe_dtl", help="Silver directory")
    parser.add_argument("--dm-bhxh", default="data/bhyt_data/dm_bhxh.parquet", help="DM_BHXH parquet path")
    parser.add_argument("--base-start", default="2024-10-01", help="Base month start date")
    parser.add_argument("--base-next", default="2024-11-01", help="Base next month start date")
    parser.add_argument("--chk-start", default="2026-08-01", help="Check month start date")
    parser.add_argument("--chk-next", default="2026-09-01", help="Check next month start date")
    parser.add_argument("--report-date", default="2026-08-10", help="Report dispatch date")
    parser.add_argument("--stop-def", default="any", choices=["any", "hssv"], help="Stopped definition")
    parser.add_argument("--method", default="both", choices=["chunk", "global", "both"], help="Computation method")
    parser.add_argument("--threads", type=int, default=4, help="DuckDB threads")
    parser.add_argument("--out-dir", default="data/output/gold", help="Output base directory")
    args = parser.parse_args()

    run_gold_pipeline(
        silver_dir=args.silver,
        dm_bhxh_path=args.dm_bhxh,
        base_start=args.base_start,
        base_next=args.base_next,
        chk_start=args.chk_start,
        chk_next=args.chk_next,
        report_date=args.report_date,
        stop_def=args.stop_def,
        method=args.method,
        threads=args.threads,
        base_out_dir=args.out_dir,
    )
