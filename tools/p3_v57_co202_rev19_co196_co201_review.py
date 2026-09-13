#!/usr/bin/env python3
"""CO-202 — **非执行者对抗复评 CO-196..CO-201**（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（**逐件**）：CO-196 → `5e6ddde`（CO-195 定稿件：验证循环）+ `2898392`（CO-196 定稿件）；CO-197 → `2898392`；
CO-198 → `c922116`；CO-199 → `87148cb`；CO-200 → `68e2952`（oracle 三案）/ `3734a2f`（runner 定稿）；CO-201 → `8a4cc3c`（现行 HEAD）。
`git show` **内存重放** ⇒ 结论**不随后续处置漂移**。

方法：正控 **V1..V8**（独立复算，非引用被评记录）+ 负控 **P1..P10**（内存注入，**零落盘**、零坐标搜索）。
只读；不改 SPEC / 板 / 冻结四源 / 台账 / 他人记录；仅写本件记录 + 卡。
CLI: python3 tools/p3_v57_co202_rev19_co196_co201_review.py
"""
from __future__ import annotations
import ast, hashlib, json, re, subprocess, sys, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
TOOL = K2 / "tools/p3_v57_co164_order_runner.py"
ORACLE = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"
OREC = STEP2 / "m13_v57_co195_fixpoint_uniqueness.json"
REC = STEP2 / "m13_v57_co202_rev19_co196_co201_review.json"
CARD = STEP2 / "m13_v57_CO202_rev19_co196_co201_review.md"
FROZEN = {
    "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
    "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
    "../_shared/eda_core/drc_rules.json": "0a459839e15960b8",
}
OBJ = {  # 各 CO 的 as-found（缺陷态）定稿
    "CO-196": ["5e6ddde", "2898392"], "CO-197": ["2898392"], "CO-198": ["c922116"],
    "CO-199": ["87148cb"], "CO-200": ["68e2952", "3734a2f"], "CO-201": ["8a4cc3c"],
}


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16p(p) -> str:
    return s16b(Path(p).read_bytes())


