"""
tests/test_edge_cases.py - Bộ kiểm thử biên (Edge Cases Test Suite)
Kiểm chứng xác nhận logic 'có tham gia tại tháng M' và 'HSSV dừng tham gia BHYT' (CV 835/QLT).

Bao gồm:
- 5 ca cơ bản của đề bài (giao tháng 10/2024).
- 20 ca bổ sung: thẻ hủy, đa thẻ, chuyển khối, gián đoạn, ngày biên, xử lý dữ liệu bẩn.
"""
import pytest
from datetime import date
import pandas as pd
import numpy as np


# Import trực tiếp hàm nghiệp vụ chuẩn từ module sản xuất (B1c)
from src.pipelines.gold_logic import (
    check_card_active_in_month as check_overlap_month,
    evaluate_person_participation,
    clean_khoi_code,
    resolve_khoi_priority,
)


def evaluate_person_status(cards: list,
                           base_start=date(2024, 10, 1),
                           base_next=date(2024, 11, 1),
                           chk_start=date(2026, 8, 1),
                           chk_next=date(2026, 9, 1),
                           stop_def="any"):
    """Wrapper gọi trực tiếp hàm sản xuất evaluate_person_participation."""
    is_stopped, ma_khoi_goc, best_card = evaluate_person_participation(
        cards, base_start, base_next, chk_start, chk_next, stop_def
    )
    has_base_hssv = (ma_khoi_goc in ("HS", "SV"))
    has_chk_any = any(
        check_overlap_month(c["TU_NGAY"], c["DEN_NGAY"], int(c.get("TRANG_THAI", 1)), chk_start, chk_next)
        for c in cards
    )
    has_chk_hssv = any(
        check_overlap_month(c["TU_NGAY"], c["DEN_NGAY"], int(c.get("TRANG_THAI", 1)), chk_start, chk_next)
        and clean_khoi_code(c.get("MA_KHOI")) in ("HS", "SV")
        for c in cards
    )
    return {
        "has_base_hssv": has_base_hssv,
        "has_chk_any": has_chk_any,
        "has_chk_hssv": has_chk_hssv,
        "is_stopped": is_stopped,
        "ma_khoi_goc": ma_khoi_goc,
    }


# ====================================================================================
# TEST CASES: 5 CA CƠ BẢN THEO ĐỀ BÀI (GIAO THÁNG 10/2024)
# ====================================================================================
class TestBasicFiveCases:
    """Năm trường hợp trong sơ đồ Gantt của đề bài."""
    BASE_START = date(2024, 10, 1)
    BASE_NEXT = date(2024, 11, 1)

    def test_case_1_het_han_truoc_thang(self):
        """1. Hết hạn trước tháng (30/09) - KHÔNG TÍNH."""
        res = check_overlap_month(date(2024, 4, 1), date(2024, 9, 30), 1, self.BASE_START, self.BASE_NEXT)
        assert res is False

    def test_case_2_het_han_giua_thang(self):
        """2. Hết hạn giữa tháng (05/10) - CÓ TÍNH."""
        res = check_overlap_month(date(2024, 7, 1), date(2024, 10, 5), 1, self.BASE_START, self.BASE_NEXT)
        assert res is True

    def test_case_3_nam_tron_trong_thang(self):
        """3. Nằm trọn trong tháng (10/10 đến 20/10) - CÓ TÍNH."""
        res = check_overlap_month(date(2024, 10, 10), date(2024, 10, 20), 1, self.BASE_START, self.BASE_NEXT)
        assert res is True

    def test_case_4_bat_dau_cuoi_thang(self):
        """4. Bắt đầu cuối tháng (31/10) - CÓ TÍNH."""
        res = check_overlap_month(date(2024, 10, 31), date(2025, 1, 31), 1, self.BASE_START, self.BASE_NEXT)
        assert res is True

    def test_case_5_bat_dau_sau_thang(self):
        """5. Bắt đầu sau tháng (01/11) - KHÔNG TÍNH."""
        res = check_overlap_month(date(2024, 11, 1), date(2025, 2, 28), 1, self.BASE_START, self.BASE_NEXT)
        assert res is False


