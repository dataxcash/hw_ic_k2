#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 含旧板身份字面量 ['f6273de6'] ⇒ **不可重放**（重跑会静默换板，禁默认重跑）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""CO-03：冻结 6L 骨架 -> 派生 8L 基线（**版本化新文件；冻结原件不动**）。

L2 依据：LAYOUT_CONSTITUTION 第二章（叠层=物理承载设计，裁判权=SI/PI 工程师）
         + 整改 #03（层数/层用途 = 容量闭合派生输出，无 owner/工单参数特权）
         + LID.1 派生（8L: F/In1(G)/In2(S)/In3(G)/In4(P)/In5(G)/In6(S)/B(S)）

Deltas（最小、可复核；任一期望子串缺失即 fail-fast 非零退出）：
  D1 层表：插入 In5.Cu(12) / In6.Cu(14)，与权威生成器 HEADER（k2_gen_v5.py:427-434）逐层一致
  D2 板框：Edge.Cuts 左边 (23,71)->(23,33) 修为 (23,79)->(23,33)（闭合；SPEC board.outline_y=[33,79]）

产出：k2/k2_v4_8L.kicad_pcb + provenance JSON（sha / 子串断言 / 8 层 / 闭合校验）。
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
SRC = K2 / "k2_v4.kicad_pcb"
DST = K2 / "k2_v4_8L.kicad_pcb"
PROV = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co03_stackup_realign.json"
SRC_SHA16 = "f6273de613f43d05"

D1_OLD = '\t\t(10 "In4.Cu" signal)\n'
D1_NEW = '\t\t(10 "In4.Cu" signal)\n\t\t(12 "In5.Cu" signal)\n\t\t(14 "In6.Cu" signal)\n'
D2_OLD = '(start 23 71)\n\t\t(end 23 33)'
D2_NEW = '(start 23 79)\n\t\t(end 23 33)'
CU_RE = re.compile(r'\s*\(\d+ "[^"]+\.Cu" (signal|power|mixed|jumper)\)$')


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    if sha(SRC)[:16] != SRC_SHA16:
        print(f"fail-fast: 冻结骨架 sha 漂移 {sha(SRC)[:16]} != {SRC_SHA16}")
        return 2
    for name, anchor in (("D1", D1_OLD), ("D2", D2_OLD)):
        if raw.count(anchor) != 1:
            print(f"fail-fast: {name} 锚点出现 {raw.count(anchor)} 次（期望 1）")
            return 3
    out = raw.replace(D1_OLD, D1_NEW, 1).replace(D2_OLD, D2_NEW, 1)
    DST.write_text(out, encoding="utf-8")

    cu = [l for l in out.splitlines() if CU_RE.match(l)]
    xs, ys, n_edges = set(), set(), 0
    for chunk in out.split("(gr_line")[1:]:
        if "Edge.Cuts" not in chunk:
            continue
        n_edges += 1
        m = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)", chunk)
        x1, y1, x2, y2 = map(float, m.groups())
        xs |= {x1, x2}; ys |= {y1, y2}
    frame_ok = xs == {23.0, 143.0} and ys == {33.0, 79.0} and n_edges == 4
    if len(cu) != 8 or not frame_ok:
        print(f"fail-fast: 自检失败 copper={len(cu)} frame_ok={frame_ok} xs={sorted(xs)} ys={sorted(ys)}")
        return 5

    prov = {
        "artifact": "m13_v57_co03_stackup_realign", "schema": 1, "revision": "CO-03.1",
        "authority": "L2 (LAYOUT_CONSTITUTION ch.2) + rectification #03 + LID.1 derivation",
        "src": {"path": str(SRC.relative_to(K2)), "sha256": sha(SRC)},
        "dst": {"path": str(DST.relative_to(K2)), "sha256": sha(DST)},
        "deltas": [
            {"id": "D1", "kind": "layer_table", "new": "+In5.Cu(12) +In6.Cu(14)",
             "basis": "k2_gen_v5.py:427-434 HEADER == LID.1 derived stackup (8L)"},
            {"id": "D2", "kind": "board_outline", "old": "Edge.Cuts left (23,71)->(23,33)",
             "new": "(23,79)->(23,33)",
             "basis": "SPEC board.outline_y=[33,79]; repair open contour (left y=71 vs right/bottom y=79)"},
        ],
        "selfcheck": {"copper_layer_lines": len(cu), "edge_cuts_segments": n_edges,
                      "frame_x": sorted(xs), "frame_y": sorted(ys), "frame_closed": frame_ok},
        "frozen_originals_untouched": True,
    }
    PROV.write_text(json.dumps(prov, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"dst": prov["dst"]["path"], "dst_sha16": prov["dst"]["sha256"][:16],
                      "copper": len(cu), "frame_closed": frame_ok,
                      "deltas": [d["id"] for d in prov["deltas"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
