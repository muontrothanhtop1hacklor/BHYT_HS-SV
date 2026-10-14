# Bài: dùng chung | common/data_gen
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_bhyt.py - Sinh fake data ST_INTHE_DTL (thẻ BHYT) theo vòng đời người (Person Lifecycle).

Lệnh:
  python gen_bhyt.py calibrate --sample 200000            # ước lượng tổng số dòng + tốc độ (không ghi file)
  python gen_bhyt.py bench --persons 400000 --workers 1 2 4 8   # đo throughput, speedup S(N), efficiency E(N)
  python gen_bhyt.py generate --out ./bhyt_data --persons 20000000 --workers 8   # sinh thật, resume được

Thiết kế chính:
  * Đơn vị chia việc = chunk theo KHOẢNG NGƯỜI (person_idx), mọi thẻ của 1 người nằm trong 1 chunk.
  * Seed của chunk = SeedSequence([seed, chunk_id]) -> kết quả không phụ thuộc số worker/thứ tự chạy.
  * Ghi atomic (file .tmp -> os.replace) + manifest từng chunk -> chạy lại sẽ bỏ qua chunk đã xong.
  * Khối (HS/SV/TE/DN/GD/HT) và SO_SO_BHXH gán bằng ánh xạ song ánh (a*i+b mod N): đúng tuyệt đối tổng
    số người từng khối, không cần bộ nhớ chia sẻ giữa các process.
  * Vòng đời sinh bằng numpy vector hóa (vòng lặp theo "thẻ thứ k", không lặp theo người).

CÁC GIẢ ĐỊNH (chưa có nguồn xác thực, cần đối chiếu với nghiệp vụ thật - xem phần ASSUMPTIONS):
  cơ cấu 15M người khối khác, số thẻ/người từng khối, danh mục DM_BHXH (mặc định là danh mục tổng hợp),
  cấu trúc SO_THE_KCB, 17 cột ngoài các cột đề bài nêu, trọng số họ tên, mức đóng.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import math
import shutil
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import numba as nb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

# ============================================================================================
# ASSUMPTIONS / CONFIG
# ============================================================================================
KHOI = ["HS", "SV", "TE", "DN", "GD", "HT"]
HS, SV, TE, DN, GD, HT = range(6)

DEFAULT_CFG = dict(
    n_persons=20_000_000,
    seed=20261012,
    chunk_persons=100_000,
    start_month="2024-01",
    n_months=36,                 # 2024-01 .. 2026-12
    base_month="2024-10",        # mốc gốc của Ý 1
    check_month="2026-08",       # mốc "đến nay" (CV 835/QLT ngày 10/08/2026) - tham số hóa
    dirty_rate=0.01,             # tỷ lệ dòng bẩn có chủ đích (có log đáp án)
    compression="zstd",
    dm_csv=None,                 # CSV danh mục thật: ID,MA_DVI,TEN_DVI,MA_CHA[,TRONG_SO]
)

# Tỷ trọng người theo khối: HS 3.8M, SV 1.2M, (15M còn lại: TE 2M, DN 6M, GD 5M, HT 2M) -> GIẢ ĐỊNH
SHARE = [0.19, 0.06, 0.10, 0.30, 0.25, 0.10]
# Tuổi tại 01/10/2024 (khoảng [lo, hi)). TE<=3 để đến cuối 2026 vẫn <6 tuổi; SV<=23 để hết 2026 vẫn <=25.
AGE_LO = np.array([6, 18, 0, 20, 18, 56], dtype=np.float64)
AGE_HI = np.array([18, 23, 3, 60, 86, 91], dtype=np.float64)

# Chu kỳ thẻ (tháng) 1/3/6/12 và xác suất theo khối. DN phải có thẻ ngắn kỳ (1 tháng) thì tổng mới tiến gần 200M.
DUR_VALUES = np.array([1, 3, 6, 12], dtype=np.int16)
DUR_P = np.array([
    [0.00, 0.15, 0.45, 0.40],   # HS
    [0.00, 0.15, 0.45, 0.40],   # SV
    [0.00, 0.05, 0.25, 0.70],   # TE
    [0.93, 0.05, 0.01, 0.01],   # DN
    [0.25, 0.30, 0.25, 0.20],   # GD
    [0.00, 0.00, 0.10, 0.90],   # HT
])
# Kịch bản vòng đời: CONT, STOP, SWITCH, GAP, LATE, UPGRADE
SC_NAMES = ["CONT", "STOP", "SWITCH", "GAP", "LATE", "UPGRADE"]
SCEN_P = np.array([
    [0.60, 0.18, 0.02, 0.08, 0.12, 0.0],   # HS  (UPGRADE HS->SV chỉ phát sinh theo quy tắc đủ 18 tuổi)
    [0.45, 0.18, 0.15, 0.08, 0.14, 0.0],   # SV
    [0.70, 0.08, 0.00, 0.07, 0.15, 0.0],   # TE
    [0.55, 0.12, 0.05, 0.13, 0.15, 0.0],   # DN
    [0.55, 0.12, 0.05, 0.13, 0.15, 0.0],   # GD
    [0.80, 0.08, 0.00, 0.06, 0.06, 0.0],   # HT
])
P_CANCEL_REPL = 0.04      # thẻ bị hủy + có thẻ thay thế
P_CANCEL_NOREPL = 0.004   # thẻ bị hủy, không có thẻ thay thế
P_MOVE = 0.06             # chuyển địa bàn
P_DAYOFF = 0.30           # tỷ lệ người có thẻ bắt đầu giữa tháng

# Họ tên: trọng số xấp xỉ, THAY bằng thống kê chính thức nếu cần.
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô",
      "Dương", "Lý", "Đinh", "Lâm", "Mai", "Trịnh", "Đào", "Cao", "Tô", "Hà", "Lương", "Tạ", "Thái", "Châu"]
HO_W = np.array([38, 11, 9.5, 7, 5, 4.5, 4.5, 3.5, 3.5, 2.5, 2, 2, 1.5, 1.2, 1, 0.9, 0.8, 0.7, 0.6, 0.6,
                 0.5, 0.5, 0.4, 0.4, 0.4, 0.3, 0.3, 0.3])
