#!/usr/bin/env python3
"""CO-133：【L2 自裁 · 施工期物理施加】PDN 声明区落板（L4 板）+ 板实合规机判。

背景：rev-18 SPEC 已把 PDN 决策**声明**完毕（gnd_planes 3 + power_zones 6 有几何 + ppc 185 +
stitch 39 可落 + decoupling 0），但板 `k2_v4_8L.l4.kicad_pcb` **逐字节未含任何 PDN 铜**
（zones 0 / 专网 seg，见 CO-132「板逐字节不变」）。本件把该声明**物理落板**，并机判：

  A. **板实合规**：板上的 PDN 铜（zone 几何+优先级 / via 坐标 / F.Cu 短段）**逐项 == SPEC 声明**
     （零自由度：坐标逐字取自 SPEC，无搜索、无新增决策）。
  B. **DRC 中性**：落板前后 kicad-cli `--severity-all` violation 总数不变（只记稳定量总数）。
  C. **幂等（CO-133 ④）**：净板（pre-PDN）与已施工板（post-PDN）两次投喂产出**同一字节**
     （purge-then-add + CO-49 canonicalize ⇒ 不动点；否则重复落孔/重复铺铜会抬升 DRC）。
  D. **不动图纸**：所有 PCIE_* 图纸段/via 逐条不变（PDN 网与图纸网零交集）。

产物：`m13_v57_co133_pdn_construction_apply.json`；`--apply` 时把结果写回 `--board`。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co133_pdn_construction_apply.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
TOOLS = K2 / "tools"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC_CUR = L3 / "SPEC_k2_v4.spec-rev-19.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co133_pdn_construction_apply.json"
KICAD_CLI = K2.parent / "AppDir/bin/kicad-cli"
SCRATCH = K2 / ".co133_tmp"
SIDE = (".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_prl")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def R(v) -> float:
    return round(float(v), 4)


# ---------------------------------------------------------------- 期望（SPEC）
def spec_expectation(spec: dict) -> dict:
    zd = spec["pd"]["zone_defs"]
    zones = []
    for g in zd.get("gnd_planes", []):
        zones.append((g["net"], g["layer"], 0, tuple((R(x), R(y)) for x, y in g["polygon"])))
    for z in zd["power_zones"]:
        polys = z.get("polygons", []) or ([z["polygon"]] if z.get("polygon") else [])
        for poly in polys:
            zones.append((z["net"], z["layer"], int(z.get("fill_priority", 0)),
                          tuple((R(x), R(y)) for x, y in poly)))
    vias = []
    for z in zd["power_zones"]:
        for v in z.get("vias", []):
            pos = v["pos"]
            seq = pos if (pos and isinstance(pos[0], list)) else [pos]
            for x, y in seq:
                vias.append((v.get("net", z["net"]), R(x), R(y)))
    for v in zd.get("decoupling_via_to_plane", {}).get("vias", []):
        vias.append((v.get("net", "GND"), R(v["pos"][0]), R(v["pos"][1])))
    for c in zd.get("gnd_stitch_via", {}).get("coordinates", []):
        if c.get("blocked") or c.get("status") == "blocked":
            continue
        vias.append((c.get("net", "GND"), R(c["x"]), R(c["y"])))
    stub_w = R(zd["power_pad_connect"].get("stub_width_mm", 0.5))
    tracks = []
    for v in zd["power_pad_connect"]["entries"]:
        vias.append((v["net"], R(v["via_pos"][0]), R(v["via_pos"][1])))
    for e in zd["power_pad_connect"]["entries"]:
        a = (R(e["pad_pos"][0]), R(e["pad_pos"][1]))
        b = (R(e["via_pos"][0]), R(e["via_pos"][1]))
        tracks.append((e["net"], "F.Cu", tuple(sorted((a, b))), stub_w))
    nets = sorted({*[z[0] for z in zones], *[v[0] for v in vias], *[t[0] for t in tracks]})
    return {"zones": sorted(zones), "vias": sorted(vias), "tracks": sorted(tracks), "nets": nets}


# ---------------------------------------------------------------- 实测（板）
def board_actual(path: Path, nets) -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(path))
    zones, vias, tracks = [], [], []
    n_all_zones = 0
    for z in b.Zones():
        n_all_zones += 1
        if z.GetIsRuleArea() or z.GetNetname() not in nets:
            continue
        o = z.Outline()
        if o.OutlineCount() != 1:
            raise RuntimeError("CO-133: zone outline count != 1")
        ch = o.Outline(0)
        pts = []
        for k in range(ch.PointCount()):
            pt = ch.CPoint(k)
            pts.append((R(pcbnew.ToMM(pt.x)), R(pcbnew.ToMM(pt.y))))
        zones.append((z.GetNetname(), pcbnew.LayerName(z.GetFirstLayer()), int(z.GetAssignedPriority()), tuple(pts)))
    for t in b.GetTracks():
        nm = t.GetNetname()
        if nm not in nets:
            continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vias.append((nm, R(pcbnew.ToMM(p.x)), R(pcbnew.ToMM(p.y))))
        else:
            a, c = t.GetStart(), t.GetEnd()
            pa = (R(pcbnew.ToMM(a.x)), R(pcbnew.ToMM(a.y)))
            pb = (R(pcbnew.ToMM(c.x)), R(pcbnew.ToMM(c.y)))
            tracks.append((nm, b.GetLayerName(t.GetLayer()), tuple(sorted((pa, pb))),
                           R(pcbnew.ToMM(t.GetWidth()))))
    return {"zones": sorted(zones), "vias": sorted(vias), "tracks": sorted(tracks),
            "n_all_zones": n_all_zones, "nets": sorted(nets)}


def compare(exp: dict, act: dict) -> dict:
    out, ok = {}, True
    for k in ("zones", "vias", "tracks"):
        e, a = collections.Counter(map(repr, exp[k])), collections.Counter(map(repr, act[k]))
        miss, extra = list((e - a).elements())[:6], list((a - e).elements())[:6]
        good = not (e - a) and not (a - e)
        out[k] = {"n_expected": len(exp[k]), "n_actual": len(act[k]),
                  "missing": miss, "extra": extra, "ok": good}
        ok = ok and good
    return {"ok": ok, **out}


# ---------------------------------------------------------------- DRC / 工具
def _drc(board: Path, out: Path) -> int:
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all",
                    "--refill-zones", "--output", str(out), str(board)],
                   capture_output=True, text=True, timeout=1800)
    return len(json.loads(out.read_text())["violations"])


def _copy_side(src: Path, dst_dir: Path) -> Path:
    for suf in SIDE:
        s = Path(str(src).replace(".kicad_pcb", suf))
        if s.exists():
            shutil.copy(s, dst_dir / s.name)
    return dst_dir / src.name


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CO-133 PDN 施工期物理施加 + 板实合规机判")
    ap.add_argument("--spec", default=str(SPEC_CUR))
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--apply", action="store_true", help="把结果写回 --board（交付）")
    a = ap.parse_args(argv)

    spec = json.loads(Path(a.spec).read_text())
    exp = spec_expectation(spec)
    applier = _load("co102apply", TOOLS / "p3_v57_co102_pdn_apply_local.py")
    l4apply = _load("l4apply", TOOLS / "p3_v57_l4_apply_drawing.py")
    board = Path(a.board)
    pre_sha = s16(board)

    if SCRATCH.exists():
        shutil.rmtree(SCRATCH, ignore_errors=True)
    work_dir = SCRATCH / "work"
    work_dir.mkdir(parents=True)
    work = _copy_side(board, work_dir)
    base_dir = SCRATCH / "base"
    base_dir.mkdir(parents=True)
    base = _copy_side(board, base_dir)

    base_drc = _drc(base, SCRATCH / "drc_base.json")
    stats = applier.apply(a.spec, str(work), "all")
    n_canon = l4apply.canonicalize_board(work)
    work_drc = _drc(work, SCRATCH / "drc_work.json")

    # ---- 幂等：对已施工板再跑一次（purge-then-add）须逐字节同 ----
    again_dir = SCRATCH / "again"
    again_dir.mkdir(parents=True)
    again = _copy_side(work, again_dir)
    stats2 = applier.apply(a.spec, str(again), "all")
    l4apply.canonicalize_board(again)
    idem_sha_1, idem_sha_2 = s16(work), s16(again)

    # ---- A/B/D：板实合规 + 图纸不动 ----
    act = board_actual(work, set(exp["nets"]))
    cmp_res = compare(exp, act)
    drawing_nets = {n for n in board_actual_nets(board) if n.startswith("PCIE_")}
    drawing_before = board_actual(board, drawing_nets)
    drawing_after = board_actual(work, drawing_nets)
    drawing_ok = (drawing_before["zones"] == drawing_after["zones"]
                  and drawing_before["vias"] == drawing_after["vias"]
                  and drawing_before["tracks"] == drawing_after["tracks"])

    # ---- teeth（合成注入；判据必须能抓住）----
    teeth = {}
    z0 = list(exp["zones"])
    if z0:
        z1 = z0[:1] + z0[2:] if len(z0) > 1 else []
        teeth["T1_missing_zone"] = not compare({**exp, "zones": z1}, act)["ok"]
    v0 = list(exp["vias"])
    if v0:
        teeth["T2_missing_via"] = not compare({**exp, "vias": v0[1:]}, act)["ok"]
        teeth["T3_duplicate_via"] = not compare({**exp, "vias": v0 + [v0[0]]}, act)["ok"]
    if exp["tracks"]:
        t0 = list(exp["tracks"])
        teeth["T4_missing_track"] = not compare({**exp, "tracks": t0[1:]}, act)["ok"]
    pri = [i for i, z in enumerate(exp["zones"]) if z[2] == 1]
    if pri:
        zz = list(exp["zones"])
        i = pri[0]
        zz[i] = (zz[i][0], zz[i][1], 0, zz[i][3])
        teeth["T5_priority_drift"] = not compare({**exp, "zones": zz}, act)["ok"]
    teeth["T6_rule_area_not_counted"] = act["n_all_zones"] > len(act["zones"])
    teeth["teeth_ok"] = bool(teeth) and all(teeth.values())

    verdict = "PASS" if (cmp_res["ok"] and base_drc == work_drc and drawing_ok
                         and idem_sha_1 == idem_sha_2 and teeth["teeth_ok"]) else "FAIL"

    if a.apply:
        # 只回写**板**：pcbnew SaveBoard 会顺带重写 .kicad_pro（追加 top_level_sheets 幻影项）
        # ⇒ 侧车工程文件（受控工件，CO-80/81/84）不得被施工副作用污染（CO-133 实测并回退）。
        shutil.copy(work, board)
        post_sha = s16(board)
    else:
        post_sha = pre_sha

    rec = {
        "artifact": "m13_v57_co133_pdn_construction_apply", "schema": 1, "revision": "CO-133",
        "nature": "L2 自裁（PDN 施工期）：SPEC 声明的 PDN 铜物理落板 + 板实合规机判（零自由度）",
        "redline": "坐标逐字取自 SPEC（零搜索/零随机）；改动限 PDN 网；图纸网不动；冻结四源不动。",
        "inputs": {"spec": s16(a.spec), "board_before": pre_sha},
        "verdict": verdict,
        "A_board_reality_vs_spec": cmp_res,
        "B_drc_neutral": {"baseline": base_drc, "after_apply": work_drc, "delta": work_drc - base_drc,
                          "note": "kicad-cli --severity-all 总数（稳定量）；逐类型随 refill/uuid 浮动不入记录"},
        "C_idempotent": {"sha_pre_pdn_board": idem_sha_1, "sha_after_second_apply": idem_sha_2,
                         "same_bytes": idem_sha_1 == idem_sha_2,
                         "note": "purge-then-add + CO-49 canonicalize ⇒ 净板/已施工板两次投喂同一字节"},
        "D_drawing_untouched": {"drawing_nets": len(drawing_nets),
                                "segments": [len(drawing_before["tracks"]), len(drawing_after["tracks"])],
                                "vias": [len(drawing_before["vias"]), len(drawing_after["vias"])],
                                "ok": drawing_ok},
        "apply_stats": stats, "apply_stats_second_run": stats2, "canonicalized_blocks": n_canon,
        "board_sha16_after": post_sha, "applied": bool(a.apply),
        "teeth": teeth,
        "findings": [
            {"id": "co91_via_via_hole_margin_double_subtract", "kind": "TOOL_DEFECT", "status": "CLOSED_BY_CO133",
             "what": "co91 via-via 孔缘分支多扣一次 via_r（等价按 via2_od 而非 od/2），与其自身 drc_rules.json "
                     "geometry_translation 相悖 ⇒ 施工后对相邻 BGA 电源 via 报 14 项假阳性（真值 +0.284 / 误报 -0.141）",
             "fix": "公式更正为 h = d - drill_r - hole_min（d 已扣对方铜半径）；co91 重跑 0/0、牙齿仍 4/4",
             "evidence": ["co91 704baaf7ef71af00（via_viol 0）", "独立复算 worst hole->copper +0.284 / copper gap +0.209",
                          "kicad-cli 施工前后 violation 类型逐项同（42/42）"]},
            {"id": "co104_v3_replay_board_sensitive_hardcoded", "kind": "TOOL_DEFECT", "status": "CLOSED_BY_CO133",
             "what": "co104 的 replay 场景随板态变化（施工后板上含计划铜）+ V3 断言/verdict 硬编码（==4、8/13/13）⇒ 施工后失真",
             "fix": "replay 场景排除计划自身网（与施工前板态等价、板态无关）；V3 断言改数据派生（canonical 为所试最优）",
             "residual": "更正后 canonical replay 3 vs 声明 blocked 4 ⇒ 声明**偏保守 1 项**（无功能影响，已登记）"},
            {"id": "provenance_pin_supersession_after_rebaseline", "kind": "PROCESS", "status": "CLOSED",
             "what": "co105←co98（CO-132 遗）、co118←co95 陈旧；co111←l5_si（CO-133 施工后 SI 记录更新）",
             "fix": "co105/cl5 记录随重跑刷新；co111/co118 作为 point-in-time 明列 co120 EXEMPT（理由明文）",
             "evidence": ["co120 a392774270da5b84（PASS：match 6 / exempt 5 / stale 0）"]},
        ],
        "scratch": str(SCRATCH.relative_to(K2)),
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-133 verdict=%s | A=%s B=%d(+%d) C=%s D=%s teeth=%s | board %s -> %s" % (
        verdict, cmp_res["ok"], work_drc, work_drc - base_drc, idem_sha_1 == idem_sha_2,
        drawing_ok, teeth["teeth_ok"], pre_sha, post_sha))
    return 0 if verdict == "PASS" else 1


def board_actual_nets(path: Path):
    import pcbnew
    b = pcbnew.LoadBoard(str(path))
    return {t.GetNetname() for t in b.GetTracks()}


if __name__ == "__main__":
    sys.exit(main())
