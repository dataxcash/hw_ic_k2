# K2 · P4 · `G9` 几何来源**停点**（SPEC 26.5 vs 权威 27.94）+ `G11` 候选补丁**已端到端验证** · v1 · 2026-09-18

> 缘起：handoff inc47 §6-3-(a)「G9/G10/G11 候选补丁（仅 `/tmp`，端到端验证）」。本会话仍**无监理放行** ⇒ 只做 ENlegal 面。
> 装置：`/tmp/opencode/inc48/{A,B,C}/k2/`（`/tmp` 镜像树：`hw`·`pm_gate`·`_shared`·`k2_v4.kicad_pcb` 软链 + 模板/生成器副本）；**仓库零写入、未改生成器**。

## 0. 结论（三条，第 2 条是**停点**）

1. **`G11` 候选补丁已端到端验证**：三方对照证明它**消除 `boards/` symlink 依赖**且**行为零变化**（产物逐字节相同 `f615ffe6b83b88a3`）。见 §1。
2. **`G9` 存在一处 ENG 不能自裁的停点**：`SPEC.components.pin_headers` 的排针列 `column_x = 26.5` 与**权威值 `27.94`** 矛盾
   （权威来源 = L2-3 裁决，已写入 L3 图纸 `p3_drawings.json`、已落在 l5 板、并被 #K2-21 §二⑥「守恒闸 排针列 `column_x=27.94`」固定），
   **且生成器 `check_pin_headers`（S8 自检）当前强制 26.5** ⇒ 任何「按 SPEC 取几何」的 G9 实现都会落在错误列**并被自身自检拒绝正确值**。
   解此停点须**改 SPEC 或改自检源**（属放行范围）⇒ 见 §3，**请监理裁（或升级 owner）**。
3. **`G9` 的 pad 来源半边无需 `⑦` 落件**：所需封装**已在库**（现仓库 20 件快照含 `PinHeader_1x04/1x02`、`DS320PR1601`），`fp-lib-table` 可解析；
   且 l5 板已给出**逐 pad 验收基准**（见 §2）⇒ G9 一旦放行即可**带字节级验收测试**实施。

## 1. `G11`（真源路径配置驱动）候选补丁 —— 已验证

**补丁（候选，未落库）**：把 `YAML_PATH` 由硬编码改为 `pm_gate.config` 驱动，并**移到 `_PMCFG` import 之后**（原第 39 行在 import 之前）：

```diff
 ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
-YAML_PATH = os.path.join(ROOT, "boards/k2_sch.yaml")
-# G2(§五④): SPEC 路径经 pm_gate.config 解析（禁硬编码 SPEC 名；根因 F-14/N-05）
+# G11(§五④): 真源网表路径经 pm_gate.config 解析（禁硬编码 + 禁 symlink 兜底；根因 F-14/N-05）
 sys.path.insert(0, os.path.join(ROOT, "_shared"))
 os.environ.setdefault("PM_GATE_PROJECT_ROOT", ROOT)   # 自定位：不依赖调用方 cwd
 from pm_gate import artifacts as _ARTIFACTS, config as _PMCFG   # noqa: E402
+YAML_PATH = os.path.join(ROOT, _PMCFG.project_config()["nets_yaml"])
 SPEC_PATH = _ARTIFACTS.path("L3", _PMCFG.spec_name())
```

**三方对照（`/tmp/opencode/inc48/`，同一 `K2_OUT_PCB` 重定向）**：

| 案 | 装置 | 结果 | 产物 sha16 |
|---|---|---|---|
| A | **未打补丁** + 有 `boards/k2_sch.yaml` symlink | 成功（= 现行行为基线） | `f615ffe6b83b88a3` |
| B | **已打补丁** + **无** `boards/` | **成功** | **`f615ffe6b83b88a3`（与 A 逐字节相同 ⇒ 行为零变化）** |
| C | **未打补丁** + **无** `boards/` | **rc=1 `FileNotFoundError: …/C/k2/boards/k2_sch.yaml`**（`parse_yaml` `:143`） | 未产出 |