DEM_M = ["Văn", "Đức", "Minh", "Quang", "Hữu", "Thanh", "Công", "Anh", "Xuân", "Hoàng", "Gia", "Đình", "Trung", "Quốc", "Tuấn"]
DEM_F = ["Thị", "Ngọc", "Thu", "Thanh", "Mai", "Hồng", "Phương", "Kim", "Bảo", "Diệu", "Quỳnh", "Khánh", "Minh", "Hà", "Thùy"]
TEN_M = ["Anh", "Bình", "Cường", "Dũng", "Đạt", "Hải", "Hùng", "Huy", "Khoa", "Long", "Minh", "Nam", "Phúc", "Quân",
         "Sơn", "Thắng", "Tuấn", "Việt", "Hiếu", "Nghĩa", "Khang", "Kiên", "Đức", "Thành", "Trung"]
TEN_F = ["Anh", "Chi", "Dung", "Giang", "Hà", "Hạnh", "Hoa", "Hương", "Lan", "Linh", "Loan", "Mai", "My", "Ngân",
         "Nhung", "Phương", "Quỳnh", "Thảo", "Thủy", "Trang", "Trinh", "Uyên", "Vy", "Yến", "Ngọc"]
STREETS = ["Đường Lê Lợi", "Đường Nguyễn Huệ", "Đường Trần Hưng Đạo", "Đường Lý Thường Kiệt", "Đường Hai Bà Trưng",
           "Đường Phạm Văn Đồng", "Đường Quang Trung", "Đường Hùng Vương", "Đường Lê Duẩn", "Đường 30 Tháng 4",
           "Đường Nguyễn Trãi", "Đường Võ Thị Sáu", "Đường Cách Mạng Tháng Tám", "Đường Điện Biên Phủ",
           "Đường Phan Đình Phùng", "Đường Ngô Quyền", "Thôn 1", "Thôn 2", "Xóm Chùa", "Khu phố 3"]
WARD_KIND = ["Phường", "Xã", "Thị trấn"]
LOAI_THE = ["CAP_MOI", "GIA_HAN", "CHUYEN_DIA_BAN", "CHUYEN_DOI_TUONG", "CAP_DOI", "CHUYEN_TRUONG"]
LY_DO_HUY = ["CAP_DOI", "SAI_THONG_TIN", "THU_HOI"]
NGUON = ["QLT", "TRUONG_HOC", "DOANH_NGHIEP", "VNEID"]
KHOI_VARIANTS = KHOI + [k.lower() for k in KHOI]            # biến thể bẩn: chữ thường
MUC_HUONG_CHOICES = {HS: [4], SV: [4], TE: [1], DN: [4, 4, 4, 3], GD: [5, 4], HT: [2, 3]}   # tổng hợp
RATE_FIXED = {HS: 63000, SV: 63000, TE: 0, GD: 100000, HT: 0}                                # tổng hợp
DIRTY_NAMES = {1: "TU_NGAY_LON_HON_DEN_NGAY", 2: "HO_TEN_NULL", 3: "GIOI_TINH_KHONG_HOP_LE",
               4: "MA_KHOI_SAI_DINH_DANG", 5: "DONG_TRUNG_LAP"}
ID_STRIDE = 128   # ID thẻ = person_idx * 128 + seq + 1  (mỗi người tối đa < 128 thẻ)

COLUMNS = ["ID", "SO_SO_BHXH", "SO_THE_KCB", "HO_TEN", "NGAY_SINH", "GIOI_TINH", "SO_CMND", "DIA_CHI", "MA_TINH",
           "MA_KHOI", "MUC_HUONG", "TU_NGAY", "DEN_NGAY", "TRANG_THAI", "DM_BHXH_ID", "LOAI_THE", "SO_THE_CU",
           "NGAY_CAP", "NGAY_HUY", "LY_DO_HUY", "SO_THANG", "MUC_DONG", "MA_TRUONG", "MA_KCB_BD", "MA_DON_VI",
           "SO_BIEN_LAI", "NGUOI_TAO", "NGAY_TAO", "NGAY_CAP_NHAT", "NGUON_DU_LIEU"]


# ============================================================================================
# Danh mục DM_BHXH
# ============================================================================================
def build_dm(cfg):
    """Trả về dict: bảng DM đầy đủ + mảng 'đơn vị cơ sở' (huyện) dùng để gán DM_BHXH_ID cho thẻ."""
    if cfg.get("dm_csv"):
        import pyarrow.csv as pacsv
        t = pacsv.read_csv(cfg["dm_csv"]).to_pydict()
        ids, ma, ten, cha = t["ID"], [str(x) for x in t["MA_DVI"]], t["TEN_DVI"], t["MA_CHA"]
        w = t.get("TRONG_SO", [1.0] * len(ids))
        ma_s = [str(x).zfill(2) if x is not None else None for x in ma]
        child = [i for i, c in enumerate(cha) if c not in (None, "")]
        prov = []
        for i in child:
            c = str(cha[i]).strip()
            prov.append(int(c) if c.isdigit() else 0)
        return dict(ids=ids, ma=ma_s, ten=ten, cha=[None if c in (None, "") else str(c) for c in cha],
                    c_id=np.array([ids[i] for i in child], dtype=np.int32), c_prov=np.array(prov, dtype=np.int16),
                    c_name=[ten[i] for i in child], c_w=np.array([w[i] for i in child], dtype=np.float64))
    rng = np.random.default_rng(777)
    n_prov = 63
    pw = 1.0 / np.arange(1, n_prov + 1) ** 0.8
    pw = pw[rng.permutation(n_prov)]
    ids, ma, ten, cha = [], [], [], []
    c_id, c_prov, c_name, c_w = [], [], [], []
    for p in range(1, n_prov + 1):
        ids.append(p); ma.append("%02d" % p); ten.append("BHXH tỉnh/thành phố %02d" % p); cha.append(None)
    nxt = 1001
    for p in range(1, n_prov + 1):
        k = int(rng.integers(6, 16))
        jit = rng.lognormal(0, 0.5, k)
        for j in range(k):
            ids.append(nxt); ma.append("%02d%02d" % (p, j + 1)); cha.append("%02d" % p)
            nm = "BHXH quận/huyện %02d-%02d" % (p, j + 1); ten.append(nm)
            c_id.append(nxt); c_prov.append(p); c_name.append(nm); c_w.append(pw[p - 1] / k * jit[j])
            nxt += 1
    return dict(ids=ids, ma=ma, ten=ten, cha=cha, c_id=np.array(c_id, dtype=np.int32),
                c_prov=np.array(c_prov, dtype=np.int16), c_name=c_name, c_w=np.array(c_w))


def dm_table(dm):
    return pa.table({"ID": pa.array(dm["ids"], pa.int32()), "MA_DVI": pa.array(dm["ma"]),
                     "TEN_DVI": pa.array(dm["ten"]), "MA_CHA": pa.array(dm["cha"])})


