#!/usr/bin/env python3
"""CO-111：【L2 自裁 · 参考平面/阻抗】In5 PCIe 走廊参考缺失**量化** + 口径裁定。

触发：CO-110 关闭 F-D 后仍缺「量」；本件把 In5←In4 走廊空洞从「54 段」量化为**长度占比**，
并核对 L5 SI 签证的**覆盖面**（只签 skew，未签阻抗）⇒ 该暴露属**未验**。

机判（全用声明数据，无坐标搜索）：
  A In5 上无 In4 参考的走线**全部**属 PCIe 类（PCIe85，target_zdiff 85Ω）——即阻抗受控网
  B 量化暴露：每条 PCIe 网 In5 走线在 In4 空洞内的长度 / 该网 In5 总长（合计 ≥ 下限）
  C L5 SI 记录**只签** intra-pair skew（`skew_ok`），无逐线阻抗核验字段 ⇒ 阻抗在走廊**未验**
裁定：走廊内 In5 PCIe 段落在 declared `symmetric_stripline(refs=[In4,In6])` 之外；终判 = SI9000 + 板厂阻抗券；
      若超规，补救层级 = (a) 走廊补 In4 铜（OWNER/PM）/ (b) 改线或换层（信号流向 ⇒ 或 L1）/ (c) 走廊段宽-隙补偿（L2，须场解）。

只读；不改 SPEC/板/阈值/冻结源。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co111_in5_pcie_corridor_exposure.py
"""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-13.json"
DRAW = STEP2 / "m13_v57_w3_joint_assignment.json"
SI = STEP2 / "m13_v57_l5_si_pi_emc_record.json"
OUT = STEP2 / "m13_v57_co111_in5_pcie_corridor_exposure.json"
CORRIDOR_X = (49.8, 88.37)
FLOOR_MM = 1000.0            # 非空真下限：走廊暴露总长下界
FLOOR_PCT = 0.39             # 非空真下限：暴露占比下界


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def polys_of(z):
    ps, p = z.get("polygons"), z.get("polygon")
    if ps:
        return ps if isinstance(ps[0][0], list) else [ps]
    if p:
        return [p] if not isinstance(p[0][0], list) else p
    return []


