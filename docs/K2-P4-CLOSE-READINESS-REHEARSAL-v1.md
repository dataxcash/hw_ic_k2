# K2 · P4 · **关门预演**（落件 + 库重指 + SPEC bump + 门禁接线 ⇒ 判定器 17P/0F）· 证据件 v1 · 2026-09-18

> 缘起：P4 判据集最后一个 FAIL（`pipeline_present`）已证明只是安装动作（inc41）；落地侧的**唯一机械缺口**是
> 「板 sha 变更 ⇒ 需 SPEC 版本 bump（pre-commit `check_pcb_spec_correlation`）」。本件补上该器，并在**沙箱**
> 把 P4 关门状态**预演一遍**（仓库零写入；判定归监理）。

## 0. 新增落件前置器

`k2/tools/k2_p4_spec_rev_bump_v1.py` sha256 前16 = **`4bd5931ab9f43806`**（dry-run 默认；T-22/T-41）。
三件事：① 把 `pd` 子树内 `ref ∈ --moved-refs` 且含 `pad_pos` 的**现行**叶（**跳过 `retired_*` 历史块**）
按**落件板实际几何**重派生 `pad_pos`/`via_pos`；② 新 rev = 旧 rev + `_spec_rev_<k>`（实况记录）+ `spec_version` bump；
③ `project.yaml` 的 `spec_name` 同步。**不写板、不写库、不动 `criteria/`、旧 rev 永不改**（机制沿复合落件器 v2）。

**SPEC bump 实况（dry-run 预览 + 沙箱直落，`spec-rev-47 → 48`）**：

| 项 | 值 |
|---|---|
| `pd` 对齐（现行叶） | **2 处**：`pd/zone_defs/power_pad_connect/entries[142]` `U4.pad2`（MCU_VDD）`pad_pos [40.95,37.95] → [40.95,38.9]` · `entries[150]` `U4.pad3`（P3V3）`pad_pos [40.0,36.05] → [40.0,37.0]`；两处 `via_pos` 不变（via 未随件移动） |
| `retired_*` 历史块 | **不动**（4 叶保持原值，历史不改写） |
| 值校验（独立） | rev-48 的 `U4` 两叶 `pad_pos` 与落件板 `U4` 实际 pad 中心**逐位相同**（2/2） |
| `spec_version` | `1.1.spec-rev-47 → 1.1.spec-rev-48` |
| 新增键 | `_spec_rev_48`（card=`SPEC-REV-48（P4 ⑥+⑦）`，含移动件/对齐明细/板 sha/库 digest/确定性说明） |
| `project.yaml` | `SPEC_k2_v4.spec-rev-47.json → SPEC_k2_v4.spec-rev-48.json`（`9cee872bd6fbdc67 → e9ab1209cdb56b11`） |
| 旧 rev | **字节未变**（`9ba09cbc148d6836` 前后一致，T-22） |
| 新 rev sha16 | `792cfb3b40980704`（沙箱实际落盘 + dry-run 预览同值） |
| 覆盖面核查 | SPEC 内 **全部** per-ref 坐标叶都在 `pd`（807 叶）；移动件中 `U4` 6 叶（2 现行 + 4 retired）、`D2`/`L1` **0 叶** ⇒ 无遗漏项 |

## 1. pre-commit 相关性闸的**精确语义**（决定是否必须 rev-48）

`_shared/eda_core/pipeline/checks.py:363-384`（`check_pcb_spec_correlation(staged)`）：
只看两件事 —— staged 里**是否有** `*.kicad_pcb`（纯改名除外）与**是否有** `_is_spec_change(p)`
（`SPEC_*.json` / `artifacts/L3/*.json`）⇒ **不做坐标比对**（亦见 ledger 664 §④）。故两种提交序：

- **(甲) 同笔提交**：⑥+⑦ 落件与**在库未提交的 rev-47 bump**（`SPEC_…rev-47.json` + `project.yaml`）同笔入库
  ⇒ 相关性已满足，**无需 rev-48**（本器不必动用）。
- **(乙) 分笔提交**：rev-47 先入库、⑥+⑦ 落件另笔 ⇒ **必须有 SPEC 变更** ⇒ 用本器落 **rev-48**（上表）。

