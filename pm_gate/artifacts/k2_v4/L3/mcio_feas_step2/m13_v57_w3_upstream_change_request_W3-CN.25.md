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
 "same_layer_crossings": 17,
 "clearance_full": {
  "thresholds": {
   "track_track": 0.38,
   "via_track": 0.4525,
   "via_via": 0.525
  },
  "viol_track_track": 23,
  "viol_via_track": 56,
  "viol_via_via": 20,
  "sample_tt": [
   [
    "PCIE_DN0/input",
    "PCIE_UP1/out_J2",
    0.1075
   ],
   [
    "PCIE_DN1/input",
    "PCIE_DN2/input",
    0.3323
   ],
   [
    "PCIE_DN1/input",
    "PCIE_DN2/input",
    0.3578
   ],
   [
    "PCIE_DN1/input",
    "PCIE_UP1/out_J2",
    0.1774
   ]
  ],
  "sample_vt": [
   [
    "PCIE_DN1/input",
    0.4131,
    [
     86.65,
     58.19
    ]
   ],
   [
    "PCIE_DN1/input",
    0.4102,
    [
     86.65,
     58.19
    ]
   ],
   [
    "PCIE_UP1/out_J2",
    0.1075,
    [
     86.65,
     58.19
    ]
   ],
   [
    "PCIE_UP0/out_J2",
    0.4028,
    [
     84.85,
     57.12
    ]
   ]
  ],
  "sample_vv": [
   [
    [
     86.65,
     58.19
    ],
    [
     86.8,
     58.273
    ],
    0.1714
   ],
   [
    [
     86.65,
     58.19
    ],
    [
     86.8,
     58.31
    ],
    0.1921
   ],
   [
    [
     87.85,
     58.19
    ],
    [
     88.35,
     58.22
    ],
    0.5009
   ],
   [
    [
     87.85,
     58.19
    ],
    [
     88.0,
     58.273
    ],
    0.1714
   ]
  ],
  "n_vias": 248
 },
 "clearance_all_ok": false,
 "crossings_by_class": {
  "r1_5": 17,
  "stub": 0
 },
 "overlaps_by_class": {
  "r1_5": 0,
  "stub": 0
 },
 "r1_assigned": 31,
 "r1_required": 32,
 "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
}
```

## Next
All in-layer legal levers measured neutral-or-worse => remaining options are UPSTREAM: (a) R1 escape domain widening, (b) F-5 frame/lane order revision, (c) connector/ball re-mapping, or (d) provide a GLOBAL infeasibility proof.