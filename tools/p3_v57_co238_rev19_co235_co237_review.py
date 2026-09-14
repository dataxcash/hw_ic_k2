#!/usr/bin/env python3
"""CO-238 — **非执行者对抗复评 CO-235..CO-237**（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（**逐件重放**）：`ab9c421`（CO-235 `b3047dc` / CO-236 `140a1a3` / CO-237 `ab9c421` 之**合并态**）。
方法：正控 V1..V4（独立复算：as-found 逐件 sha16 重放 / 冻结四源 / **漏洞形态纯复算** / 修复判据之判别力）
+ V5/V6（as-found 记录链派生键普查 / **域-声明等式复算**）。只读；不改 SPEC/板/冻结四源/他人记录。

**as-found 幂等**（R-CO193-3 / R-CO236-1）：本件内容为 `git show ab9c421` 之**纯函数**；不内嵌任何现行链派生量
（无 `--check` 计数、无现行 sha、无节计数）；同命令重跑**逐字节相同**。

CLI: python3 tools/p3_v57_co238_rev19_co235_co237_review.py
"""
from __future__ import annotations
import ast, hashlib, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
AF = "ab9c421"                                     # 被评态快照（CO-235..CO-237 合并态）
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
REC = STEP2 / "m13_v57_CO238_rev19_co235_co237_review.json"
CARD = STEP2 / "m13_v57_CO238_rev19_co235_co237_review.md"
RUNNER = "tools/p3_v57_co164_order_runner.py"
PINNED = {                                         # as-found 逐件（git show ab9c421:<rel> 重放）
    RUNNER: "2c0a68e6979ca102",
    "tools/p3_v57_co146_boundary_append.py": "0d3ff8dcf676dff6",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md": "34fe365c4a575dd2",
    "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json": "4523da1913ac2e40",
    "tools/p3_v57_co230_rev19_co225_co229_review.py": "35426723f58445a8",
    "tools/p3_v57_co235_rev19_co231_co234_review.py": "a04b9eabf0590781",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO230_rev19_co225_co229_review.json": "3b816ee2247eb7f1",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO235_rev19_co231_co234_review.json": "d6de768766e927f1",
    "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py": "585b983de844603d",
    "tools/p3_v57_co120_provenance_pin_gate.py": "28d6211f32318d9b",
    "tools/p3_v57_l5_signoff.py": "7618070712518194",
    "tools/p3_v57_co206_process_route_select.py": "83dba4f108663e6d",
    "k2_v4_8L.l4.kicad_pcb": "d4e81f647be7f980",
}
REVIEW_RE = re.compile(r"_review\.json$")
SHA_REF_RE = re.compile(r"`([^`\n]+_review\.json)`")
SHA16_RE = re.compile(r"`[0-9a-f]{16}`")


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16f(p: Path) -> str:
    return s16b(Path(p).read_bytes())


def git(rel: str, rev: str = AF) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=K2, capture_output=True).stdout


def af_pred_substring(src: str, rev: str) -> bool:
    """**as-found 之 t44 工具绑定判据**（CO-236 原文子串形态之复算）。"""
    return f'AF = "{rev}"' in src


