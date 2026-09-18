# K2 · P4 · #K2-30 §2.1 受审板重落 —— **硬条件第 1 条触发：停线**（L-3 布线来源）· v1 · 2026-09-18

> 依据：监理 **#K2-30 §2.1**「裁 **(a)**：`l6` = 现行生成器产物 + `l5` pro 规则强度/复合」+「**硬条件 1**：落件前逐件 diff（候选 l6 vs l5），差异**只允许** = ① 54 件 `lib_id` 串 + ② §3.4 具名 5 残差；**任何其他差异（几何/坐标/网络/zone/孔/层）⇒ 立即停线，不得静默落件**」。
> 本件 = **只读取证 + 停线报告**。**未落 l6、未改受审板/pro/生成器/SPEC/真源/`criteria/**`/冻结件**；未派 WORKER；临时仅 `/tmp/opencode`；未新增检查齿。
> 受审板 `k2/hw/k2_v4_8L.l5.kicad_pcb` **`dae8dc8d48ff5b81`**（未动）· 判据锚 **rev=2**。

## 0. 结论（先给）

**硬条件 1 已触发 ⇒ 停线报监理。**

候选 l6 = 现行生成器产物（`K2_OUT_PCB=/tmp/… python3 k2/tools/k2_gen_v5.py` ⇒ `d67c0f048f0d0423`，自检 6/6）与 l5 逐件 diff：

| 类别 | l5 | 产物 | 差 | 是否在裁定允许集 |
|---|---|---|---|---|
| **走线/过孔对象** | **5430**（`F.Cu` 2232 · `In5.Cu` 1907 · `via` 710 · `In2.Cu` 292 · `B.Cu` 284 · `In4.Cu` 4 · `In1.Cu` 1） | **0** | **−5430** | ✗ **不允许 ⇒ 停线** |
| **铜区填充多边形** | 10 铜区**均已填充** | 10 铜区 `IsFilled`=真但**填充多边形数 = 0** | 10 | ✗（属 zone；须补 ZONE_FILLER 复合步） |
| **网络集** | **101**（无 `NO_CONNECT`） | **102**（多出 `NO_CONNECT`，128 pad） | +1 网（表示差异） | ✗（属「网络」）⇒ 且**回退 F-10** |
| footprint | 58 | 58 | **50 件内容异**：42 仅 `lib_id` · 3 件 `lib_id`+pad（`L1`/`U1`/`U6`）· **5 件面别 `F.Cu↔B.Cu`**（`J6`/`J9`/`J11`/`J12`/`J13`，同 x/y/rot） | 42 在 ①；3 在 ②（§3.4）；**5 件面别 = ⑥，不在 ②** |
| zones 数 / keepout 数 | 18 / 8 | 18 / 8 | 0 | ✓ |
| 图元（`GetDrawings`） | 1 类 | 1 类 | 0 | ✓ |
| refs / x-y-rot | 58 | 58（同） | 0（除 5 排针面别） | ✓ |

⇒ 「① 54 件 `lib_id` + ② 5 残差」部分**符合预期**（42+3 = 45 件，与 54−4（`J2`/`E2`/`U4`/`U5` 本已正确）−5（排针）= 45 一致）；但 **走线（5430）· 铜区填充（10）· `NO_CONNECT` 网络 · 5 件排针面别** 均在允许集之外。**按硬条件 1 立即停线，未静默落件。**

## 1. 根因（证据级）：**现行构造链不产出布线**

| 事实 | 实测 |
|---|---|
| 现行链 `k2/tools/k2_gen_v5.py`（`1ca5ac79698f5873`） | 产出 = footprint（placement/pad）+ 板框 + NPTH + zone（含 keepout），**`GetTracks()` = 0** |
| 设计源板 `k2/hw/k2_v4_8L.kicad_pcb`（`fb07d25ac426ff84`） | `GetTracks()` = **0** · zones 0 · 42 fps（亦无布线） |
| **l5 的 5430 走线对象** | 来自**已离链的修补链**：`k2_p4_ls_route_v1`（F2 局部通路）· `k2_p4_ls_xlayer_v1`（F3 跨层通道）· `k2_p4_ls_in2_v1`（盲孔 + In2 通道）· `k2_p4_ls_local_v1`（F1 局部闭合）· `k2_p4_mroute_v1`（多层迷宫布线器）· `k2_p4_gnd_vias_v1`（GND 平面接入/via-in-pad）· `k2_p4_pdn_stitch_v1`/`k2_p4_pdn_in4_v1` · `k2_p4_converge_v1` · `k2_p4_c86_relocate_v1` —— **全部 RETIRED（离链）**（`k2/tools/k2_p4_RETIRED.md`，46 件） |

⇒ **受审板含「现行批准链无法再生」的布线**：这是与 **L-1（坐标来源 28 件仅板来源）** 同族的**来源缺口**，本件具名 **L-3（布线来源）**。
⇒ 因此 #K2-30 §2.1 的前提「l6 = 现行生成器产物（几何 == l5 几何）」**不成立**：产物与 l5 的差不是「只剩 lib_id」，而是**少整套布线 + 少铜区填充**。

