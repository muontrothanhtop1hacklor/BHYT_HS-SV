# Bài: dùng chung | common/config
"""
Cấu hình tập trung cho toàn bộ dự án xử lý dữ liệu 200M dòng.
"""
from pathlib import Path
from datetime import date

# 1. Thư mục gốc & đường dẫn
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Nguồn dữ liệu BHYT 200M dòng (gen_bhyt sinh vào data/bhyt_data)
BHYT_DATA_DIR = DATA_DIR / "bhyt_data"
SOURCE_DIR = DATA_DIR / "source"

if (BHYT_DATA_DIR / "ST_INTHE_DTL").exists():
    ST_INTHE_DTL_DIR = BHYT_DATA_DIR / "ST_INTHE_DTL"
elif (BHYT_DATA_DIR / "st_inthe_dtl").exists():
    ST_INTHE_DTL_DIR = BHYT_DATA_DIR / "st_inthe_dtl"
else:
    ST_INTHE_DTL_DIR = SOURCE_DIR / "st_inthe_dtl"

if (BHYT_DATA_DIR / "DM_BHXH.parquet").exists():
    DM_BHXH_FILE = BHYT_DATA_DIR / "DM_BHXH.parquet"
elif (BHYT_DATA_DIR / "dm_bhxh.parquet").exists():
    DM_BHXH_FILE = BHYT_DATA_DIR / "dm_bhxh.parquet"
elif (BHYT_DATA_DIR / "DM_BHXH.csv").exists():
    DM_BHXH_FILE = BHYT_DATA_DIR / "DM_BHXH.csv"
else:
    DM_BHXH_FILE = SOURCE_DIR / "dm_bhxh" / "dm_bhxh.parquet"

DM_BHXH_DIR = BHYT_DATA_DIR if (BHYT_DATA_DIR / "DM_BHXH.csv").exists() or (BHYT_DATA_DIR / "dm_bhxh.parquet").exists() or (BHYT_DATA_DIR / "DM_BHXH.parquet").exists() else (SOURCE_DIR / "dm_bhxh")
SCENARIO_DIR = BHYT_DATA_DIR / "SCENARIO"

OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DEV_A_DIR = OUTPUT_DIR / "dev_a"
OUTPUT_DEV_B_DIR = OUTPUT_DIR / "dev_b"
RECONCILIATION_DIR = OUTPUT_DIR / "reconciliation"

# Đường dẫn kết quả tầng Gold và kết quả đối soát trao đổi
GOLD_RESULT_DIR = OUTPUT_DIR / "gold" / "20241001_20260801_any"
GOLD_BC_FILE = GOLD_RESULT_DIR / "bc_hssv_dung_tham_gia.parquet"
GOLD_TK_CSV = GOLD_RESULT_DIR / "tk_dbhc_hssv_dung_tham_gia.csv"
KET_QUA_CUA_BAN_DIR = PROJECT_ROOT / "bai_tuan1_y1_hssv_dung_bhyt" / "p4_doi_soat" / "ket_qua_cua_ban"


# Đường dẫn bộ đáp án tham chiếu (Ground Truth)
ANSWER_DIR = DATA_DIR / "bhyt_answer"
ANSWER_LIST_FILE = ANSWER_DIR / "answer_list.parquet"
ANSWER_BY_TINH_FILE = ANSWER_DIR / "answer_by_tinh.csv"

# 2. Các tham số mốc thời gian nghiệp vụ (CV 835/QLT)
# Mốc gốc T10/2024: giao tháng 10/2024 nghĩa là TU_NGAY < 2024-11-01 và DEN_NGAY >= 2024-10-01
NGAY_DAU_THANG_GOC = date(2024, 10, 1)
NGAY_DAU_THANG_SAU_GOC = date(2024, 11, 1)

# Mốc kiểm tra "đến nay" (T08/2026): giao tháng 08/2026 nghĩa là TU_NGAY < 2026-09-01 và DEN_NGAY >= 2026-08-01
NGAY_DAU_THANG_KIEM_TRA = date(2026, 8, 1)
NGAY_DAU_THANG_SAU_KIEM_TRA = date(2026, 9, 1)

# Ngày ký công văn 835/QLT (dùng hiển thị báo cáo chi tiết)
NGAY_KIEM_TRA = date(2026, 8, 10)

# 3. Tham số sinh Fake Data
RANDOM_SEED = 20261012                   # Seed chuẩn thực tế
TOTAL_PERSONS = 20_000_000               # 20 triệu người
TOTAL_RECORDS_TARGET = 200_000_000       # ~200 triệu dòng thẻ
CHUNK_PERSONS = 100_000                  # 100k người/chunk (~1M dòng/chunk)
