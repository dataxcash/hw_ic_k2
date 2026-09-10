# EDA Autonomous Engineering — Execution Plan v2

> Supersedes `EDA_AUTONOMOUS_ARCHITECTURE_AND_EXECUTION_PLAN_v1.md` §4–§6 only.
> §1–§3 (product objective, layer contract, evidence protocol), §7 (knowledge
> promotion) and §8 (MVP definition of success) remain authoritative and unchanged.
> This document is a status/gate ledger, not an authority to change frozen inputs.

## 0. Status snapshot (2026-09-10, architect)

- G1 (W0 independent B1.5 review) = **BLOCKED** (recorded in v1).
- Only released implementation card: **W0-R** (v1 §6).
- W0-R artifacts exist and the internal validator reports `PASS`, but the
  architect's first-pass review holds W0-R **short of the B1.5 acceptance line**
  (gaps W0R-G1..G3 below). W0-R terminal status is therefore still `BLOCKED`
  until one of `B1.5 PASS` / `B1.5 INFEASIBLE_CERT` is produced and reviewed.
- Active worker cards now: **W0R-FIX** and **R1-REVIEW** (parallel, read-only
  on all frozen inputs). D0/W3/W4 remain sealed.

## 1. W0-R first-pass architect review

Satisfied by W0-R as shipped:

- Versioned input envelope (`m13_v57_big_w0r_inputs.json`) with authority
  classification and SHA-256 fingerprints for SPEC/board/manifest/rules.
- Per-corridor `usable_y_spans` for the data layer, data bands with
  `n_pairs`/`centre_span_needed_mm`/`feasible`, and a joint data frame.
- REFCLK anchors match the manifest: `PCIE_REFCLK0` = J3↔J2, `PCIE_REFCLK1` =
  J4↔J2 (a pass-through pair, corridor id `EAST+WEST_CHIP_TO_CONN`). The earlier
  WEST-endpoint concern is cleared.
- Separately implemented validator (`p3_v57_big_w0r_validator.py`) that does not
  import the generator and recomputes spans/anchors independently.

Gaps that block acceptance (must be closed by W0R-FIX):

- **W0R-G1** REFCLK domain is `resource_kind: candidate_only` with anchors only.
  Missing the quantitative conservation certificate required by v1 §6 item 4:
  `required`, `available`, `shortage`, conflicting resources, and a canonical
  minimal core. `candidate_only` may be a legitimate terminal state only if it
  is argued and evidenced as a formal L2 infeasibility certificate; otherwise it
  must become concrete legal resources.
- **W0R-G2** `verdict: FEASIBLE_RESOURCE_ENVELOPE` is not one of the two terminal
  statuses. It must be re-issued as `B1.5 PASS` or `B1.5 INFEASIBLE_CERT`, with
  the evidence protocol (v1 §3) fields present.
- **W0R-G3** `blocked_component_projections: []` must be proven to be a real
  subtraction result (geometry projections were enumerated and none intersected
  the corridor), not an empty default. Emit the projection predicate, source
  hash, and the list of components checked.

## 2. Gate ledger (DOR / DOD / owner / verification / rollback)

Owner: L2 decision owner = project owner (the human authority relaying cards);
architecture acceptance = this review role.

| Gate | DOR (entry) | DOD (exit) | Owner | Independent verification | Rollback |
|---|---|---|---|---|---|
| G0 baseline record | frozen netlist/libraries/placement/stackup/rules exist | frozen file list + SHA-256 + byte-identical double run + single `_shared` source path | architect | byte-diff of two full runs | restore prior snapshot |
| G1 W0 B1.5 review | W0-R artifacts + validator | review record: declared inputs, double-run hashes, per-certificate proof, owner, legal L2 changes; verdict `B1.5 PASS` or `B1.5 INFEASIBLE_CERT` | architect | independent re-parse, no hidden `tracks_y` authority | reopen W0-R |
| G2 L2 decision | G1 terminal verdict | D0 decision card: selected legal change or accepted infeasibility, signed authority/input version, no frozen-file mutation | project owner | record matches signed inputs | reissue D0 |
| G3 W1/W2 freeze | G2 = continue | schema gap matrix (R1) frozen + W1/W2 I/O contract frozen | architect | 32 data + 2 REFCLK pages represented; W0 block propagated | reopen R1 |
| G4 W3 joint allocation | G3 frozen | all 34 pages or one global minimal certificate; order-independent; no per-net first-fit | W3 card | independent true-drawing pre-check | return to W3 |
| G5 W4 true-drawing validation | W3 complete | A1.2/A1.3/A1.4 reports covering all pages and all strong nodes | W4 card | partial pass rejected | return to W3 |
| G6 L4 drawing-only construction | W4 PASS | PCB consumes drawing unchanged; every node connected as prescribed | L4 card | mismatch returns drawing to W3 | re-run L4 |
| G7 L5 sign-off + learning review | L4 complete | SI/PI/EMC, DFM/DFT, fabrication records + knowledge promotion review | L5 card | records are evidence, not repair permission | reopen owning layer |

