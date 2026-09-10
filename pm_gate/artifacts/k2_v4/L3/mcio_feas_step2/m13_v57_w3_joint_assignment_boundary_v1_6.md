# m13 v57 — W3 Boundary **v1.6**（W3-C6：撤 D1-1 / 回退劣化变体 / 验证式门）

> 契约 `m13_v57_w3_kickoff_card_v1_7.md`（sha `b44de1e3…`）｜引擎 rev **W3-CN.5**
> 取代 v1.5 boundary（`17de2433…`）。授权来源：**监督工单 W3-C6**（非 L2）。

## C6 整改对照

| 项 | 落实 |
|---|---|
| C6-1 撤 D1-1 | `m13_v57_layer_intent_rev1.json` 作废；撤回声明 `…_withdrawal.md`；`REV2` 意图 = **仅信号层** `[In2.Cu, B.Cu]`，**In1/In3/In4 平面不作信号用途** |
| C6-2 重选最小合法变更 | 合法杠杆清单（lane 按源序 / no_90deg 通道化 / 极性同侧 / 自适应步长）入请求卡；本轮实测「极性同侧 + 自适应步长」**劣化** ⇒ 回退 |
| C6-3 不得退化 | 回退后门计量 **同层交叉 264 / R1 29-32 = W3-CN.2 基线**（无退化） |
| C6-4 溯源更正 | 撤回声明首段明确：D1-1 授权来源是**监督工单 W3-C5**，此前标注"L2 授权"有误 |
| C6-5 继续闭环 | **未收敛**：未达 `FEASIBLE_ALL`，亦未给**全局**不可行证明 ⇒ 循环继续；门（验证式）正确阻断并出请求卡 |
| C6-6 纪律 | 零搜索（G-M1 0 命中）；冻结四源 MATCH；契约/意图修订全部版本化新文件 |

## 门语义（R-23，验证式，零搜索）

`resource_gate`：以意图层做一次**闭式构造**并统计**同层**交叉；
`SUFFICIENT ⟺ 同层交叉 == 0 ∧ lanes_needed ≤ lanes_avail`；否则 `UPSTREAM_CHANGE_REQUEST`
（工件仅含 `resource_gate` + `upstream_change_request`，**不夹带任何求解结果或待放行规则**）。

## 当前离线（W3-CN.5）

- 门：`UPSTREAM_CHANGE_REQUEST`（`same_layer_crossings=264`, `r1_assigned=29/32`）
- 可用过渡层：`A=2`（`In2.Cu`, `B.Cu`）；**未使用** In1/In3/In4
- 下一轮首选杠杆：**lane 序按源序排**（闭式依据：`sign(Δsrc_y)=sign(Δlane_y)`）
