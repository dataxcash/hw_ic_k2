# K2 · 《逐条根因闭环表》· v1 · 2026-09-17

> 依据：监理 **#K2-22**（`K2-RULING-root-cause-closure-v1.md`）+ owner `OWNER-DIRECTIVE-20260917-root-cause-closure.md`
> （「问题清单中的，一个个都需要从根上解决，否则就不给过」）。**ENG 出证据，监理判**。
> 覆盖登记册 **U-01..U-10 · M-01..M-18 · F-1..F-14 · N-01..N-07 · J-1..J-10 = 59 条，无抽样**。
> 铁律落地口径（本表**逐行**执行）：① **板面修补单独成立 ⇒ 只填①，③ 写「未修，仅板面」⇒ ⑤ = 未闭**；
> ② 判据类 ④ = 已入 `criteria/` + 正/负控（**manifest 未签认前不算在岗**）；③ OUT 须具名 + 不阻塞理由 + 替代判据。
> **边界**：本表**只读取证**；未改板/库/SPEC/生成器/`criteria/`/`.omo/supervision/**`；未派 WORKER；临时仅 `/tmp/opencode`。
> 判据现状（只读复算）：冻结 `criteria/` `897e8bfde60e2cfe`·`7ce08757eff25557`，`not_countersigned: true`，`k2/pipeline.yaml` **不存在**
> ⇒ **59 条中无一条判据「在岗」**（下表 ④ 逐条注明「未在岗」）。

## 0. 汇总（先给结论）

| ⑤ | 条数 | 条目 |
|---|---|---|
| **根闭** | **0** | —（无一条同时满足「载体已修」+「防复发判据在岗」） |
| **OUT（具名）** | **4** | `U-01` · `U-02` · `M-15` · `F-11`（计划 §1.3 **OUT #5**「3D 预览模型」；替代判据见下） |
| **未闭** | **55** | 其余全部 |
| └ 其中「**载体已修**、只差判据在岗」 | 15 | `U-05` `U-06` `U-08` `M-01` `M-04` `M-08` `M-10` `M-14` `F-3` `F-4` `F-5` `F-6` `F-8` `N-02` `N-06` |
| └ 其中「**判据已实现**、待安装 + 签认」 | 10 | `J-1..J-10` |
| └ 其中「**载体未修**（结构性根因）」 | 30 | `U-03` `U-04` `U-07` `U-09` `U-10` · `M-02` `M-03` `M-05` `M-06` `M-07` `M-09` `M-11` `M-12` `M-13` `M-16` `M-17` `M-18` · `F-1` `F-2` `F-7` `F-9` `F-10` `F-12` `F-13` `F-14` · `N-01` `N-03` `N-04` `N-05` `N-07` |

**关键判读**：
1. **P4 停工的真正原因不是缺板**，而是 **55 条未闭**（其中 30 条载体结构性未修）。
2. 按 #K2-22 §一，**`F-1` `F-7` `M-09` `U-04` `U-07` 的共同根因 G-ROOT-1**（生成器 pad 取自锚板）、
   **`U-10` `M-05` `M-11` `F-1` `F-2` 的 G-ROOT-2**（生成器无 NPTH/keepout/铺铜产出）、
   **`F-14` `N-05` 的 G-ROOT-3**（真源路径硬编码 + symlink 兜底）**均未修** ⇒ 这些条目**不得判已解决**。
3. **判据侧**：59 条中 **10 条（J-1..J-10）判据已实现但未在岗**（`criteria/` manifest `not_countersigned: true` + `k2/pipeline.yaml` 缺失）
   ⇒ 即使载体已修的 15 条，也**没有任何一条会被机判抓住再现** ⇒ 按 #K2-22 §三，**P4 门不可开**。

---

## 1. A 段：owner 原始 10 条（U-01..U-10）

| ID | ① 现象（登记册原话 / 实测） | ② 根因载体（文件:行 / 件名） | ③ 根因修复件 | ④ 防复发证明（判据名 + 在岗） | ⑤ 状态 |
|---|---|---|---|---|---|
| U-01 | J9/J13 与其间芯片 U? 焊盘重叠。实测：板 616 pad 跨器件 AABB 两两重叠 **0**；现象来自 3D 注入 | `k2/tools/k2_render_3d.py:79-81`（对所有模型 `offset 0/rotate 0`；ForgeOS 排针 origin=几何中心、pad1 在 `(0,-3.81)`，官方 `PinHeader_*_Vertical` origin=pin1）+ `k2_gen_v5.py:332`（J9/J13 为 0 焊盘） | **未修，仅板面**（P4 补 16 排针 pad）；渲染工具 `74b1ced4607dbd43` 的 origin 补偿**未改**；计划 §1.3 OUT#5 具名 | 替代判据 = J-8 器件重叠（pad AABB，本增量实测 0）—— **未实现、未在岗** | **OUT（具名，计划 §1.3 #5）** |
| U-02 | J6/J12 同焊盘重叠。J13/J6/J12 实测 `x=27.94`、y 带不相交 | 同 U-01 | 同 U-01 | 同 U-01 | **OUT（具名，同上）** |
| U-03 | 2 个 MCIO 3D 封装不对、尺寸不对。实测 J3/J4 板内 pad 名集 `A1..A19/B1..B19` vs 库 `1..38`；3D 用硬编码盒 16.0×7.0×4.6（实测 pad 场 10.8×2.5） | `hw/lib/ForgeOS.pretty/MCIO_4i_SFF-1016_RASide.kicad_mod` vs 板；`k2/tools/k2_render_3d.py:38-41` | **未修**（⑦ 库侧「按板重建 + 重指 `lib_id`」待监理裁定；渲染盒未改；仅板面 = 板为权威 land） | J-7 `lib_electrical_level`（草案 `7cf8a50eb832c284`，**未安装/未在岗**） | **未闭** |
| U-04 | SlimSAS 封装与焊盘完全正交、封装也不对。实测 J2 板内 pad `(-1.175,-10.8)` 起、`1.3×0.35` 横排；库 `(-11.4,1.5)` 起、`0.35×1.0` 竖排 ⇒ 相对库转 90° + 尺寸变 | `k2/tools/k2_gen_v5.py:332/345-346`（`d["pads"] = anchor["pads"]`，pad 几何取自锚板）= **G-ROOT-1** | **未修**（G-ROOT-1 未闭；⑦ 待裁） | J-7 `lib_electrical_level`（草案，未在岗） | **未闭** |
| U-05 | 大量丝印被遮盖、内容不全。实测：`silk_over_copper`/`silk_overlap` 被设 `ignore`；打开后 22+9=31 条 | `k2/hw/k2_v4_8L.l4.kicad_pro` → `board.design_settings.rule_severities` | **载体已修**：③ 摘除 ignore 9→0（`k2/hw/k2_v4_8L.l5.kicad_pro` **`d5e0ca067a7b585e`**）+ W-7 丝印/覆盖修复（现板 silk 违规 **0**）。模板 `k2/tools/k2_jlc_template.kicad_pro` 同含 9 条 **未改**（具名 = 计划 §P6 学习环） | `rule_severity_manifest`（冻结判定器已实现）· `drc_warning_dispositions`（草案）—— **未在岗（manifest 未签认 / 无 pipeline）** | **未闭**（载体已修） |
| U-06 | MCIO→SlimSAS 三角形/直角折弯。实测原 **2051/2512 = 81.6% 非 45°**，100% 在 `PCIE_*` 网 | 布线产物（`k2/tools/p3_v57_*` 路由）+ `_shared/eda_core/pipeline/checks.py:387-400`（`CHECK_TYPES` 无 45° 项） | **载体（判据）未修**；**板面已归一**（P4，现板非 45° = **0/4722**）。判据侧 `non45_segments` 已入冻结 `criteria/manifest.k2.yaml` | `non45_segments`（冻结，已实现；负控 = l4 板 2051 ⇒ FAIL，见 `K2-P1-criteria-execution-evidence.md`）—— **未在岗（未签认）** | **未闭**（载体已修） |
| U-07 | 「J6/9/10/11/12 为何这么多 PIN」。实测 J10 不存在；J6/J9/J11/J12/J13 **各 0 焊盘**（库分别 2/4/4/2/4）⇒ 真问题是「一个 PIN 都没有」 | `k2/tools/k2_gen_v5.py:332`（pad 取自锚板）+ `SPEC.components.pin_headers.pad_diameter` **零消费** = **G-ROOT-1** | **未修**（仅板面补 16 pad；生成器锚板取 pad 逻辑未动）= G-ROOT-1 | `device_has_pads`（冻结：每封装 pad ≥1）+ `V2 pad==引脚`（计划）—— 冻结项**未在岗** | **未闭** |
| U-08 | 上边密集、下边大量空白。实测横带占用 5.3%/17.8%/0.7%；底部空带 **9.15mm**（因板框 46mm 而设计框仍 38mm） | `k2/tools/k2_gen_v5.py:47`（原 `BOARD y=[33,71]` = 38mm） | **载体已修**：`BOARD = {"x":[23,143],"y":[33,79]}`（现源 `d8d15a31061f450f`） | J-8 `density_and_clearance`（登记册 J-8 维度）**pending 未实现**；`pads_within_outline` pending ⇒ **未在岗** | **未闭**（载体已修） |
| U-09 | 左器件密集而 MCIO/RETIMER/SlimSAS 间大量空白。实测左 30/右 12；U1→J3 空 15.00mm、J4→U6 空 17.55mm | 布置解算（`k2/tools/k2_p3_place_solver_v1.py`）+ **无密度/间距判据**（登记册 M-12 口径 19–27% 复现不出） | **未修**（P4 未做再布置；密度口径未定义） | J-8 `density_and_clearance` **pending（需 P3 图纸阈值）** ⇒ 未在岗 | **未闭** |
| U-10 | 无固定孔位、无走线回避区。实测原 NPTH=PTH=0；4 个 `ESC_*` keepout 五开关全 `allowed`（空操作） | 板内 `zone` keepout 全 allowed；**生成器无固定孔/回避区产出** = **G-ROOT-2** | **未修，仅板面**（P4 补 H1–H4 NPTH=4 + PTH=16；ESC 4 区各 ≥1 非 allowed）；生成器无该产出逻辑 | `drill_count`（冻结，NPTH≥1）+ `keepout_active`（草案）—— **未在岗** | **未闭** |

---

## 2. B 段：监理 18 条观察（M-01..M-18）

