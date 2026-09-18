# K2 · P4 · **`W-8` 安装归属草案**（放置帧归一：安装对象 / 登记 / 依赖 / 三案正负控）· v1 · 2026-09-18

> 缘起：handoff inc67 §6-3-(s)「`W-8` **安装归属草案**（§5-10 待裁采纳/驳回 + 安装归属；接 inc61 §5 三案正负控，纯文档/草案）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + 引用既有 `/tmp` 实测**，仓库零载体改动（仅新增本证据件）。
> 锚：现安装件 `k2/tools/k2_w8_footprint_audit_v1.py` **`75404d706413d546`** · 草案件 `k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py` **`34b83cff5fe8ade7`**（README `45c2e411d9a8ae60`）· 判据草案 `…/manifest.k2.v3.yaml`（`lib_electrical_level: {consume: w8_audit_json, …}`）· 判据安装件 `criteria/manifest.k2.yaml` **`7ce08757eff25557`**（**9 维、不含 `lib_electrical_level`**）。
> **归属**：采纳/驳回＝「判据语义澄清」＝**监理职权**；安装＝**gate 属主侧**；ENG 只出安装面草案、最小改动清单与复现证据，**不择一、不安装**。

## 0. 结论（六条）

1. **`W-8` 是「判据口径修正」，不是载体缺陷修复**：v1 直比**文件内存储值**（`GetFPRelativePosition`/`GetOrientationDegrees`）⇒ 对「有旋转」（板存绝对 pad 朝向、库存局部）与「背面镜像」（板存镜像后偏移）两类**放置约定差异**误报；v2 把库件**按板位姿放置**后在放置帧内取电气签名。
2. **安装对象与最小改动**：`k2/tools/k2_w8_footprint_audit_v1.py` → 版本 bump 到 **v2**。实测 v1→v2 仅 **3 处差异**：① 新增 `_SCRATCH = pcbnew.BOARD()` ＋ `posed_pad_sig()`；② 把 `lib = pad_sig(lfp)` 换成 `lib = posed_pad_sig(fp, lfp)`；③ **仅为草案目录可用**的 `--std-root` 六级上溯查找 ⇒ **安装到 `tools/` 时应还原为原 `../../AppDir/...` 默认**（否则带无关代码）。
3. **消费面与登记**：判据侧 `lib_electrical_level` 的期望式为 `n_electrical_diff == 0 且 n_pad_name_set_only == 0（以板为准）`，并且**审计 JSON 的 `board_sha16` 必须 == 受审板 sha16**（证据陈旧 ⇒ fail-closed）。安装须由监理**登记新 sha + 锚 rev**；`criteria/manifest.k2.yaml` 现为 **9 维且不含该维** ⇒ 该维上线须随判据安装件（草案 v2/v3）一并签认（`not_countersigned → false`）。
4. **关键依赖：单采 `W-8` 不会让本板 PASS** —— 当前板（仓库库）基线为 **33 件真实 land pattern 差异**；只有**⑦ 库按板重建** ＋ `W-8` v2 才使该维 PASS（6+7 复合候选实测：`lib_electrical_level` PASS，仅余 `pipeline_present`）。⇒ **W-8 与 ⑦ 宜同批**，且 `W-8` 本身**不放松**判据。
5. **三案正负控（既有实测，可复跑）**：① 基线 `31+2`(33) → v2 仍 **33 逐件相同**（不放松）· ② ⑦ 候选（按板重建库）`8+0` → **`0+0`** · ③ 合成负控（`C73` pad1 宽 +0.05mm）`9+0` → **`1+0`（恰 `['C73']`）**（真差异仍被抓）。
6. **不新增检查齿（owner ②）**：维度名与期望式**不变**，只替换归一实现（v1→v2）；ENG 未改生成器/判据/工具。

## 1. 安装面清单（最小改动）

