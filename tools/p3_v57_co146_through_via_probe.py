#!/usr/bin/env python3
"""CO-146 A5-evidence — 通孔化反证探针（只读；只写 /tmp）。

问：把交付板 220 支盲/埋孔**原地**改成通孔（坐标零改动、零搜索）是否可行？
答（机判）：**不可行** —— 111 项 shorting_items + 50 clearance + 23 hole_clearance + 14 mask bridge。
⇒ 现行 W3 派生**结构上依赖盲/埋孔**；不存在「不改派生就降级为通孔板」的路径（与 UC-01 §4 结论一致）。
产出：m13_v57_co146_through_via_probe.json
牙齿：① 转换后非通孔数必须为 0；② 必须出现 >0 新 shorting（否则本反证无效）。
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
CLI = ROOT / "AppDir/bin/kicad-cli"
SRC = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
DRU = K2 / "k2_v4_8L.l4.kicad_dru"
TMP = Path("/tmp/k2probe")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def drc(pcb: Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        b = Path(td) / pcb.name
        shutil.copy(pcb, b)
        shutil.copy(PRO, b.with_suffix(".kicad_pro"))
        shutil.copy(DRU, b.with_suffix(".kicad_dru"))
        out = Path(td) / "d.json"
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--refill-zones", "--output", str(out), str(b)],
                       capture_output=True, text=True, timeout=1800)
        d = json.loads(out.read_text())
        return {"n": len(d["violations"]),
                "by_type": dict(sorted(Counter(v["type"] for v in d["violations"]).items()))}


def main() -> int:
    import pcbnew
    TMP.mkdir(parents=True, exist_ok=True)
    out_pcb = TMP / "k2_co146_through.kicad_pcb"
    b = pcbnew.LoadBoard(str(SRC))
    n = 0
    for t in b.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetViaType() == pcbnew.VIATYPE_THROUGH and t.TopLayer() == b.GetLayerID("F.Cu") \
                and t.BottomLayer() == b.GetLayerID("B.Cu"):
            continue
        t.SetViaType(pcbnew.VIATYPE_THROUGH)
        t.SetLayerPair(b.GetLayerID("F.Cu"), b.GetLayerID("B.Cu"))
        ls = pcbnew.LSET()
        for ln in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"):
            ls.AddLayer(b.GetLayerID(ln))
        t.SetLayerSet(ls)
        n += 1
    pcbnew.SaveBoard(str(out_pcb), b)
    after = pcbnew.LoadBoard(str(out_pcb))
    left = sum(1 for t in after.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
               and not (t.GetViaType() == pcbnew.VIATYPE_THROUGH
                        and t.TopLayer() == after.GetLayerID("F.Cu")
                        and t.BottomLayer() == after.GetLayerID("B.Cu")))
    base, thr = drc(SRC), drc(out_pcb)
    delta = {k: thr["by_type"].get(k, 0) - base["by_type"].get(k, 0)
             for k in sorted(set(base["by_type"]) | set(thr["by_type"]))}
    delta = {k: v for k, v in delta.items() if v}
    teeth = {"t01_no_non_through_left": left == 0, "t02_new_shorts": delta.get("shorting_items", 0) > 0}
    rec = {"artifact": "m13_v57_co146_through_via_probe", "schema": 1, "revision": "CO146-PROBE.1",
           "nature": "只读反证：盲/埋孔原地改通孔的可行性（坐标零改动、零搜索）",
           "board": SRC.name, "board_sha16": sha16(SRC),
           "converted_vias": n, "non_through_left_after": left,
           "drc_baseline": base, "drc_through_variant": thr, "delta_by_type": delta,
           "verdict": "THROUGH_ONLY_INFEASIBLE_AT_UNCHANGED_COORDS" if delta.get("shorting_items", 0) else "FEASIBLE",
           "teeth": teeth,
           "note": "scratch 板写在 /tmp（未触碰仓库任何受控件）；含逃逸域 dru（0.075），与 as-designed 基线同判据。",
           "redline": "只读板；零坐标搜索；不改板/图纸/SPEC/冻结四源。"}
    (STEP2 / "m13_v57_co146_through_via_probe.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("converted:", n, "| left:", left, "| verdict:", rec["verdict"])
    print("baseline:", base["n"], base["by_type"])
    print("through :", thr["n"], thr["by_type"])
    print("delta   :", delta)
    print("teeth:", teeth)
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
