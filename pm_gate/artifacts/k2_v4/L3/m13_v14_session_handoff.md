# M13 v14 续接 — GAP 验证闭环 + escape_learner 判据修复（AIC 案例数据纠正）

> 权威承接（按序读）：
> ① `m13_mcio_escape_landing_gap_problem.md`（GAP 问题定义 v1，本次验证对象）
> ② 本文档（本 session 状态 + 临时资产 + 方法论）
> ③ `_shared/docs/CASE_LEARNING_SYSTEM_PLAN.md`（rev2：学人类案例，零 LLM）
> ④ `_shared/docs/LAYER3_FEASIBILITY_CLOSURE_DESIGN.md`（层3 闭环 D1-D4）

## 0. 本 session 已完成（全部 commit/push 勿重做）

| # | 内容 | 证据 |
|---|---|---|
| 1 | **GAP 验证闭环**：真板 MCIO 单区诊断 16/16 落点 x=69.8（<75 电容墙），SPEC in2_crossing_nets via1 x≥79.38（6 网）——拓扑顺序错误实锤 | 诊断 `/tmp/opencode/mcio_diag/escape_landing_report.json`；单测 t13/t14（`_shared/eda_core/tests/test_escape_landing.py`） |
| 2 | **根因归属**：escape_landing `analyze_pad_heap` 把连接器列+电容列+U3 列聚成单堆，gap_center=69.8 悬在电容前空隙；`_candidates` GAP 首候选 first-clear-wins；`corridor_bound_x` 仅报告不 gate | 代码 L351-455/800-802 |
| 3 | **escape_learner 判据修复**（AIC 案例数据纠正）：`cap_fp_re` 兼容 PADS 裸尺寸码（`0402`）；新增 `_diff_base` 归一化（`S4_TX3CN`/`S4_TX3N`→同 base `S4_TX3`）；`_ac_shape` 分母改参与耦合 lane 数 | `_shared/eda_core/escape_learner.py`；单测 `TestAicStyleCriteria` |
| 4 | **AIC 真板重解析**：ac_coupling null→193 颗（97 lane ×2 颗，物理吻合）；diff_pairs 18→239；length F.Cu 20mm→10963mm（旧数据失真） | kb `learned_aic_pex88096_10slimsas` v3 |
| 5 | **AIC 形态验证**：短链表层直连（S3_TX0：switch→AC1 电容→CN1 全 F.Cu）+ 长链电容后换层（S0_TX0：U2→F.Cu→FC36 电容→via 紧贴下游换 B.Cu）——**AC 电容在信号路径上、换层点紧贴电容下游**，K2 所需形态参考确立 | pciesw4/aic/aic.kicad_pcb 逐链追踪 |

## 1. 案例选择结论（用户确认口径：学相同拓扑约束的成功案例）

- **AIC（PEX88096_AIC_GEN4_10SLIMSAS_EVM）形态匹配成立**（learner 修复后 193 颗 AC 耦合检出）
- OpenCAPI **排除**：规范 DC 耦合无 AC 电容（ac_coupling=null 是真值非漏检）
- PEX8748_2SLIMSAS_4NGFF_GEN3（PEX8748_NVME_EVM）**数据已下载**（见 §3），待解析验证

## 2. 关键文件/状态

- `_shared/eda_core/escape_learner.py`（本次改：DEFAULT_PARAMS + `_diff_base` + `_ac_coupling` + `_ac_shape` + `_layer_assignment`）
- `_shared/eda_core/tests/test_escape_learner.py`（+`TestAicStyleCriteria` 2 测试）
- `_shared/eda_core/tests/test_escape_landing.py`（+t13/t14 GAP 锁定）
- `_shared/knowledge/kb.sqlite3`（learned_aic_pex88096_10slimsas v3）
- `pciesw4/aic/aic.kicad_pcb`（AIC 完整板 37MB PADS 导入，167148 段——只读参考源）

## 3. 临时资产（已归档 / 需知路径）

| 资产 | 路径 | 说明 |
|---|---|---|
| PEX8748 工程原始数据（PCB 2.8MB + 14 原理图，EasyEDA Pro dataStr） | **`_shared/knowledge/cases/PEX8748_2SLIMSAS_4NGFF_GEN3/`**（已 commit） | PCB=`PEX8748_NVME_EVM.pcb.eda_pro`，sch=14 个 `.sch` |
| MCIO 单区诊断报告 | `/tmp/opencode/mcio_diag/`（未 commit，可重跑） | 真板 MCIO landing 16 落点 x=69.8 |
| Firefox 登录 profile 副本 | `/tmp/opencode/ff_profile_copy/`（323MB，**不 commit**） | oshwhub 登录 cookie 载体，headless 下载用 |
| AIC 重解析 v3 JSON | `/tmp/opencode/aic_reparse_v3.json`（可重跑 CLI 生成） | 与 kb v3 同源 |
| AIC/GPU PADS 源 + 转换 | `/tmp/opencode/pads_import/` + `pciesw4/_import/` | PADS .asc 源，历史下载 |

**丢弃**：`/tmp/opencode/pex8748_raw/pex8748_nvme_evm.kicad_pcb`（2038B 空导入假成功产物，勿用）。

## 4. oshwhub 工程数据下载方法论（复用，勿重新逆向）

**结论：KiCad 10.0.5 稳定版 PCB_IO_MGR 含 EASYEDA(9)/EASYEDAPRO(10)/PADS(17) 导入器**（用户指正）。
但裸 dataStr 直接 Load EASYEDAPRO 是**空导入假成功**（10.0.5 只含 v2 解析器，dataStr 是 v3 格式）。

**已验证可用链路（取工程数据）**：
1. 登录 oshwhub（Firefox）→ cookie 在 `~/.mozilla/firefox/*.default-release/cookies.sqlite`
2. 复制 profile → headless firefox 执行 fetch（过 CloudWAF，curl 会被拦）
3. 工程详情 `GET /api/project/{projectId}`（页面 RSC 挖出 uuid）
4. 文档数据 `POST /api/v2/documents/lists` body `{project_uuid, page, pageSize}` → 响应 result[].dataStr（行式 JSON `["DOCTYPE","PCB","1.7"]`）
5. 关键 ID：PEX8748 projectId=`3e7667e620664884b5601a9ac67f8540`，PCB doc=`47e7fbc12f294c4d80f2b742f5be94e7`

**待验证路径**：dataStr → 还原 .epro2 容器（project2.json + .epru）→ 喂 KiCad master v3 解析器（源码 `/tmp/opencode/kicad-src/common/io/easyedapro/`）；或 JLC EDA 编辑器内"导出 PADS"（pciesw4 历史路径，AIC 就是这么来的）。

## 5. 铁律提醒（继承）

- 预期 = 独立可行性研究（真板几何 + SPEC）；问题回模型；零单板特判；确定性；假成功零容忍
- 学案例 ≠ 修引擎（Phase D 停）；「学」= 确定性解析器提取拓扑构造，LLM 只设计+开发系统
- 改 `_shared/eda_core` 保持通用（零 K2 坐标/网名特判；本次 `_diff_base` 是命名形态学泛化非板特判）
