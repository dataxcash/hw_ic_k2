# K2 · P4 · E-3 标准调用接线 + 载体根闭重算 · v1 · 2026-09-18

> 触发：监理 **#K2-29** §六-2/§六-3（标准调用输入接线 + w8 审计对受审板重跑）+ §七（下一件 = E-3「载体根闭重算 + 余项闭环」，唯一，禁并行）。
> 边界：本件**只读取证 + 追加文档 + 落测量件**；未改受审板 / pro / 生成器 / SPEC / 真源 / `criteria/**` / 冻结件 / `_shared`；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**（owner ②）。
> 判据锚 **rev=2（MATCH）**：`criteria/manifest.k2.yaml` **`d251bea7c2cb1873`** · `criteria/adjudicate.py` **`1cda68521d0e56be`** · `criteria/CHANGELOG` **`568d2e93d53f854c`**（本会话独立复算，与 #K2-29 §五**逐字节吻合**）。
> 受审板 `k2/hw/k2_v4_8L.l5.kicad_pcb` **`dae8dc8d48ff5b81`**（未改）· pro **`35c8f34bde7ac00c`**（未改）。

## 0. 结论（先给）

1. **19 维标准调用接线完成并实跑**（受审板）：**15 OK / 2 FAIL**（判据锚 rev=2；非 PROVISIONAL）。
2. **两条 FAIL 同一根因** = **受审板 54 件 footprint `lib_id` 未重指到 `ForgeOS:<库快照变体名>`**：
   `drc_warning_dispositions`（未登记类型 `lib_footprint_issues`×2 = `J3`/`J4`）· `lib_electrical_level`（电气级差异 **28**）。
   **生成器侧已正确**（产物审计 49/58 identical）；**受审板落后于现行链**（见 §3）。
   该根因 = 闭环表 `U-03`/`M-09`/`J-7` 家族 ③ 明载的「**⑦ 库侧：按板重建 + 重指 `lib_id`**」之**后半**（前半「按板重建」= P1 已闭）⇒ **仍待监理裁定**。
3. 闭环表**重算 = `K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md` §15（v1.7）**：**根闭 40 / 未闭 14 / OUT 5**（v1.6 = 根闭 0 / 未闭 54 / OUT 5）。
4. §六-2/§六-3 接线结果：`density_and_clearance` 测量件已通且**读数达标**（10mm/frame_origin 峰 **7 ≤ 8**；最小铜间距 bracket **[0.100, 0.105] ≥ 0.100**）⇒ 启用只差 `criteria/` 一次 rev bump（gate 属主）；`ref_plane_continuity` 严口径 **83.52%** 仍升 owner（#K2-29 §四）。

## 1. 标准调用输入接线（§六-3）—— 5 件测量件

| # | 维/用途 | 测量命令（相对仓库根） | 读数 | `board_sha16` | 工具 sha16 |
|---|---|---|---|---|---|
| 1 | `lib_electrical_level` | `AppDir/usr/bin/python3.11 k2/tools/k2_w8_footprint_audit_v1.py --board <受审板> --proj-lib k2/hw/lib --out-json … --out-md …` | `identical 4 / electrical_diff 28 / no_library_link 24 / library_item_missing 2`（58 件） | `dae8dc8d48ff5b81` | `75404d706413d546` |
| 2 | `pads_within_outline` | `AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board <受审板> --json …` | AABB 出框 **0** · 真框多边形 **0** · 接口件 **0**（685 pad，inset 0.3） | `dae8dc8d48ff5b81` | 见落件 MANIFEST |
| 3 | `ref_plane_continuity`（uncovered） | `AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-v3-measurement-v1/measure_ref_plane_continuity.py --board <受审板> --json …` | nominal **3653/3653** · strict **3051/3653 = 83.52%** | `dae8dc8d48ff5b81` | 同上 |
| 4 | `density_and_clearance`（uncovered） | `AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_density_and_clearance.py --board <受审板> --json …` | 10mm/frame_origin 件峰 **7**；三横带 **4.73%/7.59%/2.19%**；异网 pad 最小 **0.20mm**；孔环 **0.075**；pad 到边 **0.38mm** | `dae8dc8d48ff5b81` | 同上 |
| 5 | `density_and_clearance`（最小铜间距） | `AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board <受审板> --pro <同名 pro> --kicad-cli AppDir/bin/kicad-cli --work-dir <新目录> --json …` | bracket **[0.100, 0.105] mm**（T=0.100 违规 0） | `dae8dc8d48ff5b81` | 同上 |

