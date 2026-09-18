# K2 · P4 · **闭环表 3 处修正 diff 草案**（M-02 / F-12 / N-07；含计数自洽机检）· v1 · 2026-09-18

> 缘起：handoff inc65 §6-3-(p)「**闭环表 3 处修正的 diff 草案**（§5-10：`M-02`/`F-12` 归「载体已修」· `N-07` 判 OUT 具名并移出未修清单；纯 diff 草案，待裁后一次改）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 提案件/diff**，仓库零载体改动（仅新增本证据件）。
> 锚：闭环表 `k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md` **`2de0dea4f5a5729d`**（v1.4 快照）· §12.1 载体现状核验（7 处）· `K2-P4-QUEUE10-STATE-AND-CALIBER-DATA-v1.md` §6（主表 vs §12.1 自相矛盾实测）· #K2-22 §三（闭环表全闭＝P4 关门追加条件）。
> 装置（`/tmp`，易失）：提案件 `/tmp/opencode/inc63/closure_table.v1.5.proposed.md` **`86e73a061e57f5d4`** · unified diff `/tmp/opencode/inc63/closure_table.v1.5.diff` **`2b5f73d0e96a3c10`**（72 行）· 机检脚本 `/tmp/opencode/inc63/closure_table_consistency_check.py`。

## 0. 结论（四条）

1. **修正＝把 §12.1 的实测结论并入主表**：8 处编辑（§0 四行计数/清单 ＋ `M-02`/`F-12`/`N-07` 三条主表行 ＋ §7 待办文本）＋ 追加 **§13 v1.5 增量节**登记采纳依据与计数。
2. **采纳后计数**：根闭 **0** · OUT（具名）**4 → 5** · 未闭 **55 → 54**；其中「载体已修」**15 → 17**（`+M-02` `+F-12`）· 「判据已实现待安装」**10** · 「载体未修」**30 → 27**（`−M-02` `−F-12` `−N-07`）。
3. **机检**：计数清单自洽检查 —— **v1.4 现状 FAIL**（`M-02`/`F-12`/`N-07` 仍在「载体未修」·`N-07` 不在 OUT）· **v1.5 提案 PASS**（59 = 0+5+54；54 = 17+10+27；三清单条目数与标称一致）。
4. **`N-03` 不在本件**：其处置（置空 `[]` / 指向真实 sch / 是否连 k1）**待裁**，见 `K2-P4-QUEUE10-STATE-AND-CALIBER-DATA-v1.md` §2；本件**未改**该行。**ENG 不改该表**（采纳权归监理）。

## 1. 逐条改动（8 处；行号为 v1.4 快照 `2de0dea4f5a5729d`）

| # | 位置（v1.4 行） | 现状 | 改为 | 依据（实测） |
|---|---|---|---|---|
| D1 | §0 汇总 · OUT 行（L16） | `OUT（具名）4`（`U-01` `U-02` `M-15` `F-11`） | **5** ＋ `N-07`（前提实测不成立） | N-07 实例未标注 = 0 |
| D2 | §0 汇总 · 未闭行（L18） | `未闭 55` | **54** | 59 − 0 − 5 |
| D3 | §0 汇总 · 载体已修行（L17） | `载体已修 15` | **17** ＋ `M-02` `F-12` | §12.1 核验 |
| D4 | §0 汇总 · 载体未修行（L21） | `载体未修 30`（含 `M-02` `F-12` `N-07`） | **27**（移除三者） | 同上 |
| D5 | §2 `M-02` 行（L55） | ④「**未修**（两文件仍写 dual DS160PR810）」·⑥「未闭」 | ④「**载体已修**」＋三文件 sha；⑥「未闭（载体已修）」 | 三文件 `DS160PR810`/`U3`/`U7` = 0；`DS320PR1601` 4+1 |
| D6 | §3 `F-12` 行（L90） | ④「**部分修**：…7 个未标注 refdes 未修」·⑥「未闭」 | ④「**载体已修**」（库表侧＋refdes 侧＝伪缺陷）；⑥「未闭（载体已修）」 | `fp-lib-table` 存在且被 DRC 采信（`lib_footprint_issues` 6→0） |
| D7 | §4 `N-07` 行（L106） | ④「**未修**（7 个 `?` 仍在）」·⑥「未闭」 | ④「**载体无需修**」（`lib_symbols` 占位说明）；⑥「**OUT（具名：前提实测不成立）**」 | 排除 `(lib_symbols …)` 后实例未标注 = 0；netlist `?` = 0/705 |
| D8 | §7 待办（L173） | 含「`M-02/N-07`（README/原理图未标注 refdes 清理…）」 | 删除该子句 | D5/D7 后二者不再属「载体未修」 |

