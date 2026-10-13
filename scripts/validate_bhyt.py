#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_bhyt.py - Kiểm tra bộ dữ liệu do gen_bhyt.py sinh ra và tính ĐÁP ÁN tham chiếu cho Ý 1 (CV 835/QLT).

  python validate_bhyt.py --data ./bhyt_data                       # kiểm tra + tính đáp án (định nghĩa: dừng mọi khối)
  python validate_bhyt.py --data ./bhyt_data --stop-def hssv       # định nghĩa: dừng khối HS/SV (HSSV chuyển DN/GD vẫn tính là dừng)
  python validate_bhyt.py --data ./bhyt_data --export ./answer     # xuất danh sách + thống kê theo tỉnh

Quy tắc giao tháng M (theo đề bài): thẻ TRANG_THAI=1, TU_NGAY < ngày đầu tháng M+1 và DEN_NGAY >= ngày đầu tháng M.
Người thuộc đáp án = có thẻ HS/SV hợp lệ giao tháng gốc  VÀ  không có thẻ hợp lệ giao tháng kiểm tra.
Người có dòng bẩn (dirty_log) bị loại khỏi phần so khớp đáp án - đếm riêng.
"""
import argparse
import glob
import json
import os
import sys

import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

NEED = ["ID", "SO_SO_BHXH", "SO_THE_KCB", "NGAY_SINH", "SO_CMND", "MA_TINH", "MA_KHOI", "MUC_HUONG", "TU_NGAY",
        "DEN_NGAY", "TRANG_THAI", "LOAI_THE", "SO_THE_CU", "NGAY_HUY"]
KHOI = ["HS", "SV", "TE", "DN", "GD", "HT"]
SHARE = [0.19, 0.06, 0.10, 0.30, 0.25, 0.10]


def month_days(s, plus=0):
    return int((np.datetime64(s, "M") + np.timedelta64(plus, "M")).astype("datetime64[D]").astype(np.int64))


def npc(col, typ=None):
    if typ is not None:
        col = col.cast(typ)
    return col.to_numpy(zero_copy_only=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--stop-def", choices=["any", "hssv"], default="any")
    ap.add_argument("--export", default=None, help="thư mục xuất answer_list.parquet + answer_by_tinh.csv")
    a = ap.parse_args()

    meta = json.load(open(os.path.join(a.data, "_meta.json"), encoding="utf-8"))
    cfg, stride, cols_exp = meta["cfg"], meta["id_stride"], meta["columns"]
    b0, b1 = month_days(cfg["base_month"]), month_days(cfg["base_month"], 1)
    c0, c1 = month_days(cfg["check_month"]), month_days(cfg["check_month"], 1)
    ref = b0
    mans = sorted(glob.glob(os.path.join(a.data, "_manifest", "chunk-*.json")))
    fails = []

    def check(name, bad, note=""):
        ok = bad == 0
        print("  [%s] %-58s %s %s" % ("OK " if ok else "LỖI", name, "" if ok else "vi phạm=%s" % format(bad, ","), note))
        if not ok:
            fails.append(name)

    exp_chunks = (cfg["n_persons"] + cfg["chunk_persons"] - 1) // cfg["chunk_persons"]
    print("Dữ liệu: %s | chunk manifest %d/%d | mốc gốc %s | mốc kiểm tra %s | định nghĩa dừng: %s" % (
        a.data, len(mans), exp_chunks, cfg["base_month"], cfg["check_month"], a.stop_def))
    if len(mans) != exp_chunks:
        fails.append("thiếu chunk")
        print("  [LỖI] Thiếu chunk - chạy lại generate để hoàn tất")

    agg = dict(rows=0, dirty=0, dups=0, id_range=0, dt_gt_den=0, kcb=0, age=0, cmnd=0, huy_null=0, thay_the=0,
               oracle_bad=0, oracle_n=0, skipped_dirty=0)
    pbk = np.zeros(6, np.int64)
    all_so, ans_so, ans_k, ans_p = [], [], [], []
    xtab = {}
    st_m = np.zeros(12); en_m = np.zeros(12)
    schema_ok = True

    import time
    t_val_start = time.perf_counter()

    for i_man, mp in enumerate(mans):
        info = json.load(open(mp, encoding="utf-8"))
        cid = info["chunk_id"]
        f = lambda d: os.path.join(a.data, d, "part-%05d.parquet" % cid)       # noqa: E731
        t = pq.read_table(f("st_inthe_dtl"))
        if cid == info["chunk_id"] and schema_ok:
            schema_ok = t.column_names == cols_exp
        per = pq.read_table(f("persons_gt"))
        dl = pq.read_table(f("dirty_log"))
        agg["rows"] += t.num_rows
        if t.num_rows != info["rows"]:
            fails.append("số dòng khác manifest chunk %d" % cid)

        ids = npc(t["ID"])
        d_ids = npc(dl["ID"])
        d_typ = npc(dl["LOAI_LOI"])
        agg["dirty"] += d_ids.size
        agg["dups"] += t.num_rows - np.unique(ids).size - int((d_typ == 5).sum())   # chênh lệch so với số dòng trùng chủ đích
        pi = ids // stride
        agg["id_range"] += int(((pi < info["p0"]) | (pi >= info["p1"])).sum())
        is_dirty = np.isin(ids, d_ids)
        clean = ~is_dirty

        tu, den = npc(t["TU_NGAY"], pa.int32()).astype(np.int64), npc(t["DEN_NGAY"], pa.int32()).astype(np.int64)
        status = npc(t["TRANG_THAI"])
        kh_s = pc.cast(t["MA_KHOI"], pa.string())
        agg["dt_gt_den"] += int(((den < tu) & clean).sum())

        # SO_THE_KCB = MA_KHOI + MUC_HUONG + MA_TINH + SO_SO_BHXH
        exp_kcb = pc.binary_join_element_wise(kh_s, pc.cast(t["MUC_HUONG"], pa.string()),
                                              pc.cast(t["MA_TINH"], pa.string()), t["SO_SO_BHXH"], "")
        kcb_bad = ~npc(pc.equal(exp_kcb, t["SO_THE_KCB"]))
        agg["kcb"] += int((kcb_bad & clean).sum())

        # tuổi theo khối tại TU_NGAY và SO_CMND theo tuổi
        birth = npc(t["NGAY_SINH"], pa.int32()).astype(np.int64)
        age = (tu - birth) / 365.25
        kh = np.full(t.num_rows, -1)
        for i, k in enumerate(KHOI):
            kh[npc(pc.equal(kh_s, k))] = i
        lim = {0: (5.99, 18.1), 1: (17.99, 25.5), 2: (-0.0001, 6.0)}
        bad_age = np.zeros(t.num_rows, bool)
        for k, (lo, hi) in lim.items():
            m = kh == k
            bad_age |= m & ((age < lo) | (age > hi))
        agg["age"] += int((bad_age & clean).sum())
        cmnd_null = npc(pc.is_null(t["SO_CMND"]))
        agg["cmnd"] += int(((cmnd_null != ((ref - birth) < 14 * 365.25)) & clean).sum())
        agg["huy_null"] += int(((npc(pc.is_null(t["NGAY_HUY"])) != (status == 1)) & clean).sum())
        thay = npc(pc.is_valid(t["SO_THE_CU"]))
        agg["thay_the"] += int(((thay != npc(pc.equal(pc.cast(t["LOAI_THE"], pa.string()), "CAP_DOI"))) & clean).sum())

        # mùa vụ HS/SV
        hs = (kh == 0) | (kh == 1)
        ok_ = hs & (status == 1) & clean
        tm = (tu[ok_].astype("datetime64[D]").astype("datetime64[M]").astype(np.int64) % 12)
        dm = (den[ok_].astype("datetime64[D]").astype("datetime64[M]").astype(np.int64) % 12)
        st_m += np.bincount(tm, minlength=12); en_m += np.bincount(dm, minlength=12)

        # ----- ĐÁP ÁN Ý 1 -----
        so = npc(t["SO_SO_BHXH"], pa.int64())
        uniq, inv = np.unique(so, return_inverse=True)
        valid = status == 1
        base = valid & (tu < b1) & (den >= b0)
        chk = valid & (tu < c1) & (den >= c0)
        has = lambda m: np.bincount(inv, weights=m, minlength=uniq.size) > 0       # noqa: E731
        b_hs, b_sv = has(base & (kh == 0)), has(base & (kh == 1))
        c_any = has(chk)
        c_hssv = has(chk & hs)
        in_ans = (b_hs | b_sv) & ~(c_any if a.stop_def == "any" else c_hssv)

        p_so = npc(per["SO_SO_BHXH"], pa.int64())
        pbk += np.bincount(npc(pc.index_in(per["KHOI_GOC"], pa.array(KHOI))), minlength=6)
        all_so.append(p_so)
        order = np.argsort(p_so)
        row = order[np.searchsorted(p_so[order], uniq)]
        scn = np.array(per["KICH_BAN"].to_pylist())[row]
        khg = np.array(per["KHOI_GOC"].to_pylist())[row]
        f_norepl = npc(per["HUY_KHONG_THAY"])[row]
        dirty_so = set(p_so[(d_ids // stride) - info["p0"]].tolist()) if d_ids.size else set()
        pd_ = np.isin(uniq, np.fromiter(dirty_so, np.int64, len(dirty_so))) if dirty_so else np.zeros(uniq.size, bool)

        is_h = (khg == "HS") | (khg == "SV")
        use = is_h & ~pd_ & ~f_norepl
        exp = np.isin(scn, ["STOP"]) | ((scn == "SWITCH") & (a.stop_def == "hssv"))
        agg["oracle_n"] += int(use.sum())
        agg["oracle_bad"] += int((use & (exp != in_ans)).sum())
        agg["skipped_dirty"] += int((is_h & pd_).sum())
        for s in np.unique(scn[is_h]):
            m = is_h & (scn == s)
            x = xtab.setdefault(s, [0, 0, 0])
            x[0] += int(m.sum()); x[1] += int((m & (b_hs | b_sv)).sum()); x[2] += int((m & in_ans).sum())

        if in_ans.any():
            prov = npc(pc.cast(pc.cast(t["MA_TINH"], pa.string()), pa.int16())).astype(np.int64)
            rows_b = np.flatnonzero(base & hs)
            p_prov = np.full(uniq.size, -1, np.int64)
            p_prov[inv[rows_b]] = prov[rows_b]
            ans_so.append(uniq[in_ans]); ans_p.append(p_prov[in_ans])
            ans_k.append(np.where(b_sv[in_ans] & ~b_hs[in_ans], "SV", np.where(b_hs[in_ans] & ~b_sv[in_ans], "HS", "CA2")))

        cur_done = i_man + 1
        if cur_done % 10 == 0 or cur_done == len(mans):
            el = time.perf_counter() - t_val_start
            spd = agg["rows"] / max(0.001, el)
            eta = (len(mans) - cur_done) * (el / cur_done)
            print("  [%3d/%3d - %5.1f%%] chunk %05d | %s dòng | %.0f dòng/s | Đã chạy: %.1fs | ETA: %.1f phút" % (
                cur_done, len(mans), 100 * cur_done / len(mans), cid, format(agg["rows"], ","), spd, el, eta / 60), flush=True)
    print()

    print("\nKIỂM TRA")
    check("Schema đúng %d cột, đúng thứ tự" % len(cols_exp), 0 if schema_ok else 1)
    check("ID trùng ngoài các dòng trùng lặp chủ đích", abs(agg["dups"]))
    check("ID nằm trong dải người của chunk", agg["id_range"])
    so_all = np.sort(np.concatenate(all_so))
    check("SO_SO_BHXH duy nhất toàn bộ người", int((so_all[1:] == so_all[:-1]).sum()))
    check("SO_SO_BHXH đủ 10 chữ số", int(((so_all < 10**9) | (so_all >= 10**10)).sum()))
    exp_pbk = np.round(np.cumsum(SHARE) * cfg["n_persons"]).astype(np.int64)
    exp_pbk = np.diff(np.r_[0, exp_pbk])
    check("Số người từng khối đúng cơ cấu (HS/SV/TE/DN/GD/HT)", int(np.abs(pbk - exp_pbk).sum()),
          "thực tế %s" % dict(zip(KHOI, pbk.tolist())))
    check("Dòng sạch có TU_NGAY <= DEN_NGAY", agg["dt_gt_den"])
    check("SO_THE_KCB = MA_KHOI + MUC_HUONG + MA_TINH + SO_SO_BHXH (15 ký tự)", agg["kcb"])
    check("Tuổi phù hợp khối (HS 6-18, SV 18-25, TE <6) tại TU_NGAY", agg["age"])
    check("SO_CMND null đúng khi < 14 tuổi", agg["cmnd"])
    check("NGAY_HUY có giá trị khi và chỉ khi TRANG_THAI = 0", agg["huy_null"])
    check("SO_THE_CU có giá trị khi và chỉ khi LOAI_THE = CAP_DOI", agg["thay_the"])
    check("Đáp án Ý 1 khớp kịch bản sinh (STOP có; CONT/GAP/LATE/UPGRADE không)", agg["oracle_bad"],
          "trên %s người HS/SV, bỏ %s người có dòng bẩn" % (format(agg["oracle_n"], ","), format(agg["skipped_dirty"], ",")))
    print("  Tổng dòng ST_INTHE_DTL: %s | dòng bẩn chủ đích: %s (%.2f%%)" % (
        format(agg["rows"], ","), format(agg["dirty"], ","), 100 * agg["dirty"] / max(1, agg["rows"])))

    print("\nMÙA VỤ HS/SV (% theo tháng 1..12, thẻ hợp lệ, dòng sạch)")
    print("  bắt đầu :", " ".join("%4.1f" % (100 * x / st_m.sum()) for x in st_m))
    print("  kết thúc:", " ".join("%4.1f" % (100 * x / en_m.sum()) for x in en_m))

    print("\nKỊCH BẢN HS/SV  (người | có thẻ HS/SV ở tháng gốc | thuộc đáp án)")
    for s in ["CONT", "STOP", "SWITCH", "GAP", "LATE", "UPGRADE"]:
        if s in xtab:
            print("  %-8s %10s %12s %10s" % (s, *[format(v, ",") for v in xtab[s]]))

    if ans_so:
        so_a, p_a, k_a = np.concatenate(ans_so), np.concatenate(ans_p), np.concatenate(ans_k)
        print("\nĐÁP ÁN Ý 1 (định nghĩa dừng = %s): tổng %s | HS %s | SV %s | vừa HS vừa SV %s" % (
            a.stop_def, format(so_a.size, ","), format(int((k_a == "HS").sum()), ","),
            format(int((k_a == "SV").sum()), ","), format(int((k_a == "CA2").sum()), ",")))
        if a.export:
            os.makedirs(a.export, exist_ok=True)
            pq.write_table(pa.table({"SO_SO_BHXH": so_a, "LOAI": k_a, "MA_TINH": p_a.astype(np.int16)}),
                           os.path.join(a.export, "answer_list.parquet"))
            tinh = np.unique(p_a)
            rows = [(int(p), int(((p_a == p) & (k_a == "HS")).sum()), int(((p_a == p) & (k_a == "SV")).sum())) for p in tinh]
            pacsv.write_csv(pa.table({"MA_TINH": [r[0] for r in rows], "SO_HOC_SINH_DUNG": [r[1] for r in rows],
                                      "SO_SINH_VIEN_DUNG": [r[2] for r in rows],
                                      "TONG_DUNG": [r[1] + r[2] for r in rows]}),
                            os.path.join(a.export, "answer_by_tinh.csv"))
            print("  Đã xuất:", os.path.join(a.export, "answer_list.parquet"), "và answer_by_tinh.csv")
    t_val_total = time.perf_counter() - t_val_start
    print("\nTHỜI GIAN KIỂM TRA:")
    print("  Thời gian chạy: %.1f giây (%.2f phút)" % (t_val_total, t_val_total / 60))
    print("  Tốc độ quét và xác thực: %.0f dòng/giây" % (agg["rows"] / max(0.001, t_val_total)))
    print("\nKẾT QUẢ: %s" % ("ĐẠT" if not fails else "KHÔNG ĐẠT -> " + "; ".join(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
