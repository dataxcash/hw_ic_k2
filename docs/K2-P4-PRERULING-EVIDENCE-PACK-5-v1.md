# K2 · P4 · **裁定前纯证据包 #5**（#7 `J-1` 逐条台账导出 + 可安装登记块 · #10 `L-1` 具名接受拟稿 · P4 关门检查单）· v1 · 2026-09-19

> 授权：handoff §7-3（取证；**不触载体**）。本件**不落** `criteria/**`（安装/签认归 gate 属主 + 监理）。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 `d251bea7c2cb1873` · 受审板 `l6 30fa849641323f98` · pro `12ad219b9f66b7b3`

## 0. 一句话

- **#7 `J-1`**：164 条 warning **逐条机读台账已成**（`docs/data/K2-P4-J1-WARNING-LEDGER-l6-30fa8496.json` **`f468c026006c6d17`**）：**74 已登记 / 90 未登记（7 类）**；并给出**可直接粘贴的 7 条** `drc_warning_dispositions` 登记块（字段与 rev=2 现行两条同构）⇒ 批准后 gate 属主安装即关 **FAIL-1**（登记制，**不豁免**）。
- **#10 `L-1`**：**具名接受文本拟稿**已出（零改造；P4 关门可直接引用；28 件清单见证据包 #3）。
- **§3**：**P4 关门检查单**（未闭 **14** 条 × 阻塞裁定 × 收口路径）。

---

## 1. `J-1` —— 逐条台账导出 + 可安装登记块

### 1.1 导出件

| 项 | 值 |
|---|---|
| 件 | `k2/docs/data/K2-P4-J1-WARNING-LEDGER-l6-30fa8496.json` |
| sha16 | **`f468c026006c6d17`** |
| 来源 | 在册 DRC `drc_violations_clean_workdir.json` **`ad472105c88b2256`**（全新 work-dir） |
| 计数 | **164** = 已登记 **74**（`missing_courtyard` 54 + `lib_footprint_mismatch` 20）+ **未登记 90**（7 类） |
| 条目字段 | `seq · type · severity · description · registered_in_rev2 · items[{description,pos(x,y),uuid}]`（确定性排序：type→x→y→desc） |
| 判据 | `drc_warning_dispositions: board_warning_types ⊆ drc_warning_dispositions[].type`（rev=2） |

### 1.2 建议登记块（**可直接安装**；7 条新增，2 条现行不动）

```yaml
drc_warning_dispositions:
  # —— 已登记 2 条（rev=2 现行，不动）——
  - {type: missing_courtyard, disposition: "不豁免；登记为 J-7 图形级已知缺口 + L2 placement 项", evidence: "k2/docs/K2-P4-W7-SUPERVISION-DECISION-SHEET-v1.md 项4 + 监理 #K2-21 §〇③"}
  - {type: lib_footprint_mismatch, disposition: "以板为准（W-8）：电气级 0，图形/属性级容忍，逐条登记", evidence: "k2/docs/K2-J7-W8-FOOTPRINT-LIB-AUDIT-v1.md（59 件）"}
  # —— 建议新增 7 条（承 #K2-30 §2.3；逐条证据 = K2-P4-J1-WARNING-LEDGER-l6-30fa8496.json f468c026006c6d17）——
  - {type: silk_over_copper,          disposition: "不豁免；丝印图形级（被阻焊裁剪）；归属 U-05/J-4 丝印重排（P5 出图前处置）", evidence: "k2/docs/K2-P4-J1-WARNING-DISPOSITION-LEDGER-AND-U03-REMAINDER-v1.md §1 + 本件导出表 silk_over_copper 37"}
  - {type: track_not_centered_on_via, disposition: "不豁免；布线图形级；归属链内路由器（段2 器）产物，逐条登记",           evidence: "k2/docs/K2-P4-J1-WARNING-DISPOSITION-LEDGER-AND-U03-REMAINDER-v1.md §1 + 本件导出表 track_not_centered_on_via 30"}
  - {type: silk_overlap,              disposition: "不豁免；丝印图形级（丝印间距）；归属 U-05/J-4",                        evidence: "k2/docs/K2-P4-J1-WARNING-DISPOSITION-LEDGER-AND-U03-REMAINDER-v1.md §1 + 本件导出表 silk_overlap 15"}
  - {type: via_dangling,              disposition: "不豁免；过孔未连/仅单层连（P3V3/PERSTA#/UART_TX/SWCLK_BOOT0 各 1）；归属 PDN 缝合孔步（段2 器）", evidence: "本件导出表 via_dangling 4（逐条具名）"}
  - {type: silk_edge_clearance,       disposition: "不豁免；丝印被板边裁剪（C87/D2 参考字段）；图形级",                  evidence: "本件导出表 silk_edge_clearance 2（逐条具名）"}
  - {type: track_dangling,            disposition: "不豁免；GND 走线端悬空 0.775mm；归属 mroute 残段",                  evidence: "本件导出表 track_dangling 1（逐条具名）"}
  - {type: copper_sliver,             disposition: "不豁免；In4.Cu 铜箔毛刺 ×1；归属 In4 分区几何（L2）",                evidence: "本件导出表 copper_sliver 1"}
```

