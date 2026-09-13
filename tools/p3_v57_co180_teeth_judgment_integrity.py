#!/usr/bin/env python3
"""CO-180 — 牙齿纳入判决的完整性（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co164_order_runner.py`（CO-169.5，t15 +
非白名单 `step_teeth_failed`）、`p3_v57_co106_reference_plane_gate.py`（CO-106.5）、
`p3_v57_co78_layer_role_drift_gate.py`（CO-78.3）承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co180_teeth_judgment_integrity.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "复现序只对**白名单步**强制其记录 `teeth` 全 True（CO-176）；其余**含 `teeth` 的 15+ 步**（impedance_table / pm_eval / "
          "co147 / co148 / co124 / co150 / co77 / co120 / co136 / co95 / co98 / co106 / fab 包 …）的**自检牙齿只记不判** "
          "⇒ 自检崩坏时收敛照过（与 CO-176 G-1 同族，只是范围未泛化）。",
  "disposition": "CO-180：`p3_v57_co164_order_runner.py` 升 **CO-169.5** —— 新增纯函数 `step_declared_teeth(step)`："
                 "从 **CO-174 的 `STEP_ARTIFACTS`** 取该步声明产物，凡含 `teeth` 键者须机判**全 True**（无 ⇒ 不适用 None；"
                 "含但未全 True/形状不明 ⇒ False fail-closed）；`allowlist_decision()` 非白名单分支新增 "
                 "**`step_teeth_failed`**（rc==0 亦停机）；静态齿 **t15**（正/负控/不适用 + 现状普查：声明含齿者全 True 且无 False）。",
  "status": "CLOSED", "next": "凡记录暴露自检者即须**参与判决**；新步加入 ORDER 后其牙齿自动纳入（依 STEP_ARTIFACTS 派生）。",
  "evidence": ["CO-180 普查（改前）：14 条记录含 `teeth` 且现全 True，但只有白名单步被强制；`co78` 的 `teeth` 竟为**散文串**",
               "CO-180 负控（改后）：把 co78 齿还原为散文并令其落盘 ⇒ `--check` 判 **t15 False / ok=False**；还原后 ok=True"],
  "refs": ["CO-180", "CO-176", "CO-174", "CO-106", "CO-78"], "closed_by": ["CO-180"]},
 {"id": "G-2", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "`co106` 判决完整性三处缺陷：① `teeth[\"teeth_ok\"] = all(teeth.values())` 在**前 3 齿**后即结算，其后追加的 4 齿"
          "（`baseline_pin_binding`/`fail_open_closed`/`verdict_positive_control`/`carrier_exemption_declared_only`）**记录在案"
          "但不参与判决**；② 聚合键 `teeth_ok` **混入 `teeth`**（自指/混淆）；③ 两项 `checks`（`C_realized_corroboration` / "
          "`D_acceptance_matrix_coverage`）`ok` **恒真**（记录冒充判据），并入 `checks_ok`。",
  "disposition": "CO-180：`p3_v57_co106_reference_plane_gate.py` 升 **CO-106.5** —— ① 聚合移至**全部齿定义后**结算、"
                 "聚合移至**全部齿定义后**结算（聚合键保留在 `teeth` 内以兼容 co120/co135/co136 消费方），并加不变量齿 `teeth_are_bool_only`；"
                 "② 修 `hard` 的引用顺序（此前在聚合前引用）；③ C/D 两项标 **`judging: False`** 并从 `checks_ok` 折算式**显式排除**"
                 "（**行为不变**：二者 ok 仍 True、verdict 仍 PASS，仅不再冒充判据；键与字段保留以兼容 co110 消费方）。",
  "status": "CLOSED", "next": "记录内**判据项**与**记录项**须显式区分（`judging` 标记）；聚合键不得混入被聚合集合。",
  "evidence": ["CO-180 源码核（改前）：`teeth_ok` 于 4 齿之前结算；`teeth_ok` 在 `teeth` 内；C/D `ok: True` 字面量",
               "CO-180 修后：verdict **仍 PASS**（行为不变）、hard True、8 齿全 True、C/D 标 `judging: False`"],
  "refs": ["CO-180", "CO-176", "CO-106"], "closed_by": ["CO-180"]},
 {"id": "G-3", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "`co78` 记录的 `teeth` 为**散文串**（「对照历史件（LID.1 下 In6=信号层）应被抓到；否则闸无效」）—— 字段名冒充牙齿，"
          "实际机判在 `teeth_ok` ⇒ **统一牙齿消费方会被误导**（CO-180 G-1 的泛化判据会因此 fail-closed 误停）。",
  "disposition": "CO-180：`p3_v57_co78_layer_role_drift_gate.py` 升 **CO-78.3** —— `teeth` 归**真齿 dict** "
                 "（`{\"control_historical_detected\": <bool>}`）、散文移入 `teeth_note`、`teeth_ok` 改为自真齿 dict 聚合。",
  "status": "CLOSED", "next": "`teeth` 字段一律为**布尔牙齿 dict**；散文说明放 `teeth_note`。",
  "evidence": ["CO-180 实测（改前）：co78 记录 `teeth` 类型 = str",
               "CO-180 修后：类型 = dict，`teeth_ok` True；泛化判据下 co78 归入「声明含齿且全 True」"],
  "refs": ["CO-180", "CO-78"], "closed_by": ["CO-180"]},
 {"id": "G-4", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "复现序存在**固有一轮 pin 滞后**：boundary 既 pin 各记录 sha（历史区段由 `co166`（序位 21）刷新对齐），"
          "而被 pin 的记录（`co120` 序位 38、`co77` 37、`co135` 39、`co136` 40 …）在**刷新步之后**才运行 ⇒ "
          "上游记录一旦变更，**首轮**boundary pin 与记录 sha 瞬时不一致 ⇒ `co135`（V3 citation 扫描）判 FAIL ⇒ "
          "runner **首轮停机**（`unexpected_nonzero`）；须**再跑一次**方收敛（非任意态可单次重启）。",
  "disposition": "CO-180：① **如实登记**该固有滞后（不可在不让步 co135 判据的前提下消除：co135/co136 自身亦被 boundary pin ⇒ "
                 "其 pin 只能在它们运行后才新鲜）；② **文档化缓解** = 首轮若在 `co135` 停机，**重跑**同一规范序即收敛"
                 "（工具本体已支持 `--max-iter`；`co120` 在首轮的写入使次轮边界刷新到稳定值）；③ 结构性下一候选见 `next`。",
  "status": "CLOSED",
  "next": "结构性候选（下轮）：runner 增**受控 warm-up 轮**（显式声明、机判、仅首轮豁免 pin-滞后类步且**须给出变更检测证据**），"
          "或令 `co135` 的 pin 判据**显式接受「滞后一轮」**并以牙齿证明（禁静默放宽）。",
  "evidence": ["CO-180 实测（改 co106 记录后首轮）：runner 在 `co135_review_hygiene` 停机（class=unexpected_nonzero、stderr 空）；"
               "其 `V3_boundary_citations.citation_scan_clean=False`，失配 = boundary 历史区段 7 处 co120 pin（cite 8823aba680541646 / "
               "actual 8469fb63b19664c0）",
               "CO-180 实测（重跑）：runner **converged（iterations 3）**，48 步 did_work 全 True、stray 全空；"
               "稳态（无上游变更）下则 2 轮收敛"],
  "refs": ["CO-180", "CO-166", "CO-135", "CO-120", "CO-77"], "closed_by": ["CO-180"]},
]

MARK = ("；**CO-180（L2 自裁 · 牙齿判决完整性）**：① 非白名单步的自检牙齿**只记不判** ⇒ "
        "`p3_v57_co164_order_runner.py` 升 **CO-169.5**（`step_declared_teeth()` 依 CO-174 声明产物派生 + "
        "`step_teeth_failed` + t15）；② `co106` 聚合提前/聚合键混入 `teeth`/两项恒真 checks ⇒ **CO-106.5**；"
        "③ `co78` 的 `teeth` 为散文串 ⇒ **CO-78.3**（co180:G-1/G-2/G-3）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co180:" + it["id"]
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
