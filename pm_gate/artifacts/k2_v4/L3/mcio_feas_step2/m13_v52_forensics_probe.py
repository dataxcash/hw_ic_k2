#!/usr/bin/env python3
"""M14 v52 差分取证 v2（一次性诊断，非引擎结论，仅取证）。

两手段互证，零引擎文件改动：
  A) (b) 决定性实验：DN0 out_MCIO 以 shared_segs=[]（隔离同 base input 段）
     solve_pair_v4 vs 链内（带 input 段共享）——若隔离后可解 → input 段占位=(b)
     → R2 段族清网域；仍 INFEASIBLE → 非自身段，查 dip 逐候选首拒定 (a)/(c)。
  B) 场 API 包装：子类覆写 _escape_pair（仅包装 band/fcu/esc 场对象 + 转发 super），
     记录每个 seg_ok/point_ok 的 False + 最近障碍 net/dist/req（真引擎枚举序，
     零候选逻辑复制）。
"""
import json, os, sys, tempfile
from pathlib import Path
from collections import Counter

REPO = Path("/home/fila/jqdDev_2025/ic_hw/k2")
SHARED = Path("/home/fila/jqdDev_2025/ic_hw/_shared")
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(REPO / "tools"))

import p3_k2_real_board_e2e as E

# ── 1. 组装 SolveInput（同 e2e main L344-397）─────────────────────────
spec = E.load(E.SPEC_PATH)
escape_spec = E.load(E.ESCAPE_PATH)
rules = E.load(E.RULES_PATH)
base_cfg = E.load(E.CONFIG_PATH)
j2_pads = E.extract_j2_pads(E.REAL_BOARD)
region_pads, region_demands = {}, {}
for rid in ("J2", "MCIO", "U7", "U3"):
    x_lo, x_hi = E.REGION_WINDOWS[rid]
    region_pads[rid] = E.extract_region_pads(E.REAL_BOARD, x_lo, x_hi, rid)
    region_demands[rid] = E.derive_region_demands(E.REAL_BOARD, rid,
                                                  suffix_only=(rid != "J2"))
corridors = spec.get("corridors") or []
config = E.build_config(base_cfg)
cap_dem = E.derive_capacity_demands(spec, corridors, escape_spec, config)
spec["derived"] = {
    "nets": sorted({d["base"] for d in cap_dem}),
    "landing_demands": E.derive_landing_demands(j2_pads),
    "landing_pads": region_pads,
    "landing_demands_J2": region_demands["J2"],
    "landing_demands_MCIO": region_demands["MCIO"],
    "landing_demands_U7": region_demands["U7"],
    "landing_demands_U3": region_demands["U3"],
    "capacity_demands": cap_dem,
    "via_zones": E.derive_via_zones(spec, escape_spec, j2_pads, E.REAL_BOARD),
    "cap_walls": E.derive_cap_walls(spec),
    "cap_wall_pads_MCIO": E.derive_cap_wall_pads(E.REAL_BOARD, spec),
}
ri = E.spec_to_route_input(spec, escape_spec, j2_pads, config)
ri.obstacles.pads = list(j2_pads)
inp = E.SolveInput(route_input=ri, board_path=str(E.REAL_BOARD),
                   spec=spec, rules=rules, config=config)
pipe = E.SolvePipeline(inp)
feas = pipe.run_feasibility()
cap = pipe.run_capacity()
alloc_tab = pipe.run_alloc(cap)
land_tab = pipe.run_landing(alloc_tab)
print("[f52] alloc solved:", alloc_tab.solved, "infeasible:", alloc_tab.infeasible,
      "| landing verdict:", land_tab.verdict)

hs_cfg = (config or {}).get("hs_route_model")
from eda_core.route_input import ModelConfig
mcfg = ModelConfig.from_dict(hs_cfg) if hs_cfg else None
if mcfg is not None:
    _ec = (config.get("channel_alloc") or {}).get("escape_check") or {}
    if isinstance(_ec, dict) and float(_ec.get("keepout", 0.0) or 0.0) > 0:
        mcfg.escape_env_keepout = float(_ec.get("keepout", 0.0))
        mcfg.escape_env_half_track = float(_ec.get("half_track", 0.0) or 0.0)
        mcfg.escape_env_pair_half = float(_ec.get("pair_half", 0.0) or 0.0)
        mcfg.escape_env_band_spans = _ec.get("band_spans") or None

_tmp = tempfile.mkdtemp(prefix="f52_")
spec_f = os.path.join(_tmp, "spec.json"); json.dump(spec, open(spec_f, "w"))
alloc_f = os.path.join(_tmp, "alloc.json"); json.dump({"alloc": dict(alloc_tab.alloc)}, open(alloc_f, "w"))
rules_f = os.path.join(_tmp, "rules.json"); json.dump(rules, open(rules_f, "w"))

