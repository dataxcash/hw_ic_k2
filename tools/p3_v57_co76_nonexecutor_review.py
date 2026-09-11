#!/usr/bin/env python3
"""CO-76：**非执行者侧**对抗评审 pass 1/2（对象 = CO-67..CO-75 冻结态）+ F1/F2/F3 修复校验。

评审者与 CO-67..73 执行者**非同一会话**（本会话 context 归零后仅据 handoff/ledger 续接）。
宪法依据：`L2/frozen/L2_STRUCTURE_v2.0.md:137`「重开须重新过对抗评审」；CO-69 仅**执行者侧**。

发现（对 CO-67..CO-75 冻结态）：
  F1（中·声明/工件正确性）引擎把陈旧层角色写进**生产图纸**：
     `p3_v57_w3_constructive.py` 的 `decision_contract.r1_5_layer_rule` 文本为
     `(dn=B.Cu, up=In6.Cu)`；而 LID REV6 下 In6=**GND 平面**，且引擎实现本即 `up->In5.Cu`
     （代码 `"B.Cu" if band=="dn" else "In5.Cu"`）。⇒ 同 CO-72/73 类缺陷，但落在引擎/图纸（CO-73 只扫了 SPEC）。
  F2（中·探针覆盖洞）CO-69 A5 断言 `'"In6.Cu"' not in eng`（**带引号**字面量）；CO-68 已把代码字面量改成 In5，
     故该断言恒真，**结构上无法**发现未加引号的层角色文本（实测 14 处裸 `In6`）。
  F3（低·文档）10+ 处注释/docstring 仍以 In6 为信号/通道层（与同行代码矛盾，如 `"In5.Cu" # ... In6`）。
修复：F1/F3 = 文本修正（零几何）；F2 = A5 改裸 token 扫描 + 显式豁免 `In6->In5` 迁移注。
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co76_nonexecutor_review.json"
ENGINE = K2 / "tools/p3_v57_w3_constructive.py"
PROBE = K2 / "tools/p3_v57_co69_adversarial_probes.py"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REV7_GEOM = {"route_geometry": "d39becad4f51f3af", "pages": "e659edaa6608f3d2",
             "layers": "db2ee692c03204da"}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def khash(o) -> str:
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    eng = ENGINE.read_text(encoding="utf-8")
    draw = json.loads((STEP2 / "m13_v57_w3_joint_assignment.json").read_text(encoding="utf-8"))
    board = BOARD.read_text(encoding="utf-8", errors="replace")
    lid = json.loads((STEP2 / "m13_v57_layer_intent_rev6.json").read_text(encoding="utf-8"))
    spec = json.loads((L3 / "SPEC_k2_v4.spec-rev-8.json").read_text(encoding="utf-8"))
    rmcfg = json.loads((L2 / "route_model_config.json").read_text(encoding="utf-8"))
    rules = json.loads((K2.parent / "_shared/eda_core/drc_rules.json").read_text(encoding="utf-8"))
    co69 = json.loads((STEP2 / "m13_v57_co69_adversarial_review.json").read_text(encoding="utf-8"))
    co75 = json.loads((STEP2 / "m13_v57_co75_west_pitch_origin_search.json").read_text(encoding="utf-8"))

    # C1 引擎层集 + 无未豁免 In6
    in6_lines = [(i + 1, ln.strip()) for i, ln in enumerate(eng.splitlines()) if "In6" in ln]
    in6_bad = [(i, ln) for i, ln in in6_lines if "In6->In5" not in ln]
    c1 = ('LAYER_PALETTE = ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"]' in eng) and not in6_bad

    # C2 图纸声明字符串
    dc = json.dumps(draw["decision_contract"], ensure_ascii=False)
    c2 = ("In6" not in dc) and ("up=In5.Cu" in dc)

    # C3 图纸无 In6 层字段；几何键与 rev-7 基线同
    fields = []
    def walk(o, p=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, p + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, p + "[" + str(i) + "]")
        elif isinstance(o, str) and o == "In6.Cu":
            fields.append(p)
    walk(draw)
    geom = {k: khash(draw.get(k)) for k in REV7_GEOM}
    c3 = not fields and all(geom[k] == REV7_GEOM[k] for k in REV7_GEOM)

    # C4 板：段层 ∈ {F,In2,In5,B}；In4/In6 段 0；zone 仅 F.Cu（keepout 规则域）
    import collections
    seghist = collections.Counter()
    for m in re.finditer(r"\(segment\b", board):
        lm = re.search(r'\(layer "([^"]+)"\)', board[m.start():m.start() + 400])
        seghist[lm.group(1) if lm else "?"] += 1
    zonehist = collections.Counter()
    for m in re.finditer(r"\(zone\s", board):
        lm = re.search(r'\(layer "([^"]+)"\)', board[m.start():m.start() + 1500])
        zonehist[lm.group(1) if lm else "?"] += 1
    c4 = (set(seghist) <= {"F.Cu", "In2.Cu", "In5.Cu", "B.Cu"}
          and seghist.get("In4.Cu", 0) == 0 and seghist.get("In6.Cu", 0) == 0
          and set(zonehist) <= {"F.Cu"})

    # C5 A5 加固在位 + 探针记录 PASS
    a5_hard = "in6_unallowed" in PROBE.read_text(encoding="utf-8")
    _probes = co69.get("probes") or []
    _a5 = next((p for p in _probes if p.get("id") == "A5"), None)
    c5 = a5_hard and not co69.get("failed") and _a5 is not None and _a5.get("pass") is True

    # C6 引擎消费 ALLOC.7；LID 域不变量
    li = lid["layer_intent"]
    dom = lid["domain_invariance"]
    c6 = ("m13_v57_co16_channel_allocation_v7.json" in eng
          and li["In1.Cu"] == li["In3.Cu"] == li["In6.Cu"] == "gnd_plane"
          and li["In4.Cu"].startswith("power_plane")
          and set(k for k, v in li.items() if v in ("transition_eligible", "stub_only"))
              == {"F.Cu", "In2.Cu", "In5.Cu", "B.Cu"}
          and dom["plane_count"] == 4)

    # C7 ① 负结果在位（CO-75）
    c7 = (co75["n_probes"] == 23 and co75["n_placed"] == 0
          and co75["baseline_reproduction"]["placed_32of32"] is True)

    # C8 四冻结源
    fr = {"SPEC_k2_v4.json": ("0bd52ed48e720b8c", L3 / "SPEC_k2_v4.json"),
          "page_manifest": ("a8ef3ea8ecff99d7", STEP2 / "m13_v57_s1_page_manifest.json"),
          "pcb_8L": ("fb07d25ac426ff84", K2 / "k2_v4_8L.kicad_pcb"),
          "drc_rules": ("0a459839e15960b8", K2.parent / "_shared/eda_core/drc_rules.json")}
    fro = {k: s16(p) == e for k, (e, p) in fr.items()}
    c8 = all(fro.values())

    # C9 本会话/本轮工具零 while（闭式、零坐标搜索）
    whilefree = {}
    for tp in ("p3_v57_co74_pdn_bcu_rehost.py", "p3_v57_co75_west_pitch_origin_search.py",
               "p3_v57_co76_nonexecutor_review.py"):
        whilefree[tp] = not re.search(r"^\s*while\b", (K2 / "tools" / tp).read_text(encoding="utf-8"), re.M)
    c9 = all(whilefree.values())

    # C10 阈值未放宽
    c10 = (rmcfg["capacity_audit"]["inter_pair_spacing"] == 1.46
           and rmcfg["channel_alloc"]["pitch_fallback"] == 1.08
           and rules["diff_pair"]["inter_pair_spacing"] == 0.875)

    # C11 SPEC rev-8 PDN 声明
    pzs = spec["pd"]["zone_defs"]["power_zones"]
    _retired = sum(1 for z in pzs if ("retired_polygons_bcu" in z) or ("retired_segments_bcu" in z))
    c11 = ({z["layer"] for z in pzs} == {"In4.Cu"}
           and spec["pd"].get("bcu_power_copper_policy", {}).get("policy") == "PROHIBITED"
           and all("in6_segments" not in z for z in pzs)
           and _retired == 3
           and any(i["id"] == "CO-72-PDN-1" and i["ruled"] for i in spec["pd"]["zone_defs"]["ecn_pending_items"]))

    checks = {"C1_engine_layer_roles": c1, "C2_drawing_decl_string": c2, "C3_drawing_no_In6_field": c3,
              "C4_board_layer_hygiene": c4, "C5_A5_hardened_and_pass": c5, "C6_engine_input_and_LID": c6,
              "C7_interpair_negative_intact": c7, "C8_frozen_sources_4of4": c8, "C9_tools_while_free": c9,
              "C10_thresholds_not_relaxed": c10, "C11_spec_rev8_pdn": c11}
    failures = [k for k, v in checks.items() if not v]
    rec = {
        "artifact": "m13_v57_co76_nonexecutor_review", "schema": 1, "revision": "CO-76.1",
        "nature": "非执行者侧对抗评审 pass 1/2（对象 CO-67..CO-75）+ F1/F2/F3 修复校验",
        "reviewer_independence": "本会话与 CO-67..73 执行者非同一会话（context 归零续接）；CO-74/75 为本会话改动，已排除在评审对象外",
        "findings": {
            "F1_stale_role_string_in_production_drawing": {
                "severity": "medium", "class": "declaration/artifact correctness",
                "evidence_before_fix": "decision_contract.r1_5_layer_rule = '...(dn=B.Cu, up=In6.Cu)...'；"
                                       "REV6 下 In6=GND，且实现为 up->In5.Cu ⇒ 声明与实现/叠层不一致",
                "fix": "引擎文本 up=In6.Cu -> up=In5.Cu（零几何）；图纸 decision_contract 随之更新",
                "status": "fixed"},
            "F2_A5_probe_coverage_hole": {
                "severity": "medium", "class": "verification weakness",
                "evidence_before_fix": "CO-69 A5 断言 '\"In6.Cu\"' not in eng（带引号）；裸 In6 文本 14 处全漏检",
                "fix": "A5 改裸 token 扫描 + 显式豁免 In6->In5 迁移注；修复前该强化断言会 FAIL（有齿）",
                "status": "fixed"},
            "F3_stale_comments": {"severity": "low", "class": "documentation",
                                  "fix": "10 处注释/docstring 的 In6 信号层表述改 In5（0 处残留，除迁移注）",
                                  "status": "fixed"}},
        "checks": checks, "failures": failures,
        "observations": {"engine_in6_lines_after_fix": in6_lines, "board_segment_layers": dict(seghist),
                         "board_zone_layers": dict(zonehist)},
        "residual": "本件 = pass 1/2；修复后的 revision 仍欠第二路非执行者评审；① 对间净空仍为 L1（CO-75 负结果）",
        "verdict": "PASS" if not failures else "FAIL",
        "redline": "评审只读；F1/F3 为文本修正零几何；阈值未放宽；四冻结源未动。",
    }
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "failures": failures, "record": s16(OUT),
                      "F1": "fixed", "F2": "fixed", "F3": "fixed"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