- 5 件均**自带 `board_sha16`**，与受审板一致 ⇒ 无陈旧 fail-closed。
- 落件位置：`k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-v1/`（+`MANIFEST.md` 记 sha）。
- ⚠ 测量 5 必用**全新 `--work-dir`**（本会话实测 #4 具名坑，见 §4）。

## 2. 标准调用（19 维）与 verdict

```bash
cd /home/fila/jqdDev_2025/ic_hw          # 容器根；--root . 为 #K2-29 §二-3 钉死口径
python3 criteria/adjudicate.py --project k2 \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --root . \
  --drc-cli AppDir/bin/kicad-cli --drc-work-dir <全新目录> \
  --w8-audit-json <(1)> --pads-outline-json <(2)> \
  --v3-plane-json <(3)> --density-json <(4)> --min-clearance-json <(5)>
```

| 维 | 判 | 读数 |
|---|---|---|
| `zone_filled` | OK | 铜区（有网非 keepout）**10/10**；keepout 规则区 8 另计 |
| `device_has_pads` | OK | 0 焊盘器件 **0** |
| `drill_count` | OK | NPTH **4** / PTH **16** |
| `net_declared_realized` | OK | 0 焊盘声明网 **0**；<2 焊盘 **0** |
| `pin_map_complete` | OK | 网表节点无对应焊盘 **0** |
| `non45_segments` | OK | 非 45° **0/4720** |
| `refdes_sets_equal` | OK | 排除 `H1..H4`（纯机械件，逐条列名）⇒ 原理图 54 / 板 54，差集 ∅ |
| `pipeline_present` | OK | `scope=k2`：无 pipeline.yaml 目录 **0**；范围外 6（他项目阶段门） |
| `verdict_schema` | OK | 产物含 `verdict` 字段 **0** |
| `drc_errors` | OK | DRC error **0**（违规总 69） |
| **`drc_warning_dispositions`** | **FAIL** | 未登记 warning 类型 **1/3**：`['lib_footprint_issues']`；已登记 `['lib_footprint_mismatch','missing_courtyard']` |
| `unconnected_zero` | OK | unconnected_items **0** |
| `fp_lib_table_present` | OK | `k2/hw/fp-lib-table` 存在 |
| **`lib_electrical_level`** | **FAIL** | 电气级差异 **28** + 仅 pad 名差异 0（须 0）；审计板 sha 与受审板**一致** |
| `pads_within_outline` | OK | AABB 0 · 真框 0 · 接口件 0；sha 一致 |
| `keepout_active` | OK | keepout 8 区，无生效开关 **0** |
| `rule_severity_manifest` | OK | 未登记豁免的 ignore **0/62** |
| `density_and_clearance` | （uncovered，`enabled:false`） | 测量齐、读数达标，未启用（见 §6） |
| `ref_plane_continuity` | （uncovered，`enabled:false`） | nominal 100% / strict 83.52%（升 owner） |

⇒ **15 OK / 2 FAIL**。可复跑：本会话连跑 2 次（含干净/复用 work-dir 对照）读数逐项相同。

## 3. 两条 FAIL 的同一根因：受审板 `lib_id` 未重指（具名）

### 3.1 受审板实测分布（pcbnew 只读）

| lib 昵称 | 件数 | 例 |
|---|---|---|
| **空（无昵称）** | **24** | `U6 (no-nickname) DS320PR1601` · `U1 … MCU_STM32G0_LQFP48` · `J9/J6/J11/J12/J13 PinHeader_*` · `H1..H4 MountingHole_3.2mm_M3` · `L1` · `D2` · R/C 若干 |
| `Capacitor_SMD` | 17 | `C85 Capacitor_SMD:C_0402_1005Metric` |
| `Resistor_SMD` | 9 | `R43 Resistor_SMD:R_0603_1608Metric` |
| `Package_SO` | 1 | `U2 Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` |
| `LED_SMD` | 1 | `D1 LED_SMD:LED_0603_1608Metric` |
| `ForgeOS` | 6 | `J2`✔ · `E2`✔ · `U4`✔ · `U5`✔ · **`J3`/`J4` = `ForgeOS:MCIO_4i_SFF-1016_RASide`**（快照仅 `…__1`/`…__2`）⇒ **`library_item_missing`×2** |

