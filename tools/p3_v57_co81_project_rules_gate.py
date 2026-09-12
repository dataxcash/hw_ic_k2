#!/usr/bin/env python3
"""CO-81：【L2 可审计性 · 回归闸】受控工程文件设计规则 = 红线规则源（机判闸）。

把 CO-80 的 F-80-1 缺陷类固化为**可重复闸**：
  每个**受版本控制**的 `*.kicad_pro` 的 DRC 设计规则，必须等于**红线规则源**
  `_shared/eda_core/drc_rules.json:manufacturing`（+`hole_clearance:min`）；
  且 `rule_severities` 必须等于 JLC 模板 `tools/k2_jlc_template.kicad_pro`。

理由：`kicad-cli` 对 `<board>.kicad_pcb` 做 DRC 时会**自动选取**同名 `<board>.kicad_pro`；
若该文件规则与意图不符（如实测 F-80-1：kiCad 默认 0.2/0.5/0.3/0.5），
则**最自然的独立核查命令**会大面积误报（880 条），审计者据此误判板子不合格。

用法：python3 tools/p3_v57_co81_project_rules_gate.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
RULES = K2.parent / "_shared/eda_core/drc_rules.json"
TEMPLATE = K2 / "tools/k2_jlc_template.kicad_pro"
OUT = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co81_project_rules_gate.json"

# 工程文件键 -> drc_rules.json 路径
KEYMAP = {
    "min_track_width": ("manufacturing", "min_track_width"),
    "min_via_diameter": ("manufacturing", "min_via_diameter"),
    "min_via_annular_width": ("manufacturing", "min_annular_width"),
    "min_through_hole_diameter": ("manufacturing", "min_through_hole_diameter"),
    "min_copper_edge_clearance": ("manufacturing", "min_copper_edge_clearance"),
    "min_clearance": ("manufacturing", "min_clearance"),
    "min_hole_clearance": ("hole_clearance", "min"),
}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def guard(pro_rules: dict, expect: dict) -> dict:
    """返回 {key: (actual, expected)} 的失配集；空 = 通过（纯函数，便于负控）。"""
    return {k: (pro_rules.get(k), expect.get(k)) for k in expect if pro_rules.get(k) != expect.get(k)}


def main() -> int:
    rr = json.loads(RULES.read_text(encoding="utf-8"))
    expect = {k: rr[a][b] for k, (a, b) in KEYMAP.items()}
    tmpl = json.loads(TEMPLATE.read_text(encoding="utf-8"))["board"]["design_settings"]
    tmpl_sev = dict(tmpl["rule_severities"])
    tracked = subprocess.run(["git", "ls-files", "*.kicad_pro"], cwd=str(K2),
                             capture_output=True, text=True).stdout.split()
    rows, bad = [], []
    for rel in sorted(tracked):
        p = K2 / rel
        d = json.loads(p.read_text(encoding="utf-8"))["board"]["design_settings"]
        miss = guard(d["rules"], expect)
        sev = {k: (d["rule_severities"].get(k), tmpl_sev.get(k))
               for k in tmpl_sev if d["rule_severities"].get(k) != tmpl_sev.get(k)}
        ok = not miss and not sev
        rows.append({"file": rel, "sha16": s16(p), "ok": ok,
                     "rules_mismatch": miss, "severity_mismatch": sev})
        if not ok:
            bad.append(rel)
    # 负控（有齿）：喂坏输入必须被抓到
    neg = guard({**expect, "min_track_width": 0.2}, expect)
    pos = guard(dict(expect), expect)
    teeth = (neg == {"min_track_width": (0.2, expect["min_track_width"])}) and (pos == {})
    # 历史对照（F-80-1 实测原值，见 CO-80 记录）：闸必须抓到该状态
    f80_1 = {"min_track_width": 0.2, "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
             "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": 0.5,
             "min_clearance": 0.0, "min_hole_clearance": 0.25}
    hist = guard(f80_1, expect)
    hist_ok = len(hist) == 6      # min_hole_clearance 原本就一致
    teeth = teeth and hist_ok
    rec = {"artifact": "m13_v57_co81_project_rules_gate", "schema": 1, "revision": "CO-81.1",
           "nature": "L2 可审计性：受控工程文件设计规则 = 红线规则源 的回归闸",
           "authority_source": {"file": str(RULES.relative_to(K2.parent)), "sha16": s16(RULES),
                                "section": "manufacturing + hole_clearance:min"},
           "severity_reference": {"file": str(TEMPLATE.relative_to(K2)), "sha16": s16(TEMPLATE)},
           "expected": expect, "files_checked": rows,
           "violations": bad,
           "negative_control": neg, "positive_control": pos,
           "historical_control_F80_1": {"rules": f80_1, "mismatch": hist, "n_mismatch": len(hist)},
           "teeth_ok": teeth,
           "verdict": "PASS" if (not bad and teeth) else "FAIL",
           "rationale": "kicad-cli 对 <board>.kicad_pcb 自动选取同名 .kicad_pro；规则不符则自然核查命令大面积误报（F-80-1）。",
           "redline": "只读；不改任何工件；阈值取自红线规则源，不放宽。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "files": len(rows), "violations": bad,
                      "teeth_ok": teeth, "record": s16(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
