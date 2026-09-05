# M13 v21 — 46mm 单芯片 × 6L 真实路由验证：判定工件（已被对抗评审修正）

> 状态：**本工件原始"6L 闭合"结论已被非执行者对抗评审 FAIL 退回（见 REVIEW_ADVERSARIAL_v21.md）**。
> **最终判定 = 层数未定案 / INDETERMINATE（6L 试用），非"6L 闭合"**——决定性逃逸项未做工具精确验证。
> 本工件保留原始论证供审阅；**以"层数定案闸"（L2_STRUCTURE_v2.0）+ 评审记录为准**。
> 数据源分级同 AUDIT_G1_G2；结论定位 = L2 物理可行性证据（试用级）。

## 0. 一句话结论（修正后）

**46mm 单芯片 DS320PR1601 × 6L = 结构/走廊/逃逸封装设计级「未证伪」+ 宏观闭合，但层数（6L vs 8L）
暂不定案（INDETERMINATE）**。决定性逃逸项（75% via / 50% 穿越密度）未做工具精确验证 = known_gap
（工具缺 Intel footprint 物理坐标资产）；按 v20"先试 6L、不闭合回 8L" = **6L 试用 + 8L 兜底**，
逃逸验证为 L3 开工前硬门。**不宣布"6L 已闭合"。**

## 1. 判据表（每项 = 可验证性断言）

| # | 判据 | 证据 | 结论 | 验证方式 |
|---|---|---|---|---|
| 1 | 器件/板框/层数负载 | DS320PR1601 单芯片；46mm（y∈[33,79]）；6L F/G/S/G/P/B；单面 B.Cu 空 | ✓ | v19/v20 冻结 |
| 2 | 走廊真实对数 | 东(J2) 16 对/32 网；西(MCIO) 16 对/32 网（J3=8、J4=8）；REFCLK0/1=2 直通 | ✓ | [L0] net 表 census |
| 3 | 走廊横截闭合 | 2带×8对 = 10.80mm < N 16.2 / S 20.8；16对单平面 22.48 < N+S 37.0 | ✓ | precheck §2（1.46 保守口径；0.875 口径更松，robust） |
| 4 | x 净跨 | 西 17.30 / 东 27.40mm > 逃逸过渡 10–12mm | ✓ | [L0] 实测 |
| 5 | pin 逃逸可达 | 25% 外环 F.Cu 直出；75% 需 via；50%（16 对）穿越 | ✓ 结构 | [DS] 列带（本 session 确认全 lane 一致） |
| 6 | via ≤2/网 | 穿越网 F→In2→F = 2 via ≤2 硬限 | ✓ | L2 v1.2b 受控过孔 |
| 7 | 逃逸空间密度 | **Intel escape-optimized 封装**（lane 分组+组间 0.3/0.4/0.8/1.2mm 通道；短轴 ~14–15 名义 0.6 位） | **设计级 ✓**（精确解=gap） | [FP] |
| 8 | REFCLK | In2 S 翼独立带（8+2 对 ≈14.8mm < 19mm 可用），包地 ≥2mm | ✓ | precheck §5 |
| 9 | 低速/边带 24 网 | In2 端区 / B.Cu / F.Cu 外围，不争 PCIe 走廊 | ✓ | precheck §6 假设7 |

## 2. 为何"逃逸项设计级 ✓"是可信判定（非空谈）

precheck §6 断言"6L 不闭合的确切触发 = ① REFCLK 需专属层（In6） ② 逃逸 stub 密度 knife-edge"。
本 session 用 librarian 实破该封装：

- **DS320PR1601 = Intel PCIe5 retimer common footprint（354 球 8.9×22.8mm）**，TI 官方即标
  "Intel retimer common footprint compatible"（产品页）——Broadcom BCM85657 / Astera PT5161L /
  Microchip XpressConnect 全遵同 footprint。
- Intel 封装**设计意图**（专利 US20170351640）：**"balls-anywhere" 分组/六角形摆放，让每对高速
  差分信号能在单层逃逸**——即封装把 lane 分组、组间留布线通道（datasheet/机械图 callout：
  0.6 TYP 名义、组间 0.3/0.4/0.8/1.2mm 断开、短轴球跨 ~7.88mm ≈ 14–15 名义位）。
- → **precheck 的"0.6 均匀网格 → 行内 pad 不可穿线 → knife-edge"是过度保守**。真封装每 lane
  组间有通道，75% via + 50% 穿越的逃逸在封装设计它就是**要能单层做掉的**。
- 因此 §1#7 判为设计级闭合（不是工具精确解），置信度高。

## 3. 已知缺口（known_gap 更新：工具待资产，驱动"把模型做好"）

| 缺口 | 描述 | 处置 |
|---|---|---|
| DS320PR1601 物理球栅资产 | 精确逐球 X/Y = 无公开源（GitHub/UL/SnapEDA/EasyEDA 全空或同为拉伸逻辑格；真源 = Intel PCIe5 retimer spec 图（registration-gated）/ TI EVM 受限目录）。**librarian：won't guess** | 作为**模型层资产需求**上报：工具需补 Intel-retimer-footprint 物理坐标 + 支持非均匀分组 fanout |
| 逃逸精确密度 | 未用工具精确求解（资产缺）；现为设计级判定 | 工具补资产后回验；回验失败 → 回 8L（§4） |

## 4. 回退 8L 触发条件（裁决性，宪法第六章第 5 条）

**触发条件**：L3 真实路由（在取得 Intel footprint 资产后逃跑逸求解）出现下述任一不可解，
**不重跑 6L（禁暴力迭代）**，直接回 8L（旧 8 层已验证 = 兜底）：

1. 任一 lane 对（双侧 8 对/带）在其组间通道 + 翼带 keepout 内的逃逸求解 vias/间距冲突不可解；
2. REFCLK 在 6L In2 S 翼分带与 8 对穿越 + 端区 stub 争抢不可满足（In6 作第二内部信号层承接）。

**明确结论**：回 8L = 新增 In6 + 额外 GND 隔离 + B.Cu 可用，成本 +50~100% 可接受（v20 用户已批）。

## 5. 数据源与置信度标注

- **[DS] 列带结构**：本 session 从 Table 5-1 逐球解析全 128 信号球 + 354 球，列带全 lane 一致
  （A_PER@1-2/B_PET@7-10/A_PET@26-29/B_PER@34-35）= **确定性**（不依赖行距）。
- **[FP] 物理形态**：Intel retimer common footprint（非均匀分组逃逸优化）= librarian 外部核实 +
  TI 产品页/datasheet 指标 + 专利 → **设计级置信**。
- **[推导] 走廊/横截**：真板实测 + precheck 结构数学 → **确定性**。
- **[已知缺口]**：精确逐球坐标未实证（won't guess）→ 明确标注，不作数。

## 6. 产出供冻结

本工件为 **L2 物理可行性证据**（结构 + 走廊 + 逃逸设计级 + via 预算 + REFCLK + 回退预案）。
判定「6L 闭合 → 冻结 46mm+6L」；走 ECN 正式化（unlock → 改 L1/L2 → lock）+ kb 回写。
