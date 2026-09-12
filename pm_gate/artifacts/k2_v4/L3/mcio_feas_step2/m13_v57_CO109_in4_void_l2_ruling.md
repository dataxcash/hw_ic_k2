# CO-109 — L2 自裁裁定 + step ② 重定范围：**In5←In4 走廊空洞 = 按设计**（非「待 L3 派生」）；bridge zone = B.Cu

- 判定：**`RULED_L2_RESCOPE_WITH_OWNER_ESCALATION`**（L2 面自裁；仅 1 项属 owner）
- 触发：CO-108 **F-D**（medium，未决前提）
- 输入：SPEC rev-13 `7943be727a4f8ef9`｜图纸 `73c0066df83fa8c2`｜板 `0e636a67c1472462`｜CO-106 记录 `f919939ba0484aa8`
- 工具 `tools/p3_v57_co109_in4_void_l2_ruling.py`｜记录 `m13_v57_co109_in4_void_l2_ruling.json`
- 复现：`../AppDir/usr/bin/python3.11 tools/p3_v57_co109_in4_void_l2_ruling.py`

## 1. 客观证据

| 项 | 读数 |
|---|---|
| bridge zone | 3 个（`P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4` / `MCU_VDD_BCU_RESISTORS_IN4`）：`layer=In4.Cu`、名含 `BCU`、basis 含 `B.Cu`、`polygons=[]`、`geometry_status=L3_CONSTRUCTION_DERIVED` |
| 声明 bridge band 对 In5←In4 miss 点的覆盖 | **6.0%**（75/1260） |
| In4 走廊多边形 x∈(49.8,88.37)×y∈(33.3,78.7) 对同批 miss 点的覆盖 | **100.0%**（1260/1260） |
| miss 点分布 | y 峰在 35–50mm、x 峰在 60–80mm（走廊中西部） |
| 板（L4）zone 数 | 0 ⇒ 平面铺铜未在 L4 落，无法以板实判 In4 走廊铜；SPEC 亦无走廊 In4 声明几何可派生 |
| SPEC In5 阻抗声明 | `symmetric_stripline`，`refs=[In4.Cu, In6.Cu]`，`b_mm=0.5` |

## 2. 裁定（L2 自裁）

- **R1（L2）** 3 个 bridge zone 的桥接层 = **B.Cu**（zone 名 `*_BCU_*` + basis 明文；`layer: In4.Cu` 仅为 In4-可达性**簿记字段**）。派生这些 zone **不产生**该带 In4 铜。
- **R2（L2）** In4 走廊空洞 x∈(49.8, 88.37) = **按设计**（basis 记 PM T2-ECN-1/2：经 B.Cu 桥接、『In4 走线带不跨』）。
- **R3（L2）** 声明的 3 条 bridge band 仅覆盖 In5←In4 miss 点的 **6.0%** ⇒ **『L3 桥区几何派生』不能清除** In5←In4 残余（走廊主体覆盖 100%）。
- **R4（L2）** ⇒ CO-106 对 In5←In4 的 `region_scoped_indeterminate`（『几何待 L3 派生，非缺陷』）**前提不成立**：该带 In5 实为**仅 In6 参考**，与 declared `symmetric_stripline(refs=[In4,In6])` **不符**。应改判为**按设计 In4 空洞**，并登记为 **SI 待验项**（终判 = SI9000 + 板厂阻抗券，不得以假设值代填）。
- **R5（OWNER，停）** 几何侧唯一补救 = 在走廊补 In4 铜 ⇒ **反转已记录的 PM T2-ECN-1/2 裁决** ⇒ 须 owner。

## 3. step ② 重定范围

| 子项 | 内容 | 归属 |
|---|---|---|
| **②a** | 声明修正：把走廊标为「按设计 In4 空洞」+ CO-106 分类改判（新 rev + 全链重基线） | L2（自裁可做） |
| **②b** | 走廊内 In5 按 **In6-单参考**做 SI 终判 | SI/外部（SI9000 + 板厂券） |
| **②c** | 3 个 bridge zone 的 **B.Cu** 几何声明 | L2（**缺 palette**：`MCU_VDD_BCU_RESISTORS_IN4` basis 只给『短段』，未给矩形 ⇒ 需补声明坐标） |
| **②d** | 任何新 rev 重基线后须**另一会话**复评 | 流程 |

## 4. Owner 升级（一句话）

> 是否允许在 In4 走廊 x∈(49.8,88.37) 补平面铜（**反转 PM T2-ECN-1/2 裁决**）？否则 In5 在该带只能按 **In6-单参考域**走 SI 终判。

## 5. 非声明
只读；不改 SPEC/板/阈值/冻结源；不做 SI/阻抗数值计算（终判 = SI9000 + 板厂阻抗券）；不改 CO-106 记录字节（改判属后续 rev）。
