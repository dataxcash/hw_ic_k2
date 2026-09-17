#!/usr/bin/env python3
"""k2_p4_rev44_declare_v1 — P4 增量 15 的 SPEC 留痕（rev-42 -> rev-43）+ project.yaml 重指向。

依据 owner 常设裁定 #14（L2 = 走廊/**布线**/**过孔策略** = 自裁勿停）+ 《宪法》第四条（改板须 SPEC 留痕）。
零设计决策：只做「读 rev-42 → 加 `_spec_rev_33` 留痕块 → 写 rev-43」，并自检叶级 diff（仅 spec_version + 新块，删除 0）。
"""
from __future__ import annotations
import json, os, re, sys, hashlib

K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L3 = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L3")
SRC = os.path.join(L3, "SPEC_k2_v4.spec-rev-43.json")
DST = os.path.join(L3, "SPEC_k2_v4.spec-rev-44.json")
PROJ = os.path.join(K2, "pm_gate", "project.yaml")

BLOCK = {
    "card": "SPEC-REV-34",
    "at": "2026-09-17",
    "authority": "ARCHER L2 自裁（owner #14「L2 = 走廊/**布线**/**过孔策略** = 自裁勿停」）+ 监理 #K2-19 §二（W-1..W-5 授权新写确定性执行器）+ 监理本轮续推（P4 内继续 L2 收敛，不越阶段）",
    "basis": [
        "增量 15 后残 3：`12V_IN`（= **owner 硬闸 §5-5 H3**，未动）· `DS320_STRAP_A_ADDR0_15-8` · `DS320_STRAP_MODE`。",
        "诊断（T-36）：R35..R44 行的南向 F.Cu 出口**唯一**（x≈80.5..82.3），其南墙 = **`PCIE_REFCLK1_P/N` 长度匹配对**"
        "（对内等长 0.0，冻结判据 ≤0.15）⇒ **不可挪动**；两残项又都是**东缘球**（`U6.FF5` 104.17,56.29 / `U6.FF24` 104.17,52.69），"
        "仅球心盘中孔可逃逸 ⇒ 性质是**走廊容量/分配**，不是布线器搜索不足。",
        "结论（T-34）：**处理顺序即分配手段** —— 同器同板仅把 strap 组置于确定性优先序，解数由 11 → **12**。"
        "本增量据此**重做增量 15 的 M15 阶段**（同阶段内修订：旧 M15 路由集 502 段/38 孔被新集 450 段/39 孔取代，旧板仍可由 k2 commit `be86a05` 取回）。",
        "孔类**一律沿用板内既有 5 个 span 类**（0.35 盘 / 0.20 孔），**不新开孔类、不放松任何 DRC 下限**；纯增、0/45/90°、单腿 ≥0.05。",
    ],
    "findings": [
        "**T-34（处理顺序 = 走廊分配手段）**：同器同板，仅改确定性优先序（`--order list` + `PRIORITY_NETS`），解数 **11 → 12**（"
        "`DS320_STRAP_MODE` 得以落线）。三种非优先序（dist_asc / dist_desc / hard）实测均停在 11 且失败集在 2 条 strap 间轮换 ⇒ 顺序是唯一杠杆。",
        "**T-35（堆叠孔是门禁，不是技巧）**：若允许「同格连续换层」（In2→In5 与 In5→B 同 XY），会形成同点两孔 ⇒ KiCad **`holes_co_located`**"
        "（**非 ignore 族**、属门禁）⇒ 首版实测新增 1 条。修法 = 器内 **禁止同格连续换层**（`viaf` 守卫，强制中间层位移 ≥1 格），"
        "并加「本路由自身孔间两两判定」（孔-孔 / 孔-铜，**同网无豁免**）。修正后 12 条解仍成立且新增 0。",
        "**T-36（R 行南向缝的唯一性与不可动性）**：y 62.5..63.7 / x 76..108 的 F.Cu 铜**全部**属 `PCIE_REFCLK1_P`(10 段) + `PCIE_REFCLK1_N`(1 段) "
        "= 长度匹配差分对（对内等长 0.0）⇒ 任何位移都会动冻结判据「对内等长 ≤0.15」。故 R35..R44 的南向出口容量受单缝 (x∈[80.5,82.3]) 限制，"
        "strap 组必须先分配走廊（T-33 的 5/7 由此而来；本增量以优先序把 6 条**可行** strap 全部落线）。",
    ],
    "changes": [
        "spec_version: 1.1.spec-rev-43 -> 1.1.spec-rev-44",
        "P4 施工留痕（增量 16 / M15 阶段重做）：板 k2/hw/k2_v4_8L.l5.kicad_pcb = **d9813bc554a2d611**（取代 f8eeeda2495fb891）；"
        "`.kicad_pro` 未变（f68a5fb2f82bd02d）",
        "M15 处理顺序改为确定性优先序：`--order list`（`PRIORITY_NETS` = strap 组 7 条固定序 → 其余按 dist_asc）",
        "解出 **12 条**边 = strap 6 条（`A_ADDR0_7-0`/`A_ADDR1_7-0`/`B_ADDR0_7-0`/`B_ADDR1_7-0`/`B_ADDR0_15-8`/`MODE`，全可行集）+ "
        "低速·边带 4 条（`I2C1_SDA`/`I2C1_SCL`/`PWR_BTN_OUT`/`PERSTB#`）+ `PERSTA#` 2 条；共 **450 段 + 39 支盲/埋/通孔 / 591.6814mm**",
        "器内新增硬约束（两条）：① **禁止同格连续换层**（否则同点堆叠孔 ⇒ `holes_co_located`）；② 本路由自身孔间两两判定（孔-孔 / 孔-铜，同网无豁免）",
        "落板后**区域重填**（ZONE_FILLER）；T-22 守卫；uuid5 派生；幂等",
        "新执行器版本：k2/tools/k2_p4_mroute_v1.py = **7e5c0bf7bb03269d**（增量 15 版为 b3a6b6aadac741f6）",
        "pm_gate/project.yaml: spec_name -> SPEC_k2_v4.spec-rev-44.json",
    ],
    "unchanged": "除 spec_version + 本留痕块外全部叶承自 rev-43（逐叶同）；rev-19..43 原件逐字节未动",
    "before_after": {
        "drc": {
            "violations": "51 -> **51**（类型集与逐类计数**均不变**；逐条签名对增量 15 前基线 **新增 0 / 消失 0**；"
                          "对增量 15 板亦新增 0 / 消失 0）",
            "unconnected": "3 -> **2**（解 `DS320_STRAP_MODE`；新增 0）",
            "residual": "余 2 = ① `12V_IN`（J12.1）= **owner 硬闸 §5-5 H3**（未动）；"
                        "② `DS320_STRAP_A_ADDR0_15-8`（R42.1↔U6.FF5）= **端点局部不可解** —— R42.1 盘中心 ±1.2mm 内 "
                        "5 个 span 类**全无合法孔位**（阻断 = In2 `PCIE_DN1_P` 穿盘下 0.095mm），F.Cu 逃逸域粗搜仅 24 格 "
                        "⇒ 需**放置/既有铜级**处置（超 ENG 自裁域，见 handoff §5-3）",
        },
        "adjudicator": "PASS 6 / FAIL 4（**集合未变**；non45 仍 PASS 0/4701）",
        "non45": "0/4753 -> 0/4701（新增 450 段全 0/45/90°）",
        "intra_pair_skew": "max 0.0788（不变；18 对逐对同）",
        "segments": "4753 -> 4701（-52 = M15 502 -> 450）",
        "vias": "712 -> 713（+1 = M15 38 -> 39）",
        "total_length_mm": "6231.1438 -> 6273.2870（+42.1432 = 591.6814 - 549.5383 ⇒ 逐条守恒）",
        "复跑同一性": "两次独立复跑逐字节同（d9813bc554a2d611）；pro 未变",
        "ignored_checks_delta": "W-7 九条 ignore 机读复算（只读置 warning + 逐条签名）：8 项零变化；"
                                "`track_not_centered_on_via` **28 -> 30**（与增量 15 **同 2 条**：既有同网 In2 走线端点 (44.1266,46.0734) 与"
                                "新 `PERSTA#` In2→In5 孔 (44.15,46.10) 偏心 **0.035mm**）⇒ 本增量**未再增**；"
                                "属 ignore 族、非门禁，处置见 `k2/docs/K2-P4-W7-IGNORE-DISPOSITION-v1.md`",
    },
    "executor": [
        "k2/tools/k2_p4_mroute_v1.py 7e5c0bf7bb03269d（增量 16 版：优先序固化 + 禁同格连续换层 + 自孔两两判定）",
        "k2/tools/k2_p4_ls_local_v1.py 3eb4331bce9ba0ac（阶段 F1：1 段 0.5mm）",
        "kicad-cli 10.0.5（件 + 同名 .kicad_pro 同目录，T-8）+ criteria/adjudicate.py 897e8bfde60e2cfe",
    ],
    "evidence": "/tmp/opencode/p4c/{work0,i15a,i16,re3b}.kicad_pcb · {l_i16,re3_l2,l_ns_list}.json · "
                "{d_i14,d_i15a_x,d_i16_x,d_i16_repo}.json · w7/{w16,d_w16}.json · {vdist,freemap,probe2}.py（易失）",
    "rollback": "由 rev-43 原件 + 板 f8eeeda2495fb891 整体回退（增量 15 的 M15 路由集仍在 k2 commit `be86a05`）",
    "spec_sha256_before": "a98e3c482cdc15af",
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
        raise SystemExit("rev-43 往返风格不一致（拒绝写入）")
    before = leaves(d)
    d["spec_version"] = "1.1.spec-rev-44"
    d["_spec_rev_34"] = BLOCK
    out = json.dumps(d, indent=1, ensure_ascii=False).encode()
    after = leaves(json.loads(out))
    changed = [k for k in after if k in before and before[k] != after[k]]
    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    assert changed == ["/spec_version"], changed
    assert not removed, removed
    assert all(k.startswith("/_spec_rev_34") for k in added), [k for k in added if not k.startswith("/_spec_rev_34")]
    open(DST, "wb").write(out)
    proj = open(PROJ, encoding="utf-8").read()
    new_proj = re.sub(r"(?m)^spec_name: .*$", "spec_name: SPEC_k2_v4.spec-rev-44.json", proj)
    assert "spec_name: SPEC_k2_v4.spec-rev-44.json" in new_proj
    if new_proj != proj:
        open(PROJ, "w", encoding="utf-8").write(new_proj)
    print(json.dumps({"dst": os.path.basename(DST),
                      "sha256_16": hashlib.sha256(out).hexdigest()[:16],
                      "changed_leaves": changed, "added_leaves": len(added), "removed_leaves": 0,
                      "project_yaml": "spec_name -> rev-44"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
