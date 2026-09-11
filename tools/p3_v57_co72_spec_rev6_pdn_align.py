#!/usr/bin/env python3
"""CO-72：【L2 PDN】SPEC rev-6 —— PDN 平面声明对齐 LID REV6（In5 平面 -> In6）+ B.Cu 承载冲突登记。

缺陷（方案(a)/LID REV6 引入的**自身不自洽**）：`pd.gnd_planes` 与 `pd.zone_defs.gnd_planes`/解耦规则仍写
**In1/In3/In5** 为 GND 平面；而 LID REV6 下 **In5 已是信号层、In6 才是 GND 平面** ⇒ PDN 声明若照此施工会把
GND 铺在信号层 In5 上。本件对齐为 **In1/In3/In6**（纯声明修正；**零几何**——引擎不消费 `pd`）。

另登记**既有**冲突（非本件引入）：`pd.power_zones[2..4]` 的 **B.Cu POWER_POUR/桥接**；8L（LID.1 起）B.Cu 即信号层，
LID REV6 下 B.Cu 且已由 In6 参考（阻抗可控）⇒ B.Cu 铺铜与信号冲突，重规划触及**电源域划分/层数 = L1**，故登记不擅改。

只读冻结源；版本 bump 新文件；不改阈值/几何。
"""
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-5.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-6.json"
REC = L3 / "mcio_feas_step2/m13_v57_co72_pdn_align.json"


def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    s5 = json.loads(SRC.read_text(encoding="utf-8"))
    src_sha = s16(SRC)
    s6 = copy.deepcopy(s5)
    s6["spec_version"] = "1.1.spec-rev-6"

    # 1) GND 平面清单 In5 -> In6
    assert s6["pd"]["gnd_planes"] == ["In1.Cu", "In3.Cu", "In5.Cu"]
    s6["pd"]["gnd_planes"] = ["In1.Cu", "In3.Cu", "In6.Cu"]

    # 2) zone_defs.gnd_planes 的 In5 条目 -> In6
    gz = s6["pd"]["zone_defs"]["gnd_planes"]
    hit = [i for i, z in enumerate(gz) if z.get("layer") == "In5.Cu"]
    assert len(hit) == 1, hit
    gz[hit[0]]["layer"] = "In6.Cu"
    gz[hit[0]]["basis"] = (gz[hit[0]]["basis"] + "；CO-72：层名随 LID REV6 由 In5.Cu 更正为 In6.Cu"
                           "（方案(a) 后 In5=信号、In6=GND；几何/网/铜皮形状不变）")

    # 3) 解耦规则文本
    r = s6["pd"]["zone_defs"]["decoupling_via_to_plane"]["rule"]
    assert "In1/In3/In5" in r
    s6["pd"]["zone_defs"]["decoupling_via_to_plane"]["rule"] = r.replace("In1/In3/In5", "In1/In3/In6")

    # 4) 登记既有 B.Cu 承载冲突（L1：电源域划分/层数）
    s6["pd"]["zone_defs"].setdefault("ecn_pending_items", [])
    s6["pd"]["zone_defs"]["ecn_pending_items"].append({
        "id": "CO-72-PDN-1", "ruled": False,
        "desc": "pd.power_zones[2..4] 把 P3V3/P3V3_AUX/MCU_VDD 铺到 B.Cu（POWER_POUR/桥接/短段）；但 8L LID.1/REV6 下 B.Cu 为**信号层**"
                "（且 REV6 下由 In6=GND 参考、阻抗可控），与 B.Cu 承载的 PCIe 逃逸/落段直接冲突。",
        "nature": "既有漂移（8L 迁移起；本件仅登记，不擅改铜皮）",
        "resolution_scope": "L1（电源域划分 / 层数）",
        "direction": "待 owner：a) In4 分区扩展/重划  b) 增设内部电源层（层数）  c) B.Cu 信号改层；禁止自行选择"})

    # 5) 陈旧判据理由（REFCLK In2 选择依据）——只改文本，不改约束数值
    t = s6["constraints"]["escape_transition_zone"]["refclk_j2_transit"]
    old = t["in2_layer_basis"]
    t["in2_layer_basis"] = ("In2 = stripline dual GND ref (In1/In3)；选择依据 = In2 通道几何"
                            "（CO-72 更正：原文『B.Cu 参考层为 In6 信号层、非定阻抗』在 LID REV6 下已失效——B.Cu 现由 In6=GND 参考、阻抗可控）")

    s6["_spec_rev_6"] = {
        "card": "SPEC-REV-6", "at": "2026-09-12", "authority": "L2 PDN 自裁（CO-72；LAYOUT_CONSTITUTION 第二章 PDN）",
        "changes": ["spec_version: 1.1.spec-rev-5 -> 1.1.spec-rev-6",
                    "pd.gnd_planes: In5.Cu -> In6.Cu（LID REV6：In5=信号、In6=GND）",
                    "pd.zone_defs.gnd_planes[In5] -> In6.Cu（层名更正；形状/网不变）",
                    "pd.zone_defs.decoupling_via_to_plane.rule 文本 In1/In3/In5 -> In1/In3/In6",
                    "pd.zone_defs.ecn_pending_items += CO-72-PDN-1（B.Cu 铺铜 vs 信号层冲突，L1）",
                    "constraints.escape_transition_zone.refclk_j2_transit.in2_layer_basis 文本更正（B.Cu 现受参考）"],
        "unchanged": "stackup / impedance / net_classes / vias / corridors / layer_plan / board / components 全部未动；零几何",
        "geometry_impact_expected": "none（引擎不消费 pd；文本更正不影响任何几何键）",
        "rollback": "删除本文件；引擎/记录指回 spec-rev-5 (1f351194b3e22b7e)"}

    # 机判：仅上述键变化
    def diff(a, b, pre=""):
        out = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in set(a) | set(b):
                if k in ("spec_version", "_spec_rev_6"):
                    continue
                if k not in a: out.append(pre + "/" + k + " (added)")
                elif k not in b: out.append(pre + "/" + k + " (removed)")
                else: out += diff(a[k], b[k], pre + "/" + k)
        elif isinstance(a, list) and isinstance(b, list):
            if json.dumps(a) != json.dumps(b): out.append(pre + f" (list changed len {len(a)}->{len(b)})")
        elif a != b:
            out.append(pre + " (changed)")
        return out
    changes = diff(s5, s6)
    allowed = ("/pd/gnd_planes", "/pd/zone_defs/gnd_planes", "/pd/zone_defs/decoupling_via_to_plane/rule",
               "/pd/zone_defs/ecn_pending_items",
               "/constraints/escape_transition_zone/refclk_j2_transit/in2_layer_basis")
    unexpected = [c for c in changes if not any(c.startswith(a) for a in allowed)]
    OUT.write_text(json.dumps(s6, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"artifact": "m13_v57_co72_pdn_align", "schema": 1, "revision": "CO-72.1",
           "nature": "L2 PDN：SPEC rev-6 平面声明对齐 LID REV6 + B.Cu 冲突登记",
           "spec_rev5_sha16": src_sha, "spec_rev5_sha16_after": s16(SRC), "spec_rev6_sha16": s16(OUT),
           "changed_keys": changes, "unexpected_changes": unexpected,
           "geometry_invariance_expected": True,
           "redline": "原件未动；零几何/阈值改动；B.Cu 冲突为 L1（电源域/层数），仅登记。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"spec_rev6_sha16": s16(OUT), "rev5_unchanged": src_sha == s16(SRC),
                      "changed_keys": changes, "unexpected": unexpected}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
