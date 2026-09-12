#!/usr/bin/env python3
"""CO-171 — ORDER_NOTES 内**记录派生数字**与来源记录的绑定（G-1/G-2）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.7）承载。
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co171_order_notes_record_figures.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co171:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**下单备注的阻抗观察值是无源字面量且**已陈旧**：`ORDER_NOTES` §5 写死「model-spread 观察值（+11.6%）」，"
          "但该串**不存在于任何记录**；阻抗表记录自身在 s=0.395mm（设计名义最宽间距）处 M2(HJ)=94.94Ω 对目标 85Ω "
          "即 **+11.69%**（且「模型间 spread」≈4.8% —— 措辞亦失实）。CO-163 的 t09 只绑定**声明定值表**的 7 个记号，"
          "**不覆盖**记录派生的观察值 ⇒ 客户可见的阻抗告警数字与来源记录脱钩且已漂移。",
  "disposition": "CO-171：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.7** —— 新增 `impedance_watch_figure(imp)`"
                 "（从记录派生 watch 下模型相对目标的最大偏离）+ `order_notes_record_figures(note, imp, dfm)`；"
                 "**订正备注字面量**为记录一致值（+11.6% → **+11.7%**，并订正措辞为「模型偏离观察值（M2(HJ) 相对目标）」、"
                 "补「模型间 spread ≈4.8%」）；牙齿 `t12_order_notes_record_figures` + `t12b`（灵敏度）；"
                 "记录落 `record_figures.impedance_watch`。",
  "status": "CLOSED", "next": "客户可见备注/图中的**记录派生**数字一律绑定来源记录；来源记录变更即须同步备注（否则 t12 FAIL）。",
  "evidence": ["CO-171 实测（修前）：`grep 11.6` 在所有 L2/L3 记录中**零命中**；记录 M2 于 0.395mm = 94.94Ω ⇒ +11.69%",
               "CO-171 复核（修后）：备注订正为 +11.7%；`record_figures.impedance_watch.dev_pct=11.69`（F.Cu/M2）；t12/t12b 全 True"],
  "refs": ["CO-171", "CO-163", "CO-170", "CO-146"], "closed_by": ["CO-171"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**ORDER_NOTES §7 的 DRC 计数无绑定**：备注写死「DRC（as-designed）：**42** 项，全部为 `lib_footprint_*`(**41**) + "
          "`silk_edge_clearance`(**1**)」，而 DFM 记录 `drc_as_designed` 是机判来源（`n=42`；`by_type` 中 "
          "`lib_footprint_issues=12` + `lib_footprint_mismatch=29` = 41）。现态一致，但**无任何牙齿**绑定 ⇒ 板/规则变更后"
          "重跑 DFM 闸即可能留下陈旧客户可见计数。",
  "disposition": "CO-171：`order_notes_record_figures` 追加判据 —— 备注须含 DFM 记录的 `drc_as_designed.n`（`42 项`）"
                 "与 `lib_footprint_*` 计数和（`(41)`），有锚正则匹配；记录落 `record_figures.drc_as_designed_n`。",
  "status": "CLOSED", "next": "凡备注内的机判计数须由来源记录派生并绑定。",
  "evidence": ["CO-171 实测：备注 42/41 与 DFM 记录一致（现态），但修前无牙齿绑定",
               "CO-171 复核（修后）：`order_notes_record_figures.drc_as_designed_total/drc_lib_footprint_sum` 全 True；t12b 注入 n=9999 ⇒ 判不通过"],
  "refs": ["CO-171", "CO-146", "CO-163"], "closed_by": ["CO-171"]},
]
MARK = ("；**CO-171（L2 自裁 · 交付物绑定）**：G-1 备注 §5 阻抗观察值为无源字面量且已陈旧（+11.6% vs 记录 +11.69%）⇒ "
        "CO146-PKG.7 增 `impedance_watch_figure` + `order_notes_record_figures` + t12/t12b 并**订正备注字面量**；"
        "G-2 备注 §7 DRC 计数无绑定 ⇒ 一并纳入 t12。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
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
