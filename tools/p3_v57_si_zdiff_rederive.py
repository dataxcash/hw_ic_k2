#!/usr/bin/env python3
"""CO-54：差分阻抗 Zdiff **重导 harness**（L2/SI；一阶模型 = 仓内通用模型层）。

模型层（非本工具自创）：`_shared/eda_core/stackup.py` 的 IPC-2141 边缘耦合微带/对称带状线，
该模型**能复现 SPEC 自陈基准**（H1=5.0mil/Er1=4.3, w=0.205, s=0.175 → 85.1Ω）⇒ 与 SPEC 同源。
本工具**不是 sign-off**：SPEC 自陈 `coupon_required=true`，最终值须 SI9000 + 板厂券。

两种模式：
  1) 默认（无 8L 叠层输入）→ **敏感性包络**：交付 s=0.295 vs SPEC s=0.175 的 ΔZ%，按 H 扫（Er 不敏感）。
     ⇒ 把 CO-53 开放项从"定性"变"定量"；仍保留 conformance=NOT_DEMONSTRATED。
  2) `--stackup <json>`（8L 介质叠层输入到齐后）→ 分层重导 85Ω 的 (w,s)，并产出 **ECO rev-4 提议**（不落 SPEC）。

输出：m13_v57_co54_zdiff_sensitivity.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-3.json"
AUDIT = STEP2 / "m13_v57_co54_spec_delivery_audit.json"
OUT = STEP2 / "m13_v57_co54_zdiff_sensitivity.json"
sys.path.insert(0, str(ROOT / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0, _symmetric_stripline_z0  # noqa: E402

SPEC_DATUM = {"h_mm": 0.127, "er": 4.3, "t_mm": 0.035, "w_mm": 0.205, "s_mm": 0.175, "claimed_zdiff": 85.1}
H_SCAN = [0.10, 0.127, 0.15, 0.20, 0.25, 0.30]
ER_SCAN = [3.99, 4.16, 4.3, 4.5, 4.6]


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(K2))
    except ValueError:
        return str(p)


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def zdiff_microstrip(w: float, s: float, h: float, er: float, t: float) -> float:
    return _edge_coupled_microstrip_z0(w, h, t, er, s)


def zdiff_stripline(w: float, s: float, h: float, er: float, t: float) -> float:
    return _symmetric_stripline_z0(w, h, t, er, s)


def solve_ws(target: float, kind: str, h: float, er: float, t: float, tol: float = 1.0) -> dict:
    """在 (w,s) 网格上取 |Z-target|<=tol 且最接近 SPEC 几何 (0.205,0.175) 的解。"""
    f = zdiff_microstrip if kind == "microstrip" else zdiff_stripline
    best = None
    for si in range(10, 51):
        for wi in range(5, 36):
            s, w = si / 100, wi / 100
            z = f(w, s, h, er, t)
            if abs(z - target) > tol:
                continue
            dist = abs(w - 0.205) + abs(s - 0.175)
            if best is None or dist < best["_dist"]:
                best = {"w_mm": w, "s_mm": s, "zdiff_ohm": round(z, 2), "_dist": dist}
    if best:
        best.pop("_dist")
    return best or {"w_mm": None, "s_mm": None, "zdiff_ohm": None}


def load_stackup(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    need = {"microstrip": ("h_mm", "er"), "stripline": ("h_mm", "er")}
    for k, keys in need.items():
        if k not in d or any(x not in d[k] for x in keys):
            raise SystemExit(f"stackup json 缺少 {k}.{{{','.join(keys)}}}：{path}")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stackup", type=Path, default=None, help="8L 介质叠层输入 json（材料+逐层厚度→等效 H/Er）")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    imp = spec["impedance"]
    target = imp["target_zdiff"]
    datum = zdiff_microstrip(SPEC_DATUM["w_mm"], SPEC_DATUM["s_mm"], SPEC_DATUM["h_mm"],
                             SPEC_DATUM["er"], SPEC_DATUM["t_mm"])
    if abs(datum - SPEC_DATUM["claimed_zdiff"]) > 0.5:
        print(f"fail-fast: 模型保真度不足 datum={datum:.2f} vs SPEC 自陈 {SPEC_DATUM['claimed_zdiff']}")
        return 2

    delivered_s = 0.295
    envelope = []
    for h in H_SCAN:
        row = {"h_mm": h, "zdiff_at_spec_s_mm": {str(er): round(zdiff_microstrip(0.205, 0.175, h, er, 0.035), 2) for er in ER_SCAN}}
        row["zdiff_at_delivered_s_mm"] = {str(er): round(zdiff_microstrip(0.205, delivered_s, h, er, 0.035), 2) for er in ER_SCAN}
        zs = zdiff_microstrip(0.205, 0.175, h, 4.3, 0.035)
        zd = zdiff_microstrip(0.205, delivered_s, h, 4.3, 0.035)
        row["delta_pct_er4p3"] = round(100 * (zd / zs - 1), 2)
        row["within_tolerance_10pct_at_er4p3"] = abs(zd - target) <= 0.10 * target
        envelope.append(row)

    rec = {
        "artifact": "m13_v57_co54_zdiff_sensitivity", "schema": 1, "revision": "CO-54.1",
        "authority": "L2/SI（LAYOUT_CONSTITUTION 第二章）+ handoff §5(2) + CO-53 §3.2",
        "model": {"source": "_shared/eda_core/stackup.py", "method": "IPC-2141 (edge-coupled microstrip / symmetric stripline)",
                  "kind": "first_order", "signoff": False,
                  "required_for_signoff": "SI9000 + 板厂阻抗券 (SPEC coupon_required=true)"},
        "spec_datum_check": {**SPEC_DATUM, "model_zdiff_ohm": round(datum, 2), "delta_ohm": round(datum - SPEC_DATUM["claimed_zdiff"], 2)},
        "delivered_basis": {"intra_center_mm": 0.5, "spec_p_gap_mm": spec["net_classes"]["PCIe85"]["diff_pair"]["p_gap"],
                            "delivered_edge_gap_mm": delivered_s, "source": "CO-54 audit (L4 construction 实测)"},
        "sensitivity_envelope": envelope,
        "conformance": "NOT_DEMONSTRATED",
        "gate_impact": "none（不改 SPEC/板/几何；仅记录）",
        "input_gap": {"item": "8L 介质叠层（材料 + 逐层介质厚度）", "provided": a.stackup is not None,
                      "repo": "缺（四源/板/公开文档均无 8L 逐层厚度）",
                      "effect": "无此输入 ⇒ 只能给敏感性包络，不能给分层 85Ω 终值"},
    }

    if a.stackup is not None:
        st = load_stackup(a.stackup)
        t_ms = float(st["microstrip"].get("t_mm", 0.035))
        r_ms = solve_ws(target, "microstrip", float(st["microstrip"]["h_mm"]), float(st["microstrip"]["er"]), t_ms)
        t_sl = float(st["stripline"].get("t_mm", 0.0175))
        r_sl = solve_ws(target, "stripline", float(st["stripline"]["h_mm"]), float(st["stripline"]["er"]), t_sl)
        rec["stackup_input"] = {"path": str(a.stackup), "sha16": sha16(a.stackup), "name": st.get("name")}
        rec["rederivation"] = {
            "microstrip_F_Cu": {**r_ms, "h_mm": st["microstrip"]["h_mm"], "er": st["microstrip"]["er"],
                                "zdiff_at_delivered": round(zdiff_microstrip(0.205, delivered_s, float(st["microstrip"]["h_mm"]),
                                                                             float(st["microstrip"]["er"]), t_ms), 2)},
            "stripline_In2_In6": {**r_sl, "h_mm": st["stripline"]["h_mm"], "er": st["stripline"]["er"],
                                  "caveat": "对称带状线近似；非对称叠构须 SI9000"},
        }
        rec["eco4_proposal"] = {
            "applied": False,
            "patch": {"stackup.material": st.get("name"),
                      "impedance.model": f"SI9000 <{st.get('name')}>",
                      "impedance.width_mm": r_ms["w_mm"], "impedance.gap_mm": r_ms["s_mm"],
                      "net_classes.PCIe85.diff_pair.p_gap": r_ms["s_mm"],
                      "note": "p_gap 语义（精确目标 vs 下限）须同时裁定；走廊 PITCH 公式随之复核（CO-54 F3）"},
        }

    a.out.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": rel(a.out), "sha16": sha16(a.out),
                      "datum_ohm": round(datum, 2), "delta_pct_by_h": {str(r["h_mm"]): r["delta_pct_er4p3"] for r in envelope},
                      "rederivation": rec.get("rederivation", "not_run(no --stackup)")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
