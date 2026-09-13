#!/usr/bin/env python3
"""CO-176 — 闸自检强制 + 引证可核验性（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co164_order_runner.py`（CO-169.4，t14 +
allowlist `expected_step_teeth_failed`）与 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.3，t04/t05）
承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co176_gate_selfcheck_evidence.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "复现序执行器对**白名单步**只核 rc≠0 / 无 Traceback / 记录新鲜 / verdict==声明值，**不核该步 `teeth`** ⇒ "
          "白名单步（本工程唯一 = `co146_jlc_dfm_gate`）的**自检牙齿崩坏**会被「预期 FAIL」掩盖、收敛照过"
          "（与 CO-163「sha 稳定替代 rc」同族的**自检盲区**：判据说 OK 而其实自检已坏）。",
  "disposition": "CO-176：`p3_v57_co164_order_runner.py` 升 **CO-169.4** —— `EXPECTED_NONZERO` 声明 `teeth_path`；"
                 "新增纯函数 `teeth_all_true()`（bool 值 或 含 `ok` 的 dict；空/形状不明 ⇒ None **fail-closed**）+ "
                 "`record_json_path()`；`allowlist_decision()` 增 `teeth_ok` 判据 ⇒ 未全 True（含不可判）判 "
                 "**`expected_step_teeth_failed` 并停机**；静态齿 **t14**（正控/负控/形状不明）。",
  "status": "CLOSED", "next": "白名单豁免的是 **verdict**，不是**自检**；今后凡新增白名单步须声明 teeth_path。",
  "evidence": ["CO-176 实测：改前 `allowlist_decision` 无 teeth 参数（源码核）；dfm 记录 teeth 值仅在记录内、无消费方机判",
               "CO-176 修后：t14 全 True；负控（牙齿 False / 不可判）⇒ `expected_step_teeth_failed`；"
               "端到端变异测试：令 dfm 步产出 False 牙齿 ⇒ 复现序在该步**停机**（非收敛）"],
  "refs": ["CO-176", "CO-165", "CO-163", "CO-146"], "closed_by": ["CO-176"]},
 {"id": "G-2", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "JLC 能力表记录 `note` 声称「下表**逐条引用原文**」，但实测 **10/24 条非原文**：其中 "
          "`outer_copper_oz` / `min_track_width_mm` 为**静默删改**（无省略号标记即删去档位）、6 条省略式、1 条中文改写"
          "⇒ **DFM 判定（其记录随单进包 `06_rulings/`）的限值依据不可独立核验**，且有失实声明"
          "（与 CO-171「该串不存在于任何记录」同族：记录中的声明不可核验）。",
  "disposition": "CO-176：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.3** —— 能力表每条增 **`anchor`**"
                 "（抓取件**原文子串**，24/24 逐条实测命中）；新纯函数 `capability_citation_checks()` + 牙齿 "
                 "**t04**（锚点覆盖/非空/逐条原文 + **实测非原文集 == 声明集** + 声明项须有理由 + 原文数下限）/ "
                 "**t05**（灵敏度：篡改锚点即判不通过）；记录 `note` **订正**（去掉「逐条引用原文」的失实表述）+ "
                 "`citation` 块（n_verbatim 14/24 + not_verbatim 理由）；capability 记录升 **CO146-CAP.1**。",
  "status": "CLOSED", "next": "**残余如实登记**：`quote`/`value` 的**逐字**绑定未做（本项只绑 anchor；"
                              "彻底绑定须结构化抽取，作为下轮候选）。",
  "evidence": ["CO-176 实测（改前，去标签+空白归一后逐条比对）：原文 14/24；`Layer count 1-32 Layers` 等 10 条不在抓取件",
               "CO-176 修后：t04/t05 全 True；`anchor` 24/24 命中抓取件；非原文 10 条全部显式标注（含 2 条静默删改）"],
  "refs": ["CO-176", "CO-171", "CO-146"], "closed_by": ["CO-176"]},
]

MARK = ("；**CO-176（L2 自裁 · 闸自检强制 + 引证可核验性）**：① 白名单步**自检牙齿**此前不被收敛判定强制 ⇒ "
        "`p3_v57_co164_order_runner.py` 升 **CO-169.4**（`teeth_path` + `teeth_all_true` + "
        "`expected_step_teeth_failed` + t14）——rc≠0 只豁免 verdict、不豁免自检；② JLC 能力表引证实测 10/24 非原文"
        "（含 2 条**静默删改**）⇒ `p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.3**（逐条原文 `anchor` + t04/t05，"
        "记录 `note` 订正）＋ **CO146-CAP.1**（co176:G-1/G-2）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co176:" + it["id"]
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
