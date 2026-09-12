#!/usr/bin/env python3
"""CO-102：【L2 PDN 自裁 · 项目内引擎承载】修正版 PDN 施加器（不改冻结 `_shared`）。

背景（CO-99 根因②③）：冻结 `eda_core/pdn_apply.py` 有 3 处施工侧缺陷 ——
  ① `add_track(..., width=0.5)` **字面量**，不读 SPEC `power_pad_connect.stub_width_mm`（rev-12 = 0.2）；
  ② via **不去重**（同网同址重复落孔）；
  ③ 与 `gnd_stitch_gen` 的 blocked schema 不对齐（本件从 SPEC 读 blocked）。
本件按既定自裁（`_shared` **不解冻**、施工侧**改由项目内引擎承载**）提供**项目内**施加器：
坐标**逐字取自 SPEC**（零搜索、零自由度），仅修正上述施工侧口径。
CO-133 追加④**幂等性**（purge-then-add）：施加前先删除**本阶段将重发**的 PDN 网铜（zone/via/track），
与 `l4_apply_drawing`「删该网旧 track/via → 按图纸落」同构 ⇒ 板已含 PDN 铜时重跑为不动点，
`--verify` 三态在任何起态下均可复现（避免重复落孔/重复铺铜把 DRC 抬升）。

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


def add_zone(board, netname, layer, pts, priority=0):
    z = pcbnew.ZONE(board)
    z.SetLayer(LAYER_MAP[layer])
    z.SetNetCode(ensure_net(board, netname))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    if priority:
        z.SetAssignedPriority(int(priority))   # 同网岛/宿主平面重叠 ⇒ 需不同优先级（CO-132）
    z.SetLocalClearance(mm(0.2))
    z.SetThermalReliefGap(mm(0.2))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.AddPolygon(pcbnew.VECTOR_VECTOR2I([vec(p[0], p[1]) for p in pts]))
    board.Add(z)


def pdn_nets(zd: dict) -> set:
    """SPEC `pd.zone_defs` 全量 PDN 网集合（确定性；供幂等 purge 用）。"""
    nets = set()
    for g in zd.get("gnd_planes", []):
        nets.add(g["net"])
    for z in zd.get("power_zones", []):
        nets.add(z["net"])
    for e in zd.get("power_pad_connect", {}).get("entries", []):
        nets.add(e["net"])
    for v in zd.get("decoupling_via_to_plane", {}).get("vias", []):
        nets.add(v.get("net", "GND"))
    for c in zd.get("gnd_stitch_via", {}).get("coordinates", []):
        nets.add(c.get("net", "GND"))
    return nets


def purge(b, nets, stage: str) -> dict:
    """幂等：删除**本阶段将重发**的 PDN 网铜（④）。

    - stage 含 zone    -> 删 PDN 网 zone（gnd_planes + power_zones 重发）
    - stage 含 zone/connect -> 删 PDN 网 via（两阶段均发 via：power_zone/decoupling/stitch/ppc）
    - stage 含 connect -> 删 PDN 网 track（ppc F.Cu 短段重发）
    仅按**网名**删除，绝不触碰图纸网（PCIE_*）；确定性、零坐标搜索。
    """
    st = {"zones_purged": 0, "tracks_purged": 0, "vias_purged": 0}

    def _drop(item):
        """pcbnew 删除必须走 SWIG 安全路径：`Remove` 会泄漏 ZONE*/PCB_TRACK* 并使
        后续 `GetTracks()` 退化为不可迭代的 SwigPyObject（CO-133 实测）
        ⇒ 优先 `RemoveNative`（所有权转 C++），退化 `Delete`。"""
        for api in ("RemoveNative", "Delete"):
            fn = getattr(b, api, None)
            if fn is not None:
                fn(item)
                return
        b.Remove(item)

    if stage in ("zone", "all"):
        for z in list(b.Zones()):
            if z.GetNetname() in nets:
                _drop(z)
                st["zones_purged"] += 1
    if stage in ("zone", "connect", "all"):
        for t in list(b.GetTracks()):
            if t.GetNetname() not in nets:
                continue
            is_via = t.GetClass() == "PCB_VIA"
            _drop(t)
            st["vias_purged" if is_via else "tracks_purged"] += 1
    return st


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
    P.stats.update(purge(b, pdn_nets(zd), stage))       # CO-133 ④ 幂等 purge-then-add
    if stage in ("zone", "all"):
        for g in zd.get("gnd_planes", []):
            add_zone(b, g["net"], g["layer"], g["polygon"]); P.stats["zones"] += 1
        for pz in zd.get("power_zones", []):
            polys = pz.get("polygons", []) or ([pz["polygon"]] if pz.get("polygon") else [])
            for poly in polys:
                add_zone(b, pz["net"], pz["layer"], poly, pz.get("fill_priority", 0)); P.stats["zones"] += 1
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
    ap.add_argument("--spec", default=str(K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-18.json"))
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