| ID | ① 现象 | ② 根因载体 | ③ 根因修复件 | ④ 防复发证明 | ⑤ 状态 |
|---|---|---|---|---|---|
| M-01 | 板↔图脱节：板 42 / 原理图 103 / 网表 55；图有板无 64、板有图无 3 | `k2/hw/sch/*.kicad_sch` + `k2/hw/data/k2_sch.yaml`（三源漂移）+ `netlist_parity.py` 未接 | **载体已修**：真源归零 R1/R2（图删 A+C 类 52 件，现图内已无 `U3`/`U7`；板 55 + H1..H4） | `refdes_sets_equal`（冻结；负控 = 改名 `X99` ⇒ FAIL，见 `K2-P1-…-evidence.md`）—— **未在岗** | **未闭**（载体已修） |
| M-02 | README 称「双 DS160PR810（U7 上行/U3 下行）」，板上只有 1 颗 U6=DS320PR1601 | `k2/README.md:27,46`（`697fa103458268db`）· `k2/docs/01-architecture.md:9`（`c7793b922f0e8a5d`） | **未修**（两文件仍写 dual DS160PR810） | 「不适用」不成立：README 属交付证据层；无文档一致性判据 ⇒ 无替代判据 | **未闭** |
| M-03 | U6 = 354 ball，其中 **108 ball 无网络** | `k2/tools/k2_gen_v5.py:296-321`（`assign_nets`）+ 符号 pin_map | **未修**（真源 nc 声明 = 0；草案 `k2/docs/drafts/j9-wiring-option-a/` +nc 105 未安装） | `net_declared_realized` + `pin_map_complete` + `unconnected_zero`（草案）—— **未在岗** | **未闭** |
| M-04 | **2051/2512（81.6%）线段非 45°** | 同 U-06 | 同 U-06（板面已归一 0/4722；判据未在岗） | `non45_segments`（冻结）—— **未在岗** | **未闭**（载体已修） |
| M-05 | 9 个铺铜区 `filled_polygon=0`；F.Cu/B.Cu 无地平面；4 个 `ESC_*` 五 flags 全 allowed。更重：交付 8 铜层 Gerber `G36=0` | 板内 `zone` 块（未填）+ **无「填充/平面存在」前置判据** + 生成器无铺铜产出 = **G-ROOT-2** | **未修，仅板面**（P4 填充 10/10；出面前置实测 `G36>0`，`K2-P4-EXIT-PREREQ-MEASUREMENT-v1.md` `26f3193e1d0f2771`） | `zone_filled`（冻结；负控 = l4 板 0/9 ⇒ FAIL）+ V3 `ref_plane_continuity` **pending** ⇒ 未在岗 | **未闭** |
| M-06 | 未连接：不补铜 364 / 补铜 178（186 条仅靠补铜即消） | 同 M-05（补铜即消 ⇒ 反证平面缺失） | **未修，仅板面**（P4 现板 `unconnected = 0`） | `unconnected_zero`（草案）—— 未在岗 | **未闭** |
| M-07 | DFM gate 把 `unconnected:178` 写进 JSON 却不入 `fails`；42 违规全 warning；同包 `verdict` 字面 `FAIL` | `…/L5/jlc_package/06_rulings/m13_v57_co146_jlc_dfm_gate.json`；`…/L5/DELIVERY/README.md`（结论在最后一层被重写 = 审计机制③） | **未修**（gate 实现属监理/gate 属主；草案 v2 的 `drc_errors`/`unconnected_zero` **未安装**） | `drc_errors` + `drc_warning_dispositions` + `unconnected_zero`（草案，7 案正负控已做）—— **未在岗** | **未闭** |
| M-08 | `.kicad_pro` 将 `silk_over_copper`、`silk_overlap` 设 `ignore`（另 7 项 ignore，共 9） | 同 U-05（`…l4.kicad_pro: rule_severities`） | **载体已修**（l5 pro `d5e0ca06…` ignore 9→0）；**共享模板 `k2/tools/k2_jlc_template.kicad_pro` 仍含 9 条 = 未修**（具名登记 = 计划 §1.2#7 / §P6，跨板复用项） | `rule_severity_manifest`（冻结）—— 未在岗 | **未闭**（载体已修；模板余项具名） |
| M-09 | 封装 ≠ 库：J2 旋转+改尺寸；J3/J4 pad 名集不同；E2 pad 5–8 镜像 | `k2/tools/k2_gen_v5.py:322-360`（pad 几何取自锚板）= **G-ROOT-1** | **未修**（⑦ 库侧「按板重建 + 重指 `lib_id`」待监理裁；生成器锚板逻辑未动） | `lib_electrical_level`（草案，消费 W-8 审计；实测 31+2 ⇒ FAIL 如实反映）—— 未在岗 | **未闭** |
| M-10 | 全项目无 `fp-lib-table` ⇒ `ForgeOS` 未注册（12 条 `lib_footprint_issues`） | 仓库缺文件（审计 [E14]） | **载体已修**：`k2/hw/fp-lib-table` **`d731638859be9a08`**（F-12 收口） | `fp_lib_table_present`（草案，正控已做）—— 未在岗 | **未闭**（载体已修） |
| M-11 | 全板 NPTH=0、PTH=0 ⇒ 无固定孔 | 与 U-07 **同源**（排针丢焊盘 ⇒ 全板 0 孔）= **G-ROOT-1 + G-ROOT-2** | **未修，仅板面**（现 NPTH=4 / PTH=16） | `drill_count`（冻结，`npth >= 1`）—— 未在岗 | **未闭** |
| M-12 | 布局：左 30/右 12；三横带占用 19–27%（ENG 复算 5.3%/17.8%/0.7% ⇒ 口径不明） | 无密度判据；口径未定义（`hw/…l4` 实测） | **未修**（口径待监理定义 = 草案 `density_and_clearance` pending） | J-8 `density_and_clearance` **pending（需 P3 阈值）** ⇒ 未在岗 | **未闭** |
| M-13 | k2 无 `pipeline.yaml` ⇒ `checks.py` 门禁引擎对 K2 **从未运行** | `k2/pipeline.yaml`（缺） | **未修**（草案 `pipeline.yaml.draft` `3d69d40208bc630e` 已备，**安装属 gate 属主**）；本会话复算：文件仍不存在 | `pipeline_present`（冻结 + 草案 scope=k2）—— 未在岗 | **未闭** |
| M-14 | `project.yaml` 的 `board_path: k2_v4.kicad_pcb` 文件不存在 | `k2/pm_gate/project.yaml` | **载体已修**：R4 建 `k2/k2_v4.kicad_pcb → hw/k2_v4_8L.kicad_pcb`（另 `spec_name` 已 rev-47）；`project.yaml` **`9cee872bd6fbdc67`** | 无「路径可解析」判据 ⇒ 无替代判据（`fp_lib_table_present` 只覆盖库表） | **未闭**（载体已修） |
| M-15 | 渲染：排针套官方 `PinHeader_*.step`（origin=1 脚）未补偿 → 偏 3.81mm | `k2/tools/k2_render_3d.py:79-81`（`74b1ced4607dbd43`；本会话复算：`model_block()` 仍恒 `offset/rotate = 0`） | **未修**（计划 §1.3 **OUT #5** 具名：3D 预览属证据层，不阻塞可制造性/可用性） | 「不适用」+ 替代判据 = J-8 器件重叠（pad AABB，实测 0，pending 实现） | **OUT（具名）** |
| M-16 | U1 = LQFP48，库 49+9 pad，板上仅 33 pad（1..33），缺 34..49 | `k2/tools/k2_gen_v5.py:322-360` | **未修，仅板面**：现板 `U1` pad = **58**（本会话 pcbnew 实测，lib `MCU_STM32G0_LQFP48`） | V2（pad 数 == 引脚数）；冻结 `device_has_pads` 仅判 ≥1 ⇒ 覆盖不足；未在岗 | **未闭** |
| M-17 | `NO_CONNECT` 建成真实网络 → 约 26 对假未连接（DRC 中 `NO_CONNECT` 52 次） | `k2/tools/k2_gen_v5.py:296-321`（`assign_nets` 未落 no-net）= **F-10** | **未修**（真源 `nc` = 0；草案 errata-2 +nc 105 未安装） | `unconnected_zero` + `net_declared_realized`（草案/冻结）—— 未在岗 | **未闭** |
| M-18 | 无 45°/板↔原理图/铺铜/丝印/位置 的**任何机判** | `_shared/eda_core/pipeline/checks.py:387-400`（`CHECK_TYPES` 12 项无此项） | **未修**（判据草案 v2 已覆盖 45°/铺铜/丝印/连通/库表/keepout；**未安装**；位置类仍 pending） | 判据本体即防复发 = `non45_segments`/`zone_filled`/`refdes_sets_equal`/`drc_*`（冻结 + 草案）—— 未在岗 | **未闭** |

---

## 3. F 段：13+1 项（F-1..F-14，计划 §附 追溯表）

| ID | ① 现象 | ② 根因载体 | ③ 根因修复件 | ④ 防复发证明 | ⑤ 状态 |
|---|---|---|---|---|---|
| F-1 | 5 个排针 0 焊盘 / **全板 0 孔**、无 12V 输入 | `k2/tools/k2_gen_v5.py:332`（pad 取自锚板，锚板自身 0 焊盘 ⇒ 循环依赖）= **G-ROOT-1** + 生成器**无 NPTH/PTH 产出** = **G-ROOT-2** | **未修，仅板面**（P4 补 16 排针 pad + NPTH=4/PTH=16） | `device_has_pads` + `drill_count`（冻结）—— 未在岗 | **未闭** |
| F-2 | 13 区未填充 / 交付 8 铜层 Gerber `G36=0` | `hw/…l4.kicad_pcb`（zone fills）+ **无填充/平面前置判据** + 生成器无铺铜产出（G-ROOT-2） | **未修，仅板面**（P4 填充 10/10；出面前置 `G36>0` 实测 = `K2-P4-EXIT-PREREQ-MEASUREMENT-v1.md` `26f3193e1d0f2771`） | `zone_filled`（冻结）+ V3 `ref_plane_continuity`（pending）—— 未在岗 | **未闭** |
| F-3 | SPEC 6L vs 板 8L；In5 承载 2008/2512 段而无语义 | `L2/frozen/L2_STRUCTURE_v2.0.md`；`L3/SPEC_k2_v4.json`（6L canonical） | **载体已修**：版本 bump rev-20…**rev-47**（`k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json` `9ba09cbc148d6836`）+ `project.yaml: spec_name` 重指向；实测板走线层 ⊆ SPEC 信号层 | Z3 判据**未入 `criteria/`**（冻结清单无 layer 判据）⇒ 无在岗判据 | **未闭**（载体已修） |
| F-4 | 2051 条非 45°（100% 在 PCIe 网） | 同 U-06 | 同 U-06（板面 0/4722） | `non45_segments`（冻结，负控 l4 ⇒ FAIL）—— 未在岗 | **未闭**（载体已修） |
| F-5 | 板 42 / 图 103 / 网表 55 三源不齐 | `hw/sch/*.kicad_sch` + `hw/data/k2_sch.yaml`；`netlist_parity.py` 未接 | **载体已修**：真源归零 R1/R2（图删 52 陈旧件） | `refdes_sets_equal`（冻结，负控 `X99`）—— 未在岗 | **未闭**（载体已修） |
| F-6 | 9 条 DRC 规则被 `ignore`（含 via_dangling 17 条静默） | `hw/…l4.kicad_pro: rule_severities` | **载体已修**（l5 pro ignore 9→0）+ W-7 `via_dangling` 清零；模板同源 9 条**未修**（具名 P6） | `rule_severity_manifest`（冻结）—— 未在岗 | **未闭**（载体已修） |
| F-7 | U1 缺 25 pad；U6 108 球无网 | `k2_gen_v5.py:322-360`（pad 来源）+ `:296-321`（`assign_nets`） | **未修，仅板面**（U1 现 58 pad）；生成器两处逻辑未动 | V2（pad==引脚）/ `pin_map_complete` —— 未在岗 | **未闭** |
| F-8 | 46mm 板框 vs 38mm 设计框 ⇒ 底部 9.15mm 空 | `k2_gen_v5.py:47`（`BOARD`） | **载体已修**：`BOARD = {"x":[23,143],"y":[33,79]}` | 无板框判据（`pads_within_outline` pending）⇒ 不适用未成立 | **未闭**（载体已修） |
| F-9 | 走廊口径两套未对账（0.25 / 0.41mm 差） | `k2/pm_gate/artifacts/k2_v4/L2/frozen/L2_STRUCTURE_v2.0.md`（走廊表）vs 板实测 | **未修**（P3 图纸采用板侧实测口径；L2 冻结表未回改 —— 改冻结件须 owner 批）；P4 仅对齐 ESC keepout 口径（`K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md`） | `keepout_active`（草案）—— 未在岗 | **未闭** |
| F-10 | `NO_CONNECT` 建成真实网 ⇒ 26 对假未连接 | 生成器 `assign_nets` 未落 no-net = **G-ROOT-1 同族（真源声明侧）** | **未修**（草案 errata-2「+nc 105 −nets.PWR_5V_KEY」未安装） | `unconnected_zero` + `net_declared_realized`（草案/冻结）—— 未在岗 | **未闭** |
| F-11 | 3D 模型 origin 未补偿 ⇒ 3.81mm 偏移 | `k2/tools/k2_render_3d.py:79-81` | **未修**（计划 §1.3 **OUT #5**：3D 预览不阻塞可制造性，排在 P4 之后） | 「不适用」+ 替代判据 = J-8 器件重叠（pending） | **OUT（具名）** |
| F-12 | 无 `fp-lib-table`；7 个未标注 refdes | 仓库缺文件（已修）+ `hw/sch/*`（未修） | **部分修**：`k2/hw/fp-lib-table` `d731638859be9a08`（F-12 库表侧闭）；**7 个未标注 refdes 未修**（见 N-07） | `fp_lib_table_present`（草案，库表侧）—— 未在岗 | **未闭** |
| F-13 | k2 无 `pipeline.yaml`；两个核对器零调用 | `k2/pipeline.yaml`（缺）；`_shared/eda_core/{netlist_parity,board_spec_consistency}.py` | **未修**（草案 `pipeline.yaml.draft` 已备；安装属 gate 属主） | `pipeline_present`（冻结 + 草案 scope=k2）—— 未在岗 | **未闭** |
| F-14 | 生成器输入缺失 ⇒ 不可复跑 | `k2/tools/k2_gen_v5.py:39/44-47`（`YAML_PATH` 硬编码 + `boards/k2_sch.yaml` symlink 兜底；`PCB_REF_PATH` 仍指锚板）= **G-ROOT-3** | **未修**（R4 以 symlink 消 `FileNotFoundError`，属**兜底绕过**《宪法》第九条禁；E4 两次 sha 相同**未达成**） | E4 判据（产���两次 sha 相同 + refdes==42 + 板框 46mm）**未实现/未在岗** | **未闭** |

