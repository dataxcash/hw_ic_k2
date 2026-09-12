# Upstream change request (engine-generated, W3-C7)

> Semantics: UPSTREAM_CHANGE_REQUEST / CERTIFICATE = escalation trigger, not an endpoint.
> Gate criterion: SUFFICIENT iff same_layer_crossings == 0 and lanes_needed <= lanes_avail

## Rejected (do not re-propose)
- In4.Cu as signal layer - REJECTED (spec: In4 = power plane P3V3; In2 = the only internal signal layer; PD/SI red line; measured regression 29/32 -> 8/32)

## Legal levers (signal-layer routing/topology only) + measured status
- lane order by source - WITHDRAWN (equals card v1.3 R-8 closed-form infeasibility proof)
- no_90deg channelized polyline - MEASURED worse (319 > 264) -> rolled back
- per-frame adaptive step - MEASURED neutral on this geometry
- R1 escape-domain widening - UPSTREAM ONLY

## Gate measurement (verification-based, R-23)
```json
{
 "same_layer_crossings": 324,
 "clearance_full": {
  "thresholds": {
   "track_track": 0.38,
   "track_track_escape": 0.28,
   "via_track": 0.4525,
   "via_track_escape": 0.3525,
   "via_via": 0.525
  },
  "viol_track_track": 293,
  "viol_via_track": 297,
  "viol_via_via": 0,
  "sample_tt": [
   [
    "PCIE_DN0/out_MCIO",
    "PCIE_DN1/out_MCIO",
    0.2
   ],
   [
    "PCIE_DN0/out_MCIO",
    "PCIE_UP0/input",
    0.1
   ],
   [
    "PCIE_DN0/out_MCIO",
    "PCIE_UP0/input",
    0.1
   ],
   [
    "PCIE_DN0/out_MCIO",
    "PCIE_UP0/input",
    0.1
   ]
  ],
  "sample_vt": [
   [
    "PCIE_UP2/out_J2",
    0.3233,
    [
     135.0,
     54.3
    ]
   ],
   [
    "PCIE_DN1/out_MCIO",
    0.2,
    [
     85.3,
     51.673
    ]
   ],
   [
    "PCIE_UP5/input",
    0.417,
    [
     85.3,
     51.673
    ]
   ],
   [
    "PCIE_UP5/input",
    0.417,
    [
     84.1,
     51.673
    ]
   ]
  ],
  "sample_vv": [],
  "n_vias": 91
 },
 "clearance_all_ok": false,
 "crossings_by_class": {
  "r1_5": 322,
  "stub": 0
 },
 "overlaps_by_class": {
  "r1_5": 2,
  "stub": 0
 },
 "r1_assigned": 32,
 "r1_required": 32,
 "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok and complete_clearance_suite == 0"
}
```

## Next
All in-layer legal levers measured neutral-or-worse => remaining options are UPSTREAM: (a) R1 escape domain widening, (b) F-5 frame/lane order revision, (c) connector/ball re-mapping, or (d) provide a GLOBAL infeasibility proof.