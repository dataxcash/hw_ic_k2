# 任务卡 P1-B — K2 首批案例模板化（4 模板五段 JSON）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P1 后半（模板化）
> 施工位置：只读分析 K2 资产，产出模板种子 JSON（供 P1-A loader 吞入落库）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P1-A 并行，无数据依赖（双方锚定同一 SDD，合并点见「合并接口」）

## 目标

从 K2 已验证资产提取 4 个案例模板的五段 JSON（applicability/structure/params/validation/provenance），
作为首批案例库内容。模板 = "怎么走"的经验形态，坐标不写死。

## 4 个模板（category 对应 SDD §4）

1. `conn_escape_slimsas_x8`  — connector_escape  — SlimSAS(J2) x8 逃逸（16 对）
2. `conn_escape_mcio`        — connector_escape  — MCIO 逃逸（U3/U7 芯片侧）
3. `cap_wall_ac`             — cap_wall          — AC 耦合电容墙
4. `corridor_pair_dual_band` — corridor_pair     — 双带走廊对级

## 权威输入（按序读）

1. `_shared/docs/KNOWLEDGE_REUSE_SDD.md` §4（五段 JSON 结构 + 红线）
2. `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`（`layer_plan.j2_escape_nets` / `wp1_escape_nets` / `corridors` / `capacitor_walls`）
3. `k2/pm_gate/artifacts/k2_v4/L3/model_solves/`（escape_landing / channel_alloc / hs_rebuild_v12 求解产物）
4. `m13_v12_session_handoff.md` §6（物理事实）

## 已钉死事实（勿重新论证，来自 handoff §6）

- J2 逃逸落点：列间空隙 x∈[133.295,134.355]（gap_center 133.825）+ 外侧 x>135.655；36 信号（26 列间 + 10 外侧）
- SlimSAS x8 = J2，16 对；拓扑 dual_band（SPEC `corridors` 2 条）
- AC 电容墙：SPEC `capacitor_walls`（symmetric_bands + mcio_side_x/j2_side_x 双带）
- skew 缺口（已知遗留）：escape_landing 落点逐信号独立锚定、无 P/N 对称约束 → `skew_ok=false`
  （validation 必须如实标：`produced=true` 但 `skew_ok=false`，不得粉饰）

## 设计约束

1. 五段 JSON 严格分离；applicability 只放客观事实（连接器类型/pad 列数/脚距/差分对数/层），严禁把设计决策塞进 applicability
2. params 坐标不写死：`gap_center=null` 等运行时量留空；只写形态参数（track_pitch/pair_half_pitch 等）
3. validation.produced 必须真实：仅 K2 生产验证过的模板 `produced=true`；skew_ok 如实 `false`
4. 每模板同步给出 feature 抽列字段（connector/pad_columns/diff_pairs/layer…），供落 `template_features`
5. 模板 = 参数化结构，不是坐标复制；新板坐标运行时算

## 合并接口（与 P1-A 的接缝）

产出**一次性种子 JSON**（如 `_shared/knowledge/seed_k2_templates.json`），结构符合 SDD §4 五段 JSON，供 P1-A 的 `load_seed()` 吞入落库。种子落库后失效，不作为长期事实源。

## 验收（按序）

A. 4 个模板五段 JSON 完整，无空段
B. applicability 特征可抽列（能映射到 template_features 的 key/value）
C. validation.produced / skew_ok 如实反映 K2 真实状态（skew 缺口不得隐瞒）
D. 种子 JSON 可被 P1-A `load_seed()` 加载校验（合并点）

## 禁止

- 不得把 skew_ok=false 写成 true（假成功零容忍）
- 不得写死新板坐标（只给形态 + 参数化）
- 不得新增 markdown/json 散落文件作长期知识事实源（唯一事实源 = kb.sqlite3）