| # | 项 | 内容 | 归属 |
|---|---|---|---|
| 1 | 目标载体 | `k2/tools/k2_w8_footprint_audit_v1.py` → **v2**（建议新名 `k2_w8_footprint_audit_v2.py` 或就路径就地升级并由监理登记新 sha） | gate 属主 + 监理登记 |
| 2 | 必需 hunk | `_SCRATCH = pcbnew.BOARD()` ＋ `posed_pad_sig(fp, lfp)`（位置/朝向/`Flip` 背面）＋ 调用点替换 | 同上 |
| 3 | **应删除** hunk | 草案用的 `--std-root` 六级上溯查找（`tools/` 下用原 `../../AppDir/share/kicad/footprints` 即可） | 同上 |
| 4 | 登记 | 新 sha16 ＋ **锚 rev** 递增；判据侧 `lib_electrical_level.consume=w8_audit_json` 不变 | 监理 |
| 5 | 判据安装 | 该维随判据安装件（草案 v2 `0da2fb9d173fac2d` / v3 18 维）安装并签认 | gate 属主 + 监理 |

## 2. 依赖与联合放行顺序（建议）

```
Step 0  监理裁：W-8 采纳/驳回（＋若驳回，另定 lib_electrical_level 口径）
Step 1  ⑦ 库按板重建（G-ROOT-1/⑦ 放行；库 27 件 digest a63fff0769f0d0c5 已备）
Step 2  安装 W-8 v2（tools/，登记 sha + 锚 rev）
Step 3  判据安装件（含 lib_electrical_level / fp_lib_table_present 等）+ manifest 签认
Step 4  以落件板 sha 复算：期望 lib_electrical_level PASS（6+7 复合候选口径）
```
**若驳回**：`lib_electrical_level` 的 8 件（⑦ 候选口径）须另定口径；否则该维**恒 FAIL**——但差异已证明**非 land pattern 问题**（独立 `placement_equiv` 检查 0 物理差异）。

## 3. 三案正负控（复跑命令，仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; K=AppDir/usr/bin/python3.11
D=k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py
V1=k2/tools/k2_w8_footprint_audit_v1.py
# ① 基线：期望 v1=31+2(33) 与 v2=31+2(33) 逐件相同（不放松）
$K $V1 --board k2/hw/k2_v4_8L.l5.kicad_pcb --proj-lib k2/hw/lib --out-json /tmp/w8v1-base.json --out-md /tmp/w8v1-base.md
$K $D  --board k2/hw/k2_v4_8L.l5.kicad_pcb --proj-lib k2/hw/lib --out-json /tmp/w8v2-base.json --out-md /tmp/w8v2-base.md
# ② ⑦ 候选（按板重建库）+ 合成负控（C73 pad1 宽 +0.05mm）：见 lib-snapshot 件 §复跑
#   期望：候选 v1=8+0 → v2=0+0；负控 v1=9+0 → v2=1+0（恰 ['C73']）
```

## 4. 风险与实现建议（不改语义）

1. `_SCRATCH = pcbnew.BOARD()` 为**模块级全局 scratch**：多次调用共用同一 BOARD；单线程 CLI 下无碍，但若将来并发/复用需改为**每次调用新建**或加锁（**语义不变**，属实现健壮性）。
2. 背面 `Flip(fp.GetPosition(), False)` 的第二个参数（是否翻层）在 KiCad 版本间语义需钉住；本机实测 `pcbnew 10.0.5` 下三案正负控均符合预期 ⇒ 建议安装件**钉 KiCad 版本口径**（与 T-8 同名 pro 纪律一致）。
3. 安装后须**重跑三案**（§3）：基线必须仍 33（防「归一」过度放松），负控必须恰 `['C73']`。

## 5. 边界

本件**只读 + 引用既有 `/tmp` 实测**：未改生成器/工具/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/SPEC/真源/图纸/`criteria/**`/`_shared/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · v1 `75404d706413d546` · v2 `34b83cff5fe8ade7`