# ============================================================================================
# Context (dựng 1 lần / process)
# ============================================================================================
def _coprime(a, n):
    while math.gcd(a, n) != 1:
        a += 2
    return a


def make_ctx(cfg):
    H = cfg["n_months"]
    N = cfg["n_persons"]
    assert N <= 2_500_000_000, "n_persons quá lớn cho phép nhân int64"
    start = np.datetime64(cfg["start_month"], "M")
    MSD = (start + np.arange(H + 400)).astype("datetime64[D]").astype(np.int32)   # ngày đầu từng tháng (epoch days)

    def midx(s):
        return int((np.datetime64(s, "M") - start).astype(np.int64))

    cum = np.round(np.cumsum(SHARE) * N).astype(np.int64)
    cum[-1] = N
    dm = build_dm(cfg)
    cdf = np.cumsum(dm["c_w"]); cdf /= cdf[-1]
    scen = np.cumsum(SCEN_P, axis=1); scen[:, -1] = 1.0
    dcum = np.cumsum(DUR_P, axis=1); dcum[:, -1] = 1.0
    ho_p = HO_W / HO_W.sum()
    m_names = [f"{h} {d} {t}".upper() for h in HO for d in DEM_M for t in TEN_M]
    f_names = [f"{h} {d} {t}".upper() for h in HO for d in DEM_F for t in TEN_F]
    names_all = pa.array(m_names + f_names)
    kcb_lut = pa.array([f"{i:05d}" for i in range(65000)])
    num_lut = pa.array([str(i) for i in range(500)])
    prefix_table = [f"{k}{m}{p:02d}" for k in KHOI for m in range(10) for p in range(100)]
    prefix_pa = pa.array(prefix_table)
    ctx = dict(
        cfg=cfg, H=H, MSD=MSD, base_idx=midx(cfg["base_month"]), check_idx=midx(cfg["check_month"]),
        ref_days=int(np.datetime64(cfg["base_month"], "D").astype(np.int64)),
        khoi_bounds=cum, perm_a=_coprime(int(0.6180339887 * N) | 1, N), perm_b=int(cfg["seed"]) % N,
        so_a=1_000_000_007, so_b=int(cfg["seed"]) * 7919 % 9_000_000_000,
        scen_cum=scen, dur_cum=dcum, dm=dm, dm_cdf=cdf, n_dm=len(cdf),
        dm_name=pa.array(dm["c_name"]), dm_id=dm["c_id"], dm_prov=dm["c_prov"].astype(np.int64),
        ho_p=ho_p, ho=pa.array(HO), dem=pa.array(DEM_M + DEM_F), ten=pa.array(TEN_M + TEN_F),
        names_all=names_all, kcb_lut=kcb_lut, num_lut=num_lut, prefix_pa=prefix_pa,
        street=pa.array(STREETS), ward_kind=pa.array(WARD_KIND),
        khoi_pa=pa.array(KHOI), khoi_var=pa.array(KHOI_VARIANTS), digit=pa.array([str(i) for i in range(10)]),
        prov_str=pa.array(["%02d" % i for i in range(100)]),
    )
    assert math.gcd(ctx["so_a"], 9_000_000_000) == 1
    return ctx


@nb.njit(fastmath=True, nogil=True)
def fast_loai(owner, den, dmc, c_khoi, tu, rand_chtr):
    n = len(owner)
    loai = np.empty(n, dtype=np.int8)
    for i in range(n):
        if i == 0 or owner[i] != owner[i-1] or tu[i] > den[i-1] + 1:
            loai[i] = 0
        elif c_khoi[i] != c_khoi[i-1]:
            loai[i] = 3
        elif dmc[i] != dmc[i-1]:
            loai[i] = 2
        elif c_khoi[i] <= 1 and rand_chtr[i] < 0.02:
            loai[i] = 5
        else:
            loai[i] = 1
    return loai


_CTX = None


def _init_worker(cfg):
    global _CTX
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    _CTX = make_ctx(cfg)
    fast_loai(np.array([0, 0, 1]), np.array([100, 200, 300]), np.array([1, 1, 2]),
              np.array([0, 0, 1], dtype=np.int8), np.array([50, 150, 250]), np.array([0.5, 0.5, 0.5]))


# ============================================================================================
# Vòng đời
# ============================================================================================
def rint(rng, lo, hi):
    lo = np.minimum(lo, np.asarray(hi) - 1)
    return rng.integers(lo, hi)


