# K2 · P4 · **复合落件器 v1**（supersedes W-7 落件器）+ 两项核查更正 · 2026-09-18

> 性质：ENG 交**落件器（工具）+ 沙箱 `--apply` 全链实证**；**未写仓库**（板 / pro / SPEC / `project.yaml` / `criteria` 逐字节未动，见 §3）。
> 目的：把「W-7 修复 → PDN 接线 → tncv 对齐 → C86 重落位」的**复合结果板**做成**批准后一笔落**，
> 并让新 rev 的 `pd` 与落地板**几何自洽**。
> 工具：`k2/tools/k2_p4_composed_land_v1.py` sha256 前16 **`41740377fd2dca19`**（dry-run 默认）。

## 0. 一句话

复合落件器在**沙箱**完成 `--apply` 全链：板落 `686e9c2b1768c5d3`、**dst pro 逐字节不变**（T-22）、
新增 **SPEC rev-47**（`9c5aadc84f3dbd3b`）、`project.yaml` bump、**落件后 DRC（仓库 pro 语义）= error 0 / warning 35 / unconnected 0**。

## 1. 落件器做了什么

| 步 | 内容 |
|---|---|
| A 前置 fail-closed | 仓库板 `37019705ef994ccc` / pro `f68a5fb2f82bd02d` / canonical rev-46 `dea36093ba2b4031` / `criteria` 两份 sha 全对；结果板 sha 指定；rev-47 不存在；结果板 DRC error 0 且 unconnected 0 |
| B1 | 备份 src 板/pro 字节 → 写板 → **校验 dst pro 逐字节不变**（不符即回滚，T-22） |
| B2 | **SPEC rev-47** = rev-46 + `_spec_rev_37`（**按复合实况**的变更记录：5 类 181→79 · `via_dangling` 0 · `tncv` 0 · C86 重落位）+ `spec_version` bump + **`pd` 内 `C86` 的 `pad_pos`/`via_pos` 对齐**（**由落地板几何派生**，非硬编码） |
| B3 | `project.yaml.spec_name` → rev-47 |
| C | 落件后 DRC 复核（仓库 pro 语义） |

`pd` 对齐只改**现行**叶（`pd/zone_defs/power_pad_connect/entries[11]`/`[134]`）⇒
`C86.2 GND` pad(32.000,58.850)/via(32.775,58.850) · `C86.1 MCU_VDD` pad(31.100,58.850)/via(30.325,58.850)；
**`retired_superseded_*` 历史块 4 叶保持原值**（31.05/31.95, 56.0）—— 历史不改写。

## 2. 沙箱 `--apply` 实证（仓外全树副本）

| 项 | 实测 |
|---|---|
| 板落件 | `/tmp/opencode/land-sbx/hw/k2_v4_8L.l5.kicad_pcb` = **`686e9c2b1768c5d3`** |
| dst pro | 逐字节不变（T-22） |
| SPEC rev-47 | 新建 `9c5aadc84f3dbd3b`；`spec_version=1.1.spec-rev-47`；`_spec_rev_37.card="SPEC-REV-37（复合）"` |
| `project.yaml` | `9cee872bd6fbdc67`（spec_name → rev-47） |
| **落件后 DRC（仓库 pro 语义）** | **error 0 / warning 35（`lib_footprint_mismatch`）/ unconnected 0** |

## 3. 仓库未动核验

板 `37019705ef994ccc` · pro `f68a5fb2f82bd02d` · rev-46 `dea36093ba2b4031` · `project.yaml` `eb6179f5da08912e` **全未变**；
仓库内**不存在** rev-47。落件器在**仓外副本**上验证，无仓库写入。

## 4. 两项核查更正（self-correction）