---

## 4. N 段：7 项（N-01..N-07，审计新增现象）

| ID | ① 现象 | ② 根因载体 | ③ 根因修复件 | ④ 防复发证明 | ⑤ 状态 |
|---|---|---|---|---|---|
| N-01 | 交付 Gerber **无任何平面铜**：8 铜层 `G36=0` | `…/L5/jlc_package/01_gerber_rs274x/*.gbr`；出图前无「铺铜已填充」前置 | **未修**（P4 未关门，未出新 Gerber；前置已实测 `G36>0`） | `zone_filled`（冻结）+ V3 `ref_plane_continuity`（pending）+ 出面前置（实测件）—— 未在岗 | **未闭** |
| N-02 | canonical SPEC 仍 6L 且 `layer_plan` 无 In5 语义，板 80% 走线在 In5 | `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`（6L `0bd52ed4` 历史件）+ `project.yaml: spec_name` | **载体已修**：指针经 rev-20…**rev-47**（8L：`F/In1..In6/B`）；6L 历史件按「版本 bump 新文件 / 原件不动」保留 | Z3 判据**未入 `criteria/`** ⇒ 无在岗判据 | **未闭**（载体已修） |
| N-03 | `.kicad_pro sheets: []` ⇒ PCB 未挂原理图页；`schematic_parity: []`（板↔图从未跑） | `k2/hw/k2_v4_8L.l5.kicad_pro`（本会话复算：`"sheets": []` 仍在） | **未修**（l5 pro 仍 `sheets: []`） | 无判据（`refdes_sets_equal` 只比 refdes 集，不判 sheets 接线） | **未闭** |
| N-04 | `netlist_parity.py`（自带 `--fail-on-pin-mismatch`）与 `board_spec_consistency.py` 已建、**K2 零调用** | `_shared/eda_core/{netlist_parity,board_spec_consistency}.py`（已建）+ `k2/pipeline.yaml`（缺） | **未修**（接线 = gate 安装项） | `pipeline_present` + 必选三联 `sch_structural/netlist_connect/bom_consistent`（`required.py` meta-gate）—— 未在岗 | **未闭** |
| N-05 | 生成器不可复跑：冻结输入 `k2_v4.kicad_pcb`、`boards/k2_sch.yaml` 当时不存在 | `k2/tools/k2_gen_v5.py:39/44-47` = **G-ROOT-3** | **部分修**：R4 建两个 symlink（消 I1/I3 `FileNotFoundError`）⇒ 前进到下一阻断；**E4 ≠ 归零**（另三项生成器根因：板框已修 / SPEC 路径已修 / refdes 集已修，余 anchor pad + 锚板输入） | E4 判据（`K2_OUT_PCB` 两次 sha 相同）**未实现/未在岗** | **未闭** |
| N-06 | 打开被关的 9 条规则后 DRC **42→131**，其中 `via_dangling` **17** 条被静默 | `hw/…l4.kicad_pro: rule_severities` | **载体已修**：ignore 9→0（l5 pro `d5e0ca06…`）+ W-7 `via_dangling` **12→0** + `tncv` 30→0 | `rule_severity_manifest` + `drc_errors` + `drc_warning_dispositions`（冻结/草案）—— 未在岗 | **未闭**（载体已修） |
| N-07 | 原理图仍有 **7 个未标注 refdes**（`C?/D?/E?/J?/L?/R?/U?`） | `k2/hw/sch/*.kicad_sch`（本会话复算：`connectors` 2 · `mcu_sideband` 3 · `power_12v…` 1 · 另 1） | **未修**（7 个 `?` 仍在） | 无判据（`refdes_sets_equal` 不抓 `?`；ERC/结构检查未接入） | **未闭** |

---

## 5. J 段：出厂判据 10 条（J-1..J-10）

> ④ 口径（#K2-22 §二）：须「已入 `criteria/` 且经正/负控」；**manifest `not_countersigned: true` ⇒ 一律未在岗**。
> 正/负控出处：`k2/docs/K2-P1-criteria-execution-evidence.md`（冻结判定器 4 案）+ `K2-P4-CRITERIA-DRAFT-AND-MANIFEST-V2.md` §3（草案 7 案 + J-7b 4 案）。

| ID | ① 现象（维度） | ② 根因载体 | ③ 根因修复件 | ④ 防复发证明（判据 + 正负控） | ⑤ 状态 |
|---|---|---|---|---|---|
| J-1 | DRC error = 0（warning 逐项处置） | 判据缺席（`checks.py` 无 DRC 项）+ 原板 42 warning 全放行 | 冻结判定器 `criteria/adjudicate.py` `897e8bfd…`（规则强度项）+ 草案 `drc_errors`/`drc_warning_dispositions`（`7cf8a50e…`）；现板 **error 0** | 草案 7 案含 NEG-drc-errors（error=40 ⇒ FAIL）、NEG-warn-empty ⇒ 机制可用；**manifest 未签认 ⇒ 未在岗** | **未闭** |
| J-2 | 连通 = 0（补铜后） | 原板 178 未连（平面缺失）+ 无连通判据 | 板侧 P4 现 **unconnected = 0**；草案 `unconnected_zero`（与 J-1 共用一次 DRC） | 草案正负控（复用 NEG 案）⇒ 未在岗 | **未闭** |
| J-3 | 铺铜全填充 | 原板 0/9；`zone_filled` 分母口径错（含 keepout） | 板侧 P4 填充 **10/10**；草案 ② 修分母 = 有网非 keepout 铜区 | 冻结 `zone_filled` + NEG-zone-l4（0/9 ⇒ FAIL）⇒ 未在岗 | **未闭** |
| J-4 | 丝印检查全开且 0 违规 | 9 条 ignore（含 2 条丝印） | pro 载体已修 + W-7 丝印修复（现板丝印违规 0）；**无专用丝印判据**（靠 DRC 全开 + `drc_*`） | `drc_errors` + `drc_warning_dispositions`（草案）⇒ 未在岗 | **未闭** |
| J-5 | 非 45° 段 = 0 | `checks.py` 无 45° 项 | `non45_segments` 已入冻结 manifest；现板 **0/4722** | 冻结判定器正控（0/4721 PASS）+ 负控 l4（2051 ⇒ FAIL）⇒ 未在岗 | **未闭** |
| J-6 | 板↔原理图一致（refdes/封装/pad 集） | 三源漂移（M-01/F-5） | `refdes_sets_equal` 冻结版未排除 `H*` ⇒ 现 FAIL；草案 ⑤ 排除 `H\d+` ⇒ 55/55 PASS | 冻结 + 草案 NEG-refdes-X99 ⇒ 未在岗 | **未闭** |
| J-7 | 封装 = 库（mismatch/issues = 0 + `fp-lib-table` 存在） | G-ROOT-1（pad 取自锚板）+ 无库表 | `fp_lib_table_present` **已实现**（库表 `d7316388…`）；`lib_electrical_level` **已实现**（消费 W-8 审计）⇒ **实测 FAIL**（电气级差异 31 + 仅 pad 名 2）= **⑦ 待裁** | 草案 4 案（real→FAIL / green→PASS / stale→FAIL / none→FAIL）⇒ 未在岗 | **未闭** |
| J-8 | 器件位置合理性（重叠/出框/密度/间距/固定孔/回避区） | 无位置类判据实现 | 已实现：`keepout_active`（草案）；**pending**：`pads_within_outline`、`density_and_clearance`（需 P3 阈值） | `keepout_active` 在草案内；余 2 项 pending ⇒ 未在岗 | **未闭** |
| J-9 | 门禁接入（`pipeline.yaml` 存在且 ④ 段判据全机判） | `k2/pipeline.yaml` 缺（M-13/F-13） | 草案 `pipeline.yaml.draft` `3d69d40208bc630e`（符合 eda_core schema，含必选三联）⇒ **安装属 gate 属主** | `pipeline_present`（草案 scope=k2，正控：域内 0 缺 / 负控：k2 域缺 ⇒ FAIL）⇒ 未在岗 | **未闭** |
| J-10 | 完工定义可复现（命令 + 阈值 + 原始输出） | 判据/证据散落 `/tmp`（易失） | 草案 `run_controls.py`（7 案复跑）+ 本表逐项 sha；**未安装** | 复跑脚本本身即证明；未在岗 | **未闭** |

---

## 6. G-ROOT-1 / 2 / 3：修复方案（#K2-22 §五-2）

> 口径：三项**均属生成器源码**（`k2/tools/k2_gen_v5.py`，现 sha `d8d15a31061f450f`）。**本件只给方案，未动源码**
> （改生成器须监理放行：`K2-P2-Z4-generator-change-plan-v1.md` §3 已于 S1 处停机；G1–G3 已放行并落地）。
> **禁新增检查齿（owner ②）**：三项方案均复用**已裁维度**（V2 见 F-1/F-7、J-7 见 M-09、E4/J-10 见 F-14/N-05），不新造判据。

### G-ROOT-1 · 生成器 pad 几何取自锚板（循环依赖）

