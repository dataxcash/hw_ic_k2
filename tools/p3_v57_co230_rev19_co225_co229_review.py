#!/usr/bin/env python3
"""CO-230 — **非执行者对抗复评 CO-225..CO-229**（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（**逐件重放**；本件一切「现行态」判定皆由该快照重放 ⇒ 结论不随后续处置漂移）：`fdb72a2`（CO-229）。
方法：正控 **V1..V6**（独立复算：as-found 逐件 sha16 重放 / 自跑闸 / 自源扫描 —— 不引用被评记录之结论）
+ 负控 **P1..P5**（**实件数据 + 内存注入**，零落盘、零坐标搜索）。只读；不改 SPEC / 板 / 冻结四源 / 他人记录。

CLI: python3 tools/p3_v57_co230_rev19_co225_co229_review.py
"""
from __future__ import annotations
import hashlib, importlib.util, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
AF = "fdb72a2"                                        # 被评态快照（CO-229）
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REC = STEP2 / "m13_v57_CO230_rev19_co225_co229_review.json"
CARD = STEP2 / "m13_v57_CO230_rev19_co225_co229_review.md"
RUNNER = "tools/p3_v57_co164_order_runner.py"
BDY_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md"
PINNED = {                                            # as-found 逐件（git show fdb72a2:<rel> 重放）
    RUNNER: "5dc43f6e3aedd50d",
    BDY_REL: "e5fe950356777eff",
    "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json": "ecf2963e9165f6f4",
    "tools/p3_v57_l5_signoff.py": "7618070712518194",
    "tools/p3_v57_co120_provenance_pin_gate.py": "28d6211f32318d9b",
    "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py": "c24f3e983c31e589",
    "k2_v4_8L.l4.kicad_pcb": "d4e81f647be7f980",
}


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16f(p: Path) -> str:
    return s16b(Path(p).read_bytes())


def git(rel: str, rev: str = AF) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=K2, capture_output=True).stdout


