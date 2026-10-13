"""
Unit tests kiểm tra chất lượng dữ liệu và tính hợp lệ của schema.
"""
import sys
from pathlib import Path
import pytest
import pyarrow.parquet as pq

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import ST_INTHE_DTL_DIR, DM_BHXH_DIR

def test_dm_bhxh_exists_and_valid():
    """Kiểm tra danh mục cơ quan BHXH."""
    dm_file = DM_BHXH_DIR / "dm_bhxh.parquet"
    if not dm_file.exists():
        pytest.skip("Chưa sinh file dm_bhxh.parquet")
    table = pq.read_table(dm_file)
    assert len(table) > 0
    assert "ID" in table.column_names
    assert "MA_CHA" in table.column_names

def test_st_inthe_dtl_schema():
    """Kiểm tra các trường của bảng thẻ."""
    parts = list(ST_INTHE_DTL_DIR.glob("part_*.parquet"))
    if not parts:
        pytest.skip("Chưa sinh dữ liệu ST_INTHE_DTL")
    first_part = parts[0]
    table = pq.read_table(first_part)
    required_cols = [
        "ID", "SO_SO_BHXH", "SO_THE_KCB", "HO_TEN", "NGAY_SINH",
        "GIOI_TINH", "MA_KHOI", "TU_NGAY", "DEN_NGAY", "TRANG_THAI", "DM_BHXH_ID"
    ]
    for col in required_cols:
        assert col in table.column_names, f"Thiếu cột {col} trong ST_INTHE_DTL"
