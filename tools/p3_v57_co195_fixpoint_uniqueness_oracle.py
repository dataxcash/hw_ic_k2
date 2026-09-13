#!/usr/bin/env python3
"""CO-195 — **固定点唯一性（路径无关）oracle**（L2 自裁）。

缘起：co120 的 P5「下游快照」判据为**键名启发式**（`*_sha16_after` / `*_current_sha16` / register|ledger 面），
其真正要保证的**语义**性质是：文档化复现序的**不动点唯一**（CO-151 失效模式 = 「按序连跑两遍得**另一稳定不动点**，
提交 pin 不可复现」）。键名判据无法直接判该性质，且值域判据经实测**不可行**（35 条记录内嵌**受控集**未来 sha，
但其中绝大多数是**冻结历史件/自身产物**的合法 pin ⇒ 会误报）。
本 oracle 直接判**语义性质**：从**扰动态**启动规范序，要求收敛回**与规范态逐字节相同**的不动点。

方法（**自我保护**）：① 取规范态 `snapshot()` 与登记簿字节；② 注入登记簿 `meta.counts`（越界值）；③ 跑规范序
（`--max-iter`）；④ 要求 rc=0 + converged + `snapshot()` 复原 + 登记簿**逐字节**复原；⑤ `finally` 无条件复原
（不掉入扰动态）。含**判别力**合成控（唯一/非唯一不动点模型）。
CLI: python3 tools/p3_v57_co195_fixpoint_uniqueness_oracle.py [--plan] [--max-iter 5]
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, types
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
RUNNER = K2 / "tools/p3_v57_co164_order_runner.py"
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
REC = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co195_fixpoint_uniqueness.json"


def _load(name: str, path: Path) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def _s16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _snap_excl_self(cur, rec: Path, paths) -> str:
    """CO-195（I-2）：**排除本记录自身**的受控集快照（防自指：本记录写回后自身字节即变 ⇒
    若把自身计入，记录的 `sha_canon` **永不等于**其所在状态的实际 sha，且 §68 pin 随记录改写漂移）。"""
    h = hashlib.sha256()
    for p in paths:
        if Path(p) == rec:
            continue
        h.update(Path(p).read_bytes() if Path(p).exists() else b"<missing>")
    return h.hexdigest()[:16]


def _fixpoint(fn, start, n: int = 300):
    x = start
    for _ in range(n):
        y = fn(x)
        if y == x:
            return x
        x = y
    return x


def _run_order(cur, max_iter: int):
    """跑规范序一次，返回 (rc, stdout_json|None)。"""
    r = subprocess.run([str(cur.PY), str(RUNNER), "--max-iter", str(max_iter)],
                       cwd=K2, capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout)
    except Exception:
        return r.returncode, None


def uniqueness_discriminates() -> bool:
    """判别力负控：同一判据（两起点收敛值比较）须**唯一**判 True、**非唯一**判 False。"""
    uniq = lambda x: 42                       # 恒定收敛 ⇒ 唯一不动点
    nonuniq = lambda x: (x if x in (0, 1) else 0)   # 两个不动点 {0, 1} ⇒ 路径相关
    return (_fixpoint(uniq, 3) == _fixpoint(uniq, 7)) and \
           (_fixpoint(nonuniq, 0) != _fixpoint(nonuniq, 1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="只打印注入计划（不改盘、不跑序）")
    ap.add_argument("--max-iter", type=int, default=5)
    a = ap.parse_args(argv)

    cur = _load("co164_runner", RUNNER)
    # CO-195（前置）：**先结算** —— 若工作树处于「改动后未收敛」中途态，首次跑序会落到**另一**稳定态；
    # 本 oracle 的自变量是「扰动态 vs 规范态」，故须先把规范态结算成不动点，再作扰动实验（否则测的是结算，不是路径无关）。
    settle_rc, settle_json = _run_order(cur, a.max_iter)
    canon_bytes = REG.read_bytes()
    canon = json.loads(canon_bytes.decode())
    canon_counts = canon["meta"]["counts"]
    wpaths = cur.watch_paths()
    # CO-195（I-2）：判据快照**排除本记录自身**（自指防护）；`sha_incl` 仅作「排除非空转」证据
    sha_canon = _snap_excl_self(cur, REC, wpaths)
    sha_incl = cur.snapshot()

    if a.plan:
        print(json.dumps({"mode": "plan", "register": str(REG.relative_to(K2)),
                          "canonical_counts": canon_counts, "sha_canon": sha_canon,
                          "inject": "meta.counts := 越界值（999 / OPEN 7）",
                          "snapshot_scope": "watch_paths() - {本记录}"}, ensure_ascii=False))
        return 0

    t = {"t00_settle_converged": (settle_rc == 0 and bool(settle_json) and bool(settle_json.get("converged"))),
         "t01_injection_effective": False, "t02_order_converged_rc0": False,
         "t03_fixpoint_restored": False, "t04_register_byte_restored": False,
         "t05_discriminates_path_dependence": uniqueness_discriminates(),
         "t06_self_exclusion_nonvacuous": (not REC.exists()) or (sha_canon != sha_incl)}
    sha_pert, sha_after, run_rc, run_json = None, None, None, None
    try:
        inj = json.loads(canon_bytes.decode())
        inj["meta"]["counts"] = {"SPEC_DEFECT": 999, "PROVED_THRESHOLD": 999, "TOOL_DEFECT": 999,
                                 "IMPLEMENTATION_DEVIATION": 999, "OPEN": 7, "total": 999}
        REG.write_text(json.dumps(inj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        sha_pert = _snap_excl_self(cur, REC, wpaths)
        t["t01_injection_effective"] = (sha_pert != sha_canon)

        run_rc, run_json = _run_order(cur, a.max_iter)
        t["t02_order_converged_rc0"] = (run_rc == 0 and bool(run_json) and bool(run_json.get("converged")))

        sha_after = _snap_excl_self(cur, REC, wpaths)
        t["t03_fixpoint_restored"] = (sha_after == sha_canon)
        t["t04_register_byte_restored"] = (REG.read_bytes() == canon_bytes)
    finally:
        if REG.read_bytes() != canon_bytes:      # 自我保护：绝不留在扰动态
            REG.write_bytes(canon_bytes)

    teeth_ok = all(t.values())
    rec = {
        "artifact": "m13_v57_co195_fixpoint_uniqueness", "schema": 1, "revision": "CO-195",
        "nature": "固定点唯一性（路径无关）oracle：扰动启动 ⇒ 收敛须复原规范态（CO-151 失效模式的直接判据）",
        "target_repro_order": "R-CO195-2（步集/序列不变）",
        "snapshot_scope": "watch_paths() - {本记录}（CO-195 I-2：自指防护，判据不含本证据件）",
        "perturbation": {"artifact": str(REG.relative_to(K2)), "field": "meta.counts",
                         "canonical": canon_counts, "injected": {"total": 999, "OPEN": 7}},
        "sha_canon": sha_canon, "sha_perturbed": sha_pert, "sha_after": sha_after,
        "settle": {"rc": settle_rc, "converged": (settle_json or {}).get("converged"),
                   "iterations": (settle_json or {}).get("iterations")},
        "order_rc": run_rc, "order_converged": (run_json or {}).get("converged"),
        "order_iterations": (run_json or {}).get("iterations"),
        "teeth": {**t, "teeth_ok": teeth_ok},
        "verdict": "PASS" if teeth_ok else "FAIL_FIXPOINT_PATH_DEPENDENT_OR_ABORT",
        "redline": "只扰动受控件（登记簿 counts）且 finally 无条件复原；不改冻结四源/板/SPEC；本记录不被 ORDER 改写。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "teeth": t,
                      "sha_canon": sha_canon, "sha_perturbed": sha_pert, "sha_after": sha_after,
                      "order_rc": run_rc, "order_converged": rec["order_converged"],
                      "rec_sha16": _s16(REC.read_bytes())}, ensure_ascii=False, indent=1))
    return 0 if teeth_ok else 1


if __name__ == "__main__":
    sys.exit(main())
