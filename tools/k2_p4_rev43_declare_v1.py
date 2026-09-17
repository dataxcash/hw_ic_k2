#!/usr/bin/env python3
"""k2_p4_rev43_declare_v1 — P4 增量 15 的 SPEC 留痕（rev-42 -> rev-43）+ project.yaml 重指向。

依据 owner 常设裁定 #14（L2 = 走廊/**布线**/**过孔策略** = 自裁勿停）+ 《宪法》第四条（改板须 SPEC 留痕）。
零设计决策：只做「读 rev-42 → 加 `_spec_rev_33` 留痕块 → 写 rev-43」，并自检叶级 diff（仅 spec_version + 新块，删除 0）。
"""
from __future__ import annotations
import json, os, re, sys, hashlib

K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L3 = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L3")
SRC = os.path.join(L3, "SPEC_k2_v4.spec-rev-42.json")
DST = os.path.join(L3, "SPEC_k2_v4.spec-rev-43.json")
PROJ = os.path.join(K2, "pm_gate", "project.yaml")

BLOCK = {
    "card": "SPEC-REV-33",
    "at": "2026-09-17",
    "authority": "ARCHER L2 自裁（owner #14「L2 = 走廊/**布线**/**过孔策略** = 自裁勿停」）+ 监理 #K2-19 §二（W-1..W-5 授权新写确定性执行器）",
    "basis": [
        "handoff §8-2：P4 残 15 条未连接中 **14 条为 L2 布线域**（strap 7 · 低速/边带 4 · PERSTA# 3），"
        "唯一 owner 硬闸 §5-5 H3（连带 12V_IN）**不得擅动** ⇒ 本增量只做 L2 那 14 条。",
        "既有工具链 F1(`k2_p4_ls_local_v1.py`) / F2 / F3(`k2_p4_ls_xlayer_v1.py`) / G(`k2_p4_ls_in2_v1.py`) "
        "在**现板**复跑对 14 条残边**全部 0 解**（F1 仅解 1 条 0.5mm 同网相邻盘）⇒ 须新写执行器。",
        "新孔类**一律沿用板内既有 span 类**（F→In2 / F→In5 / F→B / In2→In5 / In5→B，均 0.35 盘 / 0.20 孔），"
        "**不新开孔类、不放松任何 DRC 下限**；纯增（不动既有铜）；新段 0/45/90° 且单腿 ≥0.05。",
    ],
    "findings": [
        "**T-29（布线器搜索窗必须覆盖真实走廊 —— bbox 窗是 F3 0 解的首因）**：`k2_p4_ls_xlayer_v1.py::blocked_layer` "
        "把搜索窗夹在「两端 bbox ±1mm」内，而本板 U6↔J2 类走线的**真实走廊在窗外**（南侧 y 68..78 的 B.Cu 围裙 / "
        "In5 高速道）。实测该板既有 U6↔J2 范式为「F.Cu 逃逸 → **F→In2 盲孔** → In2 竖降 → In2→In5 → In5 横贯 → "
        "In2→In5 上升 → F→In2 → J2 逃逸」（PCIE_DN0_P 全长 89.8mm）。**新器窗 = 两端 bbox 扩 `--margin`（默认 14mm）并夹于板内**。",
        "**T-30（孔 oracle 必须取「孔/铜」四种配对的 max）**：孔 DRC 有两族 —— `hole_clearance`（孔边 vs 异网**铜** 0.25）与 "
        "`hole_to_hole`（0.25，**无同网豁免**）。既有 `Ctx.via_exact` 对「via–via」只取 `max(VIA_R+v_r+req, HOLE_R+0.25)`，"
        "**漏掉 `HOLE_R+0.25+v_r`**（本孔-它铜）⇒ 首版落板后新增 **2 条 `hole_clearance`**（实测 0.2349 / 0.2263 < 0.25）。"
        "修正为四配对 max 后**新增 0**。同一漏检亦存在于 PTH 盘（须补同心孔项 `p.hole+0.25+VIA_R`）。",
        "**T-31（栅格剪枝只能「更保守」，不得「清格」）**：首版为让端点（BGA 格内焊盘）可达，曾把「同网铜覆盖格」无条件清空 ⇒ "
        "**反向擦掉异网障碍的封锁**，产生 7 条 via-clearance 假通过。正解 = **栅格余量取 0 并逐级放大重试**（0/0.03/0.08/0.15/0.25），"
        "**精确判据为唯一放行闸**。",
        "**T-32（本板 U6 是 ~0.3mm 节距「近实心」球阵 ⇒ 只能外缘逃逸；南侧 y 68..78 = B.Cu 净空围裙）**：U6 354 球 / 78 网、"
        "无净空内格（相邻球 0.3mm 节距 vs 0.35 孔 + 0.25 净距）⇒ 球只能在**外缘**（西 x≈81 / 东 x≈105.5 / 北 y≈49）逃逸；"
        "南侧围裙（板 x 23..143 / y 33..79）在三层上近乎全空，是本板唯一可用的长距离通道。",
        "**T-33（strap 组走廊容量上限）**：R35..R44 行有**唯一** F.Cu 南向缝（x≈80.5..81.75，y 63..63.5 的墙）与南侧围裙入口；"
        "三种确定性处理顺序（dist_asc / dist_desc / hard）实测**均停在 11/15**，失败集在 **2 条 strap 间轮换** "
        "⇒ strap 组在该行走廊容量上限 **5/7**（余 2 条须放置/走廊级处置，非器不足）。",
    ],
    "changes": [
        "spec_version: 1.1.spec-rev-42 -> 1.1.spec-rev-43",
        "P4 施工留痕（增量 15 / 低速·边带·strap 长逃逸布线）：板 k2/hw/k2_v4_8L.l5.kicad_pcb = **f8eeeda2495fb891**"
        "（取代 7ddfc9e3d6b23f2c）；`.kicad_pro` 未变（f68a5fb2f82bd02d）",
        "阶段 F1（复跑既有 `k2_p4_ls_local_v1.py`）：补 1 段 F.Cu 0.2mm——`PERSTA#` U1.11(31.8375,54.25) ↔ U1.12(31.8375,54.75)"
        "（同网相邻盘短连，0.5000mm）；该边为 DRC 未连接 15 之一，此前未施工",
        "阶段 M15（新器 `k2_p4_mroute_v1.py`）：多层 A*（层 = F.Cu / In2.Cu / In5.Cu / B.Cu，过孔转移仅用板内既有 5 个 span 类），"
        "粗搜 0.25mm（两端 bbox 扩 14mm）→ 走廊内精搜 0.10mm；**11 条边解出**："
        "`PERSTA#`×2（14.761 / 76.577mm）· `PERSTB#`（74.923）· `I2C1_SCL`（81.501）· `I2C1_SDA`（84.230）· "
        "`PWR_BTN_OUT`（27.554）· strap `DS320_STRAP_A_ADDR0_7-0`（17.910）· `A_ADDR1_7-0`（18.723）· "
        "`B_ADDR1_7-0`（19.510）· `B_ADDR0_15-8`（21.285）· `B_ADDR0_7-0`（21.694）；共 **502 段 + 38 支盲/埋/通孔**、549.5383mm",
        "落板后 **区域重填**（ZONE_FILLER：新孔须在 In1/In3/In6 GND 面与 In4 电源面取得 void）；新器内建 T-22 守卫（tmp 配对同名 pro + 落板后恢复 dst pro）",
        "新执行器：k2/tools/k2_p4_mroute_v1.py = b3a6b6aadac741f6（确定性；span 感知孔/层感知线 oracle + 扩张窗 + 余量逐级重试 + uuid5 派生 + 幂等）",
        "pm_gate/project.yaml: spec_name -> SPEC_k2_v4.spec-rev-43.json",
    ],
    "unchanged": "除 spec_version + 本留痕块外全部叶承自 rev-42（逐叶同）；rev-19..42 原件逐字节未动",
    "before_after": {
        "drc": {
            "violations": "51 -> **51**（类型集与逐类计数**均不变** hole_clearance 8 / courtyards_overlap 2 / "
                          "pth_in_courtyard 3 / solder_mask_bridge 2 / hole_to_hole 1 / lib_footprint_mismatch 35；"
                          "逐条签名（type + 两端位置）集合**新增 0 / 消失 0**）",
            "unconnected": "15 -> **3**（解 12；新增 0）",
            "residual": "余 3 = ① `12V_IN`(J12.1 ↔ 0.9250mm 走线) = **owner 硬闸 §5-5 H3**（keepout 未放开，不得擅动）；"
                        "② `DS320_STRAP_A_ADDR0_15-8`(R42.1 ↔ U6.FF5) = **端点局部不可解**（R42.1 盘中心 ±1.2mm 内 "
                        "5 个 span 类**全无合法孔位**，阻断 = In2 `PCIE_DN1_P` 穿盘下 0.095mm；F.Cu 逃逸域粗搜仅 24 格）；"
                        "③ `DS320_STRAP_MODE`(R35.1 ↔ U6.FF24) = **strap 组走廊容量**（见 T-33；三种顺序下失败集在 "
                        "`MODE` / `A_ADDR0_7-0` / `B_ADDR1_7-0` 间轮换，余 2 条 strap 无解）；"
                        "④ 非门禁登记：W-7 `track_not_centered_on_via` +2（见 ignored_checks_delta，"
                        "ENG 已登记，可与 W-7 一并处置）",
        },
        "adjudicator": "PASS 6 / FAIL 4（**集合未变**；non45 仍 PASS 0/4753）",
        "non45": "0/4250 -> 0/4753（新增 503 段全 0/45/90°）",
        "intra_pair_skew": "max 0.0788（不变；18 对逐对同）",
        "segments": "4250 -> 4753（+503 = F1 1 + M15 502）",
        "vias": "674 -> 712（+38，全部沿用板内既有 span 类）",
        "total_length_mm": "5681.1056 -> 6231.1438（+550.0382 = 0.5000 + 549.5383 ⇒ 逐条守恒）",
        "复跑同一性": "两次独立复跑逐字节同（f8eeeda2495fb891）；pro 未变",
        "ignored_checks_delta": "W-7 九条 ignore 的**机读复算**（只读：临时把 pro 的 rule_severities 置 warning，"
                                "pre/post 逐条签名比对）：copper_sliver 0->0 · footprint_filters_mismatch 0->0 · "
                                "footprint_type_mismatch 0->0 · tuning_profile_track_geometries 0->0 · "
                                "missing_courtyard 40->40 · silk_over_copper 44->44 · silk_overlap 20->20 · "
                                "via_dangling 12->12 · **track_not_centered_on_via 28->30（+2，本增量新增）**。"
                                "新增 2 条 = **新 In2→In5 盲孔**（`PERSTA#` @(44.15,46.10)）与既有同网 In2 走线端点 "
                                "（44.1266,46.0734）**偏心 0.035mm**（同族既有 28 条；属 ignore 族、不在冻结 manifest 控制集内）。",
    },
    "executor": [
        "k2/tools/k2_p4_mroute_v1.py b3a6b6aadac741f6（**新**）",
        "k2/tools/k2_p4_ls_local_v1.py 3eb4331bce9ba0ac（既有，阶段 F1 首次在本板施加）",
        "kicad-cli 10.0.5（件 + 同名 .kicad_pro 同目录，T-8）+ criteria/adjudicate.py 897e8bfde60e2cfe",
    ],
    "evidence": "/tmp/opencode/p4c/{work0,i15a,i15b,i15c,re2b}.kicad_pcb · {l5,l_i15c,re2_l2}.json · "
                "{d_i14,d_i15a_x,d_i15b_x,d_i15c_x}.json · {vdist.py,probe2.py,diag.py,freemap.py}（易失）",
    "rollback": "由 rev-42 原件 + 板 7ddfc9e3d6b23f2c 整体回退（或删本增量 11 网新铜 502 段 + 38 孔与 F1 单段后重填）",
    "spec_sha256_before": "9876b2ac04ceeaf4",
}