## 3. Reference register (single source of truth)

The following analyses are the authoritative detailed gap/design sources and are
registered here; the execution plan only references, never duplicates, them.

| Doc | Role |
|---|---|
| `m13_v52_architecture_target.md` | architecture target + CCF schema decisions |
| `m13_v52_irg_readiness.md` | implementation-readiness gate, READY_WITH_CHANGES + 3 revisions |
| `m13_v55_construction_module_review.md` | construction-module defects A1–E3 |
| `m13_v56_remediation_plan.md` | P0–P5 dependency-ordered fix plan |
| `m13_v57_baseline_correction.md` | v57 baseline correction: version counts, B1.5 not delivered, worktree isolation |
| `m13_v57_big_w0r_inputs.json` / `_corridor_model.json` / `_validation.json` | W0-R artifacts under review |

## 4. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | L2 decision owner absent / unsigned | High | G2 stalls, W3 cannot release | D0 must carry an explicit signed authority/input version; no unsigned continue |
| R2 | `_shared` dual-source contamination (k2 `_shared` vs container `_shared`) | Medium | nondeterministic runs, invalid baselines | G0 requires single `_shared` source path; k2 local copy stays frozen/untouched |
| R3 | W0-R re-emits `candidate_only` without quantitative certificate | High | G1 remains BLOCKED | W0R-FIX acceptance demands required/available/shortage/minimal-core or a formal INFEASIBLE_CERT |
| R4 | Learning promotion bypasses review | Low | silent rule corruption | §7 lifecycle only; no K2-specific result becomes a general rule |
| R5 | Untracked historical artifacts mixed into functional commits | Medium | unreviewable history | commit scope: only reviewed docs/artifacts; 142 legacy files stay untracked |

## 5. Active worker cards

### Card W0R-FIX — close W0R-G1/G2/G3 (implementation)

- **Scope:** only the three gaps in §1. Do not rebuild the accepted input
  envelope, data bands, or validator architecture.
- **Deliverables:**
  1. REFCLK domain per page and per corridor upgraded to a quantitative
     conservation certificate: `required`, `available`, `shortage`,
     `conflicting_resources`, and canonical `minimal_core`; OR a formal
     `B1.5 INFEASIBLE_CERT` with the same fields and a minimal conflict core.
  2. `verdict` re-issued as exactly `B1.5 PASS` or `B1.5 INFEASIBLE_CERT`.
  3. Evidence that `blocked_component_projections` is a real enumeration:
     predicate, source hash, list of checked components, and the empty result
     justification (or non-empty projections if found).
  4. Double-run byte-identical check re-executed after all changes.
- **Forbidden:** modify SPEC, frozen placement, `_shared`, W1/W2, PCB copper, or
  the generator/validator split. Do not route. Do not start allocation.
- **Acceptance:** every field of v1 §3 evidence protocol present; verdict is one
  of the two terminal statuses; gap W0R-G1/G2/G3 each closed with cited proof;
  no hidden `tracks_y` authority; clear `PASS` or `BLOCK` (no third state).

### Card R1-REVIEW — W1/W2 interface review (read-only, parallel)

- **Scope:** read-only review of W1 (`p3_v57_big_w1_assign.py` +
  `m13_v57_big_w1_report.json`) and W2 (`p3_v57_big_w2_connector_cols.py` +
  `m13_v57_big_w2_connector_cols.json`) against manifest/W0-R inputs.
- **Deliverables:** a schema gap matrix from W0/manifest/W1/W2 to W3: required
  fields, source of each field, gaps, and the independent-validator boundary.
  Must show the actual 32 data pages and 2 REFCLK pages are representable, and
  must propagate the W0-R block (mark every W3 dependency on W0 as BLOCKED-DEPENDENT).
- **Forbidden:** emit assignments, allocation, or any W3 output. No frozen-file edits.
- **Acceptance:** matrix cites field-level sources; 34 pages enumerated; W0 block
  propagated; no allocation leaked.

## 6. Sequenced status

```text
G0 pending freeze   -> G1 BLOCKED (W0R-FIX + R1-REVIEW active)
                    -> G2 sealed until G1 terminal
                    -> G3 sealed until G2 continue
                    -> G4..G7 sealed
```

End of v2.