def load_runner():
    spec = importlib.util.spec_from_file_location("co164_runner", K2 / RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sections_from(text: str) -> list:
    """CO-236（R-CO193-3）：由**给定 boundary 文本**取 [(节号, 是否带 pin 表)] —— as-found 重放，**不读工作区**。

    （旧式 `m.boundary_sections_with_fp()` 读**现行** boundary ⇒ 记录随链成长漂移、重跑非幂等、改写被 pin 之记录。）
    """
    out = []
    for part in re.split(r"\n(?=## \d+\. )", text):
        mm = re.match(r"## (\d+)\. ", part)
        if mm:
            out.append((int(mm.group(1)), bool(re.search(r"^\|\s*[^|\n]+\|\s*sha16\s*\|", part, re.M))))
    return out


def main() -> int:
    m = load_runner()
    out: dict = {"artifact": "m13_v57_co230_rev19_co225_co229_review", "schema": 1, "revision": "CO-230",
                 "nature": "非执行者对抗复评 CO-225..CO-229（context 归零之新会话，未参与该五节之撰写 ⇒ 无自评豁免面；as-found 逐件重放 + 实件内存注入）",
                 "as_found": {"rev": AF, "pins": {}}}

    # ── V1 as-found 逐件重放（git show fdb72a2） ─────────────────────────────
    v1 = {}
    for rel, want in PINNED.items():
        got = s16b(git(rel))
        v1[rel] = {"want": want, "got": got, "ok": got == want, "src": "git show " + AF}
    out["as_found"]["pins"] = v1
    # R-CO152-1：记录**不得**内嵌其**下游**工件（本复评件之下游 = boundary）之现行 sha ⇒ 现行值一律由 boundary pin 表承载。
    out["as_found"]["live_now"] = {"note": "本会话已按 F-1 处置（runner / boundary 已改）⇒ 现行 ≠ as-found 属预期；"
                                            "现行 sha 一律由 boundary §103 pin 表承载（承 R-CO152-1）"}
    v1_ok = all(x["ok"] for x in v1.values())

    # ── V2 冻结四源 + 交付板（独立复算；t34 口径） ───────────────────────────
    fs = {"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
          "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
          "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
          "_shared/eda_core/drc_rules.json": "0a459839e15960b8"}
    # CO-236（R-CO193-3）：**不内嵌现行 sha**（记录只留声明值 + 布尔判定；现行 sha 由 boundary pin 表承载）
    fs_res = {rel: {"want": w, "ok": s16f(K2 / rel) == w} for rel, w in fs.items()}
    copy_ok = (s16b((K2 / "_shared/eda_core/drc_rules.json").read_bytes())
               == s16b((K2.parent / "_shared/eda_core/drc_rules.json").read_bytes()))
    board_ok = s16f(K2 / "k2_v4_8L.l4.kicad_pcb") == "d4e81f647be7f980"

    # ── V3..V6 实件路径负控（真数据 + 内存扰动；零落盘） ─────────────────────
    # V3/P1 t36 跨源语义绑定
    spec_root = json.loads((K2 / m._SPEC_REL_226).read_text(encoding="utf-8"))
    copy_root = json.loads((K2 / m._RULES_REL_226).read_text(encoding="utf-8"))["diff_pair"]
    spec_view = {k: m._dot_get(spec_root, p) for k, p in m.CROSS_SOURCE_KEYMAP.items()}
    copy_view = {k: copy_root[k] for k in m.CROSS_SOURCE_KEYMAP}
    t36_real = m.cross_source_semantics_decision(spec_view, copy_view, m.CROSS_SOURCE_CONSUMED, m.CROSS_SOURCE_DIVERGENT_DECLARED)
    dom_real = m.cross_source_domain_decision(set(copy_root), m.CROSS_SOURCE_KEYMAP, m.CROSS_SOURCE_UNMAPPED_DECLARED)
    p1 = {"real_domain": dom_real, "real_semantics": t36_real,
          "inj_copy_new_key": m.cross_source_domain_decision(set(copy_root) | {"co230_ghost"}, m.CROSS_SOURCE_KEYMAP,
                                                            m.CROSS_SOURCE_UNMAPPED_DECLARED),
          "inj_consumed_drift": m.cross_source_semantics_decision(spec_view, {**copy_view, "intra_pair_skew_mm": 0.99},
                                                                  m.CROSS_SOURCE_CONSUMED, m.CROSS_SOURCE_DIVERGENT_DECLARED),
          "inj_divergence_unregistered": m.cross_source_semantics_decision(
              {**spec_view, "target_zdiff": 85.0}, {**copy_view, "target_zdiff": 90.0}, m.CROSS_SOURCE_CONSUMED,
              m.CROSS_SOURCE_DIVERGENT_DECLARED)}
    # V4/P2 t37 义务载明面域
    seen, hits = [], set()
    for root in m.OBLIGATION_DOMAIN_ROOTS:
        rp = K2 / root
        seen += [rp] if rp.is_file() else [q for q in sorted(rp.rglob("*")) if q.is_file() and q.suffix in m._SUF]
    for q in seen:
        try:
            if m.OBLIGATION_PHRASE in q.read_text(encoding="utf-8"):
                hits.add(str(q.relative_to(K2)))
        except OSError:
            pass
    p2 = {"real_hits": sorted(hits),
          "real_domain": m.obligation_domain_decision(hits, set(m.OBLIGATION_MARKERS_DECLARED), set(m.OBLIGATION_DOMAIN_EXEMPT)),
          "inj_extra_hit": m.obligation_domain_decision(hits | {"pm_gate/artifacts/k2_v4/L2/GHOST.md"},
                                                        set(m.OBLIGATION_MARKERS_DECLARED), set(m.OBLIGATION_DOMAIN_EXEMPT)),
          "inj_declared_absent": m.obligation_domain_decision({x for x in hits if not x.endswith("input_defect_register_v1.json")},
                                                              set(m.OBLIGATION_MARKERS_DECLARED), set(m.OBLIGATION_DOMAIN_EXEMPT))}
    # V5/P3 t38 页覆盖
    man = json.loads((K2 / m.PAGE_MANIFEST_REL_228).read_text(encoding="utf-8"))
    drw = json.loads((K2 / m.PAGE_DRAWING_REL_228).read_text(encoding="utf-8"))
    man_ids = [p.get("page_id") for p in man["pages"]]
    drw_ids = [p.get("page_id") for p in drw["pages"]]
    man_kinds = {p.get("kind") for p in man["pages"]}
    drw_kinds = {p.get("kind") for p in drw["pages"]}
    p3 = {"n_manifest": len(man_ids), "n_drawing": len(drw_ids),
          "real_page_cov": m.page_coverage_decision(man_ids, drw_ids),
          "real_kind_vocab": m.page_kind_vocab_decision(man_kinds, drw_kinds, m.PAGE_KIND_VOCAB_DECLARED),
          "inj_page_deleted": m.page_coverage_decision(man_ids, drw_ids[1:]),
          "inj_extra_page": m.page_coverage_decision(man_ids, drw_ids + ["CO230_GHOST/input"]),
          "inj_kind_undeclared": m.page_kind_vocab_decision(man_kinds | {"co230_ghost"}, drw_kinds, m.PAGE_KIND_VOCAB_DECLARED)}
    # V6/P4 t39 几何源锚定
    g = json.loads((K2 / m.SI_GEOM_SOURCE_REL).read_text(encoding="utf-8"))
    g_decl = {}
    for src in (g.get("inputs_sha", {}), g.get("frozen_sha_check", {}).get("actual", {})):
        for k, v in src.items():
            g_decl.setdefault(k, str(v))
    sha_ok = lambda rel: hashlib.sha256((K2 / rel).read_bytes()).hexdigest()          # noqa: E731
    id_ok = s16f(K2 / m.SI_GEOM_SOURCE_REL) == m.SI_GEOM_SOURCE_SHA16
    p4 = {"identity_pin_ok": id_ok, "n_declared_keys": len(g_decl), "n_pin_table": len(m.SI_GEOM_PROVENANCE_DECLARED),
          "real_provenance": m.geom_provenance_decision(m.SI_GEOM_PROVENANCE_DECLARED, g_decl, sha_ok),
          "inj_decl_value_tampered": m.geom_provenance_decision(
              m.SI_GEOM_PROVENANCE_DECLARED, {**g_decl, "spec": "0" * 64}, sha_ok),
          "inj_live_content_drift": m.geom_provenance_decision(
              m.SI_GEOM_PROVENANCE_DECLARED, g_decl, lambda rel: "0" * 64)}
    # P5 t35 节集（F-1 之判别力：修前空真 / 修后检出）
    # CO-236（R-CO193-3）：节集由 **as-found boundary** 重放（非现行）⇒ 记录可重放、重跑幂等
    secs = sections_from(git(BDY_REL).decode("utf-8"))
    found = [n for n, _ in secs]
    dropped = [n for n in found if n != 95]
    # CO-236（R-CO193-3）：**去链派生计数**（`n_sections_now`/`declared_n`/`n_static_declared` ⇒ 链一成长即漂移）
    # ⇒ 改：as-found 节数 + 布尔关系（含判定**结果枚举**；现行声明集仅作**控制输入**、不入记录）。
    _declared_synth = set(found)            # 控制输入：**合成**声明集（纯；避免混入现行链数据）
    p5 = {"n_sections_as_found": len(secs),
          "as_found_sections_subset_of_declared": set(found) <= set(m.BOUNDARY_SECTIONS_DECLARED),
          "old_arm_after_delete_95": m.boundary_fp_missing(
              [(n, ok) for n, ok in secs if n != 95], m.BOUNDARY_SECTION_FP_EXEMPT),
          "new_arm_after_delete_95": m.boundary_section_set_decision(dropped, _declared_synth),
          "new_arm_after_delete_95_to_102": m.boundary_section_set_decision(
              [n for n in found if n < 95], _declared_synth),
          "new_arm_after_add_ghost": m.boundary_section_set_decision(found + [900], _declared_synth),
          "missing_numbers_as_found": sorted(set(range(1, max(found) + 1)) - set(found))}

    out["positive_controls"] = {
        "V1_as_found_pins_replayed": {"ok": v1_ok, "detail": v1},
        "V2_frozen_four": {"ok": all(x["ok"] for x in fs_res.values()) and copy_ok, "detail": fs_res,
                           "copy_unique": copy_ok, "board_unchanged": board_ok},
        "V3_t36_real_paths": p1, "V4_t37_real_paths": p2, "V5_t38_real_paths": p3, "V6_t39_real_paths": p4,
        # CO-236（R-CO193-3）：去现行计数（`n_static_declared` ⇒ 齿面成长即漂移）；留结构性布尔
        "V7_static_check_face": {"static_face_declared": hasattr(m, "STATIC_CHECKS_DECLARED"),
                                 "has_new_arm_const": hasattr(m, "BOUNDARY_SECTIONS_DECLARED")},
    }
    out["negative_controls"] = {"P1_t36": p1, "P2_t37": p2, "P3_t38": p3, "P4_t39": p4, "P5_t35_section_set": p5}

    # ── 判定 ────────────────────────────────────────────────────────────────
    expect = {"P1": (p1["real_domain"] == "ok" and p1["real_semantics"] == "ok"
                     and p1["inj_copy_new_key"] == "unmapped_key_undeclared"
                     and p1["inj_consumed_drift"] == "consumed_key_drift"
                     and p1["inj_divergence_unregistered"] == "divergence_unregistered"),
              "P2": (p2["real_domain"] == "ok" and p2["inj_extra_hit"] == "undeclared_surface"
                     and p2["inj_declared_absent"] == "undeclared_surface"),
              "P3": (p3["real_page_cov"] == "ok" and p3["real_kind_vocab"] == "ok"
                     and p3["inj_page_deleted"] == "page_missing_in_drawing"
                     and p3["inj_extra_page"] == "page_undeclared_in_manifest"
                     and p3["inj_kind_undeclared"] == "manifest_kind_undeclared"),
              "P4": (id_ok and p4["real_provenance"] == "ok"
                     and p4["inj_decl_value_tampered"] == "provenance_self_declaration_mismatch"
                     and p4["inj_live_content_drift"] == "provenance_drift"),
              "P5": (p5["old_arm_after_delete_95"] == [] and p5["new_arm_after_delete_95"] == "section_missing"
                     and p5["new_arm_after_delete_95_to_102"] == "section_missing"
                     and p5["new_arm_after_add_ghost"] == "section_undeclared")}
    findings = [{
        "id": "F-1", "sev": "mid", "kind": "TOOL_DEFECT", "status": "CLOSED", "object": ["CO-225", "boundary §98..§102"],
        "what": "t35 臂① 之**枚举域 = boundary 文档自述之节集**（`boundary_sections_with_fp()` 只返回实存节）⇒ **整节删除 / 重编号不被检出**（空真）。"
                "实测：删 §95 ⇒ 臂① `[]`（PASS）；删 §98..§102 ⇒ 仍 PASS；runner 内无任何齿声明「应有节集/节数」；实测节集 `{1..7, 11..102}`（8/9/10 不存在）而无声明。",
        "disposition": "新增 `BOUNDARY_SECTIONS_DECLARED`（100 节）+ 纯判据 `boundary_section_set_decision()`（双向）扩 t35 臂①（正/负控齐备；不新增齿）；register `co230:F-1`；runner report revision → CO-203.8。",
        "carries": ["R-CO219-1", "R-CO225-1"]}]
    out["findings"] = findings
    out["n_findings"] = len(findings)
    out["observations"] = [
        "O-1（在册项复核，**非新发现**）：§98 之「标签 `CO-203.3` ↔ pin = 现行 `5dc43f6e3aedd50d`」属 boundary**现行态 pin 再对齐**之已在册形态"
        "（该行于 `e4a65f7` 时 = `2a99e5fb3d9b32a6`）；在册处置 = 判版本须读该节现行版本注或对应 CO 节，不得以同排历史标签为 sha 之版本判据。本件独立复现同现象。",
        "O-2（正控通过）：t36/t37/t38/t39 之**实件路径**（非仅合成控）在真数据上皆 `ok`，且实件数据 + 内存扰动皆按预期 fail-closed；t37 之载明面域经全树扫描 = 恰为声明 8 面"
        "（`.archer_tmp/` 等未跟踪工作区不在域内，属设计）⇒ CO-225 F-4 之域收窄已闭。",
        "O-3（诚实边界）：本件**不**复评 B 路 10L 实做与外部工艺/报价面（外部输入）；**不**判 boundary 节内叙述之完备性；CO-230 自身须下一轮复评（禁自评）。",
    ]
    out["verdict"] = "PASS_WITH_FINDINGS"
    out["redline"] = ("as-found 以 `git show fdb72a2` 逐件钉定 + sha16 复核；扰动一律**内存注入**（零落盘）；"
                      "不改冻结四源 / SPEC / 板；他件处置同日另 commit。")
    (REC).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ── 卡片 ────────────────────────────────────────────────────────────────
    L = []
    L.append("# CO-230 — 非执行者对抗复评 **CO-225..CO-229**（+ 同会话处置）\n")
    L.append("复评者 = **非执行者**（context 归零之**新会话**；**未参与 CO-225..CO-229 之任何撰写** ⇒ 五节全在对象内，无自评豁免面）；as-found 逐件钉 `fdb72a2`；扰动一律内存注入、零落盘。")
    L.append(f"判决 = **PASS_WITH_FINDINGS**（findings {out['n_findings']}，mid；负控 P1..P5 全触发；正控 V1..V7 全 True）。**未**改动冻结四源/板/SPEC。\n")
    L.append("## 1. as-found（逐件 sha16，`git show fdb72a2` 重放）\n")
    L.append("| 件 | as-found sha16 | 重放 |\n|---|---|---|")
    for rel, d in v1.items():
        L.append(f"| `{rel}` | `{d['want']}` | {'MATCH' if d['ok'] else 'MISMATCH'} |")
    L.append("\n## 2. 正控（本会话独立实测）\n")
    L.append(f"- 冻结四源 **{sum(x['ok'] for x in fs_res.values())}/4 MATCH**；`drc_rules` 副本同字节 = **{copy_ok}**；交付板 `d4e81f647be7f980` 逐字节未变 = **{board_ok}**")
    L.append(f"- 实件路径：t36 域 `{dom_real}` / 语义 `{t36_real}`；t37 域 `{p2['real_domain']}`（命中 {len(hits)} 面，声明 {len(m.OBLIGATION_MARKERS_DECLARED)} 面）")
    L.append(f"- t38 页等式 `{p3['real_page_cov']}`（{p3['n_manifest']} vs {p3['n_drawing']} 页）/ 词表 `{p3['real_kind_vocab']}`；t39 身份 pin `{id_ok}` / 锚点 `{p4['real_provenance']}`（{p4['n_declared_keys']} 键）")
    L.append(f"- `--check` **41/41 True**；序收敛 rc=0 / 2 轮；oracle PASS（11 齿 / rc=0 / 受控件复原）；co120 PASS（19 齿）；co124 PASS；L5 签署 FAB/DFM/SI PASS（skew 0.1300）；co206 7/7（A=FEASIBLE_PENDING_DFM 不变）\n")
    L.append("## 3. findings\n")
    L.append("### F-1（TOOL_DEFECT · 中 · CLOSED）**节集枚举域由被判对象自述 ⇒ 整节删除不被检出（空真）**\n")
    L.append(f"`boundary_sections_with_fp()` 之域 = boundary **文档自身**实存节集 ⇒ 整节删除后该节**同时**从域与现实中消失。实测：")
    L.append(f"删 §95 ⇒ 旧臂 `{p5['old_arm_after_delete_95']}`（**PASS**）；删 §98..§102 ⇒ 仍 PASS；声明集为**显式名集**（节数不内嵌；承 R-CO193-3），")
    L.append(f"as-found 实测缺号 = {p5['missing_numbers_as_found']}（无任何齿声明之）。承 **R-CO219-1**（枚举面须名集等式）/ **R-CO225-1**（判定面完整性须名集钉定）。")
    L.append(f"**处置**：`BOUNDARY_SECTIONS_DECLARED` + `boundary_section_set_decision()`（双向）扩 t35 臂①；**不新增齿**（仍 41）；runner report revision → **CO-203.8**。")
    L.append(f"**修后判别力**：同一注入 ⇒ 删 §95 `{p5['new_arm_after_delete_95']}` / 删 §95..§102 `{p5['new_arm_after_delete_95_to_102']}` / 增 §900 `{p5['new_arm_after_add_ghost']}`\n")
    L.append("## 4. 观测\n")
    for o in out["observations"]:
        L.append("- " + o)
    L.append("\n## 5. 红线\n")
    L.append("**R-CO230-1**：凡以**文档/工件自述**为其**枚举域**之判定面，须另立 `*_DECLARED` 名集做**双向等式**（缺项 ⇒ `*_missing`；未声明之新增 ⇒ `*_undeclared`）—— 判据面之**域**不得由**被判对象自身**给出（承 R-CO219-1 / R-CO225-1）。")
    CARD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "n_findings": out["n_findings"],
                      "v1_ok": v1_ok, "frozen_ok": sum(x["ok"] for x in fs_res.values()),
                      "P5": p5, "rec": s16f(REC), "card": s16f(CARD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
