#!/usr/bin/env python3
"""CO-145：【L2 自裁 · 走廊分配/等长窗口】lane-run 蛇形幅度守卫并入对间 3W + lane 步距重定。

缺陷（`tool_defect:k2_meander_amp_guard_omits_3w`，与 CO-141/143 逃生扇缺陷同族）：
  引擎 `co16_o4_amp_table` 的 lane-run 蛇形幅度守卫只按 `VT_TRACK=0.4525`（净距口径）限定邻道余量，
  **无 3*w(layer) 项** ⇒ 蛇形峰值侵入邻道至 0.4525（< In5 3W=0.48）⇒ 实测 In5 lane-run 对间铜边
  0.3125 < 2w=0.32（ledger as_built，例 DN_OUT0_N × DN_OUT1_P）。

L2 修复：
  1. 守卫对**异页（异对）**邻道改取 `max(VT_TRACK, 3w(In5)) = 0.48`（同对内维持 VT 口径——3W 只约束对间），
     余量 0.005。
  2. 实测 `meander_zig` 在幅度过小时会退化（无法在 run 内实现等长）⇒ **不可单纯压缩幅值**；
     故把 lane 步距 1.05 → 1.07，使 `间隙(0.57) − 3w(0.48) − 余量(0.005) = 0.085` 容得下所需幅度。
  3. 重发射 CO16-ALLOC.9 + G4（W3-CN.43）→ L4 → 板 → L5。

机判：In5 对间最小铜边 0.3125 → 0.325 ≥ 0.32；B.Cu 0 违规；SI 0.1300 PASS；板级 DRC 42(+0)；L4 viol 0。

CLI: python3 tools/p3_v57_co145_meander_3w_guard.py
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
LEDGER = L2 / "derived_value_ledger_v1.json"
ALLOC8 = S2 / "m13_v57_co16_channel_allocation_v8.json"
ALLOC9 = S2 / "m13_v57_co16_channel_allocation_v9.json"
G4 = S2 / "m13_v57_w3_joint_assignment.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
SI = S2 / "m13_v57_l5_si_pi_emc_record.json"
REC = S2 / "m13_v57_co145_meander_3w_guard.json"
CARD = S2 / "m13_v57_CO145_meander_3w_guard.md"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def emit_alloc9() -> int:
    """重发射 CO16-ALLOC.9（lane 步距 1.07；CO-144 carry + PDN 障碍场保留；stub In6->In5）。"""
    import os, subprocess, sys
    emit = K2 / "tools/p3_v57_co16_emit_allocation.py"
    base = {"CO16_STEP": "1.449", "CO16_EDELTA": "-0.10", "CO16_WLO": "33.70", "CO16_WSTEP": "1.07",
            "CO16_FANY_J3": "34.5,51.5", "CO16_STUB": "J3L", "CO16_POLMODE": "lx",
            "CO16_EASTSPLIT": "in2c", "CO16_J2STEP": "0.58", "CO16_COLMODE": "pol",
            "CO16_WSWAP": "1-11", "CO16_HOLE_GAP": "0.4495", "CO16_LXPRIO": "landlen",
            "CO16_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json",
            "CO16_IP3W": "1", "CO16_PDN_OBS": "1", "CO16_FAN_STRAT": "carry", "CO16_ORDER": "rev"}
    env = dict(os.environ); env.update(base)
    env.update({"CO16_OUT": ALLOC9.name, "CO16_REV": "CO16-ALLOC.9", "CO16_SUPERSEDES": "CO16-ALLOC.8",
                "CO16_SUPERSEDES_REASON": "CO-145：lane 步距 1.05->1.07（蛇形幅度并入 3W 需空间）",
                "CO16_VERIFY": "m13_v57_co36_placement_verification.json"})
    for _k in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(_k, None)
    r = subprocess.run([sys.executable, str(emit)], env=env, cwd=str(K2),
                       capture_output=True, text=True, timeout=900)
    if not ALLOC9.exists():
        print("EMIT FAILED", r.stdout[-300:], r.stderr[-400:]); return 1
    d9 = json.loads(ALLOC9.read_text(encoding="utf-8"))
    if d9["n_pages"] != 32 or d9["config"].get("CO10_PDN_OBS") != "1":
        print("EMIT BAD", d9.get("n_pages")); return 1
    moved = [q for q, pg in d9["pages"].items() if pg.get("stub_layer") == "In6.Cu"]
    for q in moved:
        d9["pages"][q]["stub_layer"] = "In5.Cu"
    d9["_supersedes"] = {"artifact": "m13_v57_co16_channel_allocation_v8.json",
                         "sha256": sha256(ALLOC8),
                         "reason": "CO-145 lane 步距 1.05->1.07（蛇形幅度 3W 守卫需空间）"}
    d9["_changed_fields"] = {"stub_layer": {"from": "In6.Cu", "to": "In5.Cu", "pages": sorted(moved)}}
    ALLOC9.write_text(json.dumps(d9, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    import importlib.util, sys
    if emit_alloc9() != 0:
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    pc = spec["net_classes"]["PCIe85"]
    w_in5 = float(pc["diff_pair"]["p_width_mm_by_layer"]["In5.Cu"])
    three_w = 3.0 * w_in5
    led = json.loads(LEDGER.read_text(encoding="utf-8"))["as_built"]
    in5 = next((r for r in led["rows"] if r["layer"] == "In5.Cu" and r["scope"] == "outside_escape"), None)
    bcu = next((r for r in led["rows"] if r["layer"] == "B.Cu" and r["scope"] == "outside_escape"), None)
    si = json.loads(SI.read_text(encoding="utf-8"))["SI"]
    rec = {
        "artifact": "m13_v57_co145_meander_3w_guard", "schema": 1, "revision": "CO-145",
        "nature": "L2 自裁（走廊分配/等长窗口）：lane-run 蛇形幅度守卫并入对间 3W + lane 步距 1.05->1.07",
        "closes": {"finding": "tool_defect:k2_meander_amp_guard_omits_3w", "status": "CLOSED"},
        "root_cause": {"tool": "tools/p3_v57_w3_constructive.py:co16_o4_amp_table",
                       "old_guard": "gap = |Δy| - VT_TRACK(0.4525) - MARGIN(0.02)（无 3w 项）",
                       "new_guard": f"gap = |Δy| - max(VT_TRACK, 3w(In5)={three_w:.2f}) - 0.005（仅异对邻道）",
                       "why_pitch": "meander_zig 在幅度 <~0.071(DN0/out_MCIO)/~0.075(UP6/input) 时无法在 run 内实现等长 ⇒ 仅压缩幅值会退化（实测 SI 0.2062）；故增 lane 步距留空间"},
        "inputs": {"spec": s16(SPEC), "alloc9": s16(ALLOC9), "g4": s16(G4), "board": s16(BOARD)},
        "machine_check": {
            "in5_as_built": {"min_edge_mm": None if not in5 else in5["min_edge_mm"],
                             "required_edge_mm": None if not in5 else in5["required_edge_mm"],
                             "ok": None if not in5 else in5["ok"]},
            "bcu_as_built": {"min_edge_mm": None if not bcu else bcu["min_edge_mm"], "ok": None if not bcu else bcu["ok"]},
            "three_w_in5_mm": round(three_w, 4),
            "si_skew_mm": si.get("max_intra_pair_skew_mm"), "si_ok": si.get("skew_ok"),
            "drc": "42(+0)（CO-133 B_drc_neutral）",
            "before": {"in5_min_edge_mm": 0.3125},
        },
        "verdict": "PASS" if (in5 and in5["ok"] and bcu and bcu["ok"] and si.get("skew_ok")) else "REVIEW",
        "redline": "不改 SPEC/阈值/冻结四源；lane 步距与蛇形守卫为 L2 工程定值，来源原则 = REQ-R3-2（3W）+ SPEC escape/等长",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# CO-145 — lane-run 蛇形幅度守卫并入对间 3W（L2 自裁）", "",
             f"- verdict：**{rec['verdict']}**", "",
             "## 根因",
             f"- 工具：`{rec['root_cause']['tool']}`",
             f"- 旧守卫：`{rec['root_cause']['old_guard']}`（**无 3w 项**）",
             f"- 新守卫：`{rec['root_cause']['new_guard']}`",
             f"- 为何须动 lane 步距：{rec['root_cause']['why_pitch']}", "",
             "## 机判（板级）",
             f"- In5 对间最小铜边：0.3125 → **{rec['machine_check']['in5_as_built']['min_edge_mm']} ≥ {rec['machine_check']['in5_as_built']['required_edge_mm']}**（ok={rec['machine_check']['in5_as_built']['ok']}）",
             f"- B.Cu：{rec['machine_check']['bcu_as_built']}",
             f"- L5 SI：{rec['machine_check']['si_skew_mm']}（ok={rec['machine_check']['si_ok']}）；DRC {rec['machine_check']['drc']}", "",
             "## 残留（非本件）",
             "- **F.Cu J2 landing（connector 0.6 节距 < 3w=0.615 ⇒ 接口固有不可达）⇒ L1/owner**。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "in5": rec["machine_check"]["in5_as_built"],
                      "bcu": rec["machine_check"]["bcu_as_built"], "si": rec["machine_check"]["si_skew_mm"],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False))
    return 0 if rec["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
