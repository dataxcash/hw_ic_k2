# CO-114 — SPEC **rev-14** 新基线**非执行者**对抗复评（对象 = CO-113 施加 + CO-115 更正 + 链 pin 前移 + 几何/板不变性）

- 判定：**`PASS_WITH_FINDINGS`**（F-1 high / F-2 medium / F-6 medium / F-3 low / F-4 low / F-5 informational）
- 复评人：非执行者会话（rev-14 施加者 z13 之外的独立、**context 隔离**会话；`L2_STRUCTURE_v2.0.md:137` 禁自评）
- 对象基线：SPEC rev-14 `188b01deb34c9fba`｜图纸主件 `0e74718b1e31dca5`（rev-13 git blob `73c0066df83fa8c2`）｜板 `0e636a67c1472462`
- 工具（本件产物）：`tools/p3_v57_co114_rev14_nonexecutor_review.py`｜记录：`m13_v57_co114_rev14_nonexecutor_review.json` `20adc9fb67e62c63`
- 复现：`python3 tools/p3_v57_co114_rev14_nonexecutor_review.py`（**两次逐字节一致** `20adc9fb67e62c63`）

## 1. 六面独立机判（全部 True）+ 9 项牙齿全触发

| 面 | 判据 | 读数 |
|---|---|---|
| **A** SPEC 差分 | rev-14 vs rev-13：既有标量**恰为** `.spec_version`；新增键**全落**声明命名空间；无删除键 | n_changed=1（`.spec_version`）；n_added=67 leaf（declared 64 + extra_source 3）；removed=∅；family={declared:64, extra_source:3} |
| **B** 几何/板/冻结源不变性 | 新图纸 vs **rev-13 git blob**（`git show d1af217^:…`）三子件**逐字节同**；板逐字节同；冻结四源 4/4；容器 `_shared` 副本同字节；frozen drift=∅ | blob `73c0066df83fa8c2`；sub `c27d9f5b…`/`2535f330…`/`74234e98…` **rev-13=rev-14**；板 `0e636a67c1472462`；SPEC 原件 `0bd52ed48e720b8c`／manifest `a8ef3ea8ecff99d7`／冻结板 `fb07d25ac426ff84`／drc `0a459839e15960b8` |
| **C** 链 pin 前移 | live 消费者**全数** pin rev-14；rev-13 仅历史件合法持有 | 15/15 live 在 rev-14；rev-13 引用者 = co107/108/109/110/111/112/113（全在允许集）；unexpected=∅ |
| **D** CO-115 更正成立性 | keepout band ↔ 走廊两侧 0.2 内缩**算术吻合**；CO-95 effect 授权铺铜 | band x`[50.0,88.17]` → 期望/实测 `49.8`、`88.37`；`corridor_x`=[49.8,88.37]；effect「按网归属铺设」✔；CO-115 四检查全 True |
| **E** CO-111 独立复算 | In5 走廊暴露长度/占比/网类**独立重算**；L5 SI 覆盖面 | 重算 **1094.812/2727.316mm = 40.14%**，16 网**全 PCIe** 差分对，与 CO-111 记录**逐位一致**；SI `skew_ok=true` 0.13≤0.15 |
| **F** 新键无消费者 | rev-14 新键在 rev-14 SPEC 消费者（引擎/L4/L5/闸）中**零引用** | consumers=∅（4/4 键）⇒ CO-113「读数不变」为**逻辑必然**（非信任执行者） |

牙齿（全部触发，非空真）：A 既有标量检测器 / A 非预期键检测器 / B 几何哈希检测器 / B 冻结源检测器 / C pin 漂移检测器 / D 内缩算术检测器 / E 零控 / E 正控 / F 搜索非空真。

## 2. 发现

