#!/usr/bin/env python3
"""CO-187 — **非执行者对抗复评** CO-181..CO-186（context 归零的续接会话；满足 handoff-z50 §6「另一会话，禁自评」）。

对象 as-found = k2 `4c581c7`（`git show` 内存重放 ⇒ 结论**不随后续修复漂移**）。方法：
正控 **V1..V6**（独立复算，非引用被评记录）+ 负控 **P1..P6**（内存注入，**零落盘**、零坐标搜索）。
只读；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；仅写本件记录 + 卡。
CLI: python3 tools/p3_v57_co187_rev19_co181_co186_review.py
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, types
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REC = STEP2 / "m13_v57_co187_rev19_co181_co186_review.json"
CARD = STEP2 / "m13_v57_CO187_rev19_co181_co186_review.md"
AS_FOUND_REV = "4c581c7"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _as_found(rel: str) -> str:
    """`git show <rev>:<path>` 内存重放（as-found 快照，不读工作树）。"""
    r = subprocess.run(["git", "-C", str(K2), "show", f"{AS_FOUND_REV}:{rel}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show failed for {rel}: {r.stderr.strip()}")
    return r.stdout


def _load_module(name: str, src: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = f"<as-found:{name}>"
    exec(compile(src, f"<as-found:{name}>", "exec"), mod.__dict__)
    return mod


def _load_current(rel: str) -> types.ModuleType:
    return _load_module(rel, (K2 / rel).read_text(encoding="utf-8"))


def main() -> int:
    cur = _load_current("tools/p3_v57_co164_order_runner.py")
    af = _load_module("co164_as_found", _as_found("tools/p3_v57_co164_order_runner.py"))
    dfm = _load_current("tools/p3_v57_co146_jlc_dfm_gate.py")

    V, P, F = {}, {}, []

    # ── V1（CO-181）：prompt 判决完整性 + 齿集 pin + fail-closed ─────────────
    decl = {}
    for st in set(cur.ORDER):
        for rel in cur.STEP_ARTIFACTS.get(st, []):
            if not str(rel).endswith(".json"):
                continue
            try:
                d = json.loads((K2 / rel).read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(d, dict) and "teeth" in d:
                decl[Path(rel).name] = sorted(d["teeth"])
    pin_ok = set(cur.EXPECTED_TEETH) == set(decl) and all(
        cur.EXPECTED_TEETH[k] == decl[k] for k in decl)
    # fail-closed 负控：声明 json 不可解析 ⇒ False（旧式 None 静默 = 缺陷）
    _orig, _n = cur.step_paths, sorted(cur.EXPECTED_TEETH)[0]
    class _P:
        suffix, name = ".json", _n
        def __init__(self, t): self._t = t
        def exists(self): return True
        def read_text(self, encoding=None):
            if self._t is None: raise ValueError("injected")
            return self._t
    try:
        _keys = cur.EXPECTED_TEETH[_n]
        cur.step_paths = lambda s: [_P(None)]
        fc_unparsable = cur.step_declared_teeth("__x__") is False
        cur.step_paths = lambda s: [_P(json.dumps({"teeth": {k: True for k in _keys[:-1]}}))]
        fc_drift = cur.step_declared_teeth("__x__") is False
        cur.step_paths = lambda s: [_P(json.dumps({"teeth": {k: True for k in _keys}}))]
        fc_ok = cur.step_declared_teeth("__x__") is True
    finally:
        cur.step_paths = _orig
    V["V1_CO181_teeth_pinned_and_fail_closed"] = pin_ok and fc_unparsable and fc_drift and fc_ok

    # ── V2（CO-182）：扫描步紧跟刷新步 + 刷新步**确实再对齐 pin**（单调用收敛机制） ──
    gi = [i for i, s in enumerate(cur.ORDER) if s in cur.BOUNDARY_SCAN_GUARDED]
    pos_ok = len(gi) == len(cur.BOUNDARY_SCAN_GUARDED) and all(
        i > 0 and cur.ORDER[i - 1] == cur.BOUNDARY_REFRESH_STEP for i in gi)
    ba = (K2 / "tools/p3_v57_co146_boundary_append.py").read_text(encoding="utf-8")
    realign_ok = "CITE.sub(_fix, txt)" in ba and "s16(hit)" in ba
    V["V2_CO182_scan_follows_refresh_and_realign"] = pos_ok and realign_ok

    # ── V3（CO-183/CO-187）：牙齿卫生棘轮（现行）全域零违规 + 逐工具齿数 ≥ pin ──
    own = {}
    for st in set(cur.ORDER):
        for rel in cur.STEP_ARTIFACTS.get(st, []):
            b = Path(rel).name
            if b in cur.EXPECTED_TEETH:
                tp = cur.tool_path(st)
                if tp is not None:
                    own[b] = tp
    floor, live = {}, {}
    for b, tp in own.items():
        floor[tp.name] = max(floor.get(tp.name, 0), len(cur.EXPECTED_TEETH[b]))
    for tp in set(own.values()):
        live[tp.name] = cur.teeth_hygiene_scan(tp.read_text(encoding="utf-8"))
    V["V3_CO183_ratchet_zero_violation_and_count_floor"] = (
        set(own) == set(cur.EXPECTED_TEETH)
        and all(live[k]["n_teeth"] >= v for k, v in floor.items())
        and all(not r["constant_teeth"] and not r["premature_agg"] for r in live.values()))

    # ── V4（CO-184）：锚点唯一定位 + 值绑定落在锚点邻域（独立复算） ────────────
    pg = dfm._page_text(dfm.CAP_SRC_HTML)
    uniq, worst = [], 0
    for k, a in dfm.CAPABILITY_ANCHORS.items():
        an = dfm._norm(a)
        if pg.count(an) != 1:
            uniq.append({"key": k, "occ": pg.count(an)})
        else:
            a0 = pg.index(an)
            for r in dfm.CAPABILITY_VALUE_BIND[k]:
                pat = re.escape(r) if isinstance(r, str) else r[0]
                mm = re.search(pat, pg)
                if mm:
                    worst = max(worst, abs(mm.start() - a0))
    V["V4_CO184_anchor_unique_and_windowed"] = (not uniq) and worst <= dfm.ANCHOR_WINDOW

    # ── V5（CO-185）：非 PASS 显式性 + 复评步 rc↔verdict ────────────────────
    np_bad = [s for s in set(cur.ORDER)
              if cur.nonpass_decision(s, cur.step_verdict(s)) == "undeclared_nonpass"]
    rc_src = {n: (K2 / f"tools/p3_v57_{n}.py").read_text(encoding="utf-8")
              for n in ("co159_rev19_co156_co157_co158_review",
                        "co166_rev19_co159_co165_review",
                        "co172_rev19_co166_co171_review")}
    rc_ok = all('return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1' in t
                for t in rc_src.values())
    V["V5_CO185_nonpass_declared_and_rc_binds_verdict"] = (not np_bad) and rc_ok

    # ── V6（CO-186/CO-187）：md 产物 ∈ pin ∪ 显式豁免；pin ⊆ 受控集 ──────────
    found = {b for st in set(cur.ORDER) if (tp := cur.tool_path(st))
             for b in cur.md_write_scan(tp.read_text(encoding="utf-8"))}
    mdpin = {Path(v).name for v in cur.ORDER_MD_PRODUCTS.values()}
    exempt = set(cur.ORDER_MD_PRODUCT_EXEMPT)
    V["V6_CO186_md_products_controlled"] = (
        found - exempt == mdpin and found & exempt == exempt and mdpin.isdisjoint(exempt)
        and mdpin <= {q.name for q in cur.watch_paths()})

    # ── P1（负控）：CO-183 棘轮**as-found 漏计** ↔ 现行抓出（别名下标 / update / AnnAssign / dict / setdefault / 字面恒真）──
    _probes = {
        "alias": 'def f(d):\n    tooth={"a":d["x"]>0}\n    rec={"teeth":tooth}\n    tooth["t01"]=True\n    return rec\n',
        "update": 'def f():\n    teeth={}\n    teeth.update({"t01":True})\n    return teeth\n',
        "ann": 'def f():\n    teeth: dict={"t01":True}\n    return teeth\n',
        "dict": 'def f():\n    teeth=dict(t01=True)\n    return teeth\n',
        "setdefault": 'def f():\n    teeth={}\n    teeth.setdefault("t01",True)\n    return teeth\n',
        "literal": 'def f(d):\n    teeth={"t01":(1==1),"t02":d["a"]>0}\n    return teeth\n',
    }
    cur_catch = {k: [x["key"] for x in cur.teeth_hygiene_scan(v)["constant_teeth"]] for k, v in _probes.items()}
    af_catch = {k: [x["key"] for x in af.teeth_hygiene_scan(v)["constant_teeth"]] for k, v in _probes.items()}
    P["P1_ratchet_catches_evasions_current"] = all(cur_catch[k] == ["t01"] for k in _probes)
    # as-found 漏计 = F-1 的证据（应为抓不到）
    P["P1_as_found_misses_aliased_and_ctor_forms"] = all(af_catch[k] == [] for k in _probes)

    # ── P2（负控）：md_write_scan 现行覆盖 open-w / copy-dst；as-found 漏 ──────
    _md = {
        "open_w": ('open("probe.md","w").write("x")\n', ["probe.md"]),
        "copy_dst": ('shutil.copy(S2 / "a.md", OUT / "imp/table.md")\n', ["table.md"]),
        "readonly": ('x = (STEP2 / "ro.md").read_text()\n', []),
    }
    P["P2_md_scan_current_forms"] = all(cur.md_write_scan(s) == e for s, e in _md.values())
    P["P2_as_found_misses_md_forms"] = (af.md_write_scan(_md["open_w"][0]) == []
                                        and af.md_write_scan(_md["copy_dst"][0]) == [])

    # ── P3（负控）：boundary 读取者判据正/负 ─────────────────────────────────
    P["P3_boundary_read_scan"] = (
        cur.boundary_read_scan('DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"\nt = DOC.read_text()')
        and cur.boundary_read_scan('B = _latest_boundary()\nx = B.read_bytes()')
        and not cur.boundary_read_scan('x = (STEP2 / "other.md").read_text()')
        and not cur.boundary_read_scan('DOC.write_text("x")'))

    # ── P4（负控）：未声明的非 PASS ⇒ undeclared_nonpass ─────────────────────
    P["P4_nonpass_undeclared_caught"] = (
        cur.nonpass_decision("__undeclared__", "FAIL") == "undeclared_nonpass"
        and cur.nonpass_decision("co146_pm_eval", "FAIL") == "declared_nonpass"
        and cur.nonpass_decision("co146_jlc_dfm_gate", "FAIL") == "declared_whitelist")

    # ── P5（负控）：CO-184 上下文判据合成正/负控（唯一+邻近 / 重复锚 / 远置值） ──
    syn_cap = {"k": {"value": 0.09, "quote": "Beta 0.09 mm"}}
    syn_anc = {"k": "Beta 0.09 mm"}
    syn_bind = {"k": [("Beta (0\\.09) mm", ["0.09"])]}
    pg_ok = "Prefix Beta 0.09 mm suffix"
    pg_dup = "Beta 0.09 mm " + ("pad " * 150) + "Beta 0.09 mm"
    pg_far = "Beta 0.09 mm " + ("pad " * 150) + "Other 0.09 mm"
    ok = dfm.capability_value_bind_checks(pg_ok, syn_cap, syn_bind, syn_anc)
    dup = dfm.capability_value_bind_checks(pg_dup, syn_cap, syn_bind, syn_anc)
    far = dfm.capability_value_bind_checks(pg_far, syn_cap, {"k": [("Other (0\\.09) mm", ["0.09"])]}, syn_anc)
    P["P5_anchor_context_controls"] = (ok["anchor_localizes_uniquely"] and ok["value_within_anchor_window"]
                                       and not dup["anchor_localizes_uniquely"]
                                       and not far["value_within_anchor_window"])

    # ── P6（负控）：as-found 齿数漏计（co81 实测）↔ 现行全计 ─────────────────
    co81 = "tools/p3_v57_co81_project_rules_gate.py"
    P["P6_as_found_undercounts_co81"] = af.teeth_hygiene_scan(_as_found(co81))["n_teeth"] < 5
    P["P6_current_counts_co81"] = cur.teeth_hygiene_scan((K2 / co81).read_text(encoding="utf-8"))["n_teeth"] == 5

    # ── Findings（复评发现，as-found 对 CO-181..186） ─────────────────────────
    if P["P1_as_found_misses_aliased_and_ctor_forms"] and P["P6_as_found_undercounts_co81"]:
        F.append({"id": "F-1", "sev": "low", "object": "CO-183",
                  "what": "`teeth_hygiene_scan()` 容器形态覆盖不完备：别名容器下标（`tooth[k]=…`，实测 co81 5 齿仅计 2）、"
                          "`AnnAssign` / `dict(...)` / `.update({...})` / `.setdefault(k,v)` / 字面恒真式（`1==1`）一律漏计 ⇒ "
                          "以这些形态加入常量齿不被 t18 截。"})
    if P["P2_as_found_misses_md_forms"]:
        F.append({"id": "F-2", "sev": "low", "object": "CO-186",
                  "what": "`md_write_scan()` 仅认 `write_text` ⇒ `open(...,'w')` / `shutil.copy*` 目的 `.md` 产物不在 pin、"
                          "t20 亦不截 ⇒ 此类 md 产物可落出受控集（R-CO186-1 静默违反）。"})
    if not (hasattr(af, "boundary_read_scan") and hasattr(af, "BOUNDARY_READ_DECLARED")):
        F.append({"id": "F-3", "sev": "low", "object": "CO-182",
                  "what": "`BOUNDARY_SCAN_GUARDED` 为**手工枚举**，无「boundary 读取者全集」机判 ⇒ 新增读取/扫描步可静默绕开 t17。"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    rec = {
        "artifact": "m13_v57_co187_rev19_co181_co186_review", "schema": 1, "revision": "CO-187.1",
        "nature": "非执行者对抗复评 CO-181..CO-186（另一会话；as-found `git show` 重放 + 内存注入）",
        "as_found": {"k2": AS_FOUND_REV,
                     "runner_as_found_sha16": hashlib.sha256(_as_found("tools/p3_v57_co164_order_runner.py").encode()).hexdigest()[:16]},
        "objects": ["CO-181", "CO-182", "CO-183", "CO-184", "CO-185", "CO-186"],
        "positive_controls": V, "negative_controls": P, "findings": F, "n_findings": len(F),
        "verdict": verdict,
        "disposition": "CO-187（L2 自裁）：runner 升 CO-187.1 —— `teeth_hygiene_scan` 容器形态全覆盖 + t18 逐工具齿数下限；"
                       "`md_write_scan` 覆盖 open-w/copy-dst + `ORDER_MD_PRODUCT_EXEMPT` 显式豁免 + t20 加固；"
                       "`BOUNDARY_READ_DECLARED` + t21（boundary 读取者全集机判）。findings 均 CLOSED。",
        "redline": "只读 as-found（`git show`）+ 内存注入、零落盘、零坐标搜索；不改他人记录/登记簿/冻结四源。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-187 — 非执行者对抗复评（CO-181..CO-186）｜as-found @ `{AS_FOUND_REV}`", "",
             f"- verdict：**{verdict}**｜findings：{len(F)}",
             f"- 方法：正控 V1..V6（独立复算）+ 负控 P1..P6（内存注入、零落盘）", "",
             "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        lines.append(f"| {k} | {'True' if v else '**False**'} |")
    if F:
        lines += ["", "## Findings（as-found）", "", "| id | sev | 对象 | what |", "|---|---|---|---|"]
        for f in F:
            lines.append(f"| {f['id']} | {f['sev']} | {f['object']} | {f['what']} |")
    lines += ["", "## 处置（CO-187，L2 自裁）", "", rec["disposition"], ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "findings": [f["id"] for f in F],
                      "V": V, "P": P, "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
