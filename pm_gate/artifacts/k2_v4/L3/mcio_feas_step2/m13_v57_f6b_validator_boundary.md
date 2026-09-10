# m13 v57 — F-6b Double-End Verifier: Validator Boundary Declaration

> Artifact: `m13_v57_f6b_report.json` (schema=1, revision=`F6B-DE.1`)
> Producer: `k2/tools/p3_v57_f6b_double_end_verifier.py`
> Scope: G3 v1.1 §3 / F-6 double-end reach predicate, per D0-4 (k:=5, leg=7.3mm)
> with k∈{1,2,3,5} sensitivity. Independent of the F4 single-end verifier and the
> W1 assign tool (neither is imported).

## 0. What is asserted (and only this)

The report answers one question per (corridor, frame, k): **does an injective,
strictly increasing (no-crossing) page→lane-index assignment exist under the
double-end predicate** `|lane_y − conn_row_y| ≤ leg ∧ |lane_y − chip_row_y| ≤ leg`?
For infeasible cases it additionally reports an inclusion-minimal core (MUS) and a
quantitative reach certificate (`required_leg_mm`, `short_mm`).

**No assignment is ever emitted.** The exact engine returns a bool only; MUS is a
page-id set, not a lane mapping.

## 1. Replayable assertions

Run: `python3 k2/tools/p3_v57_f6b_double_end_verifier.py` → exit 0, `verdict=PASS`.

| # | Assertion | Expected | Observed |
|---|---|---|---|
| A1 | manifest SHA-256 | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` | match |
| A2 | w0r_model SHA-256 | `80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa` | match |
| A3 | rules SHA-256 | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` | match |
| A4 | g3_v1_1 SHA-256 | `232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff` | match |
| A5 | g3_v1_2 SHA-256 | `128b0b97358d8980e1fecd66aa137b5b963c76cea9c4af78e71dc75e5cc85edb` | match |
| A6 | d0_card SHA-256 | `a69cc7f5eedab2a19fa6ad5be55e100e1163da71d274ad540192d35b9bfdf79d` | match |
| A7 | pitch authority (`RULES.diff_pair`: 0.175+2·0.205+0.875) | `1.46` | 1.46 (runtime assert) |
| A8 | producer tool SHA-256 | `695871b0a8ee919ff16bc72cb23aa6254121616a48a48cb5674fbfe88e874334` | recorded in `versions.*.sha256` |
| A9 | report SHA-256, two consecutive runs | byte-identical | `882eca5d25dbed92c7bf51fa19495f53cbd0c4b04d29ba974f2964c90855911d` (both runs) |
| A10 | synthetic double-end cross-check | 200/200/200 | `decision_match=200, mus_match=200, order_invariant=200` |
| A11 | real decisions == §8 table | see §2 | match (`expected_mismatch=[]`) |
| A12 | k=5 MUS == §8 table | see §2 | match |
| A13 | MUS convention | cardinality asc, then id-tuple lexicographic; first infeasible subset | W1/F4-identical code path |
| A14 | no-allocation scan | `leaked=[]` | `forbidden_keys=["selected","assigned","allocation","witness"]`, `leaked=[]` |
| A15 | forbidden imports | absent | `grep p3_v57_f4\|w1_assign` → no match in the verifier |

Frozen-SHA drift → `verdict=FAIL`, non-zero exit. Pitch drift → `assert` failure.

## 2. Real decision table (k order = [1,2,3,5]) and k=5 certificates

| corridor / frame | n | k=1 | k=2 | k=3 | k=5 |
|---|---|---|---|---|---|
| EAST_CHIP_TO_J2 / up | 8 | F | F | F | **T** |
| EAST_CHIP_TO_J2 / dn | 8 | F | F | F | **T** |
| EAST_CHIP_TO_J2 / joint | 16 | F | F | F | F |
| WEST_MCIO_TO_CHIP / up | 8 | F | F | F | F |
| WEST_MCIO_TO_CHIP / dn | 8 | F | F | F | F |
| WEST_MCIO_TO_CHIP / joint | 16 | F | F | F | F |

`joint` = single increasing assignment over all pages of both bands (sorted by
conn_row_y). 22 infeasible (frame,k) certificates emitted.

k=5 infeasible certificates (MUS page-id core / `required_leg_mm` / `short_mm`):

