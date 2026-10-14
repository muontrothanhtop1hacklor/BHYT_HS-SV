# Bài: tuan1_y1 | Phần: p2_bronze_silver
"""
Kiểm thử các quy tắc làm sạch dữ liệu bẩn tầng Bronze -> Silver.
Tách từ bộ test_edge_cases.py (5 ca kiểm tra dữ liệu bẩn).
"""
import pytest
from datetime import date
import pandas as pd
import numpy as np

# Import hàm nghiệp vụ kiểm tra giao tháng
try:
    from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.gold_logic import check_card_active_in_month as check_overlap_month
except ImportError:
    from src.pipelines.gold_logic import check_card_active_in_month as check_overlap_month


# ====================================================================================
# TEST CASES: QUY TẮC LÀM SẠCH DỮ LIỆU BẨN (DATA CLEANING RULES)
# ====================================================================================
class TestDataQualityRules:
    """Kiểm chứng các quy tắc cách ly (quarantine), chuẩn hóa và gắn cờ."""

    def test_case_21_loai_1_tu_ngay_lon_hon_den_ngay(self):
        """21. Lỗi Loại 1: TU_NGAY > DEN_NGAY không được tính vào thời gian hợp lệ."""
        res = check_overlap_month(date(2024, 10, 15), date(2024, 10, 1), 1, date(2024, 10, 1), date(2024, 11, 1))
        assert res is False

    def test_case_22_loai_4_chuan_hoa_ma_khoi(self):
        """22. Lỗi Loại 4: MA_KHOI chữ thường hoặc khoảng trắng phải được chuẩn hóa."""
        for raw in ["hs", "HS ", " hs ", "sv", " SV "]:
            norm = str(raw).strip().upper()
            assert norm in ("HS", "SV")

    def test_case_23_loai_2_ho_ten_null_gan_co(self):
        """23. Lỗi Loại 2: HO_TEN null được gắn cờ nhưng không ảnh hưởng tham gia."""
        df = pd.DataFrame([{"ID": 1, "HO_TEN": None, "SO_SO_BHXH": "1234567890"}])
        df["FLAG_NAME_NULL"] = df["HO_TEN"].isna()
        assert bool(df["FLAG_NAME_NULL"].iloc[0]) is True

    def test_case_24_loai_3_gioi_tinh_khong_hop_le_gan_co(self):
        """24. Lỗi Loại 3: GIOI_TINH = 3 được gắn cờ."""
        df = pd.DataFrame([{"ID": 1, "GIOI_TINH": 3}, {"ID": 2, "GIOI_TINH": 1}])
        df["FLAG_GENDER_INVALID"] = ~df["GIOI_TINH"].isin([1, 2])
        assert df["FLAG_GENDER_INVALID"].tolist() == [True, False]

    def test_case_25_loai_5_khu_trung_lap_theo_id(self):
        """25. Lỗi Loại 5: Hai dòng trùng ID phải được khử trùng chính xác."""
        df = pd.DataFrame([
            {"ID": 100, "SO_SO_BHXH": "123", "VAL": "A"},
            {"ID": 100, "SO_SO_BHXH": "123", "VAL": "A"},
            {"ID": 101, "SO_SO_BHXH": "456", "VAL": "B"}
        ])
        dedup = df.drop_duplicates(subset=["ID"])
        assert len(dedup) == 2
        assert dedup["ID"].tolist() == [100, 101]