### 1.3 逐类条目（小类全列；大类前 6 + 指向导出件）

**`missing_courtyard`（54 条，已登记）**

- #22 封装 J12 @(27.94,35.32)
- #23 封装 J6 @(27.94,39.66)
- #24 封装 J13 @(27.94,46.54)
- #25 封装 J9 @(27.94,55.96)
- #26 封装 J11 @(27.94,65.38)
- #27 封装 C73 @(28.0,47.9)
- …… 余 48 条见导出件 `ledger[]`（type=missing_courtyard）

**`silk_over_copper`（37 条，**未登记**）**

- #78 J12 的参考字段 @(25.94,35.32)
- #79 J6 的参考字段 @(25.94,39.66)
- #80 J13 的参考字段 @(25.94,46.54)
- #81 J9 的参考字段 @(25.94,55.96)
- #82 J11 的参考字段 @(25.94,65.38)
- #83 C73 的参考字段 @(28.0,45.9)
- …… 余 31 条见导出件 `ledger[]`（type=silk_over_copper）

**`track_not_centered_on_via`（30 条，**未登记**）**

- #131 走线 [P3V3] (B.Cu), 长度: 5.9500 mm @(29.0,38.2)
- #132 走线 [GND] (F.Cu), 长度: 0.1247 mm @(30.35,53.0)
- #133 走线 [GND] (F.Cu), 长度: 0.3001 mm @(30.438176,53.088176)
- #134 走线 [FB_U2] (In2.Cu), 长度: 3.6000 mm @(30.5,37.6)
- #135 走线 [UART_TX] (B.Cu), 长度: 10.3054 mm @(32.7,56.0)
- #136 走线 [I2C1_SDA] (B.Cu), 长度: 0.3000 mm @(33.2,47.9)
- …… 余 24 条见导出件 `ledger[]`（type=track_not_centered_on_via）

**`lib_footprint_mismatch`（20 条，已登记）**

- #2 封装 J12 @(27.94,35.32)
- #3 封装 J6 @(27.94,39.66)
- #4 封装 J13 @(27.94,46.54)
- #5 封装 J9 @(27.94,55.96)
- #6 封装 J11 @(27.94,65.38)
- #7 封装 R41 @(29.5,34.0)
- …… 余 14 条见导出件 `ledger[]`（type=lib_footprint_mismatch）

**`silk_overlap`（15 条，**未登记**）**

- #115 C73 的参考字段 @(28.0,45.9)
- #116 C86 的参考字段 @(31.55,56.85)
- #117 R32 的参考字段 @(55.5,65.5)
- #118 R32 的参考字段 @(55.5,65.5)
- #119 R33 的参考字段 @(55.5,66.5)
- #120 C74 的参考字段 @(91.0,38.0)
- …… 余 9 条见导出件 `ledger[]`（type=silk_overlap）

**`via_dangling`（4 条，**未登记**）**

- #161 过孔 [SWCLK_BOOT0] (F.Cu - B.Cu) @(29.836871,47.099923)
- #162 过孔 [UART_TX] (F.Cu - B.Cu) @(30.411329,56.062563)
- #163 过孔 [PERSTA#] (F.Cu - B.Cu) @(32.525,54.5)
- #164 过孔 [P3V3] (F.Cu - B.Cu) @(40.263888,35.980223)

