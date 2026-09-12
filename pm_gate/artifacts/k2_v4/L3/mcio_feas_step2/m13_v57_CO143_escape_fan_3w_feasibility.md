# CO-143 — 逃生扇对间 3W：定位修正 + 施加可行性研究（L2 只读）

- verdict：**FEASIBLE_BUT_REQUIRES_FAN_REDERIVATION**

## 定位修正
- 旧（CO-141 附记2）：CO-141 附记2：f13 pair_xorder / p3_v57_f13_r1_pair_xorder.py
- 不成立原因：co16 形状的 R1 逃生列 = co16_prepare() O(1) 消费 CO16-ALLOC.7；r1_place()/pair_xorder 在 co16 路径不执行 ⇒ 附记2 两次实验为 no-op
- 真实所在：p3_v57_co10_west_fan_probe.py check()（逃生竖列落位判据） → CO16-ALLOC → G4(co16) → L4

## 机判
| 配置 | 落位 | B.Cu 对间最小中心距 | <3W 对数 |
|---|---|---|---|
| A 基线 | 32/32 | 0.55 | 14 |
| B 仅并 3W | 32/32 | 0.65 | 0 |
| C rev+3W+PDN | 31/32 | 0.65 | 0 |
| C xasc+3W+PDN | 30/32 | 0.65 | 0 |

- DP 分带可满足：{"('EAST_CHIP_TO_J2', 'up')": {"pages": 8, "legal_rows_total": 3589, "dp_end_states": 428, "feasible": true}, "('WEST_MCIO_TO_CHIP', 'dn')": {"pages": 8, "legal_rows_total": 3670, "dp_end_states": 386, "feasible": true}}

## 施加实验（已还原）
- 把 3W 并入 check（CO10_IP3W=1）并重生成 ALLOC.8 → G4 → L4 板 → co133 --apply
- DRC：{'baseline': 42, 'after': 45}；3× clearance：UP0/out_J2 N corner via × GND stitch via (83.575,56.516)，铜距 0.1587 < 0.175（= 中心距 0.5087 < VV 0.525）
- **已还原**：ALLOC.8/v8_raw/板 全部回退到 rev-19 基线（板 a3ce9ab803045a0a；G4 0074dad9067af737）；本实验工件不保留

## 结论
对间 3W 约束**可满足**（DP 机判两带均有合法单调解；单独并入 3W 亦 32/32）。但**单遍贪心 + 按 pad 邻近选列**的策略在「3W + PDN 障碍」下无法 32/32，且存在「差分仅 0.0025mm 而候选网格 0.05mm」的网格夹死 ⇒ 关闭本 TOOL_DEFECT 须**重派生扇落位策略**（闭式单调 carry / 分带次序 / PDN 障碍场），属 L2 过孔策略-走廊重派生，非阈值参数追加。