- **F-1（high，OPEN_DECLARED）**：rev-14 canonical 键 `pd.zone_defs.in4_corridor_void_by_design_v1` 的陈述（`note` =「In4 走廊**按设计无铜**」）已被 **CO-115** 判为**事实错误**（走廊空洞 = 失效 keepout 残留，待 L3 派生）。A 面证明该键确为 rev-14 新增 ⇒ **现行 canonical SPEC 内含一个已定性的错误声明**。 目标：**rev-15**（须先有 OWNER/L1 band 归属界面，以 bundling 成一次 rev 重基线 + 复评）。
- **F-2（medium，OPEN_DECLARED）**：live 验收登记册 `co87` 的「参考平面」行证据仍内嵌「CO-110 判为**按设计** In4 走廊空洞（bridge zone = B.Cu）」，与 CO-115 冲突 ⇒ 该行 status（`INDETERMINATE`）正确但**证据叙述陈旧**。 目标：co87 矩阵（下一 rev 一并更正）。
- **F-6（medium，OPEN_DECLARED）**：rev-14 重基线后 **4 记录 5 处** `inputs.*_record` provenance pin 指向**已被取代**的上游记录，**打破 CO-108 check C 的不变量**：`co98←co95` / `co105←co98` / `co109←co106` / `co110←co106` / `co110←co87`。根因：CO-113 只前移 SPEC pin 并重跑闸记录（co87/95/98/106 于 `d1af217` 变 sha），未刷新上级记录的 inter-record pin ⇒ 与 **CO-108 F-A 同族盲区**（CO-77 不覆盖记录内 provenance pin）。被引值均为 git 内**真实历史版本**（非 F-A 式伪造）⇒ 属「陈旧 pin」，非「漂移伪造」。 目标：pin 刷新 CO（可并入 rev-15；CO-108 F-A 先例允许确定性重跑、语义不变），或记录内显式标注「历史 pin」。
- **F-3（low，OPEN_DECLARED）**：CO-113 记录 `changes.new_keys` **少声明**一个实际新增键 `bcu_bridge_bands_source`（工具写入，属 band 来源标注，无消费者）。无功能影响，属**声明完整性**缺口。 目标：CO-113 记录 / rev-15 声明。
- **F-4（low，INFORMATIONAL）**：CO-111 check C 措辞「**无逐线阻抗核验字段**」不精确 —— L5 SI 记录实含 `netclass_geometry.per_layer_impedance`（In5 声明 `refs=[In4,In6]`）与 `conformance=DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`。真正缺口是**区域无关性**（In5 阻抗模型无条件假定 In4 参考存在）⇒ CO-111 实质结论（走廊阻抗未验）**成立且被本件加强**，仅措辞需收敛为「区域条件阻抗未验」。 目标：CO-111 措辞（下一 rev）。
- **F-5（informational，CLOSED_BY_THIS_REVIEW）**：boundary v1.80 §2「现行 SPEC」行把 rev-14 描述为「In4 走廊空洞按设计」，与同件 §1 ㊼ / §6-36 的 CO-115 更正**自相矛盾**；由本件出 **v1.81** 时一并更正措辞。

## 3. 结论与残余

- rev-14 的**机械声明成立**：仅新增声明键（既有标量只 `spec_version` 变）、几何与板**逐字节不变**、SPEC 链 pin 全数前移、新键零消费者 ⇒ 「读数不变」为逻辑必然。
- CO-115 的 keepout 更正**算术成立**；CO-111 的 40.14% 量化经**独立复算逐位一致**，受影响 16 网全为 PCIe 阻抗受控差分对。
- **残余（非本件责任）**：F-1/F-2/F-3/F-6（→ rev-15 + pin 刷新 CO）；F-4（措辞）；**OWNER/L1 硬停点**：band x∈(50.0,88.17) 内 In4 铺铜**区域归属界面**；既有 L1 三项；外部（SI9000 + 板厂阻抗券 / PM 压降·热）。
- 非声明：只读（除自身记录）；一阶点采样（段中点）；未重跑 G4..G7 全链（「读数不变」以 A/B/F 三面论证）；未重跑 L3 桥区几何派生。