**`silk_edge_clearance`（2 条，**未登记**）**

- #76 Edge.Cuts 上的 线段 @(23.0,33.0)
- #77 Edge.Cuts 上的 线段 @(23.0,33.0)

**`copper_sliver`（1 条，**未登记**）**

- #1 铜箔毛刺 (In4.Cu) @(-,-)

**`track_dangling`（1 条，**未登记**）**

- #130 走线 [GND] (F.Cu), 长度: 0.7750 mm @(44.45,37.5)

---

## 2. `L-1` 具名接受文本拟稿（#10；P4 关门用，零改造）

> **拟稿（可直接引用）：**
> 「**`L-1` 具名接受（C4）**：经查 `k2/pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json`（rev=2 `086d453d23c5fbff`）之性质为**已批准落位（板侧 as-built）的 canonical 捕获**，**非独立求解**；54 件中 **28 件属「仅板来源」**（清单见 `K2-P4-PRERULING-EVIDENCE-PACK-3-v1.md` §2），另有 2 件（`C86`/`R42`）其解已被板侧修复超越并行陈旧。据此：**接受该 28 件以板侧坐标为权威来源**，用于 P4 及后续 P5 打样；**不主张**其为「独立推导」，**不得**在 P5 打样件与交付文档中隐去该来源限制；如后续需「完全非板来源」的坐标表，须另按 (b) placement 求解器工作包 或 (c) SPEC canonical 字段 bump 授权。」

- 引用锚：闭环表 §14.1 · §17/§23.8（C1 `dfbf65c5` + `086d453d` 未动）；证据包 #3 §2（28 件逐件具名 + 守恒 `54 = 11 + 15 + 28`）。
- 备选：**转 owner 授权 (c)**（bump SPEC canonical 几何字段承载该表）。

---

## 3. P4 关门检查单（未闭 **14** 条 × 阻塞）

根闭 40 / OUT 5 / **未闭 14**（计数不变；承闭环表 v1.12）。逐条阻塞与收口：

| ID | 阻塞裁定 | 收口路径 | 本轮证据 |
|---|---|---|---|
| `U-03` `M-09` `J-7` | #6 四路择一 | (A) 扩生成器发射面（pad rot + 无号 `F.Paste`）／(B) 判据侧具名「矩形 0≡180 + 无号 `F.Paste` 非电气」（rev bump+签认）／(C) 维持 FAIL | 证据包 #1（`(i-a)` 干跑 49/5/4/0→51/2/4/1）· #3 §2（仅 `J3`/`J4`） |
| `M-02` `M-14` `F-3` `N-02` | #8「无判据类」批定口径 | 批定后 5 条转根闭（#3 已给 `M-14` fail-OPEN 复现 + 6 处消费者） | 证据包 #2 §2 |
| `N-03` | —（载体已修） | `l6` pro `top_level_sheets=k2_sch.kicad_sch` + `sheets` 键已消 ⇒ 待判据/口径确认 | — |
| `J-1` | #7 登记安装（gate 属主） | 安装 §1.2 七条 ⇒ FAIL-1 关 | 本件 §1 |
| `J-8` | #9 `density_and_clearance` rev=3 启用 | gate 属主 rev bump + 签认 + 锚 rev=3（测量已达标） | 证据包 #3 §3 |
| `U-09` `M-12` | （承 §15.3） | 按闭环表余项通道（判据/口径 6） | — |
| `F-9` | #5 `NG-1` 口径具名/更正 + L2 冻结表回改 | owner/监理（改冻结件须 owner） | 证据包 #2 §1 · F-9 专件 `a316c49a` |
| `N-01` | **P5（未开）** | 出交付 Gerber（P4 全绿后方可） | fail-closed 未越 |

---

## 4. 复现 & 边界

```bash
python3 - <<'P'
import json,collections
d=json.load(open('k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-l6-20260920/drc_violations_clean_workdir.json'))
print(collections.Counter(x['type'] for x in d['violations']))   # 164 / 9 类
P
```
- 导出件 sha：`sha256sum k2/docs/data/K2-P4-J1-WARNING-LEDGER-l6-30fa8496.json` ⇒ `f468c026006c6d17…`。
- **未改**生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿；**未豁免任何 warning**（登记制，90 条逐条列名）；未以「接近 0」充绿。
