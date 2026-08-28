# 低速域 板↔SPEC 一致性差异报告 (B2)

- board: `strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb`（真源=板）
- spec: `strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/L3/SPEC_k2_v4.json`
- 对比网数: 22 / 有差异网: 22

## 汇总

| 维度 | 板上 | SPEC | board_only | spec_only | 层差异 |
|---|---|---|---|---|---|
| segments | 162 | 162 | 92 | 92 | 1 |
| vias | 65 | 98 | 22 | 55 | - |

## 逐网差异

### I2C1_SCL

- segments: match=4 board_only=5 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (45.250,37.450) → (45.250,60.630)
  - [board_only] B.Cu (45.250,37.450) → (55.900,37.450)
  - [board_only] B.Cu (45.250,37.450) → (133.950,37.450)
  - [board_only] B.Cu (55.900,37.450) → (55.900,64.900)
  - [board_only] B.Cu (133.950,37.450) → (133.950,56.100)
  - [spec_only] B.Cu (45.250,36.200) → (45.250,60.630)
  - [spec_only] B.Cu (51.900,36.200) → (51.900,64.900)
  - [spec_only] B.Cu (51.900,64.900) → (55.900,64.900)
  - [spec_only] B.Cu (133.950,36.200) → (133.950,56.100)
  - [spec_only] In6.Cu (45.250,36.200) → (51.900,36.200)
  - [spec_only] In6.Cu (45.250,36.200) → (133.950,36.200)
- vias: match=3 board_only=0 spec_only=3
  - [spec_only] via (45.250,36.200)
  - [spec_only] via (51.900,36.200)
  - [spec_only] via (133.950,36.200)

### I2C1_SDA

- segments: match=4 board_only=5 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (45.700,38.500) → (45.700,61.910)
  - [board_only] B.Cu (45.700,38.500) → (54.350,38.500)
  - [board_only] B.Cu (45.700,38.500) → (134.620,38.500)
  - [board_only] B.Cu (54.350,38.500) → (54.350,66.850)
  - [board_only] B.Cu (134.620,38.500) → (134.620,56.100)
  - [spec_only] B.Cu (45.700,36.550) → (45.700,61.910)
  - [spec_only] B.Cu (48.350,36.550) → (48.350,66.850)
  - [spec_only] B.Cu (48.350,66.850) → (54.350,66.850)
  - [spec_only] B.Cu (134.620,36.550) → (134.620,56.100)
  - [spec_only] In6.Cu (45.700,36.550) → (48.350,36.550)
  - [spec_only] In6.Cu (45.700,36.550) → (134.620,36.550)
- vias: match=3 board_only=0 spec_only=3
  - [spec_only] via (45.700,36.550)
  - [spec_only] via (48.350,36.550)
  - [spec_only] via (134.620,36.550)

### I2C2_SCL

- segments: match=3 board_only=3 spec_only=4 layer_mismatch=0
  - [board_only] B.Cu (35.250,54.450) → (35.250,56.000)
  - [board_only] B.Cu (35.250,54.450) → (52.150,54.450)
  - [board_only] B.Cu (52.150,54.450) → (52.150,68.350)
  - [spec_only] B.Cu (35.250,34.000) → (35.250,56.000)
  - [spec_only] B.Cu (38.150,34.000) → (38.150,68.350)
  - [spec_only] B.Cu (38.150,68.350) → (50.150,68.350)
  - [spec_only] In6.Cu (35.250,34.000) → (38.150,34.000)
- vias: match=1 board_only=1 spec_only=3
  - [board_only] via (52.150,68.350)
  - [spec_only] via (35.250,34.000)
  - [spec_only] via (38.150,34.000)
  - [spec_only] via (50.150,68.350)

### I2C2_SDA

- segments: match=3 board_only=3 spec_only=4 layer_mismatch=1
  - [board_only] B.Cu (34.750,54.700) → (34.750,55.650)
  - [board_only] B.Cu (34.750,55.650) → (53.650,55.650)
  - [board_only] B.Cu (53.650,55.650) → (53.650,69.600)
  - [spec_only] B.Cu (34.750,54.700) → (34.750,62.550)
  - [spec_only] B.Cu (54.450,69.600) → (56.450,69.600)
  - [spec_only] B.Cu (56.450,62.550) → (56.450,69.600)
  - [spec_only] In6.Cu (34.750,62.550) → (56.450,62.550)
  - [layer_mismatch] 几何 (34.750,54.700) → (34.750,55.650): 板=['B.Cu', 'F.Cu'] spec=['F.Cu']
