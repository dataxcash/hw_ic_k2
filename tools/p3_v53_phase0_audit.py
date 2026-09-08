#!/usr/bin/env python3
"""v53 Phase 0 audit — fallback 计数 + fact_validate 重放（纯审计，零引擎改动）。

范围（v53 白名单 P0）：本文件只做只读统计与几何重放，不修改任何生产文件。
  A) CountingModel：HSRouteModel 子类，仅对施工自搜入口做 wrapper/counter：
     _escape_pair / _col_stack_escape / _pad_row_dip_escape /
     _layer_swap_escape / _layer_swap_escape_v / _solve_short_v4
     —— super() 原样转发（参数/返回/顺序零改动），只累积计数。
     其中 col_stack/dip/lswap/lswap_v 接收 pn_ok 闭包，计数其 call/reject
     （对应 v52 取证口径：自搜形态候选的 P/N 净空枚举量）。
  B) fact_validate(replay)：对 report 中每条 SOLVED 段，按引擎场语义重建
     （build_hs_field clear 自身 P/N + 已解段 shared 注入 0.09 宽 + shared
     via），逐跳 seg_ok / 层变 via point_ok / pn_min_edge>=0.155 重放。
     shared 快照按 solve_all_v4 确定性顺序（K2 序 + 链内段序）模拟累积，
     仅记录 PASS/FAIL，不阻断任何旧路径。

引用引擎只读 API：hs_route_model.build_hs_field / _path_pn_min_edge_pt /
HSRouteModel；统一场 seg_ok/point_ok。坐标/网名零字面量（来自输入文件）。
"""
from __future__ import annotations

import functools
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]                 # k2/
SHARED = Path("/home/fila/jqdDev_2025/ic_hw/_shared")       # 容器级 _shared（运行真源）
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(REPO / "tools"))

import p3_k2_real_board_e2e as E                            # noqa: E402

from eda_core.hs_route_model import (                        # noqa: E402
    HSRouteModel,
    build_hs_field,
    _path_pn_min_edge_pt,
)
from eda_core.route_input import ModelConfig                 # noqa: E402


# ── 常数（随 e2e 驱动真源，勿复制板坐标）──────────────────────────
SPEC_PATH = E.SPEC_PATH
RULES_PATH = E.RULES_PATH
CONFIG_PATH = E.CONFIG_PATH
REAL_BOARD = E.REAL_BOARD
PN_MIN_EDGE = 0.155          # 引擎同阈值（0.175 − 0.02 容差，v4 原子性断言）
SHARED_SEG_W = 0.09          # 引擎 _field() 注入已解段的宽度


