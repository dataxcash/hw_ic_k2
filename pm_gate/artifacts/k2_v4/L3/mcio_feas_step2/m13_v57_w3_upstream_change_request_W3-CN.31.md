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
 "same_layer_crossings": 0,
 "clearance_full": {
  "thresholds": {
   "track_track": 0.38,
   "track_track_escape": 0.28,
   "via_track": 0.4525,
   "via_track_escape": 0.3525,
   "via_via": 0.525
  },
  "viol_track_track": 0,
  "viol_via_track": 15,
  "viol_via_via": 0,
  "sample_tt": [],
  "sample_vt": [
   [
    "PCIE_DN1/out_MCIO",
    0.4,
    [
     85.75,
     48.1487
    ]
   ],
   [
    "PCIE_DN1/out_MCIO",
    0.4,
    [
     85.75,
     47.545
    ]
   ],
   [
    "PCIE_DN1/out_MCIO",
    0.4,
    [
     85.75,
     46.9412
    ]
   ],
   [
    "PCIE_DN1/out_MCIO",
    0.4,
    [
     85.75,
     46.3375
    ]
   ]
  ],
  "sample_vv": [],
  "n_vias": 248
 },
 "clearance_all_ok": false,
 "crossings_by_class": {
  "r1_5": 0,
  "stub": 0
 },
 "overlaps_by_class": {
  "r1_5": 0,
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