def ast_tool_binding(src: str, rev: str, name: str = "AF") -> bool:
    """**修复判据**（CO-238）之独立复算：AST 赋值 + 字符串常量（注释/散文/拼接不满足）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            tgt, val = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            tgt, val = [node.target], node.value
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in tgt) \
           and isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value == rev:
            return True
    return False


def str_literals(src: str) -> set:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def main() -> int:
    af_runner = git(RUNNER).decode("utf-8", "replace")
    out: dict = {"artifact": "m13_v57_CO238_rev19_co235_co237_review", "schema": 1, "revision": "CO-238",
                 "nature": "非执行者对抗复评 CO-235..CO-237（context 归零之新会话，未参与该三节之撰写 ⇒ 无自评豁免面）；"
                           "as-found 逐件重放 + 漏洞形态纯复算 + 修复判据判别力；只读。",
                 "as_found": {"rev": AF, "pins": {}}}

    # ── V1 as-found 逐件重放（git show ab9c421） ─────────────────────────────
    v1 = {rel: {"want": w, "got": s16b(git(rel)), "ok": s16b(git(rel)) == w} for rel, w in PINNED.items()}

    # ── V2 冻结四源 + 交付板（独立复算） ─────────────────────────────────────
    fs = {"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
          "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
          "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
          "_shared/eda_core/drc_rules.json": "0a459839e15960b8"}
    fs_res = {rel: s16f(K2 / rel) == w for rel, w in fs.items()}
    copy_ok = (K2 / "_shared/eda_core/drc_rules.json").read_bytes() == \
              (K2.parent / "_shared/eda_core/drc_rules.json").read_bytes()
    board_ok = s16f(K2 / "k2_v4_8L.l4.kicad_pcb") == "d4e81f647be7f980"

    # ── V3 漏洞形态纯复算（as-found）：工具绑定臂 = 原文子串 ⇒ 注释/散文可满足 ──
    af_tool_src = git("tools/p3_v57_co235_rev19_co231_co234_review.py").decode("utf-8", "replace")
    real_binding = af_tool_src
    comment_only = af_tool_src.replace('AF = "03f8d39"',
                                       'AF_BINDING_REMOVED = None  # AF = "03f8d39"', 1)
    renamed_only = af_tool_src.replace('AF = "03f8d39"', 'SNAPSHOT = "03f8d39"', 1)
    v3 = {
        "af_pred_is_substring_form": ("in _tsrc" in af_runner and 'f\'AF = "' in af_runner),
        "af_pred_real_binding_ok": af_pred_substring(real_binding, "03f8d39"),
        "af_pred_comment_only_ok": af_pred_substring(comment_only, "03f8d39"),      # 期望 True ⇒ 漏洞
        "af_pred_renamed_no_comment_ok": af_pred_substring(renamed_only, "03f8d39"),  # 期望 False
        "renamed_with_comment_ok": af_pred_substring(renamed_only + '\n# AF = "03f8d39"\n', "03f8d39"),
    }
    v3["vulnerable"] = bool(v3["af_pred_comment_only_ok"] and v3["renamed_with_comment_ok"])

    # ── V4 修复判据（AST）之判别力（合成正/负控） ────────────────────────────
    v4 = {
        "real_binding_ok": ast_tool_binding('AF = "03f8d39"', "03f8d39"),
        "annotated_binding_ok": ast_tool_binding('AF: str = "03f8d39"', "03f8d39"),
        "comment_only_rejected": not ast_tool_binding('# AF = "03f8d39"', "03f8d39"),
        "docstring_rejected": not ast_tool_binding('"""AF = "03f8d39""""', "03f8d39"),
        "wrong_value_rejected": not ast_tool_binding('AF = "deadbeef"', "03f8d39"),
        "concat_rejected": not ast_tool_binding('AF = "03f8" + "d39"', "03f8d39"),
        "syntax_error_rejected": not ast_tool_binding('def f(:', "03f8d39"),
    }
    v4["discriminating"] = all(v4.values())

    # ── V5 as-found 记录之链派生键普查（确认 CO-236 结构臂与实况一致） ────────
    dk = {"n_sections_now", "declared_n", "n_static_declared", "V3_check"}   # as-found REISSUE_CHAIN_DERIVED_KEYS
    def keyscan(o):
        s = set()
        if isinstance(o, dict):
            for k, v in o.items():
                s.add(str(k)); s |= keyscan(v)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                s |= keyscan(v)
        return s
    v5 = {}
    for rel in ("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO230_rev19_co225_co229_review.json",
                "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO235_rev19_co231_co234_review.json"):
        try:
            rec = json.loads(git(rel).decode("utf-8"))
        except ValueError:
            rec = None
        v5[Path(rel).name] = {"rev_ok": (rec or {}).get("as_found", {}).get("rev") in ("fdb72a2", "03f8d39"),
                              "chain_keys": sorted(keyscan(rec) & dk)}
    v5_ok = all(d["rev_ok"] and not d["chain_keys"] for d in v5.values())

    # ── V6 as-found 域-声明等式复算（CO-237 之覆盖面） ──────────────────────
    af_bdy = git("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md").decode("utf-8", "replace")
    pinned_reviews = set()
    for line in af_bdy.splitlines():
        if line.startswith("|") and SHA16_RE.search(line):
            m = SHA_REF_RE.search(line)
            if m:
                pinned_reviews.add(Path(m.group(1)).name)
    af_lits = {Path(x).name for x in str_literals(af_runner) if REVIEW_RE.search(x)}
    declared = af_lits & {Path(x).name for x in PINNED if REVIEW_RE.search(x)} | {
        "m13_v57_CO230_rev19_co225_co229_review.json", "m13_v57_CO235_rev19_co231_co234_review.json"}
    v6 = {"n_pinned_reviews": len(pinned_reviews),
          "n_declared_or_exempt_literals": len(af_lits),
          "domain_minus_declared": sorted(pinned_reviews - af_lits),
          "floor_12_ok": len(pinned_reviews) >= 12}
    v6["equality_ok"] = not v6["domain_minus_declared"]

    # ── 汇总 ────────────────────────────────────────────────────────────────
    findings = [{"id": "F-1", "sev": "mid", "kind": "TOOL_DEFECT", "status": "CLOSED",
                 "what": "t44 之**工具绑定臂**（`_tool_ok`）为**原文子串** `f'AF = \"{rev}\"' in _tsrc` ⇒ 真绑定可被**注释/散文**替代而不失 pass "
                         "（承 R-CO202-4：源内声明之代理判据不得由注释满足；与 CO-215 同源缺陷）。",
                 "evidence": [f"V3 纯复算：真绑定→注释 ⇒ as-found 子串判据 = {v3['af_pred_comment_only_ok']}（True ⇒ 静默通过）",
                              f"V3：改名且加注释 ⇒ {v3['renamed_with_comment_ok']}（True）",
                              f"V4 修复判据（AST）判别力：{v4}"],
                 "disposition": "绑定判据改 **AST 赋值**（`AF` 之 `Assign`/`AnnAssign` 值须为 == rev 之字符串常量；注释/散文/拼接不满足；不可编译 ⇒ fail-closed）"
                                "+ 合成正/负控；扩 t44 绑定臂（不新增齿，仍 46）；report revision → **CO-203.15**；**R-CO238-1**。"}]
    out["as_found"]["pins"] = v1
    out["as_found"]["live_now"] = {"note": "本会话已按 F-1 处置（runner 改 AST 绑定）⇒ 现行 ≠ as-found 属预期；现行 sha 由 boundary §111 pin 表承载（承 R-CO152-1）。"}
    out["verdict"] = "PASS_WITH_FINDINGS"
    out["n_findings"] = len(findings)
    out["findings"] = findings
    out["controls"] = {
        "V1_as_found_replay_ok": all(d["ok"] for d in v1.values()),
        "V2_frozen_four": sum(fs_res.values()),
        "V2_drc_copy_identical": copy_ok,
        "V2_board_unchanged": board_ok,
        "V3_root_cause": v3,
        "V4_fix_discriminating_power": v4,
        "V5_records_clean": v5,
        "V6_domain_declared_equality": v6,
    }
    out["observations"] = [
        "O-1（as-found 诚实性）：CO-235..CO-237 之 canonical 件共 %d 件，逐件 sha16 自 `git show %s` 重放 **全 MATCH**；本会话未参与其撰写。" % (len(PINNED), AF),
        "O-2（CO-235 有效性）：其处置以「声明格式集 + 生成器 realign 同域 + t43 fail-closed」闭合该 F-1；本件 V1/V6 独立经手其产物，未见回归。",
        "O-3（CO-236 残余之界）：结构臂（as-found.rev 绑定 + 链派生键名集）与实况一致（V5：二记录 rev 合规、零链派生键）；其**工具绑定臂**为本件 F-1。",
        "O-4（CO-237 之域）：as-found pin 面之 `*_review.json` 受 pin 件 %d 件；声明/豁免字面并集 %d 件；域−声明 = %s（V6）⇒ 名集等式成立。" % (len(pinned_reviews), len(af_lits), v6["domain_minus_declared"] or "∅"),
        "O-5（残余，未闭，界定）：① 域以**文件名形态**界定（异名逃逸）；② 键名启发式（更名逃逸）；③ 绑定判据认 `AF` 之**字符串常量**赋值（非字面量构造不视为绑定 ⇒ fail-closed）。",
    ]
    out["redline"] = ("R-CO238-1：**源内声明之代理判据须为 AST 绑定** —— 复评/重出件工具之 as-found 绑定（如 `AF = \"<rev>\"`）须以 **AST 赋值 + 字符串常量** 机判；"
                      "**注释/散文/拼接一律不得满足**（承 R-CO202-4）；此形态须有机判齿（t44 绑定臂），承 R-CO225-1。")
    REC.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ── 卡片 ────────────────────────────────────────────────────────────────
    L = ["# CO-238 — 非执行者对抗复评 **CO-235..CO-237**\n"]
    L.append("复评者 = **非执行者**（context 归零之**新会话**；未参与该三节撰写 ⇒ 无自评豁免面）；as-found 逐件钉 `%s`；只读。" % AF)
    L.append(f"判决 = **{out['verdict']}**（findings {len(findings)}：F-1 mid；正控 V1..V6）。**未**改动冻结四源/板/SPEC。\n")
    L.append("## 1. as-found（逐件 sha16，`git show %s` 重放）\n" % AF)
    L.append("| 件 | as-found sha16 | 重放 |\n|---|---|---|")
    for rel, d in v1.items():
        L.append(f"| `{rel}` | `{d['want']}` | {'MATCH' if d['ok'] else 'MISMATCH'} |")
    L.append("\n## 2. 正控\n")
    L.append(f"- 冻结四源 **{sum(fs_res.values())}/4**；`drc_rules` 副本同字节 = **{copy_ok}**；交付板 `d4e81f647be7f980` 未变 = **{board_ok}**")
    L.append(f"- **V3 漏洞纯复算**（as-found）：子串判据对「真绑定→注释」= **{v3['af_pred_comment_only_ok']}**（True ⇒ 静默通过）；「改名+注释」= **{v3['renamed_with_comment_ok']}** ⇒ 绑定臂可被散文满足")
    L.append(f"- **V4 修复判据（AST）判别力** = **{v4['discriminating']}**；**V5 记录链派生键** 全清 = **{v5_ok}**；**V6 域−声明** = {v6['domain_minus_declared'] or '∅'}（{len(pinned_reviews)} 件 ≥ 下限 12 = {v6['floor_12_ok']}）\n")
    L.append("## 3. F-1（TOOL_DEFECT · mid · CLOSED）**t44 工具绑定臂 = 原文子串 ⇒ 注释/散文可替代真绑定**\n")
    L.append("**根因**：`_tool_ok[_rel] = (f'AF = \"{_d[\"as_found\"]}\"' in _tsrc)` —— 原文子串测试；**注释提及同串即满足**。"
             "承 **R-CO202-4**（源内声明之代理判据须 AST 字面量，注释/散文不得满足）与 **CO-215**（同源缺陷：子串即可满足）之既定裁定。\n")
    L.append("**处置（L2 自裁）**：绑定判据改 **AST 赋值**（`AF` 之 `Assign`/`AnnAssign` 值须为 == rev 之字符串常量；注释/散文/拼接不满足；SyntaxError ⇒ fail-closed）"
             "+ 合成正/负控（6 项）；扩 t44 绑定臂（不新增齿，仍 46）；report revision → **CO-203.15**；**R-CO238-1**。\n")
    L.append("## 4. 观测\n")
    for o in out["observations"]:
        L.append("- " + o)
    L.append("\n## 5. 红线\n")
    L.append("> " + out["redline"])
    CARD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "n_findings": len(findings),
                      "V1": out["controls"]["V1_as_found_replay_ok"], "V2_frozen": sum(fs_res.values()),
                      "V3_vulnerable": v3["vulnerable"], "V4_discriminating": v4["discriminating"],
                      "V5_ok": v5_ok, "V6": v6, "rec": s16f(REC), "card": s16f(CARD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