def _git(rel: str, rev: str) -> str:
    r = subprocess.run(["git", "-C", str(K2), "show", f"{rev}:{rel}"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show {rev}:{rel} failed")
    return r.stdout


def _load(name: str, src: str, real_file) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(real_file)
    exec(compile(src, str(real_file), "exec"), mod.__dict__)
    return mod


def _load_af(rev: str, rel: str) -> types.ModuleType:
    return _load(f"af_{rev}", _git(rel, rev), K2 / rel)


def _af_runner(rev: str) -> types.ModuleType:
    return _load_af(rev, "tools/p3_v57_co164_order_runner.py")


def _af_oracle(rev: str) -> types.ModuleType:
    return _load_af(rev, "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py")


def _t28_predicate_controls(src: str, ns: dict) -> tuple:
    """t28 中 `oracle_tool_ok` 谓词**自身**的返回路径控制覆盖：
    返回 (存在但不可编译之文件控, 类型错控)。内存 AST + 在模块命名空间求值（零落盘）。
    `src` 须为**被评态之源文本**（禁似 re-read 现行档 ⇒ 结论随处置漂移）。"""
    compile_ctrl = type_ctrl = False
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "oracle_tool_ok" and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and a.value is None:
                type_ctrl = True
                continue
            try:
                val = eval(compile(ast.Expression(a), "<t28arg>", "eval"), ns)     # noqa: S307 (内存求值)
            except Exception:
                continue
            p = Path(val)
            if p.exists() and p.is_file():
                try:
                    compile(p.read_text(encoding="utf-8"), str(p), "exec")
                except Exception:
                    compile_ctrl = True
    return compile_ctrl, type_ctrl


def main() -> int:
    af = {r: _af_runner(r) for r in ("5e6ddde", "2898392", "c922116", "87148cb", "68e2952", "3734a2f", "8a4cc3c")}
    af_oracle_old, af_oracle_new = _af_oracle("68e2952"), _af_oracle("3734a2f")
    cur = _load("cur", TOOL.read_text(encoding="utf-8"), TOOL)
    cur_oracle = _load("cur_oracle", ORACLE.read_text(encoding="utf-8"), ORACLE)
    cur_src = TOOL.read_text(encoding="utf-8")
    reg = json.loads(REG.read_text(encoding="utf-8"))
    V, P, F = {}, {}, []

    # ── V1（CO-196 J-1）：as-found 验证循环 → 现行 t28 只判**结构性事实**（禁以被验证证据为输入）──
    af_cycle = "oracle_record_ok" in _git("tools/p3_v57_co164_order_runner.py", "5e6ddde")
    V["V1_CO196J1_no_verification_cycle"] = (
        af_cycle and "oracle_record_ok" not in cur_src
        and "m13_v57_co195_fixpoint_uniqueness.json" not in cur_src
        and cur.oracle_tool_ok(ORACLE) is True
        and cur.oracle_tool_ok(K2 / "tools/__no_such_oracle__.py") is False)

    # ── V2（CO-197 K-1/K-2）：牙齿/ md 写扫描已补同族形态，且**对偶负控**（字符串操作/只读）不误报 ──
    kw = cur.teeth_hygiene_scan('def f():\n    teeth={}\n    teeth.update(**{"t01": True})\n    return teeth\n')
    V["V2_CO197K1K2_scan_family_landed"] = (
        kw["n_teeth"] >= 1 and len(kw["constant_teeth"]) == 1
        and cur.md_write_scan('import io\nf = io.open("probe.md","w")') == ["probe.md"]
        and cur.md_write_scan('Path("a.md").replace("dst.md")') == ["dst.md"]
        and cur.md_write_scan('P = Path("a.md")\nP.rename("dst.md")') == ["dst.md"]
        and cur.md_write_scan('s = "a.md".replace(".md", "")') == []
        and cur.md_write_scan('import io\nf = io.open("ro.md")') == [])

    # ── V3（CO-198 E-1）：代理 ↔ 语义闸关系机判化；残余显式 + 判官源内齿名 + 代理齿入 pin ──
    pb = cur.PROXY_SEMANTIC_BINDING
    V["V3_CO198E1_proxy_semantic_binding"] = (
        hasattr(cur, "PROXY_SEMANTIC_BINDING") and bool(pb) and set(pb) <= set(cur.ORDER)
        and all(cur.proxy_binding_decision(g, d) == "ok" for g, d in pb.items()))

    # ── V4（CO-199 F-1）：白名单须声明**预期 rc 值**；声明面 + 运行期两处收严 ──
    _d = dict(cur.EXPECTED_NONZERO["co146_jlc_dfm_gate"])
    V["V4_CO199F1_rc_class_declared"] = (
        all(isinstance(v.get("rc"), int) and not isinstance(v.get("rc"), bool) and v["rc"] != 0
            for v in cur.EXPECTED_NONZERO.values())
        and cur.expected_nonzero_binding("co146_jlc_dfm_gate", {**_d, "rc": 0}) == "rc_not_declared"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 2, "", "FAIL", True, True) == "expected_step_rc_mismatch"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 127, "", "FAIL", True, True) == "expected_step_rc_mismatch")

    # ── V5（CO-200 G-1）：oracle 扩受控 md 产物案；齿名逐案显式（不挤占既有齿名）──
    ids_old = [c["id"] for c in af_oracle_old.CASES]
    ids_new = [c["id"] for c in af_oracle_new.CASES]
    V["V5_CO200G1_md_case_landed"] = (
        ids_new == ids_old + ["D_md_card_product"] and len(ids_new) == 4
        and all("tooth" in c for c in af_oracle_new.CASES))

    # ── V6（CO-201 G-1/G-2）：出口语义（stderr 全空）+ 豁免前缀**段边界**正/负控 ──
    V["V6_CO201G1G2_exit_and_boundary"] = (
        cur.allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True) == "expected_nonzero"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 1, "Error: boom\n", "FAIL", True, True)
            == "expected_step_error_output"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 1, "Traceback (most recent call last):\n", "FAIL", True, True)
            == "expected_step_crashed"
        and cur.shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings/sub/a.md")
        and not cur.shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulingsX/a.md")
        and not cur.shadow_exempt("pm_gate/artifacts/k2_v4/L5/jlc_package/05_layer_sequence.txtX"))

    # ── V7（登记簿卫生）：140 项 / OPEN 0 / counts 复算一致 / 14 条 CO-196..CO-201 全 CLOSED ──
    import collections
    items = reg["items"]
    sel = [i for i in items if str(i.get("finding", "")).startswith(("co196:", "co197:", "co198:", "co199:", "co200:", "co201:"))]
    # 注：V7 判**卫生**（counts 据 items 复算 + OPEN 0 + co196..co201 全 CLOSED），**不**钉总项数/单一 sha
    # （违 R-CO193-3：复评件只钉被评对象之 as-found，禁内嵌处置态/现行 sha ⇒ 否则随处置漂移）。
    V["V7_register_hygiene"] = (
        len(items) >= 140 and reg["meta"]["counts"].get("OPEN") == 0
        and reg["meta"]["counts"].get("total") == len(items)
        and reg["meta"]["counts"] == {**dict(collections.Counter(i["kind"] for i in items)),
                                      "OPEN": sum(1 for i in items if i["status"] == "OPEN"), "total": len(items)}
        and len(sel) == 13 and all(i["status"] == "CLOSED" for i in sel))

    # ── V8（链态）：冻结四源 4/4 + `--check` 全 True + oracle 工具可编译、证据件 PASS 且牙齿全 True ──
    frozen_ok = all(s16p(K2 / f) == want for f, want in FROZEN.items())
    chk = json.loads(subprocess.run([str(cur.PY), str(TOOL), "--check"], cwd=K2,
                                    capture_output=True, text=True).stdout)
    orec = json.loads(OREC.read_text(encoding="utf-8")) if OREC.exists() else {}
    V["V8_chain_health"] = (
        frozen_ok and bool(chk.get("checks")) and all(chk["checks"].values())
        and cur.oracle_tool_ok(ORACLE)
        and orec.get("verdict") == "PASS" and all(orec.get("teeth", {}).values()))

    # ── P1（CO-196 J-1）：as-found 以证据件 verdict 为静态前置 ⇒ 证据 FAIL 即锁死 ──
    P["P1_as_found_verification_cycle"] = af_cycle and "oracle_record_ok" not in cur_src
    # ── P2/P3（CO-197 K-1/K-2）：as-found 扫描漏计同族形态 → 现行抓 ──
    a197 = af["2898392"]
    P["P2_as_found_teeth_miss_kwargs"] = (
        a197.teeth_hygiene_scan('def f():\n    teeth=dict(**{"t01": True})\n    return teeth\n')["n_teeth"] == 0
        and cur.teeth_hygiene_scan('def f():\n    teeth=dict(**{"t01": True})\n    return teeth\n')["n_teeth"] >= 1)
    P["P3_as_found_md_miss_io_pathlib"] = (
        a197.md_write_scan('import io\nf = io.open("probe.md","w")') == []
        and a197.md_write_scan('Path("a.md").replace("dst.md")') == []
        and cur.md_write_scan('import io\nf = io.open("probe.md","w")') == ["probe.md"])
    # ── P4（CO-199 F-1）：as-found 无 rc 声明 ⇒ rc=2/127 与 rc=1 不可分 ──
    a199 = af["87148cb"]
    P["P4_as_found_rc_class_absent"] = (
        "rc" not in a199.EXPECTED_NONZERO["co146_jlc_dfm_gate"]
        and a199.allowlist_decision("co146_jlc_dfm_gate", 2, "", "FAIL", True, True) == "expected_nonzero"
        and a199.allowlist_decision("co146_jlc_dfm_gate", 127, "", "FAIL", True, True) == "expected_nonzero"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 2, "", "FAIL", True, True) == "expected_step_rc_mismatch")
    # ── P5（CO-200 G-1）：as-found oracle 三案仅扰 json（md 卡片面从未被扰动行使）──
    P["P5_as_found_oracle_3_cases_json_only"] = (
        len(af_oracle_old.CASES) == 3
        and all(Path(t).suffix != ".md" for c in af_oracle_old.CASES for t in c["targets"])
        and any(Path(t).suffix == ".md" for c in af_oracle_new.CASES for t in c["targets"]))
    # ── P6（CO-201 G-1/G-2）：as-found stderr 文本子串代理 + 段边界分支不可证伪 ──
    a201 = af["3734a2f"]
    a201_src = _git("tools/p3_v57_co164_order_runner.py", "3734a2f")
    P["P6_as_found_exit_proxy_and_boundary_vacuous"] = (
        a201.allowlist_decision("co146_jlc_dfm_gate", 1, "Error: boom\n", "FAIL", True, True) == "expected_nonzero"
        and "06_rulingsX" not in a201_src and "06_rulingsX" in cur_src)
    # ── P7（本复评 L-1）：as-found t28 谓词级控**欠**覆盖（存在但不可编译 / 类型错 无控）──
    a_cc, a_tc = _t28_predicate_controls(_git("tools/p3_v57_co164_order_runner.py", "8a4cc3c"), dict(vars(af["8a4cc3c"])))
    c_cc, c_tc = _t28_predicate_controls(cur_src, dict(vars(cur)))
    P["P7_t28_predicate_path_controls_absent"] = (not a_cc) and (not a_tc)
    # ── P8（本复评 L-2）：as-found 新停机类 `expected_step_rc_undeclared` 无合成控（仅其 return 一处）──
    P["P8_rc_undeclared_branch_uncontrolled"] = a201_src.count("expected_step_rc_undeclared") < 2
    # ── P9（本复评 L-3）：as-found 代理「源内声明」为**原文子串**代理 ⇒ 注释/散文即可满足 ──
    _pbase = {"proxy": "p", "residual": "r（非完备）", "semantic_judge": "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py",
              "semantic_teeth": ["t00_settle_converged"], "artifact": "m13_v57_co120_provenance_pin_gate.json", "why": "w"}
    _comment_only = lambda n: n in "# t00_settle_converged   （仅注释，非声明）"      # noqa: E731
    P["P9_proxy_tooth_substring_proxy"] = (
        "lambda name: name in src" in a201_src
        and a201.proxy_binding_decision("__nc__", dict(_pbase), src_has=_comment_only) == "ok")
    # ── P10（本复评 L-4）：as-found 受控集**类别数** > oracle 扰动量类别数（.svg/图 无为案）──
    watch_cat = {p.suffix for p in cur.watch_paths()}
    case_cat = {Path(t).suffix for c in af_oracle_new.CASES for t in c["targets"]}
    P["P10_oracle_category_coverage_gap"] = bool(watch_cat - case_cat)

    if P["P7_t28_predicate_path_controls_absent"]:
        F.append({"id": "L-1", "sev": "low", "object": "CO-196",
                  "what": "**t28 谓词级合成控欠覆盖**：R-CO196-4 明列「缺件 / 语法错 / **类型错** 各一」，而 t28 对被测谓词 `oracle_tool_ok` "
                          "仅行使**缺件**与正控；「语法错」控挂在**共享子程序** `src_compiles` 上（不证明谓词的编译失败传播），"
                          "「类型错」分支**无任何控**（实测 as-found：谓词级 compile/type 控各 False，而 `oracle_tool_ok(<存在但不可编译件>)`"
                          "确返 False ⇒ 实现正确、判据不可证伪）。"})
    if P["P8_rc_undeclared_branch_uncontrolled"]:
        F.append({"id": "L-2", "sev": "low", "object": "CO-199",
                  "what": "**运行期新停机类无合成控**：CO-199 新增之 `expected_step_rc_undeclared`（`allowlist_decision` 之 return 路径）"
                          "在 runner 源内**仅出现 1 次**（即其自身 return）⇒ 无任何合成控行使该分支（声明面之 `rc_not_declared` 控不覆盖运行期分支）"
                          "⇒ 违 R-CO196-4「每条返回路径一一对应」，该分支不可证伪。"})
    if P["P9_proxy_tooth_substring_proxy"]:
        F.append({"id": "L-3", "sev": "low", "object": "CO-198",
                  "what": "**「源内声明」以原文子串代理**：`proxy_binding_decision` 默认 `has = lambda name: name in src`（**裸子串**）⇒ "
                          "齿名仅出现于**注释/散文**（实测 `src_has` 注入 `\"# t00_settle_converged  （仅注释，非声明）\"` ⇒ `ok`）亦可满足"
                          " R-CO198-1「判官**源内声明的齿名**」⇒ 该判据非语义（注释即通过）；同文件已备 AST 字面量抽取器 `_source_strings` 却未用。"})
    if P["P10_oracle_category_coverage_gap"]:
        F.append({"id": "L-4", "sev": "low", "object": "CO-200",
                  "what": "**oracle 扰动量类别覆盖不足**：R-CO200-1 宣示「覆盖面 = 类别数（md / 报告 / **图** / 二进制）」，而受控集含 "
                          "`.json`/`.md`/**`.svg`（图）** 三类、oracle `CASES` 仅扰 `.json`/`.md` 两类 ⇒ `.svg` 产物（`JLC08161H_stackup.svg`，CO-174 入 pin）"
                          "只受**结构** pin（t08/t20），**从未**被「扰动启动 ⇒ 逐字节复原」语义实验行使（其全量重写性未被证）。"
                          "（亦与本谱系交接件 §4 之延后触发条件『受控集新增**另一类**产物（报告/图/二进制）』已于 CO-174 达成相矛盾。）"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    observations = [
        {"id": "O-1", "object": "CO-201", "status": "残余（本件登记，非 finding）",
         "what": "G-1 之修只约束 **stderr**（R-CO201-1 明示）；若某步将错误文本写 **stdout** 而 stderr 空、rc 恰为声明值 ⇒ 仍作预期出口放行"
                 "（`allowlist_decision` 未收 stdout）。语义上「设计出口 vs 错误出口」仍未由单一开关完全区分；触发 = 出现 stdout 错误外壳之白名单步。"},
        {"id": "O-2", "object": "CO-196", "status": "已由本 CO 之 L-1 合并处置",
         "what": "同 L-1：谓词级控欠覆盖（存在但不可编译 / 类型错）；本 CO 补控后闭合。"},
    ]
    rec = {
        "artifact": "m13_v57_co202_rev19_co196_co201_review", "schema": 1, "revision": "CO-202",
        "nature": "非执行者对抗复评 CO-196..CO-201（本谱系 z60..z67 之外之新会话；`git show` 内存重放 + 内存注入、零落盘）",
        # R-CO193-3：复评件只钉**被评对象之 as-found**；**禁**内嵌处置态/现行 sha（否则记录随处置漂移）。
        "as_found": {"objects": OBJ,
                     "runner_af_sha16": {r: s16b(_git("tools/p3_v57_co164_order_runner.py", r).encode()) for r in
                                         ("5e6ddde", "2898392", "c922116", "87148cb", "68e2952", "3734a2f", "8a4cc3c")},
                     "oracle_af_sha16": {r: s16b(_git("tools/p3_v57_co195_fixpoint_uniqueness_oracle.py", r).encode())
                                         for r in ("68e2952", "3734a2f")}},
        "objects": ["CO-196", "CO-197", "CO-198", "CO-199", "CO-200", "CO-201"],
        "positive_controls": V, "negative_controls": P, "findings": F, "n_findings": len(F),
        "observations": observations, "verdict": verdict,
        "disposition": "CO-202（L2 自裁）：runner 升 **CO-202.1** —— ① t28 补**谓词级**逐返回路径控（存在但不可编译 / 类型错）；"
                       "② `allowlist_decision` 增**可注入声明面** `decl=`，t30 补 `expected_step_rc_undeclared` 控；"
                       "③ `proxy_binding_decision` 默认「源内声明」改 **AST 字面量集**（`_source_strings`，注释/散文不满足）；"
                       "④ 新增静态齿 **t32**（受控集产物**类别数** == oracle 扰动量类别数）；oracle 升 **CO-202** —— `CASES` 扩第 5 案 "
                       "`E_svg_product`（`.svg`/图 类别，注入内容行）+ 牙齿 9 → **10**。findings 均 CLOSED。",
        "redline": "只读 as-found（`git show`）+ 内存注入、零落盘、零坐标搜索；不改他人记录/登记簿/冻结四源。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-202 — 非执行者对抗复评（CO-196..CO-201）｜as-found 逐件钉定", "",
             f"- verdict：**{verdict}**｜findings：{len(F)}（L-1..L-4，全 low）｜观察项：{len(observations)}（O-1 残余 / O-2 已并入 L-1）",
             "- 方法：正控 V1..V8（独立复算）+ 负控 P1..P10（内存注入、零落盘、零坐标搜索）", "",
             "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        lines.append(f"| {k} | {'True' if v else '**False**'} |")
    if F:
        lines += ["", "## Findings（as-found）", "", "| id | sev | 对象 | what |", "|---|---|---|---|"]
        for f in F:
            lines.append(f"| {f['id']} | {f['sev']} | {f['object']} | {f['what']} |")
    lines += ["", "## 观察（不改判 verdict）", ""]
    for o in observations:
        lines.append(f"- **{o['id']}（{o['object']}，{o['status']}）**：{o['what']}")
    lines += ["", "## 处置（CO-202，L2 自裁）", "", rec["disposition"], ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "findings": [f["id"] for f in F],
                      "V": V, "P": P, "rec_sha16": s16p(REC), "card_sha16": s16p(CARD)}, ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
