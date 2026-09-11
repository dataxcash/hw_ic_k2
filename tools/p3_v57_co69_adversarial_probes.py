#!/usr/bin/env python3
"""CO-69 对抗评审：对方案(a) 全链执行的**独立证伪探针**（单独重算，不复用引擎/记录断言）。

执行者侧对抗（executor adversarial）：逐条**尝试证伪**关键声明；任一探针失败即对抗评审 FAIL。
（注：项目另有「非执行者双路对抗评审」外部闸；本件是其机器可判前置，不替代外部评审。）

探针：
 A1 不变量：SPEC rev-4 vs rev-5 的层数/平面数/平面网多重集（电源域划分）一致。
 A2 阈值不变：rev-4 -> rev-5 仅加性（递归比较 net_classes/impedance 数值、vias、constraints、corridors 数值）。
 A3 闭合：SPEC rev-5 dielectric_8l + 铜厚 == 1.6000mm。
 A4 阻抗：由 SPEC rev-5 per_layer 独立重算交付对内中心 {0.5,0.6} 之 Zdiff ∈ 85±10%。
 A5 引擎：引擎源码无 `In6.Cu` 字面量；LAYER_PALETTE == [F,In2,In5,B]。
 A6 板：L4 板逐 track 的宽度 == SPEC rev-5 width_mm_by_layer（需 pcbnew）。
 A7 冻结：四冻结源 sha 未变。
 A8 等长：由 L4 construction（非图纸）独立重算按层加权电气 skew，须 == SI 记录 max。
 A9 DFM：DFM 记录 new_total==0 且 disappeared_total==0。
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co69_adversarial_review.json"
SPEC4 = L3 / "SPEC_k2_v4.spec-rev-4.json"
SPEC5 = L3 / "SPEC_k2_v4.spec-rev-7.json"
FROZEN = {"SPEC_k2_v4.json": (L3 / "SPEC_k2_v4.json", "0bd52ed48e720b8c"),
          "page_manifest": (STEP2 / "m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
          "k2_v4_8L.kicad_pcb": (K2 / "k2_v4_8L.kicad_pcb", "fb07d25ac426ff84"),
          "drc_rules.json": (ROOT / "_shared/eda_core/drc_rules.json", "0a459839e15960b8")}


def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def plane_net(s):
    s = s.lower()
    if "gnd_plane" in s:
        return "GND"
    if "power_plane" in s:
        import re
        m = re.search(r"power_plane\(([^,)]+)", s)
        return m.group(1).strip() if m else "PWR"
    return None


def main() -> int:
    from collections import Counter
    s4 = json.loads(SPEC4.read_text(encoding="utf-8"))
    s5 = json.loads(SPEC5.read_text(encoding="utf-8"))
    probes = []

    def add(pid, desc, ok, detail):
        probes.append({"id": pid, "desc": desc, "pass": bool(ok), "detail": detail})

    # A1 invariants: 用**权威** LID REV5 vs REV6（rev-4 SPEC 的 stackup.Cu 键为历史 6L 残留，见 CO-53/54）
    lid5 = json.loads((STEP2 / "m13_v57_layer_intent_rev5.json").read_text(encoding="utf-8"))["layer_intent"]
    lid6 = json.loads((STEP2 / "m13_v57_layer_intent_rev6.json").read_text(encoding="utf-8"))["layer_intent"]

    def tax(intent):
        pn = {k: plane_net(v) for k, v in intent.items() if plane_net(v)}
        return {"layers": len(intent), "planes": len(pn), "nets": dict(Counter(pn.values()))}
    t4, t5 = tax(lid5), tax(lid6)
    add("A1", "layer/plane/domain invariance LID REV5 -> REV6",
        t4["layers"] == t5["layers"] and t4["planes"] == t5["planes"] and t4["nets"] == t5["nets"],
        {"rev5": t4, "rev6": t5})

    # A2 additive-only on numeric thresholds
    def nums(o, pre=""):
        out = {}
        if isinstance(o, dict):
            for k, v in o.items():
                if k.startswith("_"):
                    continue
                out.update(nums(v, pre + "/" + str(k)))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                out.update(nums(v, pre + "[%d]" % i))
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            out[pre] = float(o)
        return out
    n4 = {k: v for k, v in nums({**s4["net_classes"], "impedance": s4["impedance"], "vias": s4["vias"],
                                 "constraints": s4["constraints"], "corridors": s4["corridors"]}).items()}
    n5 = {k: v for k, v in nums({**s5["net_classes"], "impedance": s5["impedance"], "vias": s5["vias"],
                                 "constraints": s5["constraints"], "corridors": s5["corridors"]}).items()}
    # 排除**被 L2 授权变更的几何**（impedance.per_layer 线宽/介质）；其余数值（含全部阈值）不得漂移
    common = sorted(k for k in (set(n4) & set(n5)) if "/impedance/per_layer" not in k)
    drift = {k: [n4[k], n5[k]] for k in common if n4[k] != n5[k]}
    thr = {"intra_pair_skew_mm": (s4["net_classes"]["PCIe85"]["intra_pair_skew_mm"],
                                  s5["net_classes"]["PCIe85"]["intra_pair_skew_mm"]),
           "p_gap": (s4["net_classes"]["PCIe85"]["diff_pair"]["p_gap"], s5["net_classes"]["PCIe85"]["diff_pair"]["p_gap"]),
           "inter_pair_spacing_mm": (s4["net_classes"]["PCIe85"]["inter_pair_spacing_mm"],
                                     s5["net_classes"]["PCIe85"]["inter_pair_spacing_mm"])}
    thr_ok = all(a == b for a, b in thr.values())
    add("A2", "rev4->rev5: no numeric threshold changed (excl. L2-mandated impedance.per_layer geometry)",
        (not drift) and thr_ok, {"common_numeric_keys_checked": len(common), "drift": drift, "thresholds": thr})

    # A3 closure
    cu = 2 * 0.035 + 6 * 0.0175
    dz = sum(v["mm"] for k, v in s5["stackup"]["dielectric_8l"].items())
    add("A3", "dielectric+copper = 1.6000mm", abs(cu + dz - 1.6) <= 0.005,
        {"copper": round(cu, 4), "dielectric": round(dz, 4), "total": round(cu + dz, 4)})

    # A4 Zdiff
    sys.path.insert(0, str(ROOT / "_shared"))
    from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL
    pl = s5["impedance"]["per_layer"]
    zbad = {}
    for lyr, m in pl.items():
        for c in (0.5, 0.6):
            s = c - float(m["w_mm"])
            t = 0.035 if lyr in ("F.Cu", "B.Cu") else 0.0175
            var = float(m["h_mm"]) if "microstrip" in m["kind"] else float(m["b_mm"])
            z = MS(float(m["w_mm"]), var, t, float(m["er"]), s) if "microstrip" in m["kind"] else \
                SL(float(m["w_mm"]), var, t, float(m["er"]), s)
            if abs(z - 85.0) > 8.5:
                zbad[f"{lyr}@{c}"] = round(z, 2)
    add("A4", "per-layer Zdiff in 85+-10% at delivered pair centers {0.5,0.6}", not zbad,
        {"bad": zbad, "widths": s5["impedance"]["width_mm_by_layer"]})

    # A5 engine（CO-76 加固：原断言只查**带引号**字面量 `"In6.Cu"`，无法发现
    #   未加引号的层角色文本（如 emitted `up=In6.Cu`）与陈旧注释；改为裸 token 扫描 + 显式豁免）
    eng = (K2 / "tools/p3_v57_w3_constructive.py").read_text(encoding="utf-8")
    _in6_lines = [(i + 1, ln.strip()) for i, ln in enumerate(eng.splitlines()) if "In6" in ln]
    _in6_unallowed = [(i, ln) for i, ln in _in6_lines if "In6->In5" not in ln]
    _palette_ok = 'LAYER_PALETTE = ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"]' in eng
    add("A5", "engine: palette = F/In2/In5/B；无 In6 层角色文本（裸 token 扫描，豁免 In6->In5 迁移注）",
        _palette_ok and not _in6_unallowed,
        {"palette_ok": _palette_ok, "in6_quoted_literal": eng.count('"In6.Cu"'),
         "in6_bare_lines": len(_in6_lines), "in6_unallowed": _in6_unallowed})

    # A6 board widths (needs pcbnew)
    try:
        import pcbnew
        b = pcbnew.LoadBoard(str(K2 / "k2_v4_8L.l4.kicad_pcb"))
        wmap = s5["impedance"]["width_mm_by_layer"]
        bad = {}
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or not t.GetNetname().startswith("PCIE"):
                continue
            L = b.GetLayerName(t.GetLayer())
            exp = wmap.get(L)
            if exp is not None and abs(pcbnew.ToMM(t.GetWidth()) - exp) > 1e-6:
                bad[L] = bad.get(L, 0) + 1
        add("A6", "L4 board PCIE track width == SPEC width_mm_by_layer", not bad, {"mismatch": bad})
    except ImportError:
        add("A6", "L4 board width (pcbnew unavailable -> run under AppDir python)", False, {"skipped": True})

    # A7 frozen
    fr = {k: {"sha16": s16(v), "match": s16(v) == e} for k, (v, e) in FROZEN.items()}
    add("A7", "four frozen sources 4/4 MATCH", all(v["match"] for v in fr.values()), fr)

    # A8 independent electrical skew from L4 construction
    rec = json.loads((STEP2 / "m13_v57_l4_construction.json").read_text(encoding="utf-8"))
    si = json.loads((STEP2 / "m13_v57_l5_si_pi_emc_record.json").read_text(encoding="utf-8"))
    man = json.loads((STEP2 / "m13_v57_s1_page_manifest.json").read_text(encoding="utf-8"))
    mp = {p["page_id"]: p for p in man["pages"]}
    art = json.loads((STEP2 / "m13_v57_w3_joint_assignment.json").read_text(encoding="utf-8"))

    def sqer(lyr):
        m = pl.get(lyr)
        if not m:
            return 2.0
        if "stripline" in m["kind"]:
            e = float(m["er"])
        else:
            w, h, er = float(m["w_mm"]), float(m["h_mm"]), float(m["er"])
            e = (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 * h / w)
        return math.sqrt(e)

    def tlen(net):
        t = 0.0
        for s in rec["segments"].get(net, []):
            d = math.hypot(s["b"][0] - s["a"][0], s["b"][1] - s["a"][1])
            t += d * sqer(s["layer"]) / 299.792458
        return t
    worst = 0.0
    for pg in art["pages"]:
        if pg["kind"] == "data":
            nets = mp[pg["page_id"]]["nets"]
        elif pg["kind"] == "refclk":
            nets = pg["refclk"]["nets"]
        else:
            continue
        d = abs(tlen(nets["P"]) - tlen(nets["N"]))
        worst = max(worst, d * 299.792458 / math.sqrt(3.99))
    add("A8", "independent electrical skew (from L4 construction) == SI record max",
        abs(round(worst, 4) - si["SI"]["max_intra_pair_skew_mm"]) < 1e-6,
        {"recomputed": round(worst, 4), "si_record": si["SI"]["max_intra_pair_skew_mm"]})

    # A9 DFM
    dfm = json.loads((STEP2 / "m13_v57_l5_dfm_dft_record.json").read_text(encoding="utf-8"))
    add("A9", "DFM new_total=0 and disappeared_total=0",
        dfm["drc"]["new_total"] == 0 and dfm["drc"]["disappeared_total"] == 0,
        {"new_total": dfm["drc"]["new_total"], "disappeared_total": dfm["drc"]["disappeared_total"]})

    verdict = "PASS" if all(p["pass"] for p in probes) else "FAIL"
    res = {"artifact": "m13_v57_co69_adversarial_review", "schema": 1, "revision": "CO-69-AR.1",
           "nature": "执行者侧对抗证伪探针（独立重算；不替代项目「非执行者双路对抗评审」外部闸）",
           "verdict": verdict, "probes": probes,
           "failed": [p["id"] for p in probes if not p["pass"]],
           "note": ("L2_STRUCTURE_v2.0.md:137 要求重开层须重新过对抗评审；本件给出机器可判前置证据，"
                    "外部（非执行者）双路评审仍为独立闸，须由 non-executor 完成方可宣称「评审闭合」。")}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "failed": res["failed"],
                      "sha16": s16(OUT), "probes": {p["id"]: p["pass"] for p in probes}}, ensure_ascii=False))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
