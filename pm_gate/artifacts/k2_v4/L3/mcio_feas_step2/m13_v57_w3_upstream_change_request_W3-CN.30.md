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
  "viol_track_track": 7,
  "viol_via_track": 833,
  "viol_via_via": 0,
  "sample_tt": [
   [
    "PCIE_DN1/out_MCIO",
    "PCIE_DN1/out_MCIO",
    0.2236
   ],
   [
    "PCIE_DN2/out_MCIO",
    "PCIE_DN2/out_MCIO",
    0.1648
   ],
   [
    "PCIE_DN6/out_MCIO",
    "PCIE_DN6/out_MCIO",
    0.205
   ],
   [
    "PCIE_UP1/input",
    "PCIE_UP1/input",
    0.205
   ]
  ],
  "sample_vt": [
   [
    "PCIE_DN0/input",
    0.4,
    [
     85.2,
     57.94
    ]
   ],
   [
    "PCIE_DN0/input",
    0.38,
    [
     85.2,
     68.53
    ]
   ],
   [
    "PCIE_DN0/input",
    0.4,
    [
     84.8,
     68.15
    ]
   ],
   [
    "PCIE_DN0/input",
    0.38,
    [
     103.8915,
     68.15
    ]
   ]
  ],
  "sample_vv": [],
  "n_vias": 256
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