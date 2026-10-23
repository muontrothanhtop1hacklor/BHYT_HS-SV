# Bài: tuan1_y1 | Phần: p2_bronze_silver
# -*- coding: utf-8 -*-
"""
scripts/build_silver.py
Làm sạch, chuẩn hóa, ép kiểu và phân loại chất lượng dữ liệu từ Bronze sang Silver.

Nâng cấp Ngày 5:
1. KHỬ TRÙNG TOÀN CỤC (GLOBAL DEDUP):
   - Thay vì chỉ khử trùng cục bộ từng chunk, sử dụng GlobalDedupTracker xuyên suốt mọi chunk.
   - Bắt trọn 100% dòng trùng lặp ID bất kể nằm cùng chunk hay khác chunk.

2. CƠ CHẾ SMART REPAIR NGHIỆP VỤ BHYT (Khắc phục 131 ca Dương tính giả):
   - Hỗ trợ 2 chế độ xử lý lỗi Loại 1 (TU_NGAY > DEN_NGAY):
     * 'quarantine': Cách ly 100% thẻ lỗi vào quarantine (chế độ bảo thủ / baseline).
     * 'smart-repair': Đối chiếu chu kỳ thẻ BHYT thực tế (1, 3, 6, 12 tháng). Nếu lỗi do đảo ngày
       nhập liệu hợp lệ, tự động hoán đổi ngày và gắn cờ audit `_FLAG_DATE_SWAPPED = True`, cứu
       thẻ hợp lệ tại tháng 08/2026 và triệt tiêu 131 ca Dương tính giả tại tầng Gold.

Phương trình bảo toàn dòng bắt buộc:
Bronze = Silver + Quarantine + Deduplicated (Local + Cross-chunk)
"""

import os
import sys
import time
import glob
import json
import ctypes
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

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
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = stat.ullTotalPhys / (1024**3)
        used_gb = (stat.ullTotalPhys - stat.ullAvailPhys) / (1024**3)
        return used_gb, total_gb, stat.dwMemoryLoad
    except Exception:
        return 0.0, 0.0, 0


