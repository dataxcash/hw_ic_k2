#!/usr/bin/env python3
"""CO-160 — CO-159 复评 findings（F-1..F-12）处置（executor · L2 自裁 · 闸与记录卫生）。

性质：只改**登记簿**（L2 政策层）+ 由同 CO 的闸改动承载判据。幂等：按 `finding` 键 upsert；counts 重算。
证据记号化（指 CO/文件，不写记录 sha）——登记簿内不得嵌下游 sha（R-CO152-1）。
CLI: python3 tools/p3_v57_co160_co159_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co159:{}"
ITEMS = [
 {"id": "F-1", "sev": "medium",
  "what": "CO-156 的 `declared` 值-证据绑定可被「省略 `computed`」绕过（`_contains(ev,{})` 恒真）。",
  "disposition": "CO-160：co124 declared 分支增「`computed` 须非空」判据 + 负控 `T15c_declared_empty_computed_teeth`；"
                 "co124 牙齿 29→33、verdict PASS。",
  "next": "declared 派生值必须给非空 `computed` 且与证据件 key_path 递归一致。", "closed_by": ["CO-160"]},
 {"id": "F-2", "sev": "medium",
  "what": "CO-156 的 `conservative_ge` 权威交叉校验仅在权威 DV 存在时生效（缺 DV 即静默跳过，F-7 原规避复活）。",
  "disposition": "CO-160：co124 conservative_ge 分支在 `DV-INTPAIR-EDGE`/`DV-PAIR-CROSS` 权威字段缺失时显式 FAIL"
                 "（`why=authoritative_dv_missing`）+ 负控 `T16c_authoritative_dv_missing_teeth`。",
  "next": "九 DV 齐备为 K9 前提；权威 DV 缺失不得静默降级。", "closed_by": ["CO-160"]},
 {"id": "F-3", "sev": "medium",
  "what": "CO-157 的 T18 元牙齿只比对「合成电池触发集 == 声明表」，源码新增的条件分支 finder（电池未触发）可绕过。",
  "disposition": "CO-160：co124 增 `T18d_k9_finder_ids_source_complete`（源码正则抽取 finder id 集 == `K9_FINDER_IDS`）"
                 "+ `T18e_k9_finder_id_extractor_sensitivity`（抽取器灵敏度负控，探测串拼接构造以避免自匹配）。",
  "next": "新增/改 K9 判据须同步 `K9_FINDER_IDS`，否则 T18d 立即 FAIL。", "closed_by": ["CO-160"]},
 {"id": "F-4", "sev": "medium",
  "what": "R-CO156-3「禁整表重写」无机判；co136 `H4_ledger_upsert_only` 只拦「未读即写」（读后整表重写放行）。",
  "disposition": "CO-160：**对齐规则文本与机判面** —— boundary §34 记明 R-CO156-3 的机判面 = co136 H4（未读即写）+ CO-156 co134 stub 复跑证据；"
                 "「整表重写」语义面无自动判据，由复评/登记承接（不引入会误伤 co134 式「读-合并-写」合法 upsert 的脆弱语法判据）。",
  "next": "新增台账写者须先读台账；整表重写须在 boundary 显式说明并由复评核对。", "closed_by": ["CO-160"]},
 {"id": "F-5", "sev": "low",
  "what": "co120 下游快照键判据依赖嵌套容器；顶层/其它容器下 `register_sha16`/`open_total` 等漏判（当前 0 live 例）。",
  "disposition": "CO-160：co120 增**键名面**判据 `_DOWNSTREAM_KEY_RE`（`*_sha16_after` ∪ `register|ledger[_…]_sha16|items_total|open_total|n_items`）"
                 "+ 负控（顶层 `register_sha16` 必抓）/正控（`register_sha16_note` 不得误报）；co120 升 CO-120.5。",
  "next": "下游快照键一律须在 SNAPSHOT_DECLARED 声明，与嵌套位置无关。", "closed_by": ["CO-160"]},
 {"id": "F-6", "sev": "low",
  "what": "co120 `board_superseded` 为格式判：任意 16-hex（`0000…`/`deadbeef…`）即成立豁免，未与真实被取代板比对。",
  "disposition": "CO-160：co120 增 `SUPERSEDED_BOARDS` 注册表（`a3ce9ab803045a0a` = CO-144 重建前板，见 co88/co99/co137/co138/co140-143）"
                 "并要求成员资格 + 伪造 sha 负控 `negative_control_unregistered_board_sha_rejected`。",
  "next": "新增 `board_superseded` 豁免须先把被取代板 sha16 登记进注册表（可比对）。", "closed_by": ["CO-160"]},
 {"id": "F-7", "sev": "medium",
  "what": "**R-CO158-3 对 `co146_jlc_dfm_gate` 不成立**：verdict=FAIL（DFM 两项阻塞）时 rc 仍 0，复现序无法 fail-fast；J-3 修复清单遗漏此件。",
  "disposition": "CO-160：`return 0 if (rec[\"verdict\"]==\"PASS\" and teeth_ok and teeth2_ok) else 1`；实测 DFM FAIL ⇒ rc=1（记录逐字节不变）。"
                 "handoff §6 该行注记订正为「rc=1 属预期」。",
  "next": "凡 verdict 可为 FAIL 的规范序闸，rc 必须非 0。", "closed_by": ["CO-160"]},
 {"id": "F-8", "sev": "low",
  "what": "L5 打样包 `06_rulings/` 副本无「与来源一致」牙齿（来源修订后包内陈旧副本无回归保护；J-1 同类已实测发生）。",
  "disposition": "CO-160：`co146_jlc_fab_package` 升 **CO146-PKG.3**，增 `t07_packaged_rulings_match_sources`（包内副本 sha256 == 来源）"
                 "+ `t07b_parity_detector_sensitivity`。",
  "next": "随单附件副本须与来源同字节；来源变更即须重跑打包。", "closed_by": ["CO-160"]},
 {"id": "F-9", "sev": "low",
  "what": "ORDER_NOTES 目录级声明（`01_`..`06_`，如「叠层图(03_) + 阻抗表(04_)」）不在 t06 覆盖内。",
  "disposition": "CO-160：CO146-PKG.3 增 `t08_declared_dirs_present`（声明目录须在包内）。",
  "next": "声明与包内容一致性覆盖到目录级。", "closed_by": ["CO-160"]},
 {"id": "F-10", "sev": "low",
  "what": "CO-158 把 L5 包补进 co77 **与** co135 **各自**的 citation 候选表；两表已现分歧面（co77 多 container-parent `_shared`）且无一致性牙齿。",
  "disposition": "CO-160：**保留两份独立实现**（独立复评价值），co135 升 **CO-135.3** 增交叉一致性判据 `candidate_tables_agree`"
                 "（逐引用比对 co77 的 `citation_candidates()`，分歧即 FAIL）。",
  "next": "两候选表须逐引用一致；任一侧补目录须同步或将差异显式登记。", "closed_by": ["CO-160"]},
 {"id": "F-11", "sev": "medium",
  "what": "handoff §6 复现块内回归闸 co78/co81/co84/co95/co98/co106 退出码恒 0，不反映 verdict（co98 为三态报告，须按 baseline_ok+teeth_ok）。",
  "disposition": "CO-160：六件改为按各自 verdict/基线谓词返回（co78 含 teeth_ok；co98 = `baseline_ok and teeth_ok`）；"
                 "升版 CO-78.2/CO-81.2/CO-84.2/CO-95.2/CO-98.2/CO-106.3；co95 记录变更后 co98 基线 pin 同步刷新；实测全 rc=0。",
  "next": "复现序内所有闸一律「verdict/基线 ⇒ 退出码」。", "closed_by": ["CO-160"]},
 {"id": "F-12", "sev": "low",
  "what": "co135 复评件内嵌 CO-134 时点硬编码链 pin（`0074dad9067af737` 等）与硬编码 boundary 文件名 `v1_82.md` ⇒ 记录随序陈旧、改名即静默失配。",
  "disposition": "CO-160：co135 链 pin 改为由现行记录派生（G4/G5/L4val + co124/co95/co98 现行 verdict），boundary 取最新版（与 co77 同口径）。",
  "next": "记录内的现行态链 pin 须可重算或显式标注历史；不得硬编码文件名。", "closed_by": ["CO-160"]},
]
MARK = ("；**CO-160（L2 自裁 · executor · CO-159 复评处置）**：F-1 declared 非空 computed / F-2 权威 DV 缺失显式 FAIL / "
        "F-3 T18d+T18e 源码 finder 覆盖 / F-4 R-CO156-3 机判面口径对齐 / F-5 快照键名面判据 / F-6 SUPERSEDED_BOARDS 白名单 / "
        "F-7 DFM 闸 rc 反映 verdict / F-8 t07 副本来源一致性 / F-9 t08 目录级声明 / F-10 co135↔co77 候选表交叉一致性 / "
        "F-11 六件回归闸 rc 反映 verdict / F-12 co135 链 pin 与 boundary 取最新 —— 全部 CLOSED ⇒ 登记簿 OPEN 0。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = {"kind": "TOOL_DEFECT", "severity": it["sev"], "disposition": it["disposition"],
                 "status": "CLOSED", "next": it["next"], "closed_by": it["closed_by"],
                 "refs": ["CO-159", "CO-160", "CO-156", "CO-157", "CO-158"],
                 "evidence": [f"CO-159 复评件（{it['id']}，as-found @ c4e951c）", "CO-160 复核：co124/co120/co135/co136 牙齿与 rc"]}
        if "what" in it:
            patch["what"] = it["what"]
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