def plan_segments(rng, ctx, khoi, birth):
    """Mỗi người có 1-2 đoạn tham gia liên tục. Trả về kịch bản + mảng đoạn."""
    H, CK = ctx["H"], ctx["check_idx"]
    n = khoi.size
    hssv = khoi <= SV
    u = rng.random(n)[:, None]
    sc = (u > ctx["scen_cum"][khoi]).sum(1).astype(np.int8)

    # HS đủ 18 tuổi trong giai đoạn: lên SV (80%), dừng (10%), chuyển khối (10%)
    m18 = np.searchsorted(ctx["MSD"], birth + 6575, side="left")             # tháng đầu tiên sau sinh nhật 18 tuổi
    forced = (khoi == HS) & (m18 < H)
    r = rng.random(n)
    sc = np.where(forced, np.where(r < 0.80, 5, np.where(r < 0.90, 1, 2)), sc).astype(np.int8)

    # tháng bắt đầu đoạn A (HSSV: khai giảng tháng 1 / tháng 10 -> đảm bảo thẻ đầu phủ tháng gốc)
    b = rng.random(n)
    s0 = np.where(hssv, np.where(b < 0.30, 0, np.where(b < 0.85, ctx["base_idx"], rng.integers(1, ctx["base_idx"], n))),
                  np.where(b < 0.65, 0, rng.integers(0, 30, n)))
    late = sc == 4
    seas_start = np.array([c for c in (12, 21, 24, 33) if c < H - 2])
    s_late_h = np.where(rng.random(n) < 0.5, rng.choice(seas_start, n), rint(rng, 10, H - 2))
    s_late_o = rint(rng, 1, H - 2)
    s0 = np.where(late, np.where(hssv, s_late_h, s_late_o), s0)
    gap = sc == 3
    s0 = np.where(gap & ~hssv, np.minimum(s0, 20), s0)
    mb = np.searchsorted(ctx["MSD"], birth, side="right") - 1                # tháng sinh (<0 nếu sinh trước 2024-01)
    s0 = np.where(mb >= 0, np.maximum(s0, mb + 1), s0)                        # không cấp thẻ trước khi sinh
    thr = np.where(khoi == HS, 6, np.where(khoi == SV, 18, 0)) * 365.25     # HS từ đủ 6 tuổi, SV từ đủ 18 tuổi
    s0 = np.where(hssv, np.maximum(s0, np.searchsorted(ctx["MSD"], birth + thr, side="left")), s0)

    # tháng kết thúc đoạn A. HSSV dừng tập trung mùa hè (tháng 6-9). Kết thúc luôn <= CK-1 để chắc chắn "dừng".
    summer = np.array([c for c in (17, 18, 18, 19, 19, 20, 21, 29, 30, 30) if 10 <= c <= CK - 1])
    if summer.size == 0:
        summer = np.arange(10, max(11, CK))
    e_stop_h = np.where(rng.random(n) < 0.7, rng.choice(summer, n), rint(rng, 10, CK))
    e_stop_o = rint(rng, s0 + 1, CK)
    e_stop = np.where(hssv, e_stop_h, e_stop_o)
    e_gap = np.where(hssv, rint(rng, 10, 25), rint(rng, s0 + 2, 25))
    eA = np.full(n, H, dtype=np.int64)
    eA = np.where((sc == 1) | (sc == 2), e_stop, eA)
    eA = np.where(gap, e_gap, eA)
    eA = np.where(forced & (sc == 5), np.clip(m18, 10, H - 1), eA)
    eA = np.where(forced & ((sc == 1) | (sc == 2)), np.clip(m18, 10, CK - 1), eA)
    eA = np.where(sc == 5, np.where(forced, eA, rng.choice(summer, n)), eA)

    g = rng.integers(1, 7, n)
    hasB = (sc == 2) | (sc == 3) | (sc == 5)
    sB = np.where(sc == 3, eA + g, eA)
    sw = np.where(((khoi == SV) & (rng.random(n) < 0.7)) | (khoi == GD), DN, GD)
    kB = np.where(sc == 5, SV, np.where(sc == 2, sw, khoi)).astype(np.int8)

    ib = np.flatnonzero(hasB)
    owner = np.concatenate([np.arange(n), ib])
    start = np.concatenate([s0, sB[ib]]).astype(np.int16)
    end = np.concatenate([eA, np.full(ib.size, H)]).astype(np.int16)
    kh = np.concatenate([khoi, kB[ib]]).astype(np.int8)
    order = np.concatenate([np.zeros(n, np.int64), np.ones(ib.size, np.int64)])
    return sc, owner, start, end, kh, order


def gen_cards(rng, ctx, start, end, kh):
    """Sinh thẻ nối tiếp nhau trong từng đoạn: lặp theo 'thẻ thứ k' cho TẤT CẢ đoạn cùng lúc."""
    cur = start.copy()
    opn = end >= ctx["H"]                    # đoạn "mở": thẻ cuối chạy hết chu kỳ tự nhiên (có thể sang 2027)
    act = np.arange(start.size)
    seg, cs, cd, ck = [], [], [], []
    k = 0
    while act.size:
        u = rng.random(act.size)[:, None]
        d = DUR_VALUES[(u > ctx["dur_cum"][kh[act]]).sum(1)]
        d = np.where(opn[act], d, np.minimum(d, end[act] - cur[act]))   # đoạn có điểm dừng rõ ràng: cắt thẻ cuối
        seg.append(act); cs.append(cur[act].copy()); cd.append(d); ck.append(np.full(act.size, k, np.int64))
        cur[act] += d
        act = act[cur[act] < end[act]]
        k += 1
    return np.concatenate(seg), np.concatenate(cs), np.concatenate(cd), np.concatenate(ck)


# ============================================================================================
# Hàm tiện ích chuỗi (pyarrow compute, vector hóa trong C++)
# ============================================================================================
def _str(arr):
    return pc.cast(pa.array(arr), pa.string())


def _dict(idx, values, mask=None):
    ind = pa.array(np.asarray(idx).astype(np.int8), mask=mask)
    return pa.DictionaryArray.from_arrays(ind, pa.array(values))


def _date(days, mask=None):
    return pa.array(np.asarray(days).astype(np.int32), type=pa.int32(), mask=mask).cast(pa.date32())


def _addr(rng, ctx, n, dm_idx):
    no = ctx["num_lut"].take(pa.array(rng.integers(1, 400, n)))
    st = ctx["street"].take(pa.array(rng.integers(0, len(STREETS), n)))
    wk = ctx["ward_kind"].take(pa.array(rng.integers(0, 3, n)))
    ward = pc.binary_join_element_wise(wk, ctx["num_lut"].take(pa.array(rng.integers(1, 30, n))), " ")
    dn = ctx["dm_name"].take(pa.array(dm_idx))
    return pc.binary_join_element_wise(pa.repeat("Số", n), no, st, ward, dn, ", ")


