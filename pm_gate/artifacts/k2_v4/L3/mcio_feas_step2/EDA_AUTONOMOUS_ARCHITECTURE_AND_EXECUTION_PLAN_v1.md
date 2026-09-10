# EDA Autonomous Engineering — Architecture and Execution Plan v1

> Status: architecture baseline.  This document defines the product boundary, the
> authority model, and the gate-controlled route from the current K2 work to the
> programme goal.  It is not an authority to change frozen inputs.

## 1. Product objective

For a supported product family, compile an approved, structured engineering
requirement into a manufacturable PCB.  Every result must be reproducible and
traceable to its sources, rules, and construction proof.  Every infeasible or
uncertain result must be a structured certificate that is sent to the *lowest
upstream layer that has authority to change its cause*.

"Automatic learning" is controlled knowledge promotion: it may propose a new
pattern, but it may not silently alter a production rule or a released design.

## 2. Layer contract and escalation rule

| Layer | Owner and output | May change | May not repair | Failure destination |
|---|---|---|---|---|
| L0 | Product requirement: interfaces, cost, size, performance | product decisions | physical geometry | product/system architecture |
| L1 | Schematic/netlist: part choice, connectivity, power topology | schematic and approved libraries | a board workaround for a netlist error | L0/L1 |
| L2 | Board intent: stackup, placement, corridors, budgets, interface topology | approved layout/constraint inputs | a shortage by ad-hoc routing | L1/L2 decision authority |
| L3 | Construction drawing: all R1--R4 assignments and nodes | deterministic drawing output only | allocation or intent | L2 |
| L4 | PCB construction: consume drawings, connect prescribed nodes | board implementation only | drawing geometry/resources | L3 |
| L5 | Independent sign-off: electrical, SI/PI/EMC, DFM/DFT and manufacturing checks | validation records | design generation | layer owning the failed premise |

**Escalation invariant:** L(n+1) must not search for a substitute for a failed
L(n) premise.  It emits either the prescribed output or a certificate containing
the minimal conflict core, applicable input/rule fingerprints, legal edit fields,
and target owner.

## 3. Required evidence protocol

All generated artifacts and certificates shall contain:

1. schema/version and producer/validator versions;
2. source fingerprints and authority classification;
3. deterministic decision or `INFEASIBLE` status;
4. resource demand, available capacity, and minimal unsatisfied core;
5. legal escape hatches expressed as upstream input changes, never downstream
   construction edits; and
6. independent validation result.

The generator and validator must be separately implemented.  DRC is a check,
not a source of geometry or a repair mechanism.

## 4. Programme gap assessment

| Programme capability | Present K2 evidence | Remaining deliverable |
|---|---|---|
| Requirement to schematic | Existing netlist/ballmap are consumed | requirement schema, part/library authority, schematic generator and independent ERC/netlist proof |
| Proposal and design freeze | local feasibility work exists | alternative generator, cost/risk/performance objective model, decision record |
| Board intent | B1 synthetic kernel tests PASS; W0 derives real frames | approved real-board intent or L2 infeasibility decision |
| Construction drawings | manifest, R1 and landing evidence exist | joint R1--R4 allocation, complete 34-page JSON and independent true-drawing gates |
| PCB construction | S2 contract is designed | drawing-only consumer and 100% connect-the-dots proof |
| Learning | historical artifacts exist | versioned case store, candidate-rule tests, reviewed promotion and regression corpus |
| Manufacturing sign-off | local geometry checks exist | SI/PI/EMC, impedance, DFM/DFT, library and fabrication sign-off contracts |

## 5. Current K2 baseline (HEAD `67cc7d6`)

- Proven: 34-page manifest; A1.1, A1.3 and A1.4 synthetic gates; BIG B1.1--B1.4;
  R1 `32/32 ESCAPABLE`; 64 authoritative chip landing rows.
- W0 real-frame artifact reports data frames but four REFCLK-band certificates
  (two pages across EAST and WEST).  This is an **L2 blocking outcome until
  independently reviewed and either accepted as a formal infeasibility result or
  changed by an authorized upstream decision**.
- W1 supplies a no-crossing assignment oracle and W2 supplies connector-column
  data.  Neither is authority to start W3 while W0 remains blocking.
- The worktree contains a deliberately isolated `_shared` state and historical
  untracked artifacts.  They must not be folded into functional commits.

## 6. Gate-controlled execution plan

```text
G0 baseline record
  -> G1 W0 independent B1.5 review
  -> G2 L2 decision: accept certificate OR change approved intent
  -> G3 W1/W2 interface review and contract freeze
  -> G4 W3 joint R1--R4 allocation + 34-page drawings
  -> G5 W4 independent true-drawing validation
  -> G6 L4 drawing-only PCB construction
  -> G7 L5 manufacturing sign-off and knowledge promotion review
```

### G0--G3: current work

1. Preserve the baseline correction and workspace isolation record; do not clean,
   reset, or absorb unrelated artifacts.
