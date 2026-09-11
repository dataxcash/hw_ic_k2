# 变更单 CO-02 撤销补充 — R-03「层数=owner 参数裁决」**撤销**（整改 #03）

> 2026-09-11｜作者：ARCHER｜触发：整改通知 #03｜**本条撤销 CO-02 中把层数作为 owner 裁决的表述**。
> 版本纪律：CO-02 已入库（commit `37ca019`）；**不原地改写**，以本补充件撤销其 R-03 定层。

## 1. 撤销内容
| 原 CO-02 表述 | 处置 |
|---|---|
| R-03「若 L2 选中 8L，则须**层数裁决重开**（owner）」 | **撤销**——层数不是 owner 参数；见 §2 |
| 「owner 授权后版本 bump SPEC stackup/pd 重冻结」作为**决策** | 降级为**机械版本化**（层集已由机制派生，实现仅需版本 bump） |
| `m13_v57_l2_structural_envelope_v1.json` 的 `status=PENDING_OWNER_RATIFICATION`（因层数） | **superseded** by `..._envelope_v2.json`（层数 = DERIVED） |
| 保留有效的 R-01/R-02/R-04 | R-01（叠层重开）→ 由派生器给出；R-02（走廊/过孔/等长+硬门禁）保留；R-04（重跑 W3→L4→L5）保留 |

## 2. 定层纠正：层数是**机制派生输出**，非 owner 特权
- 层意图曾被工单/修订卡设定（`layer_intent_rev1/2/4.json`：authority=D1 卡 / W3-C5 / W3-C7），
  闭式仅 `SUFFICIENT iff D ≤ |给定层集|` ⇒ 机制无自主路径（根因见 `m13_v57_root_cause_layer_intent_mechanism_v1.md`）。
- 修复：`L_signal = max(L_escape, L_capacity, L_conflict, 3)`，`total = 2·L_signal`，全部由**冻结四源 + 规则**派生
  （引擎 `k2/tools/p3_v57_layer_intent_derive.py`，输出 `m13_v57_layer_intent_derived_v1.json`）。
- 本板派生结果：`L_signal=4 → 8L`（signal = F/In2/In6/B），**冻结 6L（3 信号层）不足** ⇒ `DERIVED_STACKUP_REQUIRED`。
  ⇒ 8L **不是** owner 选择的参数，而是容量闭合的**推导结论**；L2 层叠修订为**机械版本化**，不设 owner 闸口。

## 3. 其它 owner 表述的界定（防再次误升级）
- **本板层数/层用途**：机制派生（无 owner）。
- 仍属系统设计红线、不得由机制擅自变更者：**层用途物理语义红线**（不得把 GND/PWR 平面改作信号）；
  派生器只在「signal 层数」上派生，平面/电源层语义由规则固定（PWR 固定 In4，GND 夹心）。
- 冻结四源原件不动；SPEC 层叠落地为版本 bump（机械）。

## 4. 纪律
零搜索/零暴力迭代；四源 SHA MATCH；canonical `W3-CN.25` 不动；派生物版本化新件。
