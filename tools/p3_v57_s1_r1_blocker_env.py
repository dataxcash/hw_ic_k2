#!/usr/bin/env python3
"""P3 v57 S1 — R1 芯片侧障碍环境派生（图纸生成器芯片出逃列域的第一步真数据）。

输入（单向只读）：DS320 ballmap（354 球局部几何，权威手册派生）+ S0 端点模型
（32 数据页 chip 锚 expect_xy / ball）+ 页清单（出逃侧 east|west）。

变换（S0 已实证，勿重推）：gx = cx + y_local；gy = cy - x_local（cx,cy=U6 中心）。
对每页每极：列出其球行/出逃侧方向上的邻球障碍（GND/异网信号/N-C/VCC，1.5mm 窗口
内），作为 R1 禁列 blocker 集的几何来源。零板文件读取、零窗口反猜（窗口仅锚球
邻域，非 x-window 取端）。
"""
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
BALLMAP = STEP2 / "ds320pr1601_ballmap.json"
EP = STEP2 / "m13_v57_s0_endpoint_model.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_s1_r1_blocker_env.json"

CX, CY = 93.8, 53.7
WIN = 1.5


def gpos(lx, ly):
    return round(CX + ly, 4), round(CY - lx, 4)


def main() -> int:
    bm = json.load(open(BALLMAP))["ballmap"]
    ep = json.load(open(EP))
    mf = json.load(open(MANIFEST))
    chip = {d["net"]: d for d in ep["details"]["chip"]
            if d.get("kind") != "pass_through"}
    balls_global = []
    for b in bm:
        gx, gy = gpos(b["x_mm"], b["y_mm"])
        balls_global.append({"signal": b.get("signal"), "name": b["name"],
                             "g": [gx, gy]})
    # 变换对拍：抽 4 个数据球 vs S0 expect_xy
    probe = {}
    for net in ("PCIE_DN0_N", "PCIE_DN0_P", "PCIE_DN6_N", "PCIE_UP_OUT0_N_J2"):
        d = chip.get(net)
        if not d:
            continue
        b = next(x for x in balls_global if x["signal"] == d["ball"])
        probe[net] = {"ball": d["ball"], "derived": b["g"],
                      "s0_expect": d["expect_xy"],
                      "match": all(abs(a - c) <= 0.05 for a, c in
                                   zip(b["g"], d["expect_xy"]))}
    assert all(p["match"] for p in probe.values()), probe

    fam = {}
    for pg in mf["pages"]:
        if pg["kind"] != "data":
            continue
        side = pg["side"]
        for pol in ("P", "N"):
            a = pg["anchors"]["chip"][pol]
            px, py = a["pad_global"]
            nbr = []
            for b in balls_global:
                if b["signal"] == a["ball"]:
                    continue
                dx, dy = b["g"][0] - px, b["g"][1] - py
                if abs(dx) <= WIN and abs(dy) <= WIN:
                    nbr.append({"sig": (b["signal"] or "?")[:12],
                                "dx": round(dx, 3), "dy": round(dy, 3)})
            fam.setdefault(pg["page_id"], {})[pol] = {
                "ball": a["ball"], "pad": a["pad_global"], "side": side,
                "neighbors": sorted(nbr, key=lambda n: (n["dx"] ** 2 +
                                                        n["dy"] ** 2))}
    out = {"artifact": "m13_v57_s1_r1_blocker_env",
           "basis": "ballmap×U6 放置(权威) + S0 chip 锚; 窗口=锚球 1.5mm 邻域",
           "inputs_sha": {"ballmap": hashlib.sha256(
               BALLMAP.read_bytes()).hexdigest()[:12],
               "ep": hashlib.sha256(EP.read_bytes()).hexdigest()[:12]},
           "transform_probe": probe, "pages": fam}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    # 摘要：每页出逃侧最近障碍类型/距离
    import collections
    for pid in sorted(fam):
        for pol, r in fam[pid].items():
            ns = r["neighbors"]
            gnd = [n for n in ns if n["sig"].startswith("GND")]
            near = min(ns, key=lambda n: n["dx"] ** 2 + n["dy"] ** 2) if ns else None
            print(f"{pid:26s} {pol} side={r['side']:4s} ball={r['ball']:9s} "
                  f"near={near['sig'] if near else '-':>12s} "
                  f"d={((near['dx']**2+near['dy']**2)**0.5):.2f} nbr={len(ns)}"
                  + (f" gnd_near={(min((n['dx']**2+n['dy']**2)**0.5 for n in gnd)):.2f}"
                     if gnd else ""))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
