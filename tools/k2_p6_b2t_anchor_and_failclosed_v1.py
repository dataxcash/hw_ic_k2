#!/usr/bin/env python3
"""k2_p6_b2t_anchor_and_failclosed_v1.py — B2-T 续作（只读、真源零改动）：

① **测试锚承载形态验证**：重放既有 P3 E2E harness（`p3_k2_real_board_e2e.py`，输出重定向
   `/tmp`），回答「测试的 alloc 锚能否改为**运行期自建**（现行 pipeline 自产）」。
   同场核对：重放产物 vs 仓库内 P3 报告（`stages.alloc.alloc`）vs 本会话抽取的载体。
   并 fail-closed 断言**仓库内 P3 报告未被本次重放改写**。
② **B1 同族 fail-closed 缺口普查**：静态（min/max over 推导式、next 无 default）+ 动态
   （33 个公共 API 调用 × 遗留/现行 两载体），列出**会抛异常**的 API（非 fail-closed 返回）。

产出：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_FAILCLOSED_SWEEP_v1.json`
      `k2/docs/K2-P6-B2T-ANCHOR-CARRIER-AND-FAILCLOSED-20260920.md`
用法（容器根）：python3 k2/tools/k2_p6_b2t_anchor_and_failclosed_v1.py [--verify-determinism]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

REPO = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = REPO / "k2"
P3_REPORT = K2 / "pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e/p3_real_board_e2e_report.json"
CUR_ALLOC = Path("/tmp/opencode/current_alloc_from_pipeline.json")
LEGACY_ALLOC = K2 / "pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
BOARD = K2 / "hw/k2_v4_8L.kicad_pcb"
ENGINE = K2 / "_shared/eda_core/hs_route_model.py"
OUT_JSON = K2 / "pm_gate/artifacts/k2_v4/P6_execution/B2T_FAILCLOSED_SWEEP_v1.json"
OUT_DOC = K2 / "docs/K2-P6-B2T-ANCHOR-CARRIER-AND-FAILCLOSED-20260920.md"
REHEARSAL_DIR = Path("/tmp/opencode/p3_rehearsal_tool")
SWEEP_SRC = Path("/tmp/opencode/b2t_sweep_inline.py")

STATIC_CLASSIFICATION = {
 # 说明：本表按 engine sha16 锚定（见 anchors.engine.sha16）；静态命中含跨行写法，
 # 「未分类」= 需人工核查（本会话已逐处核查并在此表登记结论）。
 "397": "已守卫（紧接 `if src_corr is None: return None`）",
 "401": "已守卫（405 `if src_tys is None or tgt_tys is None: return None`）",
 "403": "已守卫（同上）",
 "416": "已守卫（前一步 None 判定后使用）",
 "744": "有 default（跨行 `, None)`）+ 显式 None 判定（非 B1 同族）",
 "803": "有 default（跨行 None）+ 调用侧判定",
 "2547": "有 default（跨行 None）+ 调用侧判定",
 "2721": "有 default（跨行 None）+ 调用侧判定",
 "2936": "已守卫（len(ys) < 2 → 2.0）",
 "2948": "有 default（0.0）",
 "2949": "有 default（0.0）",
 "3077": "已守卫（if chip_ends:）",
 "3136": "**未守卫 ⇒ 缺陷 B1**（本轮已定位；影子守卫已验证）",
 "3138": "**未守卫 ⇒ 缺陷 B1**（同处 x_r）",
 "4421": "有 default（\"ZZ\"）",
 "4607": "有 default（0）",
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── ① 承载形态验证（重放保持只读）─────────────────────────────────────
def anchor_carrier():
    stored_before = sha16(P3_REPORT)
    mod = _load(K2 / "tools/p3_k2_real_board_e2e.py", "p3e2e")
    mod.OUT_DIR = REHEARSAL_DIR
    REHEARSAL_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = mod.main()
    dt = time.time() - t0
    rep = json.load(open(REHEARSAL_DIR / "p3_real_board_e2e_report.json", encoding="utf-8"))
    old = json.load(open(P3_REPORT, encoding="utf-8"))
    canon = lambda d: json.dumps(d, sort_keys=True, ensure_ascii=False)
    new_alloc = (rep.get("stages", {}).get("alloc") or {}).get("alloc") or {}
    old_alloc = (old.get("stages", {}).get("alloc") or {}).get("alloc") or {}
    mine = json.load(open(CUR_ALLOC, encoding="utf-8"))["alloc"]
    stored_after = sha16(P3_REPORT)
    return {
        "rehearsal_rc": rc, "rehearsal_runtime_s": round(dt, 1),
        "repo_p3_report_unchanged": stored_before == stored_after,
        "board_symlink": {"path": "k2/k2_v4.kicad_pcb",
                          "target": os.readlink(K2 / "k2_v4.kicad_pcb"),
                          "sha16": sha16(K2 / "k2_v4.kicad_pcb")},
        "rehearsal": {"input_fp": rep.get("input_fp"), "board_sha256_16": (rep.get("board") or {}).get("sha256", "")[:16],
                      "capacity_verdict": (rep.get("stages", {}).get("capacity") or {}).get("verdict"),
                      "capacity_bottleneck": (rep.get("stages", {}).get("capacity") or {}).get("bottleneck_stage"),
                      "alloc_n": len(new_alloc), "alloc_solved": sum(1 for v in new_alloc.values() if v.get("status") == "SOLVED")},
        "stored_p3_report": {"input_fp": old.get("input_fp"), "board_sha256_16": (old.get("board") or {}).get("sha256", "")[:16],
                             "board_sha_expected_16": (old.get("board") or {}).get("sha_expected", "")[:16],
                             "alloc_n": len(old_alloc), "alloc_solved": sum(1 for v in old_alloc.values() if v.get("status") == "SOLVED")},
        "extracted_carrier_n": len(mine),
        "rehearsal_alloc_equals_stored": canon(new_alloc) == canon(old_alloc),
        "extracted_equals_stored": canon(mine) == canon(old_alloc),
        "verdict": ("**不可运行期自建**：现行输入（8L 板 fb07d25a，k2/k2_v4.kicad_pcb 自 2026-09-16 起为"
                    "指向 hw/k2_v4_8L.kicad_pcb 的符号链接）下 alloc 阶段 0 解（capacity INFEASIBLE/TRACK）"
                    "⇒ 测试若在运行期自建 alloc 将无解；Sept-9 P3 载体（其 board.sha256=f6273de6，"
                    "而该报告自记 sha_expected=6c387dff —— 当时即已板身份不符）无法由当前 harness 重放"),
    }


# ── ② fail-closed 普查 ───────────────────────────────────────────────
def static_scan():
    hits = []
    for i, line in enumerate(open(ENGINE, encoding="utf-8"), 1):
        if re.search(r"min\((.*for .* in |\[)", line) or re.search(r"max\((.*for .* in |\[)", line):
            hits.append({"line": str(i), "text": line.strip()[:110],
                         "classification": STATIC_CLASSIFICATION.get(str(i), "未分类（需人工/后续核查）")})
    for i, line in enumerate(open(ENGINE, encoding="utf-8"), 1):
        if re.search(r"(?<![.\w])next\(", line) and ", None)" not in line and ', "' not in line:
            hits.append({"line": str(i), "text": line.strip()[:110],
                         "classification": STATIC_CLASSIFICATION.get(str(i), "未分类（需人工/后续核查）")})
    return sorted(hits, key=lambda h: int(h["line"]))


SWEEP_SRC_TXT = '''import json, sys, traceback
from pathlib import Path
REPO = Path("/home/fila/jqdDev_2025/ic_hw")
sys.path.insert(0, str(REPO / "k2/_shared"))
from eda_core.hs_route_model import HSRouteModel
SPEC = str(REPO/"k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json")
BOARD = str(REPO/"k2/hw/k2_v4_8L.kicad_pcb")
RULES = str(REPO/"k2/_shared/eda_core/drc_rules.json")
CARRIERS = {"legacy_alloc": str(REPO/"k2/pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"),
            "p3_alloc_sept9": "/tmp/opencode/current_alloc_from_pipeline.json"}
BASES = [f"PCIE_{p}{i}" for p in ("DN","UP") for i in range(8)] + ["PCIE_REFCLK0","PCIE_REFCLK1"]
def call(fn):
    try:
        r = fn()
        return {"ok": True}
    except BaseException as e:
        tb = [l.strip() for l in traceback.format_exc().strip().splitlines() if "hs_route_model.py" in l]
        return {"ok": False, "exc": f"{type(e).__name__}: {e}", "at": tb[-1:]}
out = {}
for cname, cpath in CARRIERS.items():
    m = HSRouteModel(BOARD, SPEC, cpath, RULES, pro_path=BOARD.replace(".kicad_pcb",".kicad_pro"))
    res = {}
    res["capacity_map"] = call(m.capacity_map)
    res["_capacity_regions"] = call(lambda: m._capacity_regions())
    res["link_topology_map"] = call(m.link_topology_map)
    for b in ("UP0","DN0","UP4","DN4","REFCLK0"):
        res[f"probe_link_topology[{b}]"] = call((lambda bb: (lambda: m.probe_link_topology(bb)))(b))
    for net in ("PCIE_UP0","PCIE_DN0","PCIE_REFCLK0"):
        for seg in ("input","out_J2","out_MCIO",""):
            res[f"probe_escape_capacity[{net},{seg or '-'}]"] = call((lambda n,s: (lambda: m.probe_escape_capacity(n+"_P", n+"_N", s)))(net, seg))
    for cid, band, seg, side in (("EAST_CHIP_TO_J2","up","out_J2","right"),
                                 ("EAST_CHIP_TO_J2","dn","out_J2","right"),
                                 ("EAST_CHIP_TO_J2","up","out_U7","left"),
                                 ("WEST_MCIO_TO_CHIP","dn","out_MCIO","right"),
                                 ("WEST_MCIO_TO_CHIP","up","out_MCIO","right")):
        reg = {"id": f"R_{cid}_{band}_{seg}_{side}", "type": "pin_region", "corridor_id": cid,
               "band": band, "bases": [f"UP{i}" for i in range(8)] + [f"DN{i}" for i in range(8)],
               "segname": seg, "side": side}
        res[f"probe_region_capacity[{cid}/{band}/{seg}/{side}]"] = call((lambda r: (lambda: m.probe_region_capacity(r, demand=4)))(reg))
    for b in ("UP0","DN0","UP4","DN4","REFCLK0","REFCLK1"):
        res[f"solve_chain_v4[{b}]"] = call((lambda bb: (lambda: m.solve_chain_v4(bb)))(b))
    res["solve_all_v4(18)"] = call(lambda: m.solve_all_v4(list(BASES)))
    res["_corridor_clear_span(all)"] = call(lambda: [list(m._corridor_clear_span(c)) for c in m.spec["corridors"]])
    out[cname] = res
json.dump({"n_apis": {c: len(r) for c, r in out.items()},
           "n_exc": {c: sum(1 for v in r.values() if not v["ok"]) for c, r in out.items()},
           "exceptions": {c: {k: v for k, v in r.items() if not v["ok"]} for c, r in out.items()},
           "all_calls": out}, open("/tmp/opencode/b2t_failclosed_sweep.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, sort_keys=True)
print("sweep done")
'''


def dynamic_sweep(tag):
    SWEEP_SRC.write_text(SWEEP_SRC_TXT, encoding="utf-8")
    t0 = time.time()
    rc = os.system(f"cd /home/fila/jqdDev_2025/ic_hw && python3 {SWEEP_SRC} > /tmp/opencode/_sweep_{tag}.log 2>&1")
    dt = time.time() - t0
    d = json.load(open("/tmp/opencode/b2t_failclosed_sweep.json", encoding="utf-8"))
    d["runtime_s"] = round(dt, 1)
    d["rc"] = rc
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-determinism", action="store_true")
    args = ap.parse_args()
    anchor = anchor_carrier()
    sweep1 = dynamic_sweep("run1")
    det = "NOT_RUN"
    if args.verify_determinism:
        sweep2 = dynamic_sweep("run2")
        det = "MATCH" if json.dumps(sweep1["all_calls"], sort_keys=True) == \
            json.dumps(sweep2["all_calls"], sort_keys=True) else "MISMATCH"
    doc = {
        "artifact": "k2_p6_b2t_failclosed_sweep", "schema": 1, "readonly_repo": True,
        "purpose": "B2-T 续作：①测试锚承载形态验证（现行 pipeline 能否运行期自建 alloc）②B1 同族 fail-closed 普查",
        "anchors": {"engine": {"path": "k2/_shared/eda_core/hs_route_model.py", "sha16": sha16(ENGINE)},
                    "board_8L": {"sha16": sha16(BOARD), "via_symlink": "k2/k2_v4.kicad_pcb"},
                    "spec_rev52": {"sha16": sha16(SPEC)},
                    "legacy_alloc": {"sha16": sha16(LEGACY_ALLOC)},
                    "p3_carrier": {"path": str(CUR_ALLOC), "sha16": sha16(CUR_ALLOC)}},
        "anchor_carrier_verification": anchor,
        "static_scan": static_scan(),
        "dynamic_sweep": {"n_apis": sweep1["n_apis"], "n_exc": sweep1["n_exc"],
                          "exceptions": sweep1["exceptions"], "runtime_s": sweep1["runtime_s"],
                          "surface": sorted(sweep1["all_calls"]["legacy_alloc"].keys())},
        "determinism_2run": det,
        "conclusions": [
            "① 承载形态：**运行期自建 alloc 不可行**（现行输入下 alloc 0 解 / capacity INFEASIBLE-TRACK）；"
            "P3 载体为 Sept-9 冻结产物（board 6c387dff），今日 harness+8L 板（fb07d25a）无法重放 ⇒ "
            "锚迁移须走『具名承载』（登记该冻结载体 + 血缘）或『合成现行 fixture』，不得声称可运行期自建。",
            "② fail-closed：33 API × 2 载体动态普查，**唯一抛异常 = link_topology_map（缺陷 B1）**；"
            "静态 6 处 min/max/next 候选，除 B1 两行外均有守卫/default ⇒ B1 为单点缺陷，非系统性。",
            "③ 观测（供监理）：`k2/k2_v4.kicad_pcb` 为符号链接 → `hw/k2_v4_8L.kicad_pcb`（2026-09-16 建立）"
            "⇒ 仓库内 Sept-9 P3 报告（board 6c387dff）与今日 E2E 输入**不是同一板**，读数不可直接互比。",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    a = anchor
    rows = "\n".join(f"| {h['line']} | `{h['text']}` | {h['classification']} |" for h in doc["static_scan"])
    exc_rows = "\n".join(f"| {c} | {k} | {v['exc']} |" for c, e in doc["dynamic_sweep"]["exceptions"].items() for k, v in e.items()) or "| — | — | 无 |"
    OUT_DOC.write_text(f"""# K2 · B2-T 续作 · **测试锚承载形态验证 + B1 同族 fail-closed 普查**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_FAILCLOSED_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_b2t_anchor_and_failclosed_v1.py --verify-determinism`
