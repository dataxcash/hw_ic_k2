# M13 v15 续接 — PEX8748 案例解析完成 + AC 电容墙约束形态确立

> 权威承接（按序读）：
> ① `m13_mcio_escape_landing_gap_problem.md`（GAP 问题定义 v1）
> ② `m13_v14_session_handoff.md`（上一 session：escape_learner 判据修复 + AIC 案例确立）
> ③ `_shared/docs/CASE_LEARNING_SYSTEM_PLAN.md`（rev2：学人类案例，零 LLM）
> ④ `_shared/docs/AC_CAP_WALL_ESCAPE_CONSTRAINT.md`（**本 session 新增设计**：电容墙逃逸约束形态）

## 0. 本 session 已完成（commit fbe5eb1 push 至 _shared main，勿重做）

| # | 内容 | 证据 |
|---|---|---|
| 1 | **PEX8748 转 KiCad 成功**：oshwhub 完整工程「工程另存为(本地) V2 .epro」→ `kicad-cli pcb import --format auto` → 11.77MB 真板（807 FP/8826 seg/4423 via/2440 pad） | `/tmp/opencode/pex8748_imported.kicad_pcb`（勿删）；下载脚本见 §3 |
| 2 | **learner 命名形态泛化（+/− 极性）**：`diff_pair_re_suffix` 扩展 `C?([PN+\-])`；`cap_fp_re` 加 `:C\d{4}\|:c\d{4}`（EasyEDA 库:尺寸码）——形态 3 = EasyEDA 导出差分裸名（PEX8748 全板 330 信号网 +/− 极性） | `_shared/eda_core/escape_learner.py`；单测 test_diff_base_normalization 扩展 |
| 3 | **PEX8748 形态验证（真板几何铁证）**：AC 耦合 **96 颗**（48 lane×2）；32/32 带下游 via 耦合电容换层点距 pad **恰 2.172mm**、全 F.Cu→B.Cu、仅 C 侧（chip 远端）——C1 PEI_TX0 逐链追踪 | `/tmp/opencode/verify_direction.py`、`stat_via_dists.py` |
| 4 | **AIC 对照统计**：193 颗耦合中 33 颗带下游 via，距离定点 {0.383,1.151}mm、全 F.Cu→B.Cu、仅 CP/CN 侧——**双板同构确立** | `/tmp/opencode/stat_aic_via2.py` |
| 5 | **落库** `learned_pex8748_2slimsas_4ngff` v1（inferred，source=oshwhub PEX8748 工程页） | `_shared/knowledge/kb.sqlite3` |
| 6 | **设计定稿** `AC_CAP_WALL_ESCAPE_CONSTRAINT.md`：`series_cap_wall` config 声明式约束（轴/方向/墙位置 pads_path 引用/证据引用双案例）——层3 landing 电容墙感知的形态依据 | `_shared/docs/AC_CAP_WALL_ESCAPE_CONSTRAINT.md`（commit） |

## 1. 案例选择结论更新（三案例矩阵）

| 案例 | 拓扑 | AC 耦合 | 换层形态 | 状态 |
|---|---|---|---|---|
| AIC PEX88096 (10×SlimSAS) | switch→AC→SlimSAS | 193 颗 | via 距电容 0.38/1.15mm、F.Cu→B.Cu、仅 CP/CN 侧 | ✅ 已落库 v3 |
| **PEX8748 (2×SlimSAS+4×NGFF)** | switch→AC→8654/M.2 | 96 颗 | via 距电容 2.172mm、F.Cu→B.Cu、仅 C 侧 | ✅ 本 session 落库 |
| OpenCAPI | DC 耦合 | null（真值） | 无电容不适用 | ❌ 排除 |

## 2. 关键文件/状态

- `_shared/eda_core/escape_learner.py`（+形态3 泛化，AIC 回归 193 颗/239 对无变化，27 测试绿）
- `_shared/knowledge/kb.sqlite3`（+learned_pex8748_2slimsas_4ngff v1）
- `_shared/docs/AC_CAP_WALL_ESCAPE_CONSTRAINT.md`（series_cap_wall 设计）
- `_shared/knowledge/cases/PEX8748_2SLIMSAS_4NGFF_GEN3/`（原始 dataStr，已 commit d9b7fc6）

