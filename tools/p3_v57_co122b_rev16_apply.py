#!/usr/bin/env python3
"""CO-122b：【L2 自裁 · 施加】SPEC rev-15 → **rev-16**：西区 P3V3_AUX In4 承载落地（CO-121 裁定的施加步骤）。

变更（白名单，唯一允许路径）：
  1. `.spec_version` → 1.1.spec-rev-16
  2. + `.pd.zone_defs.in4_west_aux_allocation_v1`（CO-121 家族 chosen 6 矩形 + 判据/义务/level_basis）
  3. `.pd.zone_defs.power_zones` **追加** `{net:P3V3_AUX, zone:P3V3_AUX_WEST, polygon:<6 矩形并集单环>}`
     （**追加**不改 [0]/[1] 索引；co95 只读 singular `polygon` ⇒ 3 个 entry 由 needs_region_ruling → covered_explicit）
  4. `.pd.zone_defs.plane_reachability_status.unresolved` 删 P3V3_AUX 项（余 12V_IN）
  5. + `.pd.zone_defs.plane_reachability_status.resolved_by_co121`
只读除上述；不改板/阈值/冻结源/其它键。环 = 由 6 矩形闭式并集追踪（非手工坐标）。
CLI: python3 tools/p3_v57_co122b_rev16_apply.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-15.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-16.json"
CO121 = STEP2 / "m13_v57_co121_west_aux_allocation_ruling.json"
REC = STEP2 / "m13_v57_co122b_west_aux_rev16.json"
ZONE_NAME = "P3V3_AUX_WEST"


def s16(p):
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


def union_ring(rects):
    """轴对齐矩形并集的**外环**（闭式追踪；无洞断言）。"""
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    ys = sorted({r[1] for r in rects} | {r[3] for r in rects})
    cov = {}
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            cov[(i, j)] = any(r[0] < cx < r[2] and r[1] < cy < r[3] for r in rects)
    cnt = {}
    for (i, j), ok in cov.items():
        if not ok:
            continue
        a, b = (xs[i], ys[j]), (xs[i + 1], ys[j])
        c, d = (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])
        for p, q in ((a, b), (b, c), (c, d), (d, a)):
            e = (p, q) if p < q else (q, p)
            cnt[e] = cnt.get(e, 0) + 1
    bnd = [e for e, n in cnt.items() if n == 1]
    adj = {}
    for p, q in bnd:
        adj.setdefault(p, []).append(q)
        adj.setdefault(q, []).append(p)
    bad = [p for p, v in adj.items() if len(v) != 2]
    if bad:
        raise SystemExit(f"环追踪失败：非流形顶点 {bad[:4]}")
    start = min(adj)
    ring, prev, cur = [start], None, start
    while True:
        nxt = [p for p in adj[cur] if p != prev]
        if not nxt:
            raise SystemExit("环追踪失败：断链")
        nxt = nxt[0]
        prev, cur = cur, nxt
        if cur == start:
            break
        ring.append(cur)
    # 去共线
    out = []
    n = len(ring)
    for i, p in enumerate(ring):
        a, b = ring[i - 1], ring[(i + 1) % n]
        if (a[0] == p[0] == b[0]) or (a[1] == p[1] == b[1]):
            continue
        out.append(p)
    area2 = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1]
               for i in range(len(out)))
    if area2 < 0:
        out = out[::-1]
    return out


def main() -> int:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    co121 = json.loads(CO121.read_text(encoding="utf-8"))
    if co121["verdict"] != "FEASIBLE_WITHIN_DECLARED_FAMILY":
        raise SystemExit("CO-121 非 FEASIBLE，拒绝施加")
    rects = [[float(v) for v in r] for r in co121["family"][co121["chosen"]]]
    ring = [[float(x), float(y)] for x, y in union_ring([tuple(r) for r in rects])]
    out = json.loads(json.dumps(src))          # deep copy
    zd = out["pd"]["zone_defs"]
    out["spec_version"] = "1.1.spec-rev-16"
    zd["in4_west_aux_allocation_v1"] = {
        "note": "CO-121/122b【L2 自裁 · 施加】西区 P3V3_AUX In4 承载：本网岛/带/柱/臂（CO-121 声明式家族 chosen）",
        "level_basis": ("《宪法》ch.2：L2=PDN 架构/走廊分配，L2 裁判标准含『参考平面』；冻结 L1=域集合+粗分区，"
                        "本件二者不变 ⇒ L2（先例 CO-74；判据同 CO-117 level_basis）"),
        "domain_set_unchanged": ["P3V3", "P3V3_AUX", "MCU_VDD"],
        "zone": ZONE_NAME, "net": "P3V3_AUX", "layer": "In4.Cu",
        "targets": {k: list(map(float, v)) for k, v in co121["targets"].items()},
        "declared_rects": rects,
        "clearance_mm": 0.375,
        "clearance_basis": "冻结 drc_rules.json：POWER required 0.2 + via_od/2 0.175（孔规则 0.35 更松）",
        "merge_min_mm": 0.3,
        "design_margin_mm": 0.1,
        "constraints": ["MCU_VDD 连续性保持（岛/带不得贯通西区全高或全宽）",
                        "P3V3_AUX 3 target 互连（搭接深度 ≥ 0.3，非贴合）",
                        "异网 via 净距 ≥ 0.375"],
        "l3_derivation": "实体多边形 = 施工确定性派生（贯通孔反焊盘净距 + 异网净距 0.2 moat 从 MCU_VDD_WEST 挖出）；本件只定网归属与边界约束",
        "provenance": {"co121_record": "m13_v57_co121_west_aux_allocation_ruling.json",
                       "co121_record_sha16": s16(CO121), "chosen": co121["chosen"]},
    }
    zd["power_zones"].append({
        "net": "P3V3_AUX", "zone": ZONE_NAME, "layer": "In4.Cu", "polygon": ring, "vias": [],
        "basis": ("CO-122b：西区 P3V3_AUX 承载（CO-121 L2 裁定 chosen 家族；环 = 6 声明矩形闭式并集，"
                  "非手工坐标）"),
        "declared_rects": rects,
        "refs": ["CO-95", "CO-118", "CO-121", "CO-122", "CO-122b"],
    })
    prs = zd["plane_reachability_status"]
    prs["unresolved"] = [u for u in prs["unresolved"] if u["net"] != "P3V3_AUX"]
    prs["resolved_by_co121"] = [{
        "net": "P3V3_AUX", "pads": ["C90.1", "R1.2", "U1.15"],
        "how": "西区 In4 承载 = P3V3_AUX_WEST（CO-121 家族 chosen；CO-122b 施加）；净距 0.375 / 搭接 ≥0.3 / MCU_VDD 连续",
    }]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 白名单断言 + 不变量
    a, b = dict(flat(src)), dict(flat(out))
    changed = sorted({k for k in set(a) | set(b)
                      if k not in (".spec_version",) and a.get(k) != b.get(k)})
    allowed_pref = (".pd.zone_defs.in4_west_aux_allocation_v1",
                    ".pd.zone_defs.plane_reachability_status.unresolved",
                    ".pd.zone_defs.plane_reachability_status.resolved_by_co121")
    unexpected = [k for k in changed
                  if not k.startswith(allowed_pref)
                  and not (k.startswith(".pd.zone_defs.power_zones[5]") or k == ".pd.zone_defs.power_zones")]
    rec = {
        "artifact": "m13_v57_co122b_west_aux_rev16", "schema": 1, "revision": "CO-122b.1",
        "nature": "L2 自裁 · 施加：西区 P3V3_AUX In4 承载 → SPEC rev-16",
        "src": str(SRC.name), "src_sha16": s16(SRC), "out": str(OUT.name), "out_sha16": s16(OUT),
        "co121_record_sha16": s16(CO121), "chosen": co121["chosen"],
        "ring": ring, "ring_n": len(ring), "declared_rects": rects,
        "zone_appended": ZONE_NAME, "n_power_zones": len(out["pd"]["zone_defs"]["power_zones"]),
        "changed_paths": changed, "unexpected_changed_paths": unexpected,
        "whitelist_ok": not unexpected,
        "unresolved_after": [u["net"] for u in prs["unresolved"]],
        "board_untouched": True,
        "redline": "不改板/阈值/冻结源；历史工件不改；零坐标搜索；几何 = L3 派生",
        "board_sha16_l4": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"out_sha16": rec["out_sha16"], "ring_n": len(ring),
                      "n_zones": rec["n_power_zones"], "whitelist_ok": rec["whitelist_ok"],
                      "unexpected": unexpected[:5], "unresolved_after": rec["unresolved_after"],
                      "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
    return 0 if rec["whitelist_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