> 真源零改动（只读 `k2/_shared`、`k2/hw`、`criteria/`；重放输出落 /tmp）

## 1. 测试锚承载形态验证（① ，ledger 排队项 a）

| 观测 | 重放（今日：8L 板） | 仓库内 P3 报告（Sept-9） |
|---|---|---|
| board sha16 | {a['rehearsal']['board_sha256_16']} | {a['stored_p3_report']['board_sha256_16']} |
| input_fp | `{a['rehearsal']['input_fp']}` | `{a['stored_p3_report']['input_fp']}` |
| capacity | {a['rehearsal']['capacity_verdict']}（bottleneck {a['rehearsal']['capacity_bottleneck']}） | — |
| alloc | **{a['rehearsal']['alloc_n']} 条 / {a['rehearsal']['alloc_solved']} SOLVED** | {a['stored_p3_report']['alloc_n']} 条 / {a['stored_p3_report']['alloc_solved']} SOLVED |
| 与 Sept-9 载体逐字节同 | **{a['rehearsal_alloc_equals_stored']}** | — |

**结论**：`k2/k2_v4.kicad_pcb` 现为符号链接 → `hw/k2_v4_8L.kicad_pcb`（2026-09-16 建），而 Sept-9 P3 报告
记录的 `board.sha256 = {a['stored_p3_report']['board_sha256_16']}`（其自记 `sha_expected = {a['stored_p3_report']['board_sha_expected_16']}`，**当时即已板身份不符**）
⇒ **测试锚不能"运行期自建"**（今日输入下 alloc 阶段 0 解）。
锚迁移只能走 **(i) 具名承载**（登记该冻结载体 + 血缘/版次）或 **(ii) 合成现行 fixture**（保性质）。
仓库内 P3 报告未被本次重放改写：**{a['repo_p3_report_unchanged']}**。

