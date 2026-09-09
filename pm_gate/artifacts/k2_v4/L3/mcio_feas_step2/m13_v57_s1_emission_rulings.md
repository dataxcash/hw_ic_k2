# m13 v57 — S1 发射里程碑 几何裁决与发射契约（R1-R4 实例化前置）

> 依据：m13_v57_s1_generator_design.md（R1-R4/守恒核/证书/A1.x 映射）。
> 目的：把设计案的发射前开放点裁成可执行语义；记录真几何核对发现；
> 给出图纸页 JSON 契约（与 A1.3 不变量套件输入同构）。编码后验收仍在 A1.x 门下。

## 0. 裁决总览（本文件 = 三个摩擦点 + 一个真几何发现 + 契约）

| # | 项 | 裁决 | 状态 |
|---|---|---|---|
| R1 | 芯片出逃列域实例化 | 锚=S0 expect_xy；pad 铜=U6 板上 footprint pad（库派生实现读取，S0 先例）；列候选=出逃向 0.05 步离散 ∩ blocker(邻球铜+净空) 补集；喂守恒核(sep=0.36) | 待编码 |
| R2 | 走廊 lane 帧源 | SPEC corridors band nets=网→lane 序（布局注入）；lane y=SPEC 声明轨道作为**冻结布局帧**；生成器守恒=**校验**该帧（P/N 展开 ±0.19 对间中心距 ≥ pitch 规则、带隔离）——发现冲突即证书，不静默重推 | **发现冲突（见 §3）** |
| R3 | 连接器出逃隙 | pad 锚=S0 at_global_est；落点=pad 行 ± 半行距内可落 via 列，经邻 pad 铜净空；J2 内侧列左出/外侧列右绕 In2（j2_escape_topology 注入语义） | 待编码 |
| R4 | AC 墙穿越 | 墙 pad=downstream/upstream refdes ∩ `_MCIO` 网（权威网表 join）；每网 1 墙 pad 为强节点；1.3mm 中心距声明防互斥违例 | 待编码 |
| REFCLK | 直通模板 | 见 §4（真几何发现 → 需布局裁决） | **阻塞待裁决** |

## 1. R1 裁决语义（编码起点）

- **锚**：32 数据页 chip pad = 页清单 `anchor.chip[pol].pad_global`（=S0 expect_xy）。
- **pad 铜实现读取**：U6 footprint 板上 pads（`k2_v4.kicad_pcb` U6 块，仅取 pad
  size/pos/num），读取语义 = "库/手册派生实现"，S0 连接器侧同款；不进正确性标准。
- **邻球 blocker**：U6 同 footprint 全部 pad（异网）为 F.Cu 铜障碍，按
  `|via_center − pad_center| ≥ pad_half_extent + clearance + via_od/2` 判禁；
  clearance = netclass 对（数据网 0.175 / GND-PWR 0.2），via_od=0.35。
- **出逃向**：side=east（A_PER/B_PET 球，target 东走廊 x≈105.25）或 west
  （A_PET/B_PER 球，target 西走廊 x≈82.35），由页清单 `side` 决定；候选 x 区间 =
  pad 中心起出逃向 ≤1.5mm，0.05 步；**页内 P/N 两列 sep=0.36**（守恒核参数）。
- **产出**：每页 `R1_domain`（列候选集）+ 页级守恒判定（核引擎）→ 可行=列指派，
  不可行=证书（blockers 证据）。R1 层证书/指派先于发射，独立落盘可验收。

## 2. R2 裁决语义（lane 帧 = 布局冻结帧 + 生成器守恒校验）

- lane 帧源 = SPEC corridors `tracks_y`（v32 冻结于 SPEC，视为布局注入，不再
  "以规则重推"——原设计案 §2.3 的 re-derive 改为**校验**，理由见 §3）。
