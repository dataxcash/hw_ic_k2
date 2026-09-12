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
 "same_layer_crossings": 28,
 "crossings_by_class": {
  "r1_5": 25,
  "stub": 0
 },
 "overlaps_by_class": {
  "r1_5": 3,
  "stub": 0
 },
 "r1_assigned": 29,
 "r1_required": 32,
 "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
}
```

## Next
All in-layer legal levers measured neutral-or-worse => remaining options are UPSTREAM: (a) R1 escape domain widening, (b) F-5 frame/lane order revision, (c) connector/ball re-mapping, or (d) provide a GLOBAL infeasibility proof.