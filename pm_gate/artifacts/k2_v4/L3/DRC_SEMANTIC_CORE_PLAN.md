# K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14）

> 计划时间：2026-08-24 · 承接 `.omo/plans/k2-ls-model-gate.md`（M1-M9 已交付）
> 用户裁决（2026-08-24，两次纠偏）：
>   ① 啃硬骨头必须通过建模解决；从最难处入手，啃了骨头才能整体解决
>   ② **骨头 = 建模体系本身最难的问题（统一 DRC 语义内核），不是 DRC 某个区域的块**
> 定位：**建立基础设施，从长远彻底解决问题。** 本计划废弃并取代早期
> 草案 `k2-highspeed-escape-model.md`（方向错误：按 DRC 条数选骨头，域级、DRC 导向）。

> **啃骨头的定义（用户澄清 2026-08-24）**：建统一内核是**手段**，
> **高速域 DRC 清理是检验模型实际可用性的试金石**。内核建得对不对，
> 不以"建完"为准，以"高速域 385 条能否清掉"为准——啃下高速域 = 内核
> 实战可用（真刀真枪，非纸上对齐）；高速域啃不动 = 内核有问题，
> 回去修内核，不是修高速域。M10 语义对齐率是内核内部质量，
> M13 高速域清理是实战验收——一条链。

---

## 0. 问题定性（建模体系四大缺陷，皆为本计划要解决的根）

系统核查（2026-08-24，用户认可）确认建模体系存在四个结构性缺陷：

| # | 缺陷 | 后果 | 本计划解法 |
|---|---|---|---|
| 1 | **域分裂**：低速/高速/电源地/制造四个世界各建各的模型 | 高速域无模型（S2 锁的 290 条违规无根可查）；电源地无模型（266 条无解）；制造无模型（61 条模型看不见） | 统一建模内核，各域套模板 |
| 2 | **模型语言 ≠ DRC 语言**：ls_route_model 用中心线净距（0.25/0.35），DRC 量边缘净距/钻孔-铜/阻焊桥 | 模型预测不了 solder_mask(58)/zones(2)/diff_pair(1)，语义对齐靠猜 | 统一 DRC 语义规则库：模型语言 == DRC 语言，**用"语义对齐率"可测证明** |
| 3 | **无全局观**：单网求解 + 先到先得 | 通道分配推二期，互交靠事后审计 | 全局约束求解：冲突图 + 先难后易，建模时全局自洽 |
| 4 | **无反向定位**：DRC 报错不知元凶 | 排错靠人工翻板，drc_radar 是临时脚本 | DRC→模型元素反查引擎，系统能力（沉淀进 eda_core） |

**DRC 现状锚点（反向定位已完成，勿考古）**：867 条 = 芯片区 U3U7 574
（高速 385/电源地 69/低速 120）+ 右 SlimSAS 97 + 左 MCIO 32；高危 78 条（间距<50%）；
孔距 171 系统性。**这些数字是内核的验收标尺，不是修的对象。**

---

## 1. 攻坚目标（H1）：统一 DRC 语义建模内核

建 `drc_semantic_core`（基础设施，与 ls_route_model 同构但语义升级），四大交付：

1. **统一 DRC 语义规则库**（`drc_rules`）：把 DRC 的每类规则翻译成模型约束——
   clearance（边缘净距→中心线约束）、hole_clearance（钻孔-铜）、solder_mask_bridge
   （阻焊桥宽）、track_width（最小线宽）、diff_pair（对内/对间/等长）、
   manufacturing（孔环/板边距/孔距，JLC 工艺）
2. **统一障碍场**（五类障碍：段/via/pad/zone 铺铜/mask 开窗），统一膨胀语义——
   每个障碍按"它参与的 DRC 规则"计算膨胀量，与 DRC 引擎同口径
3. **全局约束求解**：冲突图通道分配 + 先难后易（计划 §4 二期正式落地），
   各域共用；Dijkstra 确定性求解复用
4. **DRC 反向定位引擎**：每条 DRC finding → 模型元素（段/via/pad/zone）+
   违反的规则 + 根因说明——drc_radar 从临时脚本升级为系统能力

**核心验收思想（关键创新）**：语义对齐验证——模型规则库在**现有板**上做
"预测性 DRC"，预测的违规集合与 kicad-cli 实际 DRC 的 867 条对照，
**对齐率 ≥95%** 即证明"模型语言 == DRC 语言"。语义对不对，用数据说话，
不再靠口头承诺。

---

## 2. 建模设计（DRC-SEMANTIC-CORE 规格）

### 2.1 统一语义规则库（drc_rules）

| DRC 规则 | 模型语义（与 DRC 引擎同口径） |
|---|---|
| clearance | 边缘净距 → 中心线约束 = 净距 + (w1+w2)/2；段/段、段/焊盘、段/zone 三类 |
| hole_clearance | 钻孔边缘-铜边缘净距 → 中心线约束 = 净距 + drill_r + w/2 |
| solder_mask_bridge | 阻焊桥宽度（开窗-开窗间距）→ mask 开窗几何 |
| track_width / 制造 | 最小线宽 0.15、孔环 ≥0.075、板边距 ≥0.3、孔距（JLC06161H） |
| diff_pair | 对内间距/对间间距/等长 <0.15mm/相位 |
| impedance | 叠层映射：85Ω 差分（线宽/间距由阻抗表反推） |

规则库以 `drc_rules.json`（或 yaml）声明式落盘，可扩展、可审计、零 revA 特判。

### 2.2 统一障碍场（UnifiedObstacleField）

- 五类障碍：seg / via / pad / zone（铺铜平面）/ mask（阻焊开窗）
- 每类障碍携带"参与的规则集"，膨胀量由规则计算（与 DRC 同口径）
- 同网豁免、异网净距——协议与 ls_route_model 一致，语义升级
- zone 障碍首次入模型：铺铜平面边缘 vs 走线/焊盘的净空（266 条电源地违规的根）

### 2.3 全局约束求解

- 冲突图：各域通道/走廊为资源节点，网为需求，冲突边 = 物理重叠
- 先难后易分配（按 DRC 违规密度排序，最挤的通道先分）
- 求解确定性：Dijkstra 距离升序 + 坐标序，零随机（复用 ls_route_model 框架）

### 2.4 DRC 反向定位引擎（drc_locator）

- 输入 drc.json → 每条 finding 解析 items（网/层/坐标/类型，复用 drc_radar 解析器）
- 映射到模型元素 + 规则 + 根因（"这条违规是 X 元素违反 Y 规则，因为 Z"）
- 输出：按 域×区域×规则×根因 聚类的定位报告 + 高危清单（间距<50% 优先）
- 沉淀：`/tmp/opencode/drc_radar.py` → `eda_core/drc_locator.py`（系统能力）

### 2.5 落盘与门禁

- 求解记录：`pm_gate/artifacts/L3/model_solves/`（各域子目录，solve_ref+input_fp 协议同低速域）
- 门禁：model_gate 扩展规则 7——**任何域的设计段必须出自统一内核**（带 solve_ref），
  语义规则库变更需红队可审计
- DRC 只核对：模型预测 vs 实际 DRC 的对齐率是质量度量，不是修复驱动器

---

## 3. 实施阶段（M10-M14，严格顺序，禁止跳级）

| 任务 | 内容 | 验收 |
|---|---|---|
| M10 | **统一语义规则库 drc_rules**：DRC 规则→模型约束翻译层（五类规则） + **语义对齐验证** | 模型在现有板预测违规 vs kicad-cli 867 条对照，**对齐率 ≥95%**（clearance/hole_clearance 先对齐，solder_mask 次之）；规则库单测 |
| M11 | **统一障碍场升级**：五类障碍（+zone/mask）+ 差分对语义 + 全局冲突图通道分配 | 障碍场单测（zone 边缘净空/阻焊桥几何）；通道分配表落盘；低速域迁移到新障碍场后行为不变（回归） |
| M12 | **DRC 反向定位引擎 drc_locator**：drc_radar 沉淀为系统能力 | 867 条每条可定位到"元素+规则+根因"；定位报告落盘 artifacts/L3/drc_locator/ |
| M13 | **各域套模板重建**：高速域（新内核+高速语义）→ S2 正规流程重建；电源地（新内核+zone 语义）→ S3 PDN 铺铜 | 高速域方案 100% 模型来源；电源地铺铜后 DRC 电源地 266 条 → 0（或带证明残余） |
| M14 | **整体收敛**：孔距(171)→过孔库/孔阵、低速施工(82)、制造(58) 联动 | drc.json 全项归零 → S5 Gerber |

**M10 是第一块骨头**：纯规则层建模 + 语义对齐验证（零修改板/SPEC）。对齐率
就是内核质量的客观标尺——对齐率上不去，说明规则翻译有错，继续修规则库，
**不进入任何域的方案重建**。

---

## 4. 验收指标

```yaml
# M10（第一块骨头）
semantic_alignment_rate: >= 0.95     # 模型预测违规 vs kicad-cli DRC 对齐率
drc_rules_json: 存在                  # 规则库声明式落盘 + 单测
# M11
unified_obstacle_field: 通过           # 五类障碍单测 + 低速域迁移回归不变
channel_alloc: 落盘                   # 冲突图分配表
# M12
drc_locator: 每 finding → 元素+规则+根因  # 867 条全定位，报告落盘
# M13-M14
高速域方案 100% 模型来源；电源地 266 → 0；DRC 总量 867 → 0（S5 Gerber）
```

**对齐率的定义**：模型规则库在现有板扫描出的违规集合 ∩ kicad-cli 违规集合 /
kicad-cli 违规集合。逐规则类型分别统计（clearance 对齐率 / hole_clearance 对齐率 / …），
任一核心规则（clearance/hole_clearance）对齐率 <95% → M10 不通过，修规则库。

---

## 5. 风险与决策点

| 风险 | 应对 |
|---|---|
| 规则翻译有系统性偏差（对齐率上不去） | 对齐率是客观标尺：逐规则类型看偏差模式（系统性偏移=规则翻译错；散点=个别元素特例）→ 修规则库，禁止绕过 |
| zone/mask 语义建模复杂（首次入模型） | M11 单独阶段攻坚，先用最小案例（单 zone vs 单走线）对齐，再全量 |
| S2/高速域重建（M13） | 由内核结论驱动，走 `sregress`/`sadvance` 正规流程；范围由模型判定，不预先拍板 |
| 物理容量极限 | 确认不可行 → 停止迭代，出论证报告上报，不硬凑（沿用） |
| 反死循环 | 同一命令连错 2 次即停转 Plan 等人工介入（沿用） |

---

## 6. 铁律（违反即停机）

1. **方案即模型输出**：任何域设计段必须出自统一内核，带 solve_ref；无模型来源 = 非法
2. **DRC 只核对不驱动**：对齐率是质量度量，不是修复驱动器；禁止拿 DRC 手工改走线
3. **结论带证明**：SOLVED 带路径；INFEASIBLE 带连通分量证明；对齐率带对照数据
4. **修订走输入**：冲突 → 修订规则库/输入 → 模型重算 → 落方案 → gate → 施工
5. **零 revA 特判**：内核全通用，入参全路径；规则库声明式，可扩展
6. **先难后易**：M10 语义对齐优先，禁止跳级直接改线/改域方案
7. **基础设施定位**：本计划建的是"建模体系的地基"，不是某个域的 DRC 补丁；
   任何"先修某区域 DRC"的诉求 → 回到本计划 M10-M12 完成后再谈

---

## 7. 工具基线

- 运行：`sharun python3.11` + `PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared`
- 板真源：`strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb`（120×38mm，k2_v4 实测）
- SPEC 真源：`pm_gate/artifacts/L3/SPEC_k2_v4.json`（备份 `/tmp/opencode/SPEC_k2_v4.json.work`）
- 求解记录：`pm_gate/artifacts/L3/model_solves/`（各域子目录；不 gitignore，红队可审计）
- pad 资产：`/tmp/opencode/SPEC_pad_freeze.json`
- DRC 口径：`kicad-cli pcb drc <板> --format json --severity-error --refill-zones`
  （必须带同名 .kicad_pro；基线 868，m9demo 867）
- 反向定位雏形（M12 沉淀对象）：`/tmp/opencode/drc_radar.py`
- 规则真源：板 .kicad_pro 的 clearance/孔距/阻焊设置 + AGENTS.md 制造约束
  （线宽/线距 ≥0.09/0.10；过孔 0.20/0.35 孔环 ≥0.075；板边铜 ≥0.30；JLC06161H 孔距极限）

---

## 8. 已查证勿考古（新 session 直接使用）

- DRC 反向定位已完成：867 条 → 175 根因族；芯片区 U3U7 574（高速 385/电源地 69/低速 120）、
  右 SlimSAS 97、左 MCIO 32；高危 78 条（间距<50%）；孔距 171 系统性；solder_mask 58
- 模型缺口（内核 M10 要补的语义）：solder_mask_bridge 58 + zones_intersect 2 + diff_pair_gap 1
- M1-M9 已交付：ls_route_model（可见性图/Dijkstra/连通分量证明）+ model_gate（规则 1-6）+
  全局互交审计 audit_global + resolve 确定性重解；MODE_U7 降级 INFEASIBLE 待 PM 裁决
