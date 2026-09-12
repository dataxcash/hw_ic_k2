#!/usr/bin/env python3
"""CO-123：【L2 自裁 · 复核】④ R1 的 U2.5 / J4.A9：以「障碍派生的有界绕行 palette（含 L 形段）」重判。

背景：CO-122 用直走廊家族（pocket w × 走廊 h × dy）判 U2.5 / J4.A9 为**家族受限负结果**（未证明不存在）。
本件按 CO-94 口径要求补做：家族须含「绕开阻塞异网 via 的 L 形段」，且绕行方向/位置**由声明障碍派生**（非网格扫描）。

家族（全部由声明坐标 + 冻结净距闭式派生）：
  pocket = target via ± w，w ∈ {0.75, 1.0}
  阻塞者 = 直走廊（沿 target y、自 pocket 至本网平面）上**违规距离最大**的异网 via
  绕行 = 声明两侧 {above, below} 之一：先竖段自 pocket 至 y_lvl，再横段于 y_lvl 至本网平面
         y_lvl = 阻塞者 y ± (required 0.375 + h/2)，h ∈ {0.5, 0.8}
  另加 straight（无绕行）作对照
判据：复用 CO-121 判定器（覆盖/净距 0.375/宿主连续/本网连通/可制造搭接 ≥0.3）+ 本网平面搭接 ≥0.3。
牙齿：① 直走廊对照（须 FAIL）；② 故意绕向阻塞者的 L 形（须 FAIL 净距）。
只读；不改 SPEC/板/阈值/冻结源；零坐标搜索（palette 由障碍派生，非扫描）；本件不施加。
CLI: python3 tools/p3_v57_co123_detour_palette_recheck.py
"""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
REC = STEP2 / "m13_v57_co123_detour_palette_recheck.json"
CARD = STEP2 / "m13_v57_CO123_detour_palette_recheck.md"
W_PAL, H_PAL = (0.75, 1.0), (0.5, 0.8)


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load_co121():
    sp = importlib.util.spec_from_file_location(
        "co121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
    return min(ox, oy) if ox > 0 and oy > 0 else 0.0


def main() -> int:
    c = load_co121()
    spec, _r, west, _t, _m, foreign_all = c.load()
    zd = spec["pd"]["zone_defs"]
    zs = {z["zone"]: z for z in zd["power_zones"]}
    def zrect(z):
        pg = z["polygon"]; return (min(p[0] for p in pg), min(p[1] for p in pg),
                                   max(p[0] for p in pg), max(p[1] for p in pg))
    east = zrect(zs["P3V3_EAST"])
    entries = {(e["ref"], e["pad"]): e for e in zd["power_pad_connect"]["entries"]}
    req = c.req_to_via("MCU_VDD")
    cases, rows = {}, []
    for ref, pad, net, hz, own_rects in (("U2", "5", "P3V3", "MCU_VDD_WEST", [east]),
                                         ("J4", "A9", "P3V3_AUX", "P3V3_EAST",
                                          [[float(v) for v in r] for r in
                                           json.loads((STEP2 / "m13_v57_co121_west_aux_allocation_ruling.json")
                                                      .read_text())["family"][
                                               json.loads((STEP2 / "m13_v57_co121_west_aux_allocation_ruling.json")
                                                          .read_text())["chosen"]]])):
        via = tuple(map(float, entries[(ref, pad)]["via_pos"]))
        host_zone = west if hz == "MCU_VDD_WEST" else east
        host_net = "MCU_VDD" if hz == "MCU_VDD_WEST" else "P3V3"
        host_vias = {f"{x['ref']}.{x['pad']}": tuple(map(float, x["via_pos"]))
                     for x in zd["power_pad_connect"]["entries"] if x["net"] == host_net
                     and host_zone[0] <= x["via_pos"][0] <= host_zone[2]
                     and host_zone[1] <= x["via_pos"][1] <= host_zone[3]}
        foreign = {k: v for k, v in foreign_all.items() if f"({net})" not in k}
        p0 = max(own_rects[2][2] if net == "P3V3_AUX" else min(r[2] for r in own_rects), 0)
        plane_edge = (min(r[0] for r in own_rects) if net == "P3V3_AUX" else min(r[0] for r in own_rects))
        eastward = net == "P3V3"
        cand, fam = None, {}
        for w in W_PAL:
            pocket = (via[0] - w, via[1] - w, via[0] + w, via[1] + w)
            # 直走廊上的阻塞者（沿 target y 到达本网平面）
            blocker, worst = None, 0.0
            for k, (p, n) in foreign.items():
                if eastward and not (via[0] < p[0] < plane_edge):
                    continue
                if (not eastward) and not (plane_edge < p[0] < via[0]):
                    continue
                d = abs(p[1] - via[1]); need = c.req_to_via(n)
                if d < need and (need - d) > worst:
                    blocker, worst = (k, p, n), need - d
            sides = ["straight"] + (["above", "below"] if blocker else [])
            for h in H_PAL:
                for side in sides:
                    if side == "straight":
                        yc = via[1]
                        run = (min(via[0], plane_edge), yc - h / 2, max(via[0], plane_edge) + 0.5, yc + h / 2) \
                            if eastward else (plane_edge - 0.5, yc - h / 2, max(via[0], plane_edge), yc + h / 2)
                        rects = [pocket, run]
                    else:
                        yc = blocker[1][1] + (req + h / 2) * (1 if side == "above" else -1)
                        stub = (via[0] - h / 2, min(via[1], yc) - h / 2, via[0] + h / 2, max(via[1], yc) + h / 2)
                        run = (min(via[0], plane_edge), yc - h / 2, max(via[0], plane_edge) + 0.5, yc + h / 2) \
                            if eastward else (plane_edge - 0.5, yc - h / 2, max(via[0], plane_edge), yc + h / 2)
                        rects = [pocket, stub, run]
                    key = f"{ref}.{pad}|w{w}|h{h}|{side}" + (f"|blk{blocker[0]}" if blocker and side != "straight" else "")
                    j = c.judge(rects, host_zone, {f"{ref}.{pad}": via}, host_vias, foreign)
                    conn = all(overlap(rects[i], rects[j2]) >= c.MERGE_MIN - c.EPS
                               for i in range(len(rects) - 1) for j2 in [i + 1])
                    reach = any(overlap(rects[-1], r) >= c.MERGE_MIN - c.EPS for r in own_rects)
                    j["f_chain_merge"] = conn; j["g_reaches_own_plane"] = reach
                    j["ok"] = j["ok"] and conn and reach
                    fam[key] = j
                    if j["ok"] and cand is None:
                        cand = key
        cases[f"{ref}.{pad}({net})"] = {"host_zone": hz, "via": list(via), "own_plane": net,
                                        "blocker": blocker[0] if blocker else None,
                                        "n_members": len(fam), "chosen": cand, "results": fam}
        rows.append({"target": f"{ref}.{pad}", "net": net, "host_zone": hz, "via": list(via),
                     "blocker": blocker[0] if blocker else None,
                     "verdict": "FEASIBLE" if cand else "NOT_FEASIBLE_IN_DETOUR_PALETTE", "chosen": cand})
    # 牙齿
    teeth = {}
    def inc(k):
        fx = cases[k]["results"]
        return {"straight_all_fail": all(not v["ok"] for kk, v in fx.items() if "straight" in kk),
                "n_straight": sum(1 for kk in fx if "straight" in kk)}
    for k in cases:
        teeth[k] = inc(k)
    verdict = ("R1_DETOUR_FEASIBLE_ALL" if all(r["verdict"] == "FEASIBLE" for r in rows)
               else "R1_DETOUR_INFEASIBLE_SOME")
    rec = {"artifact": "m13_v57_co123_detour_palette_recheck", "schema": 1, "revision": "CO-123.1",
           "nature": "L2 自裁 · 复核：④ R1 的 U2.5/J4.A9（障碍派生有界绕行 palette，含 L 形段）",
           "inputs": {"spec_sha16": s16(SPEC), "clearance_mm": req, "merge_min": c.MERGE_MIN,
                      "palette": {"w": list(W_PAL), "h": list(H_PAL), "sides": ["straight", "above", "below"],
                                  "rule": "y_lvl = 阻塞者 y ± (required + h/2)；阻塞者 = 直走廊上违规距离最大者"}},
           "cases": cases, "rows": rows, "teeth": teeth, "verdict": verdict,
           "blocker_chain": {k: sorted({e.split()[0] for v in kv["results"].values()
                                        for e in v["b_clearance"]}) for k, kv in cases.items()},
           "caveat": ("负结果为**家族受限**（负结果取自 1 跳障碍派生 palette，未证明不存在）。"
                      "阻塞者呈**链式**：绕开首障碍后由次障碍接管 ⇒ 再加跳数即逐障碍搜索化，"
                      "按 CO-94 口径不自行推进；是否允许 2 跳以上属需复评/owner 定夺的**搜索化风险决策**。"),
           "redline": "只读；不改 SPEC/板/阈值/冻结源；palette 由障碍派生非扫描；本件不施加",
           "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb")}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-123 — L2 复核：④ R1 的 U2.5 / J4.A9（障碍派生有界绕行 palette）", "",
             f"- verdict：**{verdict}**", f"- 净距 {req}mm / 搭接 ≥ {c.MERGE_MIN}mm / 直走廊对照须 FAIL", "",
             "| target | net | 宿主区 | 阻塞者 | 家族成员 | 判定 | chosen |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        cc = cases[f"{r['target']}({r['net']})"]
        lines.append(f"| {r['target']} | {r['net']} | {r['host_zone']} | {cc['blocker'] or '-'} | "
                     f"{cc['n_members']} | {r['verdict']} | {r['chosen'] or '-'} |")
    lines += ["", "牙齿（直走廊对照须全 FAIL）：" + json.dumps(teeth, ensure_ascii=False),
              "", "本件零 SPEC/板改动；若 R1 全可行，其施加须另开 CO（含 B.Cu 桥声明退役）。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "rows": rows, "teeth": teeth,
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
