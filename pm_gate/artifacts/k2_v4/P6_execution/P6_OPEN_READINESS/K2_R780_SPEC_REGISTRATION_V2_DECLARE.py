#!/usr/bin/env python3
"""K2 R780-A --- #K2-304 sec.2.1 : SPEC registration-version bump (append-only).

rev-56 = rev-55 + (NEW keys only):
  * `router.wall_gap_exit_registration_v2` : the R778 corrected wall-gap registration (15 kept routable
    openings + 1 added routable opening W[114,47]; 6 dead holes excluded) + the full authorisation chain
    #K2-280 -> #K2-297 -> #K2-303 -> #K2-304 + evidence hashes.
  * `_spec_rev_56` traceability card.
  * `spec_version` bump.
Existing keys/scalars/polygons are NOT modified (a flat before/after diff proves additions only, apart
from spec_version). project.yaml is re-pointed to the new rev (project convention). Other frozen sources
untouched.
"""
import json, hashlib, sys, os
from pathlib import Path
K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-55.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-56.json"
REC = K2 / "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R780_SPEC_REGISTRATION_V2_DECLARE.json"
def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from flat(v, f"{p}[{i}]")
    else: yield p, o
def main():
    spec = json.loads(SRC.read_text()); before = dict(flat(spec))
    reg2p = K2 / "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_L1_A_EXIT_REGISTRATION_REVISION_v2.json"
    certp = K2 / "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R778_CERTIFIED_16OF16_v1.json"
    reg2 = json.loads(reg2p.read_text()); cert = json.loads(certp.read_text())
    spec["router"]["wall_gap_exit_registration_v2"] = {
        "status": "ACTIVE (registration plan; physical openings NOT yet changed — board body untouched)",
        "openings_kept_routable": reg2["openings_kept_routable"],
        "openings_dead_excluded": [{"cell": o["cell"], "reason": o["reason"]} for o in reg2["openings_dead_excluded"]],
        "opening_added": reg2["opening_added"],
        "usable_openings_total": reg2["usable_openings_total"],
        "physical_opening_changes": 0,
        "authorisation_chain": ["#K2-280 (A-prime立案)", "#K2-282 (设计权威=成功案例常令)",
                                "#K2-297 (owner常令：登记修订先证后动)", "#K2-303 (R776验收：最小核+靶向)",
                                "#K2-304 (放行：SPEC bump + 一次描线)"],
        "evidence": {"registration_v2_sha16": s16(reg2p), "certification_sha16": cert.get("artifact_hash16"),
                     "certification_binary": cert.get("binary"),
                     "iis_core_size": 31, "iis_note": "pigeonhole: 16 lanes vs 15 routable openings (R776)"},
        "invariants": reg2["invariants"]}
    spec["_spec_rev_56"] = {
        "card": "SPEC-REV-56（L1 出口注册 v2 落账 · #K2-304 §二.1）",
        "at": "2026-09-27",
        "authority": "监理 #K2-304（放行 SPEC 登记版 bump 落账）· owner 常令 #K2-282/#K2-297（先证后动）",
        "scope": "ONLY new keys: router.wall_gap_exit_registration_v2 + this card + spec_version bump. No existing scalar/geometry/threshold/net/layer role changed.",
        "basis": ["R776 minimal-conflict-core IIS = 31 constraints (16 lanes + 15 routable gates), cell-free, irreducible",
                  "R778 corrected registration v2 + certified SAT_16of16 (four hard keys + layer-pair + conservation)",
                  "dead declared openings (0 legal candidates): W row114 col 16/19/20/22/23, E row135 col36"],
        "unchanged": "all pre-existing fields; other frozen sources (manifest / PCB / drc_rules) untouched",
        "spec_sha256_before": hashlib.sha256(SRC.read_bytes()).hexdigest(),
        "spec_backup": "git-tracked %s (byte-unchanged)" % SRC.name,
        "rollback": "restore project.yaml spec_name to SPEC_k2_v4.spec-rev-55.json; delete rev-56 (predecessor byte-unchanged)"}
    spec["spec_version"] = "1.1.spec-rev-56"
    after = dict(flat(spec))
    added = {k: v for k, v in after.items() if k not in before}
    removed = [k for k in before if k not in after]
    changed = {k: (before[k], after[k]) for k in before if k in after and before[k] != after[k]}
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=1))
    # re-point project.yaml (project convention: new rev becomes canonical)
    py = K2 / "pm_gate/project.yaml"; yt = py.read_text()
    assert "SPEC_k2_v4.spec-rev-55.json" in yt
    py.write_text(yt.replace("SPEC_k2_v4.spec-rev-55.json", "SPEC_k2_v4.spec-rev-56.json"))
    rec = {"artifact": "k2_r780_spec_registration_v2_declare", "src": SRC.name, "out": OUT.name,
           "src_sha16": s16(SRC), "out_sha16": s16(OUT),
           "added_keys": sorted(added.keys()), "removed_keys": removed,
           "changed_existing_scalars": {k: {"before": v[0], "after": v[1]} for k, v in changed.items()},
           "project_yaml_repointed_to": "SPEC_k2_v4.spec-rev-56.json",
           "appendonly_ok": (len(removed) == 0 and {k.lstrip(".") for k in changed.keys()} <= {"spec_version"}),
           "OWNER-ITEMS": 0}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0
if __name__ == "__main__": sys.exit(main())