- vias: match=1 board_only=1 spec_only=3
  - [board_only] via (53.650,69.600)
  - [spec_only] via (34.750,62.550)
  - [spec_only] via (54.450,69.600)
  - [spec_only] via (56.450,62.550)

### PD0_U3

- segments: match=3 board_only=5 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (50.050,45.700) → (98.300,45.700)
  - [board_only] B.Cu (91.680,65.750) → (91.680,66.150)
  - [board_only] B.Cu (91.680,65.750) → (98.300,65.750)
  - [board_only] B.Cu (98.300,45.700) → (98.300,66.150)
  - [board_only] F.Cu (95.225,57.200) → (95.225,59.700)
  - [spec_only] B.Cu (50.050,36.900) → (50.050,45.700)
  - [spec_only] B.Cu (92.480,36.900) → (92.480,66.150)
  - [spec_only] In6.Cu (50.050,36.900) → (92.480,36.900)
- vias: match=1 board_only=2 spec_only=3
  - [board_only] via (91.680,66.150)
  - [board_only] via (95.225,57.200)
  - [spec_only] via (50.050,36.900)
  - [spec_only] via (92.480,36.900)
  - [spec_only] via (92.480,66.150)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.25 pad (95.225,59.700) → via (95.225,58.675)

### PD0_U7

- segments: match=3 board_only=4 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (49.700,45.000) → (49.700,48.900)
  - [board_only] B.Cu (49.700,45.000) → (91.700,45.000)
  - [board_only] B.Cu (91.700,45.000) → (91.700,47.700)
  - [board_only] F.Cu (92.425,47.700) → (92.425,48.500)
  - [spec_only] B.Cu (49.700,37.250) → (49.700,48.900)
  - [spec_only] B.Cu (91.700,37.250) → (91.700,47.700)
  - [spec_only] In6.Cu (49.700,37.250) → (91.700,37.250)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (92.425,48.500)
  - [spec_only] via (49.700,37.250)
  - [spec_only] via (91.700,37.250)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.25 pad (92.425,47.700) → via (92.425,48.725)

### PD1_U3

- segments: match=2 board_only=5 spec_only=4 layer_mismatch=0
  - [board_only] B.Cu (53.400,45.350) → (97.080,45.350)
  - [board_only] B.Cu (92.830,64.850) → (92.830,65.100)
  - [board_only] B.Cu (92.830,64.850) → (97.050,64.850)
  - [board_only] B.Cu (97.080,45.350) → (97.080,64.850)
  - [board_only] F.Cu (94.825,58.900) → (94.825,59.700)
  - [spec_only] B.Cu (53.400,37.600) → (53.400,45.350)
  - [spec_only] B.Cu (97.050,37.600) → (97.050,64.850)
  - [spec_only] F.Cu (92.830,65.100) → (92.830,65.700)
  - [spec_only] In6.Cu (53.400,37.600) → (97.050,37.600)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (94.825,58.900)
  - [spec_only] via (53.400,37.600)
  - [spec_only] via (97.050,37.600)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.26 pad (94.825,59.700) → via (94.825,56.975)

### PD1_U7

- segments: match=2 board_only=4 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (53.050,48.900) → (53.050,52.100)
  - [board_only] B.Cu (53.050,52.100) → (92.830,52.100)
  - [board_only] B.Cu (92.830,47.650) → (92.830,52.100)
  - [board_only] F.Cu (92.825,47.700) → (92.830,47.080)
  - [spec_only] B.Cu (53.050,37.950) → (53.050,48.900)
  - [spec_only] B.Cu (92.830,37.950) → (92.830,47.650)
  - [spec_only] In6.Cu (53.050,37.950) → (92.830,37.950)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (92.830,47.080)
  - [spec_only] via (53.050,37.950)
  - [spec_only] via (92.830,37.950)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.26 pad (92.825,47.700) → via (92.825,49.025)

### PERSTA#

- segments: match=3 board_only=5 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (38.700,37.800) → (38.700,51.750)
  - [board_only] B.Cu (38.700,37.800) → (43.650,37.800)
  - [board_only] B.Cu (43.650,35.900) → (43.650,37.800)
  - [board_only] B.Cu (43.650,37.800) → (136.350,37.800)
  - [board_only] B.Cu (136.350,37.800) → (136.350,56.700)
  - [spec_only] B.Cu (38.700,51.750) → (44.700,51.750)
  - [spec_only] B.Cu (43.650,35.900) → (43.650,38.300)
  - [spec_only] B.Cu (44.700,38.300) → (44.700,51.750)
  - [spec_only] B.Cu (136.350,38.300) → (136.350,56.700)
  - [spec_only] In6.Cu (43.650,38.300) → (44.700,38.300)
  - [spec_only] In6.Cu (43.650,38.300) → (136.350,38.300)
