# -*- coding: utf-8 -*-
"""
test_timeline_gaps.py
Bộ kiểm thử đơn vị toàn diện cho thuật toán xử lý chuỗi thời gian và tính gián đoạn (CV 835/QLT - Ý 2).

Bao phủ tính liên tục/chồng lấn, gap giữa các thẻ và ở hai biên kỳ, ngưỡng 90 ngày,
trạng thái thẻ, điều kiện ứng viên và quy tắc chọn thẻ đại diện.
"""
from datetime import date
import pytest
from bai_tuan2_y2_hssv_gian_doan.p2_thuat_toan_timeline.timeline_algorithm import (
    merge_intervals,
    calculate_gaps,
    evaluate_person_gap_y2,
)


def test_continuous_cards():
    """Ca 1: Thẻ liên tục hoàn toàn -> Gap = 0."""
    intervals = [
        (date(2024, 7, 1), date(2024, 12, 31)),
        (date(2025, 1, 1), date(2025, 6, 30)),
        (date(2025, 7, 1), date(2026, 12, 31)),
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 1
    assert merged[0] == (date(2024, 7, 1), date(2026, 12, 31))
    
    total_days, num_gaps, details = calculate_gaps(merged)
    assert total_days == 0
    assert num_gaps == 0


def test_overlapping_cards():
    """Ca 2: Thẻ chồng lấn gối đầu -> Gap = 0."""
    intervals = [
        (date(2024, 10, 1), date(2025, 4, 30)),
        (date(2025, 3, 15), date(2025, 12, 31)),
        (date(2025, 11, 1), date(2026, 8, 31)),
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 1
    assert merged[0] == (date(2024, 10, 1), date(2026, 8, 31))
    
    total_days, num_gaps, _ = calculate_gaps(merged)
    assert total_days == 0
    assert num_gaps == 0


def test_short_gap_1_month():
    """Ca 3: Gián đoạn 1 tháng (30 ngày) -> Tổng ngày < 90 ngày -> Không đạt."""
    intervals = [
        (date(2024, 10, 1), date(2025, 3, 31)),
        (date(2025, 5, 1), date(2026, 7, 31)),  # Nghỉ tháng 4: 01/04 đến 30/04 = 30 ngày
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 2
    
    total_days, num_gaps, details = calculate_gaps(merged)
    assert num_gaps == 1
    assert total_days == 30
    assert details[0] == (date(2025, 4, 1), date(2025, 4, 30), 30)


def test_short_gap_2_months():
    """Ca 4: Gián đoạn 2 tháng (61 ngày) -> Tổng ngày < 90 ngày -> Không đạt."""
    intervals = [
        (date(2024, 10, 1), date(2025, 3, 31)),
        (date(2025, 6, 1), date(2026, 7, 31)),  # Nghỉ tháng 4, 5: 30 + 31 = 61 ngày
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 2
    
    total_days, num_gaps, details = calculate_gaps(merged)
    assert num_gaps == 1
    assert total_days == 61


def test_single_gap_3_months():
    """Ca 5: Gián đoạn 3 tháng (91 ngày) -> Thỏa mãn >= 90 ngày."""
    intervals = [
        (date(2024, 10, 1), date(2025, 3, 31)),
        (date(2025, 7, 1), date(2026, 7, 31)),  # Nghỉ tháng 4, 5, 6: 30 + 31 + 30 = 91 ngày
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 2
    
    total_days, num_gaps, details = calculate_gaps(merged)
    assert num_gaps == 1
    assert total_days == 91
    assert total_days >= 90


def test_multiple_fragmented_gaps():
    """Ca 6: Hai đợt gián đoạn rải rác: 30 ngày + 61 ngày = 91 ngày -> Thỏa mãn cộng dồn."""
    intervals = [
        (date(2024, 10, 1), date(2025, 3, 31)),
        (date(2025, 5, 1), date(2025, 10, 31)),  # Gap 1: 01/04 - 30/04 (30 ngày)
        (date(2026, 1, 1), date(2026, 7, 31)),   # Gap 2: 01/11 - 31/12 (61 ngày)
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 3
    
    total_days, num_gaps, details = calculate_gaps(merged)
    assert num_gaps == 2
    assert total_days == 30 + 61
    assert total_days >= 90


def test_person_evaluator_satisfies():
    """Ca 7: Kiểm thử hàm đánh giá toàn diện cá nhân - Thỏa mãn điều kiện Ý 2."""
    cards = [
        {
            "SO_SO_BHXH": "1234567890",
            "SO_THE_KCB": "HS4791234567890",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2024, 9, 1),
            "DEN_NGAY": date(2025, 3, 31),
            "TRANG_THAI": 1,
            "DM_BHXH_ID": 7901,
            "MA_TINH": "79",
        },
        {
            "SO_SO_BHXH": "1234567890",
            "SO_THE_KCB": "DN4791234567890",
            "MA_KHOI": "DN",
            "TU_NGAY": date(2025, 7, 1),
            "DEN_NGAY": date(2026, 12, 31),
            "TRANG_THAI": 1,
            "DM_BHXH_ID": 7902,
            "MA_TINH": "79",
        },
    ]
    res = evaluate_person_gap_y2(cards)
    assert res["satisfies_y2"] is True
    assert res["total_gap_days"] == 91
    assert res["primary_base"]["MA_KHOI"] == "HS"
    assert res["primary_chk"]["MA_KHOI"] == "DN"


def test_person_evaluator_not_active_in_chk():
    """Ca 8: Có thẻ mốc gốc, có gap 90 ngày nhưng mốc 07/2026 không có thẻ -> Loại (thuộc Ý 1 chứ không thuộc Ý 2)."""
    cards = [
        {
            "SO_SO_BHXH": "1234567891",
            "SO_THE_KCB": "HS4791234567891",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2024, 9, 1),
            "DEN_NGAY": date(2025, 3, 31),
            "TRANG_THAI": 1,
        },
        {
            "SO_SO_BHXH": "1234567891",
            "SO_THE_KCB": "HS4791234567891",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2025, 7, 1),
            "DEN_NGAY": date(2026, 5, 31),  # Hết hạn trước 01/07/2026
            "TRANG_THAI": 1,
        },
    ]
    res = evaluate_person_gap_y2(cards)
    assert res["satisfies_y2"] is False
    assert "No active card in 07/2026" in res["reason"]


def test_person_evaluator_cancelled_card():
    """Ca 9: Thẻ bị hủy (TRANG_THAI = 0) không được tính vào thời gian có hiệu lực."""
    cards = [
        {
            "SO_SO_BHXH": "1234567892",
            "SO_THE_KCB": "HS4791234567892",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2024, 9, 1),
            "DEN_NGAY": date(2025, 3, 31),
            "TRANG_THAI": 1,
        },
        {
            # Thẻ bị hủy trong kỳ gián đoạn
            "SO_SO_BHXH": "1234567892",
            "SO_THE_KCB": "HS4791234567892_HUY",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2025, 4, 1),
            "DEN_NGAY": date(2025, 6, 30),
            "TRANG_THAI": 0,  # Bị hủy
        },
        {
            "SO_SO_BHXH": "1234567892",
            "SO_THE_KCB": "HS4791234567892_NEW",
            "MA_KHOI": "HS",
            "TU_NGAY": date(2025, 7, 1),
            "DEN_NGAY": date(2026, 12, 31),
            "TRANG_THAI": 1,
        },
    ]
    res = evaluate_person_gap_y2(cards)
    # Thẻ hủy bị bỏ qua, khoảng trống từ 01/04 đến 30/06 là 91 ngày -> Thỏa mãn
    assert res["satisfies_y2"] is True
    assert res["total_gap_days"] == 91


def test_leading_and_trailing_window_gaps_are_counted():
    """Khoảng trống trước thẻ đầu và sau thẻ cuối nằm trong kỳ đều được tính."""
    window_start = date(2024, 10, 1)
    window_end = date(2026, 7, 31)
    intervals = merge_intervals([
        (date(2024, 10, 15), date(2025, 3, 31)),
        (date(2025, 7, 1), date(2026, 7, 15)),
    ])

    total_days, num_gaps, details = calculate_gaps(intervals, window_start, window_end)

    assert total_days == 14 + 91 + 16
    assert num_gaps == 3
    assert details[0] == (date(2024, 10, 1), date(2024, 10, 14), 14)
    assert details[-1] == (date(2026, 7, 16), date(2026, 7, 31), 16)


def test_window_gap_threshold_is_inclusive_at_90_days():
    """Cộng gap hai biên và gap trong kỳ; ngưỡng 90 ngày được tính bao gồm."""
    intervals = merge_intervals([
        (date(2024, 10, 11), date(2025, 3, 31)),  # 10 ngày đầu kỳ
        (date(2025, 6, 10), date(2026, 7, 21)),  # 70 ngày giữa kỳ, 10 ngày cuối kỳ
    ])
    total_days, num_gaps, _ = calculate_gaps(
        intervals, date(2024, 10, 1), date(2026, 7, 31)
    )
    assert total_days == 10 + 70 + 10
    assert total_days >= 90
    assert num_gaps == 3


def test_no_coverage_counts_entire_observation_window_as_one_gap():
    total_days, num_gaps, details = calculate_gaps(
        [], date(2024, 10, 1), date(2024, 10, 31)
    )
    assert total_days == 31
    assert num_gaps == 1
    assert details == [(date(2024, 10, 1), date(2024, 10, 31), 31)]


def test_representative_card_tie_break_matches_sql_ascending_card_number():
    cards = [
        {"SO_THE_KCB": "HS-B", "MA_KHOI": "HS", "TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 1, 1), "TRANG_THAI": 1},
        {"SO_THE_KCB": "HS-A", "MA_KHOI": "HS", "TU_NGAY": date(2024, 10, 1), "DEN_NGAY": date(2025, 1, 1), "TRANG_THAI": 1},
        {"SO_THE_KCB": "DN-B", "MA_KHOI": "DN", "TU_NGAY": date(2026, 7, 1), "DEN_NGAY": date(2026, 7, 31), "TRANG_THAI": 1},
        {"SO_THE_KCB": "DN-A", "MA_KHOI": "DN", "TU_NGAY": date(2026, 7, 1), "DEN_NGAY": date(2026, 7, 31), "TRANG_THAI": 1},
    ]
    result = evaluate_person_gap_y2(cards)
    assert result["primary_base"]["SO_THE_KCB"] == "HS-A"
    assert result["primary_chk"]["SO_THE_KCB"] == "DN-A"
