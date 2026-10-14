# Bài: dùng chung | common/data_gen/legacy
"""
Định nghĩa mô hình vòng đời đối tượng (Person Lifecycle) và các nhóm Test Case chuẩn.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Any
import numpy as np

@dataclass
class CardRecord:
    so_so_bhxh: str
    so_the_kcb: str
    ho_ten: str
    ngay_sinh: date
    gioi_tinh: int
    so_cmnd: str
    dia_chi: str
    ma_khoi: str
    tu_ngay: date
    den_ngay: date
    trang_thai: int
    dm_bhxh_id: int

class PersonProfile:
    """Mô phỏng nhân khẩu học và phân bổ test cases theo yêu cầu CV 835/QLT."""
    
    # 6 Nhóm test case chính
    CASE_HSSV_CONTINUOUS = 1      # Tham gia liên tục 2024 - 2026
    CASE_HSSV_STOPPED = 2         # Tham gia T10/2024, sau đó hết hạn và DỪNG HẲN (Target)
    CASE_HSSV_SWITCH_BLOCK = 3    # Tham gia T10/2024, sang 2025-2026 chuyển sang DN/GD
    CASE_HSSV_CANCELLED_CARD = 4  # Có thẻ hủy (TRANG_THAI=0) và thẻ thay thế
    CASE_HSSV_RELOCATED = 5       # Chuyển địa bàn / trường
    CASE_HSSV_INTERMITTENT = 6    # Gián đoạn rồi tham gia lại
    CASE_OTHER_BLOCKS = 7         # Khối khác: DN, GD, TE, HT...
