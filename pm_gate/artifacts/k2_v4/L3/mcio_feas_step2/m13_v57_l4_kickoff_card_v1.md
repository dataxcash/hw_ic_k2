# m13 v57 — **L4/G6 开工卡 v1**（图纸直构：PCB 原样消费图纸）

> 2026-09-11｜依 `EDA_AUTONOMOUS_EXECUTION_PLAN_v2.md` G6 行｜DOR：W4(G5) PASS
> DOD：**PCB 原样消费图纸；每节点按处方连接**｜独立验证（mismatch 退回 W3）｜rollback：re-run L4

## 1. 语义（drawing-only construction）
- L4 **零设计决策**：坐标 / 层 / 过孔**全部**取自已冻结的 W3 图纸
  `m13_v57_w3_joint_assignment.json`（34 页 `nodes`/`vias` + REFCLK `path`）+ landing rows。
- L4 只做**机械展开**：图纸节点列 → track（逐段，宽 0.205）+ 层变点 → via（钻 0.2 / 盘 0.35）。
- 图纸**只读**：作为输入校验（sha），L4 不得改动图纸（改动即退回 W3）。
- 冻结源 PCB（`k2_v4.kicad_pcb`，SPEC/manifest/PCB/rules 四源）**不得原地改**：L4 写到**新版板**文件。

## 2. 产物
| # | 文件 | 说明 |
|---|---|---|
| L1 | `tools/p3_v57_l4_apply_drawing.py` | 图纸 → `m13_v57_l4_construction.json`；`--board` 时复制冻结板 + 落 track/via → `k2_v4.l4.kicad_pcb` |
| L2 | `m13_v57_l4_construction.json` | per-net 段/过孔（逐字节 = 图纸几何） |
| L3 | `k2_v4.l4.kicad_pcb` | 新版板（冻结板不动） |
| L4 | `tools/p3_v57_l4_validator.py` + `m13_v57_l4_validation.json` | 独立验证（pcbnew 读回对拍） |

## 3. 验收（机器可判，独立于 applier）
| 检查 | 判据 |
|---|---|
| **L4-A 图纸只读** | construction.authority.drawing_sha256 == 现盘图纸 sha；冻结源 PCB sha 未变 |
| **L4-B 几何=图纸** | 由图纸**独立重算** collapse(points, seg_layers, vias) 逐段/逐 via == construction |
| **L4-C 链连续** | 每网段序列端点链式相接（度=2 内点）；每个 via 落在 ≥2 段（异层）交点 |
| **L4-D 端点处方** | 每 data 网链端 = chip pad 与 conn pad（manifest）；REFCLK 链端 = witness 锚（j2_pad/far_pad） |
| **L4-E 板已消费** | 新板（pcbnew 读回）track/via 逐条 == construction 记录（网名/层/端点，10nm 容差） |

**判定**：L4-A..E 全 True ⇒ **G6 PASS**；任一 False ⇒ mismatch，**退回 W3**（不得 partial pass）。
