#!/usr/bin/env python3
"""CO-192 — **非执行者对抗复评 CO-187..CO-191 的 L2 自裁处置**：findings 入登记簿（幂等 upsert）+ counts 复算。

对象 = `m13_v57_co192_rev19_co187_co191_review.json`（as-found @`52235b5`；verdict PASS_WITH_FINDINGS，F-1..F-4 全 low）。
只改 `L2/input_defect_register_v1.json`（按 `finding` 键 upsert；`meta.counts` 由 items 重算）。
CLI: python3 tools/p3_v57_co192_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
REVIEW = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co192_rev19_co187_co191_review.json"

ITEM_REF = "CO-192（runner 升 **CO-192.1**）"
ADD = [
    {"finding": "co192:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "牙齿卫生棘轮**容器形态仍漏计**：`|=`（AugAssign）/ 嵌套下标 `rec[\"teeth\"][k]` / dict 推导 "
             "`{k: True for k in …}` / `__setitem__` / Attribute 目标 `self.teeth[k]` / 下标赋别名 "
             "`rec[\"teeth\"]=<Name>` 一律 `n_teeth=0`（既不计数亦不报 constant）⇒ 恒真齿可经这些形态加入而不被 t18 截。",
     "disposition": ITEM_REF + "：`teeth_hygiene_scan` 容器判据改**节点形态无关** + 上述 6 类一律纳扫；"
                    "t18 合成正控同步扩展（6 类各须 `n_teeth≥1` 且报 constant）。",
     "status": "CLOSED", "next": "新增牙齿书写形态须先入 t18 合成控；漏计即停机（R-CO187-1 续）。",
     "evidence": ["复评负控（内存注入、零落盘）：6 类形态 as-found `constant_teeth` 全空 ↔ 现行全非空（P1/P2）",
                  "现行 ORDER 工具全扫 0 违规（棘轮保持零违规；齿数下限不变）"],
     "refs": ["CO-192", "CO-187"], "closed_by": ["CO-192"]},
    {"finding": "co192:F-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "md 写/拷形态仍漏计：`Path.open(w)` / `shutil.move` / `os.replace|rename` 目的一律 `md_write_scan()`==[] ⇒ "
             "此类 `.md` 产物既不在 pin、t20 亦不截（可落出受控集）。",
     "disposition": ITEM_REF + "：`md_write_scan` 补 `Path.open(w)`（写模式）+ `shutil.move` + `os.replace|rename` 目的；"
                    "t20 合成正控同步扩展。",
     "status": "CLOSED", "next": "新增 md 写/拷形态须先入 t20 合成控（R-CO187-2 续）。",
     "evidence": ["复评负控：3 形态 as-found `[]` ↔ 现行命中目的 basename（P3/P4）",
                  "现行 ORDER 工具对新增形态 0 命中（潜在面、零基线冲击）"],
     "refs": ["CO-192", "CO-187"], "closed_by": ["CO-192"]},
    {"finding": "co192:F-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "boundary 读取者判据可绕过：`D.open().read()` / `io.open(B).read()` 形态（源内无 `read_text`/`read_bytes` 字面）"
             "判 False ⇒ t21「读取者全集」机判可被此形态静默绕过。",
     "disposition": ITEM_REF + "：`boundary_read_scan` 读指标补 `.read(` / `io.open(`；t21 合成正控同步扩展。",
     "status": "CLOSED", "next": "boundary 新读取形态须先入 t21 合成控；仅引用（写/常量）不计读取者。",
     "evidence": ["复评负控：2 形态 as-found False ↔ 现行 True（P5/P5b）；写/只读他件仍 False（P6c 灵敏度对偶）"],
     "refs": ["CO-192", "CO-187"], "closed_by": ["CO-192"]},
    {"finding": "co192:F-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "R-CO191-1「**全部**声明 verdict 一律判决」对**白名单步**不生效：主循环以 `if cls == \"ok\"` 为门槛 ⇒ "
             "`expected_nonzero` 步（`co146_jlc_dfm_gate`）的**副**声明产物 verdict 不被运行期判决；副值为其声明 FAIL 之外的"
             "非 PASS 值（如 ERROR）即静默逃逸。（同值为 `declared_whitelist`，属预期，不可分。）",
     "disposition": ITEM_REF + "：新增 `all_verdicts_gate(cls, step, …)` —— **放行档**（`ok` **与** `expected_nonzero`）"
                    "一律施加全 verdict 判决；主循环改用该纯函数；t25 合成正负控同步扩展。",
     "status": "CLOSED", "next": "放行档判定须一律含全 verdict 判决（R-CO191-1 续）；停机类/超时档不受影响。",
     "evidence": ["复评负控（旧↔新判别）：`expected_nonzero` + 副 verdict=ERROR ⇒ as-found 次序**不判**（停 expected_nonzero）"
                  "↔ `all_verdicts_gate` 判 `undeclared_nonpass_verdict`（P6/P6b）",
                  "对偶：`ok`+已声明非 PASS（co146_pm_eval FAIL）仍放行；`step_timeout` 档不被覆盖"],
     "refs": ["CO-192", "CO-191", "CO-185"], "closed_by": ["CO-192"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    have = {i["finding"] for i in reg["items"]}
    added = []
    for it in ADD:
        if it["finding"] not in have:
            reg["items"].append(it)
            added.append(it["finding"])
    note = ("；**CO-192（非执行者对抗复评 CO-187..CO-191 + L2 自裁处置）**：+4 TOOL_DEFECT"
            "（`co192:F-1..F-4`，全 CLOSED；runner 升 CO-192.1 —— 扫描形态完备 + 放行档全 verdict 判决）。")
    if "CO-192（非执行者对抗复评" not in reg["meta"].get("updated_by", ""):
        reg["meta"]["updated_by"] = reg["meta"].get("updated_by", "") + note
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rev = json.loads(REVIEW.read_text(encoding="utf-8"))
    print(json.dumps({"added": added, "counts": reg["meta"]["counts"],
                      "review_verdict": rev["verdict"], "review_findings": [f["id"] for f in rev["findings"]],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
