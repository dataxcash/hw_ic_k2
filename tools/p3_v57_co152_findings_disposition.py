#!/usr/bin/env python3
"""CO-152 — CO-151 findings 处置（executor · L2 自裁）：登记 3 项 TOOL_DEFECT 并关闭 + counts 复位。

性质：只改**登记簿**（L2 政策层）。不改 SPEC / 板 / 阈值 / 冻结四源 / 其它工件 / 台账。
幂等：按 `finding` 键存在即跳过；`meta.updated_by` 追加有 guard；`meta.counts` 由 items 重算。
证据一律**记号化**（指向 CO/文件，不写记录 sha）——登记簿内不得嵌下游 sha（CO-151 F-1 / CO-152 红线）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co152_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"

ITEMS = [
    {
        "finding": "tool_defect:records_snapshot_downstream_sha_causes_pin_drift",
        "kind": "TOOL_DEFECT", "severity": "medium",
        "what": "记录内嵌**下游** sha 快照（`register_sha16` / `register.sha16_after` / `ledger.sha16_after` / "
                "`co124.sha16`）⇒ 记录 sha 随运行序/时点漂移，提交 pin 不可由文档化复现序复现。CO-151 实测："
                "按 §6 序连跑两遍得**另一稳定不动点**（co124/co147/co148/co150 四条记录 pin ≠ 提交值），"
                "且 co148 重跑会把 2 条已闭登记项重开（OPEN 0→2）。与 CO-149 已修先例同族但未覆盖这 4 件。",
        "refs": ["CO-151", "CO-152", "CO-149"],
        "disposition": "CO-152 处置：① 移除该 4 件的下游快照字段（现行 sha 一律由 boundary pin 表单一承载）；"
                       "② co120 硬化（CO-120.2）新增 P5『下游快照声明册』：`*_sha16_after` 类键未在 "
                       "SNAPSHOT_DECLARED 声明即 FAIL，附负控/正控牙齿 ⇒ 禁止复发；③ 复核：§6 序连跑两遍，"
                       "4 件记录逐字节稳定，且残留 `sha16` 键均为**上游输入** pin（definition_doc / u6_inputs / pm_eval）。",
        "status": "CLOSED", "next": "新记录不得再嵌下游 sha 快照；跨件现行 sha 一律走 boundary pin 表。",
        "evidence": ["CO-151 记录 `m13_v57_co151_rev19_nonexecutor_review.json`（F-1）",
                     "co120 CO-120.2 `snapshot_declared`/`snapshot_rows`（P5 + 牙齿）"],
        "closed_by": ["CO-152"],
    },
    {
        "finding": "tool_defect:co120_pin_scope_omits_sha16_snapshot_keys",
        "kind": "TOOL_DEFECT", "severity": "low",
        "what": "co120 P1 正则仅抽 `\"<x>_record\"` 键 ⇒ 记录内 `*_sha16` / `*_sha16_after` 快照字段**不在闸覆盖内**"
                "（CO-108/CO-114 F-6 盲区的另一半；CO-151 F-1b）。另：EXEMPT 注册表声明 10 条而闸实测 9 条"
                "（`co110←co109_record` 的 pin 已与现行一致 ⇒ 多余登记；CO-151 F-7），且 co111/co118 两条"
                "点名义依据不可机判。",
        "refs": ["CO-151", "CO-152", "CO-108", "CO-114", "CO-120"],
        "disposition": "CO-152 硬化 co120 → **CO-120.2**：① 新增 P5『下游快照声明册』（`*_sha16_after` 未声明即 "
                       "FAIL_UNDECLARED_DOWNSTREAM_SNAPSHOT，负控/正控牙齿各 1）；② EXEMPT 增补 `exemption_basis` "
                       "分级：`board_superseded`（被引记录声明板 ≠ 交付板 ⇒ **机判可证**，4 条）/ "
                       "`declared_historical`（无板级依据 ⇒ 计数明示不静默，5 条）；依据不成立即 FAIL_EXEMPTION_BASIS；"
                       "③ 删除多余豁免（co110←co109）。复核：verdict PASS（snaps=8 / undeclared=0 / basis_not_ok=0）。",
        "status": "CLOSED", "next": "新增 `*_sha16_after` 记录须在 SNAPSHOT_DECLARED 声明；新豁免须择一 basis 类并成立。",
        "evidence": ["CO-151 记录（F-1b / F-7）", "co120 CO-120.2：`snapshot_rows` / `exemption_basis` / `teeth`"],
        "closed_by": ["CO-152"],
    },
    {
        "finding": "tool_defect:record_derived_value_semantics_unlabeled",
        "kind": "TOOL_DEFECT", "severity": "low",
        "what": "三处记录内**派生物语义未标注**、易致误读（CO-151 F-4/F-5/F-6）：① 热板侧路线以**表征参数 ψJB** "
                "作加性热阻，且「两路线互校差 1.0%」措辞暗示独立证据（实为复用手册 ψJB + 声明 h）；"
                "② PDN 记录字段 `n_plane_vias` 实为**全网 net via 计数**（P3V3 41 / P3V3_AUX 12），非 zone 内净匹配"
                "（本件独立复算 35 / 5），口径未声明；③ 阻抗表称「两套**独立**闭式交叉核对」，而 M1 实为 SPEC "
                "`dielectric_8l_basis` 同式同输入的一阶复现（**非独立**），真正独立者仅 M2。",
        "refs": ["CO-151", "CO-152", "CO-149", "CO-146"],
        "disposition": "CO-152 逐项标注/披露（**不改判据/阈值/结论**）：① CO-149 增 `sensitivity` 块（ψJB↔RθJB 模型"
                       "选择所需 h：[8.15,16.38]→[8.29,16.99]，更保守 +3.4%；h 声明值敏感度：h=8.0 覆盖 0/4、"
                       "h=8.5 覆盖 1/4、h=16 覆盖 3/4）+ 牙齿 t04/t05；文档 §1 改称『一致性核对（非独立证据）』；"
                       "② CO-146 PM 评估增 `n_plane_vias_basis` 与 `method.via_count` 口径声明；"
                       "③ CO-146 阻抗表 nature/docstring 改为『M1 复现 SPEC 一阶 + M2 单一独立模型交叉核对』。"
                       "另：CO-147 R2 `as_built_edge_mm` 0.3294→**0.2577**（全量最劣，CO-151 F-2 medium）与 "
                       "R3 叙述 0.0065→**0.0205**mm（F-3）一并勘误（属 L2 裁定件勘误，不在登记簿 scope，见 boundary §28）。",
        "status": "CLOSED", "next": "记录中凡「派生/计数/模型」字段须自带口径或依据标注（不得留白致误读）。",
        "evidence": ["CO-151 记录（F-2..F-6）",
                     "co149 CO-149.2：`sensitivity` + teeth t04/t05；co146 PM 评估：`n_plane_vias_basis`；"
                     "co146 阻抗表：nature 标签；co147：`as_built_edge_basis`"],
        "closed_by": ["CO-152"],
    },
]
MARK = ("；**CO-152（L2 自裁 · CO-151 findings 处置）**：3 项 TOOL_DEFECT 登记并 CLOSED（记录内嵌下游快照致 pin 漂移 / "
        "co120 pin 覆盖面缺 *_sha16 快照键 + 豁免依据分级 / 派生物语义未标注）；并勘误 CO-147 R2 最劣值 0.2577 与 "
        "R3 叙述 0.0205（见 boundary §28）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"] for i in reg["items"]}
    added = []
    for it in ITEMS:
        if it["finding"] not in have:
            reg["items"].append(it)
            added.append(it["finding"])
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} items (total {len(reg['items'])}), counts={reg['meta']['counts']}")
    print("sha16:", s16(REG))
    return 0


if __name__ == "__main__":
    sys.exit(main())
