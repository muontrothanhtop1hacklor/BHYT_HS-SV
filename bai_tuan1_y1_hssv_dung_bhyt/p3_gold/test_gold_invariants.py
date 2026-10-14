# Bài: tuan1_y1 | Phần: p3_gold
# -*- coding: utf-8 -*-
"""
tests/test_gold_invariants.py
Bộ kiểm thử đơn vị, kiểm thử biên và kiểm tra bất biến dữ liệu tầng Gold (CV 835/QLT).

Các kiểm thử bao gồm:
1. Bất biến dữ liệu tầng Gold (Invariant Checks):
   - Tổng TONG_SO_NGUOI_DUNG ở bảng TK bằng đúng số dòng bảng BC.
   - Tổng HS + SV ở bảng TK bằng đúng TONG_SO_NGUOI_DUNG.
   - Bảng TK có đúng 63 tỉnh thành phố.
   - Mọi dòng trong BC chỉ mang MA_KHOI_GOC là 'HS' hoặc 'SV'.
2. Kiểm thử biên nghiệp vụ tầng Gold (gọi hàm sản xuất gold_logic.py):
   - Phân loại tách HS / SV.
   - Người có cả 2 thẻ HS và SV ở tháng gốc: Ưu tiên SV.
   - Thẻ hủy TRANG_THAI = 0 không tính tham gia.
   - Chuyển khối sang DN/GD tại tháng kiểm tra: Dừng ở 'hssv' nhưng KHÔNG dừng ở 'any'.
   - Tham số stop_def='hssv' cho số lượng người dừng lớn hơn stop_def='any'.
"""

import os
from datetime import date
import pytest
import pandas as pd
import pyarrow.parquet as pq

try:
    from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.gold_logic import (
        check_card_active_in_month,
        evaluate_person_participation,
        clean_khoi_code,
        resolve_khoi_priority,
    )
except ImportError:
    from src.pipelines.gold_logic import (
        check_card_active_in_month,
        evaluate_person_participation,
        clean_khoi_code,
        resolve_khoi_priority,
    )


