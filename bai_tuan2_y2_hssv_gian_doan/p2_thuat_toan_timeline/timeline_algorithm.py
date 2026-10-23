# -*- coding: utf-8 -*-
"""
timeline_algorithm.py
Module thuật toán xử lý chuỗi thời gian (Timeline & Gap Analysis) cho bài toán BHYT (CV 835/QLT - Ý 2).

Bao gồm:
1. Gộp các khoảng thời gian chồng lấn và nối tiếp (Interval Merging with Contiguity).
2. Phát hiện và tính toán các khoảng trống (Gap Detection).
3. Tổng hợp thời gian gián đoạn tích lũy của từng cá nhân.
"""
from datetime import date, timedelta
from typing import List, Tuple, Dict, Any, Optional


def merge_intervals(
    intervals: List[Tuple[date, date]]
) -> List[Tuple[date, date]]:
    """
    Gộp danh sách các khoảng thời gian [tu_ngay, den_ngay].
    
    Quy tắc nghiệp vụ BHYT:
    - Nếu khoảng sau chồng lấn với khoảng trước (T2 <= D1): Gộp thành [T1, max(D1, D2)].
    - Nếu khoảng sau nối tiếp ngay ngày hôm sau (T2 == D1 + 1 ngày): Vẫn coi là liên tục, gộp lại.
    - Nếu khoảng sau cách khoảng trước >= 1 ngày (T2 > D1 + 1 ngày): Tách thành khoảng riêng biệt (có khoảng trống ở giữa).
    
    Độ phức tạp: O(K log K) với K là số thẻ của 1 người (thường K <= 15).
    """
    if not intervals:
        return []
    
    # Sắp xếp theo ngày bắt đầu tăng dần, nếu trùng thì ngày kết thúc giảm dần
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    
    merged: List[List[date]] = []
    for cur_st, cur_en in sorted_intervals:
        if cur_st > cur_en:
            continue  # Bỏ qua khoảng nghịch đảo lỗi (nếu có)
            
        if not merged:
            merged.append([cur_st, cur_en])
        else:
            prev_st, prev_en = merged[-1]
            # Nếu ngày bắt đầu thẻ mới <= ngày kết thúc thẻ trước + 1 ngày: gộp lại
            if cur_st <= prev_en + timedelta(days=1):
                if cur_en > prev_en:
                    merged[-1][1] = cur_en
            else:
                merged.append([cur_st, cur_en])
                
    return [(item[0], item[1]) for item in merged]


def calculate_gaps(
    merged_intervals: List[Tuple[date, date]],
    window_start: Optional[date] = None,
    window_end: Optional[date] = None
) -> Tuple[int, int, List[Tuple[date, date, int]]]:
    """
    Tính khoảng trống giữa các khoảng đã gộp và ở biên cửa sổ nếu được cung cấp.
    
    Tham số:
    - merged_intervals: Danh sách các khoảng đã gộp, không chồng lấn.
    - window_start/window_end: Biên bao gồm của kỳ quan sát. Khi có cả hai, interval
      được cắt vào kỳ và ngày không có bảo hiểm ở đầu/cuối kỳ cũng được tính.
      Nếu bỏ qua, chỉ các khoảng trống giữa interval được tính.
    
    Trả về:
    - total_gap_days: Tổng số ngày gián đoạn tích lũy.
    - num_gaps: Số đợt gián đoạn.
    - gap_details: Danh sách chi tiết từng đợt [gap_start, gap_end, days].
    """
    if not merged_intervals:
        if window_start is None or window_end is None or window_start > window_end:
            return 0, 0, []
        days = (window_end - window_start).days + 1
        return days, 1, [(window_start, window_end, days)]

    # Clip to the requested observation window before measuring edge gaps.
    if window_start is not None and window_end is not None:
        if window_start > window_end:
            return 0, 0, []
        merged_intervals = [
            (max(start, window_start), min(end, window_end))
            for start, end in merged_intervals
            if max(start, window_start) <= min(end, window_end)
        ]
        if not merged_intervals:
            days = (window_end - window_start).days + 1
            return days, 1, [(window_start, window_end, days)]

    gap_details: List[Tuple[date, date, int]] = []
    total_gap_days = 0

    if window_start is not None:
        gap_end = merged_intervals[0][0] - timedelta(days=1)
        if window_start <= gap_end:
            days = (gap_end - window_start).days + 1
            gap_details.append((window_start, gap_end, days))
            total_gap_days += days
    
    # 1. Khoảng trống giữa các đoạn liên tục
    for i in range(len(merged_intervals) - 1):
        prev_en = merged_intervals[i][1]
        next_st = merged_intervals[i + 1][0]
        
        # Nếu next_st > prev_en + 1 ngày thì tồn tại khoảng trống
        gap_st = prev_en + timedelta(days=1)
        gap_en = next_st - timedelta(days=1)
        
        if gap_st <= gap_en:
            days = (gap_en - gap_st).days + 1
            gap_details.append((gap_st, gap_en, days))
            total_gap_days += days

    if window_end is not None:
        gap_start = merged_intervals[-1][1] + timedelta(days=1)
        if gap_start <= window_end:
            days = (window_end - gap_start).days + 1
            gap_details.append((gap_start, window_end, days))
            total_gap_days += days
            
    num_gaps = len(gap_details)
    return total_gap_days, num_gaps, gap_details


