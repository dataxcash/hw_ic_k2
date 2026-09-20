#!/usr/bin/env python3
"""k1_sch_regen_acceptance_v1 — N-3（K1 原理图侧再生）**验收核**（草案 · 只读）。

用途：给定一份**再生后的** `k1/boards/k1_sch.yaml`，机判其是否满足「板为权威」的同源对账：
  A. `sheets[].placements` 的 refdes 集合 **== 板 footprint refdes 集合**（应为 42）
  B. 每个 placement 的 `symbol` 在 `symbols` 中已定义
  C. 每个 symbol 的 `footprint`（basename）== `k1_board.yaml#devices[ref].footprint`（basename）
  D. `nets` 成员集合 == `k1_nets.yaml#nets` 的成员集合（逐网）
  E. 渲染（共享 schlib）后 4 页组件数合计 == 42
用法：
  PYTHONPATH=_shared python3 k1_sch_regen_acceptance_v1.py --sch-yaml <k1_sch.yaml> [--render]
返回码：0 = 全过；1 = 有 FAIL（fail-closed）。
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, tempfile
import yaml

ROOT = "/home/fila/jqdDev_2025/ic_hw"
K1 = os.path.join(ROOT, "k1")
BOARD_YAML = os.path.join(K1, "boards", "k1_board.yaml")
NETS_YAML = os.path.join(K1, "boards", "k1_nets.yaml")
PCB = os.path.join(K1, "k1_v1.kicad_pcb")
RENDERER = os.path.join(ROOT, "k2", "tools", "k2_sch_gen_v1.py")


def bn(x: str) -> str:
    return str(x or "").split(":")[-1]


def board_refdes() -> dict:
    """板 footprint refdes -> footprint 名（pcbnew-free 正则；仅供 refdes/footprint 集合核对）。"""
    s = open(PCB, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r'\(footprint "([^"]+)"', s):
        seg = s[m.start():m.start() + 4000]
        r = re.search(r'\(property "Reference" "([^"]+)"', seg)
        if r:
            out[r.group(1)] = m.group(1)
    return out


def sch_placements(sch: dict) -> dict:
    out = {}
    for sh in sch.get("sheets") or []:
        for p in sh.get("placements") or []:
            out[p.get("ref")] = p.get("symbol")
    return out


def net_members(nets_doc: dict) -> dict:
    nets = nets_doc.get("nets") or {}
    return {k: sorted(map(str, v)) for k, v in nets.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sch-yaml", required=True)
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    sch = yaml.safe_load(open(a.sch_yaml, encoding="utf-8"))
    fails, oks = [], []

    def chk(name, cond, detail):
        (oks if cond else fails).append(f"{name}: {detail}")

    # A
    bref, pref = board_refdes(), sch_placements(sch)
    chk("A_refdes_set_equal", set(bref) == set(pref),
        f"板 {len(bref)} vs 图 {len(pref)}；板独有 {sorted(set(bref)-set(pref))} · 图独有 {sorted(set(pref)-set(bref))}")

    # B
    sym_names = {s.get("name") for s in (sch.get("symbols") or [])}
    undef = sorted({s for s in pref.values() if s not in sym_names})
    chk("B_symbols_defined", not undef, f"未定义 symbol：{undef}")

    # C
    dev = (yaml.safe_load(open(BOARD_YAML, encoding="utf-8")) or {}).get("devices") or {}
    sym_by = {s.get("name"): s for s in (sch.get("symbols") or [])}
    fp_bad = []
    for ref, sym in pref.items():
        want = bn((dev.get(ref) or {}).get("footprint"))
        got = bn((sym_by.get(sym) or {}).get("footprint"))
        if want and want != got:
            fp_bad.append(f"{ref}: 图={got} 板={want}")
    chk("C_footprint_matches_board", not fp_bad, f"不符：{fp_bad}")

    # D
    kn = net_members(yaml.safe_load(open(NETS_YAML, encoding="utf-8")) or {})
    sn = net_members(sch)
    nd = [f"{k}: 差 {sorted(set(kn.get(k, [])) ^ set(sn.get(k, [])))}" for k in sorted(set(kn) | set(sn))
          if set(kn.get(k, [])) != set(sn.get(k, []))]
    chk("D_nets_match_k1_nets", not nd, f"不一致网数 {len(nd)}：{nd[:6]}")

    # E
    n_render = None
    if a.render:
        outd = tempfile.mkdtemp(prefix="k1regen_")
        env = {**os.environ, "K2_SCH_YAML": os.path.abspath(a.sch_yaml), "K2_OUT_SCH": outd}
        r = subprocess.run([sys.executable, RENDERER], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            chk("E_render", False, f"渲染 rc={r.returncode}: {r.stderr.strip()[:200]}")
        else:
            rep = json.load(open(os.path.join(outd, "sandbox_report.json"), encoding="utf-8"))
            n_render = rep.get("yaml_components")
            chk("E_render_components_42", n_render == 42, f"渲染组件数={n_render}（期望 42）")

    print(json.dumps({"ok": not fails, "sch_yaml": a.sch_yaml,
                      "n_board_refdes": len(bref), "n_placements": len(pref),
                      "render_components": n_render,
                      "fails": fails, "oks": oks}, ensure_ascii=False, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