# ============================================================================================
# Build 1 chunk
# ============================================================================================
def build_chunk(ctx, chunk_id, p0, p1, dirty_rate=None):
    cfg = ctx["cfg"]
    H, MSD = ctx["H"], ctx["MSD"]
    dirty_rate = cfg["dirty_rate"] if dirty_rate is None else dirty_rate
    rng = np.random.default_rng(np.random.SeedSequence([cfg["seed"], chunk_id]))
    n = p1 - p0
    pidx = np.arange(p0, p1, dtype=np.int64)
    N = cfg["n_persons"]

    # ---- người ----
    perm = (ctx["perm_a"] * pidx + ctx["perm_b"]) % N
    khoi = np.searchsorted(ctx["khoi_bounds"], perm, side="right").astype(np.int8)
    so = 1_000_000_000 + (ctx["so_a"] * pidx + ctx["so_b"]) % 9_000_000_000
    gender = np.where(rng.random(n) < 0.505, 1, 2).astype(np.int8)
    birth = (ctx["ref_days"] - (AGE_LO[khoi] + rng.random(n) * (AGE_HI[khoi] - AGE_LO[khoi])) * 365.25).astype(np.int32)
    dm1 = np.minimum(np.searchsorted(ctx["dm_cdf"], rng.random(n)), ctx["n_dm"] - 1)
    dm2 = np.minimum(np.searchsorted(ctx["dm_cdf"], rng.random(n)), ctx["n_dm"] - 1)
    dm2 = np.where(dm2 == dm1, (dm2 + 1) % ctx["n_dm"], dm2)
    moved = rng.random(n) < P_MOVE
    move_m = rng.integers(3, H - 1, n)
    dayoff = np.where(rng.random(n) < P_DAYOFF, rng.integers(1, 28, n), 0)
    school = np.where(khoi == HS, rng.integers(0, 40000, n), rng.integers(0, 500, n))
    employer = rng.integers(0, 600_000, n)
    wage = rng.lognormal(math.log(9_000_000), 0.45, n)
    rr = rng.random(n)
    f_repl = rr < P_CANCEL_REPL
    f_norepl = (rr >= P_CANCEL_REPL) & (rr < P_CANCEL_REPL + P_CANCEL_NOREPL)

    # ---- vòng đời -> thẻ ----
    sc, s_owner, s_start, s_end, s_kh, s_order = plan_segments(rng, ctx, khoi, birth)
    c_seg, c_start, c_dur, c_k = gen_cards(rng, ctx, s_start, s_end, s_kh)
    owner = s_owner[c_seg]
    key = owner * 1024 + s_order[c_seg] * 512 + c_k
    o = np.argsort(key)
    owner, c_start, c_dur, c_khoi = owner[o], c_start[o].astype(np.int64), c_dur[o].astype(np.int64), s_kh[c_seg][o]
    M = owner.size
    pstart = np.searchsorted(owner, np.arange(n))
    pcount = np.bincount(owner, minlength=n)
    seq = np.arange(M) - pstart[owner]

    tu = MSD[c_start] + dayoff[owner]
    den = MSD[c_start + c_dur] + dayoff[owner] - 1
    use2 = moved[owner] & (c_start >= move_m[owner])
    dmc = np.where(use2, dm2[owner], dm1[owner])
    rand_chtr = rng.random(M)
    loai = fast_loai(owner, den, dmc, c_khoi, tu, rand_chtr)

    # ---- hủy / thay thế ----
    status = np.ones(M, np.int8)
    huy = np.zeros(M, np.int32)
    huy_mask = np.ones(M, bool)
    lydo = np.zeros(M, np.int8)
    fp = np.flatnonzero(f_repl | f_norepl)
    ci = pstart[fp] + (rng.random(fp.size) * pcount[fp]).astype(np.int64)
    status[ci] = 0
    huy[ci] = tu[ci] + (rng.random(fp.size) * (den[ci] - tu[ci] + 1)).astype(np.int32)
    huy_mask[ci] = False
    lydo[ci] = np.where(f_repl[fp], 0, rng.integers(1, 3, fp.size))
    rci = ci[f_repl[fp]]
    R = rci.size

    def cat(a, extra):
        return np.concatenate([a, extra])

    owner_all = cat(owner, owner[rci])
    seq_all = cat(seq, pcount[owner[rci]])
    A = dict(owner=owner_all, seq=seq_all, khoi=cat(c_khoi, c_khoi[rci]), start=cat(c_start, c_start[rci]),
             dur=cat(c_dur, c_dur[rci]), tu=cat(tu, tu[rci]), den=cat(den, den[rci]), dm=cat(dmc, dmc[rci]),
             use2=cat(use2, use2[rci]), status=cat(status, np.ones(R, np.int8)),
             loai=cat(loai, np.full(R, 4, np.int8)), huy=cat(huy, np.zeros(R, np.int32)),
             huy_mask=cat(huy_mask, np.ones(R, bool)), lydo=cat(lydo, np.zeros(R, np.int8)),
             cu=cat(np.full(M, -1, np.int64), rci), repl_from=cat(np.full(M, -1, np.int64), rci))
    # thẻ thay thế: NGAY_CAP = NGAY_HUY của thẻ cũ
    A["cap_override"] = cat(np.full(M, -1, np.int64), huy[rci].astype(np.int64))
    ID = (p0 + A["owner"]) * ID_STRIDE + A["seq"] + 1
    ordr = np.argsort(ID)
    if R:
        inv = np.empty(ordr.size, np.int64); inv[ordr] = np.arange(ordr.size)
        A = {k: v[ordr] for k, v in A.items()}
        A["cu"] = np.where(A["cu"] >= 0, inv[np.maximum(A["cu"], 0)], -1)
        A["repl_from"] = np.where(A["repl_from"] >= 0, inv[np.maximum(A["repl_from"], 0)], -1)
        ID = ID[ordr]
    T = ID.size
    ow = A["owner"]

    # ---- thuộc tính mức thẻ ----
    muc = np.zeros(T, np.int8)
    for k_, ch in MUC_HUONG_CHOICES.items():
        m_ = A["khoi"] == k_
        muc[m_] = np.array(ch, np.int8)[rng.integers(0, len(ch), int(m_.sum()))]
    mpm = np.zeros(T, np.int64)
    for k_, v in RATE_FIXED.items():
        mpm[A["khoi"] == k_] = v
    isdn = A["khoi"] == DN
    mpm[isdn] = (wage[ow][isdn] * 0.045).astype(np.int64)
    muc_dong = mpm * A["dur"]
    cap = A["tu"] - rng.integers(0, 8, T)
    cap = np.where(A["cap_override"] >= 0, A["cap_override"], cap).astype(np.int32)
    cap_nhat = np.where(A["status"] == 0, A["huy"], cap + rng.integers(0, 30, T)).astype(np.int32)
    nguon = np.where(A["khoi"] <= SV, rng.choice([1, 0, 3], T, p=[0.85, 0.10, 0.05]),
                     np.where(A["khoi"] == DN, rng.choice([2, 0, 3], T, p=[0.80, 0.15, 0.05]),
                              rng.choice([0, 3], T, p=[0.8, 0.2])))
    prov = ctx["dm_prov"][A["dm"]]
    kcb = prov * 1000 + (so[ow] % 400) + 1
    sid = np.where(A["khoi"] == HS, school[ow], np.where(A["khoi"] == SV, 100000 + school[ow], -1))
    emp = np.where(A["khoi"] == DN, employer[ow], -1)

    # ---- dòng bẩn có chủ đích ----
    sel = np.flatnonzero(rng.random(T) < dirty_rate) if dirty_rate > 0 else np.zeros(0, np.int64)
    dtype_ = rng.integers(1, 6, sel.size)
    tu_a, den_a = A["tu"].copy(), A["den"].copy()
    gender_c = gender[ow].copy()
    khoi_idx = A["khoi"].astype(np.int64)
    name_null = np.zeros(T, bool)
    s1 = sel[dtype_ == 1]; tu_a[s1], den_a[s1] = A["den"][s1], A["tu"][s1]
    s2 = sel[dtype_ == 2]; name_null[s2] = True
    s3 = sel[dtype_ == 3]; gender_c[s3] = 3
    s4 = sel[dtype_ == 4]; khoi_idx[s4] += 6
    s5 = sel[dtype_ == 5]
    dirty_cols = {1: "TU_NGAY/DEN_NGAY", 2: "HO_TEN", 3: "GIOI_TINH", 4: "MA_KHOI", 5: "*"}
    dlog = pa.table({"ID": pa.array(ID[sel], pa.int64()), "LOAI_LOI": pa.array(dtype_.astype(np.int8)),
                     "MO_TA": pa.array([DIRTY_NAMES[int(t)] for t in dtype_], pa.string()),
                     "COT": pa.array([dirty_cols[int(t)] for t in dtype_], pa.string())})
    rows = np.concatenate([np.arange(T), s5])      # dòng trùng lặp nối ở cuối, giống hệt dòng gốc (kể cả ID)

    # ---- chuỗi mức người ----
    sg = np.where(gender == 1, 0, 1)
    ho_i = rng.choice(len(HO), n, p=ctx["ho_p"])
    dem_i = np.where(sg == 0, rng.integers(0, len(DEM_M), n), len(DEM_M) + rng.integers(0, len(DEM_F), n))
    ten_i = np.where(sg == 0, rng.integers(0, len(TEN_M), n), len(TEN_M) + rng.integers(0, len(TEN_F), n))
    dem_sub = np.where(sg == 0, dem_i, dem_i - 15)
    ten_sub = np.where(sg == 0, ten_i, ten_i - 25)
    name_idx = np.where(sg == 0, 0, 10500) + ho_i * 375 + dem_sub * 25 + ten_sub
    so_s = _str(so)
    # CCCD 12 số: [3 mã tỉnh][1 giới tính-thế kỷ][2 năm sinh][6 ngẫu nhiên]; chỉ có từ 14 tuổi
    yr = 1970 + birth / 365.2425
    gcode = np.where(yr >= 2000, 1 + gender, gender - 1).astype(np.int64)
    cmnd_v = (ctx["dm_prov"][dm1] * 10**9 + gcode * 10**8 + (yr.astype(np.int64) % 100) * 10**6 + rng.integers(0, 10**6, n))
    has_cmnd = birth <= ctx["ref_days"] - 14 * 365.25
    cmnd = pc.utf8_lpad(_str(pa.array(cmnd_v, mask=~has_cmnd)), 12, "0")
    addr = pa.concat_arrays([_addr(rng, ctx, n, dm1), _addr(rng, ctx, n, dm2)])
    ow_r, ow_pa = ow[rows], pa.array(ow[rows])
    addr_idx = pa.array(ow_r + n * A["use2"][rows])

    pref_idx = A["khoi"].astype(np.int64) * 1000 + muc.astype(np.int64) * 100 + prov
    so_the_clean = pc.binary_join_element_wise(ctx["prefix_pa"].take(pa.array(pref_idx)), so_s.take(pa.array(ow)), "")
    cu_pa = so_the_clean.take(pa.array(np.maximum(A["cu"], 0), mask=A["cu"] < 0))
    r_ = lambda a: a[rows]                                                 # noqa: E731

    cols = {
        "ID": pa.array(r_(ID), pa.int64()),
        "SO_SO_BHXH": so_s.take(ow_pa),
        "SO_THE_KCB": so_the_clean.take(pa.array(rows)),
        "HO_TEN": ctx["names_all"].take(pa.array(name_idx[ow_r], mask=r_(name_null))),
        "NGAY_SINH": _date(birth[ow_r]),
        "GIOI_TINH": pa.array(r_(gender_c), pa.int8()),
        "SO_CMND": cmnd.take(ow_pa),
        "DIA_CHI": addr.take(addr_idx),
        "MA_TINH": _dict(r_(prov), ctx["prov_str"].to_pylist()),
        "MA_KHOI": _dict(r_(khoi_idx), KHOI_VARIANTS),
        "MUC_HUONG": pa.array(r_(muc), pa.int8()),
        "TU_NGAY": _date(r_(tu_a)),
        "DEN_NGAY": _date(r_(den_a)),
        "TRANG_THAI": pa.array(r_(A["status"]), pa.int8()),
        "DM_BHXH_ID": pa.array(ctx["dm_id"][r_(A["dm"])], pa.int32()),
        "LOAI_THE": _dict(r_(A["loai"]), LOAI_THE),
        "SO_THE_CU": cu_pa.take(pa.array(rows)),
        "NGAY_CAP": _date(r_(cap)),
        "NGAY_HUY": _date(r_(A["huy"]), mask=r_(A["huy_mask"])),
        "LY_DO_HUY": _dict(r_(A["lydo"]), LY_DO_HUY, mask=r_(A["huy_mask"])),
        "SO_THANG": pa.array(r_(A["dur"]), pa.int8()),
        "MUC_DONG": pa.array(r_(muc_dong), pa.int64()),
        "MA_TRUONG": pc.utf8_lpad(_str(pa.array(np.maximum(r_(sid), 0), mask=r_(sid) < 0)), 6, "0"),
        "MA_KCB_BD": ctx["kcb_lut"].take(pa.array(r_(kcb))),
        "MA_DON_VI": pc.utf8_lpad(_str(pa.array(np.maximum(r_(emp), 0), mask=r_(emp) < 0)), 8, "0"),
        "SO_BIEN_LAI": pa.array(rng.integers(10**9, 10**10, rows.size), pa.int64()),
        "NGUOI_TAO": pa.array(rng.integers(1, 5000, rows.size), pa.int32()),
        "NGAY_TAO": _date(r_(cap)),
        "NGAY_CAP_NHAT": _date(r_(cap_nhat)),
        "NGUON_DU_LIEU": _dict(r_(nguon), NGUON),
    }
    tbl = pa.table([cols[c] for c in COLUMNS], names=COLUMNS)
    scn = np.array(SC_NAMES)[sc]
    persons = pa.table({
        "person_idx": pa.array(pidx), "SO_SO_BHXH": pa.array(so), "KHOI_GOC": pa.array(np.array(KHOI)[khoi]),
        "KICH_BAN": pa.array(scn), "HUY_THAY_THE": pa.array(f_repl), "HUY_KHONG_THAY": pa.array(f_norepl),
        "CHUYEN_DIA_BAN": pa.array(moved)})
    stats = dict(rows=int(tbl.num_rows), persons=int(n), clean_rows=int(T),
                 rows_by_khoi=np.bincount(A["khoi"], minlength=6).tolist(),
                 persons_by_khoi=np.bincount(khoi, minlength=6).tolist(),
                 scenarios=np.bincount(sc, minlength=6).tolist(), dirty=int(sel.size))
    return tbl, persons, dlog, stats


