# CO-95（L2 自裁 · PDN）— In4 平面**可达性机判** + 陈旧 keepout band 退役 → SPEC **rev-11**

> 日期 2026-09-12｜工具 `tools/p3_v57_co95_in4_reachability.py` `a2e16d6e08eef731` / `tools/p3_v57_co95_spec_rev11_in4_band_retire.py` `1a23f36a50fc24c3`
> 记录 `m13_v57_co95_in4_reachability.json` `61db48a283beeaae` / `m13_v57_co95_spec_rev11_band_retire.json` `0ec682d3d15f84d5`
> **SPEC rev-11** `d85f10f722ba22b0`（rev-10 `4416e42eed10cb8c` 原件未动）｜板 `0e636a67c1472462`（**逐字节不变**）

## 1. 问题（为何这是 L2 缺口）
`power_pad_connect.entries` 的 via 只有落在**本网 In4 铜**上才构成真实连接；否则该 entry 是**名义的**。
既有闸只判「引用存在性/覆盖/净距」（CO-88/89/90/91），**没有任何闸判「via 是否被本网平面覆盖」**。

## 2. 机判结果（rev-10，工具 + 牙齿 2/2）
55 个 power entry（非 GND）：

| 分类 | 数 | 含义 |
|---|---|---|
| `covered_explicit` | 35 | via 落在本网 In4 显式 polygon 内 |
| `covered_bridge_target` | 8 | 该 (ref,pad) 在某 In4 桥区 `targets` 声明内（几何 = L3 派生）|
| **`l3_obligation`** | **6** | 无声明覆盖，但本网有 In4 区（U6 P3V3 球，落**已失效 band** 内）|
| **`needs_region_ruling`** | **6** | 本网**无 In4 区**（12V_IN ×3）或**区域归属冲突**（P3V3_AUX 西侧 ×3）|

牙齿：band 内点被抓、东区点放行（合成注入，真跑检测路径）。

## 3. L2 裁定（自裁）
1. **退役 `in4_pcie_keepout_band`**（原因：其启用前提「wp1_escape_nets 在 In4.Cu 有 14 段走线」**已被 CO-74 判定失效** —— 引擎 `LAYER_PALETTE=F/In2/In5/B` 无 In4、交付板 In4 段数 **0**、`layer_plan` 仅把 In4 声明为 PDN 平面）。
   退役后原 band 区可按网归属铺设 In4 铜（保留 band 范围 + void 理由于 `retired_in4_keepout_band_6l`，禁静默放弃）。
2. **废止 P3V3_EAST 由 band 推导的西界**（原「左界 = In4 走线带东缘 88.17 + 0.2 = 88.37」）⇒ 西界改由 **「与异网 In4 铜边 ≥0.2mm」** 决定，落点 = L3 确定性派生（**不臆造新多边形**）。
3. **新增 `plane_reachability_requirement`**：每个 power entry 的 via 必须被**本网** In4 铜覆盖；同网各区连续（无孤岛）；异网净距 ≥0.2mm（POWER 判据）；L3 几何 = 确定性派生（零坐标搜索）。
4. **登记残余 12 项**（`plane_reachability_status`）：6 项 `l3_obligation`（band 退役后转 L3 覆盖义务）+ 6 项 `needs_region_ruling`。

**效果**：6 个 U6 P3V3 球（AC17/AC20/AK17/AK20/T17/T20，x≈84.8–87.2）原先被失效 band 排除在 In4 之外 ⇒ 退役后成为 **L3 可达性义务**（不再是结构性死结）。

## 4. 升级（一句话，交监理）
**6 项 `needs_region_ruling` 属 L1/区域划分**：`12V_IN` **无任何 In4 区**（3 pad：C88.1/U2.4/U2.6，且板上无该网铜）⇒ 需裁其承载（In4 区域分配 = 区域/电源域划分）；`P3V3_AUX` 西侧 3 pad（C90.1/R1.2/U1.15）所需区域与**西区名义网 MCU_VDD 冲突**（zone basis 文本称「P3V3_AUX+MCU_VDD 同区」而单一铜区只能属一个网）⇒ 需裁西区归属。

## 5. 施加与验证（rev-11）
- `pd` 外**仅 `spec_version` 变**（`outside_pd_changed=['spec_version']`）；rev-10 原件未动。
- **全链 G4→G7（rev-11 重基线）**：G4 `FEASIBLE_ALL` `e0a4dfd7936372f9`（34 页 / crossings 0 / work 546/546）、G5 PASS `frozen=True`、L4 viol 0、L5 FAB ok + **DFM new=0** + **SI skew 0.1300**；**板逐字节 `0e636a67c1472462` 不变**。
- **回归闸**：co78/co81/co84/co87（3 CLOSED/2 open 不变）/co88/co69（10/10，指纹不变）全 PASS；**CO-91 对 rev-11 PASS（0/0）**；CO-92 对 rev-11 = **不动点**（189/0/0、40/0/0、17/0/0）。
- CO-95 对 rev-11 = `OPEN_needs_region_ruling`（35 / 8 / 6 / 6，牙齿 2/2）。

## 6. 非声明
不改板（逐字节同）、不改阈值、不改历史 SPEC、不改冻结源、**不改 `_shared` 引擎**；
**未臆造 In4 几何**（仍属 L3 确定性派生）；不触 L1（器件分区/接口朝向/信号流向/电源域集合/球重映射均未动）；
`OPEN_needs_region_ruling` 与 `l3_obligation` **均非 PASS**；**rev-11 非执行者复评欠**。
