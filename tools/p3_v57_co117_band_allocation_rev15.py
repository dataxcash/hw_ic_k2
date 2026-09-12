#!/usr/bin/env python3
"""CO-117：【L2 自裁 · 施加】band In4 铺铜**归属分配** + SPEC **rev-15**（更正 rev-14 错误键 + 闭合走廊参考缺失）。

裁定层级（L2，非 L1）：
  《宪法》ch.2 把 **走廊分配 / PDN 架构** 列 L2，且 L2 **裁判标准**明含「**参考平面**」；
  冻结 L1（`L1_TOPOLOGY_v2.0.md` §电源域、`pd.power_partition`）= **粗分区**（东=P3V3 / 西=P3V3_AUX_MCU_VDD）
  + **域集合**，本件**不改域集合**（P3V3 / P3V3_AUX / MCU_VDD 不变）⇒ 项目先例 **CO-74**
  「层数/平面数/**电源域集合**/信号层数全不变 ⇒ L2」适用 ⇒ **L2 自裁**（CO-115 的 L1 归口系过高，更正）。

分配（零搜索：仅声明坐标 + 固定 POWER clearance 0.2，闭式）：
  强制区间：MCU_VDD ≥ 57.75（R29/R31-R34 东缘 57.55 + 0.2）；P3V3 ≤ 85.20（U6 P3V3 球/孔西缘 85.4 − 0.2）。
  自由区间 x∈(57.75, 85.20) 无声明目标 ⇒ L2 定为：**余下走廊归东侧既有权域 P3V3**
  （MCU_VDD 只扩到自身目标，最小位移；P3V3_EAST basis 本已声明覆盖 U6 P3V3 球）。
  ⇒ `MCU_VDD_WEST` 东缘 49.8→**57.75**；`P3V3_EAST` 西缘 88.37→**57.95**（=57.75+0.2）；界面中值 57.85。

SPEC 变更（rev-14 → rev-15，白名单断言）：
  1. `in4_corridor_void_by_design_v1`（CO-115 判为事实错误）→ 退役留存为 `retired_in4_corridor_void_by_design_v1`
  2. 新增 `in4_band_copper_allocation_v1`（本件 L2 分配声明）
  3. 两个 In4 显式 polygon 边界按上表更新（`P3V3_EAST` west / `MCU_VDD_WEST` east）
  4. `plane_reachability_status`：P3V3 由 unresolved → `resolved_by_co117`；`na_scope_v1.in5_corridor_reference` 更新
  5. `spec_version` → 1.1.spec-rev-15
只读除上述 SPEC；不改板/阈值/冻结源/其它键。L3 几何（含贯通孔反焊盘净距）= 施工确定性派生，非本件。
CLI: python3 tools/p3_v57_co117_band_allocation_rev15.py
"""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-14.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-15.json"
REC = STEP2 / "m13_v57_co117_band_allocation_rev15.json"
DRAW = STEP2 / "m13_v57_w3_joint_assignment.json"
CLR = 0.2
ALLOWED = (
    ".spec_version", ".pd.zone_defs.in4_corridor_void_by_design_v1",
    ".pd.zone_defs.retired_in4_corridor_void_by_design_v1", ".pd.zone_defs.in4_band_copper_allocation_v1",
    ".pd.zone_defs.power_zones[0].polygon", ".pd.zone_defs.power_zones[1].polygon",
    ".pd.zone_defs.plane_reachability_status.unresolved",
    ".pd.zone_defs.plane_reachability_status.resolved_by_co117",
    ".pd.zone_defs.plane_reachability_status.na_scope_v1.in5_corridor_reference",
)


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, o


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


