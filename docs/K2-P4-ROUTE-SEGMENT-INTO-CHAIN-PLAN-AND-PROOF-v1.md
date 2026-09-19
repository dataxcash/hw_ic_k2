# K2 · P4 · #K2-31 §二 (A)「链内路由器段」—— **段定义 + P3 子段逐段复现证明 + 施工计划** · v1 · 2026-09-19

> 依据：监理 **#K2-31 §二**（裁 (A)：链必须自己产出布线；段 = `生成器 → 路由器段 → zone fill → 落件`）+ **§2.1 段2/3 硬要求**（输入须为段1 中间产物、两次连跑逐字节同、撤 `l4`/`l5` 仍产出完整板、不放松 DRC、报逐段 sha）+ **§2.2 同批三项** + **§四-5**。
> 本件 = **只读取证 + 段定义**（未改任何载体；`l6` 未落；未动 `l4`/`l5`/生成器/SPEC/真源/`criteria/**`/冻结件）。临时仅 `/tmp/opencode/l6c`。

## 0. 结论（先给）

1. **段2 已定义为三段**（§3）：`段2a 图纸直构` + `段2b PDN 连接施加` + `段2c P4 收敛族`；`段3 = ZONE_FILLER`；`段4 = 落件 + pro 补丁`。
2. **段2a/2b 已证明可逐段再生**：以**设计源板**为底，`段2a + 段2b` 产出 l4 的 **3005 段走线，逐段 0 差**（`only_A=0 / only_B=0`；fps 42/42 · nets 93/93 · 图元同）。⇒ 高速+PDN 布线**可由链内工件确定性再生**，非「只能靠旧板」。**这是 (A) 可行性的关键证据。**
3. **段1 与 l5 的 zone / net 集已同构**（实测）：段1 的 **18 zone**（4×`F.Cu` 规则区 + 4×全层规则区 + 10 铜区）= l5 的 18 zone **逐一对应**，差**仅填充**（段1 未填 / l5 已填）⇒ 段3 = 纯 `ZONE_FILLER`；段1 的 **102 网** = l5 的 **101 网 + `NO_CONNECT`** ⇒ §2.2-2 的修复点 = 段2c 的 `converge_v1` 阶段 A1（NC pad 不入网，正是当时的修复动作）。
4. 剩余施工 = **段2c（P4 收敛族 ≥16 增量 / 13 脚本）re-hosting 到段1 产物上**，并逐项验证（§5）。

## 1. 路由来源图（实测，非推测）

| 板 | fps | 网 | zone | 走线（F/In1/In2/In4/In5/B/via） | 填充多边形 |
|---|---|---|---|---|---|
| 设计源板 `fb07d25a` | 42 | 93 | 0 | **0** | 0 |
| **`段1`（`k2_gen_v5.py`）** | **58** | **102** | **18** | **0** | **0** |
| `l4` `d4e81f64` | 42 | 93 | 13 | 3005（359/0/106/0/2008/39/493） | 0 |
| `l5` `dae8dc8d` | 58 | 101 | 18 | 5430（2232/1/292/4/1907/284/710） | 11 |

⇒ 路由来源两条支：**(i) P3 段**（设计源板 → l4 的 3005 段）· **(ii) P4 收敛族**（l4 → l5 的 +2425 段，其中 `In5` −101 = 重派生）。

## 2. 段2a/2b 复现实验（本件实测；`/tmp` 内，仓库只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# 段2a：图纸直构（W3 图纸 34 页 + REFCLK path；底 = 设计源板）
L4_OUT=/tmp/opencode/l6c/w3_apply.json AppDir/usr/bin/python3.11 k2/tools/p3_v57_l4_apply_drawing.py \
  --board --out-board /tmp/opencode/l6c/p3a.kicad_pcb        # ⇒ 2579 段（逐段 ⊆ l4；only_B=0）
# 段2b：PDN 连接施加（SPEC rev-19 坐标；幂等 purge-then-add）
AppDir/usr/bin/python3.11 k2/tools/p3_v57_co102_pdn_apply_local.py \
  --board /tmp/opencode/l6c/p3b.kicad_pcb --out /tmp/opencode/l6c/co102.json   # ⇒ +185 track / +241 via
