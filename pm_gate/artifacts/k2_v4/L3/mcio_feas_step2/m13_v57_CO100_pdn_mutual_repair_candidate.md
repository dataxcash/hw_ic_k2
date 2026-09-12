# CO-100（L2 自裁 · PDN）CO-99 互冲的**互障感知修复候选** —— rev-12 能否自解？

> 日期 2026-09-12｜工具 `tools/p3_v57_co100_pdn_mutual_repair_candidate.py` `056caaacc9ce3703`
> 记录 `m13_v57_co100_pdn_mutual_repair_candidate.json` `f8b6b2f3b11d09a9`
> 基线：SPEC rev-11 `d85f10f722ba22b0`｜板 `0e636a67c1472462`｜**scratch 机判，不改 canonical**

## 1. 问题
CO-99 判 rev-11 PDN **计划集互相冲突 = FAIL**（7 异网重叠 + 39 孔距）。本件回答：**能否在 L2 手段内（声明 palette、零坐标搜索）自解**，还是必须并入 L1/工艺？

## 2. 方法（确定性、无搜索）
- palette 与 CO-92 一致：ppc = `current` → pad 4 正交 @(VIA_R+0.3) → pad 4 正交 @0.6；stitch/zone = `current` → 原位 4 正交 @0.6。
- **互障 = 板已有铜（CO-91 `Scene`）+ 已接受的计划件（via 与 ppc stub）**；判定阈值同规则源，并叠加**孔-孔 net-agnostic ≥ 0.45mm**（板配置 `min_hole_to_hole=0.25` + drill 0.2）。
- 处理序 = 声明固定序（ppc → stitch → zone，各按 net/ref/pad 排序）。取**首个合法候选**，全不可 ⇒ `blocked`。

## 3. 结果：**PARTIAL**（verbatim）
| 类别 | kept | relocated | blocked |
|---|---|---|---|
| ppc | 126 | **58** | **5** |
| stitch | 34 | 5 | **1** |
| zone | 13 | 4 | 0 |
| **合计** | 173 | 67 | **6** |

- **残余异网重叠 = 0**（互冲可在声明 palette 内清除）。
- **新增 blocked = 6**（5 ppc + 1 stitch，**全部网 = GND**，全部位于 **U6 0.5mm 球栅场**，如 `U6@[103.651,52.99]`、`U6@[104.17,54.49]`）。

## 4. 裁定（归口）
- **互冲本身 = L2 可解**（≤ 67 项重定位、0 残余重叠、无 while/无搜索）。
- **代价 = 6 项 U6 GND 连接在冻结 8L 通孔工艺下无合法位** ⇒ 与 **CO-94** 同一张力：要保连接数须 **via-in-pad（工艺）或 HDI/微孔（层数，L1）**；否则须**接受 6 项新增 blocked**（GND 球，已在 CO-94 的 U6 63-blocked 语境中）。
- ⇒ **rev-12 计划集重导的决策点**：`(a)` 接受 6 新增 blocked（纯 L2，可自裁）＋ 显式登记；或 `(b)` 升级 owner 取裁 via-in-pad/HDI（L1/工艺）。

## 5. 非声明
- scratch 机判；**不改 SPEC/板/阈值/冻结源**；**本件不施加**（施加 = rev-12 + 全链重基线 + 换会话复评）。
- 反解为**贪心顺序重放**（声明序），非全局最优；palette 内无解即判 blocked，**不引入新候选/不搜索**。
- 本件**不判** stub-vs-pad 之类由 CO-91/CO-92 覆盖的板侧项（互判只覆盖「计划集互相」与孔距）。
