# -*- coding: utf-8 -*-
"""
scripts/build_bronze.py
Nạp dữ liệu thô nguyên trạng 200 file Parquet vào tầng Bronze (Medallion Architecture).
Yêu cầu:
- Giữ nguyên 30 cột dữ liệu gốc.
- Bổ sung 4 cột kỹ thuật metadata: _SOURCE_FILE, _CHUNK_ID, _INGESTED_AT, _BATCH_ID.
- Cơ chế ghi atomic (.tmp -> os.replace) đảm bảo tính Idempotent (không nhân đôi dòng khi chạy lại).
- Hỗ trợ đa luồng (ThreadPoolExecutor), theo dõi RAM đỉnh và thời gian thực thi.
"""

import os
import sys
import time
import glob
import json
import uuid
import ctypes
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyarrow as pa
import pyarrow.parquet as pq

# Đảm bảo UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def get_system_ram():
    """Trả về (used_gb, total_gb, percent) trên Windows."""
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = stat.ullTotalPhys / (1024**3)
        used_gb = (stat.ullTotalPhys - stat.ullAvailPhys) / (1024**3)
        return used_gb, total_gb, stat.dwMemoryLoad
    except Exception:
        return 0.0, 0.0, 0


def process_chunk(file_path: str, out_dir: str, chunk_id: int, batch_id: str, ingested_at: str):
    """
    Xử lý nạp 1 chunk từ Raw sang Bronze:
    - Đọc Parquet nguyên vẹn.
    - Gắn 4 cột kỹ thuật.
    - Ghi atomic file đích với nén zstd level 1.
    """
    base_name = os.path.basename(file_path)
    out_file = os.path.join(out_dir, base_name)
    tmp_file = out_file + ".tmp"

    table = pq.read_table(file_path)
    n_rows = len(table)

    # Nếu nguồn là dữ liệu rút gọn (Script 1) chưa có MA_TINH, tự động trích từ SO_THE_KCB (vị trí 3..5)
    if "MA_TINH" not in table.column_names and "SO_THE_KCB" in table.column_names:
        import pyarrow.compute as pc
        ma_tinh = pc.utf8_slice_codeunits(table.column("SO_THE_KCB"), 3, 5)
        table = table.append_column("MA_TINH", ma_tinh)

    # Tạo 4 cột kỹ thuật pyarrow
    col_source = pa.repeat(pa.scalar(base_name, pa.string()), n_rows)
    col_chunk = pa.repeat(pa.scalar(chunk_id, pa.int32()), n_rows)
    col_ingested = pa.repeat(pa.scalar(ingest_at, pa.string()), n_rows)
    col_batch = pa.repeat(pa.scalar(batch_id, pa.string()), n_rows)

    bronze_table = (
        table.append_column("_SOURCE_FILE", col_source)
        .append_column("_CHUNK_ID", col_chunk)
        .append_column("_INGESTED_AT", col_ingested)
        .append_column("_BATCH_ID", col_batch)
    )

    # Ghi ra file .tmp rồi rename atomic
    pq.write_table(
        bronze_table,
        tmp_file,
        compression="zstd",
        compression_level=1,
        use_dictionary=True,
    )
    if os.path.exists(out_file):
        os.remove(out_file)
    os.replace(tmp_file, out_file)

    return chunk_id, n_rows, os.path.getsize(out_file)


