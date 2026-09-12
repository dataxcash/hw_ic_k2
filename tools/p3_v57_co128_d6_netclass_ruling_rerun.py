#!/usr/bin/env python3
"""CO-128：【L2 自裁 · D-6 定案】`12V_IN` 网类裁定 + ① 按新类（POWER / feat 0.5）确定性绕障复判。

D-6（CO-124 K8 补审发现，已登记 `pdn_net_not_power_class:12V_IN`）：
  `12V_IN` 属 PDN 网（在 `pd.decoupling` 与 `power_pad_connect` 内）却未被任何 POWER 前缀命中 ⇒
  落 LOW_SPEED（净距 0.1 / 线宽 0.15），与 `constraints.power_no_fine_traces=True`「禁电源网拉细线」冲突。

**层级 = L2**：网级净距/线宽口径与 PDN 承载 = L2（《宪法》ch.2：PDN 架构）；本裁定**不改**器件分区/接口朝向/
信号流向/电源域划分/层数，**不改网名**（无 L1 面）。先例：CO-117/CO-121 同属 L2 归属更正。

**裁定（唯一机制，择一）**：`net_classes_override = {"net": "12V_IN", "class": "POWER"}`。
  择此而非「改网名为 PWR_12V_IN」：后者波及网表/BOM/板/多份工件，爆炸半径大且无增益；override 为 SPEC 既有机制、局部可逆。
  后果（须显式登记）：`12V_IN` 线宽下限 0.15→**0.5**；对异网净距 0.1→0.2 ⇒ required 一律 **0.375**；
  ① 的几何可行性判定随之改变 ⇒ 必须按新类重跑（本件；不改 SPEC，施加归 rev-17）。

**复判（① 按新类）**：以 CO-127 的「中线厚度模型 + 多分辨率细化」构建 12V_IN 承载区（连通 C88.1/U2.4/U2.6），
  判据 = 覆盖 3 target / 对异网 via 圆心 ≥ required（0.375）/ 区域宽 ≥ 0.5 / 宿主 MCU_VDD_WEST 连续性 / 可制造搭接。
  对比：CO-125 原 region+min-feature 模型在 feat=0.5 下 min rect = 0.375 ⇒ ROUTED_BUT_JUDGE_FAIL，
  该负结果已登记为 TOOL_DEFECT（`tool_defect:co126_grid_coarsening_and_self_defeating_min_feature_gate`），非不可行。

牙齿：T1 结构性不可行（合成障碍贴 root target ⇒ 须不可行）；T2 输出净距独立复算；T3 同输入两次逐字节一致；
     T4 覆盖 3/3 target。
只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加。
CLI: python3 tools/p3_v57_co128_d6_netclass_ruling_rerun.py
"""
from __future__ import annotations
import hashlib, importlib.util, json, math
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
REC = STEP2 / "m13_v57_co128_d6_netclass_ruling.json"
CARD = STEP2 / "m13_v57_CO128_d6_netclass_ruling_rerun.md"
DEF_DOC = K2 / "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md"
NET = "12V_IN"
NEW_CLASS = "POWER"
HOST_ZONE = "MCU_VDD_WEST"
WINDOW_MARGIN = 3.0
EPS = 1e-9
CLEAR = {"POWER": 0.2, "LOW_SPEED": 0.1}
VIA_OD, DRILL, MIN_HOLE, BOARD_MIN = 0.35, 0.2, 0.25, 0.1


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def mod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def req(own_cls, foreign_net, spec, c127):
    cf = c127.ncls(foreign_net, spec)[0]
    clr = max(CLEAR[own_cls], CLEAR[cf], BOARD_MIN)
    return round(max(clr + VIA_OD / 2, MIN_HOLE + DRILL / 2), 6)