class TestGoldBusinessLogicUnit:
    """Kiểm thử đơn vị các hàm sản xuất trong gold_logic.py."""

    def test_khoi_priority_hs_only(self):
        assert resolve_khoi_priority(has_hs=True, has_sv=False) == "HS"

    def test_khoi_priority_sv_only(self):
        assert resolve_khoi_priority(has_hs=False, has_sv=True) == "SV"

    def test_khoi_priority_both_hs_and_sv(self):
        """Kỳ vọng: Người có cả thẻ HS và SV ưu tiên cấp bậc SV."""
        assert resolve_khoi_priority(has_hs=True, has_sv=True) == "SV"

    def test_evaluate_person_both_cards_base_month(self):
        """Kỳ vọng: Người có 2 thẻ (HS và SV) ở T10/2024, không có thẻ T8/2026 -> dừng, khối gốc là SV."""
        cards = [
            {"TU_NGAY": date(2024, 1, 1), "DEN_NGAY": date(2024, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2024, 9, 1), "DEN_NGAY": date(2025, 8, 31), "TRANG_THAI": 1, "MA_KHOI": "SV"},
        ]
        is_stopped, ma_khoi, best_card = evaluate_person_participation(cards, stop_def="any")
        assert is_stopped is True
        assert ma_khoi == "SV"
        assert best_card["MA_KHOI"] == "SV"

    def test_evaluate_switch_dn_stop_def_difference(self):
        """
        Kỳ vọng: Người có thẻ SV ở T10/2024 và thẻ DN ở T8/2026:
        - Với stop_def='any': KHÔNG dừng (đang tham gia DN).
        - Với stop_def='hssv': DỪNG (đã dừng HSSV).
        """
        cards = [
            {"TU_NGAY": date(2024, 1, 1), "DEN_NGAY": date(2024, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "SV"},
            {"TU_NGAY": date(2026, 1, 1), "DEN_NGAY": date(2026, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "DN"},
        ]
        is_stopped_any, _, _ = evaluate_person_participation(cards, stop_def="any")
        is_stopped_hssv, _, _ = evaluate_person_participation(cards, stop_def="hssv")

        assert is_stopped_any is False
        assert is_stopped_hssv is True

    def test_cancelled_card_ignored(self):
        """Kỳ vọng: Thẻ hủy TRANG_THAI = 0 không được tính là tham gia."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2024, 10, 31), "TRANG_THAI": 0, "MA_KHOI": "HS"},
        ]
        is_stopped, ma_khoi, _ = evaluate_person_participation(cards, stop_def="any")
        assert is_stopped is False  # Không có thẻ hợp lệ ở tháng gốc


class TestGoldInvariantsOnActualOutput:
    """Kiểm tra bất biến dữ liệu trên file Gold thực tế đã xuất ra."""

    @pytest.fixture(scope="class")
    def gold_data(self):
        gold_dir = "data/output/gold/20241001_20260801_any"
        bc_path = os.path.join(gold_dir, "bc_hssv_dung_tham_gia.parquet")
        tk_path = os.path.join(gold_dir, "tk_dbhc_hssv_dung_tham_gia.csv")

        if not os.path.exists(bc_path) or not os.path.exists(tk_path):
            pytest.skip("Chưa tạo dữ liệu Gold tại " + gold_dir)

        df_bc = pq.read_table(bc_path).to_pandas()
        df_tk = pd.read_csv(tk_path, dtype={"MA_TINH": str})
        return df_bc, df_tk

    def test_invariant_1_total_count_matches(self, gold_data):
        """Bất biến 1: Tổng số người trên bảng TK phải bằng đúng số dòng bảng BC."""
        df_bc, df_tk = gold_data
        total_tk = df_tk["TONG_SO_NGUOI_DUNG"].sum()
        total_bc = len(df_bc)
        assert total_tk == total_bc, f"Lệch tổng: TK={total_tk} != BC={total_bc}"

    def test_invariant_2_hs_plus_sv_equals_total(self, gold_data):
        """Bất biến 2: Trong bảng TK, SO_LUONG_HS_DUNG + SO_LUONG_SV_DUNG == TONG_SO_NGUOI_DUNG cho mọi tỉnh."""
        _, df_tk = gold_data
        calculated_total = df_tk["SO_LUONG_HS_DUNG"] + df_tk["SO_LUONG_SV_DUNG"]
        diff = (calculated_total != df_tk["TONG_SO_NGUOI_DUNG"]).sum()
        assert diff == 0, f"Có {diff} tỉnh bị sai lệch tổng HS + SV != TONG"

    def test_invariant_3_province_count_is_63(self, gold_data):
        """Bất biến 3: Bảng TK phải có đúng 63 tỉnh/thành phố."""
        _, df_tk = gold_data
        assert len(df_tk) == 63, f"Số tỉnh không bằng 63: {len(df_tk)}"

    def test_invariant_4_bc_khoi_values(self, gold_data):
        """Bất biến 4: Mọi dòng trong BC chỉ có thể mang MA_KHOI_GOC là 'HS' hoặc 'SV'."""
        df_bc, _ = gold_data
        invalid_khoi = (~df_bc["MA_KHOI_GOC"].isin(["HS", "SV"])).sum()
        assert invalid_khoi == 0, f"Có {invalid_khoi} dòng có MA_KHOI_GOC không hợp lệ"

    def test_invariant_5_bc_so_so_unique(self, gold_data):
        """Bất biến 5: Khóa chính SO_SO_BHXH trong bảng BC phải là duy nhất tuyệt đối."""
        df_bc, _ = gold_data
        assert df_bc["SO_SO_BHXH"].is_unique, "SO_SO_BHXH trong bảng BC bị trùng lặp!"


class TestGoldFailureScenarios:
    """Kịch bản lỗi: tham số sai, file thiếu -> pipeline phải báo lỗi rõ ràng."""

    def test_invalid_stop_def_raises_error(self):
        try:
            from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold import run_gold_pipeline
        except ImportError:
            from scripts.build_gold import run_gold_pipeline
        with pytest.raises(ValueError, match="stop_def"):
            run_gold_pipeline(stop_def="invalid_def")

    def test_invalid_date_range_raises_error(self):
        try:
            from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold import run_gold_pipeline
        except ImportError:
            from scripts.build_gold import run_gold_pipeline
        with pytest.raises(ValueError, match="base_start"):
            run_gold_pipeline(base_start="2024-11-01", base_next="2024-10-01")

    def test_missing_dm_bhxh_file_raises_error(self):
        try:
            from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold import run_gold_pipeline
        except ImportError:
            from scripts.build_gold import run_gold_pipeline
        with pytest.raises(FileNotFoundError, match="BHXH"):
            run_gold_pipeline(dm_bhxh_path="data/non_existent_dm.parquet")

    def test_missing_silver_dir_raises_error(self):
        try:
            from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold import run_gold_pipeline
        except ImportError:
            from scripts.build_gold import run_gold_pipeline
        with pytest.raises(FileNotFoundError, match="Silver Parquet"):
            run_gold_pipeline(silver_dir="data/non_existent_silver")
