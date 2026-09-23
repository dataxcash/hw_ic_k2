# K2 · R438 —— 逐网独立可达性（自由格点 BFS · 只读 · 不驱动求解器）

- **ts** 2026-09-23T19:17:40 · **from** ENG·ARCHER · **to** 监理 · **owner 闸口 0**
- **authority**：#K2-147 §二.2 · **R436 口径修正** · #K2-146 §一 · owner #14⑥
- **边界**：只读确定性几何（逐网 BFS）· **未运行求解器** · 冻结四源 4/4 未动

## 0. 一句话
**逐网独立可达 = 16/16**（自由格点 7080 个 · 0.435 步距 · 8 连通 · 非 lane 障碍）⇒ 修正 R436 之过严口径（『单程直行』非必须，**多段阶梯可达**）。

## 1. 逐网结果
- `PCIE_UP_OUT0_N_J2`: reach=True · hops=152 · len≈71.0mm
- `PCIE_UP_OUT0_P_J2`: reach=True · hops=152 · len≈69.7mm
- `PCIE_UP_OUT1_N_J2`: reach=True · hops=148 · len≈66.9mm
- `PCIE_UP_OUT1_P_J2`: reach=True · hops=146 · len≈68.6mm
- `PCIE_UP_OUT2_N_J2`: reach=True · hops=139 · len≈64.4mm
- `PCIE_UP_OUT2_P_J2`: reach=True · hops=139 · len≈62.3mm
- `PCIE_UP_OUT3_N_J2`: reach=True · hops=134 · len≈59.4mm
- `PCIE_UP_OUT3_P_J2`: reach=True · hops=133 · len≈61.6mm
- `PCIE_UP_OUT4_N_J2`: reach=True · hops=128 · len≈58.6mm
- `PCIE_UP_OUT4_P_J2`: reach=True · hops=129 · len≈59.2mm
- `PCIE_UP_OUT5_N_J2`: reach=True · hops=125 · len≈56.5mm
- `PCIE_UP_OUT5_P_J2`: reach=True · hops=126 · len≈58.8mm
- `PCIE_UP_OUT6_N_J2`: reach=True · hops=122 · len≈55.4mm
- `PCIE_UP_OUT6_P_J2`: reach=True · hops=115 · len≈52.2mm
- `PCIE_UP_OUT7_N_J2`: reach=True · hops=111 · len≈49.5mm
- `PCIE_UP_OUT7_P_J2`: reach=True · hops=115 · len≈52.4mm

## 2. 解读
逐网可达**不等于** 16 网可同时**互不侵占**通过 —— 后者才是待解之**指派/打包**问题（= #K2-146 §一 形态 · 仍待**一次求解**）。本件仅证明**候选域非空**（R436 之否定性结论系口径过严所致）。

---
—— ENG（ARCHER）· 2026-09-23T19:17 · 只读几何 · sha16 `b89e7f70d5d8119c`
