"""
Sinh danh mục cơ quan BHXH (DM_BHXH) cho 63 tỉnh/thành phố và các quận/huyện trực thuộc.
Xuất ra định dạng Parquet và CSV trong data/source/dm_bhxh/.
"""
import sys
from pathlib import Path
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm root vào sys.path để import config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import DM_BHXH_DIR

# 63 tỉnh thành phố với mã tỉnh BHXH chuẩn
PROVINCES = [
    ("001", "BHXH Thành phố Hà Nội"),
    ("079", "BHXH Thành phố Hồ Chí Minh"),
    ("048", "BHXH Thành phố Đà Nẵng"),
    ("031", "BHXH Thành phố Hải Phòng"),
    ("092", "BHXH Thành phố Cần Thơ"),
    ("074", "BHXH Tỉnh Bình Dương"),
    ("075", "BHXH Tỉnh Đồng Nai"),
    ("077", "BHXH Tỉnh Bà Rịa - Vũng Tàu"),
    ("024", "BHXH Tỉnh Bắc Ninh"),
    ("022", "BHXH Tỉnh Quảng Ninh"),
    ("049", "BHXH Tỉnh Quảng Nam"),
    ("046", "BHXH Tỉnh Thừa Thiên Huế"),
    ("056", "BHXH Tỉnh Khánh Hòa"),
    ("066", "BHXH Tỉnh Đắk Lắk"),
    ("068", "BHXH Tỉnh Lâm Đồng"),
    ("080", "BHXH Tỉnh Long An"),
    ("082", "BHXH Tỉnh Tiền Giang"),
    ("089", "BHXH Tỉnh An Giang"),
    ("091", "BHXH Tỉnh Kiên Giang"),
    ("096", "BHXH Tỉnh Cà Mau"),
]

def generate_dm_bhxh():
    DM_BHXH_DIR.mkdir(parents=True, exist_ok=True)
    
    records = []
    current_id = 1
    
    for prov_code, prov_name in PROVINCES:
        # Cấp tỉnh
        records.append({
            "ID": current_id,
            "MA_DVI": prov_code + "00",
            "TEN_DVI": prov_name,
            "MA_CHA": prov_code
        })
        current_id += 1
        
        # Tạo 5 - 10 quận/huyện trực thuộc
        for district_idx in range(1, 8):
            records.append({
                "ID": current_id,
                "MA_DVI": f"{prov_code}{district_idx:02d}",
                "TEN_DVI": f"BHXH Quận/Huyện {district_idx:02d} - {prov_name}",
                "MA_CHA": prov_code
            })
            current_id += 1
            
    df = pd.DataFrame(records)
    
    parquet_path = DM_BHXH_DIR / "dm_bhxh.parquet"
    csv_path = DM_BHXH_DIR / "dm_bhxh.csv"
    
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"[OK] Đã sinh {len(df)} đơn vị DM_BHXH:")
    print(f"     - Parquet: {parquet_path}")
    print(f"     - CSV:     {csv_path}")

if __name__ == "__main__":
    generate_dm_bhxh()
