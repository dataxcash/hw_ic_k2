#!/usr/bin/env python3
"""CO-107：【L2 自裁 · PDN/平面分配】SPEC rev-13 = 平面多边形**随板框 ECO 对齐**（CO-106 FAIL 的施加）。

CO-106 机判：3 个 GND 平面 + 2 个 In4 电源区多边形仍按**旧 38mm 板框**（y 下边 70.7 = 33+38-0.3）声明，
未随 v28 ECO（y 38mm→46mm，`board.outline_y=[33,79]`）更新 ⇒ **板框内、平面外 8.3mm 带状区**
（实测板实 316 In5 + 12 In2 段 + 24 via 已在该带）无参考平面；60 个高速走线采样点落在"声明缺铜"类。

本件按该多边形**自身 basis**（「整面铺铜 + 板边内缩 edge_copper_min 0.3」）把下边 70.7 → **78.7**，
并把 rev-12 原多边形**显式退役留存**（红线：退役几何不得静默放弃）。**只改 polygon 顶点与版本号**；
不改阈值/网/层角色/坐标集/短段宽/blocked 台账；engine/L4 均不消费 `pd.zone_defs` ⇒ 走线几何应逐字节不变。

CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co107_spec_rev13_frame_align.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-12.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-13.json"
REC = STEP2 / "m13_v57_co107_spec_rev13_frame_align.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--rec", default=str(REC))
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.src).read_text())
    zd = spec["pd"]["zone_defs"]
    e = float(spec["constraints"]["edge_copper_min"])
    y0, y1 = spec["board"]["outline_y"]
    want = round(y1 - e, 3)          # 78.7
    stale = round(y0 + 38 - e, 3)    # 70.7 = 旧 38mm 板框
    retired = []

    def fix_poly(owner, poly):
        new = [[p[0], (want if abs(p[1] - stale) < 1e-6 else p[1])] for p in poly]
        if new != poly:
            retired.append({"owner": owner, "reason": "CO-107 板框 38→46mm ECO 未随动（CO-106 FAIL）",
                            "old_polygon": poly, "new_polygon": new})
        return new

    for g in zd.get("gnd_planes", []):
        g["polygon"] = fix_poly(f"gnd_planes[{g['net']}@{g['layer']}]", g["polygon"])
    for z in zd["power_zones"]:
        if isinstance(z.get("polygon"), list) and z["polygon"]:
            z["polygon"] = fix_poly(f"power_zones[{z['net']}@{z.get('zone')}]", z["polygon"])
        if isinstance(z.get("polygons"), list) and z["polygons"]:
            z["polygons"] = [fix_poly(f"power_zones[{z['net']}@{z.get('zone')}]", p) for p in z["polygons"]]
    zd["retired_superseded_frame_extent_v1"] = {
        "note": "CO-107：rev-12 原平面多边形按旧 38mm 板框（下边 70.7）声明；随 v28 ECO（y 38→46mm）对齐至 78.7 后退役留存（禁静默放弃）",
        "edge_copper_min": e, "old_frame_bottom": stale, "new_frame_bottom": want,
        "retired": retired}
    spec["spec_version"] = "1.1.spec-rev-13"
    Path(a.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")
    rec = {"artifact": "m13_v57_co107_spec_rev13_frame_align", "schema": 1, "revision": "CO-107.1",
           "nature": "L2 PDN 自裁施加：平面多边形随板框 ECO 对齐（CO-106 FAIL 的修复）",
           "src": Path(a.src).name, "src_sha16": s16(Path(a.src)),
           "out": Path(a.out).name, "out_sha16": s16(Path(a.out)),
           "changes": {"n_polygons_realigned": len(retired), "old_frame_bottom": stale, "new_frame_bottom": want,
                       "engine_consumes_zone_defs": False, "l4_consumes_zone_defs": False},
           "retired_detail": retired,
           "redline": "只改 polygon 顶点 + spec_version；不改阈值/网/层角色/坐标集/短段宽/blocked；退役几何显式留存"}
    Path(a.rec).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-107 rev-13 written:", json.dumps(rec["changes"], ensure_ascii=False))
    print("spec_sha16", rec["out_sha16"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
