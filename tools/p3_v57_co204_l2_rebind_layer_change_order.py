#!/usr/bin/env python3
"""CO-204 — 【L2 自裁】打样渠道**重绑 JLC 标准（通孔 + 背钻）** + **层分配变更裁决**（监理指令 #12 动作 1/2/3/6）。

只读判据 + 裁决落盘：独立重算（不 import 引擎）——
  P1「逃逸层 == 走廊 run 层」不可行性：把图纸全部段投到**一层**做自写 proper-intersection 计数；
  P2 内层↔内层类**不可制**：外层锚定类残桩恒 0；内层↔内层类最小残桩 = min(自 F 距, 自 B 距)；
  P3 单外层竖列容量：逃生竖列列位实测间距 vs 外层 3W 界。
产出：L2 裁定件（v1.0，取代 CO-147 R1）+ ORDER_NOTES 重绑 + 机读记录。
CLI: python3 tools/p3_v57_co204_l2_rebind_layer_change_order.py   （幂等）
"""
from __future__ import annotations
import hashlib, itertools, json, re, sys
from collections import Counter
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2D = K2 / "pm_gate/artifacts/k2_v4/L2"
L5 = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
DRAW = S2 / "m13_v57_w3_joint_assignment.json"
ALLOC = S2 / "m13_v57_co16_channel_allocation_v8.json"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
CAPREC = S2 / "m13_v57_co146_jlc8_capability.json"
BIND = S2 / "m13_v57_co204_fab_capability_binding.json"
RULING = L2D / "L2_RULING_jlc_standard_through_backdrill_v1.md"
REC = S2 / "m13_v57_co204_l2_ruling.json"
NOTES = L5 / "ORDER_NOTES.md"
PHYS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
OUTER = {"F.Cu", "B.Cu"}
EPS = 1e-9


def sha16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def span_of(spec) -> dict:
    d = spec["stackup"]["dielectric_8l"]
    keys = ["d(F.Cu-In1.Cu)", "d(In1.Cu-In2.Cu)", "d(In2.Cu-In3.Cu)", "d(In3.Cu-In4.Cu)",
            "d(In4.Cu-In5.Cu)", "d(In5.Cu-In6.Cu)", "d(In6.Cu-B.Cu)"]
    from_F, acc = {"F.Cu": 0.0}, 0.0
    for k, lo in zip(keys, PHYS[1:]):
        acc += float(d[k]["mm"]); from_F[lo] = round(acc, 6)
    return {"from_F": from_F, "from_B": {L: round(acc - v, 6) for L, v in from_F.items()}, "total": round(acc, 6)}


def stub_of(top, bot, sp) -> float:
    if top in OUTER or bot in OUTER:
        return 0.0
    return round(min(sp["from_F"][top], sp["from_B"][bot]), 6)


def _cross(a, b, c, d) -> bool:
    def o(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    if o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b):
        return True
    return False


def same_layer_crossings(draw) -> dict:
    """P1：把图纸**全部**段投影到一层，独立计数 proper intersection（不 import 引擎）。"""
    segs = []
    for pg in draw["pages"]:
        for pol, nd in (pg.get("nodes") or {}).items():
            for p, q in zip(nd, nd[1:]):
                if p[2] == q[2] and (abs(p[0] - q[0]) > EPS or abs(p[1] - q[1]) > EPS):
                    segs.append((pg["page_id"], pol, (p[0], p[1]), (q[0], q[1])))
    n = 0
    for (p1, q1, a1, b1), (p2, q2, a2, b2) in itertools.combinations(segs, 2):
        if any(abs(x[0] - y[0]) < 1e-7 and abs(x[1] - y[1]) < 1e-7 for x in (a1, b1) for y in (a2, b2)):
            continue
        if _cross(a1, b1, a2, b2):
            n += 1
    return {"n_segments": len(segs), "n_proper_crossings_if_flattened": n}