def evaluate_person_gap_y2(
    cards: List[Dict[str, Any]],
    window_start: date = date(2024, 10, 1),
    window_end: date = date(2026, 7, 31),
    min_gap_days: int = 90
) -> Dict[str, Any]:
    """
    Đánh giá toàn diện 1 cá nhân theo 3 điều kiện của bài toán Ý 2 (CV 835/QLT):
    
    1. Có thẻ HS/SV hợp lệ giao tháng 10/2024.
    2. Có thẻ hợp lệ (bất kỳ khối nào) giao tháng 07/2026.
    3. Tổng thời gian gián đoạn tích lũy trong kỳ >= min_gap_days (mặc định: 90 ngày).
    """
    # Lọc thẻ hợp lệ (TRANG_THAI == 1)
    valid_cards = [c for c in cards if c.get("TRANG_THAI", 1) == 1]
    
    # Mốc tháng gốc: 2024-10-01 đến 2024-10-31
    m10_start = date(2024, 10, 1)
    m10_next = date(2024, 11, 1)
    
    # Mốc tháng kiểm tra: 2026-07-01 đến 2026-07-31
    m07_start = date(2026, 7, 1)
    m07_next = date(2026, 8, 1)
    
    # 1. Kiểm tra mốc bắt đầu
    base_cards = [
        c for c in valid_cards
        if c["TU_NGAY"] < m10_next and c["DEN_NGAY"] >= m10_start
        and c.get("MA_KHOI", "") in ("HS", "SV")
    ]
    if not base_cards:
        return {"satisfies_y2": False, "reason": "No valid HSSV card in 10/2024"}
        
    # Chọn thẻ đại diện mốc gốc (Ưu tiên SV > HS, DEN_NGAY lớn nhất)
    base_cards.sort(key=lambda x: (
        -(1 if x["MA_KHOI"] == "SV" else 0),
        -x["DEN_NGAY"].toordinal(),
        str(x.get("SO_THE_KCB", "")),
    ))
    primary_base = base_cards[0]
    
    # 2. Kiểm tra mốc kết thúc
    chk_cards = [
        c for c in valid_cards
        if c["TU_NGAY"] < m07_next and c["DEN_NGAY"] >= m07_start
    ]
    if not chk_cards:
        return {"satisfies_y2": False, "reason": "No active card in 07/2026"}
        
    # Chọn thẻ đại diện mốc kết thúc
    chk_cards.sort(key=lambda x: (
        -x["DEN_NGAY"].toordinal(),
        str(x.get("SO_THE_KCB", "")),
    ))
    primary_chk = chk_cards[0]
    
    # 3. Cắt và gộp thẻ trong cửa sổ quan sát [window_start, window_end]
    clipped_intervals = []
    for c in valid_cards:
        st = max(c["TU_NGAY"], window_start)
        en = min(c["DEN_NGAY"], window_end)
        if st <= en:
            clipped_intervals.append((st, en))
            
    merged = merge_intervals(clipped_intervals)
    total_gap_days, num_gaps, gap_details = calculate_gaps(
        merged, window_start=window_start, window_end=window_end
    )
    
    satisfies = total_gap_days >= min_gap_days
    
    return {
        "satisfies_y2": satisfies,
        "SO_SO_BHXH": primary_base.get("SO_SO_BHXH"),
        "primary_base": primary_base,
        "primary_chk": primary_chk,
        "merged_intervals": merged,
        "gap_details": gap_details,
        "num_gaps": num_gaps,
        "total_gap_days": total_gap_days,
        "total_gap_months": round(total_gap_days / 30.0, 1),
    }
