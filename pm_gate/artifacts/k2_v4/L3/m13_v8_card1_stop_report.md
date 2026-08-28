# M13 v8 Card 1 停机报告（原文归档）

> 归档自 2026-08-26 会话（WORKER 执行 Card 1 步骤 2 时停机），供裁决与后续追溯。

## 🛑 停机报告 — Card 1 步骤 2（生成）FAIL，等 PM 裁决

### 命令原始输出（第 1 次运行即崩，未重跑——反死循环铁律）

```
$ cd revA && python3 generate_sch_v5.py
  (Traceback 尾部)
    comp = Component(
  File "<string>", line 8, in __init__
  File ".../_shared/schlib/kernel/component.py", line 39, in __post_init__
    raise ValueError(
ValueError: Component 'U1': extra net mapping for unknown pin 'PB8'
```

崩溃点在 `load_board_spec()`（组件构建阶段），**写盘之前**——`git status` 确认 sch/ 零污染（仍只有预检的 2 个 M 文件 + 未跟踪 artifacts）。

### 现象确认
生成器无法从 ioconvert_v2.yaml 构建出 U1 组件：U1 的网表里带 `PB8`，但 U1 挂的符号里没有 `PB8` 这个引脚。

### 根因分析（输入层缺陷，代码级钉死）
1. **YAML 双卡共享同一 refdes U1，但两卡符号不同**：
   - `symbols` 段：`MCU_STM32G0`（QFN-32，**含 PB8@31**，K1 卡 MCU）与 `MCU_STM32G0_C2`（LQFP-48，**无 PB8**，K2 卡 MCU）。
   - `sheets` 段 L3168：`ref: U1, symbol: MCU_STM32G0_C2, card: both` —— 把两卡的 U1 都钉到 C2。
   - `nets` 段 L2792：`SBU_SEL: [U6/SEL, U1/PB8@1, R16/A]` —— PB8 是 **K1 专属**（@1）的 QFN-32 引脚网。
2. **loader 模型缺口**（`yamlloader.py`）：`ref_to_sym` 按 ref 记一个符号、**忽略 card 维度**（L258-262）；`ref_nets` 把两卡 U1 的网集**并集**成一个 nets_map（L250-252）。→ U1 最终 = 符号 C2 + 含 PB8 的网集 → `component.py` fail-fast（L37-42）raise。
3. **与 32 网回退无关**（铁证）：同一 loader 下，WORKTREE(纯方向)/HEAD(lane 分工)/dfc76cb(lane 分工) **三版 yaml 同一位置同一错误**；`dfc76cb` 记录的 `_shared` 指针 = 0e70bd7 = 当前检出（`git ls-tree dfc76cb _shared`），即 **M-D 基线自身配置下生成器必崩**。

### 业务影响
- **"M-D 全链绿"与当前输入不自洽**：`U1/PB8@1`（a3862c0，8-21）与 `U1→MCU_STM32G0_C2` 放置均早于 dfc76cb（8-26）；而仓库内 sch/ 产物最后一次再生成是 f29a8ec（8-20，早于 @N 网加入）。推断 M-D 的"结构/ERC/gate"门禁是**对 8-20 陈旧产物**跑的，未对当前 yaml 执行过全链重生成。
- 本卡"重生成 + 全门禁绿"无法启动：步骤 3-9 全部被步骤 2 阻塞，不再往下跑。

### 修复方向（输入层，供裁决，未动任何文件）
| 方案 | 内容 | 代价 |
|---|---|---|
| A | K1/K2 的 U1 拆成不同 refdes（如 K1=U1、K2=U1B），各自挂 QFN-32 / LQFP-48 符号 | 改 yaml 放置 + 网表，K2 影响面大 |
| B | loader 升级：`(ref, card) → symbol` 二维映射 + 按卡拆组件 | 改 _shared 通用层，零单板特判，符合共享层"零特判"原则；需回归 |
| C | `SBU_SEL` 的 K1 MCU 引脚改用 K1 卡 U1 实际符号存在的引脚名 | 语义核查 |

**推荐 B**（根因在模型层：单符号/ref 无法表达"同 ref 双卡双符号"；A 是设计层变通，C 是治标）。

### 当前状态快照（未手改任何文件；eco_state.json 由 CLI 正常写回）
```
ECO-S2 PASS（run 复跑确认输入断言）→ advance → 当前 ECO-S3
git status: 仅 M revA/boards/ioconvert_v2.yaml + M SPEC_k2_v4.json + 6 个未跟踪 artifacts（与预检一致）
```
