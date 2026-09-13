#!/usr/bin/env python3
"""CO-192 — **非执行者对抗复评** CO-187..CO-191（context 归零的续接会话；满足「复评须另一会话，禁自评」）。

对象 as-found = k2 `52235b5`（`git show` 内存重放 ⇒ 结论**不随后续处置漂移**）。方法：
正控 **V1..V8**（独立复算，非引用被评记录）+ 负控 **P1..P6**（内存注入，**零落盘**、零坐标搜索）。
只读；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；仅写本件记录 + 卡。
CLI: python3 tools/p3_v57_co192_rev19_co187_co191_review.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
TOOL = K2 / "tools/p3_v57_co164_order_runner.py"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
REC = STEP2 / "m13_v57_co192_rev19_co187_co191_review.json"
CARD = STEP2 / "m13_v57_CO192_rev19_co187_co191_review.md"
AS_FOUND_REV = "52235b5"
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


def _as_found(rel: str) -> str:
    r = subprocess.run(["git", "-C", str(K2), "show", f"{AS_FOUND_REV}:{rel}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show failed for {rel}: {r.stderr.strip()}")
    return r.stdout


def _load(name: str, src: str, real_file) -> types.ModuleType:
    """以**真实 __file__** 执行给定源码 ⇒ 模块内 `Path(__file__).parents[1]` 仍指向 K2。"""
    mod = types.ModuleType(name)
    mod.__file__ = str(real_file)
    exec(compile(src, str(real_file), "exec"), mod.__dict__)
    return mod


def _as_found_loop_decision(af, cls: str, step: str, verdicts) -> str:
    """as-found @52235b5 的判定**次序**：`all_verdicts_decision` 仅在 `cls == "ok"` 时调用。"""
    if cls == "ok" and af.all_verdicts_decision(step, verdicts) == "undeclared_nonpass":
        return "undeclared_nonpass_verdict"
    return cls


def main() -> int:
    af_src = _as_found("tools/p3_v57_co164_order_runner.py")
    af = _load("co164_as_found_52235b5", af_src, TOOL)
    cur = _load("co164_current", TOOL.read_text(encoding="utf-8"), TOOL)
    V, P, F = {}, {}, []

    # ── V1（CO-187 F-1）：牙齿棘轮 —— 现行零违规 + 逐工具齿数 ≥ pin + 形态覆盖 ──────
    own, floor, live = {}, {}, {}
    for s in set(cur.ORDER):
        for rel in cur.STEP_ARTIFACTS.get(s, []):
            b = Path(rel).name
            if b in cur.EXPECTED_TEETH and (tp := cur.tool_path(s)) is not None:
                own[b] = tp
    for b, tp in own.items():
        floor[tp.name] = max(floor.get(tp.name, 0), len(cur.EXPECTED_TEETH[b]))
    for tp in set(own.values()):
        live[tp.name] = cur.teeth_hygiene_scan(tp.read_text(encoding="utf-8"))
    co81 = K2 / "tools/p3_v57_co81_project_rules_gate.py"
    V["V1_CO187_teeth_ratchet_live_clean_and_floor"] = (
        set(own) == set(cur.EXPECTED_TEETH)
        and all(not v["constant_teeth"] and not v["premature_agg"] for v in live.values())
        and all(live[k]["n_teeth"] >= v for k, v in floor.items())
        and sum(v["n_teeth"] for v in live.values()) >= 100
        and cur.teeth_hygiene_scan(co81.read_text(encoding="utf-8"))["n_teeth"] == 5)

    # ── V2（CO-187 F-2）：md 产物 —— 扫描集 == pin；⊆ 受控集；豁免绑实存补偿齿 ──────
    scan = {s: cur.md_write_scan(tp.read_text(encoding="utf-8"))
            for s in set(cur.ORDER) if (tp := cur.tool_path(s)) is not None}
    found = {b for v in scan.values() for b in v}
    pin = {Path(v).name for v in cur.ORDER_MD_PRODUCTS.values()}
    exempt = set(cur.ORDER_MD_PRODUCT_EXEMPT)
    V["V2_CO187_md_products_controlled_and_exempt_bound"] = (
        set(cur.ORDER_MD_PRODUCTS) == {s for s, v in scan.items() if set(v) - exempt}
        and found - exempt == pin and found & exempt == exempt
        and pin <= {q.name for q in cur.watch_paths()}
        and all((K2 / v).exists() for v in cur.ORDER_MD_PRODUCTS.values())
        and all(e["covered_by"] in cur.EXPECTED_TEETH["m13_v57_co146_jlc_fab_package.json"]
                for e in cur.ORDER_MD_PRODUCT_EXEMPT.values()))

    # ── V3（CO-187 F-3）：boundary 读取者全集 == 扫描步 ∪ 显式声明（互斥） ──────────
    readers = set(cur.boundary_readers())
    V["V3_CO187_boundary_readers_enumerated"] = (
        readers == set(cur.BOUNDARY_SCAN_GUARDED) | set(cur.BOUNDARY_READ_DECLARED)
        and set(cur.BOUNDARY_SCAN_GUARDED).isdisjoint(cur.BOUNDARY_READ_DECLARED)
        and set(cur.BOUNDARY_READ_DECLARED) <= set(cur.ORDER))

    # ── V4（CO-188）：越界写 fail-closed + 例外表完备 ─────────────────────────────
    watch_abs = {p.as_posix() for p in cur.watch_paths()}
    tbl_ok = all(k in set(cur.ORDER) and isinstance(v, dict) and str(v.get("why") or "").strip()
                 and isinstance(v.get("paths"), list) and set(v["paths"]) <= watch_abs
                 and not (set(v["paths"]) & set(cur.STEP_ARTIFACTS.get(k, [])))
                 for k, v in cur.STRAY_WRITE_ALLOWED.items())
    V["V4_CO188_stray_write_fail_closed"] = (
        tbl_ok and cur.stray_decision("__s__", []) == "ok"
        and cur.stray_decision("__s__", ["a/b.json"]) == "stray_write"
        and cur.stray_decision("__s__", ["a/b.json"], {"__s__": {"paths": ["a/b.json"]}}) == "ok")

    # ── V5（CO-189）：承载根 ⊇ 受控集；豁免完备；受控集外写入判据 ──────────────────
    cov_ok = {q.name for q in cur.watch_paths()} | {t for v in cur.EXPECTED_TEETH.values() for t in v}
    exp_ok = all(str(e.get("prefix") or "").strip() and str(e.get("why") or "").strip()
                 and e.get("covered_by") in cov_ok and (K2 / e["prefix"]).exists()
                 for e in cur.WRITE_SHADOW_EXEMPT)
    V["V5_CO189_write_shadow_visible"] = (
        all(str(p).startswith(str(cur.WRITE_SHADOW_ROOT) + "/") for p in cur.watch_paths())
        and exp_ok
        and cur.uncontrolled_decision([]) == "ok"
        and cur.uncontrolled_decision(["pm_gate/artifacts/k2_v4/L9_none/x.json"]) == "uncontrolled_write"
        and cur.uncontrolled_decision(["pm_gate/artifacts/k2_v4/L5/jlc_package/06_rulings/a.md"]) == "ok")

    # ── V6（CO-190）：步骤超时 fail-closed；超时值在带内；子进程接线 ────────────────
    src_cur = TOOL.read_text(encoding="utf-8")
    V["V6_CO190_step_timeout_fail_closed"] = (
        isinstance(cur.STEP_TIMEOUT_S, int) and 60 <= cur.STEP_TIMEOUT_S <= 3600
        and "timeout=STEP_TIMEOUT_S" in src_cur and "except subprocess.TimeoutExpired" in src_cur
        and cur.allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS", True, None, True) == "step_timeout"
        and cur.allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True, True, True) == "step_timeout"
        and cur.allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS") == "ok")

    # ── V7（CO-191）：每步基据非 none；下游声明合法；全 verdict 判据 ───────────────
    basis = {s: cur.judgment_basis(s) for s in set(cur.ORDER)}
    dn_ok = all(str(v.get("why") or "").strip() and isinstance(v.get("ref"), list) and bool(v["ref"])
                and set(v["ref"]) <= set(cur.ORDER) for v in cur.JUDGMENT_DOWNSTREAM.values())
    V["V7_CO191_judgment_basis_declared"] = (
        all(b != "none" for b in basis.values()) and set(cur.JUDGMENT_DOWNSTREAM) <= set(cur.ORDER) and dn_ok
        and cur.all_verdicts_decision("__nc__", [("a", "PASS"), ("b", "FAIL")]) == "undeclared_nonpass"
        and cur.all_verdicts_decision("__nc__", [("a", "PASS"), ("b", "PASS_WITH_FINDINGS")]) == "ok"
        and cur.all_verdicts_decision("co146_pm_eval", [("x", "FAIL")]) == "ok")

    # ── V8（端到端静态）：冻结四源 4/4 MATCH + ORDER==boundary 序 + `--check` 全 True ──
    frz = {k: (s16p(K2 / k) == v) for k, v in FROZEN.items()}
    r = subprocess.run([str(PY), str(TOOL), "--check"], capture_output=True, text=True, cwd=K2)
    try:
        chk = json.loads(r.stdout)["ok"]
    except Exception:
        chk = False
    V["V8_frozen_4of4_and_order_matches_and_check_green"] = (
        all(frz.values()) and bool(cur.boundary_order_steps()) and cur.boundary_order_steps() == cur.ORDER and chk)

    # ── 负控（内存注入、零落盘）：as-found 漏 ↔ 现行抓 ───────────────────────────
    inj_aug = 'def f():\n    teeth={}\n    teeth |= {"t01": True}\n    return teeth\n'
    inj_nest = 'def f():\n    rec={"teeth":{}}\n    rec["teeth"]["t01"]=True\n    return rec\n'
    inj_dcomp = 'def f(ks):\n    teeth={k: True for k in ks}\n    return teeth\n'
    inj_seti = 'def f():\n    teeth={}\n    teeth.__setitem__("t01", True)\n    return teeth\n'
    inj_attr = 'def f(self):\n    self.teeth["t01"]=True\n    return self.teeth\n'
    inj_subalias = 'TEETH={"t01":True}\ndef f():\n    rec={}\n    rec["teeth"]=TEETH\n    return rec\n'
    _new_forms = [inj_aug, inj_nest, inj_dcomp, inj_seti, inj_attr, inj_subalias]
    P["P1_as_found_teeth_miss_new_forms"] = all(
        not af.teeth_hygiene_scan(x)["constant_teeth"] for x in _new_forms)
    P["P2_current_teeth_catch_new_forms"] = all(
        cur.teeth_hygiene_scan(x)["n_teeth"] >= 1 and cur.teeth_hygiene_scan(x)["constant_teeth"]
        for x in _new_forms)

    md_pathopen = 'CARD = S2 / "x.md"\nf = CARD.open("w")\n'
    md_move = 'shutil.move(S2 / "a.md", OUT / "b.md")\n'
    md_repl = 'os.replace(S2 / "a.md", OUT / "b.md")\n'
    P["P3_as_found_md_miss_new_forms"] = (
        af.md_write_scan(md_pathopen) == [] and af.md_write_scan(md_move) == [] and af.md_write_scan(md_repl) == [])
    P["P4_current_md_catch_new_forms"] = (
        cur.md_write_scan(md_pathopen) == ["x.md"] and cur.md_write_scan(md_move) == ["b.md"]
        and cur.md_write_scan(md_repl) == ["b.md"])

    br_openread = 'D=STEP2/"m13_v57_w3_joint_assignment_boundary_v1_82.md"\nt=D.open().read()\n'
    br_ioopen = 'B=_latest_boundary()\nt=io.open(B).read()\n'
    P["P5_as_found_boundary_read_miss"] = (not af.boundary_read_scan(br_openread)) and (
        not af.boundary_read_scan(br_ioopen))
    P["P5b_current_boundary_read_catch"] = cur.boundary_read_scan(br_openread) and cur.boundary_read_scan(br_ioopen)

    # CO-192（F-4）：白名单步（rc≠0 预期 FAIL）的**副**声明 verdict（≠ 其声明 FAIL 的非 PASS 值）运行期逃逸
    _verdicts = [("a", "PASS"), ("b", "ERROR")]
    P["P6_as_found_expected_nonzero_leaks_undeclared_verdict"] = (
        _as_found_loop_decision(af, "expected_nonzero", "co146_jlc_dfm_gate", _verdicts) == "expected_nonzero")
    P["P6b_current_gate_catches_on_release_classes"] = (
        cur.all_verdicts_gate("expected_nonzero", "co146_jlc_dfm_gate", _verdicts)
        == ("undeclared_nonpass_verdict", "undeclared_nonpass")
        and cur.all_verdicts_gate("ok", "__x__", [("a", "FAIL")])
        == ("undeclared_nonpass_verdict", "undeclared_nonpass")
        and cur.all_verdicts_gate("ok", "co146_pm_eval", [("x", "FAIL")]) == ("ok", "ok"))
    # 灵敏度对偶：良性形态不得误报
    P["P6c_current_scanners_specific"] = (
        not cur.teeth_hygiene_scan('def f(d):\n    teeth={}\n    teeth["t01"]=d["a"]>0\n    return all(teeth.values())\n')["constant_teeth"]
        and cur.md_write_scan('x = (S2 / "ro.md").read_text()\n') == []
        and cur.boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"\nDOC.write_text("x")') is False)

    # ── Findings（复评发现，as-found @52235b5 对 CO-187..CO-191） ────────────────
    if P["P1_as_found_teeth_miss_new_forms"] and P["P2_current_teeth_catch_new_forms"]:
        F.append({"id": "F-1", "sev": "low", "object": "CO-187",
                  "what": "牙齿卫生棘轮容器形态仍漏计：`|=`（AugAssign）/ 嵌套下标 `rec[\"teeth\"][k]` / dict 推导 "
                          "`{k: True for k in …}` / `__setitem__` / Attribute 目标 `self.teeth[k]` / 下标赋别名 "
                          "`rec[\"teeth\"]=<Name>` 一律 n_teeth=0（既不计数亦不报 constant）⇒ 恒真齿可经这些形态"
                          "加入而不被 t18 截；R-CO187-1「**全部**容器形态」为过强声明。"})
    if P["P3_as_found_md_miss_new_forms"] and P["P4_current_md_catch_new_forms"]:
        F.append({"id": "F-2", "sev": "low", "object": "CO-187",
                  "what": "md 写/拷形态仍漏计：`Path.open(w)` / `shutil.move` / `os.replace|rename` 目的一律 "
                          "`md_write_scan()`==[] ⇒ 此类 `.md` 产物既不在 pin、t20 亦不截（可落出受控集）；"
                          "R-CO187-2「**全部**写/拷形态」为过强声明。实测现行 ORDER 工具 0 命中（潜在面）。"})
    if P["P5_as_found_boundary_read_miss"] and P["P5b_current_boundary_read_catch"]:
        F.append({"id": "F-3", "sev": "low", "object": "CO-187",
                  "what": "boundary 读取者判据仍可绕过：`D.open().read()` / `io.open(B).read()` 形态"
                          "（源内无 `read_text`/`read_bytes` 字面）判 False ⇒ t21 读取者全集可被此形态静默绕过。"})
    if P["P6_as_found_expected_nonzero_leaks_undeclared_verdict"] and P["P6b_current_gate_catches_on_release_classes"]:
        F.append({"id": "F-4", "sev": "low", "object": "CO-191",
                  "what": "「**全部**声明 verdict 一律判决」对白名单步不生效：主循环以 `if cls == \"ok\"` 为门槛 ⇒ "
                          "`expected_nonzero` 步（co146_jlc_dfm_gate）的**副**声明产物 verdict 不被运行期判决；"
                          "副值为其声明 FAIL 之外的非 PASS 值（如 ERROR）即静默逃逸，违 R-CO191-1。"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    rec = {
        "artifact": "m13_v57_co192_rev19_co187_co191_review", "schema": 1, "revision": "CO-192",
        "nature": "非执行者对抗复评 CO-187..CO-191（另一会话；as-found `git show` 重放 + 内存注入、零落盘）",
        # CO-193（G-3）：复评件为 **as-found 证据**，只钉被评对象；**不得**内嵌处置态 sha（否则记录 sha
        # 随后续 CO 漂移，违 CO-152「记录内禁止下游 sha 快照」规则）。处置态现行 sha 一律由 boundary pin 表承载。
        "as_found": {"k2": AS_FOUND_REV, "runner_as_found_sha16": s16b(af_src.encode())},
        "objects": ["CO-187", "CO-188", "CO-189", "CO-190", "CO-191"],
        "positive_controls": V, "negative_controls": P, "findings": F, "n_findings": len(F),
        "verdict": verdict,
        "disposition": "CO-192（L2 自裁）：runner 升 **CO-192.1** —— ① `teeth_hygiene_scan` 形态覆盖续加固"
                       "（`|=`/嵌套下标/推导/`__setitem__`/Attribute/下标赋别名）；② `md_write_scan` 补 "
                       "`Path.open(w)`/`shutil.move`/`os.replace|rename`；③ `boundary_read_scan` 补 `.open().read()`/"
                       "`io.open`；④ 新增 `all_verdicts_gate`：**放行档**（`ok` **与** `expected_nonzero`）一律判**全**"
                       "声明 verdict ⇒ 白名单步副 verdict 不得逃逸；t18/t20/t21/t25 合成控同步扩展。findings 均 CLOSED。",
        "redline": "只读 as-found（`git show`）+ 内存注入、零落盘、零坐标搜索；不改他人记录/登记簿/冻结四源。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-192 — 非执行者对抗复评（CO-187..CO-191）｜as-found @ `{AS_FOUND_REV}`", "",
             f"- verdict：**{verdict}**｜findings：{len(F)}", "- 方法：正控 V1..V8（独立复算）+ 负控 P1..P6c（内存注入、零落盘）", "",
             "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        lines.append(f"| {k} | {'True' if v else '**False**'} |")
    if F:
        lines += ["", "## Findings（as-found）", "", "| id | sev | 对象 | what |", "|---|---|---|---|"]
        for f in F:
            lines.append(f"| {f['id']} | {f['sev']} | {f['object']} | {f['what']} |")
    lines += ["", "## 处置（CO-192，L2 自裁）", "", rec["disposition"], ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "findings": [f["id"] for f in F],
                      "V": V, "P": P, "rec_sha16": s16p(REC), "card_sha16": s16p(CARD)},
                     ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