## 2. 若字面执行 (a) 的后果（逐条具名，供裁定）

1. **布线全部丢失**（5430 对象 ⇒ 0）：`unconnected_zero`、DRC、`non45_segments`、阻抗/等长、P5 Gerber 铜层全部失效；
2. **铜区未填充**（10 区无填充多边形）⇒ `zone_filled` = **0/10 FAIL**、V3 参考连续性不成立；
3. **`NO_CONNECT` 网络回退**（产物仍建 128 pad 的 `NO_CONNECT` 网；l5 用「空网」表示）⇒ **F-10/M-17「假未连接」复活**；
4. **5 件排针翻面**（`J6`/`J9`/`J11`/`J12`/`J13`：l5 = `B.Cu`，产物 = `F.Cu`，同 x/y/rot）⇒ ⑥ 项**反向变更**（器件面别是制造事实，非口径）。

## 3. 请裁（四条修正路径，ENG 不择一）

| 选项 | 内容 | 代价 / 冲突 |
|---|---|---|
| **(A) 链内恢复路由器** | 把离链布线器（`mroute`/`ls_*`/`gnd_vias`/`pdn_*`/`converge`）重新纳入构造链为第二段（生成器 → 路由器 → 落件），定义其输入/确定性 | 路由器**读板** ⇒ 与 **E-2「零板读」**口径冲突，须监理重裁 E-2；全链重跑 + 全锚重算 |
| **(B) 具名 L-3 + 受审板维持 l5，仅重指 `lib_id`** | 承认「l5 几何（含布线）= 冻结施工输入」；重指用 **⑦ 工具 `k2_p4_lib_snapshot_v1.py`（`afa9be4bf599626b`，其既定功能即「以板为准快照 + 全板 `lib_id` 重指」）**，非手改串 | 即被 §2.1 **驳回的 (b)** 的「工具化」版本；与 E-2「构造链非修补链」目的冲突 ⇒ 须 owner 明示 |
| **(C) 判据侧复议** | `lib_electrical_level` 改消费 `ForgeOS.refmap.json`（= §2.1 驳回的 (c)） | `criteria/**` 属 owner/gate |
| **(D) 双件制 + 交叉对账** | 布线侧判据（DRC/J/阻抗/P5）挂**施工产物（l5）**；placement/库侧判据挂**构造链产物（l6）**；两件间 refs/pads/坐标**必须 0 差异**（本件已证 42+3+5 全可解释） | 交付面须具名两件；违反「单件受审板」既往口径 ⇒ 须监理裁定 |

**ENG 建议（仅建议、不代裁）**：**(D) 或 (B)**。理由：当前链的结构性事实是「布线 = 已离链修补链产物」，(A) 会让「零板读」判据失效且需重跑全部历史收敛；(B)/(D) 只把该事实**具名**（L-3）而不隐瞒，符合 owner「不得隐去限制」与 C-12。

## 4. 本件未做（停线纪律）+ 复跑

- **未落 l6**（`k2/hw/` 无任何 `.l6.` 件新增）· **未改** 受审板/pro/生成器/SPEC/真源/`criteria/**`/冻结件/库快照/模板 · **未执行** #K2-30 §2.2/§2.3/§2.6（按 §四「唯一串行」在 #1 停线后一并未启动，等裁）。
- 复跑（本件每处实测；仓库只读）：
```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
K2_OUT_PCB=/tmp/opencode/l6c/h1.kicad_pcb K2_OUT_JSON=/tmp/opencode/l6c/h1.json python3 k2/tools/k2_gen_v5.py   # 产物 d67c0f048f0d0423
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-l6-reland-v1/board_delta_v1.py \
  k2/hw/k2_v4_8L.l5.kicad_pcb /tmp/opencode/l6c/h1.kicad_pcb    # 期望 tracks (5430,0) · nets (101,102) · fps diff 50
```

## 5. 边界

**本件新增（仅证据件）**：`k2/docs/K2-P4-L6-RELAND-STOP-DELTA-PROOF-v1.md`（本件）· `k2/docs/drafts/p4-l6-reland-v1/board_delta_v1.py` **`eda6d25a18c42f98`** · `…/delta_l5_vs_generator_product.json` **`f0db69a7295ba454`**。
**未改**：受审板 / pro · 冻结四源 · SPEC 原件 · 真源 yaml · `criteria/**` · `_shared/**` · 生成器 · 库快照 · 模板 · L5 旧包 · `.omo/supervision/**`；未出 Gerber；未派 WORKER；**未新增检查齿**。
**fail-closed**：P4 未全绿不下单、不出交付 Gerber；**冲突即停机**（宪法第九条）。

—— ENG（ARCHER）· 2026-09-18 · 受审板 `dae8dc8d48ff5b81`（未动）· 产物 `d67c0f048f0d0423` · 判据锚 rev=2
