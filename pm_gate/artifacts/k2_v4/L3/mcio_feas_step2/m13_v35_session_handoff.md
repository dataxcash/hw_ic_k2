# M14 v35 NEW SESSION 承接 — 学习参考设计真解（EVM 布线对照），勿重推已钉结论

> 承接文件（唯一必读，其余按"勿加载清单"）。上 session（v34 记录，同目录，**仅需**时深读）
> 已停于 3 次全量 run 纪律线。本 session 主任务 = 学真解（TI EVM 实际布线）→ 判摆向/侧对应
> → 确定性修复。执行纪律：全部前台自跑，禁 task() 委派/后台长跑/暴力迭代（同参 ≤2 带依据）/
> 禁 chmod。引擎改动须 unlock→改→单测→lock 0/0/0→ECN。

## 0. 上 session 已交付资产（勿重做，直接引用）

1. 引擎改动已 lock 在位（ECN-008 已建）：
   - `_shared/eda_core/hs_route_model.py`：`_col_stack_escape`（竖排主导对 In2/In1 列下穿逃逸，
     `_escape_pair` W6-D 块之后触发）+ `cs_alt_field/cs_alt_layer` 传递。备份 `.bak_v33_perball` 之前版本。
   - `_shared/eda_core/route_input.py`：`ModelConfig.col_stack_escape_layer`（None=行为不变）。
   - `k2/.../L2/route_model_config.json`：`"col_stack_escape_layer": "In1.Cu"`（方向分层）。
   - 单测：test_escape_landing/unified_field/channel_alloc 43 passed；test_hs_route_model 7 failed
     = 改动前既有同集（逐一比对过 .bak_v33_perball）。
2. 全量证据：`/tmp/solve_v33e|f|g/hs_rebuild_summary.json`（v33e=基线 0 链；v33f=col_stack In2；
   v33g=In1 分层 → UP1、DN0 全链 SOLVED）。
3. 分类结论（只读定位，勿重查）：见 `m13_v34_session_record.md` §3。

## 1. 已钉死的根因事实（勿重新推导）

1. DS320PR1601 = 354-BGA(ZDG) PCIe5 redriver。官方 datasheet SNLS683 Table 5-1 **球名与工程
   完全一致**：side A = A_PER(RX)/A_PET(TX)、side B = B_PER(RX)/B_PET(TX)。
2. 板拓扑：U6 @(93.8,53.7) rot90，长轴 22.8 沿 X(x82.9-104.7)；J2(SlimSAS,host) 东 x~132；
   MCIO(device) 西 x~64。高速球带 x84.6-93.7 × y49.8-57.6；host 族(A_PER/B_PET)行带 y55-57.6
   与 device 族(A_PET/B_PER) y49.8-52.4 **同列不同行**（每 lane 1.2 列距、P/N 0.3-0.4 交错）。
3. DIRECT 球(西向 MCIO 网) pad 列 F.Cu 被同列邻族 pad 挡死、内层床净空 → col_stack 孤立全解。
4. **全量残留（16 对）= 共享顺序调度**：每段孤立单跑全 SOLVED → 画法够，缺芯片逃逸区
   In1/In2 gutter 资产分配。**REFCLK0/1 = MCIO 连接器区真缺口**（孤立即败 @x58.9/60.7，
   pad 落在轨行带内+邻 GND 贴死）。
5. 用户裁决方向：**学参考设计真解**——两族球同列而出口分两侧 = 芯片摆向/侧对应可疑，
   参考设计会让每 side 就近扇出、不横穿芯片。

## 2. NEW SESSION 主任务（学真解 → 确定性修复）

**目标**：拿 TI DS320PR1601RSCEVM 官方评估板**实际布线资料**（user guide PDF 的布局章节 +
  设计文件/gerber 或布局图），提取：①芯片摆向与 host/device 连接器相对位置；②高速球逃逸
  形态（表层直扇出 or 球旁 via 内层、用哪层、方向分层规则）；③球侧与 lane 排列关系。
  然后对照本板 U6 摆放 + 两族球坐标，**判定**：
  - 若摆向/侧对应错（参考设计里 host/device 球分置封装两侧、板却同列）→ 改摆向或网表侧分配
    （输入修正），引擎本侧就近扇出即可，勿补穿芯片画法；
  - 若摆向对（同列是 DS320 真特性）→ 照 EVM 逃逸形态补引擎/分配。
  修复后 ≤2 次全量 run 验证；3 次不过 = 停带证据回方案层。

**取证入口**（先试，取不到再换）：
- TI 产品页 Design & development：`https://www.ti.com/tool/DS320PR1601RSCEVM`（user guide PDF + 设计文件 zip）
- EVM 用户指南（含布局图/层叠/逃逸细节，找 "Layout" 章节图）
- 关键词：DS320PR1601RSCEVM layout / escape / breakout / ball side A/B host device
- 本板权威板文件：`k2/k2_v4.kicad_pcb`（444 只读，sha f6273de6）；引擎板解析
  `/home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11`（sys.path 加 `_shared`）

## 3. 勿加载清单（省 CONTEXT，违规即浪费）

**不要读**：mcio_feas_step2 下 m13_v10~v32 任一 handoff/报告全文；per_ball_escape_6L_report.json
  全文（只按需 grep 具体 net）；c5_chip_level_expect_matrix_v28.json 全文；MODEL_CONTRACT_AUDIT.md/
  SOLVE_PIPELINE_CONTRACT.md 全文；SPEC_k2_v4.json 全文（按需 grep corridors/bands）；引擎
  hs_route_model.py 已改段落之外的全文件（col_stack 入口 = `_escape_pair` W6-D 后块 +
  `_col_stack_escape` 定义，按需 grep 定位）。
**不要重跑**：无依据的 `--all-v4`（3 次已满，只在摆向/分配/形态按 EVM 改后跑）。
**不要重推**：§0/§1 已钉结论（芯片几何、DIRECT 根因、孤立全解=调度、REFCLK 独立、球名=官方）。

## 4. 运行与合规形态（必用）

- 板/SPEC/alloc/rules/config 全路径见 v34 记录 §2 或本文件 §1。alloc 现用 `/tmp/alloc_v33e/channel_alloc.json`；
  chip-landing 用 `k2/.../mcio_feas_step2/chip_landing_v33.json`（勿重新生成）。
- 引擎改动合规：ECN 挂 ECN-008 补记录或 ecn new → freeze unlock（`bash k2/pm_gate/freeze_ctl.sh unlock`）
  → 备份 → 改 → 单测无新增回归 → lock → status 0/0/0。
- 完成判据：18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘。

## 5. 回退

引擎在 `.bak_v33_perball`（col_stack 前）。k2 SPEC 的 tracks_y/band 改动 = v32 之前既有（勿动）。
