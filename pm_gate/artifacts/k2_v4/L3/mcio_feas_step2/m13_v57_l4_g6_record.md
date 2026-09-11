# m13 v57 — **G6（L4 图纸直构）收口记录：PASS**

> 2026-09-11｜卡：`m13_v57_l4_kickoff_card_v1.md`｜applier：`tools/p3_v57_l4_apply_drawing.py`
> ｜验证器：`tools/p3_v57_l4_validator.py`（KiCad pcbnew 10.0.5）｜独立验证：见 §4

## 1. 结论
- **G6 PASS**：PCB **原样消费** W3 图纸；**每节点按处方连接**；**图纸只读**；冻结四源未动。

## 2. 产物与量
| 文件 | 关键数 / sha |
|---|---|
| `m13_v57_l4_construction.json` | **66 网 / 328 段 / 256 via**；sha `e50e2becaa921f09` |
| `k2_v4.l4.kicad_pcb`（新版板，冻结板不动）| sha `8266989a38802ddd`；src 冻结板 sha `f6273de613f43d05`（未变） |
| `m13_v57_l4_validation.json` | **verdict=PASS**；L4-A..E 全 True；0 违例；sha `a8bf6c0f064dbc8a` |

## 3. 验收结果（L4-A..E）
- **L4-A 图纸只读**：construction.authority.drawing_sha256 == 图纸 `caa516abdaf8e823`；冻结板 sha 未变。
- **L4-B 几何=图纸**：由图纸独立重算的 (points, seg_layers, vias) 与 construction 逐段一致（0 差异）。
- **L4-C 链连续**：66 网段链端点相接（内点度=2，端点数=2）；256 via 均落于 ≥2 段异层交点。
- **L4-D 端点处方**：64 data 网链端 = chip pad / conn pad；2 REFCLK 链端 = j2_pad / far_pad。
- **L4-E 板已消费**：pcbnew 读回 `k2_v4.l4.kicad_pcb` 的 track/via 与记录逐条一致（10 nm 容差；64.475 vs 64.474999 已归一）。

## 4. 独立验证（必须）
- read-only 子代理复核：重跑 applier + 验证器；确认图纸 sha 只读、冻结板 sha 未变、L4-A..E 可独立重算；
  对比历史/反例给出非零即失败（非静默零）。见 ledger / handoff。

## 5. 指纹
- 图纸 `m13_v57_w3_joint_assignment.json` rev W3-CN.22 `caa516abdaf8e823`
- construction `e50e2becaa921f09`｜validation `a8bf6c0f064dbc8a`｜dst board `8266989a38802ddd`
- 冻结四源 SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8`

## 6. 下一步
- **G7（L5 sign-off + learning review）**：SI/PI/EMC、DFM/DFT、制造记录 + 知识提升评审（记录是证据，不是修理许可）。
