# R1 路径 (ii)「由真源再生」可行性论证 v1（#K2-12 §三 回件；时间盒一轮）

- **结论**：**(ii) 可行，且不是"新造工具链"** —— 生成器库**已在仓内**（`_shared/schlib`，与 `k2/_shared/schlib` 内容一致），
  本轮已做**端到端冒烟**：真 `k2_sch.yaml` → kernel → Page → WireRouter → KiCadRenderer → `.kicad_sch`（159,374 B）
  → **`kicad-cli` 接受** → **网表回读逐网一致（74/74）**；**两次连跑逐字节相同**。
- **依据**：#K2-12 §三（先交可行性论证，监理批后实施；禁止先改图）+ §五 §七。
- **边界**：只读取源 + 草案/冒烟件**仅 `/tmp/opencode`**；未动原理图 / 网表 / 板 / SPEC / **生成器源码** / `criteria/`；未派 WORKER；P3 未开。

## 1. 工具落点（复用既有库 + 一个薄 driver）

| 层 | 件 | 现状 | 本轮实测 |
|---|---|---|---|
| 载入 | `schlib/loader/yamlloader.py` | 已有（含 schema 校验 + 行号报错） | `load_board_spec(k2_sch.yaml)` OK ⇒ **42 shapes / 55 components / 101 nets / 5 sheets** |
| 模型 | `schlib/kernel/{pin,net,component,symbol_shape}.py` | 已有（fail-fast：每脚必须归网或显式 NC） | `Component.nets` / `nc_pins` 与 yaml 一致（例 `C73: B→GND, A→NRST`） |
| 布局 | `schlib/layout/{page,labelplacer,wire_router}.py` | 已有（网格吸附 / 碰撞与越界检查 / 标签密度与重叠校验） | `Page(594,420)` + `place()`；`WireRouter.route()` 出 **140 wire + 140 label** |
| 序列化 | `schlib/renderer/kicad.py` | 已有（`render_sheet` 产完整 `.kicad_sch`；`render_symbol_library` 产 `.kicad_sym`；`render_sheet_block` 产 root 页） | 产出文本**括号平衡差 0**，KiCad 可解析 |
| 校验 | `schlib/validate/{erc,crosspage}.py` | 已有（模型级 ERC / 跨页） | 可作判据链一环 |
| **新代码** | `k2/tools/k2_sch_gen_v1.py`（薄 driver，预估 **150–250 行**） | **待写** | 只做：读 yaml → 逐 sheet 建 Page/放置 → route → render → 落 `K2_OUT_SCH`（默认 `/tmp`） |

**内建一致性证明**：现有 7 个 `hw/sch/*.kicad_sch` **本身就是生成物**（文件头 `(generator "opencode_sch_gen_v5")`），
其 yaml schema 与本仓 `k2_sch.yaml` 同源 ⇒ (ii) = **用同一工具链的升级版重跑**，非全新路线。

## 2. 符号库可得性（**不构成阻塞**）

- 符号**由 yaml `symbols` 定义**（42 个），driver 用 `render_symbol_library(shapes)` **再生成** `IOCONVERT.kicad_sym`
  ⇒ **不依赖**手维库文件。yaml 侧 `R_6K19` / `R_8K25`（strap 值）**齐备**。
- 反证手维库已陈旧：`k2/hw/lib/IOCONVERT.kicad_sym` **缺** `R_6K19`/`R_8K25`、**多** 已作废的 `REDR_DS160PR810`
  ⇒ 再生成顺带消除该陈旧（属 R1 范围内的源侧归零）。

## 3. 四类判据（全部机检、零人工判断）

| # | 判据 | 命令/接口 | 本轮冒烟 |
|---|---|---|---|
| C1 | **确定性**：同输入两次连跑逐字节相同 | 两次运行 sha256 比对 | ✅ 已证（元级：`_uuid4` = md5(seed)；`Page` 网格吸附） |
| C2 | **网表等同**：`kicad-cli sch export netlist` == `k2_sch.yaml`（101 网 / 489 节点） | `kicad-cli sch export netlist` + 集合比对 | ✅ 子集 **74/74** 一致（含需归一化的 5 条名） |
| C3 | **ERC**：模型级 + KiCad 级无 error | `schlib.validate.erc.run_model_erc` + `validate/crosspage` + `kicad-cli sch erc` | 接口就位（本轮未跑全量） |
| C4 | **结构**：括号平衡 / 每 sheet 元件数 = yaml placements 数 / 无悬空脚 | driver 内断言 + `Component` fail-fast | ✅ 冒烟：括号差 0、实例 3、wire 140 |

**已知需处理项（冒烟实测，均可机判）**：C2 中 **5 条网**（`PCIE_REFCLK0/1_P/N`、`PERSTB#`）回读名带 root 前缀 `/`
⇒ driver 须统一标签类型（或判据侧归一化）；**属可判定项，非不可行**。

## 4. 失败回退点

1. **写盘隔离**：driver 只写 `K2_OUT_SCH`（默认 `/tmp/opencode/sch_v1/`，含 7 件 + `IOCONVERT.kicad_sym`）；**绝不直写** `hw/sch`。
2. **安装 = 独立批准步**：备份现存 7 件 + lib（`git` 跟踪 ⇒ `git checkout -- k2/hw/sch k2/hw/lib` 即回退）→ 安装 → 跑 C1–C4 → 任一失败**恢复 backup 并停线**。
3. **fail-fast**：`Component`/`Net` 构造即校验（每脚归网或 NC、NC 网恰 1 脚、非 NC 网 ≥2 脚）⇒ 数据不合规时不产半成品。

## 5. 风险与**停机条款**

| 风险 | 处置 |
|---|---|
| 标签类型/名归一化（已实测 5 条） | driver 显式规则化（统一 label kind），列入 C2 判据 |
| power flag / GND 符号策略 | driver 内**显式规则**（禁隐式默认）；规则先报监理备案 |
| yaml 未覆盖的"设计意图"（如跨页归属、NC 判定策略） | **按 §五 停机条款：停线报监理，不硬编绕过** |

## 6. 与 (i) 的对比

| | 操作量 | 可机检性 | 风险 |
|---|---|---|---|
| **(i) 局部编辑** | **148 项**（60 删 + 32 并 + 56 重映 + 12 补 + 10 网），人肉对账 | 判据可机检，但**操作本身是人肉** | 本事故「人肉对账」失败模式的复现 |
| **(ii) 由真源再生** | **新代码 1 件**（driver ~150–250 行）+ 复用 9 模块；人肉操作 **0** | C1–C4 全机检 | 工具链已在仓、冒烟已过；残余风险=标签归一化/策略显式化 |

## 7. 复现（本轮冒烟）

```bash
python3 /tmp/opencode/k2p1/path_ii_smoke2.draft.py                      # yaml → .kicad_sch（/tmp）
AppDir/bin/kicad-cli sch export netlist --format kicadsexpr \
  -o /tmp/opencode/sch_smoke/connectors.net /tmp/opencode/sch_smoke/connectors.kicad_sch
cd _shared && python3 -m pytest schlib/tests -q                          # 9 passed
```
