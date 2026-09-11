# UC-01 上游变更请求 — **PCB 叠层需由 6L 重发为 LID.1 派生 8L**（G6/L4 硬阻塞）

> 2026-09-11｜发起：ARCHER（L4/G6 重评发现）｜级别：**owner / L2（结构性、涉制造）**｜状态：**待裁决**

## 1. 请求
请裁决下列二选一（现状无法继续 L4/L5）：
- **(A) 授权 8 层板重发**：按 `m13_v57_layer_intent_adoption_v1.json` 的 LID.1 叠层
  `F / In1(GND) / In2(sig) / In3(GND) / In4(PWR) / In5(GND) / In6(sig) / B(sig)` 重发 `k2_v4.kicad_pcb`。
  影响：板厚/叠层/阻抗/钻孔（blind In6↔In2 需背钻能力）/成本/交期；冻结四源将变更（需版本化新政 PCB）。
- **(B) 冻结 6L，接受 3 信号层**：则 8L 图纸作废，W3 须在 3 信号层下重解；owner 须就
  **A-CN.9 完整净距（SPEC clearance 0.175 / via-track 0.4525）** 放行或修订（前序实证：3 层下残余净距不可清零）。

## 2. 证据（可独立复核）
1. 冻结源 PCB 铜层 = **6**：`F.Cu/In1.Cu/In2.Cu/In3.Cu/In4.Cu/B.Cu`（sha `f6273de613f43d05`，四源之一）。
2. LID.1 派生件 `m13_v57_layer_intent_derived_v1.json`：`frozen_stackup_signal_layers=3`、
   **`frozen_stackup_sufficient=false`**、`L_escape=4`、`L_signal_derived=4`、`total_layers_derived=8`。
3. W3-CN.27 图纸（`13dfb9f4d74224d9`）up 带逃逸层 = `In6.Cu`；L4 构造记录含 **64 段 In6.Cu**。
4. 实测：对冻结 6L 板施加该图纸 → 板仍声明 6 层铜，却写入 **192 处 `In6.Cu`** ⇒ 无效板；
   L4-E `board != record`（64 网 + 64 via 失配）⇒ **G6 无法 PASS**。
5. 前序经验（同波次）：8L（CN.26/27）在 A-CN.9 完整净距下可收口 `FEASIBLE_ALL`（0/0/0）；
   6L（3 信号层）时代仅在旧口径（无净距谓词）下报过 FEASIBLE_ALL，L5 暴露 tt/vt。

## 3. 不做的事（红线）
- 不修改冻结四源（含 PCB）；不伪造 L4-E / G6 sign-off；不以 6L 板承载 In6 图纸。

## 4. 裁决后动作
- 选 (A)：重发 8L 冻结板（版本化）→ 更新四源 sha → 重跑 L4（G6）→ L5（G7，含 O4 对内等长）。
- 选 (B)：撤销 LID.1 采用 → 回 W3 在 3 信号层下重解（并在 owner 放行/修订净距口径后重跑 W3→W4→L4→L5）。