| 项 | 内容 |
|---|---|
| 载体 | `k2_gen_v5.py:341-346`（`anchor = ref_anchors_cache.get(ref)` → `d["pads"] = anchor["pads"]`）；锚板 = `PCB_REF_PATH = ROOT/"k2_v4.kicad_pcb"`（`:41`）→ symlink → `hw/k2_v4_8L.kicad_pcb`（设计源板 `fb07d25ac426ff84`，其 5 排针 0 焊盘、`U1` 33 pad） |
| 危害 | **循环依赖**：产物板 → 锚板 → 产物板；0 焊盘被永久继承（F-1/F-7/M-09/U-04/U-07） |
| 方案（G9，建议） | ① **删锚板路径依赖**：`PCB_REF_PATH` 不再作为 pad 来源（坐标锚点若仍需，只允许取 `at/rot`，**禁取 `pads`**）；② pad 几何来源改为 **SPEC `components.*`（`pad_diameter`/`pin_map`）+ 库 `.kicad_mod`**（经 `fp-lib-table` 解析，`d731638859be9a08` 已建）；③ 把现有 `else:` 分支的 `raise ValueError("[GEOM] 缺少 …")` 扩为**所有 ref 一律 fail-closed**（禁静默回退）；④ 头注加版本块 + 交件留痕 |
| 收敛判据（复用已裁维度，不新增齿） | **V2**（每器件 pad 数 == 符号引脚数，计划 §1.2#3 / J-7）；**E4**（两次 sha 相同，见 G-ROOT-3） |
| 停机点 | 未见阻断项；**须监理一句话放行**（动生成器源码） |

### G-ROOT-2 · 生成器无 NPTH / keepout / 铺铜产出

| 项 | 内容 |
|---|---|
| 载体 | `k2_gen_v5.py` 全文仅 2 处 `thru_hole`（`:413`/`:415`，均为 pad 渲染）；**无固定孔（NPTH）/回避区（keepout）/铺铜（zone）生成段**；grep `NPTH`/`keepout` = 0 命中 |
| 危害 | U-10 / M-05 / M-11 / F-1 / F-2 的「全板 0 孔 + 无平面 + 回避区空操作」 |
| 方案（G10，建议） | ① 从 L3 图纸取**固定孔** `H1–H4`（P3 图纸 `01_board_frame_and_holes.svg`；孔位属 L1 机械接口，**只读消费、不得擅移**）生成 NPTH pad；② 从 `ESC_*` 4 区定义生成 **keepout zone**（至少 1 个开关 `not_allowed`，语义 = 逃逸走廊不得被铺铜填死）；③ 生成**有网铜区**（GND `In1/In3/In6`、电源 `In4` 分区），并在出图前**强制 `ZONE_FILLER` 填充**；④ 前置机检（复用 J-3/J-8）：`npth >= 4`（`drill_count`）、`zone_filled` 全填、`ESC_*` 各 ≥1 非 allowed（`keepout_active`） |
| 收敛判据 | 复用 **J-3 `zone_filled`** + **J-8 `keepout_active`** + 冻结 **`drill_count`**（`npth_min` 由 1 提升到 4 的修正在草案 v2 已做） |
| 停机点 | 需 L1 机械接口（H1–H4）与孔位**逐座标确认**（P3 图纸已出、H3 曾与排针列冲突已裁）⇒ 若图纸孔位改动则**再停一次** |

### G-ROOT-3 · 真源路径硬编码 + symlink 兜底（F-14 / N-05）

| 项 | 内容 |
|---|---|
| 载体 | `k2_gen_v5.py:39` `YAML_PATH = ROOT/"boards/k2_sch.yaml"`（硬编码）；靠 `k2/boards/k2_sch.yaml → ../hw/data/k2_sch.yaml` symlink 解析（2026-09-16 R4 建）。**对照**：`SPEC_PATH`（`:42`）已改 `pm_gate.config.spec_name()` 配置驱动 ✓ |
| 危害 | 换机/换目录即复现 `FileNotFoundError`（N-05）；**兜底绕过**（《宪法》第九条禁） |
| 方案（G11，建议） | ① **配置驱动**：在 `k2/pm_gate/config.py` 增 `nets_yaml()`（或复用 project.yaml 的 `nets_yaml` 键）解析真源网表路径；生成器改为 `YAML_PATH = _PMCFG.nets_yaml()`；② 删 `k2/boards/k2_sch.yaml` symlink（或保留为**具名兼容件**并登记理由 + 删除计划，**不得静默**）；③ 同时删 `k2/k2_v4.kicad_pcb` symlink（随 G9 的锚板去依赖）；④ E4 判据落地：`K2_OUT_PCB` 连跑两次 **sha 相同** + 产物 refdes 集 == 真源 + 板框 46mm `[33,79]` |
| 收敛判据 | 复用 **J-10 完工可复现**（命令 + 阈值 + 原始输出两跑 sha 相同）；E4 = J-10 的 K2 实例 |
| 停机点 | 若 `project.yaml` 无 `nets_yaml` 键 ⇒ 需监理定「配置键名/归属」，一句话即可 |

---

## 7. 闭环路径（ENG 侧待办，按 #K2-22 §三 优先序）

1. **⑥ L2 增量**（在办）：候选板 `b2cfb087839afd73` 已出，**待监理放行落板**（见 inc37 §1）。
2. **本表（证据件）** ⇒ 监理判。
3. **G-ROOT-1/2/3**：§6 三项方案**须监理放行**改生成器源码（G9/G10/G11）+ 逐项 E4/V2/J-3/J-8 复算。
4. **其余 27 条载体未修**：`U-03/U-04/U-07`（随 ⑦ 库侧裁定 + G9）· `U-09/M-12/J-8`（密度判据实现）· `M-02/N-07`（README/原理图未标注 refdes 清理，纯文本/符号编辑）·
   `M-03/M-06/M-17/F-10`（errata-2 ncf 声明安装）· `M-07/M-13/F-13/N-04/J-9`（`pipeline.yaml` + 判据安装，**gate 属主**）·
   `N-03`（pro `sheets` 接线）· `N-01`（P4 关门后出 Gerber）。
5. **判据在岗**：安装 `criteria/` 两份新版（②④⑤/J-7b/J-8/V3）+ `k2/pipeline.yaml`，监理登记 sha + 锚 `rev=2` + **manifest 签认**
   ⇒ 15 条「载体已修」方具 `根闭` 资格。
6. **红线不变**：`criteria/` 只读；禁派 WORKER；临时仅 `/tmp/opencode`；禁写 `.omo/supervision/**`；不放松 DRC 下限；
   不得以「接近 0」宣称归零；冲突即停机。**fail-closed：P4 未全绿（本表全闭）不下单、不出交付 Gerber。**

