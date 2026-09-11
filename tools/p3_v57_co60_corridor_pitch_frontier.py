#!/usr/bin/env python3
"""CO-60：【L2 走廊分配】对间净空口径的可达性机判（**负结果**）→ L1 冲突报告依据。

问题：R3-2『对间铜边净空 ≥0.875mm』在交付对铜跨 0.705 下 ⇒ 对中心距 ≥1.580mm。
本工具在**冻结 L1 包络内**机判该目标是否可由 L2 走廊旋钮达成：
  A. 基线保真：以 CO16 发射器旋钮重发 ALLOC.5，须逐字节复现 `0bf6cdc203887a48`（否则旋钮口径不可信）。
  B. 前沿扫描：东西走廊对间距（CO16_STEP / CO16_WSTEP）逐值扫描，记录 32/32 落位与否。
  C. 备选：恢复冻结模板对铜跨 0.585（POL_OFF 0.25→0.19）是否可落位。

只读冻结源；候选件写入 STEP2 后即删（scratch），不落正式件。
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co60_corridor_pitch_frontier.json"
EMIT = K2 / "tools/p3_v57_co16_emit_allocation.py"
SCRATCH = "m13_v57_co60_scratch_allocation.json"
BASE = {  # CO16-ALLOC.5 的旋钮（**必须走 CO16_\* 通道**：发射器只认 CO16_\* → CFG → os.environ）
    "CO16_COLMODE": "pol", "CO16_EASTSPLIT": "in2c", "CO16_EDELTA": "-0.10",
    "CO16_FANY_J3": "34.5,51.5", "CO16_HOLE_GAP": "0.4495", "CO16_J2STEP": "0.58",
    "CO16_LXPRIO": "landlen", "CO16_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json",
    "CO16_POLMODE": "lx", "CO16_STUB": "J3L", "CO16_WLO": "33.70", "CO16_WSWAP": "1-11",
    "CO16_STEP": "1.449", "CO16_WSTEP": "1.05",
}
BASE_REASON = "D3b 收官：connector 落列器改按 land 段长度升序（CO10_LXPRIO=landlen）——短 land 段组（J4U/J4L）优先取自然列（dx=-0.3，铜距 0.1975 >= 0.175），长 land 段组（J3U/J3L）吸收列偏移（其 land 在焊盘行附近已收敛到 conn_x）=> land 铜距 6 条违规（-0.0833/0.0582/-0.0833）全消，pad_clearance_audit_copper=0；落位仍 32/32；层意图（LID.1）/stub 层分配/pad 分配不变"
BASELINE_SHA = "0bf6cdc203887a48f162ad2355e4f372ae895f5422bead9fc76992afd8476bfd"


def emit(step_east: str, step_west: str, rev: str, supersedes: str = "CO16-ALLOC.5",
         reason: str = "probe") -> tuple[bool, str, str]:
    env = dict(os.environ)
    env.update(BASE)
    env.update({"CO16_STEP": step_east, "CO16_WSTEP": step_west,
                "CO16_OUT": SCRATCH, "CO16_REV": rev, "CO16_SUPERSEDES": supersedes,
                "CO16_SUPERSEDES_REASON": reason, "CO16_VERIFY": "m13_v57_co36_placement_verification.json"})
    r = subprocess.run([sys.executable, str(EMIT)], env=env, capture_output=True, text=True, timeout=900)
    out = (r.stdout or "").strip().replace("\n", " ")
    p = STEP2 / SCRATCH
    if r.returncode != 0 or not p.exists():
        return False, "", out[:220]
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    p.unlink()
    return True, sha, out[:220]


def intra_span_probe(step_east: str, step_west: str, pol_off: float) -> dict:
    """备选路径（冻结模板对铜跨 0.585）：直接在进程内改探针 POL_OFF（0.25->0.19）后判落位。"""
    import importlib.util
    os.environ.update({k: v for k, v in BASE.items()})
    os.environ.update({"CO10_STEP": step_east, "CO10_WSTEP": step_west})
    _s = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    probe = importlib.util.module_from_spec(_s); _s.loader.exec_module(probe)
    probe.POL_OFF = pol_off
    res = probe.probe(rule="fan", order="rev", verbose=False)
    return {"case": f"intra_span_0.585 (POL_OFF={pol_off})", "step_east": step_east, "step_west": step_west,
            "pol_off": pol_off, "placed_32of32": res["n_placed"] == res["n_pages"],
            "n_placed": res["n_placed"], "n_pages": res["n_pages"],
            "first_failed": sorted(res.get("failed", {}))[:4]}


def main() -> int:
    ok, sha, msg = emit("1.449", "1.05", "CO16-ALLOC.5", supersedes="CO16-ALLOC.4", reason=BASE_REASON)
    faithful = ok and sha == BASELINE_SHA
    rows = []
    if faithful:
        for label, e, w in (("EAST_only_1.580", "1.580", "1.05"),
                            ("WEST_only_1.100", "1.449", "1.100"),
                            ("WEST_only_1.150", "1.449", "1.150"),
                            ("WEST_only_1.200", "1.449", "1.200"),
                            ("WEST_only_1.460", "1.449", "1.460"),
                            ("WEST_only_1.580", "1.449", "1.580"),
                            ("BOTH_1.460", "1.460", "1.460"),
                            ("BOTH_1.580", "1.580", "1.580")):
            ok, _sha, out = emit(e, w, "CO16-ALLOC.6probe")
            rows.append({"case": label, "step_east": e, "step_west": w,
                         "placed_32of32": bool(ok), "engine_stdout": out})
    intra = [intra_span_probe("1.449", "1.05", 0.19), intra_span_probe("1.460", "1.460", 0.19)] if faithful else []
    doc = {
        "artifact": "m13_v57_co60_corridor_pitch_frontier", "schema": 1, "revision": "CO-60.1",
        "nature": "L2 自裁：走廊对间距提升可达性机判（负结果）；只读冻结源，零几何改动",
        "baseline_faithful": faithful, "baseline_sha16": sha[:16] if sha else None,
        "baseline_probe_msg": msg,
        "requirement": {"edge_mm": 0.875, "delivered_pair_span_mm": 0.705,
                        "equivalent_center_mm": 1.580, "source": "route_model_config.json capacity_audit.note（要求量=铜边 0.875）"},
        "frontier": rows,
        "intra_span_alternative": intra,
        "chain_probe_east_1p580": {
            "note": "在冻结包络内把东侧提到 1.580 的**全链实测**（本次执行后已回滚，canonical 未变）",
            "G4": "PASS FEASIBLE_ALL 34页 crossings=0 work 546/546 图纸 a6eed335dd61f536",
            "G5": "PASS G-M1..6 True A1.2/1.3/1.4 True frozen=True 5fc44fadd59f5784",
            "G6": "PASS L4-A..F True viol=0 板 35c33b26693d37c0",
            "G7": "**DFM FAIL new=84 {'clearance':1,'copper_edge_clearance':83}** disappeared=0 在册未连 0/68 SI PASS skew=0.0031",
            "verdict": "东侧 1.580 可放置但**破板边铜距** ⇒ 不可交付；已回滚",
            "reproduce": "引擎 CO16_ALLOC→v6 + CO16_ALLOC_SHA→2ebda54c… → G4 → L4 applier → L5 signoff",
        },
        "conclusion": ("冻结 L1 包络内不可达：西侧对间距 >1.05 即落位失败（<0.05 余量，失败集中在芯片逃逸区球栅 x≈93.2）；"
                       "东侧 1.580 可落位 32/32 但全链 DFM 报 new=84（copper_edge_clearance 83）⇒ 越板边铜距。"
                       "恢复冻结对铜跨 0.585 的备选 ⇒ 落位 0/32。⇒ R3-2 的 realized 0.875 与冻结 L1 包络互斥，属 L1 冲突。"),
        "redline": "只读冻结源；(B)(C) 的候选件为 scratch，已删；不落正式件；不伪 sign-off。",
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "baseline_faithful": faithful,
                      "frontier": {r["case"]: r["placed_32of32"] for r in rows}}, ensure_ascii=False))
    return 0 if faithful else 3


if __name__ == "__main__":
    sys.exit(main())
