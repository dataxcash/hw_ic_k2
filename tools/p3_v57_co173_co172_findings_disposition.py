#!/usr/bin/env python3
"""CO-173 — CO-172 复评 findings 处置（F-1..F-7）⇒ 登记簿 + 施加修复。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.8，
t12/t12b/t12c..t12h + t11c/t11d）与 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.2，t03）、
`p3_v57_co164_order_runner.py`（CO-169.2，t12）承载。
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co173_co172_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L5PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
REG = L2 / "input_defect_register_v1.json"
KEY = "co172:{}"

ITEMS = [
 {"id": "F-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "`ORDER_NOTES` §5「模型间 spread ≈4.8%」为**记录派生数字**但无来源记录串、无牙齿（CO-171 t12 只绑 dev% +11.7%）"
          "⇒ R-CO171-1 在本备注内仍有未绑定项（CO-172 P1 注入实证：仅改 spread、不动 dev% 时 as-found 判据全 True）。",
  "disposition": "CO-172/CO-173：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.8** —— 新增纯谓词 "
                 "`impedance_spread_pct(imp)`（watch 逐几何模型极差 / 最小值归一）+ 有锚判据 `impedance_spread_pct` + 灵敏度 t12c。",
  "status": "CLOSED", "next": "凡备注内可由记录复算的数字（含**导出量**如 spread）一律给牙齿 + 负控。",
  "evidence": ["CO-172 P1（修前）：F.Cu M1 90.61→94.0 ⇒ spread 4.8%→1.0%，as-found `order_notes_record_figures` 仍全 True",
               "CO-173 复核（修后）：t12c 注入同扰动 ⇒ 判不通过；现行 `record_figures.impedance_spread_pct = 4.78`（备注 ≈4.8%）"],
  "refs": ["CO-172", "CO-173", "CO-171", "CO-146"], "closed_by": ["CO-173"]},
 {"id": "F-2", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "§2 非通孔过孔**逐 span 分解**（92/88/32/8）为硬编码字面量；来源 = DFM 记录 `as_built.via_type_census`。"
          "总量 220/493 由生成式绑定、**分量无牙** ⇒ 过孔口径变更后可留陈旧分解（CO-172 P2 实证）。",
  "disposition": "CO-173：新增 `via_census_figures(dfm)` + **逐 span** 有锚判据（带备注实际分隔符，防前缀匹配）"
                 "`via_census_<span>` + 灵敏度 t12d；记录落 `record_figures.via_census`。",
  "status": "CLOSED", "next": "分量级数字与总量同须绑定（总量绑定 ≠ 分量绑定）。",
  "evidence": ["CO-172 P2（修前）：`F.Cu->In2.Cu|BLIND_BURIED` 92→93 ⇒ as-found 判据仍全 True",
               "CO-173 复核（修后）：t12d 同扰动 ⇒ 判不通过；现行 4 项 span 判据全 True（92/88/32/8）"],
  "refs": ["CO-172", "CO-173", "CO-146", "CO-147"], "closed_by": ["CO-173"]},
 {"id": "F-3", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "§3 阻焊开窗-邻铜净距（0.0695mm / 欠 0.0205mm / 回退净距 0.0995 / 开窗 0.05→0.02mm）为硬编码；"
          "来源 = CO-147 裁定记录 `mask_measure`（gap/shortfall/jlc_min/mask_expansion）。本项**随单提交板厂评审**，"
          "属客户可见（CO-172 P3 实证无牙）。",
  "disposition": "CO-173：新增 `mask_clearance_figures(co147)` + 4 项有锚判据（净距 / 欠量 / JLC 限 / 回退开窗路径）+ "
                 "回退净距**可重算路径**（`gap + mask_expansion − 0.02`，提案常量 `MASK_EXPANSION_REWORK_MM`）+ 灵敏度 t12e。",
  "status": "CLOSED", "next": "客户可见的工程边界值（净距/欠量/回退方案）须绑定来源记录且**可重算**（R-CO171-2 扩大适用）。",
  "evidence": ["CO-172 P3（修前）：`mask_measure.closest.gap_mm` 0.0695→0.0694 ⇒ as-found 判据仍全 True",
               "CO-173 复核（修后）：t12e 同扰动 ⇒ 判不通过；现行 5 项判据全 True；`rework_gap_mm = 0.0995` 由记录重算"],
  "refs": ["CO-172", "CO-173", "CO-147", "CO-152"], "closed_by": ["CO-173"]},
 {"id": "F-4", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "§6 U6 热数字（PACT 4.7–7.0W / θJA(high-K) 17.4°C/W / Tj 上限 120°C / Tj 121.8–161.8°C / ψJB 路线 173.6°C / Ta 40°C）"
          "为硬编码；来源 = CO-148 热裁定 + CO-149 缓解派生（CO-172 P4 实证无牙）。",
  "disposition": "CO-173：新增 `thermal_figures(co148, co149)` + 6 项有锚判据（P 区间 / θJA / Tj 上限 / Ta / Tj 跨档 / ψJB 路线）+ 灵敏度 t12f。",
  "status": "CLOSED", "next": "跨记录派生的**系统级**数字（热）与板级数字同须绑定；记录变更即须同步备注。",
  "evidence": ["CO-172 P4（修前）：`co148.worst.Tj_C` 161.8→165.0 ⇒ as-found 判据仍全 True",
               "CO-173 复核（修后）：t12f 同扰动 ⇒ 判不通过；现行 6 项判据全 True（P 4.7–7.0 / 17.4 / 120 / 40 / 121.8–161.8 / 173.6）"],
  "refs": ["CO-172", "CO-173", "CO-148", "CO-149"], "closed_by": ["CO-173"]},
 {"id": "F-5", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "§4 JLC 限值散文（≥3.5mil / 孔 ≥0.15 / 盘径 ≥0.25 / 孔径+0.15 / ≥0.2）源 = JLC 能力记录；"
          "「板规铜-板边 0.30mm」源 = **冻结** `drc_rules.manufacturing.min_copper_edge_clearance`，而该 0.30 在"
          "**备注与 DFM 闸工具两处**均为硬编码字面量（CO-172 P5/P6 实证）。",
  "disposition": "CO-173：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.2** —— 板规值改由冻结 `drc_rules` 派生 + "
                 "正控/灵敏度牙齿 t03（记录文本须携带派生值）；备注侧增 capability/rules 派生判据 `jlc_min_track_width_mil` / "
                 "`jlc_min_via_hole` / `jlc_min_via_diameter` / `jlc_via_annular_note` / `jlc_via_hole_to_hole` / "
                 "`rule_copper_edge_clearance` / `jlc_copper_edge_clearance` + 灵敏度 t12g/t12h。",
  "status": "CLOSED", "next": "外部公布能力值与**冻结板规**值须各有单一事实源；散文副本亦须有牙。",
  "evidence": ["CO-172 P5/P6（修前）：capability min_track 0.09→0.10、rules edge 0.30→0.25 ⇒ as-found 判据均仍全 True",
               "CO-173 复核（修后）：t12g/t12h 同扰动 ⇒ 判不通过；DFM 闸 t03（0.30 由冻结规则派生）正控/灵敏度均 True"],
  "refs": ["CO-172", "CO-173", "CO-146", "CO-147"], "closed_by": ["CO-173"]},
 {"id": "F-6", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "叠层图（03_，**随单提交的制造输入**）的**铜厚矩形几何**为硬编码 0.035/0.0175mm，t11 只绑文本"
          "（CO-172 P7 实证：`stackup_svg(spec)` 不接收声明表、`stackup_svg_binding_checks` 键纯文本）⇒ "
          "声明铜厚变更时图与声明在**几何上**脱钩，制造侧按图施工。",
  "disposition": "CO-173：`stackup_svg(spec, binding)` 铜厚矩形高度与标题 oz 改由**声明定值表**派生"
                 "（1oz=0.035mm 标称，当前 1oz/0.5oz ⇒ 21.00/10.50 px，**输出逐字节不变**）+ "
                 "`stackup_svg_copper_geometry_checks` + t11c（几何正控）/ t11d（声明 2oz ⇒ 几何判据须失败）。",
  "status": "CLOSED", "next": "制造输入不仅**文本**、其**几何**亦须由声明定值派生（或至少有几何牙齿）。",
  "evidence": ["CO-172 P7（修前）：`stackup_svg` 形参不含声明表；几何检查键 = 4 个文本记号",
               f"CO-173 复核（修后）：t11c/t11d 均 True；叠层图 sha16 {hashlib.sha256((L5PKG/'03_stackup/JLC08161H_stackup.svg').read_bytes()).hexdigest()[:16]} 逐字节不变"],
  "refs": ["CO-172", "CO-173", "CO-170", "CO-146"], "closed_by": ["CO-173"]},
 {"id": "F-7", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "runner `step_did_work` 快照为**单信号 mtime_ns**（CO-172 P8 实证：值为标量 int）⇒ 粗粒度/网络 FS 同刻重写、"
          "mtime 规范化/回写、时钟回拨下可**假停机**（fail-closed，不致假通过）；且受控集为全局集合、非步本地 ⇒ "
          "并发会话写受控件时可被误判为「本步做了事」（假通过方向）。",
  "disposition": "CO-173：`p3_v57_co164_order_runner.py` 升 **CO-169.2** —— `_artifact_stamp` 多信号指纹"
                 "（mtime_ns + ctime_ns + size + 内容 sha16）、`_snap_watched` 返回指纹字典 + 静态齿 t12。"
                 "**残余如实登记**：全局集非步本地归因未解（须逐步声明产物集）⇒ 见 next。",
  "status": "CLOSED", "next": "残余（未解）：受控集为全局集合 ⇒ 并发写入仍可误判；下轮候选 = 每步声明其主产物集（40 步逐一声明）。"
                              "另：字节全同的重写在粗粒度 FS 上仍与 no-op 不可分（假停机方向，接受；收敛另由 sha 稳定判定）。",
  "evidence": ["CO-172 P8（修前）：`_snap_watched()` 值 `type=int`（mtime only）；内容变而 mtime 不动不可见",
               "CO-173 复核（修后）：t12 静态齿（mtime 同 / sha 变 ⇒ 判「做了事」；全同 ⇒ 判「未做事」）True"],
  "refs": ["CO-172", "CO-173", "CO-169", "CO-165"], "closed_by": ["CO-173"]},
]

MARK = ("；**CO-172/CO-173（L2 自裁 · 非执行者对抗复评 + 记录派生数字绑定补强）**：复评 CO-166..CO-171（as-found @ 7bffb75）"
        "得 7 项 findings —— 备注内**仍有**未绑定的记录派生数字（§5 spread / §2 过孔分解 / §3 阻焊净距 / §6 热数字 / §4 限值+板规）、"
        "叠层图**铜厚矩形几何**未绑（仅文本）、runner `step_did_work` 单信号 mtime 灵敏度缺口；⇒ CO146-PKG.8（t12c..t12h + t11c/t11d）、"
        "CO146-JLC-DFM.2（t03）、CO-169.2（多信号快照 + t12）施加修复；备注/叠层图**输出逐字节不变**。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = {k: v for k, v in it.items() if k != "id"}
        if f in have:
            have[f].update(patch); updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch)); added.append(f)
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} / upd {len(updated)} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
