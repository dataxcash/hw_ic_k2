#!/usr/bin/env python3
"""k2_placement_norms_v2.py --- #K2-343 sec.4 W1: NORM LIBRARY v2 (extended with the SAMPLE-DERIVED header policy).

Extends PLACEMENT_NORMS_v1 (N1..N7) with norms extracted from the in-register samples, each carrying its source
citation + an APPLICABILITY SCOPE declaration (#K2-343 sec.2.4) and a machine check.  Owner is not asked
(engineering autonomy); the samples are the legal authority.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L2 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", default=os.path.join(L2, "SAMPLE_RECORDS_v1.json"))
    ap.add_argument("--norms-v1", default=os.path.join(L2, "PLACEMENT_NORMS_v1.json"))
    ap.add_argument("--out", default=os.path.join(L2, "PLACEMENT_NORMS_v2.json"))
    a = ap.parse_args()
    S = json.load(open(a.samples, encoding="utf-8"))
    N1 = json.load(open(a.norms_v1, encoding="utf-8"))
    hist = S["cross_sample"]["per_sample_role_counts"]
    per = {t: sum(hist[t].values()) for t in hist}
    furn = {t: hist[t].get("CONFIG_FURNITURE", 0) for t in hist}
    frac = {t: round(100.0 * furn[t] / per[t], 1) for t in per}
    samples = [
        {"id": "N8", "rule": "排针政策：产品卡只携带 ①主机/产品高速接口 ②电源输入 ③至多一个生产编程口；"
                             "评估用配置排针/选择跳线/调试控制台**不得存在**（改测试点或删除）",
         "param": {"allowed_classes": ["HOST_EDGE/HS_PRODUCT_INTERFACE", "POWER_IN", "PROGRAMMING(<=1)"],
                   "forbidden_classes": ["CONFIG_FURNITURE (multi-position selectors, console/aux buses)"]},
         "source": {"kind": "SAMPLE_DERIVED (cross-sample inventory)", "citations": [
             {"sample": "SNLU300", "fact": "connector-like inventory %d, 其中 CONFIG_FURNITURE %d (%.1f%%)" % (per["SNLU300"], furn["SNLU300"], frac["SNLU300"])},
             {"sample": "SNLU301", "fact": "connector-like inventory %d, 其中 CONFIG_FURNITURE %d (%.1f%%)" % (per["SNLU301"], furn["SNLU301"], frac["SNLU301"])},
             {"sample": "SNLU273", "fact": "connector-like inventory %d, 其中 CONFIG_FURNITURE %d (%.1f%%)" % (per["SNLU273"], furn["SNLU273"], frac["SNLU273"])}],
             "derivation": "三样板**每一块**都带 13–20 个配置排针（占其连接器清单 48–59%）——因为样板是**评估板**；"
                           "⇒ 配置排针是评估家具，非产品必需。产品必需的交叉集 = {电源输入, 主机/产品高速接口}。"},
         "scope": "适用：**产品卡**的排针政策。样板是 EVM（评估板），其排针农场**不得**作为产品政策；"
                  "交叉集（每样板皆有）才是产品必需项。",
         "machine_check": "枚举板上连接器 → 分类 → 断言 CONFIG_FURNITURE 类 = 0（每项须有移除或改测试点的处置）"},
        {"id": "N9", "rule": "机械框架：安装孔四角（距角 ≤3.0mm）· 孔与其 6×6 禁区方框**原子同动**",
         "param": {"corner_max_mm": 3.0, "keepout_half_mm": 3.0},
         "source": {"kind": "SAMPLE_DERIVED + 规范", "citations": [
             {"sample": "SNLU300 Fig 4-1/4-2 (在册)", "fact": "四角安装孔"},
             {"sample": "在册缺陷 M-ENG-HOLE-KEEPOUT-STALE", "fact": "移动孔而禁区留守 = 静默缺陷（H2/H4 实测）"}]},
         "scope": "适用：机械框架（产品级）。样板层图给孔位政策；孔-禁区耦合为本板实测教训。",
         "machine_check": "四孔 corner_dist<=3.0 且 keepout 方框中心 == 孔位"},
        {"id": "N10", "rule": "密度/无农场：连接器不沿单边堆成配置列；左缘留给电源 + 产品接口",
         "param": {"max_same_edge_config_connectors": 0},
         "source": {"kind": "SAMPLE_DERIVED", "citations": [
             {"sample": "SNLU300/301/273", "fact": "评估板把配置排针沿边排成 2–3 列；产品卡应把接口按功能分区（N4）而非成列堆叠"}]},
         "scope": "适用：产品级分区/密度。评估板的成列堆叠是家具特征。",
         "machine_check": "同一板边同功能的排针列数 ≤1（非产品接口类为 0）"},
    ]
    rep = {"artifact": "k2_placement_norms_v2", "ts": "2026-09-28",
           "authority": "#K2-343 sec.4 W1 (sample learning pipeline) · supersedes PLACEMENT_NORMS_v1 as the library",
           "charter": "OWNER-CHARTER-v2-20260928 (sample autonomy): samples are the layout-policy authority; owner untouched",
           "inherited_norms": N1["norms"], "sample_derived_norms": samples,
           "sample_facts": {"per_sample_inventory_size": per, "config_furniture_counts": furn,
                            "config_furniture_fraction_pct": frac,
                            "records": "L2/SAMPLE_RECORDS_v1.json"},
           "next": "W2: header governance (J9 remove / J11 -> test points / J6 remove-or-testpoints; keep J2/J3/J4/J12/J13) "
                   "+ U1/U2/U4/U5 real re-placement (no rigid-translation proof) + H4 corner (C22 pour polygons) -> P1..P7",
           "OWNER-ITEMS": 0}
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "inherited": len(N1["norms"]), "sample_derived": [s["id"] for s in samples],
                      "config_furniture_fraction_pct": frac}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
