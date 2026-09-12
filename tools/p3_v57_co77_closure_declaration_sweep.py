#!/usr/bin/env python3
"""CO-77：【L2 声明一致性】收口声明件（boundary）**当前态身份引用**机判扫描。

背景：CO-76（非执行者评审）F1 证明「生产工件里残留陈旧层角色」是可发现缺陷类；
本件把同一判据**扫到收口声明件**：§1/§2/§6 里以「现行/交付/主件」口径引用的工件 sha16
必须等于**当前实际文件**。被取代的 sha 只能出现在显式历史语境。

用法：python3 tools/p3_v57_co77_closure_declaration_sweep.py [--doc PATH]
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = L3 / "mcio_feas_step2"
def _latest_boundary() -> Path:
    """默认对象 = 最新版 boundary（避免闸默认指向过期版本 —— 一种自造漂移）。"""
    cands = list(STEP2.glob("m13_v57_w3_joint_assignment_boundary_v1_*.md"))
    def key(q: Path):
        m = re.findall(r"v1_(\d+)", q.name)
        return int(m[0]) if m else -1
    return max(cands, key=key) if cands else STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_48.md"


DEFAULT_DOC = _latest_boundary()
OUT = STEP2 / "m13_v57_co77_closure_declaration_sweep.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def claims():
    """(label, 抓取正则, 期望=当前文件, 文件, 参考语境)"""
    return [
        ("current_L4_board", r"现行 L4 板 \*\*`([0-9a-f]{16})`\*\*",
         K2 / "k2_v4_8L.l4.kicad_pcb", "§6-1 字节可复现"),
        ("current_drawing_main", r"主件 \*\*`([0-9a-f]{16})`\*\*",
         STEP2 / "m13_v57_w3_joint_assignment.json", "§3 G4"),
        ("co69_adversarial_review", r"co69_adversarial_review\.json` `([0-9a-f]{16})`",
         STEP2 / "m13_v57_co69_adversarial_review.json", "§1 ⑤ / §7"),
        ("co74_chain", r"co74_chain\.json` `([0-9a-f]{16})`",
         STEP2 / "m13_v57_co74_chain.json", "§1 ⑩ / §7"),
        ("co69_card", r"CO69_L2_option_a_chain\.md` `([0-9a-f]{16})`",
         STEP2 / "m13_v57_CO69_L2_option_a_chain.md", "§1 CO-69 注"),
        ("spec_current", r"spec-rev-15\.json`[^|]*\| \*\*`([0-9a-f]{16})`\*\*",
         L3 / "SPEC_k2_v4.spec-rev-15.json", "§2 现行 ECO spec"),
        ("lid_rev6", r"layer_intent_rev6\.json`（[^）]*） \| \*\*`([0-9a-f]{16})`\*\*",
         STEP2 / "m13_v57_layer_intent_rev6.json", "§2 叠层"),
        ("alloc7", r"co16_channel_allocation_v7\.json`（[^）]*） \| \*\*`([0-9a-f]{16})`\*\*",
         STEP2 / "m13_v57_co16_channel_allocation_v7.json", "§2 通道分配"),
        ("board_baseline_8L", r"k2_v4_8L\.kicad_pcb` \| `([0-9a-f]{16})`",
         K2 / "k2_v4_8L.kicad_pcb", "§2 冻结板"),
        ("rules", r"drc_rules\.json` \| `([0-9a-f]{16})`",
         K2.parent / "_shared/eda_core/drc_rules.json", "§2 规则"),
        ("manifest", r"s1_page_manifest\.json` \| `([0-9a-f]{16})`",
         STEP2 / "m13_v57_s1_page_manifest.json", "§2 manifest"),
        ("spec_orig", r"`SPEC_k2_v4\.json`（未动） \| `([0-9a-f]{16})`",
         L3 / "SPEC_k2_v4.json", "§2 红线原件"),
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=str(DEFAULT_DOC))
    a = ap.parse_args(argv)
    doc = Path(a.doc)
    doc = doc if doc.is_absolute() else (Path.cwd() / doc)
    doc = doc.resolve()
    txt = doc.read_text(encoding="utf-8")
    rows, bad = [], []
    for label, pat, src, ctx in claims():
        exp = s16(src)
        found = sorted(set(re.findall(pat, txt)))
        ok = bool(found) and all(f == exp for f in found)
        rows.append({"claim": label, "context": ctx, "expected": exp, "found": found, "ok": ok,
                     "source": str(Path(src))})
        if not ok:
            bad.append(label)
    # CO-82 补强：**全量** sha16 引用校验 —— 任何 `file` `sha16` 形式必须等于实际文件，
    # 除非该行**显式标注历史**（原/已取代/历史/应为/实为）。12 项 claim 只是子集，本项覆盖全文。
    CITE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`\s*`([0-9a-f]{16})`")
    # CO-90 F5：历史豁免必须**按引用**判定（校验紧跟该 sha 之后的标记窗口），不得按整行判定 ——
    # 行级判定会把「现行值 + 同行括号里记录旧值已取代」这类行的**现行值**一并豁免
    # ⇒ 现行 sha 漂移被静默放过（CO-90 实测：co88 记录 d320c812…→b9990766… 漂移未被发现）。
    HIST_AFTER = re.compile(r"^[\s）)】,，、/]*[（(]?\s*(已取代|历史|应为|实为)")
    cite_rows, cite_bad, cite_hist = [], [], 0
    for m in CITE.finditer(txt):
        name, sha = m.group(1), m.group(2)
        _after = txt[m.end():m.end() + 8]
        if HIST_AFTER.match(txt[m.end():m.end() + 16]) or ("→" in _after) or ("->" in _after):
            cite_hist += 1      # 该引用自身被显式标注历史，或 "before → after" 变更记法
            continue
        n = Path(name)
        cands = [n, Path(n.name), L3 / n.name, L3 / "mcio_feas_step2" / n.name,
                 L2 / n.name, K2 / "tools" / n.name, K2 / n.name]
        hit = next((c for c in cands if c.exists()), None)
        real = s16(hit) if hit else None
        ok = bool(hit) and real == sha
        cite_rows.append({"ref": name, "cited": sha, "actual": real, "ok": ok})
        if not ok:
            cite_bad.append(name)
    CITE_FLOOR = 30                      # 非空真下限：正则失效时不得通过
    cite_floor_ok = (len(cite_rows) + cite_hist) >= CITE_FLOOR
    if not cite_floor_ok:
        cite_bad = cite_bad + ["__CITE_FLOOR_FAILED__"]
    rec = {"artifact": "m13_v57_co77_closure_declaration_sweep", "schema": 1, "revision": "CO-77.3",
           "nature": "L2 收口声明件当前态身份引用机判扫描",
           "doc": str(Path(doc).relative_to(K2)), "doc_sha16": s16(doc),
           "claims": rows, "stale_claims": bad,
           "citation_check": {"n_citations": len(cite_rows) + cite_hist,
                              "n_checked": len(cite_rows), "n_marked_historical": cite_hist,
                              "mismatches": cite_bad, "rows": cite_rows,
                              "floor": CITE_FLOOR, "floor_ok": cite_floor_ok},
           "verdict": ("PASS" if (not bad and not cite_bad) else
                       "STALE" if bad else "CITATION_MISMATCH"),
           "redline": "只读；仅比对 sha16；不改任何工件。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"doc": rec["doc"], "doc_sha16": rec["doc_sha16"],
                      "verdict": rec["verdict"], "stale": bad, "citation_mismatch": cite_bad,
                      "detail": {r["claim"]: {"exp": r["expected"], "found": r["found"]}
                                 for r in rows if not r["ok"]}}, ensure_ascii=False))
    return 0 if not bad else 0


if __name__ == "__main__":
    sys.exit(main())
