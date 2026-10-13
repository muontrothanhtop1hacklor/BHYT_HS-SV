# -*- coding: utf-8 -*-
"""
src/pipelines/gold_logic.py
Các hàm logic cốt lõi dùng trong pipeline sản xuất cho bài toán CV 835/QLT (Ý 1).
Được chia sẻ dùng chung giữa:
- Pipeline tính tầng Gold (build_gold.py)
- Bộ kiểm thử biên (test_edge_cases.py)
- Module kiểm tra chất lượng dữ liệu
"""

from datetime import date
from typing import List, Dict, Any, Tuple


def clean_khoi_code(raw_khoi: Any) -> str:
    """Chuẩn hóa mã khối (cắt khoảng trắng, viết hoa)."""
    if raw_khoi is None:
        return ""
    return str(raw_khoi).strip().upper()


def check_card_active_in_month(
    tu_ngay: date,
    den_ngay: date,
    trang_thai: int,
    month_start: date,
    month_next_start: date,
) -> bool:
    """
    Xác định thẻ BHYT có hiệu lực giao với tháng xét [month_start, month_next_start) hay không.
    Điều kiện:
    1. Thẻ không bị hủy (TRANG_THAI == 1).
    2. Ngày bắt đầu không lớn hơn ngày kết thúc (TU_NGAY <= DEN_NGAY).
    3. Thẻ giao với tháng: (TU_NGAY < month_next_start) AND (DEN_NGAY >= month_start).
    """
    if trang_thai != 1:
        return False
    if tu_ngay > den_ngay:
        return False
    return (tu_ngay < month_next_start) and (den_ngay >= month_start)


def resolve_khoi_priority(has_hs: bool, has_sv: bool) -> str:
    """
    Xác định khối gốc đại diện khi xét HSSV ở tháng gốc:
    - Chỉ có HS -> 'HS'
    - Chỉ có SV -> 'SV'
    - Có cả HS và SV -> 'SV' (ưu tiên cấp bậc học vấn cao hơn theo quy ước đặc tả)
    - Không có -> ''
    """
    if has_hs and has_sv:
        return "SV"
    if has_sv:
        return "SV"
    if has_hs:
        return "HS"
    return ""


def evaluate_person_participation(
    cards: List[Dict[str, Any]],
    base_start: date = date(2024, 10, 1),
    base_next_start: date = date(2024, 11, 1),
    chk_start: date = date(2026, 8, 1),
    chk_next_start: date = date(2026, 9, 1),
    stop_def: str = "any",
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Đánh giá trạng thái tham gia của một cá nhân dựa trên danh sách thẻ:
    - Có tham gia HSSV tại mốc gốc?
    - Có tham gia tại mốc kiểm tra?
    - Có thuộc diện dừng tham gia theo định nghĩa stop_def ('any' hoặc 'hssv')?

    Trả về:
    (is_stopped, ma_khoi_goc, best_base_card)
    """
    has_base_hs = False
    has_base_sv = False
    has_chk_any = False
    has_chk_hssv = False

    best_base_card = None

    for c in cards:
        tu = c["TU_NGAY"]
        den = c["DEN_NGAY"]
        st = int(c.get("TRANG_THAI", 1))
        kh = clean_khoi_code(c.get("MA_KHOI", ""))

        # 1. Kiểm tra hiệu lực ở tháng gốc
        if check_card_active_in_month(tu, den, st, base_start, base_next_start):
            if kh == "HS":
                has_base_hs = True
                if best_base_card is None or best_base_card.get("MA_KHOI") != "SV":
                    best_base_card = c
            elif kh == "SV":
                has_base_sv = True
                best_base_card = c

        # 2. Kiểm tra hiệu lực ở tháng kiểm tra
        if check_card_active_in_month(tu, den, st, chk_start, chk_next_start):
            has_chk_any = True
            if kh in ("HS", "SV"):
                has_chk_hssv = True

    has_base_hssv = has_base_hs or has_base_sv
    if not has_base_hssv:
        return False, "", None

    # Xác định dừng theo định nghĩa
    if stop_def == "any":
        is_stopped = not has_chk_any
    elif stop_def == "hssv":
        is_stopped = not has_chk_hssv
    else:
        raise ValueError(f"Định nghĩa dừng không hợp lệ: {stop_def}")

    ma_khoi_goc = resolve_khoi_priority(has_base_hs, has_base_sv)
    return is_stopped, ma_khoi_goc, best_base_card