NETS = {}
b = E.BoardParser(str(E.REAL_BOARD)).parse()
board_nets = {p.net for p in b.pads}
for base in ("DN0", "DN6"):
    stem = base[:-1]; num = base[-1]
    in_p, in_n = f"PCIE_{base}_P", f"PCIE_{base}_N"
    out_p = E.config_chain_out_pattern.format(stem=stem, num=num, pn="P", suf="_MCIO") \
        if hasattr(E, "config_chain_out_pattern") else None
    NETS[base] = {
        "in": (in_p, in_n),
        "out": (f"PCIE_DN_OUT{num}_P_MCIO", f"PCIE_DN_OUT{num}_N_MCIO"),
    }
print("[f52] nets DN0 out:", NETS["DN0"]["out"], "| DN6 out:", NETS["DN6"]["out"])


# ── 3. 场 API 包装子类（真引擎枚举，仅记录）──────────────────────────
class WField:
    """日志包装：转发全部属性/方法；seg_ok/point_ok False 时记首拒+最近障碍。

    最近障碍在拒绝瞬间由 inner.nearest_obstacle 取（同 inner 场对象，口径一致）。
    stage 标记由 owner.f52_stage 提供（外层 escape 的 flip + 阶段）。
    """
    def __init__(self, inner, role, log, owner=None):
        self._inner = inner
        self._role = role
        self._log = log
        self._owner = owner
    def __getattr__(self, k):
        return getattr(self._inner, k)
    def _obs(self, net, a, b):
        try:
            return self._inner.nearest_obstacle(net, a, b)
        except Exception:
            return None
    def seg_ok(self, net, a, b, width=None):
        r = self._inner.seg_ok(net, a, b, width)
        if not r:
            self._log.append({"stage": (getattr(self._owner, "f52_stage", "?")
                                        if self._owner else "?"),
                              "role": self._role, "check": "seg_ok", "net": net,
                              "pts": [list(a), list(b)],
                              "obs": self._obs(net, a, b)})
        return r
    def point_ok(self, net, p):
        r = self._inner.point_ok(net, p)
        if not r:
            self._log.append({"stage": (getattr(self._owner, "f52_stage", "?")
                                        if self._owner else "?"),
                              "role": self._role, "check": "point_ok", "net": net,
                              "pts": [list(p)],
                              "obs": self._obs(net, (p[0]-1e-3, p[1]),
                                               (p[0]+1e-3, p[1]))})
        return r


from eda_core.hs_route_model import HSRouteModel as _HRM
class F52Model(_HRM):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.f52_log = []
        self.f52_calls = []
        self.f52_stage = "?"
        self.f52_pn = {}
        self.f52_pn_ev = []

    def _col_stack_escape(self, band_field, fcu_field, esc_field,
                          pad_p, pad_n, corr_x, track_y, bound_x,
                          direction, net_p, net_n, flip, esc_layer,
                          pn_ok, carrier_field=None, carrier_layer=None):
        self.f52_stage = "col_stack"
        try:
            return super()._col_stack_escape(
                band_field, fcu_field, esc_field, pad_p, pad_n, corr_x,
                track_y, bound_x, direction, net_p, net_n, flip, esc_layer,
                self._wrap_pn(pn_ok, "col_stack"), carrier_field=carrier_field,
                carrier_layer=carrier_layer)
        finally:
            self.f52_stage = "?"

    def _pad_row_dip_escape(self, band_field, fcu_field, esc_field,
                            pad_p, pad_n, corr_x, track_y, bound_x,
                            direction, net_p, net_n, flip, esc_layer, pn_ok):
        self.f52_stage = "dip"
        try:
            return super()._pad_row_dip_escape(
                band_field, fcu_field, esc_field, pad_p, pad_n, corr_x,
                track_y, bound_x, direction, net_p, net_n, flip, esc_layer,
                self._wrap_pn(pn_ok, "dip"))
        finally:
            self.f52_stage = "?"

    def _wrap_pn(self, pn_ok, stage):
        import functools
        cnt = {"n": 0, "rej": 0}
        self.f52_pn.setdefault(stage, cnt)

        @functools.wraps(pn_ok)
        def w(p_pts, p_layers, n_pts, n_layers):
            r = pn_ok(p_pts, p_layers, n_pts, n_layers)
            cnt["n"] += 1
            if not r:
                cnt["rej"] += 1
                if cnt["rej"] <= 8:
                    from eda_core.hs_route_model import _path_pn_min_edge_pt
                    me, pt = _path_pn_min_edge_pt(
                        p_pts, p_layers, n_pts, n_layers,
                        (self.spec.get("impedance") or {}).get("width_mm", 0.205))
                    self.f52_pn_ev.append({"stage": stage, "min_edge": round(me, 4)
                                           if me is not None else None,
                                           "pt": [round(v, 3) for v in pt] if pt else None,
                                           "n_pn": cnt["n"]})
            return r
        return w

    def _escape_pair(self, band_field, fcu_field, esc_field,
                     pad_p, pad_n, corr_x, track_y, bound_x,
                     direction, net_p, net_n, flip=False, esc_layer="In2.Cu",
                     landing_pair=None, chip_landing_pair=None,
                     max_slide=30, cs_alt_field=None, cs_alt_layer=None):
        self.f52_calls.append({
            "direction": direction, "net_p": net_p, "net_n": net_n,
            "corr_x": corr_x, "track_y": track_y, "bound_x": bound_x,
            "pad_p": list(pad_p["pos"]), "pad_n": list(pad_n["pos"]),
            "flip": flip, "esc_layer": esc_layer,
            "cs_alt_layer": cs_alt_layer,
        })
        # 仅 chip 侧右逃逸包装（记拒），其余转发真场（行为不变）
        if direction < 0 and (net_p.endswith("_MCIO") or net_n.endswith("_MCIO")):
            log = self.f52_log
            wb = WField(band_field, "band", log, self)
            wf = WField(fcu_field, "fcu", log, self)
            we = WField(esc_field, "esc", log, self)
            wa = WField(cs_alt_field, "cs_alt", log, self) if cs_alt_field is not None else None
            return super()._escape_pair(
                wb, wf, we, pad_p, pad_n, corr_x, track_y, bound_x,
                direction, net_p, net_n, flip=flip, esc_layer=esc_layer,
                landing_pair=landing_pair,
                chip_landing_pair=chip_landing_pair, max_slide=max_slide,
                cs_alt_field=wa, cs_alt_layer=cs_alt_layer)
        return super()._escape_pair(
            band_field, fcu_field, esc_field, pad_p, pad_n, corr_x, track_y,
            bound_x, direction, net_p, net_n, flip=flip, esc_layer=esc_layer,
            landing_pair=landing_pair, chip_landing_pair=chip_landing_pair,
            max_slide=max_slide, cs_alt_field=cs_alt_field,
            cs_alt_layer=cs_alt_layer)



