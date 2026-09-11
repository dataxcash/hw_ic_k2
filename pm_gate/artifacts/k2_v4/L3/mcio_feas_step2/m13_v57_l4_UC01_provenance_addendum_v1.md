# UC-01 追加证据 — 6L 叠层来源归因 + 冻结基线自洽性（G6/L4 阻塞根因）

> 2026-09-11｜发起：ARCHER（续接会话；仅读 handoff / ledger 尾 / 小工件）｜性质：**UC-01 证据补强 + 归因**
> ｜不改裁决项、不改冻结四源｜状态：**待 owner**

## 0. 冻结校验（前置）
四源 4/4 MATCH：`spec 0bd52ed48e720b8c / manifest a8ef3ea8ecff99d7 / pcb f6273de613f43d05 / rules 0a459839e15960b8`。
本追加**未修改任何冻结四源**；未覆写 canonical；探针仅落 `/tmp/opencode`。

## 1. 新增事实（可复核：命令 + 文件:行）
1. **授权生成器自身 natively 8L**：`k2/tools/k2_gen_v5.py:427-434` 的 HEADER 声明 **8 层铜**
   `F.Cu(0)/In1.Cu(4)/In2.Cu(6)/In3.Cu(8)/In4.Cu(10)/In5.Cu(12)/In6.Cu(14)/B.Cu(2)`，
   与 **LID.1 派生叠层逐层一致**（F(sig)/In1(GND)/In2(sig)/In3(GND)/In4(PWR)/In5(GND)/In6(sig)/B(sig)）。
2. **冻结 PCB 仅 6 层**：`k2_v4.kicad_pcb` 头部 `(generator "pcbnew")`，铜层 = `F/In1/In2/In3/In4/B`（无 In5/In6）；
   且为**裸骨架**：`0 segment / 0 via / 0 zone / 42 footprint`。
3. **git 考古（层数变更点唯一）**：板为 **8L** 于 `1a883b8`、`c6d6373`；`In5.Cu/In6.Cu` 于
   **`0db5183`「M14 v30 scope-B 真板物理 ECO + A/B 端口对账修正（用户/架构裁决）」被删除** → 6L；
   随后 `8c1624b` 把 SPEC `layer_plan` 再生为 6L（"stale 8L/U3-U7 施工段清理"）。
4. **LID.1 派生可复现**：`python3 tools/p3_v57_layer_intent_derive.py --out /tmp/opencode/lid1_rerun.json` 与
   `m13_v57_layer_intent_derived_v1.json` **逐字节相同**；8L 由 `L_escape=4`（chip_field depth=4）确定性推出。
5. **生成器自身陈旧**：其 `BOARD` 常量 `y[33,71]`（`:47`）与冻结 SPEC `board.outline_y=[33,79]`
   （note `y 38mm->46mm (L1_TOPOLOGY_v2.0 board-frame frozen, v20 user ruling H1)`）不符 ⇒ 运行即
   `写盘阻断 (fail-fast): SPEC 板框 ... 与冻结板框 {...y[33,71]} 不符`。故生成器**当前不可运行**，
   其 8L HEADER 只反映 M14 v30 之前的层表，**不足以单独证明「意图 8L」**。
6. **冻结 PCB 板框自相矛盾**：`Edge.Cuts` 左边 `(23,71)->(23,33)` 止于 y=71，右边 `(143,33)->(143,79)`
   与下边止于 y=79 ⇒ 38mm/46mm 撕裂混存，与 SPEC 板框（y=79）亦不一致。

## 2. 归因（修正 UC-01 §1 的冲突表述）
- UC-01 现状写作「owner 二选一：8L 重发 ／ 6L+净距放行」。
- 归因结果：**6L 不是无权工单产物，而是 `0db5183`（M14 v30）「用户/架构裁决」的物理 ECO**；
  **8L 是整改 `#03` 之后的容量闭合派生输出（LID.1）**。
  ⇒ 本阻塞实质是**两条裁决冲突**：M14 v30（6L 物理叠层） vs 整改 #03（层拓扑须为容量闭合派生 → 8L）。
- 故 **选项(B) 不只是「放宽净距」**：它等价于让 owner/工单参数**否决**派生叠层 ——
  正是 #03 明文撤销的「owner 参数特权」。若确采 (B)，正确形式不是「放行净距」，而是
  **把「6L 物理叠层」升格为该派生的一个冻结硬输入**（修订派生规则 = 冻结叠层为 binding input）后重跑派生；
  若 3 信号层仍不闭合，再按第九章升级（扩资源域 / 修订净距 / 回 L1 拓扑），禁在 L3 私了。
- 另：冻结 PCB 骨架在**两处已陈旧**（6L vs 派生 8L；板框 71/79 撕裂 vs SPEC 79），
  故无论 A/B，**基线骨架都需按当前 SPEC 重新冻结一次**（版本 bump 新文件，非原地改）。

## 3. 收窄后的 owner 闸口（请裁决其一）
- **(A′) 派生优先（推荐，与已收口的 W3-CN.27 一致）**：确认 #03 派生叠层（8L）binding ⇒
  以**新版本化骨架**替换冻结 PCB 基线（载入当前 SPEC 板框 y=79 + LID.1 8L；骨架 0 track ⇒ 纯放置保持），
  同步修订 `k2_gen_v5.py` 陈旧常量（`BOARD`）与 8L 层表；并把 **O4（pair-aware 落列）并入同一次修订**；
  之后重跑 W3→W4→L4(G6)→L5(G7)，重签 G4/G5/G6/G7。
- **(B′) 物理约束优先**：确认 M14 v30 的 6L 为**硬物理约束** ⇒ 将「冻结叠层 binding」写入 LID 派生输入并重跑；
  若 3 信号层不闭合，按第九章升级（资源域/净距/回 L1），不得 partial pass。

## 4. 红线遵守与旁证
- 未改冻结四源；未新增/覆写 canonical；探针仅落 `/tmp/opencode`；未伪造 L4-E / G6 sign-off。
- 并项复核 **O3（L4 REFCLK 网名）已修**：`tools/p3_v57_l4_apply_drawing.py:60-67`（注释 `ROOT-21 ... (O3)`）
  使用 `rv["nets"][pol]`；construction 记录含 `PCIE_REFCLK0_P/N`、`PCIE_REFCLK1_P/N` ⇒ 无需再动。
