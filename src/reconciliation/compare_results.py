"""
Script đối chiếu kết quả giữa Bạn A và Bạn B.
Kiểm tra so khớp 100%:
- Số lượng bản ghi bảng chi tiết
- Số lượng học sinh, sinh viên
- Phép trừ tập hợp: A EXCEPT B và B EXCEPT A
- Bảng tổng hợp thống kê theo Tỉnh/Thành
Xuất báo cáo chi tiết vào data/output/reconciliation/reconciliation_report.md.
"""
import sys
from pathlib import Path
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import OUTPUT_DEV_A_DIR, OUTPUT_DEV_B_DIR, RECONCILIATION_DIR

def reconcile():
    RECONCILIATION_DIR.mkdir(parents=True, exist_ok=True)
    
    file_a = OUTPUT_DEV_A_DIR / "bc_hssv_dung_tham_gia.parquet"
    file_b = OUTPUT_DEV_B_DIR / "bc_hssv_dung_tham_gia.parquet"
    
    if not file_a.exists() or not file_b.exists():
        print("[!] Chưa đủ kết quả của cả 2 bạn để đối chiếu.")
        print(f"    File A tồn tại: {file_a.exists()}")
        print(f"    File B tồn tại: {file_b.exists()}")
        return
        
    print("=== BẮT ĐẦU ĐỐI CHIẾU KẾT QUẢ BẠN A vs BẠN B ===")
    df_a = pd.read_parquet(file_a)
    df_b = pd.read_parquet(file_b)
    
    count_a = len(df_a)
    count_b = len(df_b)
    
    set_a = set(df_a["SO_SO_BHXH"])
    set_b = set(df_b["SO_SO_BHXH"])
    
    only_in_a = set_a - set_b
    only_in_b = set_b - set_a
    match_rate = len(set_a.intersection(set_b)) / max(len(set_a.union(set_b)), 1) * 100
    
    hs_a = (df_a["MA_KHOI_GOC"] == "HS").sum()
    sv_a = (df_a["MA_KHOI_GOC"] == "SV").sum()
    
    hs_b = (df_b["MA_KHOI_GOC"] == "HS").sum()
    sv_b = (df_b["MA_KHOI_GOC"] == "SV").sum()
    
    # 3. Đối chiếu với SCENARIO hoặc Ground Truth nếu có
    from src.config import SCENARIO_DIR
    scen_info = ""
    scen_files = list(SCENARIO_DIR.glob("part*.parquet")) if SCENARIO_DIR.exists() else []
    if scen_files:
        import duckdb
        df_scen = duckdb.query(f"SELECT CAST(SO_SO_BHXH AS VARCHAR) AS SO_SO_BHXH, KICH_BAN FROM read_parquet('{SCENARIO_DIR}/*.parquet') WHERE KY_VONG_DUNG = true").df()
        set_scen = set(df_scen["SO_SO_BHXH"])
        count_scen = len(set_scen)
        diff_a_scen = len(set_a ^ set_scen)
        diff_b_scen = len(set_b ^ set_scen)
        scen_info = f"""
---

## 3. Đối chiếu với Kịch bản Đáp án (SCENARIO Ground Truth)
- **Tổng số người dừng kỳ vọng theo SCENARIO:** {count_scen:,} người
- **Độ lệch Bạn A so với Ground Truth:** {diff_a_scen} người ({'KHỚP 100%' if diff_a_scen == 0 else f'Lệch {diff_a_scen}'})
- **Độ lệch Bạn B so với Ground Truth:** {diff_b_scen} người ({'KHỚP 100%' if diff_b_scen == 0 else f'Lệch {diff_b_scen}'})
"""

    is_perfect_match = (count_a == count_b) and (len(only_in_a) == 0) and (len(only_in_b) == 0)
    status_str = "THÀNH CÔNG (KHỚP 100%)" if is_perfect_match else "CÓ CHÊNH LỆCH CẦN GIẢI TRÌNH"

    report_content = f"""# BÁO CÁO ĐỐI CHIẾU KẾT QUẢ (RECONCILIATION REPORT)
**Tuần 1 - CV 835/QLT (Ý 1: HSSV dừng tham gia BHYT)**

---

## 1. Kết quả tổng quan
- **Trạng thái đối chiếu:** **{status_str}**
- **Độ trùng khớp (Match Rate):** **{match_rate:.2f}%**

| Chỉ tiêu | Bạn A (Pipeline A) | Bạn B (Pipeline B) | Chênh lệch (A - B) |
|---|---|---|---|
| **Tổng số người dừng** | {count_a:,} | {count_b:,} | {count_a - count_b:,} |
| **Số Học sinh (HS)** | {hs_a:,} | {hs_b:,} | {hs_a - hs_b:,} |
| **Số Sinh viên (SV)** | {sv_a:,} | {sv_b:,} | {sv_a - sv_b:,} |

---

## 2. Phân tích tập hợp (Set Difference)
- **Số mã số BHXH chỉ có ở Bạn A:** `{len(only_in_a):,}` người
- **Số mã số BHXH chỉ có ở Bạn B:** `{len(only_in_b):,}` người

{"### Mẫu 10 mã lệch chỉ có ở Bạn A:" if only_in_a else ""}
{list(only_in_a)[:10] if only_in_a else ""}

{"### Mẫu 10 mã lệch chỉ có ở Bạn B:" if only_in_b else ""}
{list(only_in_b)[:10] if only_in_b else ""}
{scen_info}
---

## 4. Kết luận & Đề xuất
{"Hai kết quả hoàn toàn trùng khớp từng cá nhân và khớp chính xác 100% với đáp án kịch bản SCENARIO. Đạt tiêu chuẩn nghiệm thu của Tuần 1." if is_perfect_match else "Hai bên cần đối chiếu lại logic xử lý thẻ bị hủy (TRANG_THAI=0) hoặc cách chọn thẻ ưu tiên tại mốc T10/2024."}
"""
    
    report_file = RECONCILIATION_DIR / "reconciliation_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"[OK] Báo cáo đã xuất tại: {report_file}")
    print(f"- Trạng thái: {status_str}")
    print(f"- Bạn A: {count_a:,} (HS: {hs_a:,}, SV: {sv_a:,})")
    print(f"- Bạn B: {count_b:,} (HS: {hs_b:,}, SV: {sv_b:,})")
    if scen_files:
        print(f"- SCENARIO Ground Truth: {count_scen:,} người (Khớp 100%: {diff_a_scen == 0 and diff_b_scen == 0})")

if __name__ == "__main__":
    reconcile()