⇒ 28 件解析到**标准 KiCad 库**（其 land pattern ≠ 板）⇒ `electrical_diff` **28**；2 件 `ForgeOS:` 指向**不存在的 mod 名** ⇒ `library_item_missing` **2**（同时 DRC `lib_footprint_mismatch` 28 + `lib_footprint_issues` 2 = **30**，与 v1.5 §6 记载的 30 同源）。24 件空昵称无法解析（`no_library_link`）。

### 3.2 **生成器侧已正确**（产物 = 现行链代理）

`K2_OUT_PCB=/tmp/opencode/e3/gen/h1.kicad_pcb python3 k2/tools/k2_gen_v5.py` ⇒ sha16 **`d67c0f048f0d0423`**（自检 6/6 · 器件 54 · pads 672 · G10 8-10-4），其 `lib_id` 口径：

| lib 昵称 | 件数 | 例 |
|---|---|---|
| `ForgeOS` | **54** | `ForgeOS:C_0402_1005Metric__1` · `ForgeOS:MCU_STM32G0_LQFP48` · `ForgeOS:MCIO_4i_SFF-1016_RASide__1/__2` · `ForgeOS:DS320PR1601` … |
| 空 | 4 | `H1..H4 MountingHole_3.2mm_M3`（机械 NPTH，无库件依赖，audit 记 `no_library_link`，**不参与** `n_electrical_diff`） |

同一 W-8 审计对产物：**identical 49 / electrical_diff 5 / no_library_link 4 / missing 0**。⇒ **生成器已把 54 件 `lib_id` 写成 `ForgeOS:<refmap mod>`；受审板 l5 仍是旧口径**。

### 3.3 排除「KiCad 侧改写」（保真实验）

`pcbnew.LoadBoard(产物)` + `SaveBoard` ⇒ `lib_id` 昵称仍 `{ForgeOS:54, 空:4}`（逐件不变）。⇒ 受审板 l5 的旧 `lib_id` **不是** KiCad/pcbnew 引入，而是**受审板落后于现行链**（l5 落件早于 P1/P2 库快照与去锚板）。

### 3.4 「重指后」残差 5（产物代理实测，供裁定参考）

| 件 | diff 字段 | 量级 | 归属 |
|---|---|---|---|
| `C85` | `rot` 180° | — | **放置帧约定**（`fp_rot=180`）⇒ J-7b 归一草案域 |
| `J3` | `rot` 180° | — | 同上（`MCIO __1`） |
| `L1` | `dx` 1.062 vs 1.0625 | **0.0005 mm** | 板侧 3 位小数写盘 vs 库件 4 位 ⇒ 量化口径 |
| `U6` | `dx` 2.027 vs 2.0272 | **0.0002 mm** | 同上 |
| `U1` | `dx`（0.0005mm）+ `pad_name_set lib_only ['']` | — | 同上 + **库件含 1 枚空名 pad**（板侧 U1 = 49 带号 + 9 枚无号 `F.Paste` EP，见 §3.5-D） |

### 3.5 修复路径（**ENG 不择一；三项均属待裁**）

| 选项 | 内容 | 影响面 / 阻塞点 |
|---|---|---|
| **(a)** 受审板重落（l6）= 现行生成器产物 + l5 pro 规则强度/复合 | 受审板 sha 变更 ⇒ 判定器锚 / DRC / 5 件测量 / C1·C2·L-1 全部重锚 | 需监理放行（受审板变更）；**禁未获批改生成器**（生成器无需改，本项只是重新落件） |
| **(b)** 最小外科：仅改受审板 54 处 `lib_id` 串为 `ForgeOS:<refmap mod>`（几何/坐标不动） | 同上（sha 变），影响面最小 | 需监理放行 |
| **(c)** 判据侧：`lib_electrical_level` 改消费 `ForgeOS.refmap.json`（库↔板等价改由 refmap 定） | `criteria/**` 版本 bump + 签认 | **ENG 对 `criteria/**` 只读** ⇒ gate 属主/监理 |

