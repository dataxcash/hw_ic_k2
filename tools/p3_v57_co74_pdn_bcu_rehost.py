#!/usr/bin/env python3
"""CO-74：【L2 PDN】B.Cu 电力铜退役 + In4 改由承载（REV6）；CO-72-PDN-1 归口裁定（L1 -> L2）。

背景（CO-72 登记、CO-73 未解）：
  `pd.zone_defs.power_zones[2..4]` 把 P3V3 / P3V3_AUX / MCU_VDD 铺到 **B.Cu**
  （`P3V3_BCU_BRIDGE` / `P3V3_AUX_BCU_BRIDGE` / `MCU_VDD_BCU_RESISTORS`），
  而 LID REV6 下 B.Cu = **高速信号层**（dn 带逃逸/落段，CO-62 实测 32/68 网 290.21mm 铜）。
  该裁决（T2-ECN-1/2，2026-08-23）的前提是 6L 时代的『In4 走线带 x∈[50,88.17] 阻断跨带铜皮』
  ⇒ 必须借用 B.Cu（当时 SPEC 明示 B.Cu=POWER_POUR）绕行。

本件机判结论（两条，均可独立重算）：
  P1 引擎 `LAYER_PALETTE = ["F.Cu","In2.Cu","In5.Cu","B.Cu"]`（CO-68/69）⇒ In4 **不是布线层**；
  P2 交付板 `k2_v4_8L.l4.kicad_pcb`(0e636a67c1472462) 段层直方图 In4.Cu = **0**
     （F 174 / In2 106 / In5 2204 / B 39）。
  ⇒ REV6 下不存在 In4 走线带 ⇒ T2-ECN-1/2 的**前提消失**，绕行需求归零，B.Cu 电力铜无存在理由。
  另：`power_zones[3].in6_segments`（P3V3_AUX 借 In6 搭桥）在 REV6 下 In6=GND 平面 ⇒ **短路**，一并退役。

归口（L1 -> L2）：按 CO-67 已记录的 L2 不变量 —— 层数 8 / 平面数 4（3×GND+1×P3V3）/
  电源域集合 {P3V3, P3V3_AUX, MCU_VDD} 全不变 —— 本件只改**电力铜的承载层与分区几何**，
  `pd.power_plane_layer` 仍 = In4.Cu。故 CO-72-PDN-1 的 `resolution_scope` 由 L1 更正为 **L2**。
  （备选 b『增设电源层』= 层数、c『B.Cu 信号改层』= 信号流向，二者仍属 L1，本件**不选**。）

改法：B.Cu 电力铜**逐条退役并转 In4 承载**，6L 口径的 polygons/segments/in6_segments/vias
  全部**原样留存**于 `retired_*_bcu`（禁止静默放弃），新几何 = L3 施工确定性派生（非求解器）。
只读冻结源；版本 bump 新文件；零几何/阈值改动（引擎不消费 `pd.zone_defs.power_zones` / `ecn_pending_items`）。
"""
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-7.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-8.json"
REC = L3 / "mcio_feas_step2/m13_v57_co74_pdn_bcu_rehost.json"
ENGINE = K2 / "tools/p3_v57_w3_constructive.py"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
BOARD_SHA = "0e636a67c1472462"

CARRIER_BASIS = (
    "LID REV6（方案(a)）下 B.Cu = 高速信号层（承载 dn 带逃逸/落段；CO-62 实测 32/68 高速网 290.21mm 铜）"
    "⇒ 禁止电力铺铜；而 In4 在 REV6 下**无布线**（引擎 LAYER_PALETTE=F/In2/In5/B，交付板 In4.Cu 段数 0）"
    "⇒ 6L 时代『In4 走线带 x∈[50,88.17] 阻断跨带铜皮』前提消失，电力铜改由 In4 承载。"
)

TARGETS = {
    "P3V3_BCU_BRIDGE": ["U2.pad5(P3V3,33,37)", "U4.pad3(P3V3,40,37)", "C84.pad1(P3V3,44,40)"],
    "P3V3_AUX_BCU_BRIDGE": ["J3.A9(P3V3_AUX, 板实测 60.1,45.75)", "J4.A9(P3V3_AUX, 58.9,61.45)"],
    "MCU_VDD_BCU_RESISTORS": ["R29", "R31", "R32", "R33", "R34"],
}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def layer_hist(board_text: str) -> dict:
    import re, collections
    out = collections.Counter()
    for m in re.finditer(r"\(segment\b", board_text):
        lm = re.search(r'\(layer "([^"]+)"\)', board_text[m.start():m.start() + 400])
        out[lm.group(1) if lm else "?"] += 1
    return dict(out)