# ============================================================================================
# Ghi file + manifest + chạy chunk
# ============================================================================================
def _atomic_write(table, path, compression):
    tmp = path + ".tmp"
    pq.write_table(table, tmp, compression=compression, row_group_size=1_000_000, use_dictionary=True)
    os.replace(tmp, path)


def _paths(out, cid):
    return {k: os.path.join(out, d, "part-%05d.parquet" % cid) for k, d in
            (("dtl", "st_inthe_dtl"), ("per", "persons_gt"), ("dir", "dirty_log"))}


def _manifest(out, cid):
    return os.path.join(out, "_manifest", "chunk-%05d.json" % cid)


def chunk_done(out, cid):
    m = _manifest(out, cid)
    if not os.path.exists(m):
        return False
    try:
        info = json.load(open(m, encoding="utf-8"))
        return os.path.exists(_paths(out, cid)["dtl"]) and \
            os.path.getsize(_paths(out, cid)["dtl"]) == info["bytes"]
    except Exception:
        return False


def run_chunk(task):
    cid, p0, p1, out = task
    t0 = time.perf_counter()
    tbl, per, dlog, st = build_chunk(_CTX, cid, p0, p1)
    t1 = time.perf_counter()
    comp = _CTX["cfg"]["compression"]
    P = _paths(out, cid)
    _atomic_write(tbl, P["dtl"], comp)
    _atomic_write(per, P["per"], comp)
    _atomic_write(dlog, P["dir"], comp)
    st.update(chunk_id=cid, p0=p0, p1=p1, bytes=os.path.getsize(P["dtl"]),
              sec_build=round(t1 - t0, 3), sec_write=round(time.perf_counter() - t1, 3))
    tmp = _manifest(out, cid) + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, _manifest(out, cid))               # manifest ghi SAU CÙNG = chunk hoàn tất
    return st


