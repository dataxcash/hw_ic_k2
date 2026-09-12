#!/usr/bin/env python3
"""CO-167 — CO-166 复评 findings（F-1..F-6）处置（executor · L2 自裁 · 收敛判据加固）。

性质：只改**登记簿**（L2 政策层）；判据由同 CO 的源改动承载：
  `p3_v57_co164_order_runner.py`（序解析 fail-closed / `record_refreshed` 变更检测 / t07 verdict 语义 / t09 受控集 / t10 刷新灵敏度）
  `p3_v57_co146_jlc_fab_package.py`（t09 有锚正则 + 柔性空白 + 容差邻域 ⇒ CO146-PKG.5）
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co167_co166_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co166:{}"
ITEMS = [
 {"id": "F-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**t06 序解析陈旧回落（fail-open）**：`boundary_order_steps()` 取「最后一条**含字面子串** `规范复现序 =` 的行」解析序。"
          "若更新的 R-COxxx-3 行改用别样措辞（如 `规范复现序（步骤集不变）= …`），该行不含该子串 ⇒ 解析器**回落到更旧的 R-CO165-3 行**，"
          "判 `t06=True` ⇒ 文档实际最新序与执行器 `ORDER` 不一致却报一致。",
  "disposition": "CO-167：`boundary_order_steps()` 增 fail-closed 判据 —— 若**最后一 条可解析序行之后**仍有其它 `规范复现序` 提及（措辞/格式变更的新式写法）⇒ 返回 []（**禁止回落到更旧序行**）。",
  "status": "CLOSED", "next": "新增/改写 R-COxxx-3 序行必须保持 `规范复现序 = ` 可解析式样；否则 runner `--check` t06 立即 FAIL。",
  "evidence": ["CO-166 P4 负控：注入措辞变更的新序行 ⇒ `stale_fallback_still_matches_order=True`（旧判据 fail-open）",
               "CO-167 复核：同注入下 `boundary_order_steps()` 返回 [] ⇒ t06=False（fail-closed）；真 boundary 仍 == ORDER"],
  "refs": ["CO-166", "CO-167", "CO-164"], "closed_by": ["CO-167"]},
 {"id": "F-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**白名单刷新判据用绝对 mtime（fail-open）**：白名单「记录由本次执行产出」用 `st_mtime >= t0-1.0`。"
          "若盘上记录 mtime 因时钟回拨/网络盘/异机写入而落在**未来**，则**崩溃（未重写记录）**的白名单步仍被判 `expected_nonzero`。",
  "disposition": "CO-167：新增纯判据 `record_refreshed(before, after)`（步前/步后捕获 exists + mtime_ns + 内容 sha16），"
                 "以**变更检测**替代绝对时间比较（与时钟无关）；`--check` 增 t10（拒未重写的陈旧记录，含未来 mtime）。",
  "status": "CLOSED", "next": "白名单步的「本次产出」证据一律用变更检测；若文件系统 mtime 粒度不足，记录须由步内显式重写。",
  "evidence": ["CO-166 P5 负控：未来 mtime ⇒ 旧判据 `old_predicate_says_fresh=True` 且 `allowlist_decision=expected_nonzero`（fail-open）",
               "CO-167 复核：`record_refreshed` 对「mtime/sha 均不变」与「记录消失」均判 False；t10=True"],
  "refs": ["CO-166", "CO-167", "CO-165"], "closed_by": ["CO-167"]},
 {"id": "F-3", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**白名单记录 ⊆ 受控集无牙齿**：R-CO165-2 只声明「新增产物须落入 `watch_paths()`」，但无判据断言 "
          "`EXPECTED_NONZERO[*].record ⊆ watch_paths()`。当前 DFM 记录恰在 `m13_v57_co*.json` glob 内（无即时暴露），"
          "未来白名单项若指向 glob 外件（如 `.archer_tmp/`）则其抖动/2-循环对收敛判定不可见。",
  "disposition": "CO-167：runner `--check` 增 **t09**（白名单记录 ⊆ `watch_paths()`）；新增白名单须同步受控集。",
  "status": "CLOSED", "next": "新增白名单项须确保其 record 路径在 `watch_paths()` 覆盖范围内。",
  "evidence": ["CO-166 P3：`records_subset_of_watched_now=True` 但 t07/t08 均未断言（无 t09）",
               "CO-167：t09=True（DFM 记录 ⊆ 受控集）"],
  "refs": ["CO-166", "CO-167", "CO-165"], "closed_by": ["CO-167"]},
 {"id": "F-4", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**t09 无锚子串（false-accept）**：`binding_param_checks` 用**无锚子串**命中 —— 备注写 `185Ω`/`11.6 mm` 亦分别命中 `85Ω`/`1.6 mm`；"
          "且 `tolerance` 记号 `±10%` 可被**厚度公差** `（公差 ±10%）` 满足 ⇒ 阻抗容差漂移（85Ω 差分 ±5%）在备注里静默通过。",
  "disposition": "CO-167：记号改**有锚正则**（数值前缀 `(?<![0-9.])` + 后缀 `(?![0-9])`），且 `tolerance` 须在 **zdiff 记号邻域**（40 字符内）命中；"
                 "打样包升 **CO146-PKG.5**。",
  "status": "CLOSED", "next": "凡「客户可见文字 ↔ 定值」绑定判据一律数值锚定，禁止裸子串。",
  "evidence": ["CO-166 P1：`loose_substr_185_ohm_accepts=True`、`loose_substr_11_6mm_accepts=True`、`tolerance_drift_masked_by_thickness=True`",
               "CO-167 复核：`185Ω`⇒zdiff False；`11.6 mm`⇒thickness False；`85Ω 差分 ±5%`⇒tolerance False；真备注仍 7/7"],
  "refs": ["CO-166", "CO-167", "CO-163"], "closed_by": ["CO-167"]},
 {"id": "F-5", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**t09 措辞敏感（fail-closed 噪声）**：`1.6mm`（无空格）/`外层1oz`/`85 Ω` 即令 t09 失败——虽然备注语义正确。"
          "把「备注排版」与「定值漂移」混为一类。",
  "disposition": "CO-167：记号正则允许**柔性空白**（数字↔单位边界 `\\s*` + 字面空格 `\\s*`）⇒ 仅当**值**漂移才失败。",
  "status": "CLOSED", "next": "判据区分「值漂移」（须 FAIL）与「排版差异」（不应 FAIL）。",
  "evidence": ["CO-166 P1：`wording_trips=['thickness','outer_copper','zdiff']`",
               "CO-167 复核：`1.6mm`/`外层1oz`/`85 Ω` 均 7/7 通过；值漂移仍 FAIL"],
  "refs": ["CO-166", "CO-167", "CO-163"], "closed_by": ["CO-167"]},
 {"id": "F-6", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**白名单 expected verdict 未被禁 PASS（单点信任）**：t03/t07 只断言「步骤在序内」+「条目含 verdict/record」，"
          "不禁止把 expected `verdict` 写成 `PASS`（与 rc≠0 自相矛盾），亦无机制把声明 verdict 绑到独立来源。",
  "disposition": "CO-167：`allowlist_decision` 增判据（expected verdict 为 `PASS` ⇒ `expected_verdict_pass_forbidden` 并停机）；"
                 "t07 增 `all(verdict != 'PASS')`。",
  "status": "CLOSED", "next": "新增白名单项须登记期望 verdict（非 PASS）并由 t07 覆盖；禁以白名单「豁免」成功步。",
  "evidence": ["CO-166 P3：`verdict_PASS_permitted_by_tooth=True`（无判据禁止 PASS）",
               "CO-167 复核：`allowlist_decision(...,'PASS',True)='expected_verdict_pass_forbidden'`；t07=True"],
  "refs": ["CO-166", "CO-167", "CO-165"], "closed_by": ["CO-167"]},
]
MARK = ("；**CO-167（L2 自裁 · CO-166 findings 处置 + 收敛判据加固）**：F-1 t06 序解析陈旧回落 fail-open ⇒ 末条可解析序行之后仍有 "
        "`规范复现序` 提及即 fail-closed；F-2 白名单刷新用绝对 mtime ⇒ 改 `record_refreshed` 变更检测（exists/mtime_ns/sha）+ t10；"
        "F-3 白名单记录 ⊆ 受控集无牙齿 ⇒ 增 t09；F-4 t09 无锚子串 ⇒ 数值锚定 + 容差邻域（CO146-PKG.5）；F-5 t09 措辞敏感 ⇒ 柔性空白；"
        "F-6 白名单 verdict 未禁 PASS ⇒ `allowlist_decision` + t07 禁之。执行器升 CO-167.1。")


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
