#!/usr/bin/env python3
"""K2 · R330 · C-w **收益量测**（what-if · 只读）：若把窄颈处具名他网（C-w 候选）整体腾挪（铜+孔），
   ②-UP 之『单水平长走』模型候选是否出现？——**决策支持测量，非见证、非可行性主张**。
用法: python3 cw_whatif.py <model_l8.json> <out.json>
"""
import sys, json, math, importlib.util, hashlib
import numpy as np
V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
CW_NETS = {"DS320_STRAP_B_ADDR1_7-0", "DS320_STRAP_B_ADDR0_15-8", "PERSTA#", "I2C1_SDA"}
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
model = json.load(open(sys.argv[1])); OUT = sys.argv[2]
CELL, HW, P = 0.02, 0.08, 0.435
ad = {a["net"]: a for a in v3.lane_anchors(model)}
res = {}
for tag, extra in (("baseline", set()), ("post_Cw_if_relocated", CW_NETS)):
    v3.is_lane = lambda n, e=extra: n in LANES or n in e
    rast = v3.Raster(model["bbox"], CELL)
    bad = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
    NX, NY = rast.NX, rast.NY
    ab = np.zeros((NX, NY), bool); own = {}
    for n in LANES:
        a = ad[n]; mm = np.zeros((NX, NY), bool)
        v3.Raster.cir(rast, mm, a["A"][0], a["A"][1], P); v3.Raster.cir(rast, mm, a["B"][0], a["B"][1], P)
        own[n] = mm; ab |= mm
    I = lambda x: int(round((x - rast.X0) / CELL)); J = lambda y: int(round((y - rast.Y0) / CELL))
    cnt = {}
    for n in sorted(LANES, key=lambda k: ad[k]["A"][0]):
        a = ad[n]; ax, ay = a["A"]; bx, by = a["B"]
        allowed = (~bad) & (~(ab & ~own[n]))
        i0, i1 = sorted((I(ax), I(bx)))
        hor_ok = allowed[i0:i1 + 1, :].all(axis=0)
        c = 0
        for j in range(J(38.0), J(64.0) + 1):
            if not hor_ok[j]: continue
            ja, jb = sorted((J(ay), j))
            if not allowed[I(ax), ja:jb + 1].all(): continue
            jc, jd = sorted((J(by), j))
            if not allowed[I(bx), jc:jd + 1].all(): continue
            c += 1
        cnt[n[10:-3]] = c
    res[tag] = cnt
    print(tag, "zero-candidate lanes:", sum(1 for v in cnt.values() if v == 0), "/16")
z0 = sum(1 for v in res["baseline"].values() if v == 0); z1 = sum(1 for v in res["post_Cw_if_relocated"].values() if v == 0)
out = {"schema": 1, "artifact": "k2_r330_cw_benefit_whatif_v1", "to": "监理", "from": "ENG · ARCHER",
       "nature": "**C-w 收益量测（what-if · 只读）** —— 决策支持测量；**非见证 · 非可行性主张 · 非 C-w 申报**",
       "cw_candidate_nets": sorted(CW_NETS),
       "model": "R325/R326 之『单水平长走』(ax,ay)→(ax,y)→(bx,y)→(bx,by)；cell 0.02 · hw 0.08 · pitch 0.435 · 他锚孔排除 r=pitch",
       "note": "what-if = 假设该 4 网之 **In5 铜 + 孔** 整体腾挪（其端点/球位**不动**之可行性**未证**）",
       "zero_candidate_lanes": {"baseline": z0, "post_Cw_if_relocated": z1},
       "candidates_per_lane": res,
       "verdict": ("**C-w 收益显著**：单水平长走模型下零候选 lane 由 %d/16 降至 %d/16 ⇒ 具名 4 网之腾挪**足以**打开出带通道（在该模型内）。" % (z0, z1)) if z1 < z0 else
                  "**C-w 收益不足**：该 4 网腾挪后零候选 lane 仍 %d/16 ⇒ 尚需另寻（或他对象）。" % z1,
       "scope": "本件**不主张**可行性、**不申报** C-w（缺 `ref_plane_continuity` / 去向证明 / `buildability` / 端点不动证明 · 依宪法第十三条不作数）",
       "buildability_field": "不动任何对象（what-if 系**内存假设** · 未烙板 · 未改任何实体）⇒ 不动证明成立；不产出施工图。",
       "self_sha16": {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}}
t = json.dumps(out, indent=1, ensure_ascii=False)
out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(t.strip().encode()).hexdigest()[:16]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("[sha16 约定A]", out["self_sha16"]["convention_A_sha16"])