# ── 序列化/指纹工具 ────────────────────────────────────────────────
def load_json(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_json(obj) -> str:
    import hashlib
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def k2_base_key(base: str):
    """solve_all_v4 的 K2 定序键复刻（UP<DN<REFCLK，数字升序）。"""
    s = base[5:] if base.startswith("PCIE_") else base
    fam = next((f for f in ("UP", "DN", "REFCLK") if s.startswith(f)), "ZZ")
    num_s = s[len(fam):] or "0"
    try:
        num = int(num_s)
    except ValueError:
        num = 0
    return ({"UP": 0, "DN": 1, "REFCLK": 2}.get(fam, 9), num)


# ── A. CountingModel：仅包装，不改行为 ─────────────────────────────
class CountingModel(HSRouteModel):
    """施工自搜入口计数器。super() 逐参原样转发；计数不入任何返回值。"""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.audit_counts = Counter()          # form 名 -> 进入次数
        self.audit_pn = defaultdict(Counter)   # form 名 -> {calls, rejects}
        self.audit_by_net = defaultdict(int)   # (form,net_p,net_n) -> n

    # -- pn_ok 闭包包装（只数不拦） --
    def _wrap_pn(self, pn_ok, form):
        cnt = self.audit_pn[form]

        @functools.wraps(pn_ok)
        def w(p_pts, p_layers, n_pts, n_layers):
            r = pn_ok(p_pts, p_layers, n_pts, n_layers)
            cnt["calls"] += 1
            if not r:
                cnt["rejects"] += 1
            return r
        return w

    def _bump(self, form, net_p=None, net_n=None):
        self.audit_counts[form] += 1
        if net_p is not None and net_n is not None:
            self.audit_by_net[(form, net_p, net_n)] += 1

    # -- 六个白名单入口：签名与引擎逐一相同，super() 原样转发 --
    def _escape_pair(self, band_field, fcu_field, esc_field,
                     pad_p, pad_n, corr_x, track_y, bound_x,
                     direction, net_p, net_n, flip=False, esc_layer="In2.Cu",
                     landing_pair=None, chip_landing_pair=None,
                     max_slide=30, cs_alt_field=None, cs_alt_layer=None):
        self._bump("escape_pair", net_p, net_n)
        return super()._escape_pair(
            band_field, fcu_field, esc_field, pad_p, pad_n,
            corr_x, track_y, bound_x, direction, net_p, net_n,
            flip=flip, esc_layer=esc_layer, landing_pair=landing_pair,
            chip_landing_pair=chip_landing_pair, max_slide=max_slide,
            cs_alt_field=cs_alt_field, cs_alt_layer=cs_alt_layer)

    def _col_stack_escape(self, band_field, fcu_field, esc_field,
                          pad_p, pad_n, corr_x, track_y, bound_x,
                          direction, net_p, net_n, flip, esc_layer,
                          pn_ok, carrier_field=None, carrier_layer=None):
        self._bump("col_stack", net_p, net_n)
        return super()._col_stack_escape(
            band_field, fcu_field, esc_field, pad_p, pad_n,
            corr_x, track_y, bound_x, direction, net_p, net_n,
            flip, esc_layer, self._wrap_pn(pn_ok, "col_stack"),
            carrier_field=carrier_field, carrier_layer=carrier_layer)

    def _pad_row_dip_escape(self, band_field, fcu_field, esc_field,
                            pad_p, pad_n, corr_x, track_y, bound_x,
                            direction, net_p, net_n, flip, esc_layer, pn_ok):
        self._bump("pad_row_dip", net_p, net_n)
        return super()._pad_row_dip_escape(
            band_field, fcu_field, esc_field, pad_p, pad_n,
            corr_x, track_y, bound_x, direction, net_p, net_n,
            flip, esc_layer, self._wrap_pn(pn_ok, "pad_row_dip"))

    def _layer_swap_escape(self, band_field, fcu_field, esc_field,
                           pad_p, pad_n, corr_x, track_y, bound_x,
                           direction, net_p, net_n, flip, esc_layer, pn_ok):
        self._bump("layer_swap", net_p, net_n)
        return super()._layer_swap_escape(
            band_field, fcu_field, esc_field, pad_p, pad_n,
            corr_x, track_y, bound_x, direction, net_p, net_n,
            flip, esc_layer, self._wrap_pn(pn_ok, "layer_swap"))

    def _layer_swap_escape_v(self, band_field, fcu_field, esc_field,
                             pad_p, pad_n, corr_x, track_y, bound_x,
                             direction, net_p, net_n, flip, esc_layer, pn_ok):
        self._bump("layer_swap_v", net_p, net_n)
        return super()._layer_swap_escape_v(
            band_field, fcu_field, esc_field, pad_p, pad_n,
            corr_x, track_y, bound_x, direction, net_p, net_n,
            flip, esc_layer, self._wrap_pn(pn_ok, "layer_swap_v"))

    def _solve_short_v4(self, net_p, net_n, base, segname, ep,
                        shared_segs=None):
        self._bump("solve_short", net_p, net_n)
        return super()._solve_short_v4(net_p, net_n, base, segname, ep,
                                       shared_segs)


# ── run_solve 输入复刻（与 solve_pipeline.run_solve 同参）────────────
def make_config():
    """复刻 run_solve 的 ModelConfig 组装（hs_route_model + escape_check 覆写）。"""
    base_cfg = load_json(CONFIG_PATH)
    config = E.build_config(base_cfg)
    hs_cfg = (config or {}).get("hs_route_model")
    mcfg = ModelConfig.from_dict(hs_cfg) if hs_cfg else None
    if mcfg is not None:
        _ec = ((config or {}).get("channel_alloc") or {}).get("escape_check") or {}
        if isinstance(_ec, dict) and float(_ec.get("keepout", 0.0) or 0.0) > 0:
            mcfg.escape_env_keepout = float(_ec.get("keepout", 0.0))
            mcfg.escape_env_half_track = float(_ec.get("half_track", 0.0) or 0.0)
            mcfg.escape_env_pair_half = float(_ec.get("pair_half", 0.0) or 0.0)
            mcfg.escape_env_band_spans = _ec.get("band_spans") or None
    return mcfg


def run_counting_solve(alloc_table: dict, landing_allocation: dict,
                       spec_path=SPEC_PATH, rules_path=RULES_PATH,
                       board_path=REAL_BOARD):
    """CountingModel.solve_all_v4 —— 复刻 run_solve 的输入与 bases。

    返回 (raw, model)：raw 为 solve_all_v4 返回 dict（结果与 report solve
    阶段应逐字节一致）；model 带 audit_counts/audit_pn/audit_by_net。
    """
    spec = load_json(spec_path)
    rules = load_json(rules_path)
    mcfg = make_config()
    with tempfile.TemporaryDirectory(prefix="v53p0_") as td:
        spec_f = os.path.join(td, "spec.json")
        alloc_f = os.path.join(td, "alloc.json")
        rules_f = os.path.join(td, "rules.json")
        json.dump(spec, open(spec_f, "w"), ensure_ascii=False)
        json.dump({"alloc": dict(alloc_table)}, open(alloc_f, "w"))
        json.dump(rules, open(rules_f, "w"), ensure_ascii=False)
        model = CountingModel(str(board_path), spec_f, alloc_f, rules_f,
                              config=mcfg, landing=dict(landing_allocation))
        bases = sorted(k for k, r in (alloc_table or {}).items()
                       if (r or {}).get("status") == "SOLVED")
        raw = model.solve_all_v4(bases)
    return raw, model


# ── B. fact_validate：shared 快照模拟 + 几何重放 ─────────────────────
def solved_segments_in_order(results: dict):
    """按 solve_all_v4 K2 序 + 链内段序产出 SOLVED 段列表。"""
    out = []
    for base in sorted(results, key=k2_base_key):
        for seg in (results[base] or {}).get("segments", []):
            if seg.get("status") == "SOLVED":
                out.append((base, seg))
    return out


def shared_snapshot(results: dict):
    """确定性模拟 solve_all_v4/solve_chain_v4 的 shared 累积。

    返回 {(base, segname): (shared_segs, shared_vias)} —— 该段求解时刻
    之前已解段的共享注入（链内跨段 + 全 SOLVED base 跨 base 前馈）。
    """
    snap = {}
    cross_segs: list = []
    cross_vias: list = []
    for base in sorted(results, key=k2_base_key):
        rec = results[base] or {}
        chain_segs = list(cross_segs)
        chain_vias = list(cross_vias)
        for seg in rec.get("segments", []):
            if seg.get("status") != "SOLVED":
                continue
            snap[(base, seg.get("name"))] = (list(chain_segs),
                                             list(chain_vias))
            for key in ("P", "N"):
                net = seg[key]["net"]
                pts = seg[key].get("path", [])
                layers = seg[key].get("layers", [])
                for i in range(len(pts) - 1):
                    chain_segs.append((net, tuple(pts[i]),
                                       tuple(pts[i + 1]), layers[i]))
                for i in range(len(layers) - 1):
                    if layers[i] != layers[i + 1]:
                        chain_vias.append((net, pts[i + 1][0],
                                           pts[i + 1][1]))
        if rec.get("status") == "SOLVED":
            cross_segs, cross_vias = chain_segs, chain_vias
    return snap


def replay_segment(board, rules, spec, mcfg, seg, shared_segs, shared_vias):
    """单段重放。返回 {ok, checks:[...]} —— 每检查独立 PASS/FAIL。"""
    net_p = seg["P"]["net"]
    net_n = seg["N"]["net"]
    checks: list = []
    width = (spec.get("impedance") or {}).get("width_mm", 0.205)

    def field_for(layer: str):
        f = build_hs_field(board, rules, layer=layer,
                           clear_hs_pads=True, config=mcfg,
                           clear_hs_nets=(net_p, net_n))
        for (en, ea, eb, el) in shared_segs:
            if el == layer:
                f.add_seg(en, ea, eb, SHARED_SEG_W, el)
        for (en, vx, vy) in shared_vias:
            f.add_via(en, vx, vy)
        return f

    layers_used = sorted(set(seg["P"].get("layers", []) +
                             seg["N"].get("layers", [])))
    fields = {l: field_for(l) for l in layers_used}

    for key in ("P", "N"):
        net = seg[key]["net"]
        pts = seg[key].get("path", [])
        layers = seg[key].get("layers", [])
        # 结构断言：layers 数 = path 数 − 1
        ok = len(pts) >= 2 and len(layers) == len(pts) - 1
        checks.append({"check": f"{key}_structure", "ok": ok,
                       "detail": f"pts={len(pts)} layers={len(layers)}"})
        if not ok:
            continue
        # 逐跳 seg_ok
        seg_fail = None
        for i in range(len(pts) - 1):
            if not fields[layers[i]].seg_ok(net, tuple(pts[i]),
                                            tuple(pts[i + 1])):
                near = fields[layers[i]].nearest_obstacle(
                    net, tuple(pts[i]), tuple(pts[i + 1]))
                seg_fail = {"i": i, "layer": layers[i],
                            "a": list(pts[i]), "b": list(pts[i + 1]),
                            "nearest": near}
                break
        checks.append({"check": f"{key}_seg_ok", "ok": seg_fail is None,
                       "detail": seg_fail})
        # 层变点 = via：相邻两层 point_ok
        via_fail = None
        for i in range(len(layers) - 1):
            if layers[i] == layers[i + 1]:
                continue
            pt = tuple(pts[i + 1])
            for l in (layers[i], layers[i + 1]):
                if not fields[l].point_ok(net, pt):
                    near = fields[l].nearest_obstacle(net, pt, pt)
                    via_fail = {"i": i, "layers": (layers[i], layers[i + 1]),
                                "pt": list(pt), "field_layer": l,
                                "nearest": near}
                    break
            if via_fail is not None:
                break
        checks.append({"check": f"{key}_via_point_ok",
                       "ok": via_fail is None, "detail": via_fail})
    # pn_min_edge（段级组装门，阈值 0.155）
    me, pt = _path_pn_min_edge_pt(seg["P"]["path"], seg["P"]["layers"],
                                  seg["N"]["path"], seg["N"]["layers"],
                                  width)
    checks.append({"check": "pn_min_edge", "ok": me is not None and me >= PN_MIN_EDGE,
                   "detail": {"min_edge": round(me, 4) if me is not None else None,
                              "req": PN_MIN_EDGE,
                              "point": [round(v, 3) for v in pt] if pt else None}})
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def fact_validate(results: dict, spec_path=SPEC_PATH,
                  rules_path=RULES_PATH, board_path=REAL_BOARD):
    """对 report solve results 中全部 SOLVED 段做几何重放审计。"""
    from eda_core.drc_rules import BoardParser, DRCRuleLibrary
    board = BoardParser(str(board_path)).parse()
    rules = DRCRuleLibrary(str(rules_path))
    spec = load_json(spec_path)
    mcfg = make_config()
    snap = shared_snapshot(results)
    solved = solved_segments_in_order(results)
    per_seg = []
    for base, seg in solved:
        shared_segs, shared_vias = snap[(base, seg.get("name"))]
        r = replay_segment(board, rules, spec, mcfg, seg,
                           shared_segs, shared_vias)
        per_seg.append({"base": base, "segname": seg.get("name"),
                        "ok": r["ok"], "checks": r["checks"],
                        "n_shared_segs": len(shared_segs),
                        "n_shared_vias": len(shared_vias)})
    return {"n_solved": len(solved), "per_segment": per_seg,
            "all_pass": all(p["ok"] for p in per_seg)}


# ── 段级 fallback 归属（依据 SOLVED 段 escape kind）─────────────────
FALLBACK_KINDS = {"DIRECT", "VIA", "LONG", "LSWAP", "LSWAP_V",
                  "COL_STACK", "PAD_ROW_DIP"}

def fallback_segments(results: dict) -> list:
    """SOLVED 段中 escape.segments.*.kind 属自搜形态者（LANDING 除外）。"""
    out = []
    for base, seg in solved_segments_in_order(results):
        kinds = []
        esc = (seg or {}).get("escape") or {}
        for side in ("left", "right"):
            side_seg = (esc.get("segments") or {}).get(side) or {}
            for pol in ("P", "N"):
                k = (side_seg.get(pol) or {}).get("kind")
                if k:
                    kinds.append(k)
        if any(k in FALLBACK_KINDS for k in kinds):
            out.append({"base": base, "segname": seg.get("name"),
                        "kinds": sorted(set(kinds))})
    return out


if __name__ == "__main__":
    raise SystemExit("p3_v53_phase0_audit.py 为库模块，由 phase0_gate 调用")