2. Independently reproduce W0 from only its declared sources.  Review the
   REFCLK certificates for geometry, layer validity, completeness, determinism,
   and a correctly identified L2 owner.
3. If W0 is confirmed infeasible, issue a decision card to L2.  Legal choices are
   an approved F.Cu out-of-band route with complete keepout predicates, a changed
   corridor/placement/stackup, or an interface/topology change.  W3 is forbidden
   until one choice has been constructed and validated.
4. Independently review W1/W2 schema compatibility and freeze their input/output
   contract only after G2 permits continuation.

### Current worker cards and architect acceptance

| Card | Worker scope | Required deliverable | Architect acceptance |
|---|---|---|---|
| R0 | Reproduce/review W0 only | B1.5 review record: declared inputs, double-run hashes, per-certificate proof, owner and legal L2 changes | Every certificate is reproduced from the declared authority sources; no hidden old `tracks_y` authority; clear `PASS` or `BLOCK` |
| R1 | Review W1/W2 interfaces only | schema gap matrix from W0/R1/manifest to W3; required fields and independent-validator boundary | Must show actual 32 data pages and 2 REFCLK pages are represented, and propagate any W0 block |
| D0 | After R0/R1 only | L2 decision card: selected legal change or accepted infeasibility | Signed authority/input version; no mutation of frozen files bundled with the decision |
| W3 | Released only by D0=continue | complete joint allocation or a global certificate | all-or-certificate, order-independent, no per-net first-fit |
| W4 | Released only after W3 | independent true-drawing reports | all pages and all strong nodes checked; a partial pass is rejected |

The active cards are R0 and R1.  D0 is deliberately pending: a worker may gather
evidence but may not choose an L2 design change without its authorized owner.

### Review result — G1 is BLOCKED (2026-09-10)

Independent reviews change the current status from "W0 certificate pending L2
decision" to **"W0 is not yet a B1.5 result"**:

- W0 uses whole-board `[33.3, 78.7]` rather than deriving corridor-by-layer
  usable spans from the board minus component/keepout projections.  Its `0.6`
  margin and `12.0` reach budget have no locked authority source.
- Its four REFCLK entries are candidate conflicts, not conservation certificates:
  they do not state required/available/shortage, enumerate a resource domain,
  use the WEST endpoints correctly, or establish a minimal conflict core.
- W0 lacks the full input closure (SPEC, rules, stackup, geometry and producer
  hashes).  A deterministic double run is insufficient when its declared
  inputs are incomplete.
- W1 is a useful synthetic `n<=6` no-crossing/MUS algorithm oracle, but does not
  bind real manifest/W0/R1 inputs or emit actual K2 assignments.  W2 is a
  connector-column data block, not R3/R4 candidate domains or a conflict graph.

Therefore the only released implementation card is **W0-R**, not W3:

1. Create a versioned input manifest for board outline, authority placement,
   keepouts, corridor x-ranges, stackup, endpoint anchors and data/REFCLK rules.
2. Derive `usable_y_spans` separately for every `(corridor, layer)` by subtracting
   projected forbidden geometry; record the predicate and source hash.
3. Construct data resource domains and reach predicates from those spans.
4. Construct REFCLK domains per page and per corridor using the correct J2/J3/J4
   anchors.  Emit either legal resources or a quantitative certificate with
   `required`, `available`, `shortage`, conflicting resources and canonical
   minimal core.
5. Add a separately implemented validator that does not reuse the generator's
   span or REFCLK decision logic.

W0-R may add tools and artifacts but must not modify SPEC, frozen placement,
`_shared`, W1/W2, or PCB copper.  Its terminal status is only `B1.5 PASS` or
`B1.5 INFEASIBLE_CERT`; anything else remains `BLOCKED` and is not passed to W3.

### G4--G7: work released only after G3

- **W3:** deterministic, order-independent joint allocation.  It must consume
  W0/W1/W2 plus R1, emit either all 34 pages or one global minimal certificate,
  and never allocate "first available" resources per net.
- **W4:** separate A1.2/A1.3/A1.4 true-drawing validator.  A partial drawing is
  not a pass.
- **L4:** no route search.  The implementation connects only prescribed nodes;
  any mismatch returns the drawing to W3.
- **L5:** sign-off results are evidence and learning inputs, not permission for
  an implementation-stage repair.

## 7. Knowledge promotion lifecycle

`case record -> candidate pattern -> independent test + regression -> reviewed
versioned rule -> production use`.

No artifact may skip from a single K2 result directly into a generally applicable
rule.  Promotion needs its scope, assumptions, counterexamples, validator and
rollback version recorded.

## 8. Definition of success for the first MVP

The first release target is deliberately narrow: for K2 with a frozen approved
netlist, libraries, placement, stackup and rules, produce either (a) a complete,
independently validated construction drawing consumed unchanged into PCB, or (b)
a reproducible L2-or-earlier certificate.  Only after this loop is stable should
the programme claim automated schematic generation or automatic proposal/freeze.
