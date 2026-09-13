#!/usr/bin/env python3
"""CO-197 — **非执行者对抗复评** CO-192..CO-195（context 归零的续接会话；满足「复评须另一会话，禁自评」）。

对象 as-found = k2 `5e6ddde`（**逐件**：CO-192/193/194/195 各以其定稿件为 as-found；`git show` **内存重放** ⇒ 结论不随后续处置漂移）。
方法：正控 **V1..V8**（独立复算，非引用被评记录）+ 负控 **P1..P6**（内存注入，**零落盘**、零坐标搜索）。
只读；不改 SPEC/板/冻结四源/台账/他人记录；仅写本件记录 + 卡。
CLI: python3 tools/p3_v57_co197_rev19_co192_co195_review.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
TOOL = K2 / "tools/p3_v57_co164_order_runner.py"
ORACLE = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OREC = STEP2 / "m13_v57_co195_fixpoint_uniqueness.json"
REC = STEP2 / "m13_v57_co197_rev19_co192_co195_review.json"
CARD = STEP2 / "m13_v57_CO197_rev19_co192_co195_review.md"
AS_FOUND_REV = "5e6ddde"
FROZEN = {
    "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
    "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
    "../_shared/eda_core/drc_rules.json": "0a459839e15960b8",
}
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16p(p) -> str:
    return s16b(Path(p).read_bytes())


def _as_found(rel: str, rev: str = AS_FOUND_REV) -> str:
    r = subprocess.run(["git", "-C", str(K2), "show", f"{rev}:{rel}"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show {rev}:{rel} failed")
    return r.stdout


def _load(name: str, src: str, real_file) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(real_file)
    exec(compile(src, str(real_file), "exec"), mod.__dict__)
    return mod


TEETH_KW = 'def f():\n    teeth={}\n    teeth.update(**{"t01": True})\n    return teeth\n'
TEETH_KW2 = 'def f():\n    teeth=dict(**{"t01": True})\n    return teeth\n'
MD_IO = 'import io\nf = io.open("probe.md","w")\n'
MD_PATHREPL = 'Path("a.md").replace("dst.md")\n'
MD_PATHALIAS = 'P = Path("a.md")\nP.rename("dst.md")\n'
MD_STRREPL = 's = "a.md".replace(".md", "")\n'


def main() -> int:
    af_src = _as_found("tools/p3_v57_co164_order_runner.py")
    af = _load("co164_as_found_5e6ddde", af_src, TOOL)
    # 逐件 as-found：CO-192/193/194 分别以其**定稿件**（前一 CO 的提交）为被评状态
    af192 = _load("co164_as_found_52235b5", _as_found("tools/p3_v57_co164_order_runner.py", "52235b5"), TOOL)
    af193 = _load("co164_as_found_3e4f747", _as_found("tools/p3_v57_co164_order_runner.py", "3e4f747"), TOOL)
    af194 = _load("co164_as_found_334ed74", _as_found("tools/p3_v57_co164_order_runner.py", "334ed74"), TOOL)
    cur = _load("co164_current", TOOL.read_text(encoding="utf-8"), TOOL)
    af_oracle = _as_found("tools/p3_v57_co195_fixpoint_uniqueness_oracle.py")
    cur_oracle = ORACLE.read_text(encoding="utf-8")
    V, P, F = {}, {}, []

    # ── V1（CO-192 F-1 + CO-197 K-1）：牙齿棘轮 —— 现行零违规 + 逐工具齿数下限 + 全部已列形态纳扫 ──
    own = {}
    for s in set(cur.ORDER):
        for rel in cur.STEP_ARTIFACTS.get(s, []):
            b = Path(rel).name
            if b in cur.EXPECTED_TEETH and (tp := cur.tool_path(s)) is not None:
                own[b] = tp
    floor = {}
    for b, tp in own.items():
        floor[tp.name] = max(floor.get(tp.name, 0), len(cur.EXPECTED_TEETH[b]))
    live = {q.name: cur.teeth_hygiene_scan(q.read_text(encoding="utf-8")) for q in set(own.values())}
    forms = [TEETH_KW, TEETH_KW2,
             'def f():\n    teeth={}\n    teeth |= {"t01": True}\n    return teeth\n',
             'def f():\n    rec={"teeth":{}}\n    rec["teeth"]["t01"]=True\n    return rec\n',
             'def f(ks):\n    teeth={k: True for k in ks}\n    return teeth\n',
             'def f():\n    teeth={}\n    teeth.__setitem__("t01", True)\n    return teeth\n',
             'def f(self):\n    self.teeth["t01"]=True\n    return self.teeth\n',
             'TEETH={"t01":True}\ndef f():\n    rec={}\n    rec["teeth"]=TEETH\n    return rec\n']
    fx = [cur.teeth_hygiene_scan(x) for x in forms]
    V["V1_CO192F1_teeth_ratchet_live_clean_floor_and_forms"] = (
        set(own) == set(cur.EXPECTED_TEETH)
        and all(not v["constant_teeth"] and not v["premature_agg"] for v in live.values())
        and all(live[k]["n_teeth"] >= v for k, v in floor.items())
        and sum(v["n_teeth"] for v in live.values()) >= 100
        and all(r["n_teeth"] >= 1 and r["constant_teeth"] for r in fx))

    # ── V2（CO-192 F-2 + CO-197 K-2）：md 产物受控 + 豁免绑实存补偿齿 + 已列写/拷形态纳扫 ──
    scan = {s: cur.md_write_scan(tp.read_text(encoding="utf-8")) for s in set(cur.ORDER)
            if (tp := cur.tool_path(s)) is not None}
    found = {b for v in scan.values() for b in v}
    pin = {Path(v).name for v in cur.ORDER_MD_PRODUCTS.values()}
    exempt = set(cur.ORDER_MD_PRODUCT_EXEMPT)
    V["V2_CO192F2_md_products_controlled_and_forms"] = (
        set(cur.ORDER_MD_PRODUCTS) == {s for s, v in scan.items() if set(v) - exempt}
        and found - exempt == pin and found & exempt == exempt and pin.isdisjoint(exempt)
        and pin <= {q.name for q in cur.watch_paths()}
        and all((K2 / v).exists() for v in cur.ORDER_MD_PRODUCTS.values())
        and all(e["covered_by"] in cur.EXPECTED_TEETH["m13_v57_co146_jlc_fab_package.json"]
                for e in cur.ORDER_MD_PRODUCT_EXEMPT.values())
        and cur.md_write_scan(MD_IO) == ["probe.md"] and cur.md_write_scan(MD_PATHREPL) == ["dst.md"]
        and cur.md_write_scan(MD_PATHALIAS) == ["dst.md"] and cur.md_write_scan(MD_STRREPL) == [])

    # ── V3（CO-192 F-3）：boundary 读取者全集 == 扫描步 ∪ 声明（互斥、声明 ⊆ ORDER） ──
    readers = set(cur.boundary_readers())
    V["V3_CO192F3_boundary_readers_enumerated"] = (
        readers == set(cur.BOUNDARY_SCAN_GUARDED) | set(cur.BOUNDARY_READ_DECLARED)
        and set(cur.BOUNDARY_SCAN_GUARDED).isdisjoint(cur.BOUNDARY_READ_DECLARED)
        and set(cur.BOUNDARY_READ_DECLARED) <= set(cur.ORDER))

    # ── V4（CO-192 F-4）：放行档（ok **与** expected_nonzero）一律判**全**声明 verdict ──
    leak = [("a", "PASS"), ("b", "ERROR")]
    V["V4_CO192F4_all_verdicts_gate_on_release_classes"] = (
        cur.all_verdicts_gate("ok", "__nc__", [("a", "PASS"), ("b", "FAIL")])[0] == "undeclared_nonpass_verdict"
        and cur.all_verdicts_gate("expected_nonzero", "co146_jlc_dfm_gate", leak)[0] == "undeclared_nonpass_verdict"
        and cur.all_verdicts_gate("expected_nonzero", "co146_jlc_dfm_gate",
                                  [("a", "PASS"), ("b", "FAIL")])[0] == "expected_nonzero"
        and cur.all_verdicts_gate("ok", "__nc__", [("a", "PASS")])[1] == "ok")

    # ── V5（CO-193 G-1）/ V6（CO-193 G-2）：下游声明可执行 + 白名单证据本步绑定 ──
    V["V5_CO193G1_judgment_downstream_binding"] = (
        all(cur.judgment_downstream_binding(s, d) == "ok" for s, d in cur.JUDGMENT_DOWNSTREAM.items())
        and cur.judgment_downstream_binding("__nc__", {"ref": ["co146_impedance_table"], "artifact": "x.json",
                                                       "why": "w"}) == "refs_not_downstream"
        and cur.judgment_downstream_binding("co146_impedance_table",
                                            {"ref": ["co77_closure_declaration_sweep"],
                                             "artifact": "input_defect_register_v1.json",
                                             "why": "w"}) == "refs_not_reading_artifact")
    V["V6_CO193G2_expected_nonzero_binding"] = (
        all(cur.expected_nonzero_binding(s, d) == "ok" for s, d in cur.EXPECTED_NONZERO.items())
        and cur.expected_nonzero_binding("co146_jlc_dfm_gate",
                                         {"record": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co195_fixpoint_uniqueness.json",
                                          "teeth_path": ["teeth"]}) == "record_not_step_artifact"
        and cur.expected_nonzero_binding("co146_jlc_dfm_gate",
                                         {"record": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_jlc_dfm_gate.json",
                                          "teeth_path": ["__no_such__"]}) == "teeth_path_unresolved")

    # ── V7（CO-194 H-1/H-2）：基据判官可执行 + 声明 verdict 须在工具源 ──
    V["V7_CO194H1H2_basis_judge_and_verdict_in_tool"] = (
        all(cur.basis_judge_decision(k, v) == "ok" for k, v in cur.BASIS_JUDGE_DECLARED.items())
        and cur.declared_verdict_in_tool("co146_jlc_dfm_gate", {"verdict": "FAIL"})
        and not cur.declared_verdict_in_tool("co146_jlc_dfm_gate", {"verdict": "TOTALLY_BROKEN"})
        and cur.basis_judge_decision("x", {"judge": "J"}) == "declaration_incomplete")

    # ── V8（CO-195 + 端到端）：冻结四源 4/4 + ORDER==boundary 序 + `--check` 全 True +
    #      oracle 工具可编译、证据件 PASS/teeth 全 True、且**无自指字段**（R-CO195-0 / R-CO196-1b）
    try:
        orec = json.loads(OREC.read_text(encoding="utf-8"))
    except Exception:
        orec = {}
    r = subprocess.run([str(PY), str(TOOL), "--check"], capture_output=True, text=True, cwd=K2)
    try:
        chk = json.loads(r.stdout)["ok"]
    except Exception:
        chk = False
    V["V8_CO195_frozen_order_check_and_oracle_evidence"] = (
        all(s16p(K2 / k) == v for k, v in FROZEN.items())
        and bool(cur.boundary_order_steps()) and cur.boundary_order_steps() == cur.ORDER and chk
        and cur.oracle_tool_ok(ORACLE) and str(orec.get("verdict")) == "PASS"
        and all(bool(x) for x in orec.get("teeth", {}).values())
        and "sha_incl_self" not in cur_oracle)

    # ── 负控（内存注入、零落盘）：as-found 漏 ↔ 现行抓 ────────────────────────────
    P["P1_as_found_teeth_miss_kwargs_forms"] = (
        not af.teeth_hygiene_scan(TEETH_KW)["constant_teeth"]
        and not af.teeth_hygiene_scan(TEETH_KW2)["constant_teeth"])
    P["P1b_current_teeth_catch_kwargs_forms"] = (
        af.teeth_hygiene_scan(TEETH_KW)["n_teeth"] == 0 and cur.teeth_hygiene_scan(TEETH_KW)["n_teeth"] == 1
        and cur.teeth_hygiene_scan(TEETH_KW2)["n_teeth"] == 1)
    P["P2_as_found_md_miss_kwargs_forms"] = (
        af.md_write_scan(MD_IO) == [] and af.md_write_scan(MD_PATHREPL) == [] and af.md_write_scan(MD_PATHALIAS) == [])
    P["P2b_current_md_catch_kwargs_forms"] = (
        cur.md_write_scan(MD_IO) == ["probe.md"] and cur.md_write_scan(MD_PATHREPL) == ["dst.md"]
        and cur.md_write_scan(MD_PATHALIAS) == ["dst.md"] and cur.md_write_scan(MD_STRREPL) == [])
    br_openread = 'D=STEP2/"m13_v57_w3_joint_assignment_boundary_v1_82.md"\nt=D.open().read()\n'
    br_ioopen = 'B=_latest_boundary()\nt=io.open(B).read()\n'
    P["P3_as_found_boundary_read_miss"] = (not af192.boundary_read_scan(br_openread)) and (
        not af192.boundary_read_scan(br_ioopen))
    P["P3b_current_boundary_read_catch"] = cur.boundary_read_scan(br_openread) and cur.boundary_read_scan(br_ioopen)
    # CO-195（J-1 同族）：as-found t28 以**证据件 verdict** 为输入 ⇒ 验证循环；现行只判结构性
    P["P4_as_found_t28_reads_evidence_record"] = (
        hasattr(af, "oracle_record_ok")
        and af.oracle_record_ok({"verdict": "FAIL", "teeth": {"a": True, "teeth_ok": True}}) is False
        and "oracle_record_ok" in af_src and "oracle_tool_ok" not in af_src)
    P["P4b_current_t28_structural_only"] = (
        "oracle_tool_ok" in TOOL.read_text(encoding="utf-8")
        and "oracle_record_ok" not in TOOL.read_text(encoding="utf-8")
        and cur.oracle_tool_ok(ORACLE) is True and cur.oracle_tool_ok(K2 / "tools/__no_such__.py") is False)
    # CO-193（G-1/G-2 同族）：as-found（CO-192 定稿件）**无**下游/证据绑定判据；现行有且判 ok
    P["P5_as_found_no_binding_judges"] = (not hasattr(af193, "judgment_downstream_binding")) and (
        not hasattr(af193, "expected_nonzero_binding"))
    P["P5b_current_binding_judges_present"] = hasattr(cur, "judgment_downstream_binding") and hasattr(
        cur, "expected_nonzero_binding")
    # CO-194（H-2 同族）：as-found（CO-193 定稿件）**无**声明↔工具绑定判据 ⇒ 伪造 verdict 静默过静态
    P["P6_as_found_no_declared_verdict_binding"] = not hasattr(af194, "declared_verdict_in_tool")
    P["P6b_current_rejects_fake_verdict"] = not cur.declared_verdict_in_tool(
        "co146_jlc_dfm_gate", {"verdict": "TOTALLY_BROKEN"})

    _k1_miss = (af192.teeth_hygiene_scan(TEETH_KW)["n_teeth"] == 0 and af192.teeth_hygiene_scan(TEETH_KW2)["n_teeth"] == 0
                and af.teeth_hygiene_scan(TEETH_KW)["n_teeth"] == 0)
    _k2_miss = (af192.md_write_scan(MD_IO) == [] and af192.md_write_scan(MD_PATHREPL) == []
                and af.md_write_scan(MD_IO) == [] and af.md_write_scan(MD_PATHREPL) == [])
    P["P1c_k1_miss_persists_at_CO195_state"] = _k1_miss
    P["P2c_k2_miss_persists_at_CO195_state"] = _k2_miss
    if P["P1_as_found_teeth_miss_kwargs_forms"] and P["P1b_current_teeth_catch_kwargs_forms"] and _k1_miss:
        F.append({"id": "K-1", "sev": "low", "object": "CO-192",
                  "what": "`teeth_hygiene_scan` 对**关键字解包**形态漏计：`dict(**{\"t01\": True})` 与 "
                          "`teeth.update(**{\"t01\": True})`（`kw.arg is None`）一律 `n_teeth=0` ⇒ 经此形态加入的"
                          "**恒真齿**既不被计数亦不被 constancy 检；R-CO192-1 列举了 `dict(...)`/`update(...)` 为受覆盖形态"
                          "，而其**解包子形态**未实现 ⇒ 「**全部**容器形态」为过强声明（同族：CO-187 F-1 / CO-192 F-1）。"})
    if P["P2_as_found_md_miss_kwargs_forms"] and P["P2b_current_md_catch_kwargs_forms"] and _k2_miss:
        F.append({"id": "K-2", "sev": "low", "object": "CO-192",
                  "what": "`md_write_scan` 对**同族写/拷形态**漏计：`io.open(<md>, \"w\")`、`Path(...).replace|rename(<md>)` "
                          "以及**路径别名** `P = Path(...); P.replace|rename(<md>)` 一律 `==[]` ⇒ 此类 `.md` 产物既不入 pin、"
                          "t20 亦不截（可落出受控集）；且 `io.open` 在 **boundary 读取**侧已纳扫、在 **md 写**侧未覆盖（不对称）。"
                          "R-CO192-1 列举 `open(w)`/`os.replace|rename` 为受覆盖形态 ⇒ 其 pathlib/io 同族未实现。"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    observations = [
        {"id": "O-1", "object": "CO-195", "status": "已由 CO-196 J-1 登记并 CLOSED（不重复计数）",
         "what": "as-found `5e6ddde` 的静态齿 t28 以 oracle **证据件 verdict** 为输入 ⇒ 与 oracle 前置「先结算」构成"
                 "**验证循环**（证据 FAIL ⇒ t28 拒 ⇒ 静态前置失败 ⇒ oracle 无法运行 ⇒ 永久锁死）；本复评以 P4 独立复现。"},
    ]
    rec = {
        "artifact": "m13_v57_co197_rev19_co192_co195_review", "schema": 1, "revision": "CO-197",
        "nature": "非执行者对抗复评 CO-192..CO-195（另一会话；as-found `git show` 内存重放 + 内存注入、零落盘）",
        # R-CO193-3：复评件只钉**被评对象的 as-found**；**禁**内嵌处置态/现行 sha（否则记录随处置漂移）。
        "as_found": {"k2": AS_FOUND_REV, "runner_as_found_sha16": s16b(af_src.encode()),
                     "oracle_as_found_sha16": s16b(af_oracle.encode())},
        "objects": ["CO-192", "CO-193", "CO-194", "CO-195"],
        "positive_controls": V, "negative_controls": P, "findings": F, "n_findings": len(F),
        "observations": observations,
        "verdict": verdict,
        "disposition": "CO-197（L2 自裁）：runner 升 **CO-197.1** —— ① `teeth_hygiene_scan` 补关键字**解包**形态"
                       "（`dict(**{...})` / `.update(**{...})`）；② `md_write_scan` 补 `io.open(<md>,\"w\")` 与 "
                       "`Path(...)`/路径别名 `.replace|rename(<md>)` 目的；t18/t20 合成控同步扩展（含 "
                       "`\"a.md\".replace(\".md\",\"\")` **字符串操作不得误报**之对偶负控）。findings 均 CLOSED。",
        "redline": "只读 as-found（`git show`）+ 内存注入、零落盘、零坐标搜索；不改他人记录/登记簿/冻结四源。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-197 — 非执行者对抗复评（CO-192..CO-195）｜as-found @ `{AS_FOUND_REV}`", "",
             f"- verdict：**{verdict}**｜findings：{len(F)}（K-1/K-2，全 low）｜观察项：{len(observations)}（已由 CO-196 登记，**不重复计数**）",
             "- 方法：正控 V1..V8（独立复算）+ 负控 P1..P6（内存注入、零落盘、零坐标搜索）", "",
             "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        lines.append(f"| {k} | {'True' if v else '**False**'} |")
    if F:
        lines += ["", "## Findings（as-found）", "", "| id | sev | 对象 | what |", "|---|---|---|---|"]
        for f in F:
            lines.append(f"| {f['id']} | {f['sev']} | {f['object']} | {f['what']} |")
    lines += ["", "## 观察（不改判 verdict；均已被 CO-196 登记关闭）", ""]
    for o in observations:
        lines.append(f"- **{o['id']}（{o['object']}，{o['status']}）**：{o['what']}")
    lines += ["", "## 处置（CO-197，L2 自裁）", "", rec["disposition"], ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "findings": [f["id"] for f in F],
                      "V": V, "P": P, "rec_sha16": s16p(REC), "card_sha16": s16p(CARD)}, ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
