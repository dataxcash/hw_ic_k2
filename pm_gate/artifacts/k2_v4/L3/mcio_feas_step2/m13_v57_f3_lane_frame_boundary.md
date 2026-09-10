# m13 v57 — F3-LANEFRAME Boundary Declaration

> Revision: **F3-LANEFRAME.1** ｜ Artifact: `m13_v57_f3_lane_frame.json` ｜ Schema: 1
> Producer: `tools/p3_v57_f3_lane_frame.py`
> Independent verifier: `tools/p3_v57_f3_lane_frame_validator.py` (does NOT import the producer)

This card emits the R2 assignment **lane domain** (pitch grid over
`usable_y_spans`) and the independent **capacity frame**, with page-level
`conn_row_y` / `chip_row_y`, WEST `conn_ref` framing, and a per-frame
**authority fingerprint block**. It performs **NO allocation** and **NO
feasibility judgement**.

---

## 0. Frozen fingerprints (full 64-hex)

| input | path | expected (spec frozen) | actual on disk | match |
|---|---|---|---|---|
| manifest  | `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` | ✅ |
| w0r_model | `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_big_w0r_corridor_model.json` | `80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa` | `80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa` | ✅ |
| rules     | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` | ✅ |
| g3_v1_1   | `.../m13_v57_g3_freeze_contract_v1_1_frame_ruling.md` | `232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff` | `232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff` | ✅ |
| g3_v1_2   | `.../m13_v57_g3_freeze_contract_v1_2_lane_domain.md` | `c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6` | `c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6` | ✅ |
| generator | `tools/p3_v57_f3_lane_frame.py` | — | `c9b98494826cbcb6ae39b876a76b7a8e3226d6cb758eedd0dc92b20039d10603` | recorded |
| verifier  | `tools/p3_v57_f3_lane_frame_validator.py` | — | `b9350664ab238a4586aa9e32756a4283b0bc8e8a3c5247e4bd9304b9988f2496` | recorded |

Pitch authority: `RULES["diff_pair"]` ⇒ `0.175 + 2*0.205 + 0.875 = 1.46`
(asserted at runtime; `PITCH = 1.46`).

### 0.1 Authority pinned to current `g3_v1_2`

- Authority is pinned to the current on-disk `g3_v1_2 = c8f380c1…` (HEAD
  `af31397`, which appended the **§7 D0-4 revision**: reach = available
  fan-out space, 6/6 frames feasible).
- The F-3-relevant content (§1 lane domain, §3 authority) is byte-identical
  across the `2809c30`→`af31397` revisions; only §7 was added. All 5 frozen
  fingerprints match disk (`match` all true, `drift=[]`).
- Generator and verifier pin the current digest, so a future edit to any
  frozen source is a hard failure (no silent drift).

---

## 1. Replayable assertions

| # | assertion | expected | observed | verdict |
|---|---|---|---|---|
| A1 | lane `span` (both corridors) | `[33.3, 78.7]` | `[33.3, 78.7]` | ✅ |
| A2 | lane `step` / `margin` | `1.46` / `0.0` | `1.46` / `0.0` | ✅ |
| A3 | lane `positions` length | `32` | `32` | ✅ |
| A4 | lane first / last position | `33.3` / `78.56` | `33.3` / `78.56` | ✅ |
| A5 | capacity up/dn `needed_mm` | `(8-1)*1.46 = 10.22` | `10.22` | ✅ |
| A6 | capacity up/dn `avail_mm` | `78.7-33.3 = 45.4` | `45.4` | ✅ |
| A7 | capacity joint `needed_mm` | `(16-1)*1.46 = 21.9` | `21.9` | ✅ |
| A8 | capacity joint `avail_mm` | `45.4` | `45.4` | ✅ |
| A9 | capacity `capacity_ok` (up/dn/joint) | all `true` | all `true` | ✅ |
| A10 | EAST frames | 2 (`up/J2`, `dn/J2`), `order_key="conn_row_y"` | 2, `conn_row_y` | ✅ |
| A11 | EAST/up/J2 `conn_row_y` (8) | 43.2, 44.1, 46.8, 47.7, 48.6, 49.5, 52.2, 53.1 | identical | ✅ |
| A12 | EAST/dn/J2 `conn_row_y` (8) | 54.3, 55.2, 57.9, 58.8, 59.7, 60.6, 63.3, 64.2 | identical | ✅ |
| A13 | WEST frames | 4 (`up/J3`,`up/J4`,`dn/J3`,`dn/J4`), `order_key="conn_x"` | 4, `conn_x` | ✅ |
| A14 | WEST/up/J3 `conn_x` asc | UP3(55.0), UP2(56.8), UP1(62.2), UP0(64.0) | identical | ✅ |
| A15 | WEST/up/J4 `conn_x` asc | UP4(55.0), UP5(56.8), UP6(62.2), UP7(64.0) | identical | ✅ |
| A16 | WEST/dn/J3 `conn_x` asc | DN3(55.0), DN2(56.8), DN1(62.2), DN0(64.0) | identical | ✅ |
| A17 | WEST/dn/J4 `conn_x` asc | DN4(55.0), DN5(56.8), DN6(62.2), DN7(64.0) | identical | ✅ |
| A18 | page `conn_row_y`/`chip_row_y`/`conn_x` | re-derived midpoints `(P+N)/2`, 3 dp | identical | ✅ |
| A19 | authority block on lane_domain / capacity_frame / every frame | `{contract,pitch,span,bands,margin,edge_convention}` | present, hashes == disk | ✅ |
| A20 | `edge_convention` | `{"up":"lo","dn":"hi"}` | identical | ✅ |
| A21 | no-feasibility scan keys (`feasible`,`infeasible`,`selected`,`assigned`,`allocation`,`witness`,`matched`,`lane_index`,`track_y`) | 0 | 0 | ✅ |
| A22 | generator retired tokens (`0.6`, `12.0`, `tracks_y`) | 0 | 0 | ✅ |
| A23 | verifier imports producer | none | none | ✅ |
| A24 | double-run byte-identity | `run1 == run2` | `ff804e1e…ddf5cb6c` twice | ✅ |

Artifact SHA-256 (after two consecutive runs, identical):
`ff804e1edfacbf02e4227f10359a9217347ecdf0473801d655ef3a71ddf5cb6c`

`capacity_ok` is the **capacity criterion** only and is explicitly allowed by
the no-feasibility scan; no assignment/feasibility field is emitted.

---

## 2. Out of scope (belongs elsewhere)

| topic | owner | note |
|---|---|---|
| page → lane assignment / matching | **F4 / F-6b** | this card emits the candidate domain only; the double-end predicate + assignment feasibility is F-6b |
| R2 assignment feasibility verdict | **F4 / F-6b** | no `feasible` / `infeasible` field is emitted here |
| R4 / routing | **R4** | not touched |
| DRC | DRC gate | capacity criterion ≠ DRC |

---

## 3. Forbidden reverse-inference (must NOT be used as input)

- `SPEC.corridors.tracks_y` — retired W0 construct.
- Board copper / any copper-geometry reverse inference.
- Old W0 values `0.6` (margin) and `12.0` (retired track span).
- Any page → lane allocation, `lane_index`, matching, or `track_y`.

Lane domain derives **only** from `usable_y_spans` + `PITCH` + `margin=0`;
capacity derives **only** from `n_pairs` + `PITCH` + `y_hi-y_lo`.

---

## 4. Replay

```bash
python3 k2/tools/p3_v57_f3_lane_frame.py            # writes artifact (EMITTED)
python3 k2/tools/p3_v57_f3_lane_frame_validator.py  # PASS, exit 0
# double-run byte-identity:
python3 k2/tools/p3_v57_f3_lane_frame.py && sha256sum \
  k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_f3_lane_frame.json
```
