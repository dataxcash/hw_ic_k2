#!/usr/bin/env python3
"""DIR-14 — **DFM 逐项判定（对 JLC HDI 通道）· 证据生成器**（承监理指令 #14 验收判据）

用途：给出一条**可复现命令**，其**原始输出**即「DFM 对 HDI 通道」之逐项判定（替代手写映射）。
本器**不是**检查齿（不入规范序、不新增 runner 静态齿）：它消费既有闸之**机器实测**
（`m13_v57_co146_jlc_dfm_gate.json`），套用 **A 冻结（HDI）** 之通道语义与**已裁定**之处置，输出证据件。

判据（fail-closed，任一项不可判 ⇒ 不 PASS）：
  P0 冻结工艺 = A（读判据件 `owner_ruling.route_frozen`）；
  P1 输入为交付板实测（闸记录 `board_sha16` == 交付板 sha16）；
  P2 HDI 支撑锚：能力抓取件（pinned）须**含** blind/buried+HDI advanced option 之**归一原文**；
  P3 阻焊项之处置须有**已裁定**依据（L2 裁定件含 `ACCEPT_L2_WITH_FAB_REVIEW`）；
  P4 逐项映射：除「过孔类型（盲/埋孔）」与「阻焊桥/阻焊-铜净距」外，沿用机器判决；
     - 过孔类型：HDI 通道**支持**盲埋孔 ⇒ PASS（须经 P2）；
     - 阻焊项：机器判决 FAIL，但处置 = **ACCEPT_L2_WITH_FAB_REVIEW**（须经 P3）⇒ 记为 ACCEPT（**非** PASS，非静默）。
  verdict = `PASS_HDI`（无一 PASS 项被记为 PASS；且 ACCEPT 项数计入 evidence）；rc=0；否则 rc=1。

CLI: python3 tools/p3_v57_co146_jlc_dfm_hdi_report.py
"""
from __future__ import annotations
import hashlib, html, importlib.util, json, re, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2D = K2 / "pm_gate/artifacts/k2_v4/L2"
GATE_REC = S2 / "m13_v57_co146_jlc_dfm_gate.json"
CAP = S2 / "m13_v57_co146_jlc8_capability.json"
SRC = S2 / "m13_v57_co146_jlc_capability_source.html"
CRIT = L2D / "process_route_criteria_v1.json"
RULING = L2D / "L2_RULING_fab_capability_binding_A_hdi_v1.md"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT_JSON = S2 / "m13_v57_co146_jlc_dfm_hdi.json"
OUT_MD = S2 / "m13_v57_co146_jlc_dfm_hdi.md"
BLIND_ITEM, MASK_ITEM = "过孔类型（盲/埋孔）", "阻焊桥 / 阻焊-铜净距"
ACCEPT = "ACCEPT_L2_WITH_FAB_REVIEW"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main() -> int:
    gate = json.loads(GATE_REC.read_text(encoding="utf-8"))
    crit = json.loads(CRIT.read_text(encoding="utf-8"))
    cap = json.loads(CAP.read_text(encoding="utf-8"))
    src = norm(SRC.read_text(encoding="utf-8", errors="replace"))
    ruling = RULING.read_text(encoding="utf-8") if RULING.exists() else ""

    # P0..P3 前置（fail-closed）
    p0 = (crit.get("owner_ruling") or {}).get("route_frozen") == "A"
    board_now = s16(BOARD)
    p1 = gate.get("board_sha16") == board_now
    # 锚取自**单一真源** = DFM 闸工具之 `CAPABILITY_ANCHORS`（逐条为抓取件归一原文子串）
    _spec = importlib.util.spec_from_file_location("_dfmgate", K2 / "tools/p3_v57_co146_jlc_dfm_gate.py")
    _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
    faq_anchor = _m.CAPABILITY_ANCHORS["blind_buried_faq"]
    p2 = norm(faq_anchor) in src
    p3 = ACCEPT in ruling

    items = []
    for it in gate.get("items", []):
        name, verd = str(it.get("item")), str(it.get("verdict"))
        if BLIND_ITEM in name:
            items.append({"item": name, "jlc_limit_std": it.get("jlc_limit"), "measured": it.get("measured"),
                          "machine_std": verd, "hdi": "PASS" if p2 else "UNJUDGED",
                          "basis": "HDI/advanced 通道支持盲埋孔（抓取件归一原文锚；P2）"})
        elif MASK_ITEM in name:
            items.append({"item": name, "jlc_limit_std": it.get("jlc_limit"), "measured": it.get("measured"),
                          "machine_std": verd, "hdi": ACCEPT if p3 else "UNJUDGED",
                          "basis": "既有 L2 裁定（CO-147 R3）：随板厂工程评审提交，不触铜几何（P3）"})
        else:
            items.append({"item": name, "jlc_limit_std": it.get("jlc_limit"), "measured": it.get("measured"),
                          "machine_std": verd, "hdi": verd, "basis": "沿用机器实测（通道无关）"})

    n_pass = sum(1 for x in items if x["hdi"] == "PASS")
    n_accept = sum(1 for x in items if x["hdi"] == ACCEPT)
    n_fail = sum(1 for x in items if x["hdi"] not in ("PASS", ACCEPT))
    pre = p0 and p1 and p2 and p3
    verdict = "PASS_HDI" if (pre and n_fail == 0) else "FAIL"

    out = {"artifact": "m13_v57_co146_jlc_dfm_hdi", "schema": 1, "revision": "DIR-14",
           "nature": "DFM 逐项判定对 **JLC HDI 通道**（工艺 A 冻结）；消费既有闸机器实测 + 通道语义 + 已裁定处置",
           "board": {"path": BOARD.name, "sha16": board_now},
           "preconditions": {"P0_frozen_A": p0, "P1_gate_board_is_delivery": p1,
                             "P2_hdi_anchor_verbatim": p2, "P3_mask_disposition_ruled": p3},
           "evidence": {"gate_record": str(GATE_REC.relative_to(K2)), "gate_record_sha16": s16(GATE_REC),
                        "capability_source_sha256": cap.get("source_page_sha256"),
                        "mask_ruling": str(RULING.relative_to(K2))},
           "items": items,
           "summary": {"n_items": len(items), "n_pass": n_pass, "n_accept": n_accept, "n_fail": n_fail},
           "verdict": verdict, "rc": 0 if verdict == "PASS_HDI" else 1,
           "redline": "只读；不改板/SPEC/冻结四源；不把 ACCEPT 记作 PASS；判据值一律锚在 pinned 抓取件/已裁定件。"}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    L = [f"# DFM 逐项判定 — 交付板 vs **JLC HDI 通道**（DIR-14 / 工艺 A 冻结）\n",
         f"> 复现：`python3 tools/p3_v57_co146_jlc_dfm_hdi_report.py`｜板 `{board_now}`｜判据值锚 = pinned 抓取件 + 已裁定件\n",
         f"**verdict = {verdict}**｜{len(items)} 项：**{n_pass} PASS + {n_accept} ACCEPT + {n_fail} FAIL**"
         f"｜前置 P0..P3 = {[p0, p1, p2, p3]}\n",
         "| 项 | JLC 限（标准页） | 本板实测 | 机器(标准通道) | **HDI 通道** | 依据 |", "|---|---|---|---|---|---|"]
    for x in items:
        L.append(f"| {x['item']} | {x['jlc_limit_std']} | {x['measured']} | {x['machine_std']} | **{x['hdi']}** | {x['basis']} |")
    L += ["", f"> `ACCEPT` = 已由 L2 裁定接受并随单提交板厂工程评审（**非** PASS，**非**静默通过）；兜底修法已预先授权（见裁定件）。",
          f"> FAIL 项 = 0 ⇒ 可送样。原始机器实测见包内 `06_rulings/m13_v57_co146_jlc_dfm_gate.json`（sha16 `{s16(GATE_REC)}`）。"]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_pass": n_pass, "n_accept": n_accept, "n_fail": n_fail,
                      "P0": p0, "P1": p1, "P2": p2, "P3": p3,
                      "rec": s16(OUT_JSON), "md": s16(OUT_MD)}, ensure_ascii=False))
    return 0 if verdict == "PASS_HDI" else 1


if __name__ == "__main__":
    sys.exit(main())
