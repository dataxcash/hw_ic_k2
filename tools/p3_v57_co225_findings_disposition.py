#!/usr/bin/env python3
"""CO-225 — 非执行者复评（CO-219..CO-224）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co225:F-1", "sev": "mid", "kind": "TOOL_DEFECT",
     "what": "**记录卫生 · boundary 两节零在记录内指纹**：§94（CO-221）与 §96（CO-223）之 `| 工件 | sha16 |` 表缺失（全 94 节中缺者恰为此二节 + §1..§7 早期节）"
             "⇒ 违 **R-CO212-1**（「任何 verdict 记录须与被评态在**同记录内**钉指纹…pin 漂移或**缺失即 fail-closed**」）；且该红线**无机判齿** ⇒ 违例态下 `--check` 仍全绿（同 CO-219 F-1「空真」族）。",
     "disposition": "CO-225（非执行者复评 · L2 自裁）：① §94/§96 **补**在记录内指纹表；② **入机判** runner 静态齿 `t35_judgment_surface_pinned`（名集钉定双臂："
                    "(i) boundary **每节**须带在记录内指纹，缺者须在显式历史豁免名集 `BOUNDARY_SECTION_FP_EXEMPT = {1..7}`；(ii) runner **静态齿名集**须等于 `STATIC_CHECKS_DECLARED`；"
                    "两臂皆带正/负控）⇒ 齿 **修前 FAIL / 修后 PASS**（判别力实测）。**R-CO225-1**。",
     "status": "CLOSED",
     "next": "boundary **每节**须带在记录内指纹；新增节若为历史豁免须进**显式名集**；执行器**静态齿名集**须钉定（防静默删齿 ⇒ 判据面空真）。",
     "evidence": ["修前：§94/§96 `sha16` 出现数 = 0；HEAD 版 runner `--check` 仍 36/36 全 True（违例不可见）",
                  "逐臂诊断（工作树版 +t35）：唯一失败臂 = ① 实件面（`boundary_fp_missing() == [94, 96]`）；② 名集等式 / 正控 / 负控皆 True",
                  "修后：`--check` 37/37 全 True；序收敛 rc=0 / 2 轮"],
     "refs": ["CO-212", "CO-219", "CO-221", "CO-223", "CO-224", "CO-225"], "closed_by": ["CO-225"]},
    {"finding": "co225:F-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**触发覆盖 · L2 自由度以「等外部输入」悬置**：§93 §3 备择项「层分配重指派以降 HDI 阶数」**无触发**，不采理由为「无新证据…**未知项属外部** DFM 答复」"
             "= **R-CO220-1** 明文所禁之**悬置**形态；且该表述**同源于手写裁定件** `L2_RULING_cross_page_y_interleave_v1.md`（仅补 boundary = 同源只补一半，反蹈 CO-223/224 覆辙）。",
     "disposition": "CO-225（非执行者复评 · L2 自裁）：① boundary §93 **补 T3**（DFM 答复或成本序显示现行 3 次层压代价不可接受 ⇒ 以「层分配重指派以降 HDI 阶数（**保持 8 层**）」为首动作开新 rev，"
                    "量化目标 **3 → ≤2**；须改层数/叠层拓扑 ⇒ **L1，升级 owner**）；② 裁定件 `L2_RULING_cross_page_y_interleave_v1.md` **加追注 §6**（T3 + 明示「不构成悬置」/「口径以 §93 与本节为准」）"
                    "；③ §98 以名集等式对账两处。**R-CO225-1**。",
     "status": "CLOSED",
     "next": "L2 自由度之「不动」须以**自裁 + 触发**落 boundary **并与裁定件同源**；禁以「等外部输入/等 owner」悬置（承 R-CO220-1 / R-CO223-1）。",
     "evidence": ["修前：§93 仅有 T1/T2；裁定件第 17 行「未知项属外部 DFM 答复」无对应触发",
                  "修后：§93 载 T3；裁定件 §6 追注载 T3；grep '层分配重指派' 于两处皆命中且皆载 T3/追注",
                  "修后：`--check` 37/37 全 True；序收敛 rc=0 / 2 轮"],
     "refs": ["CO-205", "CO-209", "CO-220", "CO-223", "CO-224", "CO-225"], "closed_by": ["CO-225"]},
    {"finding": "co225:F-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**名集域收窄（声明强于实测）**：§97（CO-224）声明「`grep 'GND via 阵列'` ⇒ 命中面**恰为上表 7 处**（名集等式：无未登记载明面、无缺项）」，但其名集**域** = 所声明 grep 目标（md 件）"
             "⇒ **漏** `L2/input_defect_register_v1.json`（`items[22].disposition` 亦载该义务时点口径）。实测该处口径**与 CO-222 一致**（无 fail-open），属「名集域未显式声明」（承 R-CO219-1；与 CO-96 F-4「scope 缺口」同族）。",
     "disposition": "CO-225（非执行者复评 · L2 自裁）：① §97 加**追注**（名集**域** = md 件；登记该第 8 面，pin 见 §98）；② §98 以 8 面名集等式复核；③ 登记簿入册本项。**R-CO225-1**。",
     "status": "CLOSED",
     "next": "名集等式须**显式声明其域**（所声明的 grep/枚举范围即域，域外之载明面须登记或纳入）；禁以「已登记项自洽」代替「域已覆盖」（承 R-CO219-1）。",
     "evidence": ["全库 `grep -rn 'GND via 阵列'` 命中 8 面；§97 名集只列 7 面（域 = md 件）",
                  "登记簿 `items[22].disposition` 载「义务时点**以 CO-222 为准**（条件动作 T1/T2）」⇒ 口径一致、无 fail-open",
                  "修后：§97 载域追注；§98 8 面名集等式成立"],
     "refs": ["CO-96", "CO-219", "CO-222", "CO-224", "CO-225"], "closed_by": ["CO-225"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def upsert_note(ub: str, mark: str, note: str) -> str:
    """注解 upsert：**原位**替换本段（右界 = 下一 `；**CO-` 起点 / 末尾）—— 禁无界裁尾、禁移段（R-CO197-4）。"""
    if mark in ub:
        i = ub.index(mark); j = ub.find("；**CO-", i + len(mark))
        return ub[:i] + note + (ub[j:] if j != -1 else "")
    return ub + note


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    by = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by:
            if reg["items"][by[it["finding"]]] != it:
                reg["items"][by[it["finding"]]] = it; updated.append(it["finding"])
        else:
            reg["items"].append(it); added.append(it["finding"])
    note = ("；**CO-225（非执行者对抗复评 CO-219..CO-224 + 同会话处置）**：+3 TOOL_DEFECT（`co225:F-1` boundary §94/§96 零在记录内指纹 ⇒ 违 R-CO212-1 且无机判齿"
            "（处置 = 补指纹表 + 静态齿 t35 名集钉定）；`co225:F-2` §93 备择项以「等外部 DFM 答复」悬置 ⇒ 违 R-CO220-1（处置 = +T3 且裁定件追注同源）；"
            "`co225:F-4` §97 名集域收窄（漏登记簿载明面，口径一致无 fail-open）（处置 = 追注 + 8 面名集等式）；皆 low~mid、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-225（非执行者对抗复评", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