- vias: match=3 board_only=0 spec_only=3
  - [spec_only] via (43.650,38.300)
  - [spec_only] via (44.700,38.300)
  - [spec_only] via (136.350,38.300)

### PERSTB#

- segments: match=1 board_only=5 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (44.900,38.150) → (44.900,64.500)
  - [board_only] B.Cu (44.900,38.150) → (136.000,38.150)
  - [board_only] B.Cu (136.000,38.150) → (136.000,62.100)
  - [board_only] F.Cu (44.900,64.500) → (60.100,64.500)
  - [board_only] F.Cu (60.100,63.950) → (60.100,64.500)
  - [spec_only] B.Cu (44.900,64.500) → (46.100,64.500)
  - [spec_only] B.Cu (46.100,38.650) → (46.100,64.500)
  - [spec_only] B.Cu (136.000,38.650) → (136.000,62.100)
  - [spec_only] F.Cu (46.500,62.200) → (60.100,62.200)
  - [spec_only] F.Cu (60.100,62.200) → (60.100,63.950)
  - [spec_only] In6.Cu (46.100,38.650) → (136.000,38.650)
- vias: match=2 board_only=0 spec_only=2
  - [spec_only] via (46.100,38.650)
  - [spec_only] via (136.000,38.650)

### STRAP_EQ0_1_U3

- segments: match=3 board_only=4 spec_only=4 layer_mismatch=0
  - [board_only] B.Cu (50.650,52.850) → (50.650,64.850)
  - [board_only] B.Cu (50.650,52.850) → (93.200,52.850)
  - [board_only] B.Cu (93.200,52.850) → (93.200,66.800)
  - [board_only] F.Cu (94.425,57.200) → (94.425,59.700)
  - [spec_only] B.Cu (50.650,41.650) → (50.650,64.850)
  - [spec_only] B.Cu (93.200,66.800) → (94.800,66.800)
  - [spec_only] B.Cu (94.800,41.650) → (94.800,66.800)
  - [spec_only] In6.Cu (50.650,41.650) → (94.800,41.650)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (94.425,57.200)
  - [spec_only] via (50.650,41.650)
  - [spec_only] via (94.800,41.650)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.27 pad (94.425,59.700) → via (94.425,58.375)

### STRAP_EQ0_1_U7

- segments: match=4 board_only=5 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (54.000,67.650) → (90.550,67.650)
  - [board_only] B.Cu (90.550,46.700) → (90.550,67.650)
  - [board_only] B.Cu (90.550,46.700) → (93.220,46.700)
  - [board_only] B.Cu (93.220,46.700) → (93.220,47.320)
  - [board_only] F.Cu (93.225,47.700) → (93.225,48.500)
  - [spec_only] B.Cu (48.000,43.250) → (48.000,67.650)
  - [spec_only] B.Cu (48.000,67.650) → (54.000,67.650)
  - [spec_only] B.Cu (90.550,43.250) → (90.550,46.700)
  - [spec_only] B.Cu (93.220,43.250) → (93.220,47.320)
  - [spec_only] In6.Cu (48.000,43.250) → (90.550,43.250)
  - [spec_only] In6.Cu (90.550,43.250) → (93.220,43.250)
- vias: match=3 board_only=1 spec_only=3
  - [board_only] via (93.225,48.500)
  - [spec_only] via (48.000,43.250)
  - [spec_only] via (90.550,43.250)
  - [spec_only] via (93.220,43.250)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.27 pad (93.225,47.700) → via (93.225,48.725)

### STRAP_EQ0_U3

- segments: match=3 board_only=5 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (48.900,54.800) → (48.900,59.000)
  - [board_only] B.Cu (48.900,54.800) → (94.000,54.800)
  - [board_only] B.Cu (94.000,54.800) → (94.000,60.100)
  - [board_only] B.Cu (94.000,60.100) → (94.420,60.100)
  - [board_only] F.Cu (93.225,65.700) → (93.225,68.200)
  - [spec_only] B.Cu (48.900,43.600) → (48.900,59.000)
  - [spec_only] B.Cu (94.420,43.600) → (94.420,60.100)
  - [spec_only] In6.Cu (48.900,43.600) → (94.420,43.600)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (93.225,68.200)
  - [spec_only] via (48.900,43.600)
  - [spec_only] via (94.420,43.600)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.59 pad (93.225,65.700) → via (93.225,68.425)