预期（任一 + 余项裁定后）：28 → **5**（(a)/(b)/(c) 后产物代理实测）；再叠加 **J-7b 放置帧归一**（−2：`C85`/`J3`）与**量化口径**（−3：`L1`/`U1`/`U6`，≤0.5µm）+ **U1 库件空名 pad 清理** ⇒ 0。
另：`D` 项（U1 9 枚无号 `F.Paste` EP 的带号口径）与 `⑥` 项（5 件排针面别）为既有具名未裁项，**不因本件改口径**。

## 4. 具名旁证 —— 判定器 DRC 环境坑（fail-closed 隐患，非本件可改）

| 口径 | work-dir | DRC 读数 | `drc_warning_dispositions` |
|---|---|---|---|
| 默认（`work_dir=None`） | 复用既有 `/tmp/adj-drc/<stem>/`（其 `lib/` = **9-14 旧件**、`fp-lib-table` = 9-17） | **73 违规 / 2 类**（mismatch 34 + courtyard 39） | **PASS（假绿）** |
| 显式新目录 | 全新建 | **69 违规 / 3 类**（courtyard 39 + mismatch 28 + issues 2） | **FAIL（真读数）** |

- 机制：`criteria/adjudicate.py::measure_drc` 对 `fp-lib-table`/`lib` 仅在「目标不存在」时复制 ⇒ **旧目录静默复用**，同一受审板可给出 69 或 73 两种读数。
- 影响：**监理 #K2-29 §五 复跑记「16 OK / 1 FAIL」**正落在此口径（该 FAIL 为 w8 陈旧 sha 的 fail-closed）；以新鲜输入重跑后为 **15 OK / 2 FAIL**，其中 `drc_warning_dispositions` 为 #K2-29 读数**未覆盖**者。
- 归属：`criteria/**` 属工（gate 属主/监理）；**ENG 只报告不改判据**。

### 4.1 具名旁证（二）—— `verdict_schema` × W-8 测量件口径碰撞

`criteria/adjudicate.py::scan_verdict_keys` 以**正则 `"verdict"\s*:` 扫原文**判 J-10 ④；而 `k2_w8_footprint_audit_v1.py` 的**逐条记录字段名恰为 `verdict`**（`records[*].verdict` = `identical`/`electrical_diff`/…，58 条）。
⇒ **同一份 W-8 审计件**：作 `--w8-audit-json`（本件标准调用口径）**正确**；若被误作 `--artifacts` 传入 ⇒ `verdict_schema` 报 FAIL（假阳性）。
落件已在 `…/L4/E3-standard-call-v1/MANIFEST.md` 写明「测量输入，不得入 `--artifacts`」。**归属：`criteria/**` / W-8 工具命名 = gate 属主/监理**（ENG 只报告）。

## 5. 余项清单（归属 → 修复件 → 阻塞点）

| # | 项 | 归属 | 修复件 | 阻塞点 |
|---|---|---|---|---|
| 1 | 受审板 `lib_id` 未重指（`U-03`/`M-09`/`J-7`） | **监理裁定** | §3.5 (a)/(b)/(c) 任一 | 未获批；受审板 sha 变更 ⇒ 全测量链重锚 |
| 2 | `lib_footprint_issues`×2（`J3`/`J4` 无后缀 mod 名） | 同 #1 | 同 #1（一并消解） | 同 #1 |
| 3 | 放置帧归一（`C85`/`J3` rot 180°） | 监理（J-7b 草案待裁） | `w8_audit.draft-v2.py 34b83cff…`（ENG 已备 + 正负控） | 判据语义澄清属监理 |
| 4 | ≤0.5µm 量化口径（`L1`/`U1`/`U6`） | 监理 | 生成器写盘位数 **或** 审计容差（二择一；改生成器须放行） | 未获批改生成器 |
| 5 | `U1` 库件 1 枚空名 pad + 板侧 9 枚无号 `F.Paste` EP | 监理 | 库件清理 / `D` 带号口径裁定 | 未裁 |
| 6 | `density_and_clearance` 启用 | gate 属主/监理 | `criteria/manifest.k2.yaml` `enabled:true`（阈值已在件内）+ rev bump | `criteria/**` ENG 只读 |
| 7 | `ref_plane_continuity` | **owner** | (a) nominal 明示授权 /(b) 降阈值具名 /(c) 物理整改 | #K2-29 §四已升 owner |
| 8 | `N-03` pro `sheets: []` + `top_level_sheets → l4 根图`（不存在） | 监理放行 | l5 pro 一行键值 | 改 pro ⇒ pro sha 变 ⇒ 测量链重锚 |
| 9 | `F-9` 走廊口径两套未对账 | owner/监理 | L2 冻结表回改（改冻结件须 owner） | 未获批 |
| 10 | 「无判据类」根闭口径（`M-02`/`M-14`/`F-3`/`N-02`） | 监理 | 口径定义（**不新增检查齿**，owner ②） | 未裁 |
| 11 | `N-01` 交付 Gerber | P5（未开） | 出交付包 | fail-closed：P4 未全绿不下单、不出交付 Gerber |
| 12 | 模板 9 条 ignore（`U-05`/`M-08`/`F-6`/`N-06` 余项） | 计划 §P6（学习环） | `k2_jlc_template.kicad_pro` | 跨板复用项，不属 P4 受审板（已具名） |

