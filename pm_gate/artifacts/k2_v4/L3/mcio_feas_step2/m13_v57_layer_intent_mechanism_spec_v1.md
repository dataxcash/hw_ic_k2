# 机制规格 — 板层意图**容量闭合派生**（LID.1，整改 #03）

> 2026-09-11｜作者：ARCHER｜层级：**机制（methodology）**｜状态：已实现并跑通
> 引擎：`k2/tools/p3_v57_layer_intent_derive.py`（确定性 O(n)，零搜索/零枚举/零回溯）
> 输出：`m13_v57_layer_intent_derived_v1.json`（rev **LID.1**，sha16 `e7c3c91c`，双跑逐字节一致）
> **输入 = 冻结四源 + 规则，别无其他**；层数/层用途/拓扑均为**输出**，无 owner/工单/修订卡参数。

## 1. 机制（生成器，非谓词）
旧机制（缺陷）：`verdict = SUFFICIENT iff D ≤ |transition_eligible_layers|` —— **验算给定集合**，不能派生。
新机制（修复）：层集由**三个闭式下界取 max** 派生而来，全部来自冻结输入：

```
L_signal = max( L_escape , L_capacity , L_conflict , 3 )        # 3 = F+1内层+B 最小可行
total_layers = 2 · L_signal                                      # 参考平面夹心规则
signal layers = {F.Cu, B.Cu} ∪ {interior signal by 规则}
layer purpose:  PWR 固定 In4；其余 internal 偶=GND/奇=signal（复现冻结 6L/8L 家族）
topology:       层分配 = 冲突图「固定序贪心着色」（单遍 O(n+m)，合法着色 ⇒ 同层交叉 0）
```

### 三个下界（各带冻结出处，非工单常量）
| 下界 | 定义 | 出处 |
|---|---|---|
| `L_escape` | pad 墙逃逸深度：行内 pad 间隙 < 单道 lane ⇒ pad 行/列须**各自层分隔**；取各 pad 墙「较薄轴簇数」的最大值 | manifest 实测 pad 坐标 + SPEC `w/clr` |
| `L_capacity` | 区域容量闭合 `ceil(D_r / C_r)`，`C_r = floor(可用横截 / 对中心距)` | SPEC corridors + `inter_pair_spacing` |
| `L_conflict` | 通道序冲突图（排列图）最大团 = 源序/靶序反演的**最长下降子序列** | manifest 端点序（chip 坐标 / conn 坐标） |

## 2. 派生结果（本板，冻结输入一次算得）
| 量 | 值 | 依据 |
|---|---|---|
| `L_escape` | **4** | chip 逃逸区 4 pad 行（墙厚 4；间隙 0.2953 < lane 0.555 不可穿）；连接器墙厚 2 |
| `L_capacity` | 2 | chip 逃逸翼带 37.52mm（= 板框 46 − 2×板边 0.3 − 芯片 pad y 极值；由冻结板框/规则派生）/1.46 = 25 对/层 → ceil(32/25)=2；两走廊 45.4/1.46=31 → 18/31→1 |
| `L_conflict` | 2 | 源 x 序 → 靶 y 序反演的 LDS = 2 |
| **`L_signal`** | **4** | max(4,2,2,3) |
| **`total_layers`** | **8** | 2·4 |
| **signal layers** | **F.Cu / In2.Cu / In6.Cu / B.Cu** | F/B 外层；interior In2/In6 |
| layer purpose | F\|In1 GND\|**In2 sig**\|In3 GND\|**In4 PWR**\|In5 GND\|**In6 sig**\|B sig | 参考夹心 + PWR 固定 In4 |
| 闭环验证 | `region_closure = all true`；`same_layer_crossings = 0`；`greedy_colors = 2` | 引擎 `closure` |
| 与冻结 6L 对比 | `frozen_stackup_signal_layers = 3 < 4` ⇒ **冻结 6L 不足** | `verdict = DERIVED_STACKUP_REQUIRED` |

**自洽性**：派生叠层 = 8L（In2+In6 双内部信号层），与 `j2_escape_topology`「8 层定案」一致 ⇒ **消除 8L/6L 矛盾**；
层数与用途**有派生依据**（非工单常量）。**无任何 owner/工单参数介入**。

## 3. 可复现（命令 + 输出）
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
python3 tools/p3_v57_layer_intent_derive.py --out /tmp/opencode/lid_v1.json
# verdict = DERIVED_STACKUP_REQUIRED
# L_escape=4  L_capacity=2  L_conflict=2  L_signal=4  total_layers=8
# signal_layers = [F.Cu, B.Cu, In2.Cu, In6.Cu]
# closure: region_closure all closed; same_layer_crossings=0; frozen_stackup_sufficient=false
python3 tools/p3_v57_layer_intent_derive.py --out /tmp/opencode/lid_r2.json --quiet
cmp /tmp/opencode/lid_r2.json /tmp/opencode/lid_v1.json   # 逐字节一致（确定性）
```

## 4. 红线 / 边界
- 不改冻结四源原件；canonical `W3-CN.25` 不动；派生件为**新版本文件**。
- 零搜索/零暴力迭代：引擎只含 `sorted/bisect/min/max`，无 `enumerate/while`、无候选试错。
- `L_escape` 为**保守下界**（4 行视为互相阻塞）；若将来引入「同向行可嵌套」的局部闭合，只会**降低** `L_signal`，
  不会违反容量闭合。落地实现（SPEC 层叠版本 bump）属 L2 机械版本化，不再需要 owner 参数裁决。