```

| 关口 | 结果 |
|---|---|
| 走线段集 vs l4 | **3005/3005，`only_A=0`、`only_B=0`（逐段几何+层+网全等）** ✅ |
| fps / nets / 图元 | 42/42 · 93/93 · 1/1 ✅ |
| zone | 9 vs 13（**差额 = l4 的 4×`F.Cu` 规则区**；而 `段1` 的 18 zone 已含 4×`F.Cu` + 4×全层规则区 ⇒ **新链以段1 为准，不用段2b 的 zone 段**） |
| 段2b 参数修正 | 新链只取 `--stage connect`（只加 stubs/vias，**不动 zone**）⇒ 避免与段1 的 zone 集互踩 |
| 产物 sha16 | `段2a` `1d702aee8508951d` · `段2a+2b` `6740b2cf22220c28`（与 l4 `d4e81f64…` **不同**：zone 9≠13 + uuid/格式；**语义按上表逐项比对**） |

## 3. 段定义（提交监理确认的链拓扑）

| 段 | 件 | 输入（**只许链内**） | 产出 | 现状 |
|---|---|---|---|---|
| **段1** | `k2_gen_v5.py` `1ca5ac79698f5873` | 真源 YAML errata-2 + canonical SPEC rev-50 + `ForgeOS.pretty`/`refmap` + `L2/PLACEMENT_SOLUTION_v1.json` | PCB：58 fps · 18 zone（未填）· 4 NPTH · 板框 | **已成立**（`d67c0f04`） |
| **段2a** | `p3_v57_l4_apply_drawing.py`（待加 `--src`） | 段1 产物 + W3 图纸 `m13_v57_w3_joint_assignment.json`（+ `escape_domain`） | HS 布线 2579 段 | **需 re-host**（现硬编码底 = 设计源板；写入路径 `relative_to(K2)` 须改） |
| **段2b** | `p3_v57_co102_pdn_apply_local.py --stage connect` | 段2a 产物 + SPEC rev-19（PDN 坐标源） | PDN 185 track / 241 via | **需 re-host**（`--board` 已参数化；仅取 connect 段） |
| **段2c** | P4 收敛族（§5 清单；≥16 增量） | 段2b 产物 + 链内即时 DRC | 低速/电源/边带/PDN 剩余布线 + NC 语义归一 | **待施工**（13 脚本逐个 re-host） |
| **段3** | `ZONE_FILLER`（`pcbnew.ZONE_FILLER`） | 段2c 产物 | 10 铜区填充 | 待接（工具已散见 `k2_p4_*`；须固化为一段） |
| **段4** | 落件 | 段3 产物 + pro 补丁 | `k2/hw/k2_v4_8L.l6.kicad_pcb` / `.l6.kicad_pro`（`l5` 保留历史件） | 待落 |

**段4 的 pro 补丁（具名，均由裁定的规则强度/一行键值组成）**：① `rule_severities` 9 条 `ignore`→`warning`（= `l5` pro 口径，`#K2-30 §2.1`）；② `schematic.top_level_sheets` → 现行根图 + 消 `sheets: []`（= `#K2-30 §2.4` / `N-03`）。

## 4. 段2c 收敛族清单（来源：`K2-P4-CONVERGENCE-STATUS-v1.md` §7–§25 + `k2_p4_RETIRED.md`）

`converge_v1`(A1 NC 语义/旧铜避让/丝印) → `gnd_vias_v1`(E) → `ls_local_v1`(F1) → `ls_route_v1`(F2) → `ls_xlayer_v1`(F3) → `ls_xlayer` 加强(7/8) → `ls_in2_v1`(G) → `u4d_refclk_plan_v1`+`u4d_refclk_emit_v1`(10/11 非 45° 全归零) → `pdn_in4_v1`(12) → `u1c85_v1`(13) → `p3v3_col_v1`(14) → `mroute_v1`(15) → `mroute` 重做(16) → …（后续增量至未连接 0）；装配件 `c86_relocate_v1` / `l2_placement_courtyard_v1` / `tncv_align_v1` / `pdn_stitch_v1`。

## 5. 硬要求与风险（**报监理，不静默**）

| # | 项 | 要求/风险 |
|---|---|---|
| 1 | 输入面 | 段2a/2b/2c **一律只读链内中间产物**（`/tmp`）；**不得**读 `l4`/`l5`/设计源板/锚板作为真值源（#K2-31 §二-1）；段2a 现硬编码底须改 `--src` |
| 2 | 确定性 | 两次连跑**逐字节同**：需钉死 uuid 策略与排序（P3a/b 用 `uuid`；`k2_gen_v5` 用 uuid5 确定性）；**逐段报 sha** |
| 3 | 撤板三臂 | 移走 `l4`/`l5` 后链仍产出**完整板**（含布线 + 已填充铜区） |
| 4 | 不回归 | `unconnected_zero = 0` · `non45_segments = 0` · DRC error 0 · `zone_filled 10/10` · 网集 = 101（消 `NO_CONNECT`） |
| 5 | **起始板态差异（最大风险）** | 段1 = **58 fps / 102 网 / 18 zone**，而 P4 收敛族的原始起始板（l4）= 42 fps / 93 网 / 13 zone。收敛增量多为「针对该板态的定点修复 + DRC 驱动」⇒ 直接套用**可能不收敛或行为漂移**；须**逐器核前置假设**并以 DRC/未连接读数验收（不得为凑读数删差异，C-12） |
| 6 | 段2c 的 DRC 依赖 | 多数器需 `--drc <board>.json`：须在**链内**即时 `kicad-cli pcb drc` 生成（确定性；禁用旧 `/tmp` 残留，见 E-3 §4 具名坑） |
| 7 | 排针面别（§2.2-3 / ⑥） | 段1 = `F.Cu`（同 l4）；l5 = `B.Cu`（P4 期翻面）。**面别是制造事实** ⇒ 须先由 SPEC/L2/机械口径定案，再决定哪一段落面别；**不得**当口径忽略 |

## 6. 复跑（本件每处实测）

见 §2 命令块；比对器 `k2/docs/drafts/p4-l6-reland-v1/board_delta_v1.py` `eda6d25a18c42f98`。

**边界**：本件只读取证 + 追加文档；未改板/pro/库/SPEC/生成器/真源/`criteria/**`/`_shared`/冻结件；未落 `l6`；未派 WORKER；**未新增检查齿**；未以「接近 0」宣称归零。
—— ENG（ARCHER）· 2026-09-19 · 受审板 `dae8dc8d`（未动）· 判据锚 rev=2 · `l4` `d4e81f64`（未动）· 产物 `d67c0f04`（未动）