⇒ B 证明 G11 **确实解除 symlink 兜底**（C 的失败即该依赖的负控）；B==A 证明**不改行为**（配置值 `hw/data/k2_sch.errata-1.yaml` 与现行 symlink 目标 `hw/data/k2_sch.yaml` 在生成器消费字段上等价——本对照顺带确证）。
**副作用登记（须监理知悉）**：G11 后生成器读的是 `project_config()["nets_yaml"]`，其**现值 = `errata-1`，正是 F1 判定 `netlist_connect` FAIL 106 处的那份**（inc46 证据件 §1）。⇒ 若 G11 放行，宜与 F1/F2 的「真源路径归一（甲）」**同批**处理，否则生成器与管线判据指向不同真源。
**未覆盖**：G-ROOT-3 的 ③「删 `k2/k2_v4.kicad_pcb` symlink」绑定在 G9 锚板去依赖上，本补丁不含。

## 2. `G9` 的 pad 来源半边：**无需 `⑦` 落件** + 验收基准（仓库只读实测）

- 库内封装**已存在**：`PinHeader_1x04.kicad_mod`（4 pad）· `PinHeader_1x02.kicad_mod`（2 pad）· `DS320PR1601.kicad_mod`（**354 pad**）；
  `hw/fp-lib-table` = `ForgeOS → ${KIPRJMOD}/lib/ForgeOS.pretty` ⇒ 可解析。
  库内排针 pad 几何：`thru_hole circle`、`size 1.5×1.5`、`drill 0.8`、层 `*.Cu/*.Mask`、**局部间距 2.54mm**（`y = -3.81/-1.27/1.27/3.81` 与 `-1.27/1.27`）。
- **l5 板（受审交付板）的排针 pad = 逐 pad 验收基准**（本件只读实测，5 件共 **16 pad**，即 IN-11 所指）：

| ref | 封装 | fp at (x,y) | rot | pad 局部 y | type/shape | size | drill |
|---|---|---|---|---|---|---|---|
| `J13` | `PinHeader_1x04` | (27.94, 46.54) | 90 | -3.81 / -1.27 / 1.27 / 3.81 | thru_hole circle | 1.5×1.5 | 0.8 |
| `J9` | `PinHeader_1x04` | (27.94, 55.96) | 90 | 同上 | 同上 | 1.5×1.5 | 0.8 |
| `J11` | `PinHeader_1x04` | (27.94, 65.38) | 90 | 同上 | 同上 | 1.5×1.5 | 0.8 |
| `J6` | `PinHeader_1x02` | (27.94, 39.66) | 90 | -1.27 / 1.27 | 同上 | 1.5×1.5 | 0.8 |
| `J12` | `PinHeader_1x02` | (27.94, 35.32) | 90 | -1.27 / 1.27 | 同上 | 1.5×1.5 | 0.8 |

  与 L3 图纸 `p3_drawings.json` 自述一致：`"geom_src": "lib 封装几何 @(column_x=27.94, y=…, rot=90)（板 0 焊盘）"`、`pad_aabb: [23.38, 64.63, 32.5, 66.13]`（= 27.94±(3.81+0.75)）。
- 生成器现状（inc47 已复现）：这 5 件输出 **0 pad**；`else:` 分支的 size-class 几何**不覆盖**排针（排针走 anchor 分支 `:342-346`）。
- **P3 图纸自述即支持 G-ROOT-1 ②**：`p3_drawings.json` 明写「排针列按 lib 封装几何 @column_x=27.94（**板 0 焊盘 ⇒ 不得用板几何**）」⇒ 「锚板 pad 不得作来源」在 P3 侧早有记录。

## 3. `G9` 的几何半边：**停点**（SPEC ↔ 权威 27.94 矛盾 + S8 自检强化陈旧值）

