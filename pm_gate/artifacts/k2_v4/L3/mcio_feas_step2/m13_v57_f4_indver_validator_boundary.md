# m13 v57 — F4-INDVER validator boundary declaration

> Artifact: `m13_v57_f4_indver_report.json`｜Producer/validator:
> `k2/tools/p3_v57_f4_independent_verifier.py`｜Revision `F4-INDVER.1`｜Seed `20260909`
> Date: 2026-09-10｜Scope: W1 no-crossing ordered-assignment feasibility predicate.

This file declares exactly **what F4-INDVER asserts** (replayable), **what it
does not assert** (out of scope), and **what must never be reverse-inferred**
from it.

---

## 1. Replayable assertions (all machine-checked at runtime)

| # | Assertion | Evidence in report | Result |
|---|---|---|---|
| A1 | Pitch authority: `drc_rules.diff_pair` derives `0.175 + 2*0.205 + 0.875 = 1.46` | `pitch_derivation` | PASS |
| A2 | Frozen input fingerprints == disk (runtime `sha256`) | `inputs_sha` | PASS |
| A3 | `manifest` SHA == `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` | `inputs_sha.manifest`, `frozen_sha_match` | PASS |
| A4 | `rules` SHA == `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` | `inputs_sha.rules` | PASS |
| A5 | `w0r_model` SHA == `80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa` | `inputs_sha.w0r_model` | PASS |
| A6 | Producer/validator SHA == verifier file on disk | `versions.*.sha256` = `2f377a641f110251f994cf03a6b969159376895b2361f3c5960c2696e78023fe` | PASS |
| A7 | 200 synthetic instances: `exact_feasible == brute_feasible` | `synthetic.decision_match` = 200 | PASS |
| A8 | 200 synthetic instances: `mus(exact) == mus(brute)` | `synthetic.mus_match` = 200 | PASS |
| A9 | 200 synthetic instances: 3 input orders agree | `synthetic.order_invariant` = 200 | PASS |
| A10 | Real n=8 / n=16 decisions match the frozen expected table (§9) | `real.expected_mismatch` = [] | PASS |
| A11 | Frame capacity `(n-1)*pitch <= span_len` | `real.frame_capacity_crosscheck` (all `ok=true`) | PASS |
| A12 | No allocation output leaked | `no_allocation_scan.leaked` = [] | PASS |
| A13 | Double-run byte-identical | report SHA (two runs) = `11dfc99651384e3f12b36a7a37ecdd6a6b00ca0aaaa6abbffc9659dc882c53fe` | PASS |

### A2 fingerprint block (full 64-hex)

```
manifest    a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890
rules       0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448
w0r_model   80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa
w1_report   57d0c9228bf48efd63e07eec8a04bb526523650567c62a0db8c432c916ef459a
g3_contract 232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff
```

### A10 real decisions (exact engine, grid lane domain 33.3..78.56, pitch 1.46, margin 0)

| corridor | frame | n | k=1 | k=2 | k=3 | k=5 |
|---|---|---|---|---|---|---|
| EAST_CHIP_TO_J2 | up | 8 | T | T | T | T |
| EAST_CHIP_TO_J2 | dn | 8 | T | T | T | T |
| EAST_CHIP_TO_J2 | joint | 16 | **F** | T | T | T |
| WEST_MCIO_TO_CHIP | up | 8 | **F** | T | T | T |
| WEST_MCIO_TO_CHIP | dn | 8 | **F** | T | T | T |
| WEST_MCIO_TO_CHIP | joint | 16 | **F** | **F** | **F** | T |

MUS page-id cores for the infeasible real cases (exact engine, cardinality asc
then lexicographic — W1-identical convention):

- `EAST_CHIP_TO_J2/joint k=1` (12): DN0..DN5 `input` + UP2..UP7 `out_J2`
- `WEST_MCIO_TO_CHIP/up k=1` (3): UP0..UP2 `input`
- `WEST_MCIO_TO_CHIP/dn k=1` (3): DN0..DN2 `out_MCIO`
- `WEST_MCIO_TO_CHIP/joint k=1` (3): DN0..DN2 `out_MCIO`
- `WEST_MCIO_TO_CHIP/joint k=2` (6): DN4..DN7 `out_MCIO` + UP4,UP5 `input`
- `WEST_MCIO_TO_CHIP/joint k=3` (8): DN4..DN7 `out_MCIO` + UP4..UP7 `input`