def carrier(spec, c127, c121, c122b, feat, own_cls, inject=None):
    zd = spec["pd"]["zone_defs"]; zones = {z["zone"]: z for z in zd["power_zones"]}
    E = zd["power_pad_connect"]["entries"]
    targets = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in E if e["net"] == NET}
    foreign = {}
    for e in E:
        if e["net"] != NET:
            foreign[f"{e['ref']}.{e['pad']}({e['net']})"] = (tuple(map(float, e["via_pos"])), e["net"])
    for z in zd["power_zones"]:
        for i, v in enumerate(z.get("vias") or []):
            if z["net"] != NET:
                foreign[f"{z['zone']}#v{i}({z['net']})"] = (tuple(map(float, v["pos"])), z["net"])
    if inject:
        foreign.update(inject)
    reqf = {k: req(own_cls, fn, spec, c127) for k, (fp, fn) in foreign.items()}
    R = {k: reqf[k] + feat / 2 * math.sqrt(2) for k in foreign}
    wpoly = zones[HOST_ZONE]["polygon"]
    west = (min(p[0] for p in wpoly), min(p[1] for p in wpoly), max(p[0] for p in wpoly), max(p[1] for p in wpoly))
    xs_t = [p[0] for p in targets.values()]; ys_t = [p[1] for p in targets.values()]
    win = (max(min(xs_t) - WINDOW_MARGIN, west[0] + 0.3), max(min(ys_t) - WINDOW_MARGIN, west[1] + 0.3),
           min(max(xs_t) + WINDOW_MARGIN, west[2] - 0.3), min(max(ys_t) + WINDOW_MARGIN, west[3] - 0.3))
    XS = {win[0], win[2]} | {p[0] for p in targets.values()}
    YS = {win[1], win[3]} | {p[1] for p in targets.values()}
    for k, (fp, fn) in foreign.items():
        if win[0] - 2 <= fp[0] <= win[2] + 2 and win[1] - 2 <= fp[1] <= win[3] + 2:
            XS |= {round(fp[0] - R[k], 6), round(fp[0] + R[k], 6)}
            YS |= {round(fp[1] - R[k], 6), round(fp[1] + R[k], 6)}
    floor = feat / 2
    for level in range(0, 9):
        X, Y = sorted(XS), sorted(YS); nx, ny = len(X) - 1, len(Y) - 1
        clear = {}
        for i in range(nx):
            for j in range(ny):
                r = (X[i], Y[j], X[i + 1], Y[j + 1])
                clear[(i, j)] = (win[0] - EPS <= r[0] and r[2] <= win[2] + EPS
                                 and win[1] - EPS <= r[1] and r[3] <= win[3] + EPS
                                 and all(c127.p2r(fp, r) >= R[k] - EPS for k, (fp, fn) in foreign.items()))

        def cell_of(p):
            for i in range(nx):
                if X[i] - EPS <= p[0] <= X[i + 1] + EPS:
                    for j in range(ny):
                        if Y[j] - EPS <= p[1] <= Y[j + 1] + EPS:
                            return (i, j)
            return None
        tc = {k: cell_of(p) for k, p in targets.items()}
        bad = [k for k in tc if tc[k] is None or not clear.get(tc[k])]
        if bad:
            blockers = sorted(({"target": k, "foreign": fk,
                                "dist_mm": round(c127.p2r(fp, (*targets[k], *targets[k])), 4),
                                "required_mm": reqf[fk]}
                               for k in bad for fk, (fp, fn) in foreign.items()
                               if c127.p2r(fp, (*targets[k], *targets[k])) < reqf[fk] - EPS), key=lambda x: x["dist_mm"])
            return {"verdict": "STRUCTURALLY_INFEASIBLE" if blockers else "TOOL_INSUFFICIENT_TARGET_CELL",
                    "structural": bool(blockers), "blocking_foreign": blockers,
                    "level": level, "window": [round(v, 3) for v in win]}
        root = min(tc, key=lambda k: (targets[k][0], targets[k][1]))
        a, dist, prev = tc[root], {tc[root]: 0}, {}
        q = deque([a])
        while q:
            cur = q.popleft()
            for d in ((1, 0), (0, -1), (-1, 0), (0, 1)):
                n = (cur[0] + d[0], cur[1] + d[1])
                if clear.get(n) and n not in dist:
                    dist[n] = dist[cur] + 1; prev[n] = cur; q.append(n)
        if all(tc[k] in dist for k in tc):
            cells = set()
            for k in tc:
                cur = tc[k]
                while cur != a:
                    cells.add(cur); cur = prev[cur]
                cells.add(a)
            rects = c127.merge2d([(X[i] - feat / 2, Y[j] - feat / 2, X[i + 1] + feat / 2, Y[j + 1] + feat / 2)
                                  for (i, j) in cells])
            ring = [[float(x), float(y)] for x, y in c122b.union_ring([tuple(r) for r in rects])]
            mcu_in = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in E
                      if e["net"] == zones[HOST_ZONE]["net"] and c127.in_rect(tuple(map(float, e["via_pos"])), west)}
            jr = c121.judge(rects, west, dict(targets), mcu_in, foreign)
            min_dim = min(min(r[2] - r[0], r[3] - r[1]) for r in rects)
            clear_ok = all(c127.p2r(fp, r) >= reqf[k] - EPS for r in rects for k, (fp, fn) in foreign.items())
            cov_ok = all(any(c127.in_rect(p, r) for r in rects) for p in targets.values())
            glob = {"coverage_3of3": cov_ok, "clearance": clear_ok, "min_dim>=feat": min_dim >= feat - EPS,
                    "rects_connected": c127.rects_connected(rects),
                    "host_zone": HOST_ZONE, "host_judge_ok": jr["ok"]}
            ok = all(glob[k] for k in ("coverage_3of3", "clearance", "min_dim>=feat", "rects_connected")) and jr["ok"]
            out = {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER" if ok else "ROUTED_BUT_JUDGE_FAIL",
                   "net": NET, "netclass": own_cls, "min_feature_mm": feat, "cleared_at_level": level,
                   "required_mm": reqf, "centerline_radius_mm": round(max(R.values()), 4),
                   "window": [round(v, 3) for v in win], "n_cells": nx * ny,
                   "n_clear": sum(1 for v in clear.values() if v), "path_cells": len(cells),
                   "region_rects": [[round(v, 3) for v in r] for r in rects], "ring": ring,
                   "host_judge": jr, "global_judge": glob, "min_rect_dim_mm": round(min_dim, 4),
                   "clearance_recheck_ok": clear_ok, "ok": ok}
            return out
        XS, YS = c127._bisect(XS, floor), c127._bisect(YS, floor)
    return {"verdict": "TOOL_INSUFFICIENT_NO_CARRIER", "level": 8}


