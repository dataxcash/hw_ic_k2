# 任务卡 P2-B — 特征提取器 feature_extractor.py（SPEC/board 局部 → 特征 dict）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P2 后半（特征提取）
> 施工位置：`_shared/eda_core/feature_extractor.py`（公共层，零单板特判）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P2-A 并行，接口契约 = 特征 dict（字段名/值格式见「接口契约」），双方锚定同一契约

## 目标

新建 `_shared/eda_core/feature_extractor.py`：从 SPEC/board 局部（连接器/BGA/电容墙/走廊）提取拓扑特征 dict，供 P2-A 匹配器检索。提取 = 客观事实抽取，不掺设计决策（SDD §4 红线）。

## 权威输入（按序读）

1. `_shared/docs/KNOWLEDGE_REUSE_SDD.md` §4/§5（applicability 客观事实红线 + 特征提取链路）
2. `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`（`components.connectors` / `components.redriver` / `layer_plan` / `corridors` / `capacitor_walls` / `board` / `stackup`）
3. `_shared/eda_core/knowledge_base.py`（对齐 `extract_features` 的字段口径：只抽 applicability 顶层标量，值 `str(v)`）

## 已钉死事实（勿重新论证，来自 SPEC 实测）

- J2 footprint = `SlimSAS_x8_SFF-8654_74pin_RASide`（→ 规范化 connector = `SlimSAS_x8_SFF8654`）
- J3/J4 footprint = `MCIO_4i_SFF-1016_RASide`（→ 规范化 `MCIO_4i_SFF1016`）
- redriver U3/U7 = `DS160PR810`（footprint WQFN-64）
- corridors 2 条：J2_TO_U x[98.83,131.5] / U_TO_MCIO x[65.5,88.83]，pairs=18（16 数据 + 2 REFCLK）
- capacitor_walls：symmetric_bands、cap_count 32、diff_pairs 16
- board outline x[23,143] y[33,71]，8 层板（stackup）

## 设计约束

1. 零外部依赖（仅标准库），零单板特判（提取逻辑通用，SPEC 路径/参数由调用方传入，不得硬编码 k2 路径）
2. 提取 = 客观事实抽取：只从 SPEC/board 读既有事实（连接器类型/pad 列数/脚距/差分对数/层），
   严禁把设计决策（escape 策略/region 划分/拓扑形态）伪装成特征塞进输出
3. 连接器 footprint 规范化：`SlimSAS_x8_SFF-8654_74pin_RASide` → `SlimSAS_x8_SFF8654`、
   `MCIO_4i_SFF-1016_RASide` → `MCIO_4i_SFF1016`（规范映射表放代码内，零板名硬编码）
4. 输出字段名/值格式与「接口契约」严格对齐（26 条字段口径）；未知字段不编造、缺失标 null 或省略
5. 迭代序确定性（sorted）；输出契约写进 docstring

## 接口契约（与 P2-A 对齐，禁止另立字段名）

- 输出：特征 dict，值允许标量（int/float/str/bool），字段名必须是以下已落库字段之一：
  `connector` `pad_columns` `pad_pitch_x` `diff_pairs` `layer` `signal_count`
  `escape_side` `redriver` `cap_count` `cap_per_diff_pair` `footprint` `cap_value_nf`
  `band_layout` `refclk_pairs` `bands` `pairs_per_band` `refclk_layer` `corridor_count`
- 值字符串化规则 = `str(v)`（与 `template_features.feature_value` 一致）

## 验收（按序）

A. 单测：① J2 局部 → `{connector:'SlimSAS_x8_SFF8654', pad_columns:2, diff_pairs:16, layer:'F.Cu', signal_count:36}`
   ② MCIO 局部 → `{connector:'MCIO_4i_SFF1016', diff_pairs:16, escape_side:'chip_side', redriver:'DS160PR810', ...}`
   ③ 电容墙 → `{cap_count:32, cap_per_diff_pair:2, footprint:'C_0402_1005Metric', cap_value_nf:220, diff_pairs:16, band_layout:'symmetric_bands', ...}`
   ④ 走廊 → `{diff_pairs:16, refclk_pairs:2, bands:3, pairs_per_band:8, refclk_layer:'In6.Cu', corridor_count:2, ...}`
   ⑤ 确定性（两跑一致）⑥ 不编造未知字段
B. 真实闭环：对 SPEC_k2_v4.json 提取 4 组特征（J2/MCIO/电容墙/走廊），字段名全部落在契约 26 条集合内（贴输出）
C. `pytest` 全绿 + 粘贴输出；零新增 pip 依赖
D. 零单板特判（grep `k2_v4`/`SPEC_k2_v4`/板坐标 → 空；SPEC 路径由调用方传参）

## 禁止

- 禁止把设计决策（escape 策略/region 划分/拓扑形态）伪装成 applicability 特征（SDD §4 红线）
- 禁止硬编码 k2 板名/SPEC 路径/坐标（通用提取，路径传参）
- 禁止编造 SPEC 里不存在的特征值
- 禁止引入第三方包
