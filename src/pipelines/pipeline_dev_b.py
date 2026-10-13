"""
Pipeline xử lý của BẠN B:
Giải quyết bài toán Ý 1 (CV 835/QLT) - Lọc HSSV dừng tham gia BHYT.
Đầu ra:
1. data/output/dev_b/bc_hssv_dung_tham_gia.parquet
2. data/output/dev_b/tk_dbhc_hssv_dung_tham_gia.parquet
"""
import sys
import time
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import pyarrow.dataset as ds
import pyarrow.compute as pc
import pyarrow as pa
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import (
    ST_INTHE_DTL_DIR, DM_BHXH_DIR, OUTPUT_DEV_B_DIR,
    NGAY_DAU_THANG_GOC, NGAY_DAU_THANG_SAU_GOC, NGAY_KIEM_TRA
)

def run_pipeline_dev_b():
    OUTPUT_DEV_B_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    print("=== BẮT ĐẦU CHẠY PIPELINE BẠN B ===")
    
    parquet_files = list(ST_INTHE_DTL_DIR.glob("part_*.parquet"))
    if not parquet_files:
        print(f"[!] Không tìm thấy dữ liệu trong {ST_INTHE_DTL_DIR}")
        return
        
    dataset = ds.dataset(ST_INTHE_DTL_DIR, format="parquet")
    
    # Bạn B tiếp cận theo cách lọc:
    # 1. Lọc thẻ HSSV có hiệu lực trong T10/2024
    filt_oct = (
        (pc.field("TRANG_THAI") == 1) &
        (pc.field("MA_KHOI").isin(["HS", "SV"])) &
        (pc.field("TU_NGAY") < pa.scalar(NGAY_DAU_THANG_SAU_GOC, type=pa.date32())) &
        (pc.field("DEN_NGAY") >= pa.scalar(NGAY_DAU_THANG_GOC, type=pa.date32()))
    )
    t_oct = dataset.to_table(filter=filt_oct)
    df_oct = t_oct.to_pandas()
    
    # Lấy bản ghi thẻ có TU_NGAY, DEN_NGAY lớn nhất cho mỗi người
    df_oct = df_oct.sort_values(by=["DEN_NGAY", "TU_NGAY"], ascending=[False, False])
    df_oct_unique = df_oct.drop_duplicates(subset=["SO_SO_BHXH"], keep="first")
    
    # 2. Lọc thẻ còn hiệu lực tại ngày kiểm tra
    filt_now = (
        (pc.field("TRANG_THAI") == 1) &
        (pc.field("TU_NGAY") <= pa.scalar(NGAY_KIEM_TRA, type=pa.date32())) &
        (pc.field("DEN_NGAY") >= pa.scalar(NGAY_KIEM_TRA, type=pa.date32()))
    )
    t_now = dataset.to_table(filter=filt_now, columns=["SO_SO_BHXH"])
    df_now = t_now.to_pandas().drop_duplicates()
    
    # 3. Phép Left Join IS NULL để loại trừ
    merged = df_oct_unique.merge(
        df_now, on="SO_SO_BHXH", how="left", indicator=True
    )
    df_stopped = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"]).copy()
    
    # 4. Gắn mã tỉnh từ danh mục
    dm_file = DM_BHXH_DIR / "dm_bhxh.parquet"
    if dm_file.exists():
        df_dm = pd.read_parquet(dm_file)
        df_stopped = df_stopped.merge(df_dm[["ID", "MA_CHA"]], left_on="DM_BHXH_ID", right_on="ID", how="left")
        df_stopped["MA_TINH"] = df_stopped["MA_CHA"].fillna("000")
        df_stopped.drop(columns=["ID_y", "MA_CHA"], errors="ignore", inplace=True)
    else:
        df_stopped["MA_TINH"] = "000"
        
    df_stopped.rename(columns={
        "SO_THE_KCB": "SO_THE_KCB_GOC",
        "MA_KHOI": "MA_KHOI_GOC",
        "TU_NGAY": "TU_NGAY_GOC",
        "DEN_NGAY": "DEN_NGAY_GOC"
    }, inplace=True)
    df_stopped["NGAY_GOC"] = NGAY_DAU_THANG_GOC
    df_stopped["NGAY_KIEM_TRA"] = NGAY_KIEM_TRA
    
    # Xuất file chi tiết
    bc_path = OUTPUT_DEV_B_DIR / "bc_hssv_dung_tham_gia.parquet"
    df_stopped.to_parquet(bc_path, index=False)
    
    # 5. Thống kê theo tỉnh
    df_tk = df_stopped.groupby("MA_TINH").agg(
        SO_LUONG_HS_DUNG=("MA_KHOI_GOC", lambda x: (x == "HS").sum()),
        SO_LUONG_SV_DUNG=("MA_KHOI_GOC", lambda x: (x == "SV").sum()),
        TONG_SO_NGUOI_DUNG=("SO_SO_BHXH", "count")
    ).reset_index()
    df_tk["NGAY_BAO_CAO"] = NGAY_KIEM_TRA
    
    tk_path = OUTPUT_DEV_B_DIR / "tk_dbhc_hssv_dung_tham_gia.parquet"
    df_tk.to_parquet(tk_path, index=False)
    
    elapsed = time.time() - start_time
    print(f"=== PIPELINE BẠN B HOÀN THÀNH ({elapsed:.2f}s) ===")
    print(f"- File chi tiết: {bc_path}")
    print(f"- File thống kê: {tk_path}")

if __name__ == "__main__":
    run_pipeline_dev_b()