def pip(pt, poly):
    x, y = pt
    ins = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(SPEC.read_text()); draw = json.loads(DRAW.read_text())
    si = json.loads(SI.read_text())
    zd = spec["pd"]["zone_defs"]
    cu = collections.defaultdict(list)
    for g in zd.get("gnd_planes", []):
        for p in polys_of(g):
            cu[g["layer"]].append(p)
    for z in zd["power_zones"]:
        for p in polys_of(z):
            cu[z["layer"]].append(p)
    def ref_missing(q):
        return not any(pip(q, p) for p in cu.get("In4.Cu", []))
    def seg_lens(P):
        """(总长, 无 In4 参考长) —— 以段中点判参考（与 CO-106 同阶）。"""
        tot_l = miss_l = 0.0
        for i in range(len(P) - 1):
            A, B = tuple(P[i]), tuple(P[i + 1])
            L = ((B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2) ** 0.5
            tot_l += L
            if ref_missing(((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)):
                miss_l += L
        return tot_l, miss_l

    tot, unref = collections.Counter(), collections.Counter()
    for r in draw["route_geometry"]:
        if r["layer"] != "In5.Cu":
            continue
        net = (r["key"][0] if isinstance(r.get("key"), list) else str(r.get("key"))).split("/")[0]
        tl, ml = seg_lens(r["points"])
        tot[net] += tl; unref[net] += ml
    nets = sorted(tot)
    T = sum(tot.values()); U = sum(unref.values())
    worst = max(((n, unref[n], unref[n] / tot[n]) for n in nets if unref[n] > 1e-9), key=lambda x: x[1], default=("", 0, 0))
    per_net = {n: {"in5_len_mm": round(tot[n], 3), "unref_len_mm": round(unref[n], 3),
                   "unref_pct": round(unref[n] / tot[n], 4)} for n in nets}
    nclass = spec.get("net_classes", {})
    pcie_ok = all(str(n).startswith("PCIE_") or nclass.get(n, {}).get("diff_pair") for n in nets)
    imp_keys = [k for k in json.dumps(si, ensure_ascii=False).split('"') if "impedance" in k.lower()]
    per_route_imp = any(k for k in _walk_keys(si.get("SI", {})) if k in ("impedance_ok", "zdiff_ok", "impedance_verified"))
    checks = {
        "A_all_pcie_impedance_controlled": {
            "ok": bool(nets) and all(n.startswith("PCIE_") for n in nets),
            "nets": nets, "n_nets": len(nets),
            "pcie85_class": nclass.get("PCIe85", {}), "target_zdiff_ohm": spec["impedance"].get("target_zdiff"),
            "note": "In5 上失去 In4 参考的走线**全部**为 PCIe 差分对（阻抗受控）⇒ 非低速可忽略项"},
        "B_quantified_exposure": {
            "ok": U >= FLOOR_MM and (U / T) >= FLOOR_PCT,
            "in5_total_len_mm": round(T, 3), "unref_len_mm": round(U, 3), "unref_pct": round(U / T, 4),
            "floor_mm": FLOOR_MM, "floor_pct": FLOOR_PCT,
            "worst_net": {"net": worst[0], "unref_len_mm": round(worst[1], 3), "unref_pct": round(worst[2], 4)},
            "per_net": per_net, "corridor_x": list(CORRIDOR_X),
            "note": "暴露 = In5 走线落在 In4 走廊 x∈(49.8,88.37)（无声明 In4 铜）的**长度**"},
        "C_l5_si_does_not_verify_impedance": {
            "ok": bool(si.get("SI", {}).get("skew_ok") is True) and not per_route_imp,
            "skew_ok": si.get("SI", {}).get("skew_ok"),
            "impedance_model": si.get("SI", {}).get("netclass_geometry", {}).get("spec", {}).get("impedance_model"),
            "target_zdiff_ohm": si.get("SI", {}).get("netclass_geometry", {}).get("spec", {}).get("target_zdiff_ohm"),
            "note": "L5 SI 只签 intra-pair skew（本项目判据=按层加权电气长度）；**无逐线阻抗核验** ⇒ 走廊阻抗暴露未验"},
    }
    teeth = {}
    teeth["exposure_zero_control"] = (seg_lens([[100.0, 50.0], [120.0, 50.0]])[1] == 0.0)   # 全在东区 ⇒ 0
    teeth["exposure_positive_control"] = (seg_lens([[60.0, 50.0], [80.0, 50.0]])[1] > 0.0)  # 全在走廊 ⇒ >0
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    rulings = [
        {"id": "Q1", "level": "L2", "decision": f"In5 走廊参考缺失量化为 **{round(U,1)}/{round(T,1)}mm = {round(100*U/T,1)}%** 的 In5 PCIe 走线长度（{len(nets)} 网；最差 {worst[0]} {round(worst[1],1)}mm / {round(100*worst[2],1)}%）。"},
        {"id": "Q2", "level": "L2", "decision": "受影响网**全部**为 PCIe85 阻抗受控差分对 ⇒ 走廊内 declared `symmetric_stripline(refs=[In4,In6])` 不成立，属**实际阻抗暴露**（非可忽略）。"},
        {"id": "Q3", "level": "L2", "decision": "L5 SI 签证只覆盖 skew，**未**核验阻抗 ⇒ 该暴露在现行 G7 签核中**未被覆盖**，须显式登记（不得视为已验）。"},
        {"id": "Q4", "level": "EXTERNAL", "decision": "终判 = SI9000 + 板厂阻抗券（不得以假设值代填）。"},
        {"id": "Q5", "level": "OWNER/LAYERED", "decision": "若超规，补救层级：走廊补 In4 铜（OWNER/PM 反转 T2-ECN）/ 改线换层（信号流向 ⇒ 或 L1）/ 走廊段宽-隙补偿（L2，须场解）。"},
    ]
    rec = {"artifact": "m13_v57_co111_in5_pcie_corridor_exposure", "schema": 1, "revision": "CO-111.1",
           "nature": "L2 自裁量化：In5 PCIe 走廊参考缺失（长度占比）+ L5 阻抗覆盖面裁定",
           "inputs": {"spec_rev13": s16(SPEC), "drawing": s16(DRAW), "l5_si_record": s16(SI)},
           "checks": checks, "teeth": teeth, "rulings": rulings,
           "verdict": "L2_DECLARED_SI_EXPOSURE_EXTERNAL_TERMINAL" if all(v["ok"] for v in checks.values()) and teeth["teeth_ok"] else "FAIL",
           "non_claims": ["只读；不改 SPEC/板/阈值/冻结源", "不做阻抗数值计算（终判 = SI9000 + 板厂阻抗券）"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-111 verdict=%s | nets=%d unref=%.1f/%.1fmm=%.1f%% worst=%s %.1fmm | checks=%s | teeth=%s" % (
        rec["verdict"], len(nets), U, T, 100 * U / T, worst[0], worst[1],
        {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  record sha16:", s16(Path(a.out)))
    return 0


def _walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield str(k)
            yield from _walk_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk_keys(v)


if __name__ == "__main__":
    raise SystemExit(main())
