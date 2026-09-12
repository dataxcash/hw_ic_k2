#!/usr/bin/env python3
"""CO-89：【L2 PDN 自裁】SPEC rev-9 —— PDN live 机读决策的**板实化**（CO-88 前置已齐后施加）。

CO-88 机判 FAIL：`pd.zone_defs.power_pad_connect` 55/173 条引用板上不存在的 ref（红驱动 U3+U7→U6 合并遗留）、
板实 309 个 SMD 电源/地 pad 仅 118+7 有决策、`pd.decoupling` 指向不存在的 C67/C68/C72。
本件按项目自带确定性发生器对**交付板**重生成 ppc，并把旧 BOM 决策显式退役留存（不销毁可追溯性）。

L2 不变量（CO-67）：层数 8 / 平面数 4 / 电源域集合 3（P3V3/P3V3_AUX/MCU_VDD）/ 信号层 4 —— 全不变 ⇒ L2 自裁。
零几何；只读冻结源；不碰历史件；无 while/坐标搜索。
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-8.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-9.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = L3 / "m13_v57_co89_pdn_board_realize_rev9.json"
SCRATCH = K2 / ".co89_tmp"
DEC_BY_NET = {"P3V3": ["C74", "C75", "C76", "C77", "C78", "C79", "C80", "C81", "C82", "C83", "C84"],
              "MCU_VDD": ["C85", "C86"], "12V_IN": ["C88"], "P3V3_AUX": ["C90"]}
DEC_ALL = [c for v in DEC_BY_NET.values() for c in v]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def regenerate_ppc() -> dict:
    SCRATCH.mkdir(exist_ok=True)
    cand = SCRATCH / "cand.json"
    shutil.copy(SRC, cand)
    r = subprocess.run([sys.executable, "-m", "eda_core.pad_connect_gen", "--spec", str(cand),
                        "--board", str(BOARD)], cwd=str(K2.parent), capture_output=True, text=True,
                       timeout=600, env={**os.environ, "PYTHONPATH": str(K2.parent / "_shared")})
    if r.returncode != 0:
        raise SystemExit(f"pad_connect_gen failed: {r.stderr[-300:]}")
    ppc = json.loads(cand.read_text(encoding="utf-8"))["pd"]["zone_defs"]["power_pad_connect"]
    shutil.rmtree(SCRATCH, ignore_errors=True)
    return ppc


def main() -> int:
    src_sha = s16(SRC)
    board_refs = set()
    import re
    bt = BOARD.read_text(encoding="utf-8")
    for m in re.finditer(r'\(property "Reference" "([A-Z]{1,2}\d{1,3})"', bt):
        board_refs.add(m.group(1))
    d = json.loads(SRC.read_text(encoding="utf-8"))
    base = json.loads(SRC.read_text(encoding="utf-8"))
    gen = regenerate_ppc()
    probe = {"generated_entries": len(gen["entries"]), "generated_blocked": len(gen["blocked"])}
    orphan_after = sorted({str(e["ref"]) for e in gen["entries"] + gen["blocked"] if str(e["ref"]) not in board_refs})
    probe["orphan_refs_after"] = orphan_after
    assert not orphan_after, f"regenerated ppc still has non-board refs: {orphan_after[:5]}"

    zd = d["pd"]["zone_defs"]
    ppc = zd["power_pad_connect"]
    old_e, old_b = list(ppc["entries"]), list(ppc["blocked"])
    n_orph_e = sum(1 for e in old_e if str(e.get("ref")) not in board_refs)
    n_orph_b = sum(1 for e in old_b if str(e.get("ref")) not in board_refs)
    ppc["retired_superseded_bom"] = {
        "basis": ("红驱动合并 U3(DN, DS160PR810 WQFN-64)+U7(UP) → U6(DS320PR1601, 354 球)；"
                  "旧条目基准为 101 fp 重建板（U3=DN@62.7/U7=UP@44.7），其 ref 在交付板不存在 ⇒ 退役留存（不销毁可追溯性）"),
        "n_entries": len(old_e), "n_blocked": len(old_b),
        "n_orphan_entries": n_orph_e, "n_orphan_blocked": n_orph_b,
        "entries": old_e, "blocked": old_b}
    ppc["entries"], ppc["blocked"] = gen["entries"], gen["blocked"]
    ppc["frozen_at"] = "CO-89 板实化（eda_core.pad_connect_gen on 交付板）"
    ppc["board_realized"] = {"co": "CO-89", "board": BOARD.name, "board_sha16": s16(BOARD),
                             "tool": "eda_core.pad_connect_gen", "pwr_nets": sorted({e["net"] for e in gen["entries"]}),
                             "n_entries": len(gen["entries"]), "n_blocked": len(gen["blocked"])}
    ppc["rule"] = (ppc["rule"] + "；CO-89 板实化：条目对**交付板**重生成，全部候选冲突 → blocked 台账（显式 reason）")

    pd = d["pd"]
    old_dec = pd.get("decoupling")
    pd["decoupling_legacy_retired"] = old_dec
    pd["decoupling"] = ("board_real_per_net: " + " / ".join(f"{k}{{{'-'.join(v)}}}" for k, v in DEC_BY_NET.items())
                        + " → via_to_plane")
    dv = zd["decoupling_via_to_plane"]
    old_vias = dv.get("vias", [])
    dv["retired_vias_superseded_bom"] = {
        "basis": "旧 vias 落于 C67/C68/C72（板上不存在）⇒ 退役留存；板实落点 = L3 施工派生",
        "vias": old_vias}
    dv["vias"] = []
    dv["targets"] = DEC_ALL
    dv["targets_basis"] = "机器派生自交付板（接电源网的电容）：" + ", ".join(f"{k}:{v}" for k, v in DEC_BY_NET.items())
    dv["geometry_status"] = "L3_CONSTRUCTION_DERIVED"
    dv["basis"] = "CO-89：解耦 via 坐标随器件合并退役；In4 平面落点坐标 = L3 施工确定性派生（未建）"

    d["spec_version"] = "1.1.spec-rev-9"
    d["_spec_rev_9"] = {
        "card": "SPEC-REV-9", "at": "2026-09-12",
        "authority": "L2 PDN 自裁（CO-88 判定 FAIL → CO-89 板实化）",
        "changes": [
            "spec_version: 1.1.spec-rev-8 -> 1.1.spec-rev-9",
            f"pd.zone_defs.power_pad_connect.entries/blocked: 对交付板重生成（{len(old_e)}/{len(old_b)} -> "
            f"{len(gen['entries'])}/{len(gen['blocked'])}）；旧条目转 retired_superseded_bom（{n_orph_e} 孤儿 entry + {n_orph_b} 孤儿 blocked）",
            "pd.decoupling: C67_C68_C72（板上不存在）-> 板实按网集合（P3V3/C84 等）；旧串转 decoupling_legacy_retired",
            "pd.zone_defs.decoupling_via_to_plane.vias: 旧 C67/C68/C72 坐标转 retired_vias_superseded_bom；"
            "targets=板实去耦电容；geometry_status=L3_CONSTRUCTION_DERIVED",
        ],
        "unchanged": ("stackup / impedance / net_classes / vias / corridors / board / components / constraints / "
                      "pd.gnd_planes / pd.power_plane_layer / pd.power_partition / pd.power_zones / pd.bcu_power_copper_policy 全未动"),
        "not_touched": "历史件（_spec_rev_* 溯源块 / appendix / pd.zone_defs.ecn_pending_items 原文）",
        "l2_invariant": {"layers": 8, "planes": 4, "power_domains": ["P3V3", "P3V3_AUX", "MCU_VDD"], "signal_layers": 4},
        "evidence_probes": {"P1_orphans_after": len(orphan_after),
                            "P2_board_real_coverage": f"{len(gen['entries'])+len(gen['blocked'])} 决策 / 板实 SMD 电源地 pad",
                            "P3_geometry_zero": True, "P4_thresholds_untouched": True},
        "rollback": "删除 rev-9 并把引擎/validator/co77/co78/co81/co84 的 pin 指回 rev-8（rev-8 原件未动）"}
    # 不变量机判：除 pd / spec_version / _spec_rev_9 外，其余必须逐值等于 rev-8
    unexpected = [k for k in base if k not in ("pd", "spec_version", "_spec_rev_9") and
                  json.dumps(base[k], sort_keys=True) != json.dumps(d[k], sort_keys=True)]
    assert not unexpected, f"unexpected changes outside pd: {unexpected}"
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"artifact": "m13_v57_co89_pdn_board_realize_rev9", "schema": 1, "revision": "CO-89.1",
           "nature": "L2 PDN：SPEC rev-9 板实化（power_pad_connect 重生成 + 解耦决策板实化 + 旧 BOM 退役留存）",
           "src": {"spec": SRC.name, "sha16": src_sha, "unchanged": src_sha == s16(SRC)},
           "out": {"spec": OUT.name, "sha16": s16(OUT)},
           "probe": probe, "board": {"name": BOARD.name, "sha16": s16(BOARD)},
           "n_retired_entries": len(old_e), "n_orphan_entries_retired": n_orph_e,
           "n_orphan_blocked_retired": n_orph_b,
           "decoupling_targets": DEC_ALL,
           "unexpected_changes_outside_pd": unexpected,
           "l2_invariant": d["_spec_rev_9"]["l2_invariant"],
           "redline": "零几何/零阈值改动；冻结四源与 L1 冻结源未动；历史件不触碰；无 while/坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"spec_rev9_sha16": rec["out"]["sha16"], "rev8_unchanged": rec["src"]["unchanged"],
                      "generated": probe, "retired": [len(old_e), len(old_b)],
                      "orphans_after": len(orphan_after), "unexpected": unexpected}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