def _chain_out(base):
    m = F52Model(str(E.REAL_BOARD), spec_f, alloc_f, rules_f,
                 config=mcfg, route_input=ri, landing=dict(land_tab.allocation))
    res = m.solve_chain_v4(base)
    seg = next((s for s in res.get("segments", []) if s.get("name") == "out_MCIO"), None)
    return m, res, seg

def _ablate_iso(base):
    """(b) 隔离实验：out_MCIO 无同 base input 段共享（模拟段族清网）→ 若 SOLVED 即 (b)。"""
    m = F52Model(str(E.REAL_BOARD), spec_f, alloc_f, rules_f,
                 config=mcfg, route_input=ri, landing=dict(land_tab.allocation))
    num = base[-1]
    np_, nn_ = f"PCIE_DN_OUT{num}_P_MCIO", f"PCIE_DN_OUT{num}_N_MCIO"
    return m, m.solve_pair_v4(np_, nn_, base, "out_MCIO",
                              shared_segs=[], shared_vias=[])


# ── A. DN0 链（对照组，验证自校验 + fail_forms 双 flip）────────────
m, res, seg = _chain_out("DN0")
print(f"[A] DN0 chain out_MCIO -> {seg.get('status') if seg else '?'}", flush=True)
if seg and seg.get("status") == "SOLVED":
    print("  right:", json.dumps((seg.get("escape") or {}).get("segments", {}).get("right"),
                                 ensure_ascii=False))
else:
    print("  reason:", (seg.get("reason") or "")[:200])
    ff = seg.get("fail_forms") or {}
    for fk in ("flip_False", "flip_True"):
        e = (ff.get(fk) or {}).get("esc") or {}
        print(f"    {fk}: kind={e.get('kind')} reason={(e.get('reason') or '')[:150]}", flush=True)
pn = m.f52_pn
print("  pn_ok calls/rejects:", {s: dict(d) for s, d in pn.items()}, flush=True)
from collections import Counter as _C
_dip_ev = [ev for ev in m.f52_pn_ev if ev["stage"] == "dip"]
_dc = _C((tuple(ev["pt"]), ev["min_edge"]) for ev in _dip_ev)
print("    dip pn reject 分布 (top8):", flush=True)
for (pt, me), n in _dc.most_common(8):
    print(f"      pt={pt} min_edge={me} n={n}", flush=True)
print(f"    dip pn reject 去重坐标数: {len(_dc)}", flush=True)
# 完整序列尾部（最后 5 条拒 + 有无 pass 证据）
for ev in _dip_ev[-5:]:
    print("    dip pn ev tail:", ev, flush=True)

# ── B. (b) 隔离实验（决定性）：shared=[] 下 DN0/1/3 能否解 out_MCIO ──
print("\n[B] ablation: out_MCIO solved with shared_segs=[] (no own-input-seg occupancy)",
      flush=True)
for base in ("DN0", "DN1", "DN3", "DN6"):
    m, r = _ablate_iso(base)
    st = r.get("status")
    extra = ""
    if st == "SOLVED":
        esc = r.get("escape", {})
        extra = " | right=" + json.dumps(esc.get("segments", {}).get("right"),
                                         ensure_ascii=False)[:220]
    else:
        extra = " | " + (r.get("reason") or "")[:170]
    print(f"  {base} iso(shared=[]) -> {st}{extra}", flush=True)
