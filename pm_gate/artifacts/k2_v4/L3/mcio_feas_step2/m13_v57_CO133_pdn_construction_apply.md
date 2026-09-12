# CO-133（L2 自裁 · 施工期物理施加）：PDN 声明区落板 + 板实合规机判

**结论**：rev-18 SPEC 声明的 PDN 铜**已物理落板**（`k2_v4_8L.l4.kicad_pcb` `0e636a67c1472462`→`a3ce9ab803045a0a`）。

## 施加内容（坐标逐字取自 SPEC，零搜索/零随机）
| 类 | 数量 | 说明 |
|---|---|---|
| zone | 9 | 3×GND 平面（In1/In3/In6，整框 23.3..142.7 / 33.3..78.7）+ 6×In4 电源区；其中 3 区 `fill_priority=1`（与同网宿主平面重叠） |
| via | 241 | power_zones.vias 17 + power_pad_connect 185 + gnd_stitch 39（blocked 61 显式跳过） |
| track | 185 | ppc F.Cu 短段（pad_pos→via_pos，宽 = SPEC `stub_width_mm` 0.2） |

## 机判（A/B/C/D 全 PASS）
- **A 板实 vs SPEC：逐项相等**（zone 几何+层+优先级 / via 坐标多重集 / 短段坐标+宽）。
- **B DRC 中性**：kicad-cli `--severity-all` 违规**类型逐项同**（42/42，全为 lib_footprint_*/silk）；未连项 348→179。
- **C 幂等**：净板与已施工板两次投喂产出**同一字节**（purge-then-add + CO-49 canonicalize；实测重跑后板 sha 不变）。
  ⇒ `p3_v57_co102_pdn_apply_local.py` 追加④ purge-then-add（删本阶段将重发的 PDN 网铜），与 `l4_apply_drawing` 同构。
- **D 图纸不动**：2523 段 / 252 via（PCIE_*）逐条不变。

## 连带更正（显式登记，见 register / co133 记录 findings）
1. `co91` via-via 孔缘分支**多扣一次 `via_r`**（与其 `drc_rules.json` geometry_translation 相悖）⇒ 施工后 14 项假阳性；公式更正后 0/0，真值 +0.284（req 0.25）。
2. `co104` replay 场景改**排除计划自身网**（板态无关）+ V3 断言/verdict 改**数据派生**；残留：canonical replay 3 vs 声明 blocked 4 ⇒ 声明**偏保守 1 项**（无功能影响）。
3. provenance pin：co105←co98 刷新；co111←l5_si / co118←co95 明列 co120 EXEMPT（point-in-time）。

## 重基线（全 PASS）
G4 `6ad2ff97101cbc53`（不动）｜G5 `6d22980eec78094a`（不动）｜L4 `1edc5923e7a21d26`（viol 0）｜
L5 fab `fb52d100055e04f0`（DFM new=0）/ SI `b5797a58d627ab55`（0.1300）｜co95 `0bc98d2037ce5b47` / co98 `5b4ae070e4542840`（55/0/0）｜
co124 `f871db7015da3597`｜co77/co78/co81/co84/co87/co88/co69/co91/co97/co99/co102/co104/co105/co106/co120 全 PASS。

**未决**：非执行者复评（本件 + rev-18 基线）；owner ③ 0.875 口径；外部输入（板厂券/SI9000、PM 压降·热）。