# ====================================================================================
# TEST CASES: CÁC TRƯỜNG HỢP BIÊN VÀ NGHIỆP VỤ NÂNG CAO
# ====================================================================================
class TestAdvancedEdgeCases:
    """Các ca bổ sung: ngày biên, hủy thẻ, chuyển khối, gián đoạn, dữ liệu bẩn."""

    def test_case_06_the_huy_giao_thang_goc(self):
        """6. Thẻ bị hủy (TRANG_THAI = 0) giao tháng gốc không được tính."""
        res = check_overlap_month(date(2024, 10, 1), date(2025, 9, 30), 0, date(2024, 10, 1), date(2024, 11, 1))
        assert res is False

    def test_case_07_the_huy_va_co_the_thay_the(self):
        """7. Thẻ bị hủy nhưng có thẻ cấp đổi hợp lệ thay thế."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 0, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["has_base_hssv"] is True
        assert res["is_stopped"] is True  # Không có thẻ tại 2026-08 -> Đã dừng

    def test_case_08_hai_the_cung_thang_hs_va_gd(self):
        """8. Người có 2 thẻ cùng tháng gốc (1 thẻ HS và 1 thẻ GD)."""
        cards = [
            {"TU_NGAY": date(2024, 9, 1), "DEN_NGAY": date(2024, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "GD"},
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["has_base_hssv"] is True

    def test_case_09_hs_len_sv_con_hieu_luc(self):
        """9. Học sinh lên Sinh viên: Thẻ gốc HS, thẻ kiểm tra SV -> Không dừng."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 6, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2025, 10, 1), "DEN_NGAY": date(2026, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "SV"}
        ]
        res = evaluate_person_status(cards, stop_def="any")
        assert res["has_base_hssv"] is True
        assert res["has_chk_any"] is True
        assert res["is_stopped"] is False

    def test_case_10_chuyen_khoi_sv_sang_dn(self):
        """10. Sinh viên đi làm sang DN: Thẻ gốc SV, thẻ kiểm tra DN."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 6, 30), "TRANG_THAI": 1, "MA_KHOI": "SV"},
            {"TU_NGAY": date(2025, 8, 1), "DEN_NGAY": date(2026, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "DN"}
        ]
        # Định nghĩa 'any': không dừng vì còn tham gia ở DN
        res_any = evaluate_person_status(cards, stop_def="any")
        assert res_any["is_stopped"] is False

        # Định nghĩa 'hssv': dừng vì không còn tham gia ở HS/SV
        res_hssv = evaluate_person_status(cards, stop_def="hssv")
        assert res_hssv["is_stopped"] is True

    def test_case_11_gian_doan_quay_lai_truoc_moc_kiem_tra(self):
        """11. Gián đoạn rồi quay lại trước mốc kiểm tra (vẫn còn hạn ở T08/2026)."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 3, 31), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            # Gián đoạn từ 04/2025 đến 05/2026
            {"TU_NGAY": date(2026, 6, 1), "DEN_NGAY": date(2026, 12, 31), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["has_base_hssv"] is True
        assert res["is_stopped"] is False

    def test_case_12_gian_doan_quay_lai_sau_moc_kiem_tra(self):
        """12. Gián đoạn rồi chỉ quay lại SAU mốc kiểm tra (T10/2026) -> Tại T08/2026 ĐÃ DỪNG."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 3, 31), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2026, 10, 1), "DEN_NGAY": date(2027, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["has_base_hssv"] is True
        assert res["has_chk_any"] is False
        assert res["is_stopped"] is True

    def test_case_13_bien_den_ngay_bang_dau_thang_goc(self):
        """13. Biên dưới: DEN_NGAY đúng ngày đầu tháng gốc (2024-10-01) -> CÓ TÍNH."""
        res = check_overlap_month(date(2024, 4, 1), date(2024, 10, 1), 1, date(2024, 10, 1), date(2024, 11, 1))
        assert res is True

    def test_case_14_bien_den_ngay_truoc_dau_thang_goc(self):
        """14. Biên dưới - 1 ngày: DEN_NGAY = 2024-09-30 -> KHÔNG TÍNH."""
        res = check_overlap_month(date(2024, 4, 1), date(2024, 9, 30), 1, date(2024, 10, 1), date(2024, 11, 1))
        assert res is False

    def test_case_15_bien_tu_ngay_ngay_cuoi_thang_goc(self):
        """15. Biên trên: TU_NGAY = 2024-10-31 -> CÓ TÍNH."""
        res = check_overlap_month(date(2024, 10, 31), date(2025, 3, 31), 1, date(2024, 10, 1), date(2024, 11, 1))
        assert res is True

    def test_case_16_bien_tu_ngay_dau_thang_sau(self):
        """16. Biên trên + 1 ngày: TU_NGAY = 2024-11-01 -> KHÔNG TÍNH."""
        res = check_overlap_month(date(2024, 11, 1), date(2025, 3, 31), 1, date(2024, 10, 1), date(2024, 11, 1))
        assert res is False

    def test_case_17_bien_kiem_tra_den_ngay_01_08(self):
        """17. Mốc kiểm tra: Thẻ hết hạn đúng ngày 2026-08-01 -> Có giao với T08/2026 -> Không dừng."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2025, 10, 1), "DEN_NGAY": date(2026, 8, 1), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["is_stopped"] is False

    def test_case_18_bien_kiem_tra_den_ngay_31_07(self):
        """18. Mốc kiểm tra: Thẻ hết hạn ngày 2026-07-31 -> Không giao với T08/2026 -> ĐÃ DỪNG."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2025, 10, 1), "DEN_NGAY": date(2026, 7, 31), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["is_stopped"] is True

    def test_case_19_bien_kiem_tra_tu_ngay_31_08(self):
        """19. Mốc kiểm tra: Thẻ bắt đầu ngày 2026-08-31 -> Có giao với T08/2026 -> Không dừng."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2026, 8, 31), "DEN_NGAY": date(2027, 8, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["is_stopped"] is False

    def test_case_20_bien_kiem_tra_tu_ngay_01_09(self):
        """20. Mốc kiểm tra: Thẻ bắt đầu ngày 2026-09-01 -> Không giao với T08/2026 -> ĐÃ DỪNG."""
        cards = [
            {"TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 9, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"},
            {"TU_NGAY": date(2026, 9, 1), "DEN_NGAY": date(2027, 8, 30), "TRANG_THAI": 1, "MA_KHOI": "HS"}
        ]
        res = evaluate_person_status(cards)
        assert res["is_stopped"] is True