- ObstacleField 已类型标签化（_kind/_loc，顺序无关分派）——M11 升级五类障碍的地基
- 精确段-段距离 `_seg_seg_min_exact` 已在 ls_route_model（相交→0，非端点近似）
- S 状态机：S0/S1/S2 已过（S2 语义=锁定，不承诺合规），S3 被 DRC 缺失阻断
- pcbnew SWIG 退化：用"改动前快照 + 预载"规避（low_speed_apply 模式可复用）

---

## 9. NEW SESSION PROMPT（直接复制使用）

```
你是 K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14 攻坚）的执笔 session。
工作目录：/home/fila/jqdDev_2025/ic_hw
项目：PCIe Gen4 转换卡卡2-K2（120×38mm，k2_v4.kicad_pcb，U3/U7 双 DS160PR810 ReDriver）

【背景（必须读）】
1. .omo/plans/k2-ls-model-gate.md（M1-M9 已交付：低速域模型 + model_gate 规则1-6 +
   全局互交审计 + resolve；其中 ls_route_model 的 ObstacleField 已类型标签化、
   精确段-段距离可用——本计划的地基）
2. .omo/plans/k2-drc-semantic-core.md（本攻坚计划，执行以它为准）
3. AGENTS.md（PM 质量控制模型 + LAYOUT 宪法；开工第一动作：
   cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status（红队 open findings
   逐条处理）+ python3 pm_gate/cli.py sstatus）

【本轮任务（严格按序，禁止跳级）】
M10（第一块骨头，纯规则层建模，零修改板/SPEC）：
  建统一 DRC 语义规则库（新模块 eda_core/drc_rules.py + 声明式 drc_rules.json，
  零 revA 特判）：
  1. 五类规则翻译层（与 kicad-cli DRC 同口径）：
     - clearance：边缘净距 → 中心线约束 = 净距 + (w1+w2)/2（段/段、段/焊盘、段/zone）
     - hole_clearance：钻孔边缘-铜边缘 → 中心线约束 = 净距 + drill_r + w/2
     - solder_mask_bridge：阻焊桥宽度（开窗-开窗）
     - track_width / 制造：最小线宽 0.15、孔环 ≥0.075、板边距 ≥0.3、孔距（JLC06161H）
     - diff_pair / impedance：对内/对间/等长/85Ω（声明预留，M11 深化）
  2. 规则来源：板 .kicad_pro 的 clearance/孔距/阻焊设置 + AGENTS.md 制造约束，
     声明式落盘（规则值可审计、可扩展）
  3. 单测：每条规则翻译的正确性（构造已知几何 → 断言模型判定的净距 == 手算值）

【M10 核心验收：语义对齐验证（关键，不可跳过）】
  用规则库在**现有板**（k2_v4.kicad_pcb）上做预测性扫描（模型读板 → 按规则库
  判定违规）：
  - 与 kicad-cli 实际 DRC 输出（/tmp/opencode/boards/k2_m9demo.drc.json，867 条，
    口径 --severity-error --refill-zones）逐条对照
  - 对齐率 = |模型预测 ∩ 实际| / |实际|，**按规则类型分别统计**
  - clearance 与 hole_clearance 对齐率 ≥95% → M10 通过
  - 对齐率不足 → 分析偏差模式（系统性偏移=规则翻译错；散点=个别元素特例）→
    修规则库 → 重验；**禁止绕过、禁止下调阈值、禁止进入任何域方案重建**

【铁律】
- DRC 只核对不驱动：对齐率是质量度量，不是修复驱动器；禁止拿 DRC 手工改走线
- 结论带证明：对齐率带逐规则类型对照数据；任何"对齐"结论必须附数字
- 修订走输入：规则库/输入修订 → 重算 → 重验
- 零 revA 特判：规则库声明式、全通用
- 不碰任何 locked 高速段、不重建任何域方案（那是 M13 的事）
- 反死循环：同一命令连错 2 次停转 Plan 等人工介入

【工具基线】
- sharun python3.11 + PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared
- 板：strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb；SPEC：pm_gate/artifacts/L3/SPEC_k2_v4.json
- pad 资产：/tmp/opencode/SPEC_pad_freeze.json
- DRC 对照基线：/tmp/opencode/boards/k2_m9demo.drc.json（867 条，勿重跑勿考古）
- DRC 口径：kicad-cli pcb drc <板> --format json --severity-error --refill-zones（带 pro）
- 可复用：ls_route_model 的 ObstacleField（类型标签化）、_seg_seg_min_exact、可见性图框架
- 规则真源：板 .kicad_pro + AGENTS.md 制造约束（线宽/线距 ≥0.09/0.10；过孔 0.20/0.35
  孔环 ≥0.075；板边铜 ≥0.30；JLC06161H 孔距极限）

【已知勿考古】
- 867 条 DRC 已反向定位：芯片区 574（高速 385/电源地 69/低速 120）、右 SlimSAS 97、
  左 MCIO 32；高危 78 条；孔距 171 系统性；solder_mask 58
- 模型缺口（M10 要补的语义）：solder_mask_bridge/zones_intersect/diff_pair_gap
- M1-M9 已交付：低速域模型 + 门禁 + 审计 + resolve；MODE_U7 INFEASIBLE 待 PM 裁决
- pcbnew SWIG 退化：用改动前快照+预载规避

【交付物】
- eda_core/drc_rules.py + drc_rules.json（声明式规则库）+ 单测
- 语义对齐验证报告：逐规则类型对齐率 + 偏差模式分析（落盘 artifacts/L3/drc_semantic_align.md）
- M10 验收：clearance + hole_clearance 对齐率 ≥95% 的数字证据
- 全部结论带证明；红队可审计
```