⚠️ 现状提醒（承接 inc39/40/41 旁证）：仓库当前 `hw/k2_v4_8L.l5.kicad_pcb`（`6ff49da5678c2108`）、
`pm_gate/project.yaml`、`SPEC_…spec-rev-47.json` **均未提交/未跟踪** ⇒ 属 (甲) 语义。

## 2. **P4 关门沙箱预演**（`/tmp/opencode/p4rehearse/`，仓库零写入）

树 = 落件板（复合候选 `9682dd026f48c04a`）+ 落件 pro（`d5e0ca067a7b585e`）+ **快照库 27 件** + `fp-lib-table`
+ **SPEC rev-48** + `project.yaml→rev-48` + **合规 `k2/pipeline.yaml`**（`b74d1f1e883c2ca3`）+ `sch/` + `data/errata-1`。

| 复算 | 结果 |
|---|---|
| 草案 v4 判定器 | **17 PASS / 0 FAIL**（`=> PASS（PROVISIONAL：manifest 未经监理签认）`） |
| 关键项 | `drc_errors` error=0（**违规总 0**）· `unconnected_zero` 0 · `lib_electrical_level` 0+0 · `fp_lib_table_present` 存在 · `pipeline_present` 未覆盖目录 0 · `zone_filled` 10/10 · `drill_count` NPTH=4/PTH=16 |
| 框架 meta-gate | `check_all_projects_coverage()` = **PASS**「全部 1 项目 sch 必选检查声明完整」 |
| `pipeline verify k2` | 仍会在 `netlist_connect` 处**中断**（`k2/hw/data/k2_sch.errata-2.yaml` 不在库）—— 属 inc41 §3 已登记前提（errata-2/BOM 提升）+ 缺陷 D-2（引擎缺件未 fail-closed），**不阻塞判据 `pipeline_present`** |

⇒ **P4 关门状态已可复现**：除「manifest 签认」外无任何未证明项；剩余全部是**监理放行动作**（落件 / W-8 口径 / pipeline 安装 / 签认）。

## 3. 复跑链（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli
# ① 复合候选（inc40）
$K k2/tools/k2_p4_l2_placement_courtyard_v1.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
   --kicad-cli $CLI --work-dir /tmp/opencode/p4final/a6        # b2cfb087839afd73
$K k2/tools/k2_p4_lib_snapshot_v1.py --board /tmp/opencode/p4final/a6/k2_v4_8L.l5.l2-placed.kicad_pcb \
   --pro k2/hw/k2_v4_8L.l5.kicad_pro --kicad-cli $CLI --work-dir /tmp/opencode/p4final/b7   # 9682dd026f48c04a
# ② SPEC bump（dry-run 先看预览；沙箱用 --spec-dir/--project-yaml 指向副本，禁止在库预演）
$K k2/tools/k2_p4_spec_rev_bump_v1.py --board /tmp/opencode/p4final/b7/k2_v4_8L.l5.l2-placed.libsnap.kicad_pcb \
   --spec-base k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json \
   --spec-new  k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-48.json \
   --project-yaml k2/pm_gate/project.yaml --moved-refs D2,L1,U4 --new-rev 48 \
   --lib-digest a63fff0769f0d0c5 --work-dir /tmp/opencode/p4final/spec48
# ③ 预演（树构成见 §2）+ 判定器（--root 指向预演树）
python3 k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py --board /tmp/opencode/p4rehearse/k2/hw/k2_v4_8L.l5.kicad_pcb \
  --manifest k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml --pro /tmp/opencode/p4rehearse/k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --drc-cli $CLI --drc-work-dir /tmp/opencode/p4rehearse/adj/drcwd \
  --root /tmp/opencode/p4rehearse --w8-audit-json <W8v2> --pads-outline-json <PADS> --out /tmp/opencode/p4rehearse/adj/verdict.json
```

## 4. 边界

仓库板/pro/库/`fp-lib-table`/`criteria/` 两份/`_shared/**`/SPEC rev-19..47 原件/`k2/pipeline.yaml`（**未创建**）/
`project.yaml`（未改）**均未动**；本件的 rev-48 只落在 `/tmp`；未派 WORKER；临时仅 `/tmp/opencode`。

—— ENG（ARCHER）· 2026-09-18 · 器 `4bd5931ab9f43806` · 预演 = 17P/0F（PROVISIONAL）