## 3. 临时资产（/tmp/opencode，未 commit；重跑方法见下）

| 资产 | 说明 |
|---|---|
| `pex8748_full_project_v2.epro`（1.47MB） | 编辑器「工程另存为(本地)」V2 完整工程（project.json+.epcb+.efoo） |
| `pex8748_full_project.epro2`（2.47MB） | 同上 V3 格式（707 docs：588 FOOTPRINT/49 DEVICE）——**10.0.5 无 v3 parser，勿用此喂 CLI** |
| `pex8748_imported.kicad_pcb`（11.77MB） | **唯一有效转换产物**（勿与 2038B 空导入假成功混淆） |
| `pex8748_structure4.json` | learner 输出（AC 96/117 对/refclk 23） |
| `verify_direction.py` / `stat_via_dists.py` / `stat_aic_via2.py` | 形态验证脚本 |
| `ff_profile_copy/`（473MB） | oshwhub 登录 profile（不 commit） |

**丢弃**：`/tmp/opencode/pex8748_raw/pex8748_nvme_evm.kicad_pcb`（2038B 空导入假成功）。

## 4. 关键方法论沉淀（勿重新逆向）

1. **oshwhub 完整工程获取**（非 documents/lists 单文档）：
   - 打开 `https://oshwhub.com/{user}/{project}` → 克隆工程 确认框「即将打开专业版编辑器进行另存」
   - 或直开编辑器 `pro.lceda.cn/editor#id={PID},tab=*{DOC},jspm=hub.gc.sjt.pdk,jlc_vid={JLC_VID}`（JLC_VID 从工程页「在编辑器中打开」href 实时取，过期需重取）
   - 编辑器内 Alt+F → 另存为 → **工程另存为(本地)** → 格式选 **epro (V2格式)** → 确认 → 下载 .epro
   - 裸 dataStr（documents/lists）**缺 FOOTPRINT/DEVICE 库文档**（pad 几何缺失）→ 不可直接还原真板
2. **转换**：`kicad-cli pcb import --format auto x.epro`（10.0.5 自动识别 EasyEDA Pro V2）
   - 勿用 `--format easyedapro`（10.0.5 CLI 白名单无此项）；勿喂 .epro2（v3 需 master，10.0.5 无 v3 符号）
3. **编辑器只读态**：开源工程只读（点菜单弹「另存为新工程」提示）；「工程另存为(本地)」只读态可用（下载不需登录写权限），PADS/其他导出需克隆后全权（本 session 未走克隆，因 V2 .epro 已足够）

## 5. 下 session 入口（若续 K2 电容墙施工）

1. **层3 landing 电容墙感知施工卡**（触发条件满足）：
   - `escape_landing._candidates` 消费 `region.series_cap_wall`（AC_CAP_WALL_ESCAPE_CONSTRAINT.md §3 schema）
   - 墙前候选降权/拒（fail-closed 带证据）；验收 = K2 MCIO 区落点 x ≥ 电容墙下游界（不再 69.8 < 75）
2. learner `_coupling_side` 对 PEX8748 判 unknown（两端同 SLIM token）——保守正确；
   若需 chip/connector 侧区分，走几何法（via 侧向统计已在 §0.3 承担）勿改命名猜测
3. 施工前提：先完成 LAYER3_FEASIBILITY_CLOSURE_DESIGN 的 D1+D2+D3（多区落点/段廊道验证/极性硬约束）
   ——series_cap_wall 是 D1 落点候选序的增强约束（加性），不替代 D1-D3

## 6. 铁律提醒（继承）

- 预期 = 独立可行性研究（真板几何 + SPEC）；问题回模型；零单板特判；确定性；假成功零容忍
- 学案例 ≠ 修引擎（Phase D 停）；learner 形态泛化 = 命名形态学（M13 先例）非板特判
- 改 `_shared/eda_core` 保持通用：本次 +/- 极性/`:C0402` 是 EasyEDA 生态通用形态（330 网全板 +/-, 非 K2 坐标/网名）
