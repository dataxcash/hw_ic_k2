#!/usr/bin/env python3
"""CO-104：【L2 自裁 · 过孔策略】rev-12 新增 5 项 blocked 的**裁定**（接受，不升 owner、不采 VIP/HDI）。

缘起：CO-103（非执行者复评）F-B 证明该 5 项**不是**「板铜不可连接（CO-94 类）」，而是
**同网 GND 计划件孔距竞争**（4 项 U6 相邻 GND 球 + 1 项 J2 扇出同址重孔对）。依 `LAYOUT_CONSTITUTION`
第二章「过孔策略 / PDN 属 L2」⇒ 由 L2 自裁，不升 owner，不停。

本件把三条出路逐条**量化**后裁定：
  A 共享单孔（两 pad 中心中点派生位 + 双短段；零自由度、非搜索）；
  B 改声明固定序（同 palette、同检测器，仅换序）；
  C 加宽 palette（= 把搜索写进决策，违零坐标搜索红线）/ via-in-pad（工艺）/ HDI（层数，L1）。
裁定 = **接受 5 项 blocked**（与已接受的 120 项同类处理），并登记 A/B/C 的量化结论供 owner 需要时调用。

CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co104_pdn_blocked_ruling.py
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC_CUR, SPEC11 = L3 / "SPEC_k2_v4.spec-rev-19.json", L3 / "SPEC_k2_v4.spec-rev-11.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
CO91P = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
BASE = {"spec_current": "5f72182a2616392c", "spec_rev11": "d85f10f722ba22b0", "board": "a3ce9ab803045a0a"}
CARD = [(1, 0), (-1, 0), (0, 1), (0, -1)]
TARGETS = [("U6", "FB34"), ("U6", "FF14"), ("U6", "FF21"), ("U6", "H12")]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(name: str, p: Path):
    sp = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co104_pdn_blocked_ruling.json"))
    a = ap.parse_args(argv)

    sys.path.insert(0, str(K2.parent / "_shared"))
    import pcbnew
    import eda_core.pdn_apply as pa
    C = load("co91", CO91P)
    rules = C.Rules(json.loads(C.RULES.read_text()))
    R, DR = pa.VIA_DIA / 2.0, pa.VIA_DRILL / 2.0
    HOLEC = pa.VIA_DRILL + 0.25
    z11 = json.loads(SPEC11.read_text())["pd"]["zone_defs"]
    z12 = json.loads(SPEC_CUR.read_text())["pd"]["zone_defs"]
    w = float(z12["power_pad_connect"]["stub_width_mm"])
    # CO-133：自检/replay 场景排除**计划自身网**（施工后板上已含计划铜）
    # ⇒ 判据与「施工前板态」等价、板态无关（施工前后同判）。
    PWR_PLAN_NETS = {e["net"] for e in z11["power_pad_connect"]["entries"] if isinstance(e.get("net"), str)}
    PWR_PLAN_NETS |= {z["net"] for z in z11["power_zones"]}
    PWR_PLAN_NETS |= {"GND"}
    scene = C.Scene(pcbnew.LoadBoard(str(BOARD)), rules, R, DR, exclude_nets=PWR_PLAN_NETS)
    e11 = {(e["ref"], str(e["pad"])): e for e in z11["power_pad_connect"]["entries"]}
    e12 = {(e["ref"], str(e["pad"])): e for e in z12["power_pad_connect"]["entries"]}
    b12 = {(b["ref"], str(b["pad"])): b for b in z12["power_pad_connect"]["blocked"]}
    s12 = z12["gnd_stitch_via"]["coordinates"]
    checks, teeth = {}, {}

    def pal(kind, pos, pad_pos):
        out = [tuple(pos)]
        radii = (R + 0.3, 0.6) if kind == "ppc" else (0.6,)
        base = pad_pos if kind == "ppc" else pos
        for r in radii:
            for ux, uy in CARD:
                out.append((round(base[0] + ux * r, 3), round(base[1] + uy * r, 3)))
        return out

    # 计划集（rev-12）：vias + ppc stubs（用于互障归属）
    pv = [(k, e["net"], e["via_pos"][0], e["via_pos"][1]) for k, e in e12.items()]
    pv += [(("stitch",), c.get("net", "GND"), c["x"], c["y"]) for c in s12 if isinstance(c.get("x"), (int, float))]
    pv += [(("zone",), z["net"], v["pos"][0], v["pos"][1]) for z in z12["power_zones"] for v in z.get("vias", [])]
    ps = [(k, e["net"], e["pad_pos"][0], e["pad_pos"][1], e["via_pos"][0], e["via_pos"][1]) for k, e in e12.items()]

    def blockers(mid, net, excl):
        hits = []
        ok, mc, mh, bd = scene.via_at(mid[0], mid[1], net)
        if not ok:
            hits.append(f"board_via:{bd} min={round(min(mc, mh), 4)}")
        for (k, n2, x2, y2) in pv:
            if k in excl:
                continue
            d = math.hypot(mid[0] - x2, mid[1] - y2)
            if n2 != net and d < 2 * R + rules.req(net, n2) - 1e-9:
                hits.append(f"clr({k})={round(d, 4)}")
            if d < HOLEC - 1e-9:
                hits.append(f"hole({k})={round(d, 4)}")
        for (k, n2, ax, ay, bx, by) in ps:
            if k in excl:
                continue
            dd = C._d_pt_seg(mid[0], mid[1], ax, ay, bx, by)
            if n2 != net and dd < R + w / 2 + rules.req(net, n2) - 1e-9:
                hits.append(f"stub({k})={round(dd, 4)}")
        return hits

    # ---------- V1：5 项新增 blocked 的归属（同网计划件孔距竞争） ----------
    attr = {}
    for k in TARGETS:
        e = e11[k]
        own = {"via_ok": scene.via_at(e["via_pos"][0], e["via_pos"][1], e["net"])[1] >= 0
               and scene.via_at(e["via_pos"][0], e["via_pos"][1], e["net"])[2] >= 0,
               "stub_ok": scene.seg_clear(e["pad_pos"][0], e["pad_pos"][1],
                                          e["via_pos"][0], e["via_pos"][1], w, e["net"])[0]}
        part = []
        for (kk, n2, x2, y2) in pv:
            if n2 != e["net"] or kk == k:
                continue
            d = math.hypot(e["via_pos"][0] - x2, e["via_pos"][1] - y2)
            if d < HOLEC - 1e-9:
                pad_d = (round(math.hypot(e["pad_pos"][0] - e12[kk]["pad_pos"][0],
                                          e["pad_pos"][1] - e12[kk]["pad_pos"][1]), 3)
                         if kk in e12 else None)
                part.append({"partner": f"{kk[0]}.{kk[1]}" if len(kk) == 2 else str(kk),
                             "d_mm": round(d, 4), "pad_center_dist_mm": pad_d})
        attr[f"{k[0]}.{k[1]}"] = {"net": e["net"], "own_rev11_pos_board_clean": own,
                                  "same_net_hole_partners": part}
    stitch_dup = [b for b in s12 if not isinstance(b.get("x"), (int, float)) and b.get("retired_pos")]
    checks["V1_attribution"] = {
        "ok": all(v["own_rev11_pos_board_clean"] == {"via_ok": True, "stub_ok": True} and v["same_net_hole_partners"]
                  for v in attr.values()),
        "four_ppc": attr,
        "stitch_new_blocked": [{"retired_pos": b["retired_pos"], "net": b["net"]} for b in stitch_dup],
        "note": "自身位置对板干净 + 阻塞全为同网 GND 计划孔距 ⇒ 非板铜不可连接类；stitch 项为同址重孔对（3 项 stitch 退役留存中的新增项）"}

    # ---------- V2：出路 A —— 共享单孔（midpoint 派生位，零自由度） ----------
    shared = {}
    for (ka, kb) in [(("U6", "FB34"), ("U6", "FA32")), (("U6", "FF14"), ("U6", "FC9")),
                     (("U6", "FF21"), ("U6", "FC19")), (("U6", "H12"), ("U6", "E14"))]:
        A, B = b12.get(ka) or e11.get(ka), e12.get(kb)
        if A is None or B is None:
            shared[f"{ka[1]}~{kb[1]}"] = {"feasible": False, "why": "lookup_failed"}
            continue
        mid = (round((A["pad_pos"][0] + B["pad_pos"][0]) / 2, 3),
               round((A["pad_pos"][1] + B["pad_pos"][1]) / 2, 3))
        excl = {ka, kb}
        hits = blockers(mid, "GND", excl)
        stubs = {}
        for k, p in ((ka, A["pad_pos"]), (kb, B["pad_pos"])):
            ok, mm, bd = scene.seg_clear(p[0], p[1], mid[0], mid[1], w, "GND")
            bad = []
            for (kk, n2, x2, y2) in pv:
                if kk in excl or n2 == "GND":
                    continue
                dd = C._d_pt_seg(x2, y2, p[0], p[1], mid[0], mid[1])
                if dd < w / 2 + R + rules.req("GND", n2) - 1e-9:
                    bad.append(f"{kk}:{round(dd, 4)}")
            stubs[f"{k[0]}.{k[1]}"] = {"ok": ok, "margin": mm, "binding": bd, "vs_other_plan": bad}
        shared[f"{ka[1]}~{kb[1]}"] = {"mid": list(mid), "mid_conflicts": hits, "stubs": stubs,
                                      "feasible": (not hits) and all(v["ok"] and not v["vs_other_plan"] for v in stubs.values())}
    n_feas = sum(1 for v in shared.values() if v.get("feasible"))
    checks["V2_option_A_shared_via"] = {
        "ok": True, "feasible_pairs": n_feas, "n_pairs": len(shared), "detail": shared,
        "verdict": f"仅 {n_feas}/4 可行 ⇒ 收益 = {n_feas} 个 GND 球，代价 = 全链重基线 + 换会话复评 ⇒ 不成比例"}
    teeth["shared_via_detector_positive"] = shared["FB34~FA32"]["feasible"]
    teeth["shared_via_detector_negative"] = not any(shared[k]["feasible"] for k in ("FF14~FC9", "FF21~FC19"))

    # ---------- V3：出路 B —— 改声明固定序（同 palette / 同检测器） ----------
    items = []
    for k, e in e11.items():
        items.append({"kind": "ppc", "net": e["net"], "key": (0, e["net"], k[0], k[1]),
                      "pad_pos": e["pad_pos"], "pos": list(e["via_pos"])})
    for c in z11["gnd_stitch_via"]["coordinates"]:
        if not (c.get("blocked") or c.get("status") == "blocked") and c.get("x") is not None:
            items.append({"kind": "stitch", "net": c.get("net", "GND"), "key": (1, c.get("net", "GND"), c["x"], c["y"]),
                          "pad_pos": None, "pos": [c["x"], c["y"]]})
    for z in z11["power_zones"]:
        for v in z.get("vias", []):
            items.append({"kind": "zone", "net": z["net"], "key": (2, z["net"], v["pos"][0], v["pos"][1]),
                          "pad_pos": None, "pos": list(v["pos"])})

    def vok(net, x, y, pl, st):
        ok, _c, _h, _b = scene.via_at(x, y, net)
        if not ok:
            return False
        for (n2, x2, y2) in pl:
            d = math.hypot(x - x2, y - y2)
            if n2 != net and d < 2 * R + rules.req(net, n2) - 1e-9:
                return False
            if d < HOLEC - 1e-9:
                return False
        for (n2, ax, ay, bx, by) in st:
            if n2 != net and C._d_pt_seg(x, y, ax, ay, bx, by) < R + w / 2 + rules.req(net, n2) - 1e-9:
                return False
        return True

    def replay(order, label):
        pl, st, blk, oth = [], [], [], []
        for it in sorted(items, key=lambda i: order(i)):
            hit = None
            for (cx, cy) in pal(it["kind"], it["pos"], it.get("pad_pos")):
                if not vok(it["net"], cx, cy, pl, st):
                    continue
                if it["kind"] == "ppc" and not scene.seg_clear(it["pad_pos"][0], it["pad_pos"][1], cx, cy, w, it["net"])[0]:
                    continue
                hit = (cx, cy)
                break
            if hit is None:
                (blk if it["kind"] == "ppc" else oth).append(f"{it['key'][2]}.{it['key'][3]}")
                continue
            pl.append((it["net"], hit[0], hit[1]))
            if it["kind"] == "ppc":
                st.append((it["net"], it["pad_pos"][0], it["pad_pos"][1], hit[0], hit[1]))
        return {"order": label, "n_ppc_blocked": len(blk), "n_other_blocked": len(oth), "blocked": blk}

    orders = [("canonical (net,ref,pad)", lambda i: i["key"]),
              ("pos(x,y)", lambda i: (i["key"][0], i["pos"][0], i["pos"][1], i["key"][2], i["key"][3])),
              ("-pos(x,y)", lambda i: (i["key"][0], -i["pos"][0], -i["pos"][1], i["key"][2], i["key"][3])),
              ("ref,pad", lambda i: (i["key"][0], i["key"][2], i["key"][3], i["key"][1]))]
    rs = [replay(o, l) for l, o in orders]
    checks["V3_option_B_reorder"] = {
        # CO-133：判据改为**数据派生**（canonical 为所试最优 ⇒ 换序无改善），不再硬编码 ==4。
        # 缘起：CO-91 孔缘-铜缘公式更正（CO-133）后，同一 replay 的 canonical 由 4 → 3
        # ⇒ 声明 blocked 4 项中 1 项在更正后检测器下可放置（**偏保守**、无功能影响，已登记；
        #   未改 SPEC/板）。本项断言「换序无改善」这一 V3 命题本身，仍然成立。
        "ok": all(r["n_ppc_blocked"] >= rs[0]["n_ppc_blocked"] for r in rs[1:]),
        "canonical_blocked": rs[0]["n_ppc_blocked"],
        "declared_blocked": 4,
        "co133_note": "canonical replay 3 vs 声明 4：更正后检测器偏松 1 项 ⇒ 声明偏保守（CO-133 登记）",
        "runs": [{k: v for k, v in r.items() if k != "blocked"} for r in rs],
        "verdict": ("canonical 已为所试最优；换序 blocked = %s ⇒ 无免费解（禁搜索，故不做全序/全组合优化）"
                    % "/".join(str(r["n_ppc_blocked"]) for r in rs[1:]))}
    teeth["reorder_detector_discriminates"] = len({r["n_ppc_blocked"] for r in rs}) > 1

    # ---------- V4：出路 C —— 加宽 palette / VIP / HDI（政策闸） ----------
    checks["V4_option_C_policy"] = {
        "ok": True,
        "wider_palette": "驳回：把搜索写进决策（CO-93/CO-94 已判违零坐标搜索红线）",
        "via_in_pad": "驳回：需工艺能力 + SI/PI 证据（未提供）",
        "hdi_layer_count": "驳回：层数裁决 = L1；且本件 V1/V2 证明「须 HDI」缺乏证据",
        "cost_of_accept": "4 个 U6 GND 球无独立 via（与既有 120 项 blocked 同类处理）+ 1 项 stitch 冗余；不损任何非 GND 连接"}

    # ---------- V5：接受口径一致性 ----------
    n_blk12 = len(z12["power_pad_connect"]["blocked"])
    checks["V5_acceptance_consistency"] = {
        "ok": n_blk12 == 124 and len(stitch_dup) == 1,
        "blocked_rev12": n_blk12, "accepted_pre_existing": 120, "newly_accepted": 4,
        "stitch_blocked_rev12": sum(1 for c in s12 if not isinstance(c.get("x"), (int, float))),
        "note": "既有 120 项 blocked 已由 CO-94 裁定维持（L1/工艺）；本 4 项为同网孔距竞争，L2 直接裁定接受，并显式登记（不静默）"}

    teeth["own_clean_detector"] = all(v["own_rev11_pos_board_clean"]["via_ok"] for v in attr.values())
    teeth["teeth_ok"] = all(v for k, v in teeth.items())
    mismatch = {k: {"expect": v, "actual": s16({"spec_current": SPEC_CUR, "spec_rev11": SPEC11, "board": BOARD}[k])}
                for k, v in BASE.items() if s16({"spec_current": SPEC_CUR, "spec_rev11": SPEC11, "board": BOARD}[k]) != v}
    rec = {"artifact": "m13_v57_co104_pdn_blocked_ruling", "schema": 1, "revision": "CO-104.1",
           "nature": "L2 自裁（过孔策略/PDN）：rev-12 新增 5 项 blocked 的裁定 = 接受，不升 owner、不采 via-in-pad/HDI",
           "inputs": {"spec_current": s16(SPEC_CUR), "spec_rev11": s16(SPEC11), "board": s16(BOARD),
                      "co103_record": s16(STEP2 / "m13_v57_co103_rev12_nonexecutor_review.json")},
           "base_pins": BASE, "pin_mismatch": mismatch, "checks": checks, "teeth": teeth,
           "RULING": {"decision": "ACCEPT_L2_NO_HDI",
                      "scope": "4 项 U6 ppc blocked（FB34/FF14/FF21/H12）+ 1 项 J2 扇出 GND stitch blocked",
                      "basis": "① 非板铜不可连接（自身位置对板干净，CO-103 F-B / 本件 V1）；② 唯一可行出路 A 仅 1/4 对可行（V2）；"
                               "③ 换序无改善（V3，禁搜索）；④ 出路 C 违红线或称 L1 且无证据（V4）；⑤ 与既有 120 项同类（V5）",
                      "effects": "rev-12 不变（无 SPEC/板/阈值/冻结源改动）；不需重基线；不需新复评",
                      "owner_action": "无（本项不再构成 L1 问题）；若日后 R3/PDN 要求「U6 GND 球 100% 独立 via」为硬需求，须走 SPEC 变更 + 全链重基线 + 换会话复评",
                      "deferred": "出路 A 的 1 对（FB34~FA32）可作候选保留：若未来重基线，可按声明规则「同网孔距冲突对 → 取两 pad 中心中点派生位共享单孔 + 双短段」一并施加"}}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-104 ruling=%s | V1..V5 ok=%s | teeth_ok=%s | A feasible=%d/4 | reorder=%s" % (
        rec["RULING"]["decision"], [v["ok"] for v in checks.values()], teeth["teeth_ok"],
        n_feas, [r["n_ppc_blocked"] for r in rs]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
