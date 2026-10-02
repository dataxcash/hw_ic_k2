# DISCLOSURE - K2 m7t6 closure package

- **packaged board**: `k2/pm_gate/artifacts/k2_v4/L6/board/k2_v4_8L.m7t7.kicad_pcb` (sha16 `7a99ab2e55e281b4`) - the board the NINE-ROW RECORD judged, so the governing
  C1/C2/C6 are that record's own rows (#K2-548 sec.1 invariant).
- **DFM vs the JLC HDI channel**: 16 PASS / 1 ACCEPT / 0 FAIL (17 items; details in `06_rulings/`).
- **NAMED RESIDUAL (accepted by #K2-551 sec.3 item 1)**: the delivered Gerber set is the `--check-zones`
  PLOT-TIME RECOMPUTED pour - the copper any plotter emits. On `MCU_VDD|In4.Cu` that pour is deeper outside
  the frame by about +10.31 mm2 against a 0.85 mm2 derived tolerance (a deeper plane pour). Real copper
  (tracks/vias/pads) is unchanged and no DFM row is affected. Readings: `../K2_M7T6_PACKAGE_DELIVERY_NOTE_v1.json` and the git history
  (R1898/R1900/R1908).
- **integrity**: `MANIFEST.json` lists every packaged file with its sha256; `07_verify/` carries the
  generator's own checks including the delivery-board identity row.
- **conventions**: per #K2-551 sec.3 item 3 this directory is generator output only; this package's
  governance/disclosure text lives outside it at `../K2_M7T6_PACKAGE_DELIVERY_NOTE_v1.json`.
- **not an order**: generating a package is not an order; ordering, quoting and lead time belong to the owner.
