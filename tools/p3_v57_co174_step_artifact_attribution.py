#!/usr/bin/env python3
"""CO-174 — CO-172 F-7 残余处置：runner `did_work` 归因**步本地化**（⇒ 登记簿 + 残余显式化）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co164_order_runner.py`（CO-169.3，t13/t13b/t13c）
     承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co174_step_artifact_attribution.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "runner（CO-169.2）的 `step_did_work` 归因基于**全局受控集**（`watch_paths()`）⇒ 并发/他人写**任一**受控件"
          "都会被误判为「本步做了事」（CO-172 F-7 残余的**假通过方向**）。",
  "disposition": "CO-174：`p3_v57_co164_order_runner.py` 升 **CO-169.3** —— 新增 `STEP_ARTIFACTS`（**每步主产物集**，"
                 "由实测探针逐步跑 ORDER **钉定、非猜测**）+ `step_paths()`；`_snap_watched(paths)` 参数化；"
                 "`did_work` 归因**仅限本步声明集**（全局集仅保留给收敛 sha，R-CO165 不变）；报告增 "
                 "`declared_changed` / `stray_changed` 证据；牙齿 **t13**（每步声明完备且 ⊆ 全局受控集）/ "
                 "**t13b**（步本地负控：非声明受控件的变动不得归因于本步）。",
  "status": "CLOSED", "next": "共享主产物残余见 co174:G-2。",
  "evidence": ["CO-172 P8：`_snap_watched()` 受控集 = 全局 `watch_paths()`（非步本地）",
               "CO-174 实测探针：逐步跑 ORDER（42 步）得每步真实产物集；实现后 --check t13/t13b/t13c 全 True 且全序收敛"],
  "refs": ["CO-172", "CO-169", "CO-174"], "closed_by": ["CO-174"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**残余（如实登记）**：处置类步骤（co152..co174 共 17 步）的**唯一**主产物是**共享**的 "
          "`input_defect_register_v1.json`（`derived_value_ledger_v1.json` 亦被 4 步共享）⇒ 即便步本地归因，"
          "**他人/并发对同一共享件的写**仍会被误判为「本步做了事」（假通过方向）。",
  "disposition": "CO-174：残余**显式枚举**于 runner `SHARED_ARTIFACT_RESIDUAL` 常量 + **t13c 机判**"
                 "（共享件集 == 枚举键集，新增共享件即 fail ⇒ 防静默遗忘）。彻底关闭须每步写**独立标记件**（未做）。",
  "status": "CLOSED",
  "next": "下轮候选：每步写独立标记件（如 `.archer_tmp/step_evidence/<step>.json`）或 step-local 输出 ⇒ 归因不依赖共享件。",
  "evidence": ["CO-174 探针：17 步 changed == [`input_defect_register_v1.json`]；4 步含 `derived_value_ledger_v1.json`",
               "CO-174 t13c：`_multi`（STEP_ARTIFACTS 中出现 >1 次者）== `SHARED_ARTIFACT_RESIDUAL` 键集 True"],
  "refs": ["CO-172", "CO-174"], "closed_by": ["CO-174"]},
]

MARK = ("；**CO-174（L2 自裁 · 复现序归因硬化）**：处置 CO-172 F-7 残余（did_work 归因基于全局受控集 ⇒ 假通过方向）"
        "—— `p3_v57_co164_order_runner.py` 升 **CO-169.3**：`STEP_ARTIFACTS` 每步主产物集（实测探针钉定）+ "
        "`did_work` 步本地归因 + 报告 `declared_changed`/`stray_changed` + 牙齿 t13/t13b/t13c；"
        "共享主产物（登记簿 17 步 / 台账 4 步）残余**显式枚举**于 `SHARED_ARTIFACT_RESIDUAL` 并机判（co174:G-1/G-2）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co174:" + it["id"]
        patch = {k: v for k, v in it.items() if k != "id"}
        if f in have:
            have[f].update(patch); updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch)); added.append(f)
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} / upd {len(updated)} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