def run_bronze(
    input_dir: str = "data/bhyt_data/st_inthe_dtl",
    output_dir: str = "data/bronze/st_inthe_dtl",
    workers: int = 4,
    batch_id: str = None,
):
    start_time = time.time()
    if not batch_id:
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    global ingest_at
    ingest_at = datetime.now().isoformat()

    if not os.path.exists(input_dir):
        alt = os.path.join(os.path.dirname(input_dir), "ST_INTHE_DTL")
        if os.path.exists(alt):
            input_dir = alt
    os.makedirs(output_dir, exist_ok=True)
    raw_files = sorted(glob.glob(os.path.join(input_dir, "part*.parquet")))
    total_files = len(raw_files)

    ram_used_start, ram_total, _ = get_system_ram()
    print("=" * 80)
    print(f" KHỞI CHẠY NẠP DỮ LIỆU TẦNG BRONZE (MEDALLION ARCHITECTURE)")
    print("=" * 80)
    print(f" Thư mục nguồn : {input_dir} ({total_files} files)")
    print(f" Thư mục đích  : {output_dir}")
    print(f" Số luồng xử lý: {workers}")
    print(f" Mã lượt chạy  : {batch_id}")
    print(f" RAM ban đầu   : {ram_used_start:.2f} / {ram_total:.2f} GB")
    print("-" * 80)

    total_rows = 0
    total_bytes = 0
    peak_ram = ram_used_start

    # Thực thi đa luồng
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for idx, fpath in enumerate(raw_files):
            fut = executor.submit(process_chunk, fpath, output_dir, idx, batch_id, ingest_at)
            futures[fut] = idx

        done_count = 0
        for fut in as_completed(futures):
            chunk_id, rows, size = fut.result()
            total_rows += rows
            total_bytes += size
            done_count += 1

            used_ram, _, _ = get_system_ram()
            if used_ram > peak_ram:
                peak_ram = used_ram

            if done_count % 20 == 0 or done_count == total_files:
                elapsed = time.time() - start_time
                rps = total_rows / elapsed if elapsed > 0 else 0
                print(
                    f" [{done_count:3d}/{total_files:3d}] Tiến độ: {done_count/total_files*100:5.1f}% | "
                    f"Số dòng: {total_rows:11,d} | Tốc độ: {rps:10,.0f} dòng/s | RAM: {used_ram:5.2f} GB"
                )

    elapsed_total = time.time() - start_time
    total_gb = total_bytes / (1024**3)
    avg_rps = total_rows / elapsed_total if elapsed_total > 0 else 0

    # Ghi manifest tầng Bronze
    manifest_info = {
        "batch_id": batch_id,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "ingested_at": ingest_at,
        "total_files": total_files,
        "total_rows": total_rows,
        "total_size_bytes": total_bytes,
        "total_size_gb": round(total_gb, 3),
        "elapsed_seconds": round(elapsed_total, 2),
        "rows_per_second": round(avg_rps, 0),
        "peak_ram_gb": round(peak_ram, 2),
        "columns_count": 34,
        "technical_columns": ["_SOURCE_FILE", "_CHUNK_ID", "_INGESTED_AT", "_BATCH_ID"],
    }

    manifest_path = os.path.join(os.path.dirname(output_dir), "_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest_info, mf, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f" HOÀN TẤT NẠP TẦNG BRONZE:")
    print(f" - Tổng số dòng nạp    : {total_rows:,} dòng")
    print(f" - Tổng dung lượng đĩa : {total_gb:.2f} GB")
    print(f" - Thời gian thực thi  : {elapsed_total:.2f} giây")
    print(f" - Tốc độ trung bình   : {avg_rps:,.0f} dòng/giây")
    print(f" - RAM đỉnh            : {peak_ram:.2f} GB (trên tổng {ram_total:.2f} GB)")
    print(f" - File manifest       : {manifest_path}")
    print("=" * 80)

    # Kiểm tra tính toàn vẹn dòng
    EXPECTED_ROWS = 195305908
    if total_rows == EXPECTED_ROWS:
        print(f" [PASS] Bảo toàn dòng tuyệt đối: {total_rows:,} == {EXPECTED_ROWS:,} dòng.")
    else:
        print(f" [FAIL] Lệch dòng: {total_rows:,} != {EXPECTED_ROWS:,} dòng!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Bronze layer for BHYT dataset")
    parser.add_argument("--input", default="data/bhyt_data/st_inthe_dtl", help="Input raw directory")
    parser.add_argument("--output", default="data/bronze/st_inthe_dtl", help="Output bronze directory")
    parser.add_argument("--workers", type=int, default=4, help="Number of thread workers")
    parser.add_argument("--batch-id", default=None, help="Batch run ID")
    args = parser.parse_args()

    run_bronze(
        input_dir=args.input,
        output_dir=args.output,
        workers=args.workers,
        batch_id=args.batch_id,
    )
