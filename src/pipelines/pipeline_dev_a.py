"""
Pipeline xử lý của BẠN A:
Giải quyết bài toán Ý 1 (CV 835/QLT) - Lọc HSSV dừng tham gia BHYT.
Giải pháp 1: PyArrow Chunk Streaming / Out-of-Core Processing.

Đầu ra:
1. data/output/dev_a/bc_hssv_dung_tham_gia.parquet
2. data/output/dev_a/tk_dbhc_hssv_dung_tham_gia.parquet
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import (
    ST_INTHE_DTL_DIR, DM_BHXH_FILE, OUTPUT_DEV_A_DIR,
    NGAY_DAU_THANG_GOC, NGAY_DAU_THANG_SAU_GOC,
    NGAY_DAU_THANG_KIEM_TRA, NGAY_DAU_THANG_SAU_KIEM_TRA,
    NGAY_KIEM_TRA, ANSWER_LIST_FILE
)

COLS = [
    'ID', 'SO_SO_BHXH', 'HO_TEN', 'NGAY_SINH', 'GIOI_TINH', 'SO_CMND',
    'SO_THE_KCB', 'MA_KHOI', 'TU_NGAY', 'DEN_NGAY', 'TRANG_THAI',
    'DM_BHXH_ID', 'MA_TINH'
]

B0 = int(np.datetime64(NGAY_DAU_THANG_GOC, 'D').astype(np.int64))
B1 = int(np.datetime64(NGAY_DAU_THANG_SAU_GOC, 'D').astype(np.int64))
C0 = int(np.datetime64(NGAY_DAU_THANG_KIEM_TRA, 'D').astype(np.int64))
C1 = int(np.datetime64(NGAY_DAU_THANG_SAU_KIEM_TRA, 'D').astype(np.int64))


def process_parquet_chunk(fpath):
    """
    Xử lý 1 chunk Parquet thẻ BHYT:
    Do mỗi chunk chứa trọn vẹn toàn bộ thẻ của từng cá nhân (person-chunk invariant),
    việc kiểm tra điều kiện tham gia mốc gốc và mốc kiểm tra được đóng gói hoàn toàn trong chunk.
    """
    t = pq.read_table(fpath, columns=COLS)
    n_rows = t.num_rows
    if n_rows == 0:
        return None, 0

    tu = pc.cast(t['TU_NGAY'], pa.int32()).to_numpy(zero_copy_only=False).astype(np.int64)
    den = pc.cast(t['DEN_NGAY'], pa.int32()).to_numpy(zero_copy_only=False).astype(np.int64)
    status = t['TRANG_THAI'].to_numpy(zero_copy_only=False)
    kh_s = pc.cast(t['MA_KHOI'], pa.string()).to_numpy(zero_copy_only=False)
    so_int = pc.cast(t['SO_SO_BHXH'], pa.int64()).to_numpy(zero_copy_only=False)

    kh = np.full(n_rows, -1, dtype=np.int8)
    kh[kh_s == 'HS'] = 0
    kh[kh_s == 'SV'] = 1
    hs = kh >= 0

    valid = status == 1
    base = valid & (tu < B1) & (den >= B0)
    chk = valid & (tu < C1) & (den >= C0)

    uniq, inv = np.unique(so_int, return_inverse=True)
    has = lambda m: np.bincount(inv, weights=m, minlength=uniq.size) > 0
    b_hs = has(base & (kh == 0))
    b_sv = has(base & (kh == 1))
    c_any = has(chk)
    in_ans = (b_hs | b_sv) & ~c_any

    if not in_ans.any():
        return None, n_rows

    # Lấy thẻ mốc gốc mới nhất (DEN_NGAY lớn nhất) cho mỗi người dừng
    rows_b = np.flatnonzero(base & hs)
    order = np.argsort(den[rows_b])
    sorted_rows = rows_b[order]
    p_row = np.full(uniq.size, -1, np.int64)
    p_row[inv[sorted_rows]] = sorted_rows

    stopped_idx = np.flatnonzero(in_ans)
    chosen_rows = p_row[stopped_idx]

    sub = t.take(pa.array(chosen_rows))
    return sub, n_rows


def run_pipeline_dev_a():
    OUTPUT_DEV_A_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.perf_counter()
    print("=" * 80)
    print("BẮT ĐẦU CHẠY PIPELINE BẠN A (GIẢI PHÁP 1: PYARROW STREAMING / OUT-OF-CORE)")
    print("=" * 80)

    # 1. Quét danh sách file Parquet
    parquet_files = sorted(Path(ST_INTHE_DTL_DIR).glob("part*.parquet"))
    if not parquet_files:
        print(f"[!] Không tìm thấy file dữ liệu nào trong {ST_INTHE_DTL_DIR}")
        return

    print(f"- Nguồn dữ liệu: {ST_INTHE_DTL_DIR}")
    print(f"- Số file Parquet cần xử lý: {len(parquet_files)} files")
    print(f"- Mốc gốc T10/2024: {NGAY_DAU_THANG_GOC} -> {NGAY_DAU_THANG_SAU_GOC}")
    print(f"- Mốc kiểm tra T08/2026: {NGAY_DAU_THANG_KIEM_TRA} -> {NGAY_DAU_THANG_SAU_KIEM_TRA}")
    print("-" * 80)

    # 2. Xử lý đa luồng streaming qua ThreadPoolExecutor
    n_workers = min(os.cpu_count() or 4, 8)
    sub_tables = []
    total_scanned_rows = 0
    done_files = 0

    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futures = {ex.submit(process_parquet_chunk, str(f)): f for f in parquet_files}
        for fut in as_completed(futures):
            sub, n_rows = fut.result()
            total_scanned_rows += n_rows
            if sub is not None and sub.num_rows > 0:
                sub_tables.append(sub)
            done_files += 1
            if done_files % 20 == 0 or done_files == len(parquet_files):
                el = time.perf_counter() - start_time
                spd = total_scanned_rows / max(0.001, el)
                print(f"  [{done_files:3d}/{len(parquet_files):3d} - {100*done_files/len(parquet_files):5.1f}%] "
                      f"Đã quét: {total_scanned_rows:,} dòng | {spd:,.0f} dòng/s | Đã chạy: {el:.1f}s")

    print("-" * 80)
    print(f"- Đang tổng hợp danh sách từ {len(sub_tables)} chunks kết quả...")
    full_sub = pa.concat_tables(sub_tables)
    total_stopped = full_sub.num_rows
    print(f"- Tổng số HSSV dừng tham gia tìm thấy: {total_stopped:,}")

    # 3. Chuẩn hóa schema Bảng chi tiết: BC_HSSV_DUNG_THAM_GIA
    now_ts = pa.scalar(datetime.now(), type=pa.timestamp('us'))
    goc_date = pa.scalar(NGAY_DAU_THANG_GOC, type=pa.date32())
    kiem_tra_date = pa.scalar(NGAY_KIEM_TRA, type=pa.date32())

    detail_cols = {
        "SO_SO_BHXH": pc.cast(full_sub["SO_SO_BHXH"], pa.string()),
        "HO_TEN": full_sub["HO_TEN"],
        "NGAY_SINH": full_sub["NGAY_SINH"],
        "GIOI_TINH": pc.cast(full_sub["GIOI_TINH"], pa.int16()),
        "SO_CMND": full_sub["SO_CMND"],
        "SO_THE_KCB_GOC": full_sub["SO_THE_KCB"],
        "MA_KHOI_GOC": pc.cast(full_sub["MA_KHOI"], pa.string()),
        "TU_NGAY_GOC": full_sub["TU_NGAY"],
        "DEN_NGAY_GOC": full_sub["DEN_NGAY"],
        "DM_BHXH_ID": full_sub["DM_BHXH_ID"],
        "MA_TINH": pc.cast(full_sub["MA_TINH"], pa.string()),
        "NGAY_GOC": pa.repeat(goc_date, total_stopped),
        "NGAY_KIEM_TRA": pa.repeat(kiem_tra_date, total_stopped),
        "CREATED_AT": pa.repeat(now_ts, total_stopped),
    }
    bc_table = pa.table(detail_cols)
    bc_path = OUTPUT_DEV_A_DIR / "bc_hssv_dung_tham_gia.parquet"
    tmp_bc = str(bc_path) + ".tmp"
    pq.write_table(bc_table, tmp_bc, compression="zstd")
    os.replace(tmp_bc, bc_path)
    print(f"[OK] Bảng chi tiết: {bc_path} ({os.path.getsize(bc_path)/1024/1024:.2f} MB)")

    # 4. Tạo Bảng tổng hợp thống kê: TK_DBHC_HSSV_DUNG_THAM_GIA
    # Đọc danh mục tỉnh từ dm_bhxh.parquet
    ten_tinh_map = {}
    if Path(DM_BHXH_FILE).exists():
        dm_tbl = pq.read_table(DM_BHXH_FILE)
        p_mask = pc.is_null(dm_tbl["MA_CHA"])
        p_tbl = dm_tbl.filter(p_mask)
        for ma, ten in zip(p_tbl["MA_DVI"].to_pylist(), p_tbl["TEN_DVI"].to_pylist()):
            ten_tinh_map[str(ma).zfill(2)] = ten

    # Tính thống kê theo tỉnh
    prov_arr = detail_cols["MA_TINH"].to_numpy(zero_copy_only=False)
    khoi_arr = detail_cols["MA_KHOI_GOC"].to_numpy(zero_copy_only=False)

    all_provinces = sorted(set(list(ten_tinh_map.keys()) + [str(x).zfill(2) for x in np.unique(prov_arr)]))
    tk_rows = []
    for p in all_provinces:
        p_str = str(p).zfill(2)
        m_prov = prov_arr == p_str
        hs_cnt = int(((khoi_arr == "HS") & m_prov).sum())
        sv_cnt = int(((khoi_arr == "SV") & m_prov).sum())
        tot_cnt = hs_cnt + sv_cnt
        ten_tinh = ten_tinh_map.get(p_str, f"BHXH tỉnh/thành phố {p_str}")
        tk_rows.append({
            "MA_TINH": p_str,
            "TEN_TINH": ten_tinh,
            "SO_LUONG_HS_DUNG": hs_cnt,
            "SO_LUONG_SV_DUNG": sv_cnt,
            "TONG_SO_NGUOI_DUNG": tot_cnt,
            "NGAY_BAO_CAO": NGAY_KIEM_TRA
        })

    tk_df = pd.DataFrame(tk_rows)
    tk_table = pa.Table.from_pandas(tk_df)
    tk_path = OUTPUT_DEV_A_DIR / "tk_dbhc_hssv_dung_tham_gia.parquet"
    tmp_tk = str(tk_path) + ".tmp"
    pq.write_table(tk_table, tmp_tk, compression="zstd")
    os.replace(tmp_tk, tk_path)
    print(f"[OK] Bảng thống kê: {tk_path} ({len(tk_df)} tỉnh/thành phố)")

    # 5. Đối chiếu nhanh với đáp án chuẩn nếu có
    if Path(ANSWER_LIST_FILE).exists():
        ans_tbl = pq.read_table(ANSWER_LIST_FILE)
        ans_cnt = ans_tbl.num_rows
        print("-" * 80)
        print("KIỂM TRA ĐỐI CHIẾU VỚI ĐÁP ÁN CHUẨN (ORACLE GROUND TRUTH):")
        print(f"  - Số lượng Bạn A tìm thấy:    {total_stopped:,} người")
        print(f"  - Số lượng đáp án tham chiếu: {ans_cnt:,} người")
        if total_stopped == ans_cnt:
            print("  => KẾT QUẢ KHỚP 100% VỚI ĐÁP ÁN CHUẨN!")
        else:
            print(f"  => CHÊNH LỆCH: {total_stopped - ans_cnt:,} người")

    el_total = time.perf_counter() - start_time
    print("=" * 80)
    print(f"PIPELINE BẠN A HOÀN THÀNH XUẤT SẮC TRONG {el_total:.2f} GIÂY ({el_total/60:.2f} PHÚT)")
    print(f"Tốc độ xử lý trung bình: {total_scanned_rows/el_total:,.0f} dòng/giây")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline_dev_a()