def in5_exposure(spec, draw):
    """In5 走线落在无 In4 声明铜处的长度（段中点判，与 CO-111 同阶）。返回 (总长, 无参考长, 网表, 无参考段中点)。"""
    cu = []
    zd = spec["pd"]["zone_defs"]
    for g in zd.get("gnd_planes", []):
        if g.get("layer") == "In4.Cu":
            cu += polys_of(g)
    for z in zd["power_zones"]:
        if z.get("layer") == "In4.Cu":
            cu += polys_of(z)
    tot, unref = collections.Counter(), collections.Counter()
    for r in draw["route_geometry"]:
        if r["layer"] != "In5.Cu":
            continue
        key = r.get("key")
        net = (key[0] if isinstance(key, list) else str(key)).split("/")[0]
        P = r["points"]
        for i in range(len(P) - 1):
            A, B = tuple(P[i]), tuple(P[i + 1])
            L = ((B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2) ** 0.5
            tot[net] += L
            if not any(pip(((A[0] + B[0]) / 2, (A[1] + B[1]) / 2), p) for p in cu):
                unref[net] += L
    res = []
    for r in draw["route_geometry"]:
        if r["layer"] != "In5.Cu":
            continue
        P = r["points"]
        for i in range(len(P) - 1):
            A, B = tuple(P[i]), tuple(P[i + 1])
            m = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            if not any(pip(m, q) for q in cu):
                res.append(m)
    T, U = sum(tot.values()), sum(unref.values())
    return T, U, sorted(tot), res


def rect(y0, y1, x0, x1):
    return [[float(x0), float(y0)], [float(x1), float(y0)], [float(x1), float(y1)], [float(x0), float(y1)]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC)); ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    draw = json.loads(DRAW.read_text())
    src_obj = json.loads(Path(a.src).read_text())
    T0, U0, _, _ = in5_exposure(src_obj, draw)    # rev-14 基线
    spec = json.loads(json.dumps(src_obj))        # rev-15 候选（内存）
    before = dict(flat(src_obj))
    zd = spec["pd"]["zone_defs"]
    zones = {z["zone"]: z for z in zd["power_zones"]}
    mcu, p3v3 = zones["MCU_VDD_WEST"], zones["P3V3_EAST"]
    mcu_e0 = max(p[0] for p in mcu["polygon"]); p3v3_w0 = min(p[0] for p in p3v3["polygon"])
    # 强制区间（声明坐标 + 固定 clearance，闭式，零搜索）
    rez = zones["MCU_VDD_BCU_RESISTORS_IN4"]
    mcu_tgt_e = max(p[0] for p in rez["bcu_bridge_bands"][0])
    entries = zd["power_pad_connect"]["entries"]
    p3 = [e[key][0] for u in zd["plane_reachability_status"]["unresolved"] if u["net"] == "P3V3"
          for p in u["pads"] for e in entries if e.get("ref") == p.split(".")[0] and e.get("pad") == p.split(".")[1]
          for key in ("pad_pos", "via_pos") if key in e]
    mcu_e1 = round(mcu_tgt_e + CLR, 6); p3v3_w1 = round(min(p3) - CLR, 6)
    gap = [mcu_e1, p3v3_w1]; new_p3v3_w = round(mcu_e1 + CLR, 6)
    # 1) 错误键退役留存 + 2) 新分配声明
    zd["retired_in4_corridor_void_by_design_v1"] = dict(
        zd.pop("in4_corridor_void_by_design_v1"),
        retired_by="CO-117", retired_reason="CO-115 判其陈述（In4 走廊按设计无铜）为事实错误；"
                                            "本键被 in4_band_copper_allocation_v1 取代；CO-109 R2/CO-110 同批更正")
    zd["in4_band_copper_allocation_v1"] = {
        "note": "CO-117（L2 自裁）：原退役 keepout band 内 In4 铜按网归属铺设（CO-95 effect 授权）",
        "band_x": [50.0, 88.17], "band_y": [43.44, 65.1], "corridor_x": [mcu_e0, p3v3_w0],
        "allocation": [
            {"net": "MCU_VDD", "zone": "MCU_VDD_WEST", "x_range": [mcu_e0, mcu_e1],
             "basis": f"覆盖声明目标 R29/R31-R34 东缘 {mcu_tgt_e} + POWER clearance {CLR}"},
            {"net": "P3V3", "zone": "P3V3_EAST", "x_range": [new_p3v3_w, p3v3_w0],
             "basis": f"覆盖 U6 P3V3 球/孔西缘 {min(p3):.3f} − {CLR}；余下走廊 x∈({mcu_e1},{p3v3_w1}) 无声明目标 ⇒ 归东侧既有权域；west edge = {mcu_e1}+{CLR}"}],
        "interface_mid_x": round((mcu_e1 + new_p3v3_w) / 2, 6),
        "domain_set_unchanged": ["P3V3", "P3V3_AUX", "MCU_VDD"],
        "level_basis": "《宪法》ch.2：L2=走廊分配/PDN 架构，L2 裁判标准含『参考平面』；冻结 L1=粗分区+域集合，"
                       "本件域集合不变 ⇒ L2（先例 CO-74：层数/平面数/电源域集合/信号层数全不变 ⇒ L2）",
        "l3_derivation": "band 内多边形 = L3 施工确定性派生（贯通孔反焊盘净距 + 异网净距 0.2），非求解器；本件只定网归属与边界约束",
        "refs": ["CO-95", "CO-115", "CO-116", "CO-117"]}
    # 3) polygon 边界
    p3v3["polygon"] = rect(33.3, 78.7, new_p3v3_w, 142.7)
    mcu["polygon"] = rect(33.3, 78.7, 23.3, mcu_e1)
    # 4) reachability 状态
    prs = zd["plane_reachability_status"]
    p3_entry = [u for u in prs["unresolved"] if u["net"] == "P3V3"]
    prs["unresolved"] = [u for u in prs["unresolved"] if u["net"] != "P3V3"]
    prs["resolved_by_co117"] = [{"net": "P3V3", "pads": p3_entry[0]["pads"] if p3_entry else [],
                                 "how": f"P3V3_EAST 西界 {p3v3_w0}→{new_p3v3_w} 覆盖 U6 P3V3 球/孔（band 归属 = CO-117）"}]
    prs["na_scope_v1"]["in5_corridor_reference"] = {
        "ref": "CO-117", "supersedes": "CO-111",
        "note": "走廊 In4 声明铜已由 CO-117 band 归属闭合（模型内 In5←In4 参考恢复）；实体铜 = L3 施工派生；"
                "In5 阻抗终判仍 = SI9000 + 板厂阻抗券"}
    spec["spec_version"] = "1.1.spec-rev-15"
    after = dict(flat(spec))
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    bad = sorted(c for c in changed if not any(c.startswith(p) for p in ALLOWED))
    assert not bad, f"unexpected changed paths: {bad}"
    T1, U1, nets1, res_pts = in5_exposure(spec, draw)
    resid_x = [round(m[0], 4) for m in res_pts]
    sliver = [mcu_e1, new_p3v3_w]
    teeth = {
        "exposure_positive_control_rev14": U0 > 1000.0,
        "exposure_reduced_ge_99pct": U1 <= 0.01 * U0,
        "residual_confined_to_clearance_sliver": all(sliver[0] - 1e-6 <= x <= sliver[1] + 1e-6 for x in resid_x),
        "free_gap_nonempty": gap[1] > gap[0] > 0,
        "inter_net_clearance_exact": abs((new_p3v3_w - mcu_e1) - CLR) < 1e-9,
    }
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    rec = {
        "artifact": "m13_v57_co117_band_allocation_rev15", "schema": 1, "revision": "CO-117.1",
        "nature": "L2 自裁施加：band In4 铺铜归属分配 + SPEC rev-15（更正 rev-14 错误键 + 闭合 In5 走廊参考缺失）",
        "src": Path(a.src).name, "src_sha16": s16(Path(a.src)), "out": Path(a.out).name, "out_sha16": s16(Path(a.out)),
        "level": {"ruling": "L2", "basis": zd["in4_band_copper_allocation_v1"]["level_basis"],
                  "supersedes": "CO-115/CO-116 的『band 归属 = L1』归口（判定过高）"},
        "allocation": {"forced_interval": {"MCU_VDD_east_min": mcu_e1, "P3V3_west_max": p3v3_w1},
                       "free_gap": gap, "chosen": "free_gap → P3V3（东侧既有权域）",
                       "MCU_VDD_WEST_east_edge": {"before": mcu_e0, "after": mcu_e1},
                       "P3V3_EAST_west_edge": {"before": p3v3_w0, "after": new_p3v3_w},
                       "interface_mid_x": zd["in4_band_copper_allocation_v1"]["interface_mid_x"]},
        "spec_changes": {"changed_paths": sorted(changed), "whitelist_ok": not bad,
                         "new_keys": ["pd.zone_defs.in4_band_copper_allocation_v1",
                                      "pd.zone_defs.retired_in4_corridor_void_by_design_v1",
                                      "pd.zone_defs.plane_reachability_status.resolved_by_co117"],
                         "polygons_changed": ["power_zones[0].polygon(P3V3_EAST)", "power_zones[1].polygon(MCU_VDD_WEST)"],
                         "thresholds_unchanged": True, "vias_unchanged": True, "board_untouched": True},
        "in5_reference": {"rev14_total_mm": round(T0, 3), "rev14_unref_mm": round(U0, 3),
                          "rev14_unref_pct": round(U0 / T0, 4), "rev15_total_mm": round(T1, 3),
                          "rev15_unref_mm": round(U1, 3), "rev15_unref_pct": round(U1 / T1, 4),
                          "note": "CO-111 的 In5 单参考暴露在**声明模型内**归零；实体 In4 铜 = L3 施工派生"},
        "teeth": teeth,
        "findings_addressed": {
            "F-1": "rev-14 错误键 in4_corridor_void_by_design_v1 已退役留存，取代键 = in4_band_copper_allocation_v1",
            "F-3": "CO-113 记录 new_keys 少声明 bcu_bridge_bands_source：本件记录显式补登（历史 CO-113 记录按红线不改）",
            "F-4": "CO-111 措辞『无逐线阻抗核验字段』应收敛为『区域条件阻抗未验』：本件记录显式补正（历史 CO-111 记录按红线不改）",
            "F-2": "co87 矩阵『参考平面』行证据文本陈旧（下同→由 CO-117b 随重基线重跑 co87 一并更正）",
            "F-6": "4 记录 5 处 inputs.*_record provenance pin：由重基线重跑相应闸记录刷新（见 co117 记录 spec_chain 段）"},
        "redline": "不改板/阈值/冻结源；历史工件不改；零坐标搜索；L3 几何不代填",
        "verdict": "L2_ALLOCATED_REV15_WRITTEN" if (not bad and teeth["teeth_ok"]) else "FAIL",
    }
    rec["in5_reference"]["rev15_residual_midpoints_x"] = sorted(set(resid_x))
    rec["in5_reference"]["residual_width_mm"] = round(sliver[1] - sliver[0], 6)
    # F-6：历史记录 inter-record provenance pin 显式标注（红线『历史工件不改』⇒ 不回写）
    hist = []
    for rf in ("m13_v57_co109_in4_void_l2_ruling.json", "m13_v57_co110_l2_coverage_closure.json",
               "m13_v57_co112_bcu_bridge_declaration.json", "m13_v57_co111_in5_pcie_corridor_exposure.json"):
        try:
            d = json.loads((STEP2 / rf).read_text())
        except Exception:
            continue
        txt = json.dumps(d)
        import re as _re
        for m in _re.finditer(r'"([a-z0-9_]*(?:record|_record))"\s*:\s*"([0-9a-f]{16})"', txt):
            if m.group(1) in ("record",):
                continue
            hist.append({"file": rf, "key": m.group(1), "cited": m.group(2)})
    rec["historical_pins"] = {
        "note": "F-6：下列 inter-record provenance pin 指向已被取代的上游记录版本（被引值均为 git 内真实历史版本，非伪造）；"
                "记录本体已由 CO-115/CO-117 取代 ⇒ 按红线『历史工件不改』显式标注为**历史 pin**，不回写、不重跑。"
                "live 链 pin（co98←co95 / co105←co98）已于本次重基线刷新。",
        "pins": hist}
    rec["l2_si_note"] = ("残余 0.2mm 缝 = **POWER 异网净距（强制，不可消除）**的参考平面分割；In5 走线跨越该分割 "
                         "属**新增 L2 登记 SI 项**，终判 = SI9000 + 板厂阻抗券（不得以假设值代填）")
    if not (not bad and teeth["teeth_ok"]):
        print("CO-117 ABORT: whitelist_bad=%s teeth=%s" % (bad, teeth)); return 1
    Path(a.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")
    Path(REC).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"CO-117 rev15 sha16={rec['out_sha16']} | In5 unref {round(100*U0/T0,2)}% -> {round(100*U1/T1,4)}% "
          f"({round(U0,1)}→{round(U1,1)}mm) | MCU east {mcu_e0}→{mcu_e1} P3V3 west {p3v3_w0}→{new_p3v3_w} | teeth={teeth['teeth_ok']}")
    return 0 if rec["verdict"].startswith("L2_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