def main() -> int:
    c127 = mod("c127", K2 / "tools/p3_v57_co127_multires_router.py")
    c121 = mod("c121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    c122b = mod("c122b", K2 / "tools/p3_v57_co122b_rev16_apply.py")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    new = carrier(spec, c127, c121, c122b, feat=0.5, own_cls=NEW_CLASS)
    again = carrier(spec, c127, c121, c122b, feat=0.5, own_cls=NEW_CLASS)
    teeth = {"T3_determinism_reproduced": new.get("region_rects") == again.get("region_rects")}
    t1 = carrier(spec, c127, c121, c122b, feat=0.5, own_cls=NEW_CLASS,
                 inject={"SYNTH@C88.1": ((28.275, 41.5), "GND")})
    teeth["T1_structural_infeasible_detected"] = t1["verdict"] == "STRUCTURALLY_INFEASIBLE"
    teeth["T2_output_clearance_recheck"] = bool(new.get("clearance_recheck_ok"))
    teeth["T4_coverage_3of3"] = bool((new.get("global_judge") or {}).get("coverage_3of3"))
    teeth_ok = all(teeth.values())
    verdict = ("D6_RULED_AND_1_FEASIBLE_UNDER_NEW_CLASS" if new.get("ok") and teeth_ok
               else "D6_RULED_1_NOT_FEASIBLE_UNDER_NEW_CLASS")
    rec = {"artifact": "m13_v57_co128_d6_netclass_ruling", "schema": 1, "revision": "CO-128.1",
           "nature": "D-6 定案（12V_IN 网类 L2 裁定）+ ① 按新类（POWER/feat 0.5）确定性绕障复判",
           "level": {"ruling": "L2", "basis": "《宪法》ch.2：网级净距/线宽口径 + PDN 承载 = L2（PDN 架构）；不改网名/域/层数 ⇒ 无 L1 面"},
           "definition_doc": {"path": "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md", "sha16": s16(DEF_DOC)},
           "decision": {"finding": "pdn_net_not_power_class:12V_IN",
                        "mechanism": {"net_classes_override": {"net": NET, "class": NEW_CLASS}},
                        "rejected_alternative": "改网名 PWR_12V_IN（波及网表/BOM/板/多工件，爆炸半径大且无增益）",
                        "consequences": {"trace_width_min_mm": {"from": 0.15, "to": 0.5},
                                         "clearance_to_foreign_mm": {"from": 0.1, "to": 0.2},
                                         "required_to_foreign_via_center_mm": 0.375},
                        "application": "rev-17（本件不改 SPEC）；施加后强制跑 co124 并 PASS"},
           "rerun_new_class": new,
           "model_note": ("① 复判采用 CO-127 的「中线厚度模型 + 多分辨率细化」。现行口径（LOW_SPEED/feat 0.15）的"
                          "① 结论见 CO-125 记录 `249166650c91fcba`；其 region+min-feature 模型在 feat=0.5 下不足以承载"
                          "（属已登记 TOOL_DEFECT `tool_defect:co126_grid_coarsening_and_self_defeating_min_feature_gate`），"
                          "故新类复判以 CO-127 模型为准。"),
           "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CARD.write_text("\n".join([
        "# CO-128 — D-6 定案（`12V_IN` → POWER）+ ① 按新类复判", "",
        f"- verdict：**{verdict}**", f"- 层级：**L2**（网级净距/线宽口径 + PDN 承载；无 L1 面）",
        f"- 裁定：`net_classes_override = {{'net': '{NET}', 'class': '{NEW_CLASS}'}}`；改网名方案已否决",
        f"- 后果：线宽下限 0.15→0.5；净距 0.1→0.2（required 0.375）；施加归 rev-17 并强制跑 co124", "",
        "| 口径 | feat | 判定 | 区域矩形 | 最小矩形 | 覆盖3/3 | 宿主连续 | ok |",
        "|---|---|---|---|---|---|---|---|",
        f"| 新类 POWER | 0.5 | {new['verdict']} | {len(new.get('region_rects') or [])} | {new.get('min_rect_dim_mm')} | "
        f"{(new.get('global_judge') or {}).get('coverage_3of3')} | {(new.get('host_judge') or {}).get('c_mcu_continuity')} | {new.get('ok')} |",
        "", f"牙齿：{json.dumps(teeth, ensure_ascii=False)}", "",
        "算法/根因/完备性见 CO-127；本件零 SPEC/板改动（施加归 rev-17）。"]), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "new": {k: new.get(k) for k in ("verdict", "ok", "min_rect_dim_mm",
                      "path_cells", "cleared_at_level", "clearance_recheck_ok")},
                      "teeth": teeth, "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