---

## 10. M10 交付记录（2026-08-24，新 session 直接引用，勿考古）

> **M10 状态：已交付 PASS**。验收证据：
> - **clearance 对齐率 100%**（430/430 唯一对，500 违规行全命中，零漏报）
> - **hole_clearance 对齐率 100%**（106/106 唯一对，171 违规行全命中）
> - 核心规则综合对齐率 100% ≥ 95% → **M10 通过**
> - 次之规则：solder_mask_bridge 98.3%（57/58）、tracks_crossing 100%（46/46）、
>   shorting_items 95.2%（80/84）；未实现：diff_pair_gap(1)/zones_intersect(2) 留 M11

**交付物**：
| 产物 | 路径 |
|---|---|
| 规则库 | `eda_core/drc_rules.py` + `eda_core/drc_rules.json`（声明式，五类规则翻译层） |
| 单测 | `eda_core/tests/test_drc_rules.py`（28 条，规则翻译手算对照） |
| 对齐报告 | `pm_gate/artifacts/L3/drc_semantic_align_af328772.md`（含偏差分析 + KiCad 源码佐证） |
| 对齐数据 | 同目录 `drc_semantic_align_af328772.json` |

**关键语义发现（新 session 勿考古，直接用）**：
1. **net→class 真源 = 板 .kicad_pro `net_settings.classes` + `netclass_assignments`**
   （146 网显式分配：PCIe85=0.175/LOW_SPEED=0.1/POWER=0.2/Default=0.1，未分配→Default；
   GND 属 Default 0.1）。规则库 `--pro <pro>` 直接读取，零 revA 特判。required = max(ncA, ncB)。
2. **kicad DRC 报告语义**（源码确认）：required = max(netclass)；段-段用真最小段距离；
   via-via 按铜层重复报告（贯穿 8 层 → 同一对 8 行，无跨层去重）；RTree 预筛用最大
   clearance；DRCEpsilon 0.5µm。模型保留全部几何有效对（recall 100%，保守安全），
   kicad ≤1/primary/层 是输出层优化 — 偏差分析见报告 §3。
3. **hole_clearance** = 孔缘-铜缘 ≥0.25（via 孔 vs 段/焊盘/异网 via 铜；via-via 取双向 min）。
4. **solder_mask_bridge** 经验校准：开窗 == 铜几何（无 pad_to_mask 膨胀），异网开窗边缘
   净距 < 0.05 → 违规（53/58→57/58 实现修复后 98.3%）。

**M10 遗留（M11 深化）**：diff_pair_gap(1)/zones_intersect(2) 未建模；
THT 焊盘 mask/短接细节 4 条短接漏报；红队 F-R14（SPEC 低速段 solve_ref，M1-M9 遗留）与 M10 无关。

---

## 11. M11 NEW SESSION PROMPT（直接复制使用，续接 M10）

