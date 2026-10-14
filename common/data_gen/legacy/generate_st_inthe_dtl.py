# Bài: dùng chung | common/data_gen/legacy
"""
Script sinh dữ liệu thẻ BHYT chi tiết (ST_INTHE_DTL) chuẩn thực tế.
Quy mô: Mặc định sinh thử nghiệm hoặc full 200M dòng.
Lưu dưới dạng các chunk Parquet nén Snappy/ZSTD trong data/source/st_inthe_dtl/.
"""
import sys
import argparse
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from datetime import date, timedelta
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# Thêm root vào sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from common.config import ST_INTHE_DTL_DIR, RANDOM_SEED, CHUNK_PERSONS as CHUNK_SIZE

HO_LIST = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]
DEM_LIST = ["Văn", "Thị", "Đức", "Minh", "Thanh", "Hồng", "Tuấn", "Hải", "Xuân", "Phương", "Gia", "Ngọc", "Thu", "Mai"]
TEN_LIST = ["An", "Bình", "Cường", "Dũng", "Em", "Giang", "Hà", "Hải", "Khánh", "Linh", "Minh", "Nam", "Nga", "Phong", "Quân", "Sơn", "Tâm", "Thảo", "Trang", "Tùng", "Vinh", "Yến"]

def generate_records(total_rows: int, chunk_size: int, seed: int):
    ST_INTHE_DTL_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    
    print(f"=== BẮT ĐẦU SINH DỮ LIỆU ST_INTHE_DTL ===")
    print(f"- Tổng số dòng mục tiêu: {total_rows:,}")
    print(f"- Kích thước mỗi chunk:   {chunk_size:,}")
    print(f"- Random Seed:           {seed}")
    print(f"- Thư mục lưu:           {ST_INTHE_DTL_DIR}")
    
    total_chunks = (total_rows + chunk_size - 1) // chunk_size
    current_record_id = 1
    
    for chunk_idx in range(1, total_chunks + 1):
        rows_in_this_chunk = min(chunk_size, total_rows - (chunk_idx - 1) * chunk_size)
        if rows_in_this_chunk <= 0:
            break
            
        # 1. Sinh các trường định danh
        # Người tham gia: chia sẻ không gian ~20 triệu người
        person_nums = rng.integers(10000000, 30000000, size=rows_in_this_chunk)
        so_so_bhxh = [f"{num:010d}" for num in person_nums]
        
        # 2. Phân loại khối đối tượng:
        # Tỷ lệ: 20% HS, 10% SV, 40% DN, 20% GD, 10% khác (TE, HT)
        block_types = rng.choice(
            ["HS", "SV", "DN", "GD", "TE", "HT"],
            size=rows_in_this_chunk,
            p=[0.20, 0.10, 0.40, 0.20, 0.05, 0.05]
        )
        
        # 3. Mã thẻ BHYT (15 ký tự: 2 ký tự khối + 1 mã quyền lợi + 2 mã tỉnh + 10 mã số)
        provinces = rng.choice(["01", "79", "48", "31", "92", "74", "75", "24", "49"], size=rows_in_this_chunk)
        so_the_kcb = [f"{blk}4{prv}{ss}" for blk, prv, ss in zip(block_types, provinces, so_so_bhxh)]
        
        # 4. Thông tin cá nhân
        ho = rng.choice(HO_LIST, size=rows_in_this_chunk)
        dem = rng.choice(DEM_LIST, size=rows_in_this_chunk)
        ten = rng.choice(TEN_LIST, size=rows_in_this_chunk)
        ho_ten = [f"{h} {d} {t}" for h, d, t in zip(ho, dem, ten)]
        
        # Ngày sinh
        # HS: 2006-2018 (6-18 tuổi), SV: 1999-2006 (18-25 tuổi), DN/GD: 1965-2006
        birth_years = np.where(
            block_types == "HS", rng.integers(2006, 2018, size=rows_in_this_chunk),
            np.where(
                block_types == "SV", rng.integers(1999, 2006, size=rows_in_this_chunk),
                rng.integers(1965, 2006, size=rows_in_this_chunk)
            )
        )
        birth_months = rng.integers(1, 13, size=rows_in_this_chunk)
        birth_days = rng.integers(1, 29, size=rows_in_this_chunk)
        ngay_sinh = [date(y, m, d) for y, m, d in zip(birth_years, birth_months, birth_days)]
        
        gioi_tinh = rng.choice([1, 2], size=rows_in_this_chunk).astype(np.int16)
        so_cmnd = [f"0{rng.integers(10000000000, 99999999999)}" for _ in range(rows_in_this_chunk)]
        dia_chi = [f"Địa chỉ mẫu {i}" for i in range(rows_in_this_chunk)]
        
        # 5. Thời hạn thẻ (TU_NGAY, DEN_NGAY) giai đoạn 2024 - 2026
        # Mô phỏng mùa vụ HSSV: Nhiều thẻ bắt đầu tháng 10/2024 hoặc 01/2025
        card_start_base = rng.choice([
            date(2024, 10, 1),
            date(2024, 1, 1),
            date(2024, 7, 1),
            date(2025, 1, 1),
            date(2025, 10, 1),
            date(2026, 1, 1),
        ], size=rows_in_this_chunk, p=[0.30, 0.15, 0.10, 0.20, 0.15, 0.10])
        
        # Thời hạn thẻ: 3 tháng, 6 tháng, 12 tháng
        durations = rng.choice([90, 180, 365], size=rows_in_this_chunk, p=[0.15, 0.25, 0.60])
        
        tu_ngay = [d + timedelta(days=int(rng.integers(-15, 15))) for d in card_start_base]
        den_ngay = [t + timedelta(days=int(dur)) for t, dur in zip(tu_ngay, durations)]
        
        # 6. Trạng thái thẻ: 97% hiệu lực (1), 3% hủy/cấp đổi (0)
        trang_thai = rng.choice([1, 0], size=rows_in_this_chunk, p=[0.97, 0.03]).astype(np.int16)
        
        # 7. Cơ quan BHXH quản lý
        dm_bhxh_id = rng.integers(1, 160, size=rows_in_this_chunk).astype(np.int32)
        
        # ID bản ghi
        ids = np.arange(current_record_id, current_record_id + rows_in_this_chunk, dtype=np.int64)
        current_record_id += rows_in_this_chunk
        
        # Tạo PyArrow Table
        table = pa.Table.from_arrays(
            [
                pa.array(ids),
                pa.array(so_so_bhxh),
                pa.array(so_the_kcb),
                pa.array(ho_ten),
                pa.array(ngay_sinh, type=pa.date32()),
                pa.array(gioi_tinh),
                pa.array(so_cmnd),
                pa.array(dia_chi),
                pa.array(block_types),
                pa.array(tu_ngay, type=pa.date32()),
                pa.array(den_ngay, type=pa.date32()),
                pa.array(trang_thai),
                pa.array(dm_bhxh_id),
            ],
            names=[
                "ID", "SO_SO_BHXH", "SO_THE_KCB", "HO_TEN", "NGAY_SINH",
                "GIOI_TINH", "SO_CMND", "DIA_CHI", "MA_KHOI", "TU_NGAY",
                "DEN_NGAY", "TRANG_THAI", "DM_BHXH_ID"
            ]
        )
        
        chunk_file = ST_INTHE_DTL_DIR / f"part_{chunk_idx:04d}.parquet"
        pq.write_table(table, chunk_file, compression="SNAPPY")
        print(f"[{chunk_idx}/{total_chunks}] Đã ghi {rows_in_this_chunk:,} dòng vào {chunk_file.name}")
        
    print(f"=== HOÀN THÀNH SINH {total_rows:,} DÒNG THÀNH CÔNG ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sinh dữ liệu fake ST_INTHE_DTL.")
    parser.add_argument("--rows", type=int, default=1_000_000, help="Tổng số dòng cần sinh")
    parser.add_argument("--chunk-size", type=int, default=500_000, help="Kích thước mỗi chunk parquet")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed")
    args = parser.parse_args()
    
    generate_records(args.rows, args.chunk_size, args.seed)
