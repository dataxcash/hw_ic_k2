#!/usr/bin/env python3
"""CO-84：【L2 可审计性 · 回归闸】DRC 放宽域一致性（dru ↔ 域工件 ↔ 板 rule area ↔ SPEC）。

`k2_v4_8L.l4.kicad_dru` **放宽**逃逸区铜净距至 0.075（SPEC ECN-001）。若其作用域
（4 个 rule area）与域工件/板实现不一致（过宽），会**掩盖真实违规**；过窄则对已授权的
逃逸区误报。故立闸，四向必须一致：

  1. 净距值：dru min == SPEC `escape_transition_zone.escape_clearance_mm` == 域工件 `escape_clearance_mm`
  2. 域集合：dru `intersectsArea` 名集 == 域工件 `domains[].id` 集 == **板内 rule area 名集**
  3. 层：全部 = F.Cu
  4. 排除网：dru 条件含 REFCLK 排除，且与域工件 `excluded_nets` 一致
  5. 溯源：dru 注释所引域工件 sha256 == 实际文件 sha256
  6. 几何：域工件 `rect_mm` 与**板内 zone bbox** 逐值一致（tol 1e-6）

用法：python3 tools/p3_v57_co84_dru_domain_gate.py
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-18.json"
FIXTURE = STEP2 / "m13_v57_co37_escape_domain.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
DRU = K2 / "k2_v4_8L.l4.kicad_dru"
OUT = STEP2 / "m13_v57_co84_dru_domain_gate.json"
TOL = 1e-6


def s256(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_dru(text: str) -> dict:
    clr = re.search(r"\(constraint clearance \(min ([\d.]+)mm\)", text)
    layer = re.search(r'\(layer "([^"]+)"\)', text)
    areas = re.findall(r"intersectsArea\('([^']+)'\)", text)
    refclk = re.search(r"NetName == '([^']*\*[^']*)'", text)
    cited = re.search(r"sha256=([0-9a-f]{64})", text)
    return {"clearance_mm": float(clr.group(1)) if clr else None,
            "layer": layer.group(1) if layer else None,
            "areas": sorted(set(areas)),
            "refclk_exclusion": refclk.group(1) if refclk else None,
            "cited_fixture_sha256": cited.group(1) if cited else None}


def board_rule_areas(text: str) -> dict:
    out = {}
    for m in re.finditer(r"\(zone\s", text):
        ch = text[m.start():m.start() + 2500]
        nm = re.search(r'\(name "([^"]+)"\)', ch)
        ly = re.search(r'\(layer "([^"]+)"\)', ch)
        pts = re.search(r"\(polygon\s*\(pts(.*?)\)\s*\)", ch, re.S)
        if not (nm and nm.group(1).startswith("ESC_") and pts):
            continue
        xy = [(float(a), float(b)) for a, b in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", pts.group(1))]
        xs = [p[0] for p in xy]; ys = [p[1] for p in xy]
        # 与域工件 rect_mm 同序：[x0, y0, x1, y1]
        out[nm.group(1)] = {"layer": ly.group(1) if ly else None,
                            "bbox": [min(xs), min(ys), max(xs), max(ys)],
                            "all_allowed": bool(re.search(r"\(tracks allowed\)[\s\S]{0,200}\(footprints allowed\)", ch))}
    return out


def gate(dru: dict, fix: dict, board: dict, spec_clr: float) -> dict:
    """纯函数：返回失配集（空 = 通过），便于负控。"""
    bad = {}
    dom = {d["id"]: d for d in fix["domains"]}
    if dru["clearance_mm"] != spec_clr or dru["clearance_mm"] != fix["escape_clearance_mm"]:
        bad["clearance_mm"] = [dru["clearance_mm"], spec_clr, fix["escape_clearance_mm"]]
    if dru["areas"] != sorted(dom) or dru["areas"] != sorted(board):
        bad["area_set"] = [dru["areas"], sorted(dom), sorted(board)]
    if dru["layer"] != "F.Cu" or any(d["layer"] != "F.Cu" for d in fix["domains"]) \
            or any(v["layer"] != "F.Cu" for v in board.values()):
        bad["layer"] = [dru["layer"], sorted({d["layer"] for d in fix["domains"]}),
                        sorted({v["layer"] for v in board.values()})]
    if dru["refclk_exclusion"] is None or \
            [dru["refclk_exclusion"]] != [n for n in fix["excluded_nets"]]:
        bad["refclk_exclusion"] = [dru["refclk_exclusion"], fix["excluded_nets"]]
    for i in sorted(dom):
        b = board.get(i)
        if b is None:
            bad["missing_in_board:" + i] = None
        elif any(abs(a - c) > TOL for a, c in zip(dom[i]["rect_mm"], b["bbox"])):
            bad["rect:" + i] = [dom[i]["rect_mm"], b["bbox"]]
    return bad


def main() -> int:
    dru_txt = DRU.read_text(encoding="utf-8")
    dru = parse_dru(dru_txt)
    fix = json.loads(FIXTURE.read_text(encoding="utf-8"))
    spec_clr = json.loads(SPEC.read_text(encoding="utf-8"))["constraints"]["escape_transition_zone"]["escape_clearance_mm"]
    board = board_rule_areas(BOARD.read_text(encoding="utf-8", errors="replace"))
    bad = gate(dru, fix, board, spec_clr)
    sha_ok = dru["cited_fixture_sha256"] == s256(FIXTURE)
    if not sha_ok:
        bad["cited_fixture_sha256"] = [dru["cited_fixture_sha256"], s256(FIXTURE)]
    # 负控（有齿）：过宽作用域 / 净距不符 / 丢掉 REFCLK 排除 / 矩形漂移，都必须被抓到
    import copy
    negs = {
        "extra_area": gate({**dru, "areas": sorted(set(dru["areas"]) | {"ESC_XX"})}, fix, board, spec_clr),
        "clearance_off": gate({**dru, "clearance_mm": 0.1}, fix, board, spec_clr),
        "no_refclk_exclusion": gate({**dru, "refclk_exclusion": None}, fix, board, spec_clr),
        "rect_drift": gate(dru, copy.deepcopy({**fix, "domains": [{**fix["domains"][0], "rect_mm": [0.0, 1.0, 2.0, 3.0]}] + fix["domains"][1:]}), board, spec_clr),
    }
    teeth = all(len(v) > 0 for v in negs.values())
    rec = {"artifact": "m13_v57_co84_dru_domain_gate", "schema": 1, "revision": "CO-84.1",
           "nature": "L2 可审计性：DRC 放宽域一致性（dru ↔ 域工件 ↔ 板 rule area ↔ SPEC）",
           "inputs": {"dru": {"file": str(DRU.relative_to(K2)), "sha256": s256(DRU)},
                      "fixture": {"file": str(FIXTURE.relative_to(K2)), "sha256": s256(FIXTURE)},
                      "spec": {"file": str(SPEC.relative_to(K2)), "sha256": s256(SPEC)},
                      "board": {"file": str(BOARD.relative_to(K2)), "sha256": s256(BOARD)}},
           "parsed": {"dru": dru, "spec_clearance_mm": spec_clr, "board_areas": board,
                      "fixture_domains": sorted(d["id"] for d in fix["domains"])},
           "mismatches": bad, "negative_controls": {k: len(v) for k, v in negs.items()},
           "teeth_ok": teeth, "verdict": "PASS" if (not bad and teeth) else "FAIL",
           "rationale": "dru 放宽净距；作用域过宽会掩盖真实违规，过窄则对授权区误报。",
           "redline": "只读；不改任何工件；净距值取自红线 SPEC，不放宽。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "mismatches": bad, "teeth_ok": teeth,
                      "neg": {k: len(v) for k, v in negs.items()}, "areas": dru["areas"],
                      "record": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