def cfg_hash(cfg):
    keys = {k: cfg[k] for k in sorted(cfg) if k not in ("compression",)}
    return hashlib.sha1(json.dumps(keys, sort_keys=True, default=str).encode()).hexdigest()[:12]


def generate(cfg, out, workers, force=False, quiet=False):
    for d in ("st_inthe_dtl", "persons_gt", "dirty_log", "_manifest"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    meta_p = os.path.join(out, "_meta.json")
    h = cfg_hash(cfg)
    if os.path.exists(meta_p):
        old = json.load(open(meta_p, encoding="utf-8"))
        if old["hash"] != h and not force:
            sys.exit("Cấu hình khác lần chạy trước (hash %s != %s). Dùng --force để xóa chunk cũ, hoặc đổi --out." % (old["hash"], h))
        if old["hash"] != h:
            for d in ("st_inthe_dtl", "persons_gt", "dirty_log", "_manifest"):
                shutil.rmtree(os.path.join(out, d)); os.makedirs(os.path.join(out, d))
    json.dump(dict(hash=h, cfg=cfg, columns=COLUMNS, khoi=KHOI, share=SHARE, sc_names=SC_NAMES, id_stride=ID_STRIDE),
              open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    for root, _, files in os.walk(out):
        for f in files:
            if f.endswith(".tmp"):
                os.remove(os.path.join(root, f))
    pq.write_table(dm_table(build_dm(cfg)), os.path.join(out, "dm_bhxh.parquet"))

    N, cp = cfg["n_persons"], cfg["chunk_persons"]
    chunks = [(i, i * cp, min(N, (i + 1) * cp)) for i in range((N + cp - 1) // cp)]
    todo = [(c, a, b, out) for c, a, b in chunks if force or not chunk_done(out, c)]
    total_rows = sum(json.load(open(_manifest(out, c), encoding="utf-8"))["rows"] for c, _, _ in chunks
                     if chunk_done(out, c) and not any(c == t[0] for t in todo))
    t_start_str = time.strftime("%Y-%m-%d %H:%M:%S")
    if not quiet:
        print("=" * 80)
        print("BẮT ĐẦU SINH DỮ LIỆU BHYT: %s người | mốc %s -> %s" % (format(N, ","), cfg["base_month"], cfg["check_month"]))
        print("Chunks: %d tổng, %d đã xong, %d cần chạy | workers = %d | nén = %s" % (
            len(chunks), len(chunks) - len(todo), len(todo), workers, cfg["compression"]))
        print("Thời điểm bắt đầu: %s" % t_start_str)
        print("=" * 80)

    t0, done, rows_new = time.perf_counter(), 0, 0
    total_dirty = 0
    total_bytes = 0
    rbk_total = np.zeros(6, np.int64)
    scen_total = np.zeros(6, np.int64)

    if workers <= 1:
        _init_worker(cfg)
        results = (run_chunk(t) for t in todo)
    else:
        ex = ProcessPoolExecutor(workers, initializer=_init_worker, initargs=(cfg,))
        futs = [ex.submit(run_chunk, t) for t in todo]
        results = (f.result() for f in as_completed(futs))
    try:
        for st in results:
            done += 1
            rows_new += st["rows"]
            total_rows += st["rows"]
            total_dirty += st.get("dirty", 0)
            total_bytes += st.get("bytes", 0)
            if "rows_by_khoi" in st:
                rbk_total += np.array(st["rows_by_khoi"], dtype=np.int64)
            if "scenarios" in st:
                scen_total += np.array(st["scenarios"], dtype=np.int64)

            el = time.perf_counter() - t0
            if not quiet:
                eta = el / done * (len(todo) - done)
                speed = rows_new / max(0.001, el)
                pct = 100 * done / len(todo)
                print("[%3d/%3d - %5.1f%%] chunk %05d: %s dòng (bld: %.2fs, wrt: %.2fs) | Tích lũy: %s dòng | %.0f dòng/s | ETA: %.1f phút" % (
                    done, len(todo), pct, st["chunk_id"], format(st["rows"], ","),
                    st.get("sec_build", 0.0), st.get("sec_write", 0.0),
                    format(total_rows, ","), speed, eta / 60), flush=True)
    except KeyboardInterrupt:
        print("\nDừng giữa chừng. Chạy lại cùng lệnh để tiếp tục (chunk xong được giữ nguyên).")
        if workers > 1:
            ex.shutdown(wait=False, cancel_futures=True)
        sys.exit(1)
    if workers > 1:
        ex.shutdown()
    el = time.perf_counter() - t0
    if not quiet:
        t_finish = time.strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 80)
        print("TỔNG KẾT SINH DỮ LIỆU BHYT (CV 835/QLT)")
        print("=" * 80)
        print("  Bắt đầu:               %s" % t_start_str)
        print("  Kết thúc:              %s" % t_finish)
        print("  Tổng thời gian:        %.2f giây (%d phút %02d giây)" % (el, int(el // 60), int(el % 60)))
        print("  Tổng số người:         %s người" % format(N, ","))
        print("  Tổng số dòng thẻ:      %s dòng" % format(total_rows, ","))
        print("  Tốc độ trung bình:     %.0f dòng/giây (%.0f người/giây)" % (rows_new / max(0.001, el), N / max(0.001, el)))
        print("  Số chunk đã sinh:      %d / %d chunks" % (len(chunks), len(chunks)))
        print("  Số dòng bẩn chủ đích:  %s dòng (%.2f%%)" % (format(total_dirty, ","), 100 * total_dirty / max(1, total_rows)))
        print("  Dung lượng trên đĩa:   %.2f MB (%.2f GB)" % (total_bytes / 1e6, total_bytes / 1e9))
        print("-" * 80)
        print("Cơ cấu dòng theo khối:")
        for k_i, k_name in enumerate(KHOI):
            print("  %-4s: %12s dòng (%5.1f%%)" % (k_name, format(rbk_total[k_i], ","), 100 * rbk_total[k_i] / max(1, total_rows)))
        print("-" * 80)
        print("Cơ cấu người theo kịch bản:")
        for sc_i, sc_name in enumerate(SC_NAMES):
            print("  %-8s: %12s người (%5.1f%%)" % (sc_name, format(scen_total[sc_i], ","), 100 * scen_total[sc_i] / max(1, N)))
        print("=" * 80 + "\n")
    return rows_new, el


# ============================================================================================
# calibrate / bench
# ============================================================================================
def calibrate(cfg, sample):
    ctx = make_ctx(cfg)
    fast_loai(np.array([0, 0, 1]), np.array([100, 200, 300]), np.array([1, 1, 2]),
              np.array([0, 0, 1], dtype=np.int8), np.array([50, 150, 250]), np.array([0.5, 0.5, 0.5]))
    cp = min(cfg["chunk_persons"], sample)
    tot = dict(rows=0, persons=0, rbk=np.zeros(6), pbk=np.zeros(6), sc=np.zeros(6))
    t0 = time.perf_counter()
    mid = cfg["n_persons"] // 2            # lấy mẫu từ giữa dải để không phụ thuộc đầu dải
    for i, a in enumerate(range(mid, mid + sample, cp)):
        _, _, _, st = build_chunk(ctx, 10_000 + i, a, min(a + cp, mid + sample))
        tot["rows"] += st["rows"]; tot["persons"] += st["persons"]
        tot["rbk"] += st["rows_by_khoi"]; tot["pbk"] += st["persons_by_khoi"]; tot["sc"] += st["scenarios"]
    el = time.perf_counter() - t0
    scale = cfg["n_persons"] / tot["persons"]
    print("Mẫu %s người -> %s dòng (%.2f dòng/người) trong %.1fs = %.0f dòng/s (1 process, gồm dựng bảng)" % (
        format(tot["persons"], ","), format(tot["rows"], ","), tot["rows"] / tot["persons"], el, tot["rows"] / el))
    print("Ngoại suy tổng cho %s người: ~%s dòng (mục tiêu ~200,000,000)" % (
        format(cfg["n_persons"], ","), format(int(tot["rows"] * scale), ",")))
    print("%-4s %12s %12s" % ("Khối", "thẻ/người", "ước tính M dòng"))
    for k in range(6):
        if tot["pbk"][k]:
            print("%-4s %12.2f %12.1f" % (KHOI[k], tot["rbk"][k] / tot["pbk"][k], tot["rbk"][k] * scale / 1e6))
    print("Kịch bản (toàn mẫu):", {SC_NAMES[i]: int(tot["sc"][i]) for i in range(6)})
    print("Thời gian 1 worker cho toàn bộ (ngoại suy tuyến tính, CHƯA gồm ghi Parquet): %.1f phút" % (
        tot["rows"] * scale / (tot["rows"] / el) / 60))


def bench(cfg, persons, chunk, workers_list):
    cfg = dict(cfg, n_persons=persons, chunk_persons=chunk)
    base = None
    print("%8s %10s %12s %10s %10s" % ("workers", "giây", "dòng/giây", "speedup", "efficiency"))
    for w in workers_list:
        tmp = tempfile.mkdtemp(prefix="bhyt_bench_")
        try:
            rows, el = generate(cfg, tmp, w, quiet=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        thr = rows / el
        base = base or (thr, w)
        s = thr / base[0]
        print("%8d %10.1f %12.0f %10.2f %9.0f%%" % (w, el, thr, s, 100 * s / (w / base[1])), flush=True)


# ============================================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--seed", type=int, default=DEFAULT_CFG["seed"])
        p.add_argument("--chunk-persons", type=int, default=DEFAULT_CFG["chunk_persons"])
        p.add_argument("--check-month", default=DEFAULT_CFG["check_month"])
        p.add_argument("--base-month", default=DEFAULT_CFG["base_month"])
        p.add_argument("--dirty-rate", type=float, default=DEFAULT_CFG["dirty_rate"])
        p.add_argument("--compression", default=DEFAULT_CFG["compression"], choices=["zstd", "snappy", "none"])
        p.add_argument("--dm-csv", default=None, help="CSV danh mục thật: ID,MA_DVI,TEN_DVI,MA_CHA[,TRONG_SO]")

    g = sp.add_parser("generate"); common(g)
    g.add_argument("--out", required=True)
    g.add_argument("--persons", type=int, default=DEFAULT_CFG["n_persons"])
    g.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    g.add_argument("--force", action="store_true", help="xóa chunk cũ nếu cấu hình khác")
    c = sp.add_parser("calibrate"); common(c)
    c.add_argument("--sample", type=int, default=200_000)
    c.add_argument("--persons", type=int, default=DEFAULT_CFG["n_persons"])
    b = sp.add_parser("bench"); common(b)
    b.add_argument("--persons", type=int, default=400_000)
    b.add_argument("--chunk", type=int, default=20_000)
    b.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    a = ap.parse_args()

    cfg = dict(DEFAULT_CFG, seed=a.seed, chunk_persons=a.chunk_persons, check_month=a.check_month,
               base_month=a.base_month, dirty_rate=a.dirty_rate, dm_csv=a.dm_csv,
               compression="NONE" if a.compression == "none" else a.compression)
    if a.compression == "none":
        cfg["compression"] = "none"
    if a.cmd == "generate":
        generate(dict(cfg, n_persons=a.persons), a.out, a.workers, a.force)
    elif a.cmd == "calibrate":
        calibrate(dict(cfg, n_persons=a.persons), a.sample)
    else:
        bench(cfg, a.persons, a.chunk, a.workers)


if __name__ == "__main__":
    main()
