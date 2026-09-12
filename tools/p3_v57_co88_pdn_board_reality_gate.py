#!/usr/bin/env python3
"""CO-88：【L2 PDN】live 机读字段的**板实性**机判 + 修复候选派生（只读 + scratch）。

背景：CO-74 逼出「PDN 声明 vs 板现实」这一缺陷类。本件把它机判化：`pd.zone_defs.power_pad_connect`
与 `pd.decoupling(_via_to_plane)` 是**机读、且被 `_shared/eda_core/pdn_apply.py` 消费**的铺铜决策，
若引用板上不存在的器件（红驱动 U3+U7 合并为 U6 后遗留），L3 铺铜会落**幻影 via**。

判据（ch.5 §1 覆盖性 / §2 可追溯性 / §3 可验证性）：
  A. live 字段引用的 ref 必须**存在于交付板**（否则决策不可追溯/不可验证）；
  B. 板上每个 SMD 电源/地 pad 必须**有决策**（entry 覆盖 或 blocked 台账带 reason）；
  C. 解耦决策落点必须在板上。
另派生**修复候选**：用项目自带确定性发生器 `eda_core.pad_connect_gen` 对交付板重生成（scratch 副本，用完即删）。

需 pcbnew ⇒ 用 `AppDir/usr/bin/python3.11`。只读；不改 SPEC/板/阈值；零 while。
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co88_pdn_board_reality_gate.json"
SCRATCH = K2 / ".co88_tmp"
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.pad_connect_gen import DEFAULT_PWR_NETS as PWR_NETS  # noqa: E402


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def current_spec() -> Path:
    cands = list(L3.glob("SPEC_k2_v4.spec-rev-*.json"))

    def key(p: Path):
        m = re.findall(r"rev-(\d+)", p.name)
        return int(m[0]) if m else -1
    return max(cands, key=key)


def board_power_pads(board_path: Path) -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(board_path))
    out = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            if p.GetNetname() in PWR_NETS and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                out[(ref, p.GetNumber())] = p.GetNetname()
    return out


def spec_refs(spec: dict) -> dict:
    zd = spec["pd"]["zone_defs"]
    ppc = zd.get("power_pad_connect", {})
    ent = {str(e.get("ref")) for e in ppc.get("entries", []) if isinstance(e, dict)}
    blk = {str(e.get("ref")) for e in ppc.get("blocked", []) if isinstance(e, dict)}
    dv = zd.get("decoupling_via_to_plane", {})
    vias = {str(v.get("ref")) for v in dv.get("vias", []) if isinstance(v, dict)}
    # 解耦决策集：优先取**结构化** targets（CO-89 起）；vias 为空时不以 prose 串反推 ref（防 P3V3→P3/V3 误抓）
    targets = {str(x) for x in dv.get("targets", []) if isinstance(x, str)}
    dec = str(spec["pd"].get("decoupling", ""))
    return {"entries_refs": ent, "blocked_refs": blk, "decoupling_via_refs": vias | targets,
            "decoupling_string_refs": set(), "decoupling": dec,
            "decoupling_targets": sorted(targets)}


def scratch_regeneration(spec_path: Path) -> dict:
    """用项目自带发生器对交付板重生成 ppc（scratch 副本；用完即删）。返回候选规模。"""
    SCRATCH.mkdir(exist_ok=True)
    cand = SCRATCH / "rev_candidate.json"
    shutil.copy(spec_path, cand)
    r = subprocess.run([sys.executable, "-m", "eda_core.pad_connect_gen",
                        "--spec", str(cand), "--board", str(BOARD)],
                       cwd=str(K2.parent), capture_output=True, text=True, timeout=600,
                       env={**__import__("os").environ, "PYTHONPATH": str(K2.parent / "_shared")})
    if r.returncode != 0:
        return {"ok": False, "stderr_tail": (r.stderr or "")[-200:]}
    d = json.loads(cand.read_text(encoding="utf-8"))
    ppc = d["pd"]["zone_defs"]["power_pad_connect"]
    ent, blk = ppc["entries"], ppc["blocked"]
    from collections import Counter
    u6 = sum(1 for x in blk if x.get("ref") == "U6")
    out = {"ok": True, "entries": len(ent), "blocked": len(blk),
           "blocked_by_ref_top": dict(Counter(x.get("ref") for x in blk).most_common(5)),
           "blocked_U6_share": f"{u6}/{len(blk)}",
           "decisions_total": len(ent) + len(blk), "rule": ppc["rule"][:60]}
    shutil.rmtree(SCRATCH, ignore_errors=True)
    return out


def ripple_checklist() -> list:
    """哪些工具/文件钉住现行 SPEC rev 文件或其 sha（施加 rev-9 需同步 bump 的清单）。"""
    cur = current_spec().name
    hits = []
    for p in sorted((K2 / "tools").glob("*.py")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if cur in t or re.search(r"SPEC_k2_v4\.spec-rev-\d+\.json", t):
            hits.append(p.name)
    return hits


def main() -> int:
    spec_path = current_spec()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    pads = board_power_pads(BOARD)
    refs = spec_refs(spec)
    board_refs = {k[0] for k in pads}
    def orphan_scan(spec_obj: dict) -> dict:
        """判据 A 检测路径（正式判定与牙齿注入测试共用同一实现）。"""
        r = spec_refs(spec_obj)
        return {k: sorted(v - board_refs) for k, v in
                (("entries", r["entries_refs"]), ("blocked", r["blocked_refs"]),
                 ("decoupling_via", r["decoupling_via_refs"]),
                 ("decoupling_string", r["decoupling_string_refs"]))}

    def coverage_scan(spec_obj: dict) -> tuple:
        """判据 B 检测路径（正式判定与牙齿注入测试共用同一实现）。"""
        p_ = spec_obj["pd"]["zone_defs"]["power_pad_connect"]
        c_ = {(str(e["ref"]), str(e["pad"])) for e in p_.get("entries", []) if isinstance(e, dict)}
        bk_ = {(str(e["ref"]), str(e["pad"])) for e in p_.get("blocked", []) if isinstance(e, dict)}
        return ([k for k in pads if k in c_], [k for k in pads if k in bk_],
                sorted(k for k in pads if k not in c_ and k not in bk_))

    def decoupling_ok(spec_obj: dict) -> bool:
        """判据 C 检测路径：解耦目标非空 且 目标/vias 全板实。"""
        r = spec_refs(spec_obj)
        return bool(r["decoupling_targets"]) and not (r["decoupling_via_refs"] - board_refs)

    orphans = orphan_scan(spec)
    ppc = spec["pd"]["zone_defs"]["power_pad_connect"]
    covered, declared_blocked, silent = coverage_scan(spec)
    c_ok = decoupling_ok(spec)
    n_orphan_entries = sum(1 for e in ppc.get("entries", []) if str(e.get("ref")) not in board_refs)
    n_orphan_blocked = sum(1 for e in ppc.get("blocked", []) if str(e.get("ref")) not in board_refs)

    # 牙齿（CO-90 F2 加固）：阳性对照必须**真跑检测路径**；原实现 "bool({"U99"} - board_refs)" 恒真（仅查板 ref，未运行检测器）。
    syn_orphan = json.loads(json.dumps(spec))
    syn_orphan["pd"]["zone_defs"]["power_pad_connect"]["entries"].append(
        {"ref": "U99", "pad": "1", "net": "GND"})
    syn_silent = json.loads(json.dumps(spec))
    syn_silent["pd"]["zone_defs"]["power_pad_connect"]["entries"].pop(0)
    syn_dec_empty = json.loads(json.dumps(spec))
    syn_dec_empty["pd"]["zone_defs"]["decoupling_via_to_plane"]["targets"] = []
    syn_dec_empty["pd"]["zone_defs"]["decoupling_via_to_plane"]["vias"] = []
    syn_dec_miss = json.loads(json.dumps(spec))
    syn_dec_miss["pd"]["zone_defs"]["decoupling_via_to_plane"]["vias"] = [
        {"ref": "U99", "pos": [[0.0, 0.0]]}]
    teeth = {"detector_orphan_injection_caught": "U99" in orphan_scan(syn_orphan)["entries"],
             "detector_silent_pad_injection_caught": len(coverage_scan(syn_silent)[2]) >= 1,
             "detector_empty_decoupling_caught": not decoupling_ok(syn_dec_empty),
             "detector_missing_decoupling_ref_caught": not decoupling_ok(syn_dec_miss),
             "board_pad_floor": len(pads), "spec_entry_floor": len(ppc.get("entries", [])),
             "decoupling_target_floor": len(refs["decoupling_targets"])}
    teeth_ok = all(v for k, v in teeth.items() if k.startswith("detector_"))

    rec = {"artifact": "m13_v57_co88_pdn_board_reality_gate", "schema": 1, "revision": "CO-88.3",
           "hardening": "CO-90 F1/F2：headline verdict 并入判据 C（消除 C=FAIL 而 headline=PASS 的空真）；teeth 改为真跑检测路径的注入测试。CO-90 F4：ripple_checklist 移出哈希体（其内容随 tools/*.py 集合变化 ⇒ 会使本记录 sha 依赖无关工具文件，破坏逐字节可复现）",
           "nature": "L2 PDN：live 机读字段（power_pad_connect / decoupling）的板实性 + 覆盖性机判",
           "inputs": {"spec": spec_path.name, "spec_sha16": s16(spec_path), "board": BOARD.name,
                      "board_sha16": s16(BOARD), "pwr_nets": sorted(PWR_NETS)},
           "A_refdes_existence": {"orphan_refs_by_field": orphans,
                                  "n_orphan_entries": n_orphan_entries,
                                  "n_orphan_blocked": n_orphan_blocked,
                                  "verdict": "FAIL" if any(orphans.values()) else "PASS"},
           "B_coverage": {"board_smd_power_pads": len(pads), "covered": len(covered),
                          "declared_blocked": len(declared_blocked), "silent_undecided": len(silent),
                          "silent_list": [f"{r}.{p}" for r, p in silent[:20]],
                          "verdict": "PASS" if not silent else "FAIL"},
           "coverage_scope": {"b_denominator_net_set": sorted(PWR_NETS),
                              "source": "eda_core.pad_connect_gen.DEFAULT_PWR_NETS（内置常量；--nets 可覆盖）",
                              "note": "B 判据分母 = 此网集合上的板实 SMD pad，非「板全电源网」；集合外电源类 pad 不计入（CO-90 F3 已登记）"},
           "C_decoupling": {"field": refs["decoupling"], "targets": refs["decoupling_targets"],
                            "n_targets": len(refs["decoupling_targets"]),
                            "missing_on_board": orphans["decoupling_via"],
                            "verdict": "PASS" if c_ok else "FAIL"},
           "fix_candidate": scratch_regeneration(spec_path),
           # CO-90 F4：本记录必须是 (SPEC, 板) 的**纯函数**；任何目录扫描类「建议清单」不得进入哈希体。
           # 需要 ripple 清单时按需调用 ripple_checklist()（见文件尾部函数；不写入本记录）。
           "advisory_ripple_policy": "ripple_checklist 不嵌入哈希体（CO-90 F4）；按需调用 ripple_checklist()",
           "teeth": teeth,
           "verdict_by_criterion": {"A_refdes_existence": "PASS" if not any(orphans.values()) else "FAIL",
                                    "B_coverage": "PASS" if not silent else "FAIL",
                                    "C_decoupling": "PASS" if c_ok else "FAIL"},
           "verdict": ("PASS（三项均合规：引用全板实 / 板实 pad 全有决策 / 解耦目标板实）"
                       if (not any(orphans.values()) and not silent and c_ok)
                       else "FAIL（L2 SPEC 未达 ch.5 §1/§2/§3）"),
           "redline": "只读；scratch 即用即删；不改 SPEC/板/阈值；不 partial pass。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"][:24], "orphan_entries": n_orphan_entries,
                      "orphan_refs": sum(len(v) for v in orphans.values()),
                      "pads": len(pads), "covered": len(covered), "blocked": len(declared_blocked),
                      "silent": len(silent), "decoupling_missing": orphans["decoupling_via"],
                      "fix_candidate": rec["fix_candidate"], "teeth": teeth, "teeth_ok": teeth_ok,
                      "ripple_advisory_out_of_record": ripple_checklist()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