```
你是 K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14 攻坚）的 M11 执笔 session。
工作目录：/home/fila/jqdDev_2025/ic_hw
项目：PCIe Gen4 转换卡卡2-K2（120×38mm，k2_v4.kicad_pcb，U3/U7 双 DS160PR810 ReDriver）

【背景（必须读，M10 已完成勿考古）】
1. 本计划 §10 = M10 交付记录（PASS，含"关键语义发现"四条——直接引用，禁止重做语义探索）
2. artifacts/L3/drc_semantic_align_af328772.md = M10 对齐报告（数字证据 + 偏差分析 + 源码佐证）
3. eda_core/drc_rules.py + drc_rules.json = M10 交付规则库（本次工作基础，--pro 直读 net class）
4. .omo/plans/k2-ls-model-gate.md（M1-M9：ls_route_model + ObstacleField 类型标签化地基）
5. AGENTS.md（开工第一动作：cd strix-halo-ioconvert/revA/pcb &&
   python3 pm_gate/cli.py status（红队 open findings 逐条处理）+ python3 pm_gate/cli.py sstatus）

【本轮任务（M11，严格按序，禁止跳级）】
统一障碍场升级（基于 M10 规则库几何，非重写）：
1. 五类障碍统一膨胀语义（与 DRC 同口径）：
   - seg/via/pad/zone(铺铜平面)/mask(阻焊开窗)，每类携带"参与的规则集"，
     膨胀量由规则计算（clearance/hole_clearance/solder_mask_bridge）
   - zone 障碍首次入模型：铺铜平面边缘 vs 走线/焊盘净空（电源地 266 条违规的根）
   - 差分对语义：对内间距(p_gap 0.175)/对间间距(0.875)/等长<0.15mm
   - 收编 M10 遗留：diff_pair_gap_out_of_range(1)/zones_intersect(2)/THT pad mask 细节
2. 全局冲突图通道分配：
   - 冲突图：各域通道/走廊为资源节点，网为需求，冲突边=物理重叠
   - 先难后易分配（按 DRC 违规密度排序，最挤通道先分）
   - 求解确定性：Dijkstra 距离升序 + 坐标序，零随机（复用 ls_route_model 框架）
   - 通道分配表落盘 artifacts/L3/model_solves/channel_alloc/
3. 低速域迁移回归：低速域迁移到新障碍场后行为不变（回归验证，行为变=障碍场有 bug）

【M11 验收】
- 障碍场单测：zone 边缘净空 / 阻焊桥几何 / 差分对语义 / 收编遗留类型
- 通道分配表落盘（solve_ref 协议同低速域）
- 低速域迁移回归不变
- M10 遗留收编后的对齐率更新（跑 python -m eda_core.drc_rules align）

【M10 关键语义（勿考古直接用）】
- net→class 真源 = 板 .kicad_pro net_settings（146 网显式分配；GND=Default 0.1）
- required(a,b) = max(nc(A), nc(B))；hole_clearance = 孔缘-铜缘 ≥0.25
- kicad 报告语义：via-via 按铜层重复（8 层→8 行）；段-段真最小距离；DRCEpsilon 0.5µm；
  模型全对子是保守安全语义（约束求解不漏约束）
- solder_mask_bridge：开窗==铜几何（无膨胀），异网开窗边缘 <0.05
- 工具：python -m eda_core.drc_rules predict|align（--board --pro --rules --drc）

【铁律】
- DRC 只核对不驱动：对齐率是质量度量，不是修复驱动器；禁止拿 DRC 手工改走线
- 方案即模型输出：任何域设计段必须出自模型求解，带 solve_ref
- 结论带证明：SOLVED 带路径；INFEASIBLE 带连通分量；对齐率带逐类型数据
- 修订走输入：规则库/输入修订 → 重算 → 重验
- 零 revA 特判；不碰任何 locked 高速段（那是 M13 的事）
- 反死循环：同一命令连错 2 次停转 Plan 等人工介入

【工具基线】
- sharun python3.11 + PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared
- 板：strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb
- DRC 基线：/tmp/opencode/boards/k2_m9demo.drc.json（867 条，勿重跑勿考古）
- 规则库：eda_core/drc_rules.json（M10）+ 板 .kicad_pro（net class 真源）
- 求解记录：pm_gate/artifacts/L3/model_solves/
- 可复用：drc_rules.py 几何（_seg_seg_min_dist/_seg_rect_dist/_point_rect_dist）、
  ls_route_model 可见性图/Dijkstra/连通分量框架、netclass 装载（--pro）

【交付物】
- 五类障碍统一膨胀（含 zone/mask 几何 + 差分对语义）+ 单测全绿
- 冲突图通道分配表落盘（channel_alloc/）
- 低速域迁移回归证据
- M10 遗留收编后的对齐率更新（附数字）
- 全部结论带证明；红队可审计
```