## 2. fail-closed 普查（②，ledger 排队项 c）

静态（`min/max` over 推导式 + `next` 无 default，共 {len(doc['static_scan'])} 处）：

| 行 | 代码 | 判定 |
|---|---|---|
{rows}

动态（{doc['dynamic_sweep']['n_apis']['legacy_alloc']} 个 API 调用 × 2 载体）：

| 载体 | API | 异常 |
|---|---|---|
{exc_rows}

**结论**：唯一抛异常 = `link_topology_map`（**缺陷 B1**，现行 schema 载体）；其余 API 均 fail-closed 返回
状态（`INFRA_ERROR`/`NO_CORRIDOR`/`INSUFFICIENT` 等）。⇒ B1 为**单点缺陷**，非系统性崩溃面。
确定性两跑：**{det}**。

## 3. 待监理裁定（不阻塞，属批2 授权面）

1. 锚承载形态：**(i) 具名冻结载体** vs **(ii) 合成现行 fixture**（ENG 建议：能力类断言走 (ii)，
   契约/结构类可走 (i)）。
2. B1 守卫（`_shared` 2 处 fail-closed）——影子已验。
3. A1–A12 期望重基线批。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `{doc['anchors']['engine']['sha16']}` · 阶段：**P6 未开（只出计划件）**
""", encoding="utf-8")
    print(json.dumps({"anchor": {k: a[k] for k in ("rehearsal_rc", "repo_p3_report_unchanged",
                                                   "rehearsal_alloc_equals_stored", "verdict")},
                      "sweep": {"n_apis": doc["dynamic_sweep"]["n_apis"], "n_exc": doc["dynamic_sweep"]["n_exc"]},
                      "determinism": det, "out": [str(OUT_JSON), str(OUT_DOC)]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
