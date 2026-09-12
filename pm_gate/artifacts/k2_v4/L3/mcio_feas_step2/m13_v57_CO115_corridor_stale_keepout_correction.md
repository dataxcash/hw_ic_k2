# CO-115 — L2 事实更正：In4 走廊空洞 = **失效 keepout 的残留**（待 L3 派生），**非**「按设计」

- 判定：**`L2_CORRECTION_STALE_KEEPOUT_PENDING_L3_L1_OWNERSHIP`**
- 更正对象：**CO-109 `R2`（按设计）/ CO-110 / CO-113 rev-14 `in4_corridor_void_by_design_v1`**
- 复现：`python3 tools/p3_v57_co115_corridor_stale_keepout_correction.py`

## 1. 机判依据（全部来自声明源）

| 项 | 读数 |
|---|---|
| `retired_in4_keepout_band_6l.band` | **x[50.0, 88.17]**，y[43.44, 65.1]（CO-95 退役；premise voided by CO-74） |
| keepout premise | 「铜皮东西两区**禁止跨越此带**（两侧各留 POWER clearance 0.2）」 |
| 走廊西界 | `MCU_VDD_WEST` 东缘 **49.8 = 50.0 − 0.2** |
| 走廊东界 | `P3V3_EAST` 西缘 **88.37 = 88.17 + 0.2** |
| CO-95 `effect` | 「退役后 **In4 铜可在原 band 区内按网归属铺设**（仍须满足 plane_reachability_requirement）」 |

⇒ 走廊空洞（x∈(49.8,88.37)）**就是该退役 keepout 的两侧 0.2mm 内缩**，即**约束退役后边界未随动的残留**，**属待 L3 派生** —— handoff §4-2 原判正确，**CO-109 的「按设计」判定错误**。

## 2. 更正后的推论

- **CO-111 的 In5 PCIe 40.1% 参考缺失「可修」**：把 In4 铜按网归属铺入 band 即可恢复参考（**非**永久缺口）。
- **CO-113 rev-14 的 `in4_corridor_void_by_design_v1` 键错误**，须后续 **rev-15** 更正 + 全链重基线 + 换会话复评。
- CO-98 `declared_pending_l3`（8 桥区 target + 6 band 义务）语义**回到「待派生」**（CO-112 的桥区 N/A 仅对其 targets 成立，不覆盖 band 铺铜）。

## 3. 唯一硬停点（OWNER / L1）

> band x∈(50.0, 88.17) 内 In4 铺铜的**区域归属界面**（MCU_VDD / P3V3_AUX / P3V3）如何划分？（界面一定，L2 即可派生铺铜并消除 In5 40.1% 参考缺失）

band 内归属特征：P3V3 U6 球 x∈[85.4,88.28]｜MCU_VDD R29–R34 x∈[50.2,57.55]｜P3V3_AUX vias x∈[26.5,58.9]。
界面未定 ⇒ **无法在 L2 内唯一确定铺铜几何**（不得以假设值代填界面）。此即既有 L1 项「P3V3_AUX 西区归属」（CO-98 `ruling_pending_l1=6`）的同族问题。

## 4. 非声明
只读；不改 SPEC/板/阈值/冻结源；本件不做铺铜几何派生；不代填归属假设值。