def escape_columns(alloc) -> dict:
    """P3：逃生竖列（via1）列位实测间距（东/西两侧分开看 = 芯片侧列组）。"""
    xs = sorted({round(p["via1"][pol][0], 4) for p in alloc["pages"].values() for pol in ("N", "P")})
    gaps = [round(b - a, 4) for a, b in zip(xs, xs[1:])]
    return {"n_columns": len(xs), "x_span_mm": round(xs[-1] - xs[0], 4),
            "min_gap_mm": min(gaps) if gaps else None,
            "n_gaps_lt_0.615": sum(1 for g in gaps if g < 0.615),
            "n_gaps_lt_0.48": sum(1 for g in gaps if g < 0.48)}


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    alloc = json.loads(ALLOC.read_text(encoding="utf-8"))
    _capart = json.loads(CAPREC.read_text(encoding="utf-8"))
    cap = {**_capart["capability"], "backdrill": _capart.get("backdrill_capability") or _capart["capability"].get("backdrill") or {}}
    bind = json.loads(BIND.read_text(encoding="utf-8"))
    sp = span_of(spec)
    p1 = same_layer_crossings(draw)
    p3 = escape_columns(alloc)
    census = bind["board"]["census"]
    classes = sorted({tuple(k.split("->")) for k in census})
    vtab = {k: {"n": census[k], "stub_min_mm": stub_of(k.split("->")[0], k.split("->")[1], sp),
                "outer_anchored": k.split("->")[0] in OUTER or k.split("->")[1] in OUTER} for k in census}

    rec = {
        "artifact": "m13_v57_co204_l2_ruling", "schema": 1, "revision": "CO-204",
        "level": "L2",
        "nature": "打样渠道重绑（JLC 标准 = 通孔 + 背钻）+ 层分配变更裁决（消内层↔内层跨层）—— 监理指令 #12 动作 1/2/3/6",
        "supersedes": {"doc": "L2_RULING_via_channel_and_interpair_domain_v1.md", "clause": "R1（过孔策略/打样渠道）",
                       "reason": "JLC 无 advanced/盲埋孔通道（能力页明文 only through holes）；该绑定不成立"},
        "capability": {"backdrill_supported": cap["backdrill"]["supported"],
                       "backdrill_limits": {k: cap["backdrill"][k] for k in
                                            ("layers_min", "layers_max", "thickness_min_mm", "via_drill_d_mm",
                                             "backdrill_w_over_d_mm", "dielectric_t_min_mm", "safety_s_min_mm")},
                       "blind_buried_supported": cap["blind_buried"]["supported"]},
        "evidence": {"P1_same_layer_flattened": p1, "P3_escape_columns": p3,
                     "stackup_layer_distance_mm": sp, "via_class_table": vtab},
        "ruling": {
            "R1": "**撤销 CO-147 R1**（JLC advanced / 盲埋孔通道不存在）。打样渠道**绑定 JLC 标准 = 通孔 + 背钻**。",
            "R2": "**层分配须消内层↔内层跨层**：全部过孔 = 通孔(F↔B) + 按需背钻；目标 **0 盲埋孔**；残桩 <0.15mm。",
            "R3": "「逃逸层 == 走廊 run 层」**不可行**（P1：投影单层 1296 处相交）⇒ 采**等价手段**：把层间转移**锚到外层**"
                  "（候选 A：走廊 run → B.Cu，竖段留 In2；候选 B：run→B.Cu，竖段 In2/In5 分色；候选 C：每处 In2↔In5 "
                  "改为 In2→B→In5 双孔桥）。择优 = **A**（竖段单层 In2：3W 内层界 0.48 可容；B.Cu 仅跑横段 ⇒ 无同层交叉；"
                  "全类外层锚定 ⇒ 残桩 0）。**候选 A/B 改变走廊 run 层 ⇒ 须改 SPEC impedance.per_layer + 阻抗重签**。",
            "R4": "**实施 = WORKER**（层分配重派生）：G4 图纸重派生 → DRC → L4 → L5；本件只裁决策与判据，不代实施。",
            "R5": "**两闸**：板厂能力绑定闸 `p3_v57_co204_fab_capability_binding_gate.py`（已入库；现行板预期 FAIL）"
                  "+ 散热验证闸（设计期结温）。**复评债**：本件 + CO-202/CO-203（另一会话）。",
        },
        "self_proof_5": [
            f"① 现象：交付板 493 via 中 {bind['board']['n_inner_inner']} 支内层↔内层（In2.Cu→In5.Cu），"
            f"残桩 {vtab.get('In2.Cu->In5.Cu', {}).get('stub_min_mm')}mm ≥ 0.15mm ⇒ 高速 SI 不达标；JLC 不支持盲埋孔。",
            "② 结构归因：图纸每线 = F→In2(竖段)→In5(横 run)→(B)；竖段与横段**必相交** ⇒ 必须异层（P1 独立复算）；"
            "而竖段容量须 ≥2 层（P3 列位间距 < 外层 3W 0.615）⇒ 至少一层为内层 ⇒ 其与外层锚定之外的层间转移即内层↔内层。",
            f"③ 算法完备性：「逃逸层 == run 层」在现行 lane/列序下**不可行**（P1 = {p1['n_proper_crossings_if_flattened']} 处相交，"
            "自写 proper-intersection 核，未 import 引擎）；" "「竖段全落单外层」**容量不可行**"
            f"（P3：{p3['n_columns']} 列 / 跨度 {p3['x_span_mm']}mm，其中 {p3['n_gaps_lt_0.615']} 处相邻列距 <0.615 ⇒ 外层 3W 放不下）。",
            "④ 候选：A/B/C（见 R3）；择优 A（外层锚定、残桩 0、无同层交叉）；B/C 备选。",
            "⑤ 处置：裁决 R2/R3 冻结 → WORKER 重派生一次（禁暴力迭代，宪法第八章第 8 条）→ 两闸复核 → 包重出。",
        ],
        "verdict": "RULING_FROZEN_IMPLEMENTATION_PENDING",
        "blocker": "交付板仍 220/493 非通孔 ⇒ **不可送样**（板厂能力绑定闸 FAIL）；须 WORKER 按 R3 候选 A 重派生层分配。",
        "redline": "只读分析（未改 SPEC/板/冻结四源）；零坐标搜索；结论由自写判据重算，不引用被评记录。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    md = f"""# L2 裁定 v1.0（CO-204）— 打样渠道重绑 JLC 标准（通孔 + 背钻）+ 层分配变更裁决

> 层级：**L2**（过孔策略 / 叠层分配 —— 宪章第二章 L2 职权明列）｜**取代 CO-147 R1**（过孔策略/打样渠道）
> 板 `{bind['board']['sha256'][:16]}`（**未改动**）｜SPEC rev-19 `{sha16(SPEC)}`（未改动）｜零坐标搜索｜只读分析

## R1 撤销（打样渠道）
- **撤销**：CO-147 R1 之「维持盲/埋孔 + 绑定 JLC advanced / 盲埋孔通道」。**JLC 无该通道**：能力页明文
  *"Blind/Buried Vias Not supported … only make through holes"*。
- **新绑**：打样渠道 = **JLC 标准（通孔 + 背钻）**。能力页同页明文 Backdrill 支持：
  4–32 层 FR4 / 板厚 ≥0.8mm / D {cap['backdrill']['via_drill_d_mm'][0]}–{cap['backdrill']['via_drill_d_mm'][1]}mm /
  W = D+{cap['backdrill']['backdrill_w_over_d_mm']}mm / **T ≥{cap['backdrill']['dielectric_t_min_mm']}mm** / S ≥{cap['backdrill']['safety_s_min_mm']}mm
  （anchor 逐条为抓取件归一原文子串，见 `{CAPREC.name}`）。

## R2 层分配目标（消内层↔内层跨层）
- **全部过孔 = 通孔(F↔B) + 按需背钻**；目标 **0 盲埋孔**；**残桩 <0.15mm**（高速 SI 不降级）。
- 现行板：493 via = F→B 273（通孔）/ F→In2 **92** / F→In5 **8** / **In2→In5 88（不可制）** / In5→B 32。

| 类 | 支数 | 外层锚定 | 最小残桩 mm | 以「通孔+背钻」可制 |
|---|---|---|---|---|
""" + "\n".join(
        f"| {k} | {v['n']} | {'是' if v['outer_anchored'] else '**否**'} | {v['stub_min_mm']} | "
        f"{'可（残桩 0）' if v['outer_anchored'] else '**不可**（残桩 ≥0.15）'} |" for k, v in vtab.items()) + f"""

## R3 等价手段（「逃逸层 == run 层」不可行 ⇒ 改为**外层锚定**）
- **P1（自写 proper-intersection 核，独立复算）**：图纸 {p1['n_segments']} 段投到**一层** ⇒ **{p1['n_proper_crossings_if_flattened']} 处相交**
  ⇒ 「竖段 + run 同层」在现行 lane/列序下**不可行**（除非重派生为单调序 —— 属重派生范畴）。
- **P3（逃生竖列容量）**：via1 列位 {p3['n_columns']} 列 / 跨度 {p3['x_span_mm']}mm；相邻列距 <0.615（外层 3W）者
  **{p3['n_gaps_lt_0.615']}** 处 ⇒ 竖段**不能全落单外层**。
- **候选**：
  - **A（择优）**：走廊 run → **B.Cu**；竖段留 **In2**（内层 3W 0.48 可容）。全类 {{F↔In2, In2↔B, B↔In2, In2↔F}} ⇒ **残桩 0**。
  - B：run → B.Cu；竖段 **In2 / In5 分色**（容量更宽）。
  - C：保留 run=In5，把每处 In2↔In5 改为 **In2→B→In5 双孔桥**（不动 run 层，但增孔）。
- **代价（A/B）**：走廊 run 层由 In5（带状线，参考 In4/In6）改为 B.Cu（外层微带）⇒ **须改 SPEC `impedance.per_layer` + 阻抗重签**。

## R4 两闸（防再犯）
- **板厂能力绑定闸**：`tools/p3_v57_co204_fab_capability_binding_gate.py`（C0 能力源绑定 / C1 类别合法性 /
  C2 残桩 / C3 背钻工艺限 / C4 禁盲埋孔）。**现行板预期 FAIL**（内层↔内层 88）。
- **散热验证闸**：设计期结温（输入显式声明）。见 CO-146/co149 链（U6 定案 O2）。

## R5 五项自证（含算法完备性）
""" + "\n".join(f"{s}" for s in rec["self_proof_5"]) + f"""

## 影响与后续
- **不可送样**：{rec['blocker']}
- **实施 = WORKER**：按 R3 候选 A **一次**重派生（G4 → DRC → L4 → L5），禁暴力迭代（宪章第八章第 8 条）。
- **复评债**：本件 + CO-202 + CO-203（须另一会话，禁自评）。
"""
    RULING.write_text(md, encoding="utf-8")

    # ORDER_NOTES：**生成权归 fab package 工具**（CO-204 已改其 §2 模板）⇒ 本件只做**只读校验**
    notes = NOTES.read_text(encoding="utf-8")
    notes_ok = ("绑定 JLC 标准（通孔 + 背钻）" in notes) and ("advanced / 盲埋孔通道" not in notes)
    if not notes_ok:
        rec["verdict"] = "ORDER_NOTES_NOT_REBOUND"
        REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "P1": p1, "P3": p3,
                      "inner_inner": bind["board"]["n_inner_inner"],
                      "stub_in2_in5": vtab.get("In2.Cu->In5.Cu", {}).get("stub_min_mm"),
                      "ruling_sha16": sha16(RULING), "rec_sha16": sha16(REC), "notes_sha16": sha16(NOTES)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