## 6. 二维读数 vs 已裁阈值（#K2-29 §四）

| 维 | 已裁阈值 | 本件实测 | 判 |
|---|---|---|---|
| `density_and_clearance` | `cell_mm=10` · `cell_origin=frame_origin` · `max_fp_per_cell=8` · `min_copper_clearance_mm=0.100` | 件峰 **7** ≤ 8 ✓ · 最小铜间距 bracket **[0.100, 0.105]** ≥ 0.100 ✓ | **达标**（只差启用） |
| 同（可选 3 键，**未裁**） | 未给 | 三横带 max **7.59%** · 孔环 **0.075mm** · pad 到边 **0.38mm** | 报告，不作判 |
| `ref_plane_continuity` | `min_coverage 1.0`（严） | strict **83.52%** < 1.0；守恒级证明齐 | **不可达** ⇒ 升 owner |

## 7. 复跑（本件每处实测；仓库只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# ① 5 件测量（全新 work-dir！）—— 读数见 §1
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts; B=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro
$K k2/tools/k2_w8_footprint_audit_v1.py --board $B --proj-lib k2/hw/lib --out-json /tmp/opencode/e3/w8.json --out-md /tmp/opencode/e3/w8.md   # 期望 4/28/24/2
$K $D/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board $B --json /tmp/opencode/e3/outline.json                 # 期望出框 0/0/0
$K $D/p4-j8-v3-measurement-v1/measure_ref_plane_continuity.py --board $B --json /tmp/opencode/e3/v3.json                      # 期望 3653 / 3051
$K $D/p4-j8-density-clearance-v1/measure_density_and_clearance.py --board $B --json /tmp/opencode/e3/dc.json                  # 期望 10mm frame 峰 7
$K $D/p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board $B --pro $P --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/e3/clr --json /tmp/opencode/e3/mc.json  # 期望 [0.100,0.105]
# ② 19 维标准调用（--root .；--drc-work-dir 须全新）—— 期望 15 OK / 2 FAIL
# ③ 构造链确定性 —— 期望 sha d67c0f048f0d0423 且两次逐字节同
# ④ k2 门禁 —— 期望 4/4 PASS
cd k2 && PYTHONPATH="$PWD/_shared:$PWD" python3 _shared/eda_core/pipeline/engine.py verify k2; cd ..
```

## 8. 边界

**已改（本件）**：`k2/docs/K2-P4-E3-STANDARD-CALL-WIRING-AND-CARRIER-DELTA-v1.md`（新）· `k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md`（**追加 §15**；§0–§14 历史快照不改写）· `k2/pm_gate/artifacts/k2_v4/L4/E3-standard-call-v1/**`（新：5 件测量 + verdict + MANIFEST）。
**未改**：受审板 / pro · 冻结四源 · SPEC 原件（rev-47..50）· 真源 yaml · `criteria/**` · `_shared/**` · 生成器 · 库快照 · 模板 · `project.yaml` · L5 旧包 · `.omo/supervision/**`；未出 Gerber；未派 WORKER；**未新增检查齿**。
**fail-closed**：P4 未全绿（闭环表全闭 + 全 J 类绿）不下单、不出交付 Gerber。

—— ENG（ARCHER）· 2026-09-18 · 受审板 `dae8dc8d48ff5b81`（未动）· 判据锚 rev=2 · 产物 `d67c0f048f0d0423`（未动）
