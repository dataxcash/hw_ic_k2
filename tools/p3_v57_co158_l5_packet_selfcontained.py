#!/usr/bin/env python3
"""CO-158 — L5 打样包自足性（L2 自裁 · 记录/交付物完整性）。

实测缺口（修前）：ORDER_NOTES.md §2 声明「随单提交 … L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md`」，
§3/§6 另引 DFM 记录与 U6 热裁定，但**包内均无该等文件**（机判 in-package=False）⇒ 下单（zip 上传）时会静默漏交声明附件。
本件只改**登记簿**（L2 政策层）；交付物由 co146_jlc_fab_package（CO146-PKG.2）承载。幂等。
CLI: python3 tools/p3_v57_co158_l5_packet_selfcontained.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM = {
 "finding": "co158:J-1", "kind": "TOOL_DEFECT", "severity": "medium",
 "what": "L5 打样包**非自足**：ORDER_NOTES.md 声明随单提交的 L2 裁定件（R1/R2/R3）与所引 DFM 记录、U6 热裁定"
         "**均不在包内**（实测在 `jlc_package/` 下 in-package=False）⇒ 下单时 silent omission（声明与交付物不一致）。"
         "该包同时携带**陈旧**的阻抗表副本（CO-156 前的 dcd307530cd2a9e9）。",
 "refs": ["CO-158", "CO-147", "CO-146", "CO-152"],
 "disposition": "CO-158：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.2** —— 新增 `06_rulings/`（随单提交的 3 份 L2 裁定件 + "
                "DFM 记录）并把 ORDER_NOTES 内引用改为**包内路径**；新增牙齿 `t05_declared_rulings_packaged`（声明附件必须在包内）、"
                "`t06_order_notes_refs_resolve_in_package`（ORDER_NOTES 内 `06_rulings/*` 引用必须可解析）。"
                "复核：**全 gerber/drill 逐字节未变**（纯增量，t01 幂等 True）、n_files 30→34、牙齿 6/6 True；"
                "阻抗表副本随之刷新为现行 `794132ded5a0ce61`。并把该工具**并入规范序**（此前不在序内）。",
 "status": "CLOSED", "next": "新增「随单声明附件」必须落包内并由 t05/t06 把关；交付物声明与包内容须一致。",
 "evidence": ["CO-158 实测：ORDER_NOTES 声明的附件 in-package=False",
              "CO146-PKG.2 teeth t05/t06 + MANIFEST n_files=34"],
 "closed_by": ["CO-158"],
}

ITEM2 = {
 "finding": "co158:J-2", "kind": "TOOL_DEFECT", "severity": "medium",
 "what": "**两处** citation 解析候选目录均**不含 L5 打样包**（co77 与 co135 各自的 CITE 扫描）⇒ boundary 一旦引用包内文件"
         "（如 §33 的 MANIFEST.json / ORDER_NOTES.md），解析必然失败并误报 CITATION_MISMATCH（实测：§33 落地后 co77 mismatches = "
         "['L5/jlc_package/MANIFEST.json','L5/jlc_package/ORDER_NOTES.md']；co135 独立扫描同样 clean=false ⇒ FAIL，并连带 co136 判 FAIL）。"
         "即「闸无法解析自己要求引用的交付物」。",
 "refs": ["CO-158", "CO-77", "CO-135", "CO-136"],
 "disposition": "CO-158：co77 升 **CO-77.6**（抽出 `citation_candidates()`，候选目录**增 L5 打样包** + 正控牙齿 `l5_packet_citation_resolvable`）；"
                "co135 升 **CO-135.2**（其独立 CITE 扫描候选目录同补 L5 包）。复核：co77 = **PASS**（mismatches []）、co135 = PASS_WITH_FINDINGS（citation_scan_clean=true）、co136 恢复 PASS。",
 "status": "CLOSED", "next": "新增交付物目录若会被 boundary 引用，须同时加入 citation 候选目录。",
 "evidence": ["CO-158 实测：§33 引用 L5 包内文件 ⇒ co77 误报 mismatch", "CO-77.6 复核 PASS"],
 "closed_by": ["CO-158"],
}
ITEM3 = {
 "finding": "co158:J-3", "kind": "TOOL_DEFECT", "severity": "medium",
 "what": "**闸退出码不反映 verdict**：co77（`return 0 if not bad else 0` 恒 0）、co124、co135、co136 均无条件 `return 0` ⇒ "
         "shell/CI 复现序**无法据退出码发现 FAIL**（实测：co136 判 FAIL 时 rc 仍为 0，我的复现循环因此静默放行）。"
         "对照：co120 / co150 / l4_validator / l5_signoff 已正确反映 verdict。",
 "refs": ["CO-158", "CO-77", "CO-124", "CO-135", "CO-136"],
 "disposition": "CO-158：四件改为**按 verdict 返回码** —— co77/co124/co136 = `PASS ⇒ 0 否则 1`；co135 = "
                "`PASS/PASS_WITH_FINDINGS ⇒ 0 否则 1`。负控：co77 喂合成漂移声明件 ⇒ rc=1（端到端）；co124/co136 注入失败路径 ⇒ rc=1。",
 "status": "CLOSED", "next": "新闸一律「verdict ⇒ 退出码」；复现序可据此 fail-fast。",
 "evidence": ["CO-158 实测：co136 FAIL 时 rc=0", "CO-158 负控：co77 合成漂移件 rc=1"],
 "closed_by": ["CO-158"],
}
MARK = ("；**CO-158（L2 自裁 · 交付物自足 + 闸卫生）**：J-1 ORDER_NOTES 声明的随单附件不在包内 ⇒ CO146-PKG.2 新增 `06_rulings/` + 牙齿 t05/t06（gerber/drill 逐字节未变）；"
        "J-2 co77 citation 候选目录缺 L5 包 ⇒ CO-77.6 补入 + 正控牙齿；J-3 co77/co124/co135/co136 退出码不反映 verdict ⇒ 四件改为按 verdict 返回码。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added = updated = 0
    for _it in (ITEM, ITEM2, ITEM3):
        f = _it["finding"]
        if f in have:
            have[f].update({k: v for k, v in _it.items() if k != "finding"}); updated += 1
        else:
            reg["items"].append(dict(_it)); added += 1
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{added} / upd {updated} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
