# -*- coding: utf-8 -*-
"""
build_gold_y2.py
Xây dựng tầng Gold cho bài toán CV 835/QLT (Ý 2: HSSV gián đoạn BHYT >= 3 tháng).

Lệnh chạy mẫu:
  python -m bai_tuan2_y2_hssv_gian_doan.p3_gold.build_gold_y2 --method chunk --threads 4
  python -m bai_tuan2_y2_hssv_gian_doan.p3_gold.build_gold_y2 --method global --threads 4
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import threading
import time
from datetime import date
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import duckdb
import psutil
import pyarrow.parquet as pq

# Import cấu hình chung
from common.config import (
    DM_BHXH_FILE,
    GOLD_Y2_RESULT_DIR,
    GOLD_Y2_BC_FILE,
    GOLD_Y2_TK_CSV,
    MIN_GAP_DAYS_Y2,
    NGAY_DAU_THANG_GOC,
    NGAY_DAU_THANG_SAU_GOC,
    NGAY_DAU_THANG_KIEM_TRA_Y2,
    NGAY_DAU_THANG_SAU_KIEM_TRA_Y2,
    NGAY_CUOI_THANG_KIEM_TRA_Y2,
    NGAY_KIEM_TRA,
    DATA_DIR,
)
from bai_tuan2_y2_hssv_gian_doan.p3_gold.gold_logic_y2 import build_gold_y2_sql


class MemoryMonitor:
    """Theo dõi mức chiếm dụng RAM hệ thống và Process Tree định kỳ."""
    def __init__(self, interval_sec: float = 0.5):
        self.interval = interval_sec
        self.stop_event = threading.Event()
        self.thread = None
        self.peak_process_tree_rss_bytes = 0
        self.baseline_sys_used_bytes = 0
        self.peak_sys_used_bytes = 0
        self.baseline_sys_total_bytes = 0

    def _get_tree_rss(self) -> int:
        try:
            parent = psutil.Process(os.getpid())
            total_rss = parent.memory_info().rss
            for child in parent.children(recursive=True):
                try:
                    total_rss += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return total_rss
        except Exception:
            return 0

    def _monitor(self):
        while not self.stop_event.is_set():
            vm = psutil.virtual_memory()
            if vm.used > self.peak_sys_used_bytes:
                self.peak_sys_used_bytes = vm.used
            rss = self._get_tree_rss()
            if rss > self.peak_process_tree_rss_bytes:
                self.peak_process_tree_rss_bytes = rss
            time.sleep(self.interval)

    def start(self):
        vm = psutil.virtual_memory()
        self.baseline_sys_total_bytes = vm.total
        self.baseline_sys_used_bytes = vm.used
        self.peak_sys_used_bytes = vm.used
        self.peak_process_tree_rss_bytes = self._get_tree_rss()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self) -> dict:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        final_rss = self._get_tree_rss()
        if final_rss > self.peak_process_tree_rss_bytes:
            self.peak_process_tree_rss_bytes = final_rss
        return {
            "baseline_sys_used_gb": round(self.baseline_sys_used_bytes / (1024**3), 2),
            "baseline_sys_total_gb": round(self.baseline_sys_total_bytes / (1024**3), 2),
            "peak_sys_used_gb": round(self.peak_sys_used_bytes / (1024**3), 2),
            "peak_process_tree_rss_mb": round(self.peak_process_tree_rss_bytes / (1024**2), 2),
            "peak_process_tree_rss_gb": round(self.peak_process_tree_rss_bytes / (1024**3), 3),
        }


def get_file_sha256(filepath: str) -> str:
    """Tính mã băm SHA-256 của file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_gold_y2_chunk(
    silver_dir: str,
    dm_path: str,
    out_dir: Path,
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-07-01",
    chk_next: str = "2026-08-01",
    window_start: str = "2024-10-01",
    window_end: str = "2026-07-31",
    min_gap_days: int = 90,
    report_date: str = "2026-08-10",
    threads: int = 4,
) -> dict:
    """
    Xử lý tầng Gold Ý 2 theo từng chunk:
    Tận dụng bất biến toàn vẹn: mọi thẻ của 1 người nằm trong 1 chunk.
    Duyệt từng chunk để giảm mức dùng bộ nhớ; RAM thực tế phụ thuộc kích thước chunk,
    dữ liệu và cấu hình DuckDB/máy chạy, không được bảo đảm dưới một ngưỡng cố định.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    bc_file = out_dir / "bc_hssv_gian_doan_bhyt.parquet"
    tk_file = out_dir / "tk_dbhc_hssv_gian_doan_bhyt.csv"

    silver_files = sorted(glob.glob(os.path.join(silver_dir, "part-*.parquet")))
    if not silver_files:
        silver_files = sorted(glob.glob(os.path.join(silver_dir, "*.parquet")))

    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={threads};")
    con.execute("PRAGMA preserve_insertion_order=false;")

    dm_read_sql = (
        f"read_csv_auto('{dm_path}')"
        if str(dm_path).endswith(".csv")
        else f"read_parquet('{dm_path}')"
    )

    con.execute(f"""
    CREATE TEMPORARY TABLE dm_tinh AS
    SELECT
        CAST(MA_DVI AS VARCHAR(20)) AS MA_TINH,
        CAST(TEN_DVI AS VARCHAR(200)) AS TEN_TINH
    FROM {dm_read_sql}
    WHERE MA_CHA IS NULL OR MA_CHA = '' OR MA_CHA = '00';

    CREATE TEMPORARY TABLE dm_mapping AS
    SELECT
        ID AS DM_BHXH_ID,
        CAST(COALESCE(NULLIF(NULLIF(MA_CHA, ''), '00'), MA_DVI) AS VARCHAR(20)) AS MA_TINH_QUY_DOI
    FROM {dm_read_sql};

    CREATE TEMPORARY TABLE bc_raw (
        SO_SO_BHXH VARCHAR(10),
        HO_TEN VARCHAR(100),
        NGAY_SINH DATE,
        GIOI_TINH SMALLINT,
        SO_CMND VARCHAR(12),
        DIA_CHI VARCHAR(255),
        SO_THE_KCB_GOC VARCHAR(15),
        MA_KHOI_GOC VARCHAR(10),
        TU_NGAY_GOC DATE,
        DEN_NGAY_GOC DATE,
        DM_BHXH_ID_GOC INTEGER,
        MA_TINH_GOC VARCHAR(20),
        SO_THE_KCB_HIEN_TAI VARCHAR(15),
        MA_KHOI_HIEN_TAI VARCHAR(10),
        TU_NGAY_HIEN_TAI DATE,
        DEN_NGAY_HIEN_TAI DATE,
        DM_BHXH_ID_HIEN_TAI INTEGER,
        MA_TINH_HIEN_TAI VARCHAR(20),
        SO_DOT_GIAN_DOAN INTEGER,
        SO_NGAY_GIAN_DOAN INTEGER,
        SO_THANG_GIAN_DOAN NUMERIC(4, 1),
        NGAY_GOC DATE,
        NGAY_KIEM_TRA DATE,
        CREATED_AT TIMESTAMP
    );
    """)

    chunk_query = f"""
    INSERT INTO bc_raw
    WITH valid_cards AS (
        SELECT
            SO_SO_BHXH, HO_TEN, NGAY_SINH, GIOI_TINH, SO_CMND, DIA_CHI,
            SO_THE_KCB, MA_KHOI, TU_NGAY, DEN_NGAY, DM_BHXH_ID, MA_TINH,
            GREATEST(TU_NGAY, DATE '{window_start}') AS tu_clip,
            LEAST(DEN_NGAY, DATE '{window_end}') AS den_clip
        FROM read_parquet('?')
        WHERE TRANG_THAI = 1
    ),
    base_cards AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY SO_SO_BHXH
                ORDER BY CASE WHEN MA_KHOI = 'SV' THEN 2 ELSE 1 END DESC, DEN_NGAY DESC, SO_THE_KCB ASC
            ) AS rn_base
        FROM valid_cards
        WHERE TU_NGAY < DATE '{base_next}' AND DEN_NGAY >= DATE '{base_start}'
          AND MA_KHOI IN ('HS', 'SV')
    ),
    primary_base AS (SELECT * FROM base_cards WHERE rn_base = 1),
    check_cards AS (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY SO_SO_BHXH ORDER BY DEN_NGAY DESC, SO_THE_KCB ASC) AS rn_chk
        FROM valid_cards
        WHERE TU_NGAY < DATE '{chk_next}' AND DEN_NGAY >= DATE '{chk_start}'
    ),
    primary_chk AS (SELECT * FROM check_cards WHERE rn_chk = 1),
    candidates AS (
        SELECT b.SO_SO_BHXH, b.HO_TEN, b.NGAY_SINH, b.GIOI_TINH, b.SO_CMND, b.DIA_CHI,
            b.SO_THE_KCB AS SO_THE_KCB_GOC, b.MA_KHOI AS MA_KHOI_GOC, b.TU_NGAY AS TU_NGAY_GOC, b.DEN_NGAY AS DEN_NGAY_GOC,
            b.DM_BHXH_ID AS DM_BHXH_ID_GOC, b.MA_TINH AS MA_TINH_GOC,
            c.SO_THE_KCB AS SO_THE_KCB_HIEN_TAI, c.MA_KHOI AS MA_KHOI_HIEN_TAI, c.TU_NGAY AS TU_NGAY_HIEN_TAI, c.DEN_NGAY AS DEN_NGAY_HIEN_TAI,
            c.DM_BHXH_ID AS DM_BHXH_ID_HIEN_TAI, c.MA_TINH AS MA_TINH_HIEN_TAI
        FROM primary_base b JOIN primary_chk c ON b.SO_SO_BHXH = c.SO_SO_BHXH
    ),
    cand_cards AS (
        SELECT v.SO_SO_BHXH, v.tu_clip AS tu, v.den_clip AS den
        FROM valid_cards v JOIN candidates cd ON v.SO_SO_BHXH = cd.SO_SO_BHXH
        WHERE v.tu_clip <= v.den_clip
    ),
    with_prev AS (
        SELECT SO_SO_BHXH, tu, den,
            MAX(den) OVER (PARTITION BY SO_SO_BHXH ORDER BY tu, den ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS prev_max_den
        FROM cand_cards
    ),
    with_new_grp AS (
        SELECT SO_SO_BHXH, tu, den,
            CASE WHEN prev_max_den IS NULL OR tu > prev_max_den + INTERVAL 1 DAY THEN 1 ELSE 0 END AS is_new_grp
        FROM with_prev
    ),
    with_grp_id AS (
        SELECT SO_SO_BHXH, tu, den,
            SUM(is_new_grp) OVER (PARTITION BY SO_SO_BHXH ORDER BY tu, den ROWS UNBOUNDED PRECEDING) AS grp_id
        FROM with_new_grp
    ),
    merged_intervals AS (
        SELECT SO_SO_BHXH, grp_id, MIN(tu) AS m_tu, MAX(den) AS m_den
        FROM with_grp_id GROUP BY SO_SO_BHXH, grp_id
    ),
    with_gaps AS (
        SELECT SO_SO_BHXH,
            (m_tu - LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) - 1) AS gap_days
        FROM merged_intervals
    ),
    gap_events AS (
        SELECT SO_SO_BHXH, gap_days FROM with_gaps WHERE gap_days > 0
        UNION ALL
        SELECT mi.SO_SO_BHXH, mi.m_tu - DATE '{window_start}' AS gap_days
        FROM merged_intervals mi
        WHERE mi.m_tu = (
            SELECT MIN(x.m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH
        ) AND mi.m_tu > DATE '{window_start}'
        UNION ALL
        SELECT mi.SO_SO_BHXH, DATE '{window_end}' - mi.m_den AS gap_days
        FROM merged_intervals mi
        WHERE mi.m_tu = (
            SELECT MAX(x.m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH
        ) AND mi.m_den < DATE '{window_end}'
    ),
    person_gaps AS (
        SELECT SO_SO_BHXH,
            COUNT(gap_days) AS SO_DOT_GIAN_DOAN,
            COALESCE(SUM(gap_days), 0) AS SO_NGAY_GIAN_DOAN,
            ROUND(COALESCE(SUM(gap_days), 0) / 30.0, 1) AS SO_THANG_GIAN_DOAN
        FROM gap_events GROUP BY SO_SO_BHXH
    )
    SELECT
        CAST(c.SO_SO_BHXH AS VARCHAR(10)),
        CAST(c.HO_TEN AS VARCHAR(100)),
        CAST(c.NGAY_SINH AS DATE),
        CAST(c.GIOI_TINH AS SMALLINT),
        CAST(c.SO_CMND AS VARCHAR(12)),
        CAST(c.DIA_CHI AS VARCHAR(255)),
        CAST(c.SO_THE_KCB_GOC AS VARCHAR(15)),
        CAST(c.MA_KHOI_GOC AS VARCHAR(10)),
        CAST(c.TU_NGAY_GOC AS DATE),
        CAST(c.DEN_NGAY_GOC AS DATE),
        CAST(c.DM_BHXH_ID_GOC AS INTEGER),
        CAST(c.MA_TINH_GOC AS VARCHAR(20)),
        CAST(c.SO_THE_KCB_HIEN_TAI AS VARCHAR(15)),
        CAST(c.MA_KHOI_HIEN_TAI AS VARCHAR(10)),
        CAST(c.TU_NGAY_HIEN_TAI AS DATE),
        CAST(c.DEN_NGAY_HIEN_TAI AS DATE),
        CAST(c.DM_BHXH_ID_HIEN_TAI AS INTEGER),
        CAST(c.MA_TINH_HIEN_TAI AS VARCHAR(20)),
        CAST(g.SO_DOT_GIAN_DOAN AS INTEGER),
        CAST(g.SO_NGAY_GIAN_DOAN AS INTEGER),
        CAST(g.SO_THANG_GIAN_DOAN AS NUMERIC(4, 1)),
        DATE '{base_start}',
        DATE '{window_end}',
        CAST('{report_date} 08:00:00' AS TIMESTAMP)
    FROM candidates c
    JOIN person_gaps g ON c.SO_SO_BHXH = g.SO_SO_BHXH
    WHERE g.SO_NGAY_GIAN_DOAN >= {min_gap_days};
    """

    t_exec_start = time.perf_counter()
    n_files = len(silver_files)
    for idx, fpath in enumerate(silver_files):
        f_norm = fpath.replace("\\", "/")
        con.execute(chunk_query.replace("?", f_norm))
        if (idx + 1) % 20 == 0 or (idx + 1) == n_files:
            el = time.perf_counter() - t_exec_start
            cur_count = con.execute("SELECT COUNT(*) FROM bc_raw;").fetchone()[0]
            spd = (idx + 1) / max(0.001, el)
            eta = (n_files - (idx + 1)) / spd if spd > 0 else 0
            print(
                f"  [{idx+1:3d}/{n_files:3d} - {(idx+1)*100/n_files:5.1f}%] "
                f"Tích lũy: {cur_count:,} người | {spd:.1f} chunks/s | "
                f"Đã chạy: {el:.1f}s | ETA: {eta:.1f}s",
                flush=True,
            )

    # 10. Bảng tổng hợp thống kê địa bàn hành chính: TK_DBHC_HSSV_GIAN_DOAN_BHYT
    con.execute(f"""
    CREATE TEMPORARY TABLE tk_raw AS
    WITH person_prov AS (
        SELECT
            bc.SO_SO_BHXH,
            bc.MA_KHOI_GOC,
            bc.SO_NGAY_GIAN_DOAN,
            COALESCE(m.MA_TINH_QUY_DOI, LPAD(CAST(bc.MA_TINH_GOC AS VARCHAR), 2, '0')) AS MA_TINH_FINAL
        FROM bc_raw bc
        LEFT JOIN dm_mapping m ON bc.DM_BHXH_ID_GOC = m.DM_BHXH_ID
    ),
    agg_prov AS (
        SELECT
            MA_TINH_FINAL,
            COUNT(CASE WHEN MA_KHOI_GOC = 'HS' THEN 1 END) AS SO_LUONG_HS_GIAN_DOAN,
            COUNT(CASE WHEN MA_KHOI_GOC = 'SV' THEN 1 END) AS SO_LUONG_SV_GIAN_DOAN,
            COUNT(*) AS TONG_SO_NGUOI_GIAN_DOAN,
            COALESCE(SUM(SO_NGAY_GIAN_DOAN), 0) AS TONG_NGAY_GIAN_DOAN
        FROM person_prov
        GROUP BY MA_TINH_FINAL
    )
    SELECT
        t.MA_TINH,
        t.TEN_TINH,
        COALESCE(a.SO_LUONG_HS_GIAN_DOAN, 0) AS SO_LUONG_HS_GIAN_DOAN,
        COALESCE(a.SO_LUONG_SV_GIAN_DOAN, 0) AS SO_LUONG_SV_GIAN_DOAN,
        COALESCE(a.TONG_SO_NGUOI_GIAN_DOAN, 0) AS TONG_SO_NGUOI_GIAN_DOAN,
        COALESCE(a.TONG_NGAY_GIAN_DOAN, 0) AS TONG_NGAY_GIAN_DOAN,
        DATE '{report_date}' AS NGAY_BAO_CAO
    FROM dm_tinh t
    LEFT JOIN agg_prov a ON t.MA_TINH = a.MA_TINH_FINAL
    ORDER BY t.MA_TINH ASC;
    """)

    # Xuất file Parquet danh sách chi tiết (sắp xếp theo SO_SO_BHXH)
    con.execute(
        f"COPY (SELECT * FROM bc_raw ORDER BY SO_SO_BHXH ASC) TO '{bc_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    )
    # Xuất file CSV thống kê 63 tỉnh
    con.execute(
        f"COPY tk_raw TO '{tk_file.as_posix()}' (FORMAT CSV, HEADER TRUE);"
    )
    t_exec_end = time.perf_counter()

    # Thống kê nhanh kết quả
    total_persons = con.execute("SELECT COUNT(*) FROM bc_raw;").fetchone()[0]
    total_hs = con.execute(
        "SELECT COUNT(*) FROM bc_raw WHERE MA_KHOI_GOC = 'HS';"
    ).fetchone()[0]
    total_sv = con.execute(
        "SELECT COUNT(*) FROM bc_raw WHERE MA_KHOI_GOC = 'SV';"
    ).fetchone()[0]
    avg_gap_days = con.execute(
        "SELECT COALESCE(ROUND(AVG(SO_NGAY_GIAN_DOAN), 1), 0) FROM bc_raw;"
    ).fetchone()[0]
    total_provinces = con.execute("SELECT COUNT(*) FROM tk_raw;").fetchone()[0]

    return {
        "total_persons": total_persons,
        "total_hs": total_hs,
        "total_sv": total_sv,
        "avg_gap_days": avg_gap_days,
        "total_provinces": total_provinces,
        "execution_sec": round(t_exec_end - t_exec_start, 3),
        "bc_file": str(bc_file),
        "tk_file": str(tk_file),
        "bc_sha256": get_file_sha256(str(bc_file)),
        "tk_sha256": get_file_sha256(str(tk_file)),
    }


def compute_gold_y2_global(
    silver_pattern: str,
    dm_path: str,
    out_dir: Path,
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-07-01",
    chk_next: str = "2026-08-01",
    window_start: str = "2024-10-01",
    window_end: str = "2026-07-31",
    min_gap_days: int = 90,
    report_date: str = "2026-08-10",
    threads: int = 4,
) -> dict:
    """
    Xử lý tầng Gold Ý 2 theo phương pháp DuckDB Global song song.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    bc_file = out_dir / "bc_hssv_gian_doan_bhyt.parquet"
    tk_file = out_dir / "tk_dbhc_hssv_gian_doan_bhyt.csv"

    con = duckdb.connect(database=":memory:")
    con.execute(f"PRAGMA threads={threads};")
    con.execute("PRAGMA preserve_insertion_order=false;")

    sql = build_gold_y2_sql(
        silver_pattern=silver_pattern,
        dm_path=dm_path,
        base_start=base_start,
        base_next=base_next,
        chk_start=chk_start,
        chk_next=chk_next,
        window_start=window_start,
        window_end=window_end,
        min_gap_days=min_gap_days,
        report_date=report_date,
    )

    t_exec_start = time.perf_counter()
    con.execute(sql)

    # Xuất file Parquet danh sách chi tiết
    con.execute(
        f"COPY bc_raw TO '{bc_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    )
    # Xuất file CSV thống kê 63 tỉnh
    con.execute(
        f"COPY tk_raw TO '{tk_file.as_posix()}' (FORMAT CSV, HEADER TRUE);"
    )
    t_exec_end = time.perf_counter()

    # Thống kê nhanh kết quả
    total_persons = con.execute("SELECT COUNT(*) FROM bc_raw;").fetchone()[0]
    total_hs = con.execute(
        "SELECT COUNT(*) FROM bc_raw WHERE MA_KHOI_GOC = 'HS';"
    ).fetchone()[0]
    total_sv = con.execute(
        "SELECT COUNT(*) FROM bc_raw WHERE MA_KHOI_GOC = 'SV';"
    ).fetchone()[0]
    avg_gap_days = con.execute(
        "SELECT COALESCE(ROUND(AVG(SO_NGAY_GIAN_DOAN), 1), 0) FROM bc_raw;"
    ).fetchone()[0]
    total_provinces = con.execute("SELECT COUNT(*) FROM tk_raw;").fetchone()[0]

    return {
        "total_persons": total_persons,
        "total_hs": total_hs,
        "total_sv": total_sv,
        "avg_gap_days": avg_gap_days,
        "total_provinces": total_provinces,
        "execution_sec": round(t_exec_end - t_exec_start, 3),
        "bc_file": str(bc_file),
        "tk_file": str(tk_file),
        "bc_sha256": get_file_sha256(str(bc_file)),
        "tk_sha256": get_file_sha256(str(tk_file)),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build Gold Ý 2: HSSV gián đoạn BHYT >= 3 tháng (CV 835/QLT)"
    )
    parser.add_argument(
        "--method",
        choices=["chunk", "global"],
        default="chunk",
        help="Phương pháp xử lý: 'chunk' (từng phần) hoặc 'global' (DuckDB SQL toàn cục)",
    )
    parser.add_argument(
        "--silver-dir",
        default=str(DATA_DIR / "silver" / "st_inthe_dtl"),
        help="Thư mục chứa dữ liệu Silver",
    )
    parser.add_argument(
        "--dm-file",
        default=str(DM_BHXH_FILE),
        help="Đường dẫn file DM_BHXH (parquet/csv)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(GOLD_Y2_RESULT_DIR),
        help="Thư mục ghi kết quả Gold",
    )
    parser.add_argument(
        "--min-gap-days",
        type=int,
        default=MIN_GAP_DAYS_Y2,
        help="Ngưỡng số ngày gián đoạn tối thiểu (mặc định: 90 ngày)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Số luồng xử lý CPU song song",
    )

    args = parser.parse_args()

    silver_pattern = Path(args.silver_dir).resolve() / "*.parquet"
    silver_files = sorted(glob.glob(str(silver_pattern)))
    if not silver_files:
        sys.exit(f"LỖI: Không tìm thấy file parquet nào tại {silver_pattern}")

    out_path = Path(args.out_dir).resolve()
    dm_path = Path(args.dm_file).resolve()
    if not dm_path.exists():
        sys.exit(f"LỖI: Không tìm thấy file danh mục DM_BHXH tại {dm_path}")

    print("=" * 80)
    print("KHỞI CHẠY PIPELINE TẦNG GOLD (CV 835/QLT - Ý 2)")
    print(f"Mục tiêu: HSSV tham gia 10/2024, vẫn tham gia 07/2026, gián đoạn >= {args.min_gap_days} ngày")
    print(f"Nguồn Silver: {len(silver_files)} tệp parquet")
    print(f"Danh mục: {dm_path}")
    print(f"Thư mục xuất: {out_path}")
    print(f"Phương pháp: {args.method.upper()} | Số luồng: {args.threads}")
    print("=" * 80)

    monitor = MemoryMonitor(interval_sec=0.2)
    monitor.start()
    t_start = time.perf_counter()

    try:
        if args.method == "chunk":
            res = compute_gold_y2_chunk(
                silver_dir=str(Path(args.silver_dir).resolve()),
                dm_path=dm_path.as_posix(),
                out_dir=out_path,
                base_start=NGAY_DAU_THANG_GOC.strftime("%Y-%m-%d"),
                base_next=NGAY_DAU_THANG_SAU_GOC.strftime("%Y-%m-%d"),
                chk_start=NGAY_DAU_THANG_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                chk_next=NGAY_DAU_THANG_SAU_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                window_start=NGAY_DAU_THANG_GOC.strftime("%Y-%m-%d"),
                window_end=NGAY_CUOI_THANG_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                min_gap_days=args.min_gap_days,
                report_date=NGAY_KIEM_TRA.strftime("%Y-%m-%d"),
                threads=args.threads,
            )
        else:
            silver_sql_pattern = (Path(args.silver_dir).resolve() / "part-*.parquet").as_posix()
            res = compute_gold_y2_global(
                silver_pattern=silver_sql_pattern,
                dm_path=dm_path.as_posix(),
                out_dir=out_path,
                base_start=NGAY_DAU_THANG_GOC.strftime("%Y-%m-%d"),
                base_next=NGAY_DAU_THANG_SAU_GOC.strftime("%Y-%m-%d"),
                chk_start=NGAY_DAU_THANG_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                chk_next=NGAY_DAU_THANG_SAU_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                window_start=NGAY_DAU_THANG_GOC.strftime("%Y-%m-%d"),
                window_end=NGAY_CUOI_THANG_KIEM_TRA_Y2.strftime("%Y-%m-%d"),
                min_gap_days=args.min_gap_days,
                report_date=NGAY_KIEM_TRA.strftime("%Y-%m-%d"),
                threads=args.threads,
            )
    finally:
        mem_info = monitor.stop()
        total_sec = time.perf_counter() - t_start

    meta = {
        "bai_toan": "CV 835/QLT - Y 2 (HSSV gian doan >= 3 thang)",
        "method": args.method,
        "threads": args.threads,
        "min_gap_days": args.min_gap_days,
        "total_persons": res["total_persons"],
        "total_hs": res["total_hs"],
        "total_sv": res["total_sv"],
        "avg_gap_days": res["avg_gap_days"],
        "total_provinces": res["total_provinces"],
        "execution_sec": res["execution_sec"],
        "total_wall_sec": round(total_sec, 3),
        "memory_telemetry": mem_info,
        "files": {
            "bc_file": res["bc_file"],
            "bc_sha256": res["bc_sha256"],
            "tk_file": res["tk_file"],
            "tk_sha256": res["tk_sha256"],
        },
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    meta_file = out_path / "_metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("HOÀN TẤT XÂY DỰNG TẦNG GOLD Ý 2 THÀNH CÔNG")
    print("=" * 80)
    print(f"  Tổng số người gián đoạn >= {args.min_gap_days} ngày: {res['total_persons']:,} người")
    print(f"  - Học sinh (HS):                     {res['total_hs']:,} người")
    print(f"  - Sinh viên (SV):                    {res['total_sv']:,} người")
    print(f"  - Thời gian gián đoạn trung bình:    {res['avg_gap_days']} ngày")
    print(f"  - Tổng số tỉnh/thành phố:            {res['total_provinces']} tỉnh")
    print("-" * 80)
    print(f"  Thời gian thực thi:                  {total_sec:.2f} giây")
    print(f"  RAM đỉnh điểm Process Tree:          {mem_info['peak_process_tree_rss_mb']} MB ({mem_info['peak_process_tree_rss_gb']} GB)")
    print(f"  RAM hệ thống sử dụng:                {mem_info['peak_sys_used_gb']} / {mem_info['baseline_sys_total_gb']} GB")
    print("-" * 80)
    print(f"  Tệp chi tiết:                        {res['bc_file']}")
    print(f"  Mã băm SHA-256:                      {res['bc_sha256']}")
    print(f"  Tệp thống kê:                        {res['tk_file']}")
    print(f"  Mã băm SHA-256:                      {res['tk_sha256']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
