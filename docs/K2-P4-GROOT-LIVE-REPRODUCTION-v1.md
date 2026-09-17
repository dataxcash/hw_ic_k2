# K2 · P4 · `G-ROOT-1/2/3` **活体复现**（冻结生成器 `/tmp` 运行）+ 修复输入就绪度 + N-03 载体实证 · v1 · 2026-09-18

> 缘起：监理续推令「按已批准整改计划推进当前阶段，阶段门未过不得越阶段」；本会话无放行 ⇒ 续做 handoff inc46 §6-3 指名项
> **(b) G-ROOT-1/2/3 候选化准备**。本件把 §6 G9/G10/G11 的①/②列从**代码阅读**升级为**活体复现**（owner 五列闭环表 ①现象/②载体 所需实据）。
> 装置：冻结生成器 `k2/tools/k2_gen_v5.py` **`d8d15a31061f450f`**（与闭环表记载一致），输出经 `K2_OUT_PCB`/`K2_OUT_JSON` 定向 `/tmp`；**仓库零写入**、未改生成器、未派 WORKER。

## 0. 结论

1. **G-ROOT-1 活体复现成立**：生成器产物对 5 个排针 `J6/J9/J11/J12/J13` 输出 **0 焊盘**、`U1` **33 pad** —— 与冻结锚板**逐项相同** ⇒ 锚板 pad 几何被继承（循环依赖）**在运行期可观测**，非仅代码推断。
2. **G-ROOT-2 活体复现成立**：产物 `thru_hole=0 · np_thru_hole=0 · zone=0 · keepout=0 · via=0 · segment=0` ⇒ 生成器确**无** NPTH/keepout/铺铜产出段。
3. **G-ROOT-3 载体复核**：`YAML_PATH` 硬编码 `ROOT/boards/k2_sch.yaml`，仅靠 symlink `→ ../hw/data/k2_sch.yaml` 解析；**而配置侧早已声明** `project_config()["nets_yaml"]="hw/data/k2_sch.errata-1.yaml"`（仅缺模块级访问器）⇒ G11 是**约 3 行**改动。
4. **N-03 载体实证（新增，独立于契约）**：生成器 `main()` 把 `tools/k2_jlc_template.kicad_pro` **逐字复制**为产物 pro
   ⇒ **每次生成都产出 `top_level_sheets → k2_eco22.kicad_sch`（不存在）**。⇒ 只改 l5 pro 必被判「板面修补」，**载体修必须含模板**。
5. **G9 的输入已冻结、数据充分**（此前最大不确定性）：排针 pad **数/号** 来自 `k2_sch.yaml::symbols[].pins`，**几何**来自 `SPEC.components.pin_headers` ⇒ 无需 L1/owner 追加输入；阻塞**仅**在「改生成器的放行」。
6. **新登记 D-6（声称/实际失配）**：生成器打印 `自检结果 (8/8)` 且注释写「8 项 fail-fast 自检」，实际仅登记 **6** 项（S1/S2/S4/S5/S6/S8）；`S3`/`S7` 全文件 **0 命中** ⇒ 自检覆盖被高报（D-1 同型：声称 ≠ 实际）。

## 1. 复现装置（确定性，仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
mkdir -p /tmp/opencode/inc47
K2_OUT_PCB=/tmp/opencode/inc47/k2_v5.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc47/k2_v5_layout.json \
  python3 k2/tools/k2_gen_v5.py          # 实测 exit 0
```

生成器自检输出（**注意声称 8/8、实际 6 项**）：

```
k2_gen_v5 自检结果 (8/8):
  ✅ S1 焊盘重叠 / S2 refdes 对齐 / S4 缺失器件 / S5 坐标范围 / S6 网表一致性 / S8 排针坐标冻结: PASS
  排针坐标 (SPEC 冻结): J11@(26.5,65.38), J12@(26.5,35.32), J13@(26.5,46.54), J6@(26.5,39.66), J9@(26.5,55.96)
  器件数: 42    pads 总数: 262    使用网名数: 101 (YAML nets 共 101)    NO_CONNECT pads: 27
