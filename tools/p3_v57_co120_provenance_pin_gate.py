#!/usr/bin/env python3
"""CO-120：【L2 过程闸】记录内 **inter-record provenance pin** 一致性闸（关闭 CO-108/CO-114 **F-6 盲区**）。

背景（F-6 根因）：CO-77 只校验**收口声明件（boundary）**里的 `file`+`sha16` 引用；**记录内部**的
`*_record` / `inputs.*` provenance pin（指向上游记录版本）**无闸覆盖** ⇒ rev 重基线后上级记录 pin 陈旧
也不会被发现（CO-114 实测 co109←co106 / co110←co106 / co110←co87）。

本闸判据（机判、零搜索）：
  P1 扫描 STEP2 下全部 `m13_v57_co*.json`，抽取形如 `"<x>_record": "<sha16>"` 的 pin；
  P2 由 key 前缀解析被引记录文件（`m13_v57_<x>*.json`，唯一命中）；解析唯一性不足者记 `unresolved_key`（不计失败）；
  P3 现行 pin 必须等于被引文件**当前** sha16；不等 ⇒ 必须是**已声明豁免**（`EXEMPT` 注册表：记录本体已被后续 CO 取代、
      pin 属历史，理由明文）；
  P4 牙齿：注入一个**未声明**的陈旧 pin 必须被判 FAIL（负控）；注入匹配 pin 必须 PASS（正控）。
只读；不改任何工件。CLI: python3 tools/p3_v57_co120_provenance_pin_gate.py
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co120_provenance_pin_gate.json"
PIN = re.compile(r'"([a-z0-9_]*(?:record|_record))"\s*:\s*"([0-9a-f]{16})"')
# 已声明豁免：{被引记录文件: {pin_key: 理由}} —— 仅限「记录本体已被后续 CO 取代 ⇒ pin 属历史」
EXEMPT = {
    "m13_v57_co109_in4_void_l2_ruling.json": {"co106_record": "CO-109 R2『按设计』已被 CO-115 更正 ⇒ 本记录为历史；pin 属历史"},
    "m13_v57_co111_in5_pcie_corridor_exposure.json": {"l5_si_record": "CO-111 时点 SI 记录；CO-133 施工后 L5 SI 记录随板重跑 ⇒ pin 属历史"},
    "m13_v57_co118_bcu_bridge_conflict_check.json": {"co95_record": "CO-118 的 B.Cu 桥冲突已由 CO-130/CO-132 取代（B.Cu 载体退役 + In4 承载）⇒ 本记录为历史；CO-132 重跑 co95 后 pin 属历史"},
    "m13_v57_co110_l2_coverage_closure.json": {"co106_record": "CO-110 依赖被 CO-115 取代的前提 ⇒ 历史",
                                              "co87_record": "CO-110 时点 co87 版本 ⇒ 历史（co87 已随后续 rev 重跑）"},
    # CO-144（L2 重基线）：CO-140/141 是对 **CO-134 板 a3ce9ab8** 的归因/全量审计（结论驱动 CO-143/144）；
    # 板随 CO-144 重建（76cdf64c）且 co134 记录重派生 ⇒ 其 co134_record pin 属历史。
    "m13_v57_co140_deviation_attribution.json": {"co134_record": "CO-144 重基线前的板 a3ce9ab8 归因 ⇒ 历史（结论已由 CO-144 关闭 B.Cu）"},
    "m13_v57_co141_interpair_conformance_audit.json": {"co134_record": "CO-144 重基线前的板 a3ce9ab8 全量审计 ⇒ 历史（B.Cu 违规已由 CO-144 消除）"},
    "m13_v57_co137_interpair_fixspace.json": {"co134_record": "CO-137 对 CO-134 板 a3ce9ab8 的偏差几何可行性分析 ⇒ 历史（CO-144 已改几何）"},
    "m13_v57_co138_interpair_scope_probe.json": {"co134_record": "CO-138 对 CO-134 板 a3ce9ab8 的耦合几何画像 ⇒ 历史（CO-144 已改几何）"},
}


# F-7（CO-151）：豁免依据分级 —— `board_superseded`（被引记录声明板 ≠ 交付板 ⇒ 机判可证）
# vs `declared_historical`（无板级依据，仅声明为时点记录 ⇒ 本闸计数并明示，不静默接受）。
EXEMPT_BASIS = {
    "m13_v57_co109_in4_void_l2_ruling.json": {"co106_record": "declared_historical"},
    "m13_v57_co110_l2_coverage_closure.json": {"co106_record": "declared_historical",
                                               "co87_record": "declared_historical"},
    "m13_v57_co111_in5_pcie_corridor_exposure.json": {"l5_si_record": "declared_historical"},
    "m13_v57_co118_bcu_bridge_conflict_check.json": {"co95_record": "declared_historical"},
    "m13_v57_co137_interpair_fixspace.json": {"co134_record": "board_superseded"},
    "m13_v57_co138_interpair_scope_probe.json": {"co134_record": "board_superseded"},
    "m13_v57_co140_deviation_attribution.json": {"co134_record": "board_superseded"},
    "m13_v57_co141_interpair_conformance_audit.json": {"co134_record": "board_superseded"},
}
# F-1b（CO-151）：记录内**下游时点快照**（`*_sha16_after`）声明册 —— 未声明者一律 FAIL。
# 缘起：CO-148/147/124/150 曾内嵌 register/ledger/co124 的 sha 快照 ⇒ 记录随运行序漂移、
# 提交 pin 不可由复现序复现。CO-152 移除该 4 件快照，并以本闸禁止复发。
SNAPSHOT_DECLARED = {
    "m13_v57_co68_option_a_execute_derive.json": "历史：lid_rev5/spec_rev4 时点快照，已被 CO-113+ 取代",
    "m13_v57_co72_pdn_align.json": "历史：spec_rev5 时点快照，已被 CO-113+ 取代",
    "m13_v57_co73_layer_role_consistency.json": "历史：spec_rev6 时点快照，已被 CO-113+ 取代",
    "m13_v57_co74_pdn_bcu_rehost.json": "历史：spec_rev7 时点快照，已被 CO-113+ 取代",
    "m13_v57_co80_l4_project_rule_align.json": "历史：l4_project 时点快照（工程文件随后续 rev 重生成）",
    "m13_v57_co82_l4_project_netclass_align.json": "历史：l4_project 时点快照（同上）",
    "m13_v57_co133_pdn_construction_apply.json": "上游稳定：board_sha16_after = 交付板 d4e81f647be7f980（非下游漂移）",
    "m13_v57_co146_jlc_rebind.json": "历史：register 时点快照；CO-152 起同类字段一律禁止，本件留存为历史",
    "m13_v57_co159_rev19_co156_co157_co158_review.json": "CO-159 复评件：`register` 计数取自 as-found 锚点（`git show c4e951c`），"
                                                         "为不可变历史值（非下游时点观测）⇒ 不随运行序漂移",
}
DELIVERED_BOARD = "d4e81f647be7f980"
# CO-157（H-3）：`board_superseded` 的「机判可证」须是**格式可判的板 sha16**，自由文本不算证据。
BOARD_RE = re.compile(r"[0-9a-f]{16}")
# CO-159（F-6）：格式判仍被任意 16-hex（`0000…`/`deadbeef…`）满足 ⇒ 收为**已登记被取代板白名单**（可比对）。
# 登记依据：该 sha 在 co88/co99/co137/co138/co140/co141/co142/co143 记录中一致出现（CO-144 重建前的板）。
SUPERSEDED_BOARDS = {
    "a3ce9ab803045a0a": "CO-144 重建前的 PDN/载体板（B.Cu 载体 + In4 承载改造前）",
}


# CO-156（F-2b）：下游快照键的**通用**判据 —— 除 `*_sha16_after` 外，`register.*` / `ledger.*` 下的
# `sha16*` 与计数键（items_total / open_total / n_items）同属下游时点观测，未声明一律 FAIL。
DOWNSTREAM_CONTAINER = ("register", "ledger")
DOWNSTREAM_COUNT_KEYS = ("items_total", "open_total", "n_items")


# CO-159（F-5）：键名面判据（不再要求嵌在 `register`/`ledger` 容器内）——
# 顶层/其它容器下的 `register_sha16` / `open_total` 等同属规则禁止的下游快照。
_DOWNSTREAM_KEY_RE = re.compile(
    r"^(register|ledger)(_[a-z0-9_]+)?_?(sha16|items_total|open_total|n_items)$")


def _is_downstream_snapshot(path: list, key: str) -> bool:
    k = str(key)
    if k.endswith("sha16_after"):
        return True
    if _DOWNSTREAM_KEY_RE.fullmatch(k):
        return True
    return any(seg in DOWNSTREAM_CONTAINER for seg in path) and \
        (k.endswith("sha16") or k in DOWNSTREAM_COUNT_KEYS)


def scan_snapshots(records: dict) -> list:
    """F-1b / CO-156：扫描下游快照键（sha16_after ∪ register/ledger 下 sha16|计数）；未声明者 = 违规。"""
    rows = []
    for name in sorted(records):
        keys = set()

        def w(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    if _is_downstream_snapshot(path, k):
                        keys.add(".".join(path + [str(k)]))
                    w(v, path + [str(k)])
            elif isinstance(o, list):
                for v in o:
                    w(v, path)
        w(records[name], [])
        if keys:
            rows.append({"record": name, "keys": sorted(keys), "declared": name in SNAPSHOT_DECLARED,
                         "reason": SNAPSHOT_DECLARED.get(name, "")})
    return rows


def basis_of(records: dict) -> list:
    """F-7：逐条复核豁免依据类别是否成立（board_superseded 须机判可证）。"""
    out = []
    for name, pins in EXEMPT.items():
        d = records.get(name)
        if d is None:
            continue
        blob = json.dumps(d, ensure_ascii=False)
        board = (d.get("inputs") or {}).get("board") or d.get("board_sha16") or d.get("board")
        for key in pins:
            cls = (EXEMPT_BASIS.get(name) or {}).get(key, "undeclared")
            ok = ((cls == "board_superseded" and isinstance(board, str) and bool(BOARD_RE.fullmatch(board))
                   and board != DELIVERED_BOARD and board in SUPERSEDED_BOARDS)
                  or (cls == "declared_historical"))
            out.append({"record": name, "key": key, "basis": cls, "basis_ok": ok,
                        "declared_board": board})
    return out


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# 歧义 key 的显式目标（globs 命中 >1；零搜索：显式登记，guarded by 存在性）
PIN_TARGETS = {
    "co95_record": "m13_v57_co95_in4_reachability.json",
}


def resolve(key: str):
    pre = key[:-len("_record")] if key.endswith("_record") else key
    if pre in ("", "record"):
        return None, "unresolved_key"
    if key in PIN_TARGETS:
        f = STEP2 / PIN_TARGETS[key]
        return (f, None) if f.exists() else (None, f"unresolved_key(mapped missing {PIN_TARGETS[key]})")
    cands = sorted(STEP2.glob(f"m13_v57_{pre}*.json")) + sorted(L3.glob(f"m13_v57_{pre}*.json"))
    if len(cands) != 1:
        return None, f"unresolved_key({len(cands)} cands)"
    return cands[0], None


def scan(records: dict) -> list:
    rows = []
    for name, d in records.items():
        for m in PIN.finditer(json.dumps(d)):
            key, cited = m.group(1), m.group(2)
            if key == "record":
                rows.append({"record": name, "key": key, "cited": cited, "actual": None, "status": "unresolved_key"})
                continue
            p, err = resolve(key)
            if err:
                rows.append({"record": name, "key": key, "cited": cited, "actual": None, "status": err})
                continue
            actual = s16(p)
            if actual == cited:
                st = "match"
            elif key in EXEMPT.get(name, {}):
                st = "exempt_historical"
            else:
                st = "STALE"
            rows.append({"record": name, "key": key, "cited": cited, "actual": actual,
                         "resolved": p.name, "status": st})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    records = {}
    for f in sorted(STEP2.glob("m13_v57_co*.json")):
        try:
            records[f.name] = json.loads(f.read_text())
        except Exception:
            continue
    rows = scan(records)
    stale = [r for r in rows if r["status"] == "STALE"]
    unresolved = [r for r in rows if str(r["status"]).startswith("unresolved")]
    # F-1b：下游快照键（未声明 = 违规）
    snaps = scan_snapshots(records)
    snap_undeclared = [s for s in snaps if not s["declared"]]
    # F-7：豁免依据类别机判
    basis = basis_of(records)
    basis_bad = [b for b in basis if not b["basis_ok"]]
    n_decl_hist = sum(1 for b in basis if b["basis"] == "declared_historical")
    # 牙齿（负控/正控，走真实 scan）
    neg = scan({"synthetic_probe.json": {"co95_record": "0" * 16}})
    neg_hit = any(r["status"] == "STALE" for r in neg)
    p95 = STEP2 / "m13_v57_co95_in4_reachability.json"
    pos = scan({"synthetic_probe.json": {"co95_record": s16(p95)}})
    pos_ok = any(r["status"] == "match" for r in pos)
    # 牙齿（P5）：未声明的下游快照键必须被抓；已声明的必须放行
    neg_snap = scan_snapshots({"synthetic_probe.json": {"x_sha16_after": "0" * 16}})
    neg_snap_hit = any(not s["declared"] for s in neg_snap)
    pos_snap = scan_snapshots({k: {"x_sha16_after": "0" * 16} for k in list(SNAPSHOT_DECLARED)[:1]})
    pos_snap_ok = bool(pos_snap) and all(s["declared"] for s in pos_snap)
    snap_ok = neg_snap_hit and pos_snap_ok
    # CO-156（F-2b）：`register.*`/`ledger.*` 下的非 `_after` 下游键（sha16/计数）亦须被抓
    neg_snap2 = scan_snapshots({"synthetic_probe.json": {"register": {"open_total": 3, "sha16": "0" * 16}}})
    neg_snap2_hit = any(not s2["declared"] for s2 in neg_snap2)
    pos_snap2 = scan_snapshots({k: {"register": {"items_total": 1}} for k in list(SNAPSHOT_DECLARED)[:1]})
    pos_snap2_ok = bool(pos_snap2) and all(s2["declared"] for s2 in pos_snap2)
    snap_ok = snap_ok and neg_snap2_hit and pos_snap2_ok
    # CO-157（H-3）负控/正控：`board_superseded` 依据须为板 sha16（自由文本必拒）
    neg_basis = basis_of({"m13_v57_co137_interpair_fixspace.json": {"inputs": {"board": "superseded"}}})
    neg_basis_hit = bool(neg_basis) and not neg_basis[0]["basis_ok"]
    pos_basis = basis_of({"m13_v57_co137_interpair_fixspace.json": {"inputs": {"board": "a3ce9ab803045a0a"}}})
    pos_basis_ok = bool(pos_basis) and pos_basis[0]["basis_ok"]
    # CO-159（F-6）负控：未登记（伪造）的 16-hex 板 sha 不得成立豁免
    fake_basis = basis_of({"m13_v57_co137_interpair_fixspace.json": {"inputs": {"board": "deadbeefdeadbeef"}}})
    fake_basis_hit = bool(fake_basis) and not fake_basis[0]["basis_ok"]
    # CO-159（F-5）负控/正控：顶层（非容器）下游键必须被抓；带 `_note` 后缀的说明键不得误报
    neg_snap3 = scan_snapshots({"synthetic_probe.json": {"register_sha16": "0" * 16}})
    neg_snap3_hit = any(not s3["declared"] for s3 in neg_snap3)
    pos_snap3_ok = scan_snapshots({"synthetic_probe.json": {"register_sha16_note": "说明，非快照"}}) == []
    teeth_ok = (neg_hit and pos_ok and snap_ok and neg_basis_hit and pos_basis_ok
                and fake_basis_hit and neg_snap3_hit and pos_snap3_ok)
    rec = {
        "artifact": "m13_v57_co120_provenance_pin_gate", "schema": 1, "revision": "CO-120.5",
        "nature": "L2 过程闸：记录内 inter-record provenance pin 一致性（关闭 CO-108/CO-114 F-6 盲区）",
        "pins_total": len(rows), "n_match": sum(1 for r in rows if r["status"] == "match"),
        "n_exempt_historical": sum(1 for r in rows if r["status"] == "exempt_historical"),
        "n_stale_undeclared": len(stale), "n_unresolved_key": len(unresolved),
        "stale_undeclared": stale, "unresolved_key": unresolved,
        "exemption_registry": EXEMPT, "superseded_boards": SUPERSEDED_BOARDS,
        "exemption_basis": {"classes": EXEMPT_BASIS, "rows": basis,
                           "n_declared_historical": n_decl_hist,
                           "n_basis_not_ok": len(basis_bad)},
        "snapshot_declared": SNAPSHOT_DECLARED,
        "snapshot_rows": snaps, "n_snapshot_undeclared": len(snap_undeclared),
        "rows": rows,
        "teeth": {"negative_control_undeclared_stale_caught": neg_hit,
                  "positive_control_matching_pin_passes": pos_ok,
                  "negative_control_undeclared_snapshot_caught": neg_snap_hit,
                  "negative_control_register_snapshot_caught": neg_snap2_hit,
                  "positive_control_declared_register_snapshot_passes": pos_snap2_ok,
                  "negative_control_freetext_board_basis_rejected": neg_basis_hit,
                  "negative_control_unregistered_board_sha_rejected": fake_basis_hit,
                  "negative_control_top_level_register_snapshot_caught": neg_snap3_hit,
                  "positive_control_note_key_not_snapshot": pos_snap3_ok,
                  "positive_control_board_sha_basis_accepted": pos_basis_ok,
                  "positive_control_declared_snapshot_passes": pos_snap_ok,
                  "teeth_ok": teeth_ok},
        "verdict": ("FAIL_STALE_PROVENANCE_PIN" if stale else
                    "FAIL_UNDECLARED_DOWNSTREAM_SNAPSHOT" if snap_undeclared else
                    "FAIL_EXEMPTION_BASIS" if basis_bad else
                    "PASS" if teeth_ok else "FAIL(teeth)"),
        "non_claims": ["只读；不改任何记录/SPEC/板/阈值/冻结源",
                       "CO-156（F-2b）：下游快照键 = `*_sha16_after` ∪ `register.*`/`ledger.*` 下的 `sha16*`/`items_total`/`open_total`/`n_items`；"
                       "后者必须在本闸 SNAPSHOT_DECLARED 声明（未声明一律 FAIL）"
                       "（理由：该类快照使记录 sha 随运行序漂移 ⇒ 提交 pin 不可复现）；未声明一律 FAIL",
                       "F-7：豁免依据分 `board_superseded`（机判可证）与 `declared_historical`（无板级依据，计数明示）两类",
                       "CO-159（F-6）：`board_superseded` 的板 sha16 须在 `SUPERSEDED_BOARDS` 白名单（可比对）；未登记 16-hex 一律不成立",
                       "CO-159（F-5）：下游快照键判据为键名面（`*_sha16_after` ∪ `register|ledger[_…]_sha16|items_total|open_total|n_items`），不依赖嵌套容器",
                       "豁免仅限『记录本体已被后续 CO 取代 ⇒ pin 属历史』并在本闸注册表明文；未声明陈旧 pin 一律 FAIL",
                       "pin→文件解析失败（歧义/无候选）记 unresolved_key，不计失败但入记录",
                       "扫描范围（CO-153 声明）：仅 STEP2 下 m13_v57_co*.json 记录的 `*_record` 键；"
                       "台账（L2/derived_value_ledger_v1.json）内 DV 的 reachability.evidence_ref pin "
                       "由 co124 K9 的 declared/process_floor 判据覆盖（CO-153）"],
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"CO-120 verdict={rec['verdict']} | snaps={len(snaps)} undeclared={len(snap_undeclared)} "
          f"basis_not_ok={len(basis_bad)} | pins={len(rows)} match={rec['n_match']} exempt={rec['n_exempt_historical']} stale_undeclared={rec['n_stale_undeclared']} unresolved={rec['n_unresolved_key']} teeth={teeth_ok}")
    for r in stale:
        print("   STALE", r["record"], r["key"], r["cited"], "->", r["actual"])
    with_out = rec["n_exempt_historical"]
    if with_out:
        print("   (exempt historical:", [(r['record'], r['key']) for r in rows if r['status'] == 'exempt_historical'], ")")
    return 0 if rec["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