class GlobalDedupTracker:
    """
    Theo dõi ID toàn cục xuyên suốt các chunk để khử trùng (Cross-chunk Global Deduplication).
    Thread-safe cho đa luồng.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._seen_ids = set()

    def filter_unique(self, id_array: np.ndarray):
        """
        Nhận vào mảng ID của chunk, trả về:
        - mask_keep: bool array giữ lại các bản ghi xuất hiện lần đầu tiên trên toàn cục.
        - n_dedup: số bản ghi bị trùng (gồm cả nội bộ chunk và liên chunk).
        """
        n = len(id_array)
        mask_keep = np.zeros(n, dtype=bool)
        with self._lock:
            for i, val in enumerate(id_array):
                if val not in self._seen_ids:
                    self._seen_ids.add(val)
                    mask_keep[i] = True
        n_dedup = n - int(np.sum(mask_keep))
        return mask_keep, n_dedup

    def total_unique_seen(self):
        with self._lock:
            return len(self._seen_ids)


def process_silver_chunk(
    bronze_file: str,
    silver_dir: str,
    quarantine_dir: str,
    chunk_id: int,
    dedup_tracker: GlobalDedupTracker = None,
    mode_loai1: str = "quarantine"
):
    """
    Xử lý 1 chunk từ Bronze sang Silver:
    - Đọc Parquet.
    - Khử trùng toàn cục theo ID (Loại 5) qua GlobalDedupTracker.
    - Chuẩn hóa MA_KHOI (Loại 4).
    - Gắn cờ Loại 2 (HO_TEN is null) & Loại 3 (GIOI_TINH invalid).
    - Xử lý Loại 1 theo mode:
      * 'quarantine': Tách 100% TU_NGAY > DEN_NGAY vào quarantine.
      * 'smart-repair': Tự động hoán đổi ngày nếu khoảng cách hợp lý theo chu kỳ BHYT thực tế (1-12 tháng)
        và gắn cờ `_FLAG_DATE_SWAPPED = True`. Chỉ cách ly những ca không thể phục hồi.
    - Ép kiểu date32 cho các trường ngày.
    - Ghi atomic file Silver & Quarantine.
    """
    base_name = os.path.basename(bronze_file)
    table = pq.read_table(bronze_file)
    n_bronze = len(table)

    # 1. Khử trùng Loại 5 theo ID (Toàn cục xuyên chunk)
    id_np = table.column("ID").to_numpy(zero_copy_only=False)
    if dedup_tracker is not None:
        mask_unique, n_dedup = dedup_tracker.filter_unique(id_np)
        if n_dedup > 0:
            table = table.filter(pa.array(mask_unique))
    else:
        # Fallback cục bộ nếu không dùng tracker
        _, unique_indices = np.unique(id_np, return_index=True)
        unique_indices.sort()
        n_dedup = n_bronze - len(unique_indices)
        if n_dedup > 0:
            table = table.take(pa.array(unique_indices))

    # 2. Chuẩn hóa Loại 4: MA_KHOI (chữ thường / khoảng trắng thừa)
    ma_khoi_str = pc.cast(table.column("MA_KHOI"), pa.string())
    ma_khoi_clean = pc.utf8_trim_whitespace(pc.utf8_upper(ma_khoi_str))
    table = table.set_column(
        table.schema.get_field_index("MA_KHOI"),
        "MA_KHOI",
        pc.dictionary_encode(ma_khoi_clean),
    )

    # 3. Gắn cờ Loại 2: HO_TEN is null
    ho_ten_col = table.column("HO_TEN")
    flag_name_null = pc.is_null(ho_ten_col)
    n_flag_name = pc.sum(flag_name_null).as_py() or 0

    # 4. Gắn cờ Loại 3: GIOI_TINH not in (1, 2)
    gioi_tinh_col = table.column("GIOI_TINH")
    is_valid_gender = pc.or_(pc.equal(gioi_tinh_col, 1), pc.equal(gioi_tinh_col, 2))
    flag_gender_invalid = pc.invert(is_valid_gender)
    n_flag_gender = pc.sum(flag_gender_invalid).as_py() or 0

    table = table.append_column("_FLAG_NAME_NULL", flag_name_null).append_column(
        "_FLAG_GENDER_INVALID", flag_gender_invalid
    )

    # 5. Ép kiểu date32 cho các trường ngày
    tu_ngay_col = table.column("TU_NGAY")
    den_ngay_col = table.column("DEN_NGAY")
    if tu_ngay_col.type != pa.date32():
        tu_ngay_col = pc.cast(tu_ngay_col, pa.date32())
        table = table.set_column(table.schema.get_field_index("TU_NGAY"), "TU_NGAY", tu_ngay_col)
    if den_ngay_col.type != pa.date32():
        den_ngay_col = pc.cast(den_ngay_col, pa.date32())
        table = table.set_column(table.schema.get_field_index("DEN_NGAY"), "DEN_NGAY", den_ngay_col)
    if "NGAY_SINH" in table.column_names and table.column("NGAY_SINH").type != pa.date32():
        table = table.set_column(table.schema.get_field_index("NGAY_SINH"), "NGAY_SINH", pc.cast(table.column("NGAY_SINH"), pa.date32()))

    # 6. Xử lý Loại 1: TU_NGAY > DEN_NGAY
    is_invalid_date_range = pc.greater(tu_ngay_col, den_ngay_col)
    n_invalid_raw = pc.sum(is_invalid_date_range).as_py() or 0
    n_swapped = 0

    flag_date_swapped = pa.repeat(pa.scalar(False, pa.bool_()), len(table))

    if mode_loai1 == "smart-repair" and n_invalid_raw > 0:
        # Cơ chế Smart Repair nghiệp vụ:
        # Kiểm tra khoảng cách ngày giữa TU_NGAY và DEN_NGAY
        # Thẻ BHYT thực tế có chu kỳ 1, 3, 6, 12 tháng (khoảng 25 - 375 ngày).
        # Nếu rơi vào khoảng này -> Đây là lỗi nhập liệu đảo ngày (Swap).
        tu_days = tu_ngay_col.cast(pa.int32()).to_numpy(zero_copy_only=False)
        den_days = den_ngay_col.cast(pa.int32()).to_numpy(zero_copy_only=False)
        invalid_mask = tu_days > den_days

        diff_days = tu_days - den_days
        # Khoảng cách hợp lệ theo chu kỳ BHYT chuẩn (1-12 tháng): 25 đến 375 ngày
        repairable_mask = invalid_mask & (diff_days >= 25) & (diff_days <= 375)
        n_swapped = int(np.sum(repairable_mask))

        # Thực hiện Swap cho các bản ghi sửa được
        if n_swapped > 0:
            new_tu_days = np.where(repairable_mask, den_days, tu_days)
            new_den_days = np.where(repairable_mask, tu_days, den_days)

            tu_ngay_repaired = pa.array(new_tu_days, type=pa.int32()).cast(pa.date32())
            den_ngay_repaired = pa.array(new_den_days, type=pa.int32()).cast(pa.date32())

            table = table.set_column(table.schema.get_field_index("TU_NGAY"), "TU_NGAY", tu_ngay_repaired)
            table = table.set_column(table.schema.get_field_index("DEN_NGAY"), "DEN_NGAY", den_ngay_repaired)
            flag_date_swapped = pa.array(repairable_mask)

        # Cập nhật lại mask cách ly (chỉ cách ly những ca không thể sửa)
        unrepairable_mask = invalid_mask & (~repairable_mask)
        is_quarantine = pa.array(unrepairable_mask)
    else:
        is_quarantine = is_invalid_date_range

    table = table.append_column("_FLAG_DATE_SWAPPED", flag_date_swapped)

    n_quarantine = pc.sum(is_quarantine).as_py() or 0
    silver_table = table.filter(pc.invert(is_quarantine))
    quarantine_table = table.filter(is_quarantine)

    # Thêm cột lý do cách ly cho quarantine
    if len(quarantine_table) > 0:
        col_reason = pa.repeat(pa.scalar("TU_NGAY_LON_HON_DEN_NGAY", pa.string()), len(quarantine_table))
        col_q_at = pa.repeat(pa.scalar(datetime.now().isoformat(), pa.string()), len(quarantine_table))
        quarantine_table = quarantine_table.append_column("_QUARANTINE_REASON", col_reason).append_column(
            "_QUARANTINE_AT", col_q_at
        )

        q_out = os.path.join(quarantine_dir, base_name)
        q_tmp = q_out + ".tmp"
        pq.write_table(quarantine_table, q_tmp, compression="zstd", compression_level=1)
        if os.path.exists(q_out):
            os.remove(q_out)
        os.replace(q_tmp, q_out)

    # Ghi Silver
    s_out = os.path.join(silver_dir, base_name)
    s_tmp = s_out + ".tmp"
    pq.write_table(silver_table, s_tmp, compression="zstd", compression_level=1)
    if os.path.exists(s_out):
        os.remove(s_out)
    os.replace(s_tmp, s_out)

    n_silver = len(silver_table)
    return {
        "chunk_id": chunk_id,
        "n_bronze": n_bronze,
        "n_silver": n_silver,
        "n_quarantine": n_quarantine,
        "n_dedup": n_dedup,
        "n_flag_name": n_flag_name,
        "n_flag_gender": n_flag_gender,
        "n_swapped": n_swapped,
    }


def run_silver(
    bronze_dir: str = "data/bronze/st_inthe_dtl",
    silver_dir: str = "data/silver/st_inthe_dtl",
    quarantine_dir: str = "data/silver/quarantine",
    workers: int = 4,
    global_dedup: bool = True,
    mode_loai1: str = "quarantine",
):
    start_time = time.time()
    os.makedirs(silver_dir, exist_ok=True)
    os.makedirs(quarantine_dir, exist_ok=True)

    bronze_files = sorted(glob.glob(os.path.join(bronze_dir, "part*.parquet")))
    total_files = len(bronze_files)

    ram_start, ram_total, _ = get_system_ram()
    print("=" * 80)
    print(f" KHỞI CHẠY LÀM SẠCH & CHUYỂN ĐỔI TẦNG SILVER (MEDALLION ARCHITECTURE - NGÀY 5)")
    print("=" * 80)
    print(f" Thư mục Bronze    : {bronze_dir} ({total_files} files)")
    print(f" Thư mục Silver    : {silver_dir}")
    print(f" Thư mục Quarantine: {quarantine_dir}")
    print(f" Chế độ Khử trùng  : {'TOÀN CỤC (GLOBAL DEDUP XUYÊN CHUNK)' if global_dedup else 'CỤC BỘ TỪNG CHUNK'}")
    print(f" Chế độ Loại 1     : {mode_loai1.upper()} ({'Smart Repair triệt tiêu 131 FP' if mode_loai1 == 'smart-repair' else 'Baseline Quarantine'})")
    print(f" Số luồng xử lý    : {workers}")
    print(f" RAM ban đầu       : {ram_start:.2f} / {ram_total:.2f} GB")
    print("-" * 80)

    dedup_tracker = GlobalDedupTracker() if global_dedup else None

    tot_bronze = 0
    tot_silver = 0
    tot_quarantine = 0
    tot_dedup = 0
    tot_flag_name = 0
    tot_flag_gender = 0
    tot_swapped = 0
    peak_ram = ram_start

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for idx, fpath in enumerate(bronze_files):
            fut = executor.submit(
                process_silver_chunk,
                fpath,
                silver_dir,
                quarantine_dir,
                idx,
                dedup_tracker,
                mode_loai1,
            )
            futures[fut] = idx

        done_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            tot_bronze += res["n_bronze"]
            tot_silver += res["n_silver"]
            tot_quarantine += res["n_quarantine"]
            tot_dedup += res["n_dedup"]
            tot_flag_name += res["n_flag_name"]
            tot_flag_gender += res["n_flag_gender"]
            tot_swapped += res["n_swapped"]
            done_count += 1

            used_ram, _, _ = get_system_ram()
            if used_ram > peak_ram:
                peak_ram = used_ram

            if done_count % 20 == 0 or done_count == total_files:
                elapsed = time.time() - start_time
                rps = tot_bronze / elapsed if elapsed > 0 else 0
                print(
                    f" [{done_count:3d}/{total_files:3d}] Tiến độ: {done_count/total_files*100:5.1f}% | "
                    f"Đã xử lý: {tot_bronze:11,d} dòng | Tốc độ: {rps:10,.0f} dòng/s | RAM: {used_ram:5.2f} GB"
                )

    elapsed_total = time.time() - start_time
    avg_rps = tot_bronze / elapsed_total if elapsed_total > 0 else 0

    print("=" * 80)
    print(f" HOÀN TẤT XỬ LÝ TẦNG SILVER:")
    print(f" - Tổng dòng Bronze        : {tot_bronze:11,d}")
    print(f" - Tổng dòng Silver        : {tot_silver:11,d}")
    print(f" - Tổng dòng Quarantine    : {tot_quarantine:11,d} (Loại 1: TU_NGAY > DEN_NGAY)")
    print(f" - Tổng dòng Khử trùng     : {tot_dedup:11,d} (Loại 5: Trùng ID toàn cục)")
    print(f" - Dòng cờ HO_TEN null     : {tot_flag_name:11,d} (Loại 2)")
    print(f" - Dòng cờ GIOI_TINH sai   : {tot_flag_gender:11,d} (Loại 3)")
    if mode_loai1 == "smart-repair":
        print(f" - Dòng Smart Repaired     : {tot_swapped:11,d} (Hoán đổi ngày hợp lệ BHYT)")
    print(f" - Thời gian thực thi      : {elapsed_total:.2f} giây")
    print(f" - Tốc độ trung bình       : {avg_rps:,.0f} dòng/giây")
    print(f" - RAM đỉnh                : {peak_ram:.2f} GB (trên tổng {ram_total:.2f} GB)")
    print("-" * 80)

    # Kiểm tra phương trình bảo toàn dòng
    sum_parts = tot_silver + tot_quarantine + tot_dedup
    diff = tot_bronze - sum_parts
    print(f" ĐỐI SOÁT BẢO TOÀN DÒNG:")
    print(f"   Bronze ({tot_bronze:,}) = Silver ({tot_silver:,}) + Quarantine ({tot_quarantine:,}) + Dedup ({tot_dedup:,})")
    print(f"   Tổng vế phải: {sum_parts:,} | Chênh lệch: {diff}")

    if diff == 0:
        print(" [PASS] Phương trình bảo toàn dòng thoả mãn 100%!")
    else:
        print(f" [FAIL] Phương trình bảo toàn dòng KHÔNG thoả mãn (lệch {diff} dòng)!")

    # Ghi manifest Silver
    silver_manifest = {
        "timestamp": datetime.now().isoformat(),
        "total_bronze_rows": tot_bronze,
        "total_silver_rows": tot_silver,
        "total_quarantine_rows": tot_quarantine,
        "total_deduplicated_rows": tot_dedup,
        "flagged_name_null_rows": tot_flag_name,
        "flagged_gender_invalid_rows": tot_flag_gender,
        "smart_repaired_rows": tot_swapped,
        "global_dedup_enabled": global_dedup,
        "mode_loai1": mode_loai1,
        "conservation_passed": (diff == 0),
        "elapsed_seconds": round(elapsed_total, 2),
        "rows_per_second": round(avg_rps, 0),
        "peak_ram_gb": round(peak_ram, 2),
    }

    manifest_path = os.path.join(os.path.dirname(silver_dir), "_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(silver_manifest, mf, indent=2, ensure_ascii=False)
    print(f" File manifest Silver: {manifest_path}")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Silver layer for BHYT dataset (Day 5 Enhanced)")
    parser.add_argument("--bronze", default="data/bronze/st_inthe_dtl", help="Input bronze directory")
    parser.add_argument("--silver", default="data/silver/st_inthe_dtl", help="Output silver directory")
    parser.add_argument("--quarantine", default="data/silver/quarantine", help="Output quarantine directory")
    parser.add_argument("--workers", type=int, default=4, help="Number of thread workers")
    parser.add_argument("--no-global-dedup", action="store_true", help="Tắt khử trùng toàn cục (chỉ khử trùng nội bộ chunk)")
    parser.add_argument(
        "--mode-loai1",
        choices=["quarantine", "smart-repair"],
        default="quarantine",
        help="Chế độ xử lý Loại 1 (TU_NGAY > DEN_NGAY): 'quarantine' (mặc định bảo thủ) hoặc 'smart-repair' (chuẩn nghiệp vụ BHYT, triệt tiêu 131 FP)",
    )
    args = parser.parse_args()

    run_silver(
        bronze_dir=args.bronze,
        silver_dir=args.silver,
        quarantine_dir=args.quarantine,
        workers=args.workers,
        global_dedup=not args.no_global_dedup,
        mode_loai1=args.mode_loai1,
    )
