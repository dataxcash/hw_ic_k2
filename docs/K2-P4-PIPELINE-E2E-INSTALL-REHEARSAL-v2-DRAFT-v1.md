# K2 · P4 · **`pipeline.yaml` 安装后「实质在岗」端到端重演 v2**（三项必选 sch 检查全部真执行）· v1 · 2026-09-18

> 缘起：handoff inc71 §6-3-(bb)「`k2/pipeline.yaml` 安装后『实质在岗』端到端重演（容器式路径 + ⑤ 现状 ⇒ 记录唯一失败项与耗时，纯 `/tmp`）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 镜像**，仓库零载体改动（仅新增本证据件）。
> 锚：hook 修正 `pre-commit.d3fix` **`61331e0bb17fa477`** · 全修 engine `a015f8cfcc24c581` · 全修 checks `0cbd9a478c694a12` · 镜像 `/tmp/opencode/inc63/sandbox/e2e`（真 `k2/hw/sch/*.kicad_sch` 复制·`errata-1`·本骨架 BOM·`pipeline.yaml` 变体② 乙）。
> 日志：`/tmp/opencode/inc63/e2e_verify.log`。**归属**：门禁接入＝gate 属主 + 监理；本件只出端到端证据，**不新增检查齿**（owner ②）。

## 0. 结论（四条）

1. **「实质在岗」成立（容器式提交路径）**：一次 hook 运行内，**三项必选 sch 检查全部真被执行** —— `bom_consistent: PASS`（55 器件）· `sch_structural: PASS` · `netlist_connect: FAIL`；另有 `preflight/check[project_sch_coverage]: PASS`（**该行只在 `D-4b` 之后可能出现**）。
2. **失败项唯一＝⑤**：`网 'PWR_5V_KEY' 在 KiCad netlist 中不存在` ＋ `非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单` ⇒ `rc=1` 拒绝提交（与 inc58 案 B 逐字一致）。
3. **耗时**：整次 hook（全局 sch 完整性 + meta-gate + 过程门禁 + 受影响项目 + verify 三项）＝ **1.4 s**（本地、镜像树）⇒ 提交期开销可接受。
4. **顺序效应（与真载体的差异，须明示）**：本件在**沙箱探针**里把 `bom_consistent` 前移，以便一次跑全三项；**真载体顺序**下 `cmd_verify` 首个 FAIL 即 `return 1` ⇒ `bom_consistent` **不会被执行**（见 inc64 §0-4）。⇒ 若监理要「三项全可见」，须在 `D-4b` 语义上明确「全 phase checks 均跑」或调整 verify 顺序（属判据语义，见 inc57 §2 / inc65 (o) 件）。

## 1. 装置（镜像 + 沙箱探针）

| 组件 | 值 |
|---|---|
| 镜像树 | `/tmp/opencode/inc63/sandbox/e2e`（容器式：项目在 `k2/` 子目录、仓根另设 `.git`） |
| `k2/pipeline.yaml` | 变体②（`preflight.checks=[project_sch_coverage]` ＋ 三项必选 sch 检查）；沙箱把顺序改为 `bom_consistent → sch_structural → netlist_connect` |
| 前置件 | `errata-1`（`17d540f058631a5e`）· `k2/fab/k2_v4_bom.csv`（本骨架产出 `9e4ddf4a44302b76`，55 refs 每行一 ref） |
| 判据实现 | 全修 checks `0cbd9a478c694a12`（D-2 缺件 guard ＋ D-7 开关式）· `K2_NC_SOURCES=top,placements`（＝`D-7a` ①②，③ 关） |
| hook | `pre-commit.d3fix`（D-3 修正：`rel=='.'` ＋ 裸 gitlink） |

## 2. 原始输出（全文）

```
[pipeline:pre-commit] 全局 sch 完整性检查 ...
全局 sch 完整性 OK (6 文件)
[pipeline:pre-commit] meta-gate (项目 sch 必选检查声明) ...
全部 1 项目 sch 必选检查声明完整
[pipeline:pre-commit] 过程门禁 (process_gate opt-in) ...
[pipeline:pre-commit] k2: 未启用 process_gate — 跳过过程门禁
[pipeline:pre-commit] 受影响项目: k2
[pipeline:pre-commit] k2 verify ...
  preflight/check[project_sch_coverage]: PASS
  verify/bom_consistent: PASS
  verify/sch_structural: PASS
  verify/netlist_connect: FAIL
    netlist 连接校验失败 2 处:
      网 'PWR_5V_KEY' 在 KiCad netlist 中不存在
      非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单
[pipeline:pre-commit] ✗ verify 未通过 — 拒绝提交 (先按流程修复并验证)
```
`rc=1` · 耗时 **1.4 s**。

## 3. 判读（与「形式 vs 实质在岗」对照）

| 观测 | 含义 |
|---|---|
| `受影响项目: k2` | **D-3 已修**（容器式路径命中；仓根即项目根/裸 gitlink 两支见 inc70 (z) 件） |
| `preflight/check[project_sch_coverage]: PASS` | **D-4b 已修**（`cmd_verify` 读 `checks`；此前该行不可能出现） |
| `bom_consistent / sch_structural / netlist_connect` 三行 | **三项必选 sch 检查真执行** ⇒ J-9「门禁接入」为**实质** |
| 唯一 FAIL ＝ ⑤ 两行 | 与本板既有登记一致（⑤＝**L1，须 owner**）⇒ **门禁有效性已证，阻塞在 ⑤ 而非门禁本身** |

## 4. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; D=/tmp/opencode/inc63/sandbox/e2e
cd $D && SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun K2_NC_SOURCES=top,placements \
  bash /tmp/opencode/inc51/pre-commit.d3fix
# 期望：受影响项目 k2 · preflight PASS · bom_consistent PASS · sch_structural PASS · netlist_connect FAIL(2 行) · rc=1
```

## 5. 边界

本件**只读 + `/tmp` 镜像**：未改 `_shared/**`、判据、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · hook `61331e0bb17fa477` · engine `a015f8cfcc24c581` · checks `0cbd9a478c694a12`
