# m13 v57 — W3（G4）开工卡 **v1.5**（W3-C5：撤下 v1.4 §R-15 + 按 D1 修订意图继续）

> 版本 bump（v1–v1.4 原文与指纹不动）。依据：监督 W3-C5 工单 + D0/D1 层意图修订卡（D1-1）。
> 基线 HEAD：`b8dd37f`。

## R-17（撤下 v1.4 §R-15）

v1.4 §R-15（「R1 极性同侧规则，待门放行后生效」）**撤下，不再作为契约条款**。
其内容按 C5-A2 改记为**上游变更请求项**（见 `m13_v57_w3_upstream_change_request.md` 第 5 项）。
W3 门失败态与本卡均**不夹带任何"待放行生效"的参数或规则**。

## R-18（门输入改为版本化层意图）

门 `resource_gate` 的可用过渡层改为**读版本化意图文件** `m13_v57_layer_intent_rev1.json`
（sha 钉住，权威 = `m13_v57_d1_layer_intent_revision_card.md` D1-1）：
`transition_eligible = [In2.Cu, In4.Cu, B.Cu]` ⇒ `A = 3 ≥ D = 3` ⇒ 门 `SUFFICIENT`。
判据闭式不变：`SUFFICIENT ⟺ D ≤ A ∧ lanes_needed ≤ lanes_avail`。

## R-19（层分配方法，确定性非搜索）

扇面组 `(corridor, band)` 的层由**区间图贪心着色**决定（按 `fan_y_extent` 起点升序，
取第一个未被重叠组占用的 `transition_eligible` 层；区间图贪心 = 最优，O(g·A)，g=4）。
每页的「chip 锚 → 走廊入口过渡 + 走廊 lane」同层直行（via₁ F→L、via₂ L→F，**每线 2 via**）。

## R-20（产物版本化，禁原地覆盖）

- 引擎每次运行同时写出：canonical `m13_v57_w3_joint_assignment.json` 与
  **版本化副本 `m13_v57_w3_joint_assignment_<REVISION>.json`**（同字节），使各版本并存、旧件哈希不变。
- 独立门工件 `m13_v57_w3_resource_gate.json`（每次运行必出，含 verdict/D/A/gap/fan_groups/着色）。
- 历史版本 `_W3-CN.1.json` / `_W3-CN.2.json` 由 git 历史恢复并纳入版本链。

## R-21（纪律）

冻结四源不动；零搜索（G-M1 令牌扫描 0）；契约修订一律新文件。

End of W3-C5 v1.5.
