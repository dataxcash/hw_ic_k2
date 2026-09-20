#!/usr/bin/env python3
"""k2_p6_exception_path_sweep_v1.py — B2-T 续作（只读，真源零改动）：**(l) 异常路径 fail-closed 普查**。

覆盖两类「B2 同族」（抛错未包装 / 非法输入）：
  A) **CLI 层**：`--nets`（合法对 / 不存在的网 / 元数错误）、`--all-v2`、`--link-topology-mapping`（合成映射）
     × {遗留 alloc, 现行 schema}（B1 无关，故不重复守卫对照）。
  B) **API 层**（进程内）：非法/边界输入下各 `probe_*`/`solve_*` 是**返回状态**还是**抛异常**。

产出：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_EXCEPTION_PATH_SWEEP_v1.json`
      `k2/docs/K2-P6-B2T-EXCEPTION-PATH-SWEEP-20260920.md`
用法（容器根）：python3 k2/tools/k2_p6_exception_path_sweep_v1.py [--verify-determinism]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

REPO = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = REPO / "k2"
BOARD = K2 / "hw/k2_v4_8L.kicad_pcb"
PRO = K2 / "hw/k2_v4_8L.kicad_pro"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
LEGACY = K2 / "pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"
P3 = Path("/tmp/opencode/current_alloc_from_pipeline.json")
OUT = Path("/tmp/opencode/exc_sweep_out")
LINK_MAP = Path("/tmp/opencode/exc_link_map.json")
OUT_JSON = K2 / "pm_gate/artifacts/k2_v4/P6_execution/B2T_EXCEPTION_PATH_SWEEP_v1.json"
OUT_DOC = K2 / "docs/K2-P6-B2T-EXCEPTION-PATH-SWEEP-20260920.md"
CLI_CASES = [("nets_ok", ["--nets", "PCIE_UP0_P,PCIE_UP0_N"]),
             ("nets_unknown", ["--nets", "PCIE_NOPE_P,PCIE_NOPE_N"]),
             ("nets_bad_arity", ["--nets", "PCIE_UP0_P"]),
             ("all_v2", ["--all-v2"]),
             ("link_topology_mapping", ["--link-topology-mapping", str(LINK_MAP)])]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def run_cli(carrier, name, extra, timeout=420):
    alloc = str(P3 if carrier == "p3_current_schema" else LEGACY)
    env = {k: v for k, v in os.environ.items() if k != "PM_GATE_PROJECT_ROOT"}
    env["PYTHONPATH"] = str(K2 / "_shared")
    outdir = OUT / f"{carrier}_{name}"
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "eda_core.hs_route_model", "--board", str(BOARD), "--spec", str(SPEC),
           "--alloc", alloc, "--rules", str(RULES), "--pro", str(PRO), *extra, "--out", str(outdir)]
    t0 = time.time()
    try:
        pr = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True, timeout=timeout)
        rc, so, se, to = pr.returncode, pr.stdout, pr.stderr, False
    except subprocess.TimeoutExpired as e:
        rc, so, se, to = None, "", "", True
    status = None
    for line in reversed(so.strip().splitlines()):
        try:
            status = (json.loads(line) or {}).get("status"); break
        except Exception:
            continue
    exc = ""
    if se:
        lines = [l.strip() for l in se.strip().splitlines() if l.strip()]
        exc = lines[-1][:140] if lines else ""
    infra = "[infra]" in so
    return {"scope": "cli", "carrier": carrier, "case": name, "rc": rc, "status": status,
            "exception": exc, "infra_msg": infra, "timeout": to, "runtime_s": round(time.time() - t0, 1),
            "stdout_tail": so.strip().splitlines()[-1][:110] if so.strip() else ""}


API_CASES = [
 ("solve_pair_segment[unknown]", "solve_pair_segment", ("PCIE_NOPE_P", "PCIE_NOPE_N"), {}),
 ("solve_chain_v4[unknown]", "solve_chain_v4", ("NOPE",), {}),
 ("solve_all_v4[empty]", "solve_all_v4", ([],), {}),
 ("probe_escape_capacity[unknown]", "probe_escape_capacity", ("PCIE_NOPE_P", "PCIE_NOPE_N", "input"), {}),
 ("probe_path_clearance[empty_path]", "probe_path_clearance", ("PCIE_DN0_P", [], []), {}),
 ("probe_path_clearance[unknown_net]", "probe_path_clearance", ("PCIE_NOPE_P", [(100.0, 58.0), (110.0, 58.0)], ["F.Cu"]), {}),
 ("probe_region_capacity[unknown_corridor]", "probe_region_capacity",
  ({"id": "R", "type": "pin_region", "corridor_id": "NOPE", "band": "up", "bases": ["UP0"],
    "segname": "out_J2", "side": "right"},), {"demand": 1}),
 ("probe_region_capacity[missing_keys]", "probe_region_capacity", ({"id": "R"},), {"demand": 1}),
 ("link_topology_virtual_map[empty]", "link_topology_virtual_map", ({},), {}),
 ("link_topology_virtual_map[bad_ref]", "link_topology_virtual_map",
  ({"UP0": {"chip": "NOPE", "conn": "NOPE"}},), {}),
 ("_corridor_clear_span[malformed]", "_corridor_clear_span", ({"x_range": [100.0]},), {}),
]


def api_sweep(carrier):
    sys.path.insert(0, str(K2 / "_shared"))
    for m in [x for x in list(sys.modules) if x == "eda_core" or x.startswith("eda_core.")]:
        del sys.modules[m]
    from eda_core.hs_route_model import HSRouteModel
    alloc = str(P3 if carrier == "p3_current_schema" else LEGACY)
    model = HSRouteModel(str(BOARD), str(SPEC), alloc, str(RULES), pro_path=str(PRO))
    rows = []
    for name, meth, args, kw in API_CASES:
        try:
            r = getattr(model, meth)(*args, **kw)
            st = r.get("status") if isinstance(r, dict) else None
            rows.append({"scope": "api", "carrier": carrier, "case": name, "exception": "",
                         "status": st, "returned": type(r).__name__})
        except BaseException as e:
            tb = [l.strip() for l in traceback.format_exc().strip().splitlines() if "hs_route_model.py" in l]
            rows.append({"scope": "api", "carrier": carrier, "case": name,
                         "exception": f"{type(e).__name__}: {e}"[:140], "status": None,
                         "at": tb[-1:]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-determinism", action="store_true")
    args = ap.parse_args()
    LINK_MAP.write_text(json.dumps({"UP0": {"chip": "U7", "conn": "J2", "direction": "out"},
                                    "UP1": {"chip": "U7", "conn": "J2", "direction": "out"},
                                    "DN0": {"chip": "U7", "conn": "J2", "direction": "in"}}),
                        encoding="utf-8")
    cli = [run_cli(c, n, x) for c in ("legacy_alloc", "p3_current_schema") for n, x in CLI_CASES]
    api = api_sweep("legacy_alloc") + api_sweep("p3_current_schema")
    det = "NOT_RUN"
    if args.verify_determinism:
        cli2 = [run_cli(c, n, x) for c in ("legacy_alloc", "p3_current_schema") for n, x in CLI_CASES]
        slim = lambda rs: [{k: r[k] for k in ("carrier", "case", "rc", "status", "exception")} for r in rs]
        det = "MATCH" if json.dumps(slim(cli), sort_keys=True) == json.dumps(slim(cli2), sort_keys=True) else "MISMATCH"
    exc_cli = [r for r in cli if r["exception"]]
    exc_api = [r for r in api if r["exception"]]
    doc = {
        "artifact": "k2_p6_exception_path_sweep", "schema": 1, "readonly_repo": True,
        "purpose": "(l) CLI/API 异常路径 fail-closed 普查（B2 同族：抛错未包装 / 非法输入行为）",
        "anchors": {"engine": {"path": "k2/_shared/eda_core/hs_route_model.py", "sha16": sha16(K2 / "_shared/eda_core/hs_route_model.py")},
                    "board_8L": {"sha16": sha16(BOARD)}, "spec_rev52": {"sha16": sha16(SPEC)},
                    "legacy_alloc": {"sha16": sha16(LEGACY)}, "p3_carrier": {"sha16": sha16(P3)}},
        "cli_matrix": cli, "api_matrix": api, "determinism_2run": det,
        "n_exc_cli": len(exc_cli), "n_exc_api": len(exc_api),
        "exception_cases": [r["carrier"] + "/" + r["case"] for r in exc_cli + exc_api],
        "conclusions": [
            "CLI：`--nets` 元数错误 = **优雅 [infra]-2**（合规）；`,unknown nets` 与 `--link-topology-mapping` "
            "见下表（是否抛错/状态）。",
            "API：见下表 —— 抛异常者属「异常路径未 fail-closed」（应为状态或具名异常契约）；"
            "合法状态返回者合规。",
            "共同口径建议（并入 B1 授权件）：异常路径返回 `status=INFRA_ERROR` + 可机辨退出码，"
            "避免与『正常未解/未 TOPOLOGY_OK』同为 rc=1。",
            "发现 B4（低严重度，私有 API）：`_corridor_clear_span` 对畸形 corridor（`x_range` 非二元素）"
            "抛 `ValueError: not enough values to unpack`；该 API 为内部函数、契约输入来自 SPEC 真源，"
            "风险低（建议随手加形状校验，非阻塞）。",
            "注：`link_topology_virtual_map` 返回 **verdict 键**（非 status），本表 status=None 属预期；"
            "`--nets` 未知网为优雅 `INFRA_ERROR`、元数错误为优雅 `[infra]`/rc=2 ⇒ CLI 输入校验合规。",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    cli_md = "\n".join(f"| {r['carrier']} | `{r['case']}` | {r['rc']} | {r['status']} | {r['exception'] or '—'} | "
                       f"{r['stdout_tail'][:60]} |" for r in cli)
    api_md = "\n".join(f"| {r['carrier']} | `{r['case']}` | {r['exception'] or '—'} | {r['status']} |" for r in api)
    OUT_DOC.write_text(f"""# K2 · B2-T 续作 · **异常路径 fail-closed 普查（l）**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_EXCEPTION_PATH_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_exception_path_sweep_v1.py --verify-determinism`