### STRAP_EQ0_U7

- segments: match=2 board_only=4 spec_only=5 layer_mismatch=0
  - [board_only] B.Cu (53.050,52.500) → (53.050,59.000)
  - [board_only] B.Cu (53.050,52.500) → (94.420,52.500)
  - [board_only] B.Cu (94.420,42.350) → (94.420,52.500)
  - [board_only] F.Cu (94.425,40.900) → (94.425,41.700)
  - [spec_only] B.Cu (52.650,49.250) → (52.650,59.000)
  - [spec_only] B.Cu (52.650,59.000) → (53.050,59.000)
  - [spec_only] B.Cu (93.620,42.350) → (93.620,49.250)
  - [spec_only] B.Cu (93.620,42.350) → (94.420,42.350)
  - [spec_only] In6.Cu (52.650,49.250) → (93.620,49.250)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (94.425,40.900)
  - [spec_only] via (52.650,49.250)
  - [spec_only] via (93.620,49.250)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.59 pad (94.425,41.700) → via (94.425,40.675)

### STRAP_EQ1_1_U3

- segments: match=3 board_only=4 spec_only=4 layer_mismatch=0
  - [board_only] B.Cu (49.400,54.100) → (97.480,54.100)
  - [board_only] B.Cu (49.800,54.100) → (49.800,69.000)
  - [board_only] B.Cu (97.480,54.100) → (97.480,66.300)
  - [board_only] F.Cu (93.620,60.430) → (93.625,59.700)
  - [spec_only] B.Cu (37.800,34.350) → (37.800,69.000)
  - [spec_only] B.Cu (37.800,69.000) → (49.800,69.000)
  - [spec_only] B.Cu (97.480,34.350) → (97.480,66.150)
  - [spec_only] In6.Cu (37.800,34.350) → (97.480,34.350)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (93.620,60.430)
  - [spec_only] via (37.800,34.350)
  - [spec_only] via (97.480,34.350)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.29 pad (93.625,59.700) → via (93.625,56.975)

### STRAP_EQ1_1_U7

- segments: match=4 board_only=6 spec_only=6 layer_mismatch=0
  - [board_only] B.Cu (51.800,68.000) → (51.800,68.750)
  - [board_only] B.Cu (51.800,68.000) → (90.900,68.000)
  - [board_only] B.Cu (90.900,46.350) → (90.900,68.000)
  - [board_only] B.Cu (90.900,46.350) → (94.030,46.350)
  - [board_only] B.Cu (94.030,46.350) → (94.030,47.650)
  - [board_only] F.Cu (94.025,47.700) → (94.025,48.500)
  - [spec_only] B.Cu (51.800,68.750) → (55.800,68.750)
  - [spec_only] B.Cu (55.800,67.650) → (55.800,68.750)
  - [spec_only] B.Cu (90.900,46.350) → (90.900,67.650)
  - [spec_only] B.Cu (95.230,47.650) → (95.230,67.650)
  - [spec_only] In6.Cu (55.800,67.650) → (90.900,67.650)
  - [spec_only] In6.Cu (90.900,67.650) → (95.230,67.650)
- vias: match=2 board_only=2 spec_only=4
  - [board_only] via (94.025,48.500)
  - [board_only] via (94.030,47.650)
  - [spec_only] via (55.800,67.650)
  - [spec_only] via (90.900,67.650)
  - [spec_only] via (95.230,47.650)
  - [spec_only] via (95.230,67.650)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.29 pad (94.025,47.700) → via (94.025,49.025)

### STRAP_EQ1_U3

- segments: match=3 board_only=4 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (49.400,55.500) → (49.400,63.000)
  - [board_only] B.Cu (49.400,55.900) → (95.600,55.900)
  - [board_only] B.Cu (95.600,55.900) → (95.600,60.450)
  - [board_only] F.Cu (93.625,65.700) → (93.625,66.500)
  - [spec_only] B.Cu (49.400,50.150) → (49.400,63.000)
  - [spec_only] B.Cu (95.600,50.150) → (95.600,60.450)
  - [spec_only] In6.Cu (49.400,50.150) → (95.600,50.150)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (93.625,66.500)
  - [spec_only] via (49.400,50.150)
  - [spec_only] via (95.600,50.150)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.60 pad (93.625,65.700) → via (93.625,66.725)

