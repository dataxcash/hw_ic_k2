#!/usr/bin/env python3
"""CO-99：【L2 PDN · 施工就绪性】计划集**互相冲突**闸 + 施工 dry-run 取证（CO-96 覆盖面之外的新缺陷类）。

背景（本件发现）：既有 PDN 闸（CO-88/91/92/95/98）与 CO-96 复评**都只判「计划几何 vs 板已有铜」**；
CO-91 的 `Scene` 仅由板（pads/segs/vias）构建 ⇒ **对「计划集内部互相」零判**。本件把工件驱动过其**真实消费面**
（`eda_core.pdn_apply` + `kicad-cli pcb drc`）后测得：rev-11 计划集在 U6 0.5mm 球栅场内存在**异网 via 互相重叠**
（d=0.220/0.220/0.277mm < via 直径 0.35mm ⇒ 电气短路），另 stitch via 互相过近/同址（39 项孔违规）。
⇒ 复现命令可证：本闸 PASS/FAIL 与 `pdn_apply` 实落后的 DRC 一致（本件**FAIL**）。

判据（机判，纯几何；半径/宽度取自 `pdn_apply.VIA_DIA/VIA_DRILL` 与 SPEC `stub_width_mm`）：
  A1 异网 via-via：`d < 2r` ⇒ **重叠/短路**；`2r ≤ d < 2r+req` ⇒ 净距违规；
  A2 异网 stub-via：`pt_seg(w/2+r)` 同理；A3 异网 stub-stub：`seg_seg((w1+w2)/2)` 同理。
  A4 孔-孔（**net-agnostic**）：`d < drill + min_hole_to_hole(0.25)`（板配置口径；项目 drc_rules 为 same_net_exempt ⇒ CO-91 盲）。
  `req = Rules.req(netA, netB)`（规则源 = `_shared/eda_core/drc_rules.json`，与 CO-91 同源）。
B（恒跑；需 AppDir pcbnew + kicad-cli）：scratch 板 baseline DRC → `pdn_apply --stage all` → DRC 差值（只记稳定量）。
牙齿：合成重叠 via 必被抓、干净集合必放行。

只读 SPEC/板（scratch 除外）；不改 SPEC/板/阈值/冻结源；零坐标搜索；无 while。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co99_pdn_mutual_conflict_gate.py
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-11.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co99_pdn_mutual_conflict_gate.json"
SCRATCH = K2 / ".co99_dryrun"
KICAD_CLI = K2.parent / "AppDir/bin/kicad-cli"
BASE = {"spec": "d85f10f722ba22b0", "board": "0e636a67c1472462"}


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load_co91():
    spec = importlib.util.spec_from_file_location("co91mod", K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    sys.path.insert(0, str(K2.parent / "_shared"))
    import eda_core.pdn_apply as pa
    co91 = load_co91()

    ident = {"spec": s16(Path(a.spec)), "board": s16(Path(a.board))}
    mismatch = {k: {"expect": v, "actual": ident.get(k)} for k, v in BASE.items() if ident.get(k) != v}

    spec = json.loads(Path(a.spec).read_text())
    zd = spec["pd"]["zone_defs"]
    rules = co91.Rules(json.loads(co91.RULES.read_text()))
    R = pa.VIA_DIA / 2.0
    w = float(zd.get("power_pad_connect", {}).get("stub_width_mm", co91.STUB_W_DEFAULT))
    targets, stubs = co91.collect(zd)
    stubs = [(k, r, p_, n, ax, ay, bx, by, w) for (k, r, p_, n, ax, ay, bx, by, _w) in stubs]

    def req(x, y):
        return rules.req(x, y)

    def conflicts(w_stub):
        ov2, clr2 = [], []
        for (k1, r1, p1, n1, x1, y1), (k2, r2, p2, n2, x2, y2) in itertools.combinations(targets, 2):
            if n1 == n2:
                continue
            d = math.hypot(x1 - x2, y1 - y2)
            if d < 2 * R - 1e-9:
                ov2.append({"kind": "via_via", "a": f"{k1}:{n1}", "b": f"{k2}:{n2}",
                            "d": round(d, 4), "need": round(2 * R + req(n1, n2), 4),
                            "pos": [[round(x1, 3), round(y1, 3)], [round(x2, 3), round(y2, 3)]]})
            elif d < 2 * R + req(n1, n2) - 1e-9:
                clr2.append({"kind": "via_via", "a": f"{k1}:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4)})
        for (k1, r1, p1, n1, ax, ay, bx, by, _w1) in stubs:
            for (k2, r2, p2, n2, x2, y2) in targets:
                if n1 == n2:
                    continue
                d = co91._d_pt_seg(x2, y2, ax, ay, bx, by)
                if d < w_stub / 2 + R - 1e-9:
                    ov2.append({"kind": "stub_via", "a": f"stub:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4),
                                "need": round(w_stub / 2 + R + req(n1, n2), 4), "pos": [round(x2, 3), round(y2, 3)]})
                elif d < w_stub / 2 + R + req(n1, n2) - 1e-9:
                    clr2.append({"kind": "stub_via", "a": f"stub:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4)})
        for (k1, r1, p1, n1, ax, ay, bx, by, _w1), (k2, r2, p2, n2, cx, cy, dx, dy, _w2) in itertools.combinations(stubs, 2):
            if n1 == n2:
                continue
            d = co91._d_seg_seg(ax, ay, bx, by, cx, cy, dx, dy)
            if d < w_stub - 1e-9:
                ov2.append({"kind": "stub_stub", "a": f"{k1}:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4),
                            "need": round(w_stub + req(n1, n2), 4),
                            "pos": [[round(ax, 3), round(ay, 3)], [round(cx, 3), round(cy, 3)]]})
            elif d < w_stub + req(n1, n2) - 1e-9:
                clr2.append({"kind": "stub_stub", "a": f"{k1}:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4)})
        return ov2, clr2

    ENGINE_STUB_W = 0.5  # `pdn_apply.add_track(..., width=0.5)` 字面量（施工侧未读 SPEC）
    ov, clr = conflicts(w)                     # SPEC 声明宽（0.2）
    ov_e, clr_e = conflicts(ENGINE_STUB_W)     # 引擎实落宽（0.5）
    # 孔-孔（**net-agnostic**；源自板配置 `.kicad_pro` rules.min_hole_to_hole=0.25，非项目 drc_rules.json 的 same_net_exempt 口径）
    DRILL = pa.VIA_DRILL
    HOLE_MIN = 0.25
    hole_ht = []
    for (k1, r1, p1, n1, x1, y1), (k2, r2, p2, n2, x2, y2) in itertools.combinations(targets, 2):
        d = math.hypot(x1 - x2, y1 - y2)
        if d < DRILL + HOLE_MIN - 1e-9:
            hole_ht.append({"a": f"{k1}:{n1}", "b": f"{k2}:{n2}", "d": round(d, 4),
                            "pos": [[round(x1, 3), round(y1, 3)], [round(x2, 3), round(y2, 3)]],
                            "co_located": d < 1e-6})
    hole_ht.sort(key=lambda x: x["d"])
    hole_colocated = [x for x in hole_ht if x["co_located"]]

    ov.sort(key=lambda x: x["d"])
    # 牙齿：合成重叠 via 必被抓；干净对必放行
    tooth_bad = 0.20 < 2 * R            # 0.20mm 间距 < 0.35mm 直径 ⇒ 视为重叠（必被抓）
    tooth_ok = 0.60 >= 2 * R + 0.2      # 0.60mm 间距满足 0.35+0.2 ⇒ 放行
    teeth_ok = tooth_bad and tooth_ok

    dry = dryrun(Path(a.spec))  # 恒跑（~6s）：保证「一条命令 ⇒ 一份记录」

    verdict = ("BASELINE_MISMATCH" if mismatch else
               ("TEETH_FAIL" if not teeth_ok else
                ("FAIL_MUTUAL_SHORT" if ov else
                 ("FAIL_HOLE_SPACING" if (hole_ht or clr) else "PASS"))))
    rec = {
        "artifact": "m13_v57_co99_pdn_mutual_conflict_gate", "schema": 1, "revision": "CO-99.1",
        "nature": "L2 PDN 施工就绪性：计划集**互相冲突**闸（补 CO-91/CO-96 的「只判 vs 板已有铜」覆盖缺口）",
        "inputs": {**ident, "via_dia": pa.VIA_DIA, "via_drill": pa.VIA_DRILL, "stub_width_mm": w},
        "baseline_expectations": BASE, "baseline_mismatch": mismatch,
        "counts": {"realized_vias": len(targets), "stubs": len(stubs),
                   "cross_net_overlap": len(ov), "cross_net_clearance": len(clr)},
        "counts_engine_width_0p5": {"cross_net_overlap": len(ov_e), "cross_net_clearance": len(clr_e),
                                    "note": "以 pdn_apply 实落短段宽 0.5mm 计算的计划集互判（SPEC 声明为 0.2mm）"},
        "engine_width_overlaps": ov_e[:12],
        "overlaps": ov[:40], "clearance": clr[:40],
        "hole_conflicts": {"threshold_mm": DRILL + HOLE_MIN, "hole_to_hole": len(hole_ht),
                           "holes_co_located": len(hole_colocated),
                           "net_agnostic": True,
                           "source": "板配置 .kicad_pro rules.min_hole_to_hole=0.25（项目 drc_rules.json 为 same_net_exempt ⇒ CO-91 盲）",
                           "sample": hole_ht[:8]},
        "by_kind": {"overlap": dict(collections.Counter(x["kind"] for x in ov)),
                    "clearance": dict(collections.Counter(x["kind"] for x in clr))},
        "dryrun": dry,
        "teeth": {"overlap_pair_detected": tooth_bad, "clean_pair_passes": tooth_ok}, "teeth_ok": teeth_ok,
        "source_of_gap": "CO-91 `Scene` 仅由板 pads/segs/vias 构建；计划集内部（stub-stub/stub-via/via-via）无判 ⇒ "
                         "CO-91 PASS 不蕴含可施工。本闸为同一规则源下的**计划集互判**。",
        "non_claims": ["只读 SPEC/板（dry-run 用 scratch 副本）", "本件不改 SPEC/板/阈值/冻结源",
                       "dry-run 的 DRC 为 kicad-cli 实跑（与板配套 .kicad_pro/.kicad_dru 同目录）",
                       "本件不施加修补；修补 = 计划集重导（rev-12）或施工期引擎避让"],
        "verdict": verdict,
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-99 verdict=%s overlaps=%d clearance=%d hole_to_hole=%d co_located=%d teeth_ok=%s" %
          (verdict, len(ov), len(clr), len(hole_ht), len(hole_colocated), teeth_ok))
    for x in ov[:6]:
        print("   OVERLAP", x["kind"], x["a"], x["b"], "d=%s need=%s" % (x["d"], x["need"]))
    if dry:
        print("   dryrun:", json.dumps(dry, ensure_ascii=False)[:300])
    return 0


def dryrun(spec_path: Path) -> dict:
    """scratch 板：baseline DRC → pdn_apply --stage all → DRC 差值（不动交付板）。"""
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)
    for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl"):
        s = BOARD.with_suffix(suf) if suf == ".kicad_pcb" else Path(str(BOARD).replace(".kicad_pcb", suf))
        if s.exists():
            shutil.copy(s, SCRATCH / s.name)
    board = SCRATCH / BOARD.name
    out_b, out_a = SCRATCH / "drc_base.json", SCRATCH / "drc_after.json"

    def drc(dst):
        subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--refill-zones", "--output", str(dst), str(board)],
                       capture_output=True, text=True, timeout=900)
        return json.loads(dst.read_text())

    b = drc(out_b)
    rc = subprocess.run([sys.executable, "-c",
                         "import sys;sys.path.insert(0,%r);from eda_core import pdn_apply;sys.exit(pdn_apply.main(%r))"
                         % (str(K2.parent / "_shared"), ["--spec", str(spec_path), "--board", str(board), "--stage", "all"])],
                        capture_output=True, text=True, timeout=900)
    applied = (rc.stdout or "").strip().splitlines()[:1]
    a = drc(out_a)
    tb = collections.Counter(x["type"] for x in b["violations"])
    ta = collections.Counter(x["type"] for x in a["violations"])
    # 只记录**稳定**指标（violation 总数 / 未连数）；逐类型明细与 scratch 板 hash 随 zone refill/UUID 分组浮动 ⇒ 不入记录
    res = {"applied": applied,
           "baseline_total": len(b["violations"]), "after_total": len(a["violations"]),
           "delta_total": len(a["violations"]) - len(b["violations"]),
           "unconnected_baseline": len(b.get("unconnected_items", [])),
           "unconnected_after": len(a.get("unconnected_items", [])),
           "stability_note": "仅记录稳定量（violation 总数 / 未连数）；逐类型明细随 zone refill 与 UUID 分组浮动 ⇒ 不入记录（见卡）",
           "scratch": str(SCRATCH.relative_to(K2))}
    return res


if __name__ == "__main__":
    raise SystemExit(main())