### A12 no-allocation scan

`forbidden_keys = ["selected","assigned","allocation","witness"]`; the report
object (excluding the scan block itself) is walked for these as dict keys and
`leaked = []`. The four literal words appear in the report only inside the
scan's own `forbidden_keys` declaration, by construction.

### Independent W1 cross-check (extra evidence, NOT part of the verifier)

A throwaway script (`/tmp/opencode/f4_w1_crosscheck.py`) imported W1's
`kernel_feasible` and the F4 `exact_feasible`, replayed the same 200 instances
(seed 20260909), and confirmed:

```
exact == kernel on 200/200 replayed instances
```

This is corroboration only; the deliverable verifier never imports W1.

---

## 2. Non-assertable / out of scope

- **No page→lane selection is asserted or emitted.** F4 decides only the
  boolean feasibility of the predicate. Any concrete page→lane mapping is W3
  allocation work and is explicitly outside this artifact ("no allocation
  output"). The engine returns `bool` only.
- **MUS is a page-id core, not an allocation.** MUS lists identify an
  inclusion-minimal infeasible page subset; they carry no lane indices.
- **R4 wall pads are out of the chain.** Any R4 wall/pad consideration is not
  part of the page↔lane feasibility predicate modelled here.
- **n>7 real MUS are not brute-verified.** The brute oracle is limited to
  n<=7; real n=8/n=16 MUS are produced by the exact engine and are minimal by
  construction (cardinality-ascending enumeration), not by brute replay.
- **Single-end grid domain only.** Decisions use the full pitch grid over
  `usable_y_spans[0]`; no board-level, layer-assignment or keep-out projection
  effects beyond the frozen span are re-derived.

---

## 3. Forbidden reverse-inference

The following must never be inferred from, or fed back into, this artifact:

- `SPEC.corridors.tracks_y` (superseded authority).
- Board copper tracks / vias / zones (fabricated geometry is not a premise).
- Legacy lane books / pre-freeze lane assignments.
- Old W0 constants `0.6` (void margin) and `12.0` (void single-end LEG/reach budget; superseded by F-6 `k·1.46`, k∈{1,2,3,5}).
- Any page→lane allocation, matching, witness or `track_y` value — none is
  emitted by design; reconstructing one from this report is invalid.

Authoritative inputs are only: the frozen manifest, `drc_rules.json`, the W0-R
corridor model, and the G3 v1.1 frame-ruling contract (margin=0, edge
`up→lo`/`dn→hi`, pitch=1.46).

---

## 架构师签收（2026-09-10，审核注记）

独立复验：A1–A13 全 PASS；双跑 `11dfc996…`；`no_allocation_scan.leaked=[]`；
验证器不 import W1（grep 确认），W1 工具 SHA 仍 `6583a552…`；
`g3_contract_sha=232fda85…` == 磁盘 G3 v1.1。

三条裁定：

1. **lane 域 vs 容量帧（接受）**：确认 §2 的 "span pitch grid 作为 lane 域" 正确。
   G3 v1.1 §1 的 span 端 frame 是**容量帧**（判 `(n−1)·pitch ≤ span`），**不是**指派
   lane 域。已由 G3 v1.2 正式澄清并 ratify。
2. **谓词范围（限定通过）**：F4 验证的是 **W1 单端谓词** `|lane_y − conn_row_y| ≤ leg`，
   **未覆盖** G3 v1 §3/F-6 的**双端**谓词（chip_row_y 端）。本卡按"取代 W1 穷举 oracle"
   的范围**通过**；双端谓词验证记为 **F-6b 待补**，不作双端终判。
3. **LEG 预算 `k` 无权威源（上报）**：`k` 决定可行性与否（WEST joint 在 k≤3 全 F，k=5 才 T）。
   R1 W1-3 早已记其"无权威源"。→ 开 **D0-4** 请 L2 裁决；在 `k` 定前，F4 表为**灵敏度
   分析，非终判**。

**F4-INDVER = 验收通过（范围限定）。**