```

## 2. G-ROOT-1 活体复现（锚板 pad 继承）

| 量 | 冻结锚板 `k2/hw/k2_v4_8L.kicad_pcb` `fb07d25ac426ff84` | 生成器产物 `/tmp/opencode/inc47/k2_v5.kicad_pcb` | 判 |
|---|---|---|---|
| footprint 数 | 42 | 42 | 一致 |
| pad 总数 | 616 | 262 | — |
| `U1` pad 数 | **33** | **33** | **继承** |
| `J6/J9/J11/J12/J13` pad 数 | **0 / 0 / 0 / 0 / 0** | **0 / 0 / 0 / 0 / 0** | **继承（0 焊盘被永久继承）** |
| 额外 0-pad 件 | — | **`U6`**（单颗 ReDriver，合 U3+U7 后） | **新观察**：`U6` 在产物中亦 0 焊盘 |
| thru_hole / np_thru_hole | 0 / 0 | 0 / 0 | 见 §3 |

代码位点（闭环表 §6 G-ROOT-1 ②）：`tools/k2_gen_v5.py:339-346` `anchor = ref_anchors_cache.get(ref) … d["pads"] = anchor["pads"]`；
锚板来源 `:45 PCB_REF_PATH = ROOT/"k2_v4.kicad_pcb"` → symlink → `hw/k2_v4_8L.kicad_pcb`（冻结设计源板，其 5 排针 0 焊盘、`U1` 33 pad，**本件独立复算确认**）。
⇒ **循环依赖运行期可观测**；`else:` 分支（`:347-360`）的 size-class 几何**不覆盖**排针（排针走 anchor 分支）。

## 3. G-ROOT-2 活体复现（无 NPTH / keepout / 铺铜产出）

产物实测：`thru_hole=0` · `np_thru_hole=0` · `zone=0` · `zone 内 keepout=0` · `via=0` · `segment=0`（锚板同为 0）。
`grep -c 'thru_hole'` = 仅 `:413/:415` 两处 pad 渲染；无 `NPTH`/`keepout` 生成段 ⇒ 与闭环表 §6 G-ROOT-2 ②一致，**运行期确认**。

## 4. G-ROOT-3 载体复核（硬编码 + symlink 兜底）

- 生成器：`YAML_PATH = os.path.join(ROOT,"boards/k2_sch.yaml")`（`:39`，硬编码）。
- 实测该路径**是 symlink**：`k2/boards/k2_sch.yaml -> ../hw/data/k2_sch.yaml`（不建即 `FileNotFoundError`）。
- **配置侧已具备**：`pm_gate.config.project_config()` 返回 `nets_yaml = "hw/data/k2_sch.errata-1.yaml"`；
  模块级访问器**仅缺 `nets_yaml`**（现有 `board_path`/`spec_name`/`l1_escape_edges`/`l1_candidate_fields`/`l1_g15`）。
- 对照：`SPEC_PATH` 已由 `_PMCFG.spec_name()` 配置驱动（`:42`）⇒ G11 属「照抄既有范式」，**约 3 行**。

## 5. N-03 载体实证（生成器每次运行产出悬挂指针）—— **决定「一行修复」不成立**

`tools/k2_gen_v5.py:766-767`：

```python
tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k2_jlc_template.kicad_pro")
dst  = OUT_PCB.replace(".kicad_pcb", ".kicad_pro")
shutil.copy(tmpl, dst)          # ← 逐字复制模板（含悬挂 top_level_sheets）
```

实测产物 pro：`schematic.top_level_sheets = [{"filename":"k2_eco22.kicad_sch","name":"k2_eco22","uuid":"00000000-…"}]`，
与 `tools/k2_jlc_template.kicad_pro` **逐字相同**，而该文件**不存在**（`find` 0 命中）。
同族（同值、同悬挂）：`k2/tools/k2_jlc_template.kicad_pro` · `k1/tools/k1_jlc_template.kicad_pro` · `k1/k1_v1.kicad_pro` · `k2/hw/k2_v4_8L.kicad_pro`。

⇒ 载体链 = **模板 → 生成器复制 → 产物 pro**（外加上一轮 N-03 件 §3 记录的 `pcbnew.SaveBoard` 侧车幻影项）。
⇒ `N-03` 的载体修复**必须**含模板（`k2/tools/k2_jlc_template.kicad_pro`），否则下次生成即复发 ⇒ 只改 l5 pro = 板面修补。

**反面澄清（避免误登记）**：`net_settings.classes` 注入**正常**（模板 1 类 → 产物 **4** 类，`netclass_assignments` 齐备），非缺陷。

## 6. `G9/G10/G11` 修复**输入就绪度**（决定「放行后是否一发可做」）

| 项 | 所需输入 | 现状 | 就绪 |
|---|---|---|---|
| **G9**（去锚板依赖） | 每器件 pad **数/号** + pad **几何** | **数/号**：`k2_sch.yaml::symbols[].pins.right`，形如 `HEADER_4PIN=[[TX,1],[RX,2],[GND,3],[VCC,4]]`、`HEADER_2PIN=[[PWR_BTN#,1],[GND,2]]`（引脚号在真源内）；**几何**：`SPEC.components.pin_headers{pad_diameter:1.5, column_x:26.5, rot:90, min_net_gap:0.3, positions:{J6,J9,J11,J12,J13}, layout_basis: 中心距=1.5+0.3=1.8mm}`；**pad 名**：`nets` 已声明（`J6/GND`、`J6/PWR_BTN#`、`J9/{GND,RX,TX,VCC}`、`J11/{EC_3V3,EC_SCL,EC_SDA,GND}`、`J12/{GND,VIN_12V}`、`J13/{GND,RX,TX,VCC}`） | ✅ **数据充分，无需追加 L1/owner 输入**（阻塞仅=放行） |
| **G10**（NPTH/keepout/zone） | 固定孔逐座标 + 回避区定义 | 图纸**在库**：`pm_gate/artifacts/k2_v4/L3/drawings/01_board_frame_and_holes.svg`；`ESC_*` 4 区定义在 SPEC | ⚠️ 孔位逐座标确认 = 闭环表登记的**停机点**（H3 曾与排针列冲突已裁）；keepout/zone 生成段需新写 |
| **G11**（配置驱动真源路径） | `nets_yaml` 配置 | `project_config()["nets_yaml"]` **已存在**；缺模块级访问器；删两个 symlink | ✅ 约 3 行（照抄 `spec_name()` 范式） |

> 口径：本表**不**新增检查齿（owner ②）；G9/G10/G11 收敛判据沿用已裁维度（V2 / J-3 `zone_filled` / J-8 `keepout_active` / J-10 两跑 sha 相同）。

## 7. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 活体复现（仓库零写入）
mkdir -p /tmp/opencode/inc47
K2_OUT_PCB=/tmp/opencode/inc47/k2_v5.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc47/k2_v5_layout.json \
  python3 k2/tools/k2_gen_v5.py
# ② 锚板 0-pad 排针 / U1 33（独立复算，不依赖生成器）
#    解析 k2/hw/k2_v4_8L.kicad_pcb：footprint=42 pad=616 U1=33 0-pad={J6,J9,J11,J12,J13} thru/npth=0
# ③ 产物 pro 悬挂指针（= 模板值）
python3 -c "import json;print(json.load(open('/tmp/opencode/inc47/k2_v5.kicad_pro'))['schematic']['top_level_sheets'])"
python3 -c "import json;print(json.load(open('k2/tools/k2_jlc_template.kicad_pro'))['schematic']['top_level_sheets'])"
# ④ G11 输入：配置已声明 nets_yaml，但无访问器
(cd k2 && PM_GATE_PROJECT_ROOT=$PWD python3 -c "
import sys,os;sys.path.insert(0,os.path.join(os.getcwd(),'_shared'))
from pm_gate import config as C
print('nets_yaml=',C.project_config()['nets_yaml'],' 访问器存在=',hasattr(C,'nets_yaml'))")
# ⑤ D-6：声称 8/8，实际 6 项
for n in 1 2 3 4 5 6 7 8; do printf 'S%s=%s ' "$n" "$(grep -c "\"S$n \|S$n " k2/tools/k2_gen_v5.py)"; done; echo
```

## 8. 边界

本件**只读 + `/tmp` 运行**：未改生成器/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/SPEC/真源/`criteria/**`/`_shared/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；
未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿）。
产物与布局仅存在于 `/tmp/opencode/inc47/`（易失，按 §7 重建）。
—— ENG（ARCHER）· 2026-09-18 · 生成器 `d8d15a31061f450f` · 锚板 `fb07d25ac426ff84`
