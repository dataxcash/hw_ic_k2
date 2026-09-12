#!/usr/bin/env python3
"""CO-102：【L2 PDN 自裁 · 项目内引擎承载】修正版 PDN 施加器（不改冻结 `_shared`）。

背景（CO-99 根因②③）：冻结 `eda_core/pdn_apply.py` 有 3 处施工侧缺陷 ——
  ① `add_track(..., width=0.5)` **字面量**，不读 SPEC `power_pad_connect.stub_width_mm`（rev-12 = 0.2）；
  ② via **不去重**（同网同址重复落孔）；
  ③ 与 `gnd_stitch_gen` 的 blocked schema 不对齐（本件从 SPEC 读 blocked）。
本件按既定自裁（`_shared` **不解冻**、施工侧**改由项目内引擎承载**）提供**项目内**施加器：
坐标**逐字取自 SPEC**（零搜索、零自由度），仅修正上述三处施工侧口径。

CLI:
  ../AppDir/usr/bin/python3.11 tools/p3_v57_co102_pdn_apply_local.py --spec S --board B [--stage all]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pcbnew

K2 = Path(__file__).resolve().parents[1]
KICAD_CLI = K2.parent / "AppDir/bin/kicad-cli"
SCRATCH = K2 / ".co102_dryrun"

LAYER_MAP = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu,
             "In3.Cu": pcbnew.In3_Cu, "In4.Cu": pcbnew.In4_Cu, "In5.Cu": pcbnew.In5_Cu, "In6.Cu": pcbnew.In6_Cu}
VIA_DRILL, VIA_DIA = 0.2, 0.35


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def ensure_net(board, netname):
    nc = board.GetNetcodeFromNetname(netname)
    if nc > 0:
        return nc
    n = pcbnew.NETINFO_ITEM(board, netname)
    board.Add(n)
    return n.GetNetCode()


def add_zone(board, netname, layer, pts):
    z = pcbnew.ZONE(board)
    z.SetLayer(LAYER_MAP[layer])
    z.SetNetCode(ensure_net(board, netname))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetLocalClearance(mm(0.2))
    z.SetThermalReliefGap(mm(0.2))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.AddPolygon(pcbnew.VECTOR_VECTOR2I([vec(p[0], p[1]) for p in pts]))
    board.Add(z)


class Placer:
    def __init__(self, board):
        self.b = board
        self.vias = set()      # 去重键 (net, x, y)
        self.stats = {"zones": 0, "vias": 0, "vias_deduped": 0, "tracks": 0, "blocked": []}

    def via(self, net, x, y):
        k = (net, round(x, 3), round(y, 3))
        if k in self.vias:                 # ① 去重
            self.stats["vias_deduped"] += 1
            return
        self.vias.add(k)
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(vec(x, y)); v.SetDrill(mm(VIA_DRILL)); v.SetWidth(mm(VIA_DIA))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); v.SetLayerSet(ls)
        v.SetNetCode(ensure_net(self.b, net))
        self.b.Add(v); self.stats["vias"] += 1

    def track(self, net, layer, p0, p1, width):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(vec(*p0)); t.SetEnd(vec(*p1)); t.SetWidth(mm(width)); t.SetLayer(LAYER_MAP[layer])
        t.SetNetCode(ensure_net(self.b, net))
        self.b.Add(t); self.stats["tracks"] += 1


def apply(spec_path: str, board_path: str, stage: str = "all") -> dict:
    spec = json.loads(open(spec_path).read())
    zd = spec.get("pd", {}).get("zone_defs", {})
    if not zd:
        raise SystemExit("[infra] SPEC 缺 pd.zone_defs")
    stub_w = float(zd.get("power_pad_connect", {}).get("stub_width_mm", 0.5))   # ② 读 SPEC
    b = pcbnew.LoadBoard(board_path)
    P = Placer(b)
    if stage in ("zone", "all"):
        for g in zd.get("gnd_planes", []):
            add_zone(b, g["net"], g["layer"], g["polygon"]); P.stats["zones"] += 1
        for pz in zd.get("power_zones", []):
            polys = pz.get("polygons", []) or ([pz["polygon"]] if pz.get("polygon") else [])
            for poly in polys:
                add_zone(b, pz["net"], pz["layer"], poly); P.stats["zones"] += 1
            for v in pz.get("vias", []):
                pos = v["pos"]
                seq = pos if (pos and isinstance(pos[0], list)) else [pos]
                for x, y in seq:
                    P.via(v.get("net", pz["net"]), x, y)
            for seg in pz.get("in6_segments", []):
                pts = seg["pts"]
                for i in range(len(pts) - 1):
                    P.track(seg.get("net", pz["net"]), "In6.Cu", pts[i], pts[i + 1], seg.get("width", 0.5))
            for seg in pz.get("segments", []):
                pts = seg if isinstance(seg[0][0], list) else seg
                for i in range(len(pts) - 1):
                    P.track(pz["net"], pz["layer"], pts[i], pts[i + 1], pz.get("width", 0.5))
        for v in zd.get("decoupling_via_to_plane", {}).get("vias", []):
            P.via(v.get("net", "GND"), v["pos"][0], v["pos"][1])
    if stage in ("connect", "all"):
        for c in zd.get("gnd_stitch_via", {}).get("coordinates", []):
            if c.get("blocked") or c.get("status") == "blocked":      # ③ blocked 口径
                P.stats["blocked"].append(f"stitch:{c.get('net')}@{c.get('x')},{c.get('y')}")
                continue
            P.via(c.get("net", "GND"), c["x"], c["y"])
        for e in zd.get("power_pad_connect", {}).get("entries", []):
            P.track(e["net"], "F.Cu", e["pad_pos"], e["via_pos"], stub_w)
            P.via(e["net"], e["via_pos"][0], e["via_pos"][1])
    b.Save(board_path)
    return {"stub_width_mm": stub_w, **P.stats}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _drc(board: Path, out: Path) -> int:
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all",
                    "--refill-zones", "--output", str(out), str(board)], capture_output=True, text=True, timeout=900)
    return len(json.loads(out.read_text())["violations"])


def verify(spec: str, board: str, out: str) -> int:
    """scratch 三态 DRC：baseline / 冻结引擎 / 项目内引擎（只记稳定量）。"""
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)
    src = Path(board)
    for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
        s = Path(str(src).replace(".kicad_pcb", suf))
        if s.exists():
            shutil.copy(s, SCRATCH / s.name)
    sc = SCRATCH / src.name
    base = _drc(sc, SCRATCH / "drc_base.json")
    # 冻结引擎
    sys.path.insert(0, str(K2.parent / "_shared"))
    import eda_core.pdn_apply as frozen          # noqa: E402
    rc = frozen.main(["--spec", spec, "--board", str(sc), "--stage", "all"])
    frozen_out = (rc if isinstance(rc, int) else 0)
    frozen_drc = _drc(sc, SCRATCH / "drc_frozen.json")
    # 项目内引擎（重开 scratch）
    for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
        s = Path(str(src).replace(".kicad_pcb", suf))
        if s.exists():
            shutil.copy(s, SCRATCH / s.name)
    st = apply(spec, str(sc), "all")
    local_drc = _drc(sc, SCRATCH / "drc_local.json")
    rec = {"baseline_violations": base, "frozen_violations": frozen_drc, "local_violations": local_drc,
           "frozen_delta": frozen_drc - base, "local_delta": local_drc - base,
           "local_apply": st, "frozen_rc": frozen_out,
           "stability_note": "只记 violation 总数（稳定量）；逐类型随 refill/UUID 浮动不入记录",
           "scratch": str(SCRATCH.relative_to(K2))}
    Path(out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-102 verify: baseline=%d frozen=%d(+%d) local=%d(+%d) stub_w=%s vias=%s deduped=%s" %
          (base, frozen_drc, frozen_drc - base, local_drc, local_drc - base,
           st["stub_width_mm"], st["vias"], st["vias_deduped"]))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CO-102 项目内 PDN 施加器（修正施工侧三处口径）")
    ap.add_argument("--spec", default=str(K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-16.json"))
    ap.add_argument("--board", default=str(K2 / "k2_v4_8L.l4.kicad_pcb"))
    ap.add_argument("--stage", default="all", choices=["zone", "connect", "all"])
    ap.add_argument("--verify", action="store_true", help="scratch 三态 DRC 对比（baseline/冻结/项目内）")
    ap.add_argument("--out", default=str(K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co102_pdn_local_apply.json"))
    a = ap.parse_args(argv)
    if a.verify:
        return verify(a.spec, a.board, a.out)
    st = apply(a.spec, a.board, a.stage)
    print(f"OK stage={a.stage} zones={st['zones']} vias={st['vias']} (deduped={st['vias_deduped']}) "
          f"tracks={st['tracks']} stub_w={st['stub_width_mm']} blocked={len(st['blocked'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
