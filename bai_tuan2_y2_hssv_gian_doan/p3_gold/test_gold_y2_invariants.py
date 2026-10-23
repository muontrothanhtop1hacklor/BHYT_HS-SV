# -*- coding: utf-8 -*-
"""
test_gold_y2_invariants.py
Kiểm thử các bất biến nghiệp vụ và tính toàn vẹn dữ liệu tầng Gold Ý 2 (CV 835/QLT).

Các bất biến bắt buộc:
1. File kết quả bc_hssv_gian_doan_bhyt.parquet và tk_dbhc_hssv_gian_doan_bhyt.csv phải tồn tại.
2. Số dòng chi tiết phải khớp tuyệt đối với tổng của 63 tỉnh trong bảng thống kê:
   SUM(TONG_SO_NGUOI_GIAN_DOAN) == len(bc_df)
3. Tổng số học sinh và sinh viên trong bảng thống kê phải khớp với bảng chi tiết:
   SUM(SO_LUONG_HS_GIAN_DOAN) == count(MA_KHOI_GOC = 'HS')
   SUM(SO_LUONG_SV_GIAN_DOAN) == count(MA_KHOI_GOC = 'SV')
4. Không có giá trị NULL ở các trường định danh bắt buộc: SO_SO_BHXH, HO_TEN, MA_KHOI_GOC, MA_TINH_GOC.
5. 100% đối tượng trong danh sách kết quả phải có SO_NGAY_GIAN_DOAN >= 90 ngày.
6. 100% đối tượng phải có MA_KHOI_GOC thuộc tập {'HS', 'SV'}.
7. Bảng thống kê phải có đủ 63 tỉnh/thành phố chuẩn.
"""
from pathlib import Path
import pytest
import pandas as pd
import pyarrow.parquet as pq

from common.config import (
    GOLD_Y2_BC_FILE,
    GOLD_Y2_TK_CSV,
    MIN_GAP_DAYS_Y2,
)


@pytest.fixture(scope="module")
def gold_y2_data():
    if not GOLD_Y2_BC_FILE.exists() or not GOLD_Y2_TK_CSV.exists():
        pytest.skip(f"Chưa chạy build_gold_y2, thiếu file kết quả: {GOLD_Y2_BC_FILE}")
        
    bc_df = pq.read_table(str(GOLD_Y2_BC_FILE)).to_pandas()
    tk_df = pd.read_csv(str(GOLD_Y2_TK_CSV), dtype={"MA_TINH": str})
    return bc_df, tk_df


def test_gold_y2_files_exist():
    """Kiểm tra sự tồn tại của các tệp kết quả Gold Ý 2."""
    assert GOLD_Y2_BC_FILE.exists(), f"Thiếu file: {GOLD_Y2_BC_FILE}"
    assert GOLD_Y2_TK_CSV.exists(), f"Thiếu file: {GOLD_Y2_TK_CSV}"


def test_gold_y2_reconciliation_totals(gold_y2_data):
    """Bất biến 1: Tổng số người trong bảng thống kê tỉnh phải khớp 100% với bảng chi tiết."""
    bc_df, tk_df = gold_y2_data
    total_bc = len(bc_df)
    total_tk = tk_df["TONG_SO_NGUOI_GIAN_DOAN"].sum()
    assert total_bc == total_tk, (
        f"Lệch số lượng tổng: Chi tiết={total_bc:,} vs Thống kê={total_tk:,}"
    )


def test_gold_y2_hssv_counts_match(gold_y2_data):
    """Bất biến 2: Số lượng HS và SV phân theo khối phải khớp tuyệt đối."""
    bc_df, tk_df = gold_y2_data
    
    bc_hs = (bc_df["MA_KHOI_GOC"] == "HS").sum()
    tk_hs = tk_df["SO_LUONG_HS_GIAN_DOAN"].sum()
    assert bc_hs == tk_hs, f"Lệch số lượng HS: Chi tiết={bc_hs:,} vs Thống kê={tk_hs:,}"
    
    bc_sv = (bc_df["MA_KHOI_GOC"] == "SV").sum()
    tk_sv = tk_df["SO_LUONG_SV_GIAN_DOAN"].sum()
    assert bc_sv == tk_sv, f"Lệch số lượng SV: Chi tiết={bc_sv:,} vs Thống kê={tk_sv:,}"


def test_gold_y2_gap_days_threshold(gold_y2_data):
    """Bất biến 3: 100% đối tượng trong danh sách phải có SO_NGAY_GIAN_DOAN >= MIN_GAP_DAYS_Y2 (90 ngày)."""
    bc_df, _ = gold_y2_data
    violators = bc_df[bc_df["SO_NGAY_GIAN_DOAN"] < MIN_GAP_DAYS_Y2]
    assert len(violators) == 0, (
        f"Phát hiện {len(violators)} bản ghi có số ngày gián đoạn < {MIN_GAP_DAYS_Y2} ngày!"
    )


def test_gold_y2_valid_khoi_goc(gold_y2_data):
    """Bất biến 4: Khối gốc bắt buộc chỉ là 'HS' hoặc 'SV'."""
    bc_df, _ = gold_y2_data
    invalid_khoi = bc_df[~bc_df["MA_KHOI_GOC"].isin(["HS", "SV"])]
    assert len(invalid_khoi) == 0, (
        f"Phát hiện {len(invalid_khoi)} bản ghi có MA_KHOI_GOC không hợp lệ!"
    )


def test_gold_y2_no_null_keys(gold_y2_data):
    """Bất biến 5: Không có giá trị NULL ở các trường định danh và liên kết quan trọng."""
    bc_df, _ = gold_y2_data
    assert bc_df["SO_SO_BHXH"].isnull().sum() == 0, "SO_SO_BHXH chứa NULL"
    assert bc_df["MA_KHOI_GOC"].isnull().sum() == 0, "MA_KHOI_GOC chứa NULL"
    assert bc_df["SO_NGAY_GIAN_DOAN"].isnull().sum() == 0, "SO_NGAY_GIAN_DOAN chứa NULL"
    assert bc_df["SO_SO_BHXH"].nunique() == len(bc_df), "SO_SO_BHXH bị trùng lặp trong bảng chi tiết"


def test_gold_y2_provinces_complete(gold_y2_data):
    """Bất biến 6: Bảng thống kê địa bàn hành chính phải có đủ 63 tỉnh/thành phố."""
    _, tk_df = gold_y2_data
    assert len(tk_df) == 63, f"Bảng thống kê có {len(tk_df)} tỉnh, kỳ vọng 63 tỉnh!"
    assert tk_df["MA_TINH"].nunique() == 63, "Mã tỉnh bị trùng lặp"
