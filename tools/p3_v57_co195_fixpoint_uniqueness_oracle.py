#!/usr/bin/env python3
"""CO-195/CO-196 — **固定点唯一性（路径无关）oracle**（L2 自裁）。

缘起：co120 的 P5「下游快照」判据为**键名启发式**（廉价前置代理），其真正要保证的**语义**性质是：文档化复现序的
**不动点唯一**（CO-151 失效模式 = 「按序连跑两遍得**另一稳定不动点**，提交 pin 不可复现」）。键名判据无法直接判该
性质，且**值域判据经实测不可行**（35 条记录内嵌受控集未来 sha，但绝大多数是冻结历史件/自身产物的合法 pin ⇒ 误报）。
本 oracle 直接判**语义性质**：从**扰动态**启动规范序，要求收敛回**与规范态逐字节相同**的不动点。

CO-196（**触发已发生**：CO-195 的 I-2 缺陷即「自指/链式 pin 写法」实例 ⇒ 扩扰动量）：**多扰动量**（3 案）
—— A 登记簿 `meta.counts`；B 单个 ORDER 步记录注入；C **同时**注入（交互）。每案独立要求「收敛 + 目标件逐字节复原 +
排除自身快照复原」，且**任一案失败即停**（后续案不再在非规范态上开跑）。

方法（**自我保护**）：先**结算**（工作树先收敛为不动点，再作扰动实验）；每案 `finally` 无条件复原该案目标件，
**绝不留在扰动态**。含**判别力**合成控（唯一 vs 非唯一不动点模型）。
CLI: python3 tools/p3_v57_co195_fixpoint_uniqueness_oracle.py [--plan] [--max-iter 5]
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
RUNNER = K2 / "tools/p3_v57_co164_order_runner.py"
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
REC = STEP2 / "m13_v57_co195_fixpoint_uniqueness.json"
IMP = STEP2 / "m13_v57_co146_impedance_table.json"        # ORDER 步（co146_impedance_table）自持记录：每次全量重写
IMP_MD = STEP2 / "m13_v57_co146_impedance_table.md"     # CO-200（G-1）：同一步的 **md 卡片产物**（CO-186 起受控且入 pin）
# CO-202（L-4）：受控集含 **图（.svg）** 类别（CO-174 入 pin）—— 旧四案只扰 json/md ⇒ 补第 5 案（R-CO200-1 覆盖面=类别数）。
SVG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/03_stackup/JLC08161H_stackup.svg"
BOGUS_COUNTS = {"SPEC_DEFECT": 999, "PROVED_THRESHOLD": 999, "TOOL_DEFECT": 999,
                "IMPLEMENTATION_DEVIATION": 999, "OPEN": 7, "total": 999}
CASES = (
    {"id": "A_register_counts", "why": "登记簿 meta.counts（跨件 pin 链最敏感）", "targets": (REG,),
     "tooth": "t02_A_converged_and_restored"},
    {"id": "B_step_record", "why": "单个 ORDER 步自持记录（步内全量重写 ⇒ 应自愈）", "targets": (IMP,),
     "tooth": "t03_B_converged_and_restored"},
    {"id": "C_double", "why": "同时扰动（两件交互）", "targets": (REG, IMP),
     "tooth": "t04_C_converged_and_restored"},
    # CO-200（G-1）：**md 卡片产物**（CO-186 起受控并入 pin）此前**从未**被扰动实验行使 —— 旧三案只扰 json 记录。
    # 该项判「步是否**真正全量重写**其 md 产物」（追加式/增量式写 ⇒ 注入行残留 ⇒ 复原失败 ⇒ 停机）。
    {"id": "D_md_card_product", "why": "受控 md 卡片产物（步内全量重写 ⇒ 应自愈；追加式写即被本项抓）",
     "targets": (IMP_MD,), "tooth": "t08_D_md_restored"},
    # CO-202（L-4 / R-CO202-3）：受控 **图（.svg）** 产物类别（fab 步生成）—— 追加式写即被本项抓。
    {"id": "E_svg_product", "why": "受控 图（.svg）产物类别（fab 步全量重写 ⇒ 应自愈）",
     "targets": (SVG,), "tooth": "t09_E_svg_restored"},
)


def _load(name: str, path: Path) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def _s16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _snap_excl(cur, rec: Path) -> str:
    """判据快照 = `watch_paths()` **排除本记录自身**（CO-195 I-2：防自指 —— 本记录写回后自身字节即变，
    若计入则记录内的 `sha_canon` 永不等于其所在状态的实际 sha，且 pin 随记录改写漂移）。"""
    h = hashlib.sha256()
    for p in cur.watch_paths():
        if Path(p) == rec:
            continue
        h.update(Path(p).read_bytes() if Path(p).exists() else b"<missing>")
    return h.hexdigest()[:16]


def _run_order(cur, max_iter: int):
    r = subprocess.run([str(cur.PY), str(RUNNER), "--max-iter", str(max_iter)],
                       cwd=K2, capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except Exception:
        return r.returncode, None


def _fixpoint(fn, start, n: int = 300):
    x = start
    for _ in range(n):
        y = fn(x)
        if y == x:
            return x
        x = y
    return x


def uniqueness_discriminates() -> bool:
    """判别力负控：同一判据（两起点收敛值比较）须对**唯一**判 True、对**非唯一**（两不动点）判 False。"""
    uniq = lambda x: 42
    nonuniq = lambda x: (x if x in (0, 1) else 0)
    return (_fixpoint(uniq, 3) == _fixpoint(uniq, 7)) and \
           (_fixpoint(nonuniq, 0) != _fixpoint(nonuniq, 1))


def _inject(target: Path) -> None:
    """按目标件类型注入：登记簿改 `meta.counts`；ORDER 步记录加探针键（步将全量重写 ⇒ 应消失）。"""
    if target.suffix in (".md", ".svg"):     # CO-200 md / CO-202 svg（图）：注入**内容行**（步若全量重写 ⇒ 该行应消失）
        target.write_text(target.read_text(encoding="utf-8") + "\n<!-- CO-202 injection probe -->\n", encoding="utf-8")
        return
    d = json.loads(target.read_text(encoding="utf-8"))
    if target == REG:
        d["meta"]["counts"] = dict(BOGUS_COUNTS)
    else:
        d["__probe_196__"] = "INJECTED"
    target.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="只打印扰动计划（不改盘、不跑序）")
    ap.add_argument("--max-iter", type=int, default=5)
    a = ap.parse_args(argv)

    cur = _load("co164_runner", RUNNER)
    if a.plan:
        print(json.dumps({"mode": "plan", "cases": [{"id": c["id"], "why": c["why"],
                                                     "targets": [str(t.relative_to(K2)) for t in c["targets"]]}
                                                    for c in CASES],
                          "snapshot_scope": "watch_paths() - {本记录}",
                          "precondition": "先结算（工作树须已收敛为不动点）"}, ensure_ascii=False, indent=1))
        return 0

    t = {"t00_settle_converged": False, "t01_injections_effective": False,
         "t02_A_converged_and_restored": False, "t03_B_converged_and_restored": False,
         "t04_C_converged_and_restored": False, "t05_discriminates_path_dependence":
             uniqueness_discriminates(), "t06_self_exclusion_nonvacuous": False,
         "t07_no_residual_perturbation": False, "t08_D_md_restored": False,   # CO-200（G-1）
         "t09_E_svg_restored": False}                                        # CO-202（L-4）

    # ① 先结算：工作树须已是规范序不动点，否则测的是「结算」而非「路径无关」
    settle_rc, settle_json = _run_order(cur, a.max_iter)
    t["t00_settle_converged"] = (settle_rc == 0 and bool(settle_json) and bool(settle_json.get("converged")))

    canon_bytes = {str(p): p.read_bytes() for p in {tgt for c in CASES for tgt in c["targets"]}}
    sha_canon = _snap_excl(cur, REC)
    sha_incl = cur.snapshot()
    t["t06_self_exclusion_nonvacuous"] = (not REC.exists()) or (sha_canon != sha_incl)

    rows, all_inj_effective, aborted = [], True, None
    for idx, case in enumerate(CASES):
        tgts = list(case["targets"])
        saved = {str(p): p.read_bytes() for p in tgts}
        row = {"id": case["id"], "why": case["why"], "targets": [str(p.relative_to(K2)) for p in tgts]}
        try:
            for p in tgts:
                _inject(p)
            row["sha_perturbed"] = _snap_excl(cur, REC)
            row["injection_effective"] = (row["sha_perturbed"] != sha_canon)
            all_inj_effective = all_inj_effective and row["injection_effective"]
            rc, j = _run_order(cur, a.max_iter)
            row["order_rc"] = rc
            row["order_converged"] = bool(j) and bool(j.get("converged"))
            row["targets_byte_restored"] = {str(p): (p.read_bytes() == saved[str(p)]) for p in tgts}
            row["snapshot_restored"] = (_snap_excl(cur, REC) == sha_canon)
            row["restored"] = (row["order_converged"]
                               and all(row["targets_byte_restored"].values())
                               and row["snapshot_restored"])
        finally:
            for p in tgts:                      # 自我保护：每案无条件复原，绝不留在扰动态
                if p.read_bytes() != saved[str(p)]:
                    p.write_bytes(saved[str(p)])
        rows.append(row)
        t[case["tooth"]] = row["restored"]          # CO-200：齿名由 CASES 显式给出（新增案不再挤占既有齿名）
        if not row["restored"]:
            aborted = case["id"]
            break
    t["t01_injections_effective"] = all_inj_effective
    t["t07_no_residual_perturbation"] = all(
        p.read_bytes() == canon_bytes[str(p)] for c in CASES for p in c["targets"])
    teeth_ok = all(t.values())

    rec = {
        "artifact": "m13_v57_co195_fixpoint_uniqueness", "schema": 1, "revision": "CO-200",
        "nature": "固定点唯一性（路径无关）oracle：**多扰动量**（4 案）扰动启动 ⇒ 收敛须复原规范态（CO-151 失效模式的直接判据）",
        "trigger": "CO-196（I-2 自指/链式 pin）起，**CO-200（G-1）**再扩：受控集含 **md 卡片产物**（CO-186 入 pin）而旧三案只扰 json 记录 ⇒ 该受控面从未被扰动实验行使",
        "snapshot_scope": "watch_paths() - {本记录}（自指防护，判据不含本证据件）",
        "precondition": "先结算（t00）：工作树须已收敛为不动点",
        # CO-196（J-3）：**不落盘任何含本记录自身的 sha** —— `sha_incl`（= snapshot() 含证据件自身）会使记录内容依赖
        # 自身字节 ⇒ 记录**非幂等**（实测连跑 3f1f9b37869f93ea → 35549fe1c938139b）。自排除的**判据**在运行期算（t06），
        # 只落**布尔结论**，不落原始自指 sha。
        "sha_canon": sha_canon,
        "cases": rows, "aborted_case": aborted,
        "teeth": {**t, "teeth_ok": teeth_ok},
        "verdict": "PASS" if teeth_ok else "FAIL_FIXPOINT_PATH_DEPENDENT_OR_ABORT",
        "redline": "只扰动**受控**件且逐案 `finally` 无条件复原；不改冻结四源/板/SPEC；本证据件**不入 pin 表**（R-CO195-0）。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "teeth": t, "cases": rows,
                      "sha_canon": sha_canon, "rec_sha16": _s16(REC.read_bytes())},
                     ensure_ascii=False, indent=1))
    return 0 if teeth_ok else 1


if __name__ == "__main__":
    sys.exit(main())