### STRAP_EQ1_U7

- segments: match=4 board_only=4 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (39.600,37.100) → (86.700,37.100)
  - [board_only] B.Cu (86.700,37.100) → (86.700,41.260)
  - [board_only] B.Cu (86.700,41.260) → (94.030,41.260)
  - [board_only] F.Cu (94.025,39.200) → (94.025,41.700)
  - [spec_only] B.Cu (37.100,34.700) → (37.100,37.100)
  - [spec_only] B.Cu (94.030,34.700) → (94.030,41.260)
  - [spec_only] In6.Cu (37.100,34.700) → (94.030,34.700)
- vias: match=1 board_only=2 spec_only=3
  - [board_only] via (39.600,37.100)
  - [board_only] via (94.025,39.200)
  - [spec_only] via (37.100,34.700)
  - [spec_only] via (37.100,37.100)
  - [spec_only] via (94.030,34.700)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.60 pad (94.025,41.700) → via (94.025,38.975)

### STRAP_MODE_U3

- segments: match=4 board_only=3 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (51.050,55.150) → (93.620,55.150)
  - [board_only] B.Cu (93.620,55.150) → (93.620,59.800)
  - [board_only] F.Cu (94.025,65.700) → (94.025,68.200)
  - [spec_only] B.Cu (51.050,50.850) → (51.050,55.150)
  - [spec_only] B.Cu (93.620,50.850) → (93.620,59.800)
  - [spec_only] In6.Cu (51.050,50.850) → (93.620,50.850)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (94.025,68.200)
  - [spec_only] via (51.050,50.850)
  - [spec_only] via (93.620,50.850)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.61 pad (94.025,65.700) → via (94.025,68.425)

### STRAP_MODE_U7

- segments: match=4 board_only=3 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (54.850,53.400) → (93.620,53.400)
  - [board_only] B.Cu (93.620,42.350) → (93.620,53.400)
  - [board_only] F.Cu (93.625,40.900) → (93.625,41.700)
  - [spec_only] B.Cu (54.850,51.650) → (54.850,53.400)
  - [spec_only] B.Cu (96.120,42.350) → (96.120,51.650)
  - [spec_only] In6.Cu (54.850,51.650) → (96.120,51.650)
- vias: match=1 board_only=2 spec_only=3
  - [board_only] via (93.620,42.350)
  - [board_only] via (93.625,40.900)
  - [spec_only] via (54.850,51.650)
  - [spec_only] via (96.120,42.350)
  - [spec_only] via (96.120,51.650)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.61 pad (93.625,41.700) → via (93.625,40.675)

### STRAP_READ_EN_U3

- segments: match=5 board_only=3 spec_only=3 layer_mismatch=0
  - [board_only] B.Cu (51.550,56.250) → (96.680,56.250)
  - [board_only] B.Cu (96.680,56.250) → (96.680,59.250)
  - [board_only] F.Cu (92.425,65.700) → (92.425,68.200)
  - [spec_only] B.Cu (51.550,52.000) → (51.550,56.250)
  - [spec_only] B.Cu (96.680,52.000) → (96.680,59.250)
  - [spec_only] In6.Cu (51.550,52.000) → (96.680,52.000)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (92.425,68.200)
  - [spec_only] via (51.550,52.000)
  - [spec_only] via (96.680,52.000)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U3.57 pad (92.425,65.700) → via (92.425,66.725)

### STRAP_READ_EN_U7

- segments: match=3 board_only=3 spec_only=4 layer_mismatch=0
  - [board_only] B.Cu (53.400,53.750) → (95.220,53.750)
  - [board_only] B.Cu (95.220,42.350) → (95.220,53.750)
  - [board_only] F.Cu (95.225,40.900) → (95.225,41.700)
  - [spec_only] B.Cu (53.400,53.750) → (53.800,53.750)
  - [spec_only] B.Cu (53.800,35.850) → (53.800,53.750)
  - [spec_only] B.Cu (95.220,35.850) → (95.220,42.350)
  - [spec_only] In6.Cu (53.800,35.850) → (95.220,35.850)
- vias: match=2 board_only=1 spec_only=2
  - [board_only] via (95.225,40.900)
  - [spec_only] via (53.800,35.850)
  - [spec_only] via (95.220,35.850)
- chip_escape: frozen=1 in_spec=0 missing=1
  - [missing] U7.57 pad (95.225,41.700) → via (95.225,38.975)