| 事实 | 证据 |
|---|---|
| SPEC 仍是被修正**前**的值 | `SPEC_k2_v4.spec-rev-47.json` `components.pin_headers.column_x = 26.5`，`positions` 亦为 `[26.5, y]`（26.5 出现 8 次 / 27.94 出现 2 次） |
| 权威值 = **27.94**（L2-3 裁决） | `L3/drawings/p3_drawings.json`：排针 `at: [27.94, y]`、`src: "SPEC pin_headers.positions（column_x 由 L2-3 修正 26.5→27.94）"`、`note: "L2-3 移位 dx=+1.44mm（column_x 26.5→27.94）"`、`D1_pinheader_interference.column_x = 27.94`；l5 板实测 `fp_at.x = 27.94`（§2）；#K2-21 §二⑥ 守恒闸亦为 `27.94` |
| **S8 自检强制陈旧值** | `tools/k2_gen_v5.py::check_pin_headers` = 「排针坐标 == SPEC components.pin_headers.positions (精确匹配)」，不符即 `raise ValueError("[S8 PIN_HEADER] … != 冻结坐标")`；生成器运行输出亦打印 `排针坐标 (SPEC 冻结): …@(26.5,…)` |

⇒ **矛盾成立**：任何「从 SPEC 取排针几何」的 G9 实现会落在 `26.5`（偏离权威 `27.94` 达 **1.44mm**），且其 **S8 自检会拒绝**把坐标校正为 `27.94`。
⇒ 本停点 ENG **不自裁**（触及 (a) 冻结侧 SPEC 取值、(b) 排针列这一**板级接口坐标**）：**请监理裁**「以 27.94 为准并 bump SPEC（`components.pin_headers.column_x`/`positions`）」或「指定 G9 几何改为消费 L3 图纸」；若判定属 L1（接口坐标）请**升级 owner**。
⇒ 该矛盾**同时影响 G9 收敛判据**：G9 的验收不能只比「pad 数/几何」，还须与守恒闸 `column_x=27.94` 一致，否则修完仍破守恒闸。

## 4. `G10` 现状（不变）

输入在库（`L3/drawings/01_board_frame_and_holes.svg`）；停点仍为**固定孔逐座标确认**（#K2-22 登记）+ keepout/zone 生成段需新写（无可复用的现成段）。本件未推进（无放行且非本轮指名项）。

## 5. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw; M=/tmp/opencode/inc48
# G11 三方对照（A=未打补丁+有 boards/ · B=已打补丁+无 boards/ · C=未打补丁+无 boards/）
#   镜像树构建与补丁文本见本件 §1；期望：A/B 产物 sha 相同，C rc=1 FileNotFoundError
K2_OUT_PCB=$M/out_base.kicad_pcb K2_OUT_JSON=$M/out_base.json python3 $M/A/k2/tools/k2_gen_v5.py
K2_OUT_PCB=$M/out_fix.kicad_pcb  K2_OUT_JSON=$M/out_fix.json  python3 $M/B/k2/tools/k2_gen_v5.py
K2_OUT_PCB=$M/out_c.kicad_pcb    K2_OUT_JSON=$M/out_c.json    python3 $M/C/k2/tools/k2_gen_v5.py; echo "rc=$?"
# 库内封装 pad 几何 / l5 验收基准 / SPEC-vs-L3 矛盾：见 §2 §3 内联解析
# SPEC 侧陈旧值 vs L3 侧权威值（实测：SPEC 26.5 / L3 图纸 27.94 出现 25 次，含 "26.5→27.94" 裁决注记）
python3 -c "import json;d=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json'));ph=d['components']['pin_headers'];print('SPEC column_x =',ph['column_x'],' positions.x =',sorted({v[0] for v in ph['positions'].values()}))"
grep -c '27\.94' k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json
grep -o 'column_x 26.5→27.94' k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json | head -1
```

## 6. 边界

本件**只读 + `/tmp` 运行/补丁（未落库）**：未改生成器/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/SPEC/真源/`criteria/**`/`_shared/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
`/tmp/opencode/inc48/` 全部产物易失（按 §5 重建）。
—— ENG（ARCHER）· 2026-09-18 · 生成器 `d8d15a31061f450f` · 受审板 `6ff49da5678c2108`
