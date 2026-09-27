# K2 · R780 回执 —— #K2-304 §二「SPEC 登记版 bump 落账 ＋ 一次描线」

> 依据：#K2-304 §二「1. SPEC 登记版 bump 落账（登记 v2 写入 SPEC，授权链 #K2-280→#K2-297→#K2-303 全链留痕；其余三源不动）；2. 一次描线（按《整版分配 SOP》W5 域=1 一次性构造，把 16 条线按认证表落图；一次执行·禁迭代；完成即机核（DRC 全绿目标）＋渲染图随件交）」。
> 护栏：不导 Gerber／不进 P5／不下单／禁 WORKER／板本体零改动。

## 〇、结论

1. **SPEC 登记版 bump 落账完成**：`SPEC_k2_v4.spec-rev-55` → **`spec-rev-56`**（**纯追加** ＋ `spec_version` bump），`pm_gate/project.yaml: spec_name` 重指向 rev-56。
2. **一次描线完成**：按 R778 认证表把 **16 条线落图**（几何 mm）⇒ **机核 DRC 全绿**（`ALL_GREEN=True`）＋ **渲染图**随件交。

## 一、SPEC 登记版 bump（§二.1）

| 项 | 读数 |
|---|---|
| 源 / 目标 | `spec-rev-55`（sha16 `48933863ef621510`）→ **`spec-rev-56`**（sha16 **`3b4e3733a21e72cb`**） |
| 追加（新键，82 leaf） | `router.wall_gap_exit_registration_v2`（登记 v2：15 留 ＋ 1 补 ＋ 6 死洞剔除 · 授权链 · 证据 hash · 不变量）＋ `_spec_rev_56` 溯源卡 |
| 变更（既有键） | **仅 `.spec_version`**（`1.1.spec-rev-49` → `1.1.spec-rev-56`） |
| 删除 | **0** |
| 追加性证明 | 监理可复核：`removed_keys=[]`、`changed_existing_keys=['.spec_version']`（记录件 `K2_R780_SPEC_REGISTRATION_V2_DECLARE.json`） |
| `project.yaml` | `spec_name: SPEC_k2_v4.spec-rev-56.json`（按项目惯例新 rev 即 canonical） |
| 回滚 | 恢复 `project.yaml` 指向 rev-55 ＋ 删 rev-56（前身逐字节未动） |
| **其余三源** | 未动（manifest / PCB / drc_rules 逐字节不动） |

## 二、一次描线（§二.2）

| 项 | 读数 |
|---|---|
| 输入 | R778 认证表（`SAT_16of16` · `3d9a821b94174c1d`）＋ 登记 v2 |
| 落图 | **16/16 行** · 格 **1390** · 过孔 **5** · 总长（模型格距）见件 |
| 层 | `L0=In5.Cu` / `L1=In4.Cu`（R550 模型口径）· In5 跨 13 线 / In4 跨 8 线 |
| 几何口径 | mm = 原点 `(84.0, 41.0)` ＋ 格距 `0.435` |
| **机核 DRC（drawing-level · 全绿）** | 连续性 PASS · 线宽 `0.205 ≥ 0.09` PASS · **同层最小中心距 0.435 mm ≥ 需 0.305** PASS · 四硬键 `4/4` · 门互异 · 门在登记集内 · 层对键 0 违例 |
| 渲染图 | `K2_R780_FINAL_ROUTING_DRAWING_v1.png`（In5 / In4 双面板，门位方块标记） |
| 件 | `K2_R780_FINAL_ROUTING_DRAWING_v1.py/.json/.png`（hash16 **`0c5812040a57d574`**）· `K2_R780_draw.log` |
| 纪律 | `construction_runs=1` · `drawings=1` · **无求解器** · 未导 Gerber · 未进 P5 · 未下单 · **板本体零改动** |

**DRC 口径如实标注**：本窗 DRC = **图纸级（网格分辨率 · mm 几何）**：连续性即可铜连通性；同层中心距 ≥ `线宽+净距`；线宽合规；四硬键＋层对键。**完整 kicad-cli 板级 DRC 属 P4/P5 闸**，不在本窗（本窗未写任何 `.kicad_pcb`）。

## 三、工程解读（人话）

- 16 条信号已**全部排通并落成一张确定的施工图**：从芯片侧槽位 → 高速行 → 下钻 → 过孔换层 → 沿墙逃逸到**各自独立的出口开口**；彼此**零重叠**、间隔 0.435 mm（> 0.305 要求）。
- 出口开口用了 **15 个既有可路由口 ＋ 1 个新增口 `W[114,47]`**；被剔除的 6 个"死洞"不再出现。
- **图上画的是模型坐标系的铜线**（In5/In4 两层）；**尚未落到实体板**（`physical_opening_changes=0`）。

## 四、边界

- 板本体／manifest／rules **逐字节不动**；SPEC 仅**追加**登记键（监理可逐 leaf 复核）。
- 物理开口落板（P-b）与完整板级 DRC/Gerber 仍**待监理另行放行**（#K2-297 §二.4）。

OWNER-ITEMS: 0
