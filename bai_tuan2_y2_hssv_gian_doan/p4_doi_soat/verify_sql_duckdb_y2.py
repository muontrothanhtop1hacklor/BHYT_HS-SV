# -*- coding: utf-8 -*-
"""
verify_sql_duckdb_y2.py
Kiểm chứng độc lập bằng truy vấn DuckDB SQL thuần túy cho bài toán CV 835/QLT (Ý 2).
"""
import argparse
import sys
import time
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import duckdb
import pandas as pd
import pyarrow.parquet as pq

from common.config import (
    GOLD_Y2_BC_FILE,
    GOLD_Y2_TK_CSV,
    PROJECT_ROOT,
    ST_INTHE_DTL_DIR,
)


def main():
    parser = argparse.ArgumentParser(
        description="Kiểm chứng SQL DuckDB độc lập cho Ý 2 (CV 835/QLT)"
    )
    parser.add_argument(
        "--chunks",
        type=int,
        default=0,
        help="Số chunks đầu để kiểm chứng; mặc định 0 = toàn bộ chunks",
    )
    args = parser.parse_args()

    sql_file = (
        PROJECT_ROOT
        / "bai_tuan2_y2_hssv_gian_doan"
        / "p4_doi_soat"
        / "sql"
        / "query_y2_timeline_window.sql"
    )
    if not sql_file.exists():
        sys.exit(f"LỖI: Không tìm thấy file SQL: {sql_file}")

    print("=" * 80)
    print("BÁO CÁO KIỂM CHỨNG ĐỘC LẬP BẰNG DUCKDB SQL (CV 835/QLT - Ý 2)")
    print(f"File truy vấn: {sql_file}")
    print("=" * 80)

    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    silver_dir = PROJECT_ROOT / "data" / "silver" / "st_inthe_dtl"
    chunk_files = sorted(list(silver_dir.glob("part-*.parquet")))
    if not chunk_files:
        chunk_files = sorted(list(silver_dir.glob("*.parquet")))
    if not chunk_files:
        sys.exit(f"LỖI: Không tìm thấy file Parquet trong {silver_dir}")
    if args.chunks > 0:
        selected_files = chunk_files[: args.chunks]
        print(f"Chế độ: Kiểm chứng mẫu {len(selected_files)} / {len(chunk_files)} chunks đầu tiên")
        file_list_str = "[" + ", ".join(f"'{p.as_posix()}'" for p in selected_files) + "]"
        sql = sql.replace("read_parquet('data/silver/st_inthe_dtl/*.parquet')", f"read_parquet({file_list_str})")
        con_sample = duckdb.connect()
        sample_so_so = set(
            con_sample.execute(
                f"SELECT DISTINCT SO_SO_BHXH FROM read_parquet({file_list_str})"
            ).fetchnumpy()["SO_SO_BHXH"]
        )
    else:
        print(f"Chế độ: Kiểm chứng toàn bộ {len(chunk_files)} chunks")
        sample_so_so = None

    con = duckdb.connect(database=":memory:")
    con.execute("PRAGMA threads=4;")

    t0 = time.perf_counter()
    res_df = con.execute(sql).fetchdf()
    el = time.perf_counter() - t0

    print(f"\nKết quả truy vấn SQL độc lập (Thời gian: {el:.2f} giây):")
    print(res_df.to_string(index=False))

    print("-" * 80)
    print("ĐỐI CHIẾU TỪNG MÃ BHXH VÀ CÁC CHỈ TIÊU VỚI GOLD:")
    if not GOLD_Y2_BC_FILE.exists():
        print(f"  [CẢNH BÁO] Chưa có file Gold tại {GOLD_Y2_BC_FILE}. Hãy chạy build_gold_y2 trước.")
        return

    gold_df = pq.read_table(str(GOLD_Y2_BC_FILE)).to_pandas()
    if sample_so_so is not None:
        gold_df = gold_df[gold_df["SO_SO_BHXH"].isin(sample_so_so)]
    compare_cols = ["SO_SO_BHXH", "MA_KHOI_GOC", "SO_DOT_GIAN_DOAN", "SO_NGAY_GIAN_DOAN"]
    missing_gold_cols = set(compare_cols) - set(gold_df.columns)
    if missing_gold_cols:
        sys.exit(f"LỖI: Thiếu cột Gold cần đối chiếu: {sorted(missing_gold_cols)}")
    sql_compare = res_df[compare_cols].copy()
    gold_compare = gold_df[compare_cols].copy()
    sql_compare["SO_SO_BHXH"] = sql_compare["SO_SO_BHXH"].astype(str)
    gold_compare["SO_SO_BHXH"] = gold_compare["SO_SO_BHXH"].astype(str)
    for column in ("MA_KHOI_GOC",):
        sql_compare[column] = sql_compare[column].astype(str)
        gold_compare[column] = gold_compare[column].astype(str)
    for column in ("SO_DOT_GIAN_DOAN", "SO_NGAY_GIAN_DOAN"):
        sql_compare[column] = pd.to_numeric(sql_compare[column]).astype("int64")
        gold_compare[column] = pd.to_numeric(gold_compare[column]).astype("int64")
    sql_compare = sql_compare.sort_values("SO_SO_BHXH").reset_index(drop=True)
    gold_compare = gold_compare.sort_values("SO_SO_BHXH").reset_index(drop=True)
    exact_match = sql_compare.equals(gold_compare)
    print(f"  Số người SQL: {len(sql_compare):,} | Số người Gold: {len(gold_compare):,}")
    print(f"  So khớp từng mã BHXH + khối gốc + số đợt + số ngày: {'KHỚP' if exact_match else 'LỆCH'}")

    if exact_match:
        print("\n [XÁC NHẬN] Các bản ghi và chỉ tiêu đã so khớp.")
    else:
        print("\n [LỖI] Sai lệch bản ghi hoặc chỉ tiêu giữa SQL và Gold!")
        print("  Chỉ xuất mẫu tối đa 10 bản ghi lệch:")
        merged = sql_compare.merge(gold_compare, on="SO_SO_BHXH", how="outer", suffixes=("_SQL", "_GOLD"), indicator=True)
        print(merged[merged["_merge"] != "both"].head(10).to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