## 8. 复现（本表每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# 载体现状（G-ROOT-1/2/3）
sed -n '335,360p' k2/tools/k2_gen_v5.py        # 锚板取 pad
grep -n "thru_hole\|NPTH\|keepout" k2/tools/k2_gen_v5.py
sed -n '39,48p'  k2/tools/k2_gen_v5.py        # YAML_PATH / SPEC_PATH / BOARD / PCB_REF_PATH
ls -l k2/boards/k2_sch.yaml k2/k2_v4.kicad_pcb  # 两个 symlink（兜底）
# 载体已修 / 未修抽查
sha256sum k2/hw/k2_v4_8L.l5.kicad_pro k2/hw/fp-lib-table k2/pm_gate/project.yaml   # d5e0ca06… / d7316388… / 9cee872b…
grep -c '"?"' k2/hw/sch/*.kicad_sch 2>/dev/null | grep -v ':0'                    # N-07：7 个未标注 refdes
grep -n "DS160PR810" k2/README.md k2/docs/01-architecture.md                      # M-02：仍未修
ls k2/pipeline.yaml                                                               # M-13/F-13：不存在
```
基准板/pro（唯一受审对）：`k2/hw/k2_v4_8L.l5.kicad_pcb` **`6ff49da5678c2108`** · pro **`d5e0ca067a7b585e`**
（⑥ 候选板 `b2cfb087839afd73` 未落仓库，落板归监理）。冻结件 `d4e81f647be7f980` / `fb07d25ac426ff84` / 真源 yaml / SPEC rev-19 原件 /
`criteria/` 两份 `897e8bfde60e2cfe`·`7ce08757eff25557` **未动**。

—— ENG（ARCHER）· 2026-09-17 · 覆盖登记册 **59/59 条**，无抽样

---

## 9. v1.1 增量更新（2026-09-17，监理自动续推后；本件 §0/§1..§8 为 v1 快照，不改写）

| 项 | 变化 | 依据（件 + sha） |
|---|---|---|
| `M-02` | ③ 由「未修」→「**载体已修**」：`k2/README.md` `dc28708ba34fddf2` · `k2/docs/01-architecture.md` `e7a478b5420dc161` · `k2/docs/01-architecture.zh-CN.md` `6182d4a040d1cfc2`（三文件 `DS160PR810`/`U3`/`U7` 命中 = 0） | `K2-P4-J8-V3-MEASUREMENT-AND-M02-DOC-FIX-v1.md` `3955d1af993febbe` |
| `J-8`（出框） | ④ 由「pending 未实现」→「**已实现 + 正负控命中**」：`measure_pads_within_outline.py` `1b177638cde3cd55`（正控 l5 = 0；负控合成板 = 2、rc=1，AABB 与真框双口径同命中）—— **仍待安装 + 签认 ⇒ 未在岗** | 同上 |
| V3（`ref_plane_continuity`） | 由「设计」→「**测量已实现 + 正负控命中**」：`measure_ref_plane_continuity.py` `7a3cc545c1447b04`（正控 l5 名义 3653/3653；负控冻结 l4 = 0/2327、rc=1）—— **待安装 + 签认，且阈值口径待监理定** | 同上 |
| `J-8`（密度/间距） | 仍 **pending**（`density_and_clearance` 需 P3 图纸阈值 = 监理/owner 输入） | — |

**计数更新**：`根闭 0` · `OUT（具名）4` · `未闭 55` 不变；其中「载体已修」**15 → 16**（+`M-02`）、「载体未修」**30 → 29**。
**P4 门**：仍不可开（`criteria/` 未签认 + `k2/pipeline.yaml` 缺失 ⇒ 无判据在岗；G-ROOT-1/2/3 未修待放行）。

## 10. v1.2 增量更新（2026-09-17 夜；判据草案 v3 集成）

| 项 | 变化 | 依据（件 + sha） |
|---|---|---|
| `J-8`（出框）④ | 由「已实现 + 正负控命中」→ **「已入判定器草案 v3 并可安装（`enabled:true`）」**：`adjudicate.draft-v3.py` `b77eacb11a261925` + `manifest.k2.v3.yaml` `4e3a629c22f85607`；A 案整判 15P/2F（FAIL 集未变） | `K2-P4-CRITERIA-V3-INTEGRATION-EVIDENCE-v1.md` `ef090eb0ca353d44` |
| V3（`ref_plane_continuity`）④ | 由「测量已实现」→ **「机制已入草案 v3（消费 `v3_plane_json`）+ 控制件六案命中」**；安装仍 `enabled:false`（**阈值口径待监理**） | 同上（`…/manifest.k2.control-v3.yaml` `22bf55ac605b9a5d`） |
| `criteria/` 在岗 | **仍为 0 条**（`criteria/` 未动；v2/v3 均为草案，`not_countersigned: true`，`k2/pipeline.yaml` 缺失） | — |

**计数不变**：`根闭 0` · `OUT（具名）4` · `未闭 55`（载体已修 16 / 载体未修 29）。
**P4 门**：不可开；开门的 ENG 侧前置已就绪（① 判据 v3 可安装；② ⑥ 候选板 `b2cfb087839afd73` 待落板；③ G-ROOT-1/2/3 待放行）。

## 11. v1.3 增量更新（2026-09-17 夜；J-8 密度/间距机制落地）

| 项 | 变化 | 依据（件 + sha） |
|---|---|---|
| `J-8`（密度/间距）④ | 由「仍 pending（需 P3 阈值）」→ **「机制已实现 + 正负控七案全命中」**：`adjudicate.draft-v4.py` `1cda68521d0e56be`（v3 严格超集，diff 3 hunk 全新增）+ 安装件 `manifest.k2.v4.yaml` `004f7ac2666da437`（仍 `enabled:false`，`consume`/阈值键已定）+ 测量件 `measure_density_and_clearance.py` `dccaaa476c807def` · `measure_min_clearance_drc.py` `4386efde7451bf8e` + 控制件 `manifest.k2.control-v4.yaml` `2531d4c616d855e9` | `K2-P4-J8-DENSITY-CLEARANCE-MECHANISM-EVIDENCE-v1.md` `cbbf5df47f0c86da` |
| `J-8` 三项 | **`keepout_active` · `pads_within_outline` · `density_and_clearance` 机制全部齐备**；仅差 ① `criteria/` 安装 + manifest 签认 ② 密度/间距**应然阈值**（`cell_mm`/`cell_origin`/`max_fp_per_cell`/`min_copper_clearance_mm` …）归监理 | 同上 + §10 |
| S-6a（M-12 口径） | ENG 交**两个可复算口径**：10mm 格峰值（`absolute_zero` **5** = 登记提案；`frame_origin` 7）· 三横带占用比明确定义版 **4.78/7.59/2.19%**；**M-12「19–27%」仍复现不出** ⇒ 待监理择一 + 给阈 | 同上 §2.1/§2.2 |
| `criteria/` 在岗 | **仍为 0 条**（`criteria/` 未动：`897e8bfde60e2cfe` · `7ce08757eff25557`；v2/v3/v4 均草案，`not_countersigned: true`，`k2/pipeline.yaml` 缺失） | — |

**计数不变**：`根闭 0` · `OUT（具名）4` · `未闭 55`（载体已修 16 / 载体未修 29）。
**P4 门**：仍不可开（owner #14 ③ fail-closed 不变）；ENG 侧判据前置再增一档：① v3 可安装 ② **v4 可安装** ③ ⑥ 候选板 `b2cfb087839afd73` 待落板 ④ G-ROOT-1/2/3 待放行。

---

## 12. v1.4 增量更新（2026-09-18，inc39–44；**载体现状实测核验 + 三处修正**；§0/§1..§11 为历史快照，不改写）

> 触发：监理 #K2-22 §三把本表「全闭」列为 **P4 关门追加条件**，而 §1..§11 的载体现状是 **9-17 夜**快照。
> 本节的 ②③ 列**逐条以只读实测复核**；判定仍归监理。仪器：`k2/tools/k2_refdes_annotation_probe_v1.py`
> `1bd3f4a9d47ff0d4`（refdes 标注）· `AppDir/bin/kicad-cli`（netlist/DRC）· `python3 -c json`（pro 键值）。

### 12.1 载体现状核验（7 处，实测 vs 表内记载）

| 行 | 表内记载（§1..§11） | **本轮只读实测** | 结论 |
|---|---|---|---|
| `M-02` | 「**未修**（两文件仍写 dual DS160PR810）」 | `k2/README.md` / `k2/docs/01-architecture.md` 中 **`DS160PR810`/`dual`/`双颗`/`U3`/`U7` 出现 0 次**（`DS320PR1601` 4+1 次）；全仓 `DS160PR810` 仅存于**历史 SPEC rev-7/11/12**（版本化历史，原件按机制不改） | **表内陈旧**：载体**已修** ⇒ 归入「载体已修待判据」 |
| `N-07` | 「原理图仍有 **7 个未标注 refdes**（`C?/D?/E?/J?/L?/R?/U?`）」 | 排除 `(lib_symbols …)` 子树后，**实例未标注 = 0**（55 实例全已标注）；那 31 个 `?` 全是 **`lib_symbols` 定义占位符**（KiCad 正常内容）；「7」= **7 个不同前缀**；netlist（KiCad 自身口径）**`?` = 0 / 705 ref 条目** | **现象不成立 = 伪缺陷** ⇒ 建议监理判 **OUT（具名：前提实测不成立）** |
| `F-12` | 「**部分修**：库表侧闭；7 个未标注 refdes 未修（见 N-07）」 | `k2/hw/fp-lib-table` `d731638859be9a08` **存在**且被 DRC 采信（`lib_footprint_issues` 6→0）；refdes 侧 = 伪缺陷（见 `N-07`） | **两半均就绪** ⇒ 载体**已修** |
| `N-03` | 「`.kicad_pro sheets: []` ⇒ PCB 未挂原理图页」 | pro `schematic.top_level_sheets` = **`[{filename: "k2_v4_8L.l4.kicad_sch", name: "k2_v4_8L.l4", …}]`** 而 **全仓不存在 `k2_v4_8L.l4.kicad_sch`**（`find` 0 命中）；`sheets: []` 亦在 | **缺陷更锐化**：根图指针指向**不存在的 l4 根图**（跨 revision 悬挂）；修复 = 一行 pro 键值（§12.3 决策 8） |
| `M-10` | 「载体已修：`k2/hw/fp-lib-table` `d731638859be9a08`」 | 文件存在，sha 一致 | 一致 ✓ |
| `M-08` / `U-05` / `U-06` / `N-06` | 「载体已修：l5 pro ignore 9→0（`d5e0ca06…`）」 | pro `rule_severities` 中 `ignore` **0 条** | 一致 ✓ |
| `F-6` / `M-08` 模板余项 | 「共享模板 `k2/tools/k2_jlc_template.kicad_pro` 仍含 9 条 ignore」 | 模板 `ignore` **9 条**（`copper_sliver`/`footprint_filters_mismatch`/`footprint_type_mismatch`/`missing_courtyard`/`silk_over_copper`/`silk_overlap`/`track_not_centered_on_via`/`tuning_profile_track_geometries`/`via_dangling`） | 一致 ✓（计划 §1.2#7 / §P6，须获批） |
| `F-14` / `N-05` | 「部分修：R4 建两个 symlink 兜底」 | `k2/boards/k2_sch.yaml → ../hw/data/k2_sch.yaml`、`k2/k2_v4.kicad_pcb → hw/k2_v4_8L.kicad_pcb` **均在** | 一致 ✓（G-ROOT-3 未闭） |

### 12.2 修正后的计数（**ENG 实测口径；判定归监理**）

| ⑤ | v1.3 记载 | **v1.4（本表实测修正后）** | 变动来源 |
|---|---|---|---|
| 根闭 | 0 | **0**（判据仍未安装/未签认 ⇒ 无一行满足 ④） | — |
| OUT（具名） | 4 | **5** | `N-07`（前提实测不成立，建议 OUT） |
| 未闭 | 55 | **54** | 同上 |
| └ 载体已修、只差判据在岗 | 15 | **17** | `+M-02` `+F-12` |
| └ 判据已实现、待安装 + 签认（J-1..J-10） | 10 | **10**（v1.4 实测：最终板全判据 **19P/0F**，见 `K2-P4-THRESHOLD-MARGIN-AND-19P-REHEARSAL-v1.md`） | — |
| └ 载体未修（结构性根因） | 30 | **27** | `−M-02` `−F-12` `−N-07` |

### 12.3 关门剩余动作 —— 按**缺失条件的责任方**归类（P4 关门 = 全闭）

| 责任方 | 缺失条件 | 涉及条目 | 条数 | 备注 |
|---|---|---|---|---|
| **gate 属主 + 监理** | 判据安装 + manifest 签认（**对全部 54 条都是必要条件**，因 #K2-22 §二「manifest 未签认前不算在岗」） | **全部** | **54** | 安装包就绪度与两处缺陷见 `K2-P4-PIPELINE-INSTALL-READINESS-v1.md`（D-1 消歧 / D-2 派单） |
| **监理放行（落件）** | 载体侧最后一步：⑥+⑦ 落件（库/几何） | `U-03` `U-04` `M-09`（库侧）+ `F-12` | 4 | 候选 `9682dd026f48c04a` + 库 27 件已就绪（inc40） |
| **监理放行（改生成器）** | G-ROOT-1/2/3 或其衍生（方案见 §6 G9/G10/G11） | `U-04` `U-07` `U-09` `U-10` · `M-03` `M-05` `M-06` `M-09` `M-11` · `F-1` `F-2` `F-7` `F-10` `F-14` · `N-05` | 15 | 未获批不得改生成器（红线）⇒ 不放行则这 15 条**结构性不可闭** |
| **监理/owner（真源/原理图/冻结件）** | 真源 nc 声明（errata-2）· 原理图 · L2 冻结表回改 · 6L 历史件 | `M-03` `F-10` · `N-03`（pro 侧，ENG 可执行）· `F-9`（冻结件回改须 owner 批） | 3~4 | `N-03` 修复本身 ENG 可做（§12.1），但需监理排程以免与待批落件冲突 |
| **监理（口径/阈值）** | J-8 密度口径与阈值 · V3 阈值口径 | `M-12` `U-09`（判据侧） | 2 | 裕量与后果见 `K2-P4-THRESHOLD-MARGIN-AND-19P-REHEARSAL-v1.md` §3 |
| **P5 交付面** | 出交付 Gerber（P4 未关门不得出） | `N-01` | 1 | 前置已实测（`G36>0`） |

> 读法：**任何一条未闭行都同时缺「判据在岗」**（第一行），因此「安装 + 签认」是一次性最大杠杆；
> 第二/三行是**仅凭放行即可闭**的 19 条（4+15，含交集 `U-04`/`M-09`）；其余为真源/口径/交付面。

### 12.4 复跑（本节每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli
grep -rn "DS160PR810" k2/README.md k2/docs/01-architecture.md            # 期望 0 命中
grep -rn "DS160PR810" --include='*.json' k2/pm_gate/artifacts/k2_v4/L3/ | grep -c "spec-rev-47"   # 期望 0
$K k2/tools/k2_refdes_annotation_probe_v1.py --sch-dir k2/hw/sch --board k2/hw/k2_v4_8L.l5.kicad_pcb \
   --kicad-cli $CLI --root-sch k2/hw/sch/k2_sch.kicad_sch --netlist-out /tmp/opencode/n07/k2.net --json /tmp/opencode/n07/probe.json
python3 -c "import json;d=json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'));print(d['schematic']['top_level_sheets'])"
find . -name 'k2_v4_8L.l4.kicad_sch' -not -path './AppDir/*'              # 期望 0 命中
```

**边界**：本节**只读取证**；未改板/pro/库/SPEC/生成器/`criteria/`/真源 yaml/冻结件；未派 WORKER；临时仅 `/tmp/opencode`。

—— ENG（ARCHER）· 2026-09-18 · 探针 `1bd3f4a9d47ff0d4`

---

## 13. v1.5 增量更新（2026-09-18；**#K2-23 §二-11 采纳生效 + inc77/79/80/83 载体态刷新**；§0/§1..§12 为历史快照，不改写）

> 触发：监理 **#K2-23 §二-11**「闭环表 3 处修正 —— **放行采纳**（提案 `86e73a061e57f5d4`；一致性机检 **v1.4 FAIL → v1.5 PASS**；对 19 维读数影响 **0 处**）」+
> 监理自动续推（按已批准计划推进当前阶段）。本节 ③ 列**逐条以只读实测复核**；**判定仍归监理**。

### 13.0 生效：§12 的 3 处修正（由「建议/核验」→ **采纳生效**）

| 行 | 生效后 ③ | 生效后 ⑤ | 依据 |
|---|---|---|---|
| `M-02` | **载体已修**（`k2/README.md` · `k2/docs/01-architecture.md` 中 `DS160PR810` = **0**，本轮复测 0；`DS320PR1601` 为现行名） | **未闭**（载体已修；**无判据消费文档层** ⇒ 「无判据类」根闭口径**须监理定义**，ENG 不预判） | `#K2-23 §二-11` · 本节 §13.4 |
| `F-12` | **载体已修**（`k2/hw/fp-lib-table` `d731638859be9a08` 存在 + `ForgeOS` 1 条 + `ForgeOS.pretty` **20** 件；refdes 侧 = 伪缺陷 ⇒ 由 `N-07` 消解） | **未闭**（④ `fp_lib_table_present` 已实现、**待安装 + 签认**） | 同上 |
| `N-07` | **现象不成立（伪缺陷）**：排除 `(lib_symbols …)` 子树后**实例态未标注 refdes = 0**（本轮回测 6 个 sch 全 0；31 个 `?` 全在定义子树） | **OUT（具名：前提实测不成立）** | 同上（`K2-P4-CLOSURE-ADOPTION-CRITERIA-IMPACT-DRAFT-v1.md`） |

### 13.1 载体态刷新（**仅列本轮实测复核到的变化**；未列条目 = §12 记载仍成立，其 ⑤ 前提见 §13.2）

| 行 | §12 记载 | **本轮实测（2026-09-18）** | 新 ③ 归类 | 证据 |
|---|---|---|---|---|
| `U-10` | 未修（生成器无孔/keepout 产出 = G-ROOT-2） | **G-ROOT-2 已闭载体**：生成器 emit **18 zone（8 keepout + 10 有网铜区，源＝SPEC rev-49 输入层，不读板）+ 4 NPTH**；KiCad 级实测 `zones 18 / keepout 8 / NPTH 4 Ø3.2 / ZONE_FILLER 后 zone_filled 10/10 / keepout_active=True` | **载体已修**（余 ④ 未在岗） | k2 `6cae23a`（inc80）· Step 5 复跑件 `K2-P4-Z4-STEP5-RERUN-ACCEPTANCE-v1.md` |
| `M-05` | 未修，仅板面（生成器无铺铜产出 = G-ROOT-2） | **G-ROOT-2 已闭载体（铺铜产出侧）**：10 有网铜区由生成器按 SPEC 输入层产出、填充由出图前 `ZONE_FILLER` 强制（实测 10/10）；**「无填充/平面前置判据」侧**仍待 `ref_plane_continuity` 安装 | **载体已修**（判据侧待安装） | 同上 |
| `F-2` | 同 `M-05` | 同 `M-05` | **载体已修**（判据侧待安装） | 同上 |
| `M-11` | 未修（G-ROOT-1 + G-ROOT-2） | **G-ROOT-2 侧已闭**（4 NPTH 产出）；**G-ROOT-1 侧未闭**（排针 pad 几何仍取自锚板 ⇒ 生成器产物 `pads=262` 仍缺 16 排针 pad） | **载体未修**（余 G-ROOT-1） | k2 `6cae23a` + Step 5 复跑件（产物 `器件数 42 / pads 262`） |
| `F-1` | 未修（G-ROOT-1 + G-ROOT-2；5 排针 0 焊盘 / 全板 0 孔） | **G-ROOT-2 侧已闭**（4 NPTH）；**G-ROOT-1 侧未闭**（排针 pad 循环依赖） | **载体未修**（余 G-ROOT-1） | 同上 |
| `F-14` | 未修（`YAML_PATH` 硬编码 + symlink 兜底 = G-ROOT-3） | **G-ROOT-3 已闭载体**：`YAML_PATH = ROOT/_PMCFG.project_config()["nets_yaml"]` + **显式 fail-closed「禁 symlink 兜底」**；`k2/boards/k2_sch.yaml` **已删**（`k2/boards/` 空目录）；E4 确定性实测（两次运行同 sha `1252bd2e74957d82`） | **载体已修**（E4 判据实现待安装） | k2 `ba3cd07`（inc79）· Step 5 复跑件 |
| `N-05` | 部分修（symlink 消错） | **G-ROOT-3 侧已闭**（同上）；余 `PCB_REF_PATH` = **G-ROOT-1** 侧未闭 | **载体已修（G-ROOT-3 侧）**，余 G-ROOT-1 | 同上 |
| `M-03` | 未修（真源 nc 声明 = 0；errata-2 +nc 105 未安装） | **路径已裁 + 口径载体已落**：`#K2-23 §二-6` 裁 **乙**（不动真源、只修判据读取口径）；`D-7a`（NC 白名单 ①②）已落 `_shared a266851`（实测负控：无 NC 口径 → 106 处误报；有 D-7a → 余 **2 处**，同根 `C89/A`） | **载体已修**（口径侧；余 ⑤） | `_shared a266851` · inc76 件 |
| `M-17` | 未修（同上） | 同 `M-03` | **载体已修**（口径侧；余 ⑤） | 同上 |
| `F-10` | 未修（草案 errata-2 未安装） | 同 `M-03`（`#K2-23 §二-6` 裁乙 ⇒ errata-2 属**已驳回**路径，非欠件） | **载体已修**（口径侧；余 ⑤） | 同上 |
| `M-13` | 未修（`k2/pipeline.yaml` 缺；安装属 gate 属主） | **共享层 5 修已落 + BOM 前置已落**：`_shared a266851`（D-2 缺件 fail-closed / D-3 affected 三路径 / **D-4b 案A `cmd_verify` 跑各 phase `checks`** / `D-7a`）；`k2/fab/k2_v4_bom.csv` **`9e4ddf4a44302b76`**（55 refs，每行一 ref）⇒ 只差 **安装**（⑤ 硬前置） | **载体已修（前置件）**；安装待 ⑤ | `_shared a266851` · 本节 §13.4 |
| `F-13` | 未修（同上；两个核对器零调用） | 同 `M-13`（安装待 ⑤；核对器接线随装） | **载体已修（前置件）** | 同上 |
| `N-04` | 未修（接线 = gate 安装项） | 同 `M-13`（必选三联 `sch_structural/netlist_connect/bom_consistent` 的 **BOM 件已存在** ⇒ 安装后 `bom_consistent` 有实件可判） | **载体已修（前置件）** | 同上 |
| `J-9` | 未闭（草案 `pipeline.yaml.draft` 已备，安装属 gate 属主） | 同 `M-13`：**判据侧 + BOM 件均已就绪**，唯一欠项 = 安装（⑤ 硬前置） | **未闭**（判据类，见 §13.2） | 同上 |
| `F-3` | 载体已修（rev-20…**rev-47**） | 版本链延伸：**现行 SPEC `rev-49`** `b8f4a7cb67b575f0`（`project.yaml` 指向；D1/D2 与 G10 输入层已载） | **载体已修**（刷新） | `k2/pm_gate/project.yaml` · SPEC rev-48/49 |
| `N-02` | 载体已修（指针经 rev-20…**rev-47**） | 同 `F-3`：**rev-49** | **载体已修**（刷新） | 同上 |

> **未列出的其余条目**：§12 的 ③ 记载自 inc44 起**无对应载体动作**（本会话载体动作仅 inc77/79/80/82/83 五项，逐项影响面已在上表穷举）⇒ 原样保留，**非抽样**。

### 13.2 计数（**v1.5，ENG 实测口径；判定归监理**）

| ⑤ | v1.4 | **v1.5（本轮）** | 变动来源 |
|---|---|---|---|
| 根闭 | 0 | **0**（④ 仍未在岗：`criteria/` 未签认 + `k2/pipeline.yaml` 缺失，本轮实测同前） | — |
| OUT（具名） | 5 | **5** | `U-01` `U-02` `M-15` `F-11` `N-07` |
| 未闭 | 54 | **54** | — |
| └ 载体已修、只差判据在岗 | 17 | **25** | `+U-10` `+M-05` `+F-2` `+F-14` `+N-05` `+M-03` `+M-17` `+F-10` |
| └ 判据已实现、待安装 + 签认（`J-1..J-10`） | 10 | **10** | — |
| └ 载体未修（结构性根因） | 27 | **19** | `−` 上表 8 条 |

### 13.3 关门剩余动作（更新 §12.3；P4 关门 = 全闭）

| 责任方 | 缺失条件 | 涉及条目 | 条数 |
|---|---|---|---|
| **gate 属主 + 监理** | 判据安装 + manifest 签认（对全部 54 条均为必要条件） | 全部 | **54** |
| **owner（L1，唯一）** | **⑤ `C89/A`／`PWR_5V_KEY`**（`pipeline.yaml` 安装与 `net_declared_realized` 严口径同源硬前置） | `M-03` `M-17` `F-10` `J-9` 等（经 ⑤ 显形） | — |
| **监理（落件/放行）** | **⑦ 库快照重建 + 落件 + 库↔板名集** ⇒ G-ROOT-1 | `U-03` `U-04` `U-07` `M-09` `F-1` `F-7` `M-11` `F-14`（`PCB_REF_PATH` 侧）`N-05`（同侧） | 结构性 |
| **监理（口径/阈值）** | 密度/间距应然阈值 · `ref_plane_continuity` 阈值 · 「无判据类」根闭口径（`M-02`） | `M-12` `U-09` `M-05` `F-2` `M-02` | — |
| **ENG（获批后）** | `N-03` pro 根图指针（一行键值；与待批落件排程） | `N-03` | 1 |
| **P5 交付面** | 出交付 Gerber | `N-01` | 1 |

> **读法不变**：任一条未闭行都同时缺「判据在岗」（首行）⇒ **安装 + 签认是一次性最大杠杆**；本轮把「仅凭 **⑦ 放行** 即可闭」的结构性条目从 15 收敛到 **G-ROOT-1 家族**一处。

### 13.4 复跑（本节每处实测；仓库只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# G-ROOT-3 已闭（YAML_PATH 配置驱动 + symlink 已删）
grep -n 'YAML_PATH' k2/tools/k2_gen_v5.py; ls -la k2/boards/            # 期望：配置驱动 + 空目录（无 k2_sch.yaml）
# G-ROOT-2 已闭（emit 18 zone / 4 NPTH；两次同 sha）
K2_OUT_PCB=/tmp/opencode/inc83/g1.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc83/g1.json python3 k2/tools/k2_gen_v5.py
AppDir/usr/bin/python3.11 -c "
import pcbnew;b=pcbnew.LoadBoard('/tmp/opencode/inc83/g1.kicad_pcb')
print('zones',len(b.Zones()),'keepout',sum(1 for z in b.Zones() if z.GetIsRuleArea()))"
# BOM 前置已落（55 refs；真 check PASS）
python3 k2/tools/k2_p4_bom_gen_v1.py --out /tmp/opencode/bomchk.csv     # 期望预测 sha16 = 9e4ddf4a44302b76
python3 -c "
import pathlib,sys; sys.path.insert(0,'_shared')
from eda_core.pipeline import checks
print(checks.check_bom_consistent({'_root':pathlib.Path('k2').resolve(),'_yaml_path':pathlib.Path('k2/pipeline.yaml')},
      {'sch':'k2/hw/sch/k2_sch.kicad_sch','bom_csv':'k2/fab/k2_v4_bom.csv'}))"   # 期望 (True, 'BOM 与 sch 同步 (55 器件)')
# M-02 / F-12 / N-07（3 处采纳）
grep -c 'DS160PR810' k2/README.md k2/docs/01-architecture.md                     # 期望 0 / 0
sha256sum k2/hw/fp-lib-table; ls k2/hw/lib/ForgeOS.pretty | wc -l                # d7316388… / 20
# N-07：实例态未标注 refdes = 0（31 个 ? 全在 lib_symbols 定义子树）——见 §12.4 探针命令
# ④ 在岗态（全表前提）
sha256sum criteria/*; ls k2/pipeline.yaml                                        # 未改 / 不存在
```

**边界**：本节**只读取证 + 追加本段**；未改板/pro/库/SPEC/生成器/`criteria/`/真源 yaml/冻结件/`_shared`；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**。
**fail-closed**：P4 未全绿（本表全闭）不下单、不出交付 Gerber。

—— ENG（ARCHER）· 2026-09-18 · 表版本 **v1.5** · 图集 v10 `d6613754a7382c99` · BOM `9e4ddf4a44302b76` · 受审板 `6ff49da5678c2108`

## 14. v1.6 增量（2026-09-18；**#K2-28 裁定收口：P3 PASS + 坐标源 (a) + L-1 登记 + E-4 在岗**）

> 触发：监理 **#K2-28**（P3 五项全 PASS · 坐标源裁 **(a)** · 库旧件/`k2_p4_*` 两项裁定 · 下一件 = E-4/E-5）。§0–§13 为历史快照，不改写。

### 14.1 **L-1 来源限制登记（#K2-28 §2.3-C2）**

| 编号 | 限制 | 内容（**逐条机检，非估计**） | 处置 |
|---|---|---|---|
| **L-1** | **坐标来源** | canonical 布局解 `k2/pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json`（rev=2 `086d453d23c5fbff`）= **P4 已批准落位的 canonical 捕获，非独立求解**；54 件中 **28 件仅板来源**（冻结输入无任何非板权威）+ **2 件曾陈旧**（`C86`/`R42`，已由 #K2-28 §2.3-C1 推 `p3_placement_solution.json` rev=2 补正 ⇒ 现 **15 一致 / 0 陈旧**） | **不得主张独立推导**；**C4**：L-1 若未被 owner 另行授权 (c)，须在 **P4 关门**时**具名接受**（或转 (c)）后方可进 P5；**不得**在 P5 打样件中隐去 |

**C3 口径标注**：`产物 == 受审板` 等式 = **确定性检查**，**非独立性证明**（#K2-28 §2.3-C3）。

### 14.2 ④「判据在岗」推进（E-4/E-5，本轮）

| 项 | v1.5（§13.2） | **v1.6（本轮）** |
|---|---|---|
| `k2/pipeline.yaml` | **不存在**（`pipeline_present` FAIL） | **已安装 `c89cc57fb988f821`**（phases-only + `errata-2` + D-7a）；`engine verify k2` **4/4 PASS** |
| 在库判定器（rev=1）复跑 | PASS 7 / FAIL 3 | **PASS 8 / FAIL 2**（`pipeline_present` **FAIL→PASS**；余 `zone_filled` 10/18 · `refdes_sets_equal` 54/58 = **已具名口径项**） |
| 19 维 canonical | 草案未装 | **在岗清单 + 5 组别名钉死已交**（`manifest.k2.canonical-draft-v1.yaml 3f003cffe33a6cfd`，17 true / 2 false）；**签认/安装请求**见 E-4/E-5 提交件 §4 |
| `criteria/**` | rev=1（未签认） | **仍 rev=1**（`897e8bfde60e2cfe` / `7ce08757eff25557`）⇒ **④ 在岗 = 0 条**（签认属监理）；**锚 rev=2 登记请求**已交（提交件 §5） |
| 判定器口径分歧（登记备裁） | — | `net_declared_realized` 声明 `>=2` **未 gate**（`nets_with_lt2` 仅报告）；现行真源 `errata-2` 下 `lt2 = 0` ⇒ **潜伏**，文字口径仍须裁 |
| 二维阈值 | 待裁 | `ref_plane_continuity`：nominal **100%** / strict **83.52%**（**1.0 不可达**，守恒级证明齐）· `density_and_clearance`：机制齐 + 7 案正负控齐（候选阈值见提交件 §6）⇒ **均待裁**（切 nominal 须明示授权，**禁充绿**） |

### 14.3 载体侧（本轮同批）

| 项 | 结果 |
|---|---|
| **C1** L3 布局解补正 | `L3/drawings/p3_placement_solution.json` **rev=2 `dfbf65c5b456cdd2`**（`C86`→`31.55,58.85` · `R42`→`93.3,61.55`；bbox 级独立复算四闸 0 违规）⇒ **权威链内部一致**（L2 布局解随之 rev=2 `086d453d23c5fbff`；**产物 sha 不变** `d67c0f048f0d0423`） |
| **§三** 库旧件退役 | 12 件 stale mod → `k2/archive/k2_v4_stale_lib_20260918/` + `MANIFEST.md`；库 **36 → 24** 文件（digest `078f7dc78d980696` → **`efcd88b35d6d846c`**）；`MountingHole_3.2mm_M3` **保留**（其名被生成器 `NPTH_FP_NAME` 用） |
| **§四** `k2_p4_*` 退役 | `k2/tools/k2_p4_RETIRED.md`（**44 件清单标记 RETIRED(离链)**；**未删/未移动**，保精确路径可追溯）；构造链 = `k2_gen_v5.py` 单件 |
| **§2.4** 注释更正 | `k2_gen_v5.py` 内 `nets_yaml` 注释 `errata-1` → **`errata-2`**（纯注释，无行为变更） |

**fail-closed**：P4 未全绿（本表全闭）不下单、不出交付 Gerber。

—— ENG（ARCHER）· 2026-09-18 · 表版本 **v1.6** · pipeline.yaml `c89cc57fb988f821` · 布局解 rev=2 `086d453d23c5fbff` · 受审板 `dae8dc8d48ff5b81`（未动）

---

## 15. v1.7 增量（2026-09-18；**E-3「载体根闭重算 + 余项闭环」** —— #K2-29 §六-2/§六-3/§七）

> 触发：监理 **#K2-29**（E-4/E-5 判 PASS · 判据在岗 = 安装 + 签认 + **锚 rev=2** · 下一件 = E-3「载体根闭重算 + 余项闭环」，唯一）。§0–§14 为历史快照，**不改写**。
> **口径（本版新增，ENG 实测；判定归监理）**：`⑤ = 根闭 ⟺ ① 本受审板载体已修 ∧ ② 本条 ④ 所指判据**在岗**（已入 `criteria/` + 签认 + 正/负控）∧ ③ 该判据对本条**实测为绿**`。
> 判据在岗事实：`criteria/**` **rev=2 COUNTERSIGNED**（`d251bea7c2cb1873` / `1cda68521d0e56be` / `568d2e93d53f854c`）+ `k2/pipeline.yaml` **`c89cc57fb988f821`**（`engine verify k2` **4/4 PASS**）⇒ **v1.5/v1.6 的「④ 未在岗」这一全局豁免已消失**。
> 19 维标准调用实测 = **15 OK / 2 FAIL**（受审板 `dae8dc8d48ff5b81`）：FAIL = `drc_warning_dispositions`（`lib_footprint_issues`×2）+ `lib_electrical_level`（差异 28），**同一根因** = 受审板 `lib_id` 未重指（本表 `U-03`/`M-09`/`J-7`）⇒ 详见 `k2/docs/K2-P4-E3-STANDARD-CALL-WIRING-AND-CARRIER-DELTA-v1.md` **`e861fd9d8bfce7c7`**。

### 15.1 全 59 条重算（②③ 载体态沿用 §13.1 及本会话实测；⑤ 为本版重定）

| 段 | 条目 ⑤ 重定 | 依据 / 余项 |
|---|---|---|
| U-01 | **OUT**（不变） | 计划 §1.3#5 具名（3D 渲染 origin）；替代判据 J-8 器件重叠 |
| U-02 | **OUT**（不变） | 同上 |
| U-03 | **未闭** | 受审板 `J3`/`J4` `lib_id` = `ForgeOS:MCIO_4i_SFF-1016_RASide`（快照仅 `…__1`/`…__2`）⇒ `library_item_missing`×2 + DRC `lib_footprint_issues`×2；**⑦「重指 lib_id」待裁** |
| U-04 | **根闭** | W-8 实测 `J2` = `electrical_identical`（P1 按板重建落库闭）；④ 在岗 |
| U-05 | **根闭** | pro `ignore 9→0` + 丝印违规 0 + `rule_severity_manifest` 在岗**绿**；余项 共享模板 9 条（§P6 具名） |
| U-06 | **根闭** | 非 45° **0/4720** + `non45_segments` 在岗绿（负控 l4 已做） |
| U-07 | **根闭** | 生成器 pad ← 库快照（排针 16 pad 已产出）；`device_has_pads`+`pin_map_complete` 在岗绿 |
| U-08 | **根闭** | `BOARD` 46mm + `pads_within_outline` 在岗绿（出框 0）；density 余项归 M-12 |
| U-09 | **未闭** | 密度口径：测量接线**已通**、读数达标；启用待 `criteria/` rev bump（gate 属主） |
| U-10 | **根闭** | G-ROOT-2 闭（生成器 emit **4 NPTH + 8 keepout**）；`drill_count`+`keepout_active` 在岗绿 |
| M-01 | **根闭** | 真源归零 + `refdes_sets_equal` 在岗绿 **54/54** |
| M-02 | **未闭**（仅余④口径） | 载体已修（`README`/`01-architecture` 中 `DS160PR810` = **0**）；**「无判据类」根闭口径待监理定义** |
| M-03 | **根闭** | `errata-2` 现行 + D-7a（#K2-23 §二-6 裁乙）+ `net_declared_realized`/`pin_map_complete`/`unconnected_zero` 在岗绿；⑤ 硬前置已由 owner **#K2-24** 闭 |
| M-04 | **根闭** | 同 U-06 |
| M-05 | **根闭** | `zone_filled` 在岗绿 **10/10**（G-ROOT-2 铺铜产出闭）；余项 `ref_plane_continuity` 升 owner + Gerber 侧归 P5 |
| M-06 | **根闭** | `unconnected_zero` 在岗绿 |
| M-07 | **根闭**（判据侧） | `drc_errors`+`unconnected_zero` 在岗绿；L5 旧包历史件由 P5 新包取代 |
| M-08 | **根闭** | 同 U-05（模板余项 §P6 具名） |
| M-09 | **未闭** | 同 U-03：`lib_id` 未重指 ⇒ `lib_electrical_level` 在岗但**红 28** |
| M-10 | **根闭** | `fp-lib-table` `d7316388…` 在 + `fp_lib_table_present` 在岗绿 |
| M-11 | **根闭** | NPTH 4 / PTH 16 + `drill_count` 在岗绿（G-ROOT-2 闭） |
| M-12 | **未闭** | 同 U-09（密度口径/启用） |
| M-13 | **根闭** | `k2/pipeline.yaml` 已装 + `pipeline_present` 在岗绿 + `engine verify` 4/4 |
| M-14 | **未闭**（仅余④口径） | 载体已修（`project.yaml` + `k2_v4.kicad_pcb` symlink）；「路径可解析」无判据 ⇒ 口径待监理 |
| M-15 | **OUT**（不变） | 计划 §1.3#5 具名 |
| M-16 | **根闭** | `U1` = 49 带号 pad（+9 枚无号 `F.Paste` EP 归 **D** 口径）；`device_has_pads`+`pin_map_complete` 在岗绿 |
| M-17 | **根闭** | NO_CONNECT 128 pad 不产生假未连 ⇒ `unconnected_zero`+`net_declared_realized` 在岗绿 |
| M-18 | **根闭** | 19 维判据在岗（rev=2 签认） |
| F-1 | **根闭** | G-ROOT-1（P2 去锚板）+ G-ROOT-2 闭；`device_has_pads`+`drill_count` 在岗绿 |
| F-2 | **根闭** | 同 M-05 |
| F-3 | **未闭**（仅余④口径） | SPEC **rev-50**（8L）载体已修；层判据未入 canonical ⇒ 口径待监理（**不新增齿**） |
| F-4 | **根闭** | 同 U-06 |
| F-5 | **根闭** | 同 M-01 |
| F-6 | **根闭** | 同 U-05 |
| F-7 | **根闭** | pad 对账 **672/672 · 逐件名集 0 差异** + `device_has_pads`/`pin_map_complete` 在岗绿；U6 无网球经 D-7a/⑤ 闭 |
| F-8 | **根闭** | `BOARD` 46mm + `pads_within_outline` 在岗绿 |
| F-9 | **未闭** | 走廊口径两套未对账（L2 冻结表回改须 **owner**） |
| F-10 | **根闭** | 同 M-03 |
| F-11 | **OUT**（不变） | 计划 §1.3#5 具名 |
| F-12 | **根闭** | `fp-lib-table` 在岗绿；refdes 侧 = 伪缺陷（`N-07` OUT 消解） |
| F-13 | **根闭** | 同 M-13 |
| F-14 | **根闭** | G-ROOT-3 闭（`YAML_PATH` 配置驱动 + symlink 删 + 显式 fail-closed）；产物确定性 8×同 sha |
| N-01 | **未闭** | 交付 Gerber 未出（P5 未开）；fail-closed：P4 未全绿不下单 |
| N-02 | **未闭**（仅余④口径） | 指针 **rev-50**（8L）载体已修；层判据口径待监理（同 F-3） |
| N-03 | **未闭** | pro `sheets: []` + `top_level_sheets → k2_v4_8L.l4.kicad_sch`（**全仓不存在**）；修复 = **一行 pro 键值**（须放行；改 pro ⇒ sha 重锚） |
| N-04 | **根闭** | `engine verify` 4/4（必选三联 `sch_structural`/`netlist_connect`/`bom_consistent`）+ `pipeline_present` 在岗绿 |
| N-05 | **根闭** | G-ROOT-3 闭 + 残余 G-ROOT-1 侧已由 P2 闭 |
| N-06 | **根闭** | 同 U-05 |
| N-07 | **OUT**（§13.0 生效） | 前提实测不成立（伪缺陷：实例态未标注 refdes = 0） |
| J-1 | **未闭** | `drc_errors` 在岗绿（error **0**）；但 warning **未逐项处置**（`lib_footprint_issues` 未登记）⇒ 余项归 U-03 同根 |
| J-2 | **根闭** | `unconnected_zero` 在岗绿 |
| J-3 | **根闭** | `zone_filled` 在岗绿 10/10 |
| J-4 | **根闭** | 丝印违规 **0** + `rule_severities` ignore **0**（全开）+ `drc_errors` 在岗绿；`drc_warning_dispositions` 红属非丝印类（归 J-1/U-03） |
| J-5 | **根闭** | `non45_segments` 在岗绿 |
| J-6 | **根闭** | `refdes_sets_equal` 在岗绿 |
| J-7 | **未闭** | `lib_electrical_level` 在岗但**红 28**（`lib_id` 未重指）；含 `fp_lib_table_present` 侧绿 |
| J-8 | **未闭** | `keepout_active`/`pads_within_outline` 在岗绿；`density_and_clearance` **未启用** |
| J-9 | **根闭** | `pipeline_present` 在岗绿 + `engine verify` 4/4 |
| J-10 | **根闭** | 复跑链固定（构造 8×同 sha `d67c0f048f0d0423` · 19 维标准调用 · `engine verify` 4/4 · 判据锚 rev=2） |

### 15.2 计数（**v1.7，ENG 实测口径；判定归监理**）

| ⑤ | v1.5（§13.2） | **v1.7（本轮）** | 变动来源 |
|---|---|---|---|
| **根闭** | 0 | **40** | ④ 全局豁免消失（rev=2 签认 + `pipeline.yaml`）⇒ 「载体已修待判据」族 + J 段多数转绿 |
| **未闭** | 54 | **14** | 余项 = 判据红 2（U-03/M-09/J-7）· 口径待裁 3（U-09/M-12 ·「无判据类」3）· pro 一行 1（N-03）· 走廊 1（F-9）· 交付面 1（N-01）· 密度启用 1（J-8）· warning 登记 1（J-1） |
| **OUT（具名）** | 5 | **5** | `U-01` `U-02` `M-15` `F-11` `N-07`（不变） |

> **未闭 14 条具名**：`U-03` `U-09` · `M-02` `M-09` `M-12` `M-14` · `F-3` `F-9` · `N-01` `N-02` `N-03` · `J-1` `J-7` `J-8`
> **不得宣称归零**（C-12）：本版**没有**任何一条以「接近 0」或「口径切换」充绿；`ref_plane_continuity` 严口径 **83.52%** 仍为**不可达**（升 owner），`lib_electrical_level` 仍 **FAIL 28**。

### 15.3 未闭 14 条的归属 → 修复件 → 阻塞点

| ID | 归属 | 修复件 | 阻塞点 |
|---|---|---|---|
| `U-03` `M-09` `J-7` | **监理裁定**（⑦ 库侧） | 受审板 54 件 `lib_id` 重指 `ForgeOS:<refmap mod>`（生成器产物已正确：`49 identical / 5 diff`）——选项 (a) 受审板重落 /(b) 最小外科改串 /(c) 判据改消费 refmap | 未获批；受审板（或 `criteria/`）sha 变更 ⇒ 测量链全重锚 |
| `J-1` | 同上一行（**同根**） | `lib_footprint_issues`×2 = `J3`/`J4` 无后缀 mod 名，随重指一并消解 | 同上一行 |
| `U-09` `M-12` `J-8` | gate 属主/监理 | `criteria/manifest.k2.yaml` `density_and_clearance.enabled:true`（阈值已在件内）+ rev bump | `criteria/**` ENG 只读；测量 5 件已通且达标 |
| `M-02` `M-14` `F-3` `N-02` | 监理 | 「无判据类」根闭口径定义（文档层/路径层/SPEC 层；**不新增检查齿**） | 未裁 |
| `N-03` | 监理放行 | l5 pro 一行键值（`sheets` / `top_level_sheets` → 现行根图） | 改 pro ⇒ pro sha 变 ⇒ 测量链重锚 |
| `F-9` | owner/监理 | L2 冻结走廊表回改（改冻结件须 owner） | 未获批 |
| `N-01` | P5（未开） | 出交付 Gerber 包（8 铜层 + 阻焊/丝印/边框/job + Excellon 含 HDI + 叠层图 + 阻抗表 + MANIFEST） | **fail-closed**：P4 未全绿不下单、不出交付 Gerber |

### 15.4 复跑（本节每处实测；仓库只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
sha256sum criteria/*                       # 期望 d251bea7…/1cda6852…/568d2e93…
tail -1 .omo/supervision/ledger/adjudication-ledger.jsonl | head -c 200            # 期望 rev:2 / COUNTERSIGNED（#K2-29）
cd k2 && PYTHONPATH="$PWD/_shared:$PWD" python3 _shared/eda_core/pipeline/engine.py verify k2; cd ..   # 期望 4/4 PASS
# 19 维标准调用（15 OK / 2 FAIL）与 5 件测量读数：见 K2-P4-E3-…-v1.md §1/§2/§7
# 受审板 l5 lib_id 分布（24 空 /17 Capacitor_SMD /9 Resistor_SMD /1 Package_SO /1 LED_SMD /6 ForgeOS）
# 生成器产物 lib_id：ForgeOS 54 + 空 4；产物 sha d67c0f048f0d0423
```

**边界**：本节**只读取证 + 追加本段**；未改板/pro/库/SPEC/生成器/`criteria/`/真源/`_shared`/冻结件；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**。
**fail-closed**：P4 未全绿（本表全闭 + 全 J 类绿）不下单、不出交付 Gerber。

—— ENG（ARCHER）· 2026-09-18 · 表版本 **v1.7** · 判据锚 **rev=2** · `pipeline.yaml c89cc57fb988f821` · 受审板 `dae8dc8d48ff5b81`（未动）· 产物 `d67c0f048f0d0423`（未动）


---

## 16. v1.8 增量（2026-09-19；**#K2-32 §一/§二 落件后全链重锚 + `M-14` fail-closed 实证**）

> 触发：监理 **#K2-32**（§一 放行 (a) 同笔 SPEC bump + §二 `top_level_sheets` 裁定 + §三 段2/段3 PASS）。§0–§15 历史快照**不改写**。
> 落件：k2 **`2b4792c`** —— 受审板 **`l5 dae8dc8d48ff5b81` → `l6 30fa849641323f98104f`**（l5 保留历史件）；SPEC **rev-51 `e96f2df07fe1d764`**（rev-50 `ed0950687e5aec97` 逐字节不改）；pro **`12ad219b9f66b7b3`**（链 pro + 两补丁）。
> 全链重锚与逐项读数见 `k2/docs/K2-P4-SEGMENT2C-CANONICAL-ORDER-AND-BLOCKERS-v1.md` **§23**（`daa51ad7916b81a9`）。

### 16.1 受审载体变更对 ⑤ 的影响（**计数不变：根闭 40 / OUT 5 / 未闭 14**）

| 条 | ⑤ | 本版实测依据（受审板 `30fa849641323f98`） |
|---|---|---|
| `U-03` `M-09` `J-7` | **未闭（读数显著改善）** | `lib_electrical_level` 由 `差异 28` → **`差异 5`**（w8 58 件：identical **4→49** · electrical_diff **28→5** · no_library_link **24→4** · unloadable **2→0**）；仍 FAIL（须 0）⇒ ⑦「重指 `lib_id`」仍待裁 |
| `J-1` | **未闭（读数更新）** | `drc_warning_dispositions`：受审 pro `ignore` 归 0 后，未登记 warning 类型 **7/9**（`copper_sliver`/`silk_edge_clearance`/`silk_over_copper`/`silk_overlap`/`track_dangling`/`track_not_centered_on_via`/`via_dangling`；已登记 2） |
| 全条 | 不回退 | `drc_errors` error **0** · `unconnected_zero` **0** · `zone_filled` **10/10** · `non45_segments` **0/5125** · `rule_severity_manifest` ignore **0/62** · `pads_within_outline` 出框 **0/0/0** · `engine verify k2` **4/4 PASS** |
| `M-14` | **未闭（④口径）** | 见 §16.2：**实证为 fail-OPEN**，不满足「置坏指针 ⇒ 链失败」 |

### 16.2 `M-14` fail-closed 实证（#K2-30 §2.3；三臂实跑）

- **ARM1**（现行指针，cwd=k2）：`config.board_path()`=`k2_v4.kicad_pcb`，文件在 → `red_team.R13_pcb_guard` = `[]`（审到、无异常）。
- **ARM2**（**坏指针**，临时 project root）：`k2_v4_NOPE.kicad_pcb`，文件不在 → R13 = **`[]`（静默跳过 = 链不失败）**。
- **ARM3**（合法名 + 空 registry，对照）：R13 = **有 findings**（`PCB … 无合法写盘登记`）⇒ 探测器**活着**。
⇒ **`M-14` 的「置坏指针 ⇒ 链失败」在 `red_team` 消费者处不成立**（`if not isfile(pcb): return out` = fail-OPEN）。
- **消费者盘点**：`check_qa.py:22`（基址=`_shared`，恒 FAIL）· `wp1_semantics_check.py:46`/`tools_measure_l1.py`/`tools_executor_single_pair.py:17`（同族）· `red_team.py:346,395`（cwd 相对，缺文件 fail-OPEN）· `cli.py:367`（cwd 相对）· `falsify_service.py:290`（`pcb_root` 拼接）。
- **ENG 建议口径（供监理裁，非新增检查齿）**：钉死「`board_path` 基址 = 项目根（`artifacts.discover_project_root()`）」+ 在**既有**消费者上加 fail-closed 断言；否则 `M-14` 余④无法闭。

### 16.3 本版未闭 14 条（不变，读数刷新）

`U-03` `U-09` · `M-02` `M-09` `M-12` `M-14` · `F-3` `F-9` · `N-01` `N-02` `N-03` · `J-1` `J-7` `J-8`
（余项通道：判据/口径 6 · 交付面 1 · 密度启用 1 · warning 登记 1 · 走廊 1 · `lib_id` 重指 3 · 无判据类 1）