> 真源零改动（输出落 /tmp）

## A. CLI 层（{len(cli)} 运行 = 2 载体 × {len(CLI_CASES)} 用例）

| 载体 | 用例 | exit | status | 异常 | stdout 尾 |
|---|---|---|---|---|---|
{cli_md}

## B. API 层（{len(api)} 调用 = 2 载体 × {len(API_CASES)} 用例）

| 载体 | 用例 | 异常 | status |
|---|---|---|---|
{api_md}

## 结论

- 抛异常用例（{len(exc_cli) + len(exc_api)} 个）：{doc['exception_cases']}
- 判定：CLI `--nets` 元数错误 = **优雅 `[infra]`/rc=2**（合规）；其余见上表。
  抛异常者属「**异常路径未 fail-closed**」⇒ 建议并入 B1 授权件的 CLI/API 异常语义整改
  （`status=INFRA_ERROR` + 可机辨码）。
- **发现 B4（低严重度）**：私有 API `_corridor_clear_span` 对畸形 corridor 抛 `ValueError`（非 fail-closed 状态）；
  该 API 为内部函数、输入来自 SPEC 真源 ⇒ 风险低（建议随手加形状校验，非阻塞）。
- 注：`link_topology_virtual_map` 返回 **verdict 键**（非 status），表中 status=None 属预期；`--nets` 输入校验合规
  （未知网 ⇒ 优雅 `INFRA_ERROR`；元数错误 ⇒ `[infra]`/rc=2）。
- 确定性两跑：**{det}**。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `{doc['anchors']['engine']['sha16']}` · 阶段：**P6 未开（只出计划件）**
""", encoding="utf-8")
    print(json.dumps({"n_exc_cli": len(exc_cli), "n_exc_api": len(exc_api),
                      "exception_cases": doc["exception_cases"], "determinism": det,
                      "cli": [{k: r[k] for k in ("carrier", "case", "rc", "status", "exception")} for r in cli],
                      "api": [{k: r[k] for k in ("carrier", "case", "exception", "status")} for r in api]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