- 生成器守恒校验项（每带每 lane）：
  a) 同带相邻 lane 中心距 ≥ max(1.2 声明值, P/N 展开+净空约束)；P/N ±0.19 展开后
     铜边净距 ≥0.175（对带内相邻对中心距 ⇒ ≥ 0.19×2 + 0.205 + 0.175 = 0.755? 需带
     帧声明口径，冲突以 SPEC/capacity_audit 对账裁决）；
  b) 带间（dn/up/refclk）最小 y 距 ≥ 隔离净空；
  c) lane 全程 x∈走廊 x_range 内 P/N point_ok（禁列/禁行区由权威网表+墙声明推导）。
- 任一校验不过 → 该带证书（层 R2 + lane 集 + 需求集 + 冲突对），**不改帧不硬凑**。

## 3. 真几何核对发现（S1 阻塞级，须布局层裁决后才可发射）

**发现 F-A（lane 帧 vs 差分规则自相矛盾，机器核对数值）**：差分对在走廊按 lane ±
0.19 展开（P/N 中心距 0.38，占宽 0.205）。SPEC 轨道帧核对结果：
- EAST 廊 refclk@45.7 vs up 带 @45.1 / @46.3：lane 距 0.6 → 展开后最近 P/N 中心距
  = 0.6−0.38 = **0.22mm → 铜边净距 0.015mm < 0.175 必违**；
- WEST 廊 refclk@45.7 vs up 带 @45.5：lane 距 0.2 → 0.2−0.38 = **−0.18mm = 铜几何
  重叠（无论极性排布）**；
- REFCLK 旧解 In6.Cu（8L 栈废层）不构成 6L 参照。
**结论**：现 SPEC 轨道帧在 REFCLK×up 带共存区不满足守恒 → 任何基于此帧的发射都会
自产证书。**出路（改输入，守恒墙只能改输入消失）**：
  1. REFCLK 改走不冲突带/层（如 F.Cu 绕芯片带外、或专用隔离 y 带 ≥1.46 外移）；
  2. 或 up 带 lane 重排（layout 层裁决，重冻结 SPEC corridors 轨道）。
  S1 发射暂停于 F-A 关闭前（L6：守恒墙只能改输入，引擎对给定输入给确定答案）。

**发现 F-B（6L 层语义）**：REFCLK 旧解（In6.Cu）基于已废 8L 栈；6L 下 REFCLK
必须与数据带共享 In2 或改 F.Cu 带外路径 → 与 F-A 同源，同一裁决关闭。

## 4. 图纸页 JSON 契约 v1（发射输出格式 = A1.3 套件输入）

```jsonc
{
  "page_id": "PCIE_DN0/input",
  "kind": "data" | "refclk_pass",
  "nets": {"P": "...", "N": "..."},
  "corridor": {"id": "...", "band": "...", "lane_y": 58.3},
  "anchor_pads": {"P": {"chip": [x,y], "conn": [x,y]},
                  "N": {"chip": [x,y], "conn": [x,y]}},
  "paths": {
    "P": {"points": [[x,y],...], "layers": ["F.Cu","In2.Cu",...],
          "vias": [[x,y],...]},
    "N": {同型}
  },
  "chip_landing_rows": [{"net":"...","method":"VIA_IN2","status":"ASSIGNED",
                          "pad":[x,y],"landing":{"x":..,"y":..}}],
  "reservations": {"R1_cols": [...], "R2_lane": ..., "R3": ..., "R4": ...}
}
```
不变量（A1.3 V1-V6 已实现且自测 PASS）直接消费本契约。

## 5. 本文件之后的编码序列（不可跳步）

1. F-A/F-B 布局裁决（改输入）→ 2. R1 实例化 + 核判定（32 页 R1 报告/证书）
→ 3. R2 校验 + R3/R4 实例化 → 4. 发射 34 页 → 5. A1.2 三枚举序字节比对 +
A1.3/A1.4 真图纸重跑 → 6. 全过才 lock+commit+push。

## 6. 关联

- 设计案：m13_v57_s1_generator_design.md；页清单：m13_v57_s1_page_manifest.json；
- 守恒核/基准/门：p3_v57_s1_conservation.py / _exhaustive_ref.py / _a11_gate.py；
- 不变量套件/门：p3_v57_s1_invariants.py / _a13_gate.py；单向门：_a14_gate.py。