**附加（D9）**：文末追加 **§13 v1.5 增量节**（不重写 §1..§12 历史快照，沿用本表既有「§N 增量更新」体例），登记：触发、8 处改动摘要、采纳后计数、未动项（`N-03` + 其余 26 条）。

## 2. unified diff（可直接 `git apply`，裁后一次改）

```diff
--- k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md	2026-09-18 00:46:26.085521178 +0800
+++ /tmp/opencode/inc63/closure_table.v1.5.proposed.md	2026-09-18 11:27:06.436412727 +0800
@@ -14,11 +14,11 @@
 | ⑤ | 条数 | 条目 |
 |---|---|---|
 | **根闭** | **0** | —（无一条同时满足「载体已修」+「防复发判据在岗」） |
-| **OUT（具名）** | **4** | `U-01` · `U-02` · `M-15` · `F-11`（计划 §1.3 **OUT #5**「3D 预览模型」；替代判据见下） |
-| **未闭** | **55** | 其余全部 |
-| └ 其中「**载体已修**、只差判据在岗」 | 15 | `U-05` `U-06` `U-08` `M-01` `M-04` `M-08` `M-10` `M-14` `F-3` `F-4` `F-5` `F-6` `F-8` `N-02` `N-06` |
+| **OUT（具名）** | **5** | `U-01` · `U-02` · `M-15` · `F-11`（计划 §1.3 **OUT #5**「3D 预览模型」；替代判据见下） · `N-07`（**前提实测不成立**，见 §4/§12.1） |
+| **未闭** | **54** | 其余全部 |
+| └ 其中「**载体已修**、只差判据在岗」 | 17 | `U-05` `U-06` `U-08` `M-01` `M-02` `M-04` `M-08` `M-10` `M-14` `F-3` `F-4` `F-5` `F-6` `F-8` `F-12` `N-02` `N-06` |
 | └ 其中「**判据已实现**、待安装 + 签认」 | 10 | `J-1..J-10` |
-| └ 其中「**载体未修**（结构性根因）」 | 30 | `U-03` `U-04` `U-07` `U-09` `U-10` · `M-02` `M-03` `M-05` `M-06` `M-07` `M-09` `M-11` `M-12` `M-13` `M-16` `M-17` `M-18` · `F-1` `F-2` `F-7` `F-9` `F-10` `F-12` `F-13` `F-14` · `N-01` `N-03` `N-04` `N-05` `N-07` |
+| └ 其中「**载体未修**（结构性根因）」 | 27 | `U-03` `U-04` `U-07` `U-09` `U-10` · `M-03` `M-05` `M-06` `M-07` `M-09` `M-11` `M-12` `M-13` `M-16` `M-17` `M-18` · `F-1` `F-2` `F-7` `F-9` `F-10` `F-13` `F-14` · `N-01` `N-03` `N-04` `N-05` |
 
 **关键判读**：
 1. **P4 停工的真正原因不是缺板**，而是 **55 条未闭**（其中 30 条载体结构性未修）。
@@ -52,7 +52,7 @@
 | ID | ① 现象 | ② 根因载体 | ③ 根因修复件 | ④ 防复发证明 | ⑤ 状态 |
 |---|---|---|---|---|---|
 | M-01 | 板↔图脱节：板 42 / 原理图 103 / 网表 55；图有板无 64、板有图无 3 | `k2/hw/sch/*.kicad_sch` + `k2/hw/data/k2_sch.yaml`（三源漂移）+ `netlist_parity.py` 未接 | **载体已修**：真源归零 R1/R2（图删 A+C 类 52 件，现图内已无 `U3`/`U7`；板 55 + H1..H4） | `refdes_sets_equal`（冻结；负控 = 改名 `X99` ⇒ FAIL，见 `K2-P1-…-evidence.md`）—— **未在岗** | **未闭**（载体已修） |
-| M-02 | README 称「双 DS160PR810（U7 上行/U3 下行）」，板上只有 1 颗 U6=DS320PR1601 | `k2/README.md:27,46`（`697fa103458268db`）· `k2/docs/01-architecture.md:9`（`c7793b922f0e8a5d`） | **未修**（两文件仍写 dual DS160PR810） | 「不适用」不成立：README 属交付证据层；无文档一致性判据 ⇒ 无替代判据 | **未闭** |
+| M-02 | README 称「双 DS160PR810（U7 上行/U3 下行）」，板上只有 1 颗 U6=DS320PR1601 | `k2/README.md:27,46`（`697fa103458268db`）· `k2/docs/01-architecture.md:9`（`c7793b922f0e8a5d`） | **载体已修**：`k2/README.md` `dc28708ba34fddf2` · `k2/docs/01-architecture.md` `e7a478b5420dc161` · `k2/docs/01-architecture.zh-CN.md` `6182d4a040d1cfc2`（`DS160PR810`/`U3`/`U7` 命中 = 0；见 §12.1） | 「不适用」不成立：README 属交付证据层；无文档一致性判据 ⇒ 无替代判据 | **未闭**（载体已修） |
 | M-03 | U6 = 354 ball，其中 **108 ball 无网络** | `k2/tools/k2_gen_v5.py:296-321`（`assign_nets`）+ 符号 pin_map | **未修**（真源 nc 声明 = 0；草案 `k2/docs/drafts/j9-wiring-option-a/` +nc 105 未安装） | `net_declared_realized` + `pin_map_complete` + `unconnected_zero`（草案）—— **未在岗** | **未闭** |
 | M-04 | **2051/2512（81.6%）线段非 45°** | 同 U-06 | 同 U-06（板面已归一 0/4722；判据未在岗） | `non45_segments`（冻结）—— **未在岗** | **未闭**（载体已修） |
 | M-05 | 9 个铺铜区 `filled_polygon=0`；F.Cu/B.Cu 无地平面；4 个 `ESC_*` 五 flags 全 allowed。更重：交付 8 铜层 Gerber `G36=0` | 板内 `zone` 块（未填）+ **无「填充/平面存在」前置判据** + 生成器无铺铜产出 = **G-ROOT-2** | **未修，仅板面**（P4 填充 10/10；出面前置实测 `G36>0`，`K2-P4-EXIT-PREREQ-MEASUREMENT-v1.md` `26f3193e1d0f2771`） | `zone_filled`（冻结；负控 = l4 板 0/9 ⇒ FAIL）+ V3 `ref_plane_continuity` **pending** ⇒ 未在岗 | **未闭** |
@@ -87,7 +87,7 @@
 | F-9 | 走廊口径两套未对账（0.25 / 0.41mm 差） | `k2/pm_gate/artifacts/k2_v4/L2/frozen/L2_STRUCTURE_v2.0.md`（走廊表）vs 板实测 | **未修**（P3 图纸采用板侧实测口径；L2 冻结表未回改 —— 改冻结件须 owner 批）；P4 仅对齐 ESC keepout 口径（`K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md`） | `keepout_active`（草案）—— 未在岗 | **未闭** |
 | F-10 | `NO_CONNECT` 建成真实网 ⇒ 26 对假未连接 | 生成器 `assign_nets` 未落 no-net = **G-ROOT-1 同族（真源声明侧）** | **未修**（草案 errata-2「+nc 105 −nets.PWR_5V_KEY」未安装） | `unconnected_zero` + `net_declared_realized`（草案/冻结）—— 未在岗 | **未闭** |
 | F-11 | 3D 模型 origin 未补偿 ⇒ 3.81mm 偏移 | `k2/tools/k2_render_3d.py:79-81` | **未修**（计划 §1.3 **OUT #5**：3D 预览不阻塞可制造性，排在 P4 之后） | 「不适用」+ 替代判据 = J-8 器件重叠（pending） | **OUT（具名）** |
-| F-12 | 无 `fp-lib-table`；7 个未标注 refdes | 仓库缺文件（已修）+ `hw/sch/*`（未修） | **部分修**：`k2/hw/fp-lib-table` `d731638859be9a08`（F-12 库表侧闭）；**7 个未标注 refdes 未修**（见 N-07） | `fp_lib_table_present`（草案，库表侧）—— 未在岗 | **未闭** |
+| F-12 | 无 `fp-lib-table`；7 个未标注 refdes | 仓库缺文件（已修）+ `hw/sch/*`（未修） | **载体已修**：`k2/hw/fp-lib-table` `d731638859be9a08`（库表侧；DRC `lib_footprint_issues` 6→0）；refdes 侧＝**伪缺陷**（见 `N-07`/§12.1） | `fp_lib_table_present`（草案，库表侧）—— 未在岗 | **未闭**（载体已修） |
 | F-13 | k2 无 `pipeline.yaml`；两个核对器零调用 | `k2/pipeline.yaml`（缺）；`_shared/eda_core/{netlist_parity,board_spec_consistency}.py` | **未修**（草案 `pipeline.yaml.draft` 已备；安装属 gate 属主） | `pipeline_present`（冻结 + 草案 scope=k2）—— 未在岗 | **未闭** |
 | F-14 | 生成器输入缺失 ⇒ 不可复跑 | `k2/tools/k2_gen_v5.py:39/44-47`（`YAML_PATH` 硬编码 + `boards/k2_sch.yaml` symlink 兜底；`PCB_REF_PATH` 仍指锚板）= **G-ROOT-3** | **未修**（R4 以 symlink 消 `FileNotFoundError`，属**兜底绕过**《宪法》第九条禁；E4 两次 sha 相同**未达成**） | E4 判据（产���两次 sha 相同 + refdes==42 + 板框 46mm）**未实现/未在岗** | **未闭** |
 
@@ -103,7 +103,7 @@
 | N-04 | `netlist_parity.py`（自带 `--fail-on-pin-mismatch`）与 `board_spec_consistency.py` 已建、**K2 零调用** | `_shared/eda_core/{netlist_parity,board_spec_consistency}.py`（已建）+ `k2/pipeline.yaml`（缺） | **未修**（接线 = gate 安装项） | `pipeline_present` + 必选三联 `sch_structural/netlist_connect/bom_consistent`（`required.py` meta-gate）—— 未在岗 | **未闭** |
 | N-05 | 生成器不可复跑：冻结输入 `k2_v4.kicad_pcb`、`boards/k2_sch.yaml` 当时不存在 | `k2/tools/k2_gen_v5.py:39/44-47` = **G-ROOT-3** | **部分修**：R4 建两个 symlink（消 I1/I3 `FileNotFoundError`）⇒ 前进到下一阻断；**E4 ≠ 归零**（另三项生成器根因：板框已修 / SPEC 路径已修 / refdes 集已修，余 anchor pad + 锚板输入） | E4 判据（`K2_OUT_PCB` 两次 sha 相同）**未实现/未在岗** | **未闭** |
 | N-06 | 打开被关的 9 条规则后 DRC **42→131**，其中 `via_dangling` **17** 条被静默 | `hw/…l4.kicad_pro: rule_severities` | **载体已修**：ignore 9→0（l5 pro `d5e0ca06…`）+ W-7 `via_dangling` **12→0** + `tncv` 30→0 | `rule_severity_manifest` + `drc_errors` + `drc_warning_dispositions`（冻结/草案）—— 未在岗 | **未闭**（载体已修） |
-| N-07 | 原理图仍有 **7 个未标注 refdes**（`C?/D?/E?/J?/L?/R?/U?`） | `k2/hw/sch/*.kicad_sch`（本会话复算：`connectors` 2 · `mcu_sideband` 3 · `power_12v…` 1 · 另 1） | **未修**（7 个 `?` 仍在） | 无判据（`refdes_sets_equal` 不抓 `?`；ERC/结构检查未接入） | **未闭** |
+| N-07 | 原理图仍有 **7 个未标注 refdes**（`C?/D?/E?/J?/L?/R?/U?`） | `k2/hw/sch/*.kicad_sch`（本会话复算：`connectors` 2 · `mcu_sideband` 3 · `power_12v…` 1 · 另 1） | **载体无需修**：排除 `(lib_symbols …)` 子树后**实例未标注 = 0**（55 实例全标注）；31 个 `?` 全在 `lib_symbols` 定义占位；netlist `?` = **0** / 705 ref 条目 | 无判据（`refdes_sets_equal` 不抓 `?`；ERC/结构检查未接入） | **OUT（具名：前提实测不成立）** |
 
 ---
 
@@ -170,7 +170,7 @@
 1. **⑥ L2 增量**（在办）：候选板 `b2cfb087839afd73` 已出，**待监理放行落板**（见 inc37 §1）。
 2. **本表（证据件）** ⇒ 监理判。
 3. **G-ROOT-1/2/3**：§6 三项方案**须监理放行**改生成器源码（G9/G10/G11）+ 逐项 E4/V2/J-3/J-8 复算。
-4. **其余 27 条载体未修**：`U-03/U-04/U-07`（随 ⑦ 库侧裁定 + G9）· `U-09/M-12/J-8`（密度判据实现）· `M-02/N-07`（README/原理图未标注 refdes 清理，纯文本/符号编辑）·
+4. **其余 27 条载体未修**：`U-03/U-04/U-07`（随 ⑦ 库侧裁定 + G9）· `U-09/M-12/J-8`（密度判据实现）·
    `M-03/M-06/M-17/F-10`（errata-2 ncf 声明安装）· `M-07/M-13/F-13/N-04/J-9`（`pipeline.yaml` + 判据安装，**gate 属主**）·
    `N-03`（pro `sheets` 接线）· `N-01`（P4 关门后出 Gerber）。
 5. **判据在岗**：安装 `criteria/` 两份新版（②④⑤/J-7b/J-8/V3）+ `k2/pipeline.yaml`，监理登记 sha + 锚 `rev=2` + **manifest 签认**
@@ -298,3 +298,17 @@
 **边界**：本节**只读取证**；未改板/pro/库/SPEC/生成器/`criteria/`/真源 yaml/冻结件；未派 WORKER；临时仅 `/tmp/opencode`。
 
 —— ENG（ARCHER）· 2026-09-18 · 探针 `1bd3f4a9d47ff0d4`
+
+## 13. v1.5 增量更新（2026-09-18；**闭环表 3 处修正并入主表**）
+
+> 触发：inc61 §6 实测复核「主表 §1..§11 与 §12.1 自纠表自相矛盾」＋监理采纳三处修正。本节的改动**已并入 §0/§2/§3/§4/§7**（§12 之前的行不再作为「现状」读）。
+> 备份锚：本表 v1.4 快照 sha `2de0dea4f5a5729d`（改动前）。
+
+| # | 条 | 改动 | 依据（实测） |
+|---|---|---|---|
+| 1 | `M-02` | 主表 ④「未修」→「**载体已修**」（三文件 sha 登记）；⑥ →「未闭（载体已修）」 | `DS160PR810`/`dual`/`双颗`/`U3`/`U7` 在三文件命中 = 0；`DS320PR1601` 4+1 次 |
+| 2 | `F-12` | 主表 ④「部分修」→「**载体已修**」（库表侧 ＋ refdes 侧＝伪缺陷） | `fp-lib-table` `d731638859be9a08` 存在且 DRC 采信（`lib_footprint_issues` 6→0） |
+| 3 | `N-07` | 主表 ④「未修」→「**载体无需修**」；⑥ →「**OUT（具名：前提实测不成立）**」；并移出 §0「载体未修」清单 | 排除 `(lib_symbols …)` 后实例未标注 = 0；netlist `?` = 0 / 705 ref 条目 |
+
+**计数（并入后）**：根闭 **0** · OUT（具名）**5** · 未闭 **54**；其中「载体已修」**17** · 「判据已实现待安装」**10** · 「载体未修」**27**。
+**未动**：`N-03`（悬挂指针，处置待裁，见 `K2-P4-QUEUE10-STATE-AND-CALIBER-DATA-v1.md` §2）与其余 26 条载体未修项。
```

## 3. 一致性机检（只读；对 v1.4 现状 与 v1.5 提案）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/closure_table_consistency_check.py k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md                            # 现状 ⇒ 期望 FAIL
python3 /tmp/opencode/inc63/closure_table_consistency_check.py /tmp/opencode/inc63/closure_table.v1.5.proposed.md                 # 提案 ⇒ 期望 PASS
```
实测输出：
```
== v1.4（现状）  根闭 0 | OUT 4 4 | 未闭 55 | 载体已修 15 15 | 判据已实现 10 | 载体未修 30 30
   一致性: FAIL -> M-02 仍在「载体未修」清单; F-12 仍在「载体未修」清单; N-07 仍在「载体未修」清单; N-07 不在 OUT 清单   (rc=1)
== v1.5（提案）  根闭 0 | OUT 5 5 | 未闭 54 | 载体已修 17 17 | 判据已实现 10 | 载体未修 27 27
   一致性: PASS   (rc=0)
```

## 4. 采纳后的后续（与 P4 关门链的关系）

1. **只解决「表内自相矛盾」**，不改变任何**载体**状态；`根闭` 仍为 **0**（④「防复发判据在岗」未满足）。
2. 采纳后本表才可作为 **#K2-22 §三「闭环表全闭」** 的有效读数；`根闭` 资格仍取决于 **判据安装（`criteria/` 两份新版 + `k2/pipeline.yaml`）+ 监理签认锚 rev**。
3. 与 §12.2 的既有修正口径**合并为同一版本**（避免 v1.5 与 §12.2 两处并存再次自相矛盾）。

## 5. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
sha256sum k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md                    # 期望 2de0dea4f5a5729d（前提：未改）
python3 /tmp/opencode/inc63/closure_table_consistency_check.py <表>     # 见 §3
diff -u k2/docs/K2-ROOT-CAUSE-CLOSURE-TABLE-v1.md /tmp/opencode/inc63/closure_table.v1.5.proposed.md | head -80
```

## 6. 边界

本件**只读 + `/tmp` 提案件**：未改闭环表/SPEC/图纸/板/pro/真源/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 闭环表 v1.4 `2de0dea4f5a5729d` · 提案 `86e73a061e57f5d4`