def leaves(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items(): o.update(leaves(v, p + "/" + str(k)))
    elif isinstance(d, list):
        o[p] = "list[%d]" % len(d)
    else:
        o[p] = d
    return o


def main():
    raw = open(SRC, "rb").read()
    d = json.loads(raw)
    if json.dumps(d, indent=1, ensure_ascii=False).encode() != raw:
        raise SystemExit("rev-42 往返风格不一致（拒绝写入）")
    before = leaves(d)
    d["spec_version"] = "1.1.spec-rev-43"
    d["_spec_rev_33"] = BLOCK
    out = json.dumps(d, indent=1, ensure_ascii=False).encode()
    after = leaves(json.loads(out))
    changed = [k for k in after if k in before and before[k] != after[k]]
    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    assert changed == ["/spec_version"], changed
    assert not removed, removed
    assert all(k.startswith("/_spec_rev_33") for k in added), [k for k in added if not k.startswith("/_spec_rev_33")]
    open(DST, "wb").write(out)
    proj = open(PROJ, encoding="utf-8").read()
    new_proj = re.sub(r"(?m)^spec_name: .*$", "spec_name: SPEC_k2_v4.spec-rev-43.json", proj)
    assert "spec_name: SPEC_k2_v4.spec-rev-43.json" in new_proj
    if new_proj != proj:
        open(PROJ, "w", encoding="utf-8").write(new_proj)
    print(json.dumps({"dst": os.path.basename(DST),
                      "sha256_16": hashlib.sha256(out).hexdigest()[:16],
                      "changed_leaves": changed, "added_leaves": len(added), "removed_leaves": 0,
                      "project_yaml": "spec_name -> rev-43"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