def main() -> int:
    s7 = json.loads(SRC.read_text(encoding="utf-8"))
    src_sha = s16(SRC)
    s8 = copy.deepcopy(s7)

    engine_src = ENGINE.read_text(encoding="utf-8")
    hist = layer_hist(BOARD.read_text(encoding="utf-8", errors="replace"))
    board_sha = hashlib.sha256(BOARD.read_bytes()).hexdigest()[:16]
    probes = {
        "P1_engine_palette_excl_In4": 'LAYER_PALETTE = ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"]' in engine_src,
        "P1_engine_has_no_In6_literal": '"In6.Cu"' not in engine_src,
        "P2_board_In4_segments_zero": hist.get("In4.Cu", 0) == 0,
        "P2_board_sha": board_sha == BOARD_SHA,
        "P3_engine_ignores_power_zones": "power_zones" not in engine_src,
        "P3_engine_ignores_ecn_pending": "ecn_pending" not in engine_src,
        "segment_layer_hist": hist,
    }
    for k, v in probes.items():
        if isinstance(v, bool):
            assert v, f"probe failed: {k}"
    assert board_sha == BOARD_SHA, (board_sha, BOARD_SHA)

    s8["spec_version"] = "1.1.spec-rev-8"
    zd = s8["pd"]["zone_defs"]
    pzs = zd["power_zones"]

    rehosted = []
    for i, z in enumerate(pzs):
        if z.get("layer") != "B.Cu":
            continue
        zone_name = z.get("zone")
        old_vias = z.get("vias", [])
        for key in ("polygons", "segments", "in6_segments"):
            if key in z:
                z["retired_" + key + "_bcu"] = z.pop(key)
        z["layer"] = "In4.Cu"
        z["zone"] = zone_name + "_IN4"
        z["carrier_change"] = {
            "co": "CO-74", "from": "B.Cu", "to": "In4.Cu", "basis": CARRIER_BASIS,
            "voided_premise": "T2-ECN-1/2 (2026-08-23) 裁决前提 = 6L『In4 走线带阻断跨带铜皮』+ SPEC B.Cu=POWER_POUR；"
                              "二者在 LID REV6 下均已失效（见 probes）。PM 裁决原文保留于 pd.ecn_pending_items，不改。",
            "direction_scope": "REV6 下方向选择（In4 内分区/西区小岛/西侧 annex）不涉及电源域集合与层数 ⇒ L2（CO-67 不变量）。",
        }
        z["polygons"] = []
        z["segments"] = []
        z["geometry_status"] = "L3_CONSTRUCTION_DERIVED"
        z["derivation"] = (
            "In4 区域多边形 + 贯通孔反焊盘净空 = L3 施工确定性派生（非求解器、零坐标搜索）；"
            "要求：① 覆盖 targets 全部 pad；② 与 In4 上全部贯孔反焊盘按 shop 判据净空；"
            "③ 与异网 In4 区域铜边净距 ≥0.2mm（POWER 判据，不得放宽）；④ 同网各区须连续（无孤岛未连）。"
        )
        z["targets"] = TARGETS.get(zone_name, [])
        z["vias"] = old_vias
        z["vias_note"] = ("落点坐标为 6L 口径（原落 B.Cu）；REV6 下须落 **In4 平面**（贯孔至 In4），坐标于 L3 重导。"
                          "原坐标保留以便对账，禁止静默放弃。")
        rehosted.append({"index": i, "zone": zone_name, "retired_keys": sorted(
            k for k in z if k.startswith("retired_"))})

    assert len(rehosted) == 3, rehosted
    assert not any(z.get("layer") == "B.Cu" for z in pzs), "B.Cu 电力铜未清空"
    assert all("in6_segments" not in z for z in pzs), "In6 搭桥未退役"

    s8["pd"]["bcu_power_copper_policy"] = {
        "policy": "PROHIBITED",
        "basis": "LID REV6：B.Cu = 高速信号层（In6=GND 参考，85Ω 可控），不得铺电力铜/搭桥。",
        "co": "CO-74",
    }

    ecn = zd["ecn_pending_items"]
    hit = 0
    for it in ecn:
        if it.get("id") == "CO-72-PDN-1":
            it["ruled"] = True
            it["ruled_at"] = "2026-09-12T09:40:00+08:00"
            it["resolution_scope"] = "L2（PDN/叠层分配；原标 L1 系过高归口，按 CO-67 不变量更正）"
            it["ruling"] = (
                "CO-74 裁定：冲突前提（6L『In4 走线带 x∈[50,88.17] 阻断跨带铜皮』+ SPEC B.Cu=POWER_POUR）"
                "在 LID REV6 下均已失效 —— 引擎 LAYER_PALETTE 无 In4、交付板 In4.Cu 段数 0 ⇒ In4 无布线带，"
                "跨带绕行需求归零。故 B.Cu 电力铜（power_zones[2..4]）**全部退役**，改由 In4 承载"
                "（layer=B.Cu->In4.Cu；6L 几何原样留存于 retired_*_bcu）；In6 搭桥（in6_segments）"
                "在 In6=GND 下会短路，一并退役。层数 8 / 平面数 4 / 电源域集合不变 ⇒ 属 L2（CO-67）。"
                "新几何（In4 分区多边形 + 反焊盘净空 + 同网连续性）= L3 施工确定性派生。"
                "备选 b（增设电源层）/ c（B.Cu 信号改层）仍属 L1，本件不选。"
            )
            hit += 1
    assert hit == 1, hit

    s8["_spec_rev_8"] = {
        "card": "SPEC-REV-8", "at": "2026-09-12",
        "authority": "L2 PDN 自裁（CO-74：B.Cu 电力铜退役 + In4 承载；CO-72-PDN-1 归口 L1->L2）",
        "changes": [
            "spec_version: 1.1.spec-rev-7 -> 1.1.spec-rev-8",
            "pd.zone_defs.power_zones[2..4]（B.Cu）: layer B.Cu -> In4.Cu；6L 几何转 retired_*_bcu；新几何=L3 派生",
            "pd.zone_defs.power_zones[3].in6_segments: 退役（REV6 In6=GND，搭桥即短路）",
            "pd.bcu_power_copper_policy: PROHIBITED（新增）",
            "pd.ecn_pending_items[CO-72-PDN-1]: ruled=true，scope L1->L2",
        ],
        "unchanged": "stackup / impedance / net_classes / vias / corridors / board / components / "
                     "pd.gnd_planes / pd.power_plane_layer(In4.Cu) / pd.power_partition / constraints 全部未动；零几何",
        "not_touched": "历史件（_spec_rev_* 溯源块 / appendix / pd.ecn_pending_items 的 T2-ECN-1/2/3 原文）",
        "evidence_probes": {k: v for k, v in probes.items()},
        "geometry_impact_expected": "none（引擎不消费 power_zones/ecn_pending_items）",
        "rollback": "删除本文件；引擎/记录指回 spec-rev-7 (a15ffcd104d82f43)",
    }

    def diff(a, b, pre=""):
        out = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in set(a) | set(b):
                if k in ("spec_version", "_spec_rev_8"):
                    continue
                if k not in a:
                    out.append(pre + "/" + k + " (added)")
                elif k not in b:
                    out.append(pre + "/" + k + " (removed)")
                else:
                    out += diff(a[k], b[k], pre + "/" + k)
        elif isinstance(a, list) and isinstance(b, list):
            if json.dumps(a) != json.dumps(b):
                out.append(pre + " (list changed)")
        elif a != b:
            out.append(pre + " (changed)")
        return out

    changes = diff(s7, s8)
    allowed = ("/pd/zone_defs/power_zones", "/pd/bcu_power_copper_policy", "/pd/zone_defs/ecn_pending_items")
    unexpected = [c for c in changes if not any(c.startswith(a) for a in allowed)]
    OUT.write_text(json.dumps(s8, ensure_ascii=False, indent=1), encoding="utf-8")

    rec = {
        "artifact": "m13_v57_co74_pdn_bcu_rehost", "schema": 1, "revision": "CO-74.1",
        "nature": "L2 PDN：B.Cu 电力铜退役 + In4 承载；CO-72-PDN-1 归口 L1->L2",
        "spec_rev7_sha16": src_sha, "spec_rev7_sha16_after": s16(SRC),
        "spec_rev8_sha16": s16(OUT),
        "changed_keys": changes, "unexpected_changes": unexpected,
        "rehosted": rehosted,
        "probes": probes,
        "retired_geometry_preserved": True,
        "l2_invariant": {"layers": 8, "planes": 4, "power_domains": ["P3V3", "P3V3_AUX", "MCU_VDD"],
                          "signal_layers": 4, "power_plane_layer": "In4.Cu"},
        "geometry_invariance_expected": True,
        "redline": "原件未动；零几何/阈值改动；阈值未放宽；历史件不触碰；无 while/坐标搜索。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"spec_rev8_sha16": s16(OUT), "rev7_unchanged": src_sha == s16(SRC),
                      "changes": changes, "unexpected": unexpected,
                      "rehosted": [r["zone"] for r in rehosted]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