1. **上一笔的过强断言更正**：「`pd` 未对齐 ⇒ *PCB↔SPEC 1:1* pre-commit 会失败」**不准确**。
   实读 `k2/_shared/eda_core/pipeline/hooks/pre-commit` 与 `eda_core.pipeline.checks.check_pcb_spec_correlation`：
   该检查**只要求** `.kicad_pcb` 变更**伴随**同笔 SPEC 变更，**不做坐标级比对**。
   故 `pd` 对齐属**一致性 / 规划数据**修正（仍必要：`pd` 是后续 PDN 施工的输入），**不是门禁项**。
2. **via span 审计（负结果，非缺陷）**：实测 span 分布 = `F→In1` 130 · `F→In2` 127 · `F→In4` 4 · `F→In5` 16 · `F→B` 310 · `In2→In5` 92 · `In5→B` 32。
   多层跨度（`F→In4`/`F→In5`、`In2→In5`、`In5→B`）**已登记于 SPEC / 层计划**（信号层 = F/In2/In5/B；
   `In2→In5` 与 `F→In2` 换层是 P4 已批准布线路径；rev-30/32 明写新增 `F→In4` 盲孔）⇒ **不是缺陷**，无需停机。

## 5. 批准后的一键落件

```bash
AppDir/usr/bin/python3.11 k2/tools/k2_p4_composed_land_v1.py \
  --result-board /tmp/opencode/c86-6/k2_v4_8L.l5.repaired.pdn-stitched.tncv-aligned.c86-relocated.kicad_pcb \
  --result-sha16 686e9c2b1768c5d3 --apply --confirm-repo-write
```
（`/tmp` 易失；复合结果板可由确定性链重建：W-7 → PDN → tncv → C86，各步 sha 见对应交件。）


## 6. 事故与硬化（T-41，自曝）

**事故（本轮，已完全还原）**：写本文件的父命令**误用未加引号的 heredoc 分隔符**，shell 把文件内容里的示例命令当命令执行，
其中 `k2_p4_composed_land_v1.py … --apply`（**未带沙箱路径覆盖，即默认仓库路径**）被实际运行
⇒ **未经批准把复合板落进仓库**：板 `37019705ef994ccc → 686e9c2b1768c5d3`、新建 `SPEC_k2_v4.spec-rev-47.json`、
`project.yaml` bump（当时尚无复核、无 SPEC pd 对齐确认）。

**发现与还原**：比对 inode / 时间戳 / sha 定位来源后，`git -C k2 checkout HEAD -- hw/k2_v4_8L.l5.kicad_pcb pm_gate/project.yaml`
+ 删除未跟踪的 rev-47，**逐字节还原**；复核：板 `37019705ef994ccc` · pro `f68a5fb2f82bd02d` · rev-46 `dea36093ba2b4031` ·
`project.yaml` `eb6179f5da08912e` · 仓库内无 rev-47 · `git -C k2 status` 仅余本会话前既有的未跟踪 `hw/k2_v4_8L.l5.kicad_prl`；
**12 项冻结源全部一致**（`l4` 未受影响）。

**硬化（T-41）**：`--apply` 现在必须**同时**给 `--confirm-repo-write`，否则 fail-closed 拒绝（实测拒绝生效，且仓库板仍 `37019705…`）。
带旗标的沙箱 `--apply` 复跑仍**逐字节同**：板 `686e9c2b1768c5d3` / rev-47 `9c5aadc84f3dbd3b` / `project.yaml` `9cee872bd6fbdc67`。

**教训**：① 文档/脚本里的示例命令必须写在**加引号**的 heredoc（`<<'EOF'`）内，否则 `$`、`` ` ``、反斜杠续行会被 shell 展开并可能**执行**；
② 任何会写仓库的工具都要有**独立的二次确认旗标**——不能只靠「默认 dry-run」，因为示例命令常带 `--apply`。

—— ENG（ARCHER）· 2026-09-18 · 仓库板 / pro / SPEC / 判据**未动** · 未派 WORKER · 临时仅 `/tmp/opencode`