| corridor / frame | MUS (k=5) | leg* (mm) | short (mm) |
|---|---|---|---|
| EAST_CHIP_TO_J2 / joint | `PCIE_DN0..DN7/input` + `PCIE_UP0..UP3/out_J2` (12) | 10.497 | 3.197 |
| WEST_MCIO_TO_CHIP / up | `[PCIE_UP4/input, PCIE_UP5/input]` | 9.56 | 2.26 |
| WEST_MCIO_TO_CHIP / dn | `[PCIE_DN4/out_MCIO … PCIE_DN7/out_MCIO]` (4) | 7.56 | 0.26 |
| WEST_MCIO_TO_CHIP / joint | `[PCIE_UP4/input, PCIE_UP5/input]` | 11.02 | 3.72 |

`leg*` is a property of the frame (minimal leg making it feasible), computed once
per frame by monotone binary search with the exact DP; `short_mm = max(0, leg*−leg)`.
k=1/2/3 MUS cores are computed, never hardcoded.

Per-frame context: `required_band_mm=(n−1)·pitch` (10.22 single-band / 21.9 joint);
`reachable_band_mm` = (max chip_row + 7.3) − (min chip_row − 7.3) at k=5.

## 3. Exact engine and why the DP (not matching) is required

The double-end allowed set per page is `[conn−leg, conn+leg] ∩ [chip−leg, chip+leg]`.
Because `chip_row_y` varies independently of `conn_row_y` (in the joint frame a
page's chip row can decrease while conn row increases), these allowed sets are
**not** monotone intervals, so the single-end uncrossing/bipartite-matching
equivalence does **not** apply. The verifier therefore uses the exact
increasing-constraint reachability DP (frontier = set of reachable last lane
indices; next frontier = allowed j with some reachable i<j). `brute_feasible`
independently enumerates strictly increasing lane-index tuples (n≤7) under the
double-end predicate as the small-n reference.

## 4. Out-of-scope / non-assertable

- **No allocation output**: no page→lane assignment, matching, witness, lane list
  or `track_y` is emitted or recoverable from the report.
- **No physical/DRC validation**: vias, pad geometry, clearance, layering and
  copper are out of scope; this is a pure combinatorial reachability decision.
- **No `k` authority**: `k=5` is consumed from D0-4, not established here; the
  k∈{1,2,3,5} rows are sensitivity only, not a final G4 admission.
- **`leg*` is a predicate threshold, not a physical leg budget**; it is not a
  manufacturable geometry parameter.
- **No capacity claim**: `required_band_mm`/`reachable_band_mm` are context, not
  a span-conservation proof.
- **Coverage**: only EAST_CHIP_TO_J2 and WEST_MCIO_TO_CHIP corridors and the
  frames present in the manifest; other nets/layers are not covered.
- **Synthetic cross-check coverage**: n≤6, lanes of length n..n+3, the seven
  fixed conn/chip offsets, and legs {1.46,2.92,4.38,7.3}; it is a same-seed
  differential test, not an exhaustive proof over all instances.

## 5. Forbidden reverse-inference

- Do **not** infer any page→lane assignment, ordering index or `track_y` from a
  feasibility bool, a MUS, or `leg*`.
- Do **not** treat a MUS as an allocation plan or as a construction order.
- Do **not** infer that an infeasible frame is physically unbuildable without an
  upstream input change (escape hatch); infeasibility is a predicate statement.
- Do **not** reverse-engineer `required_leg_mm`/`short_mm` into a physical leg
  budget or a routing constraint.
- Do **not** use the k<5 sensitivity rows as a G4/W3 admission conclusion.
- Do **not** read the `no_allocation_scan.forbidden_keys` declaration as leaked
  data: those four strings occur only inside that declaration; `leaked=[]`.

---

## 架构师签收（2026-09-10，审核注记）

独立复验：双跑 `882eca5d…` 一致；stdlib-only、不 import F4/W1（grep=0）；
谓词确为双端 `|lane−conn|≤leg ∧ |lane−chip|≤leg`；报告字段齐、无分配泄漏。

**裁定**：F-6b 工具与实现**通过**。但其 k=5 终判**不作为可行性结论**——见 D0-4 修订
（G3 v1.2 §7）：k∈{1,2,3,5} 是合成代理集，无权威源；7.3mm cap 比几何所需还紧，
产生假不可行。证书中的 `required_leg_mm`（EAST joint 10.497 / WEST joint 11.02）
是**真几何量**，已用于修订判据：可用 fan-out（走廊 45.4mm）≫ required → **全帧 FEASIBLE**。

F-6b 的 `required_leg_mm` / `reachable_band_mm` / MUS 保留为**拥塞与逃逸代价指标**。
