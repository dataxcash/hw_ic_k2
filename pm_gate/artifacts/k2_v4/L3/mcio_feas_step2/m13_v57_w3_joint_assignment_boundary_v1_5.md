# m13 v57 — W3 Boundary **v1.5**（W3-C5：v1.4 §R-15 撤下 + D1 意图继续）

> 契约 `m13_v57_w3_kickoff_card_v1_5.md`（sha `b717f1c7…`）｜引擎 rev **W3-CN.4**
> 取代 v1.4 boundary（`3b538b86…`）。

## 1. W3-C5 合规整改对照

| 项 | 证据 |
|---|---|
| A1 禁原地覆盖 | `m13_v57_w3_joint_assignment_W3-CN.1.json`（`dd19a9ad`）/`_W3-CN.2.json`（`f599dad0`）由 git 历史恢复并入库；引擎此后每次同时写 canonical + `_<REV>.json`（`_W3-CN.3.json` `c7abb47f`、`_W3-CN.4.json` `24cc4b64`），旧件哈希不变 |
| A2 撤下 W3 内调参 | card v1.5 §R-17 明确撤下 v1.4 §R-15；其内容改记为请求卡第 5 项 |
| A3 独立门工件 | `m13_v57_w3_resource_gate.json`（`e940dc2f…`）每次运行必出，含 verdict/D/A/gap/着色 |
| A4 父仓 bump | 见 `chore(ic_hw): bump k2(...)` 提交 |

## 2. B 段（回上层解决）结果

- **D1-1 已裁**：放行 `In4.Cu` 作过渡信号层（最小合法变更，`A: 2→3`），意图落
  `m13_v57_layer_intent_rev1.json`；冻结四源未动。
- 门复跑：`SUFFICIENT`（`D=3 ≤ A=3`）→ 进入求解（非停摆）。
- W3-CN.4 实测：同层交叉 **264 → 30**（3 层确定性区间图着色）；R2/R3/REFCLK 构造可行；
  R1 部分赋位失败（步长 1.2 + 同侧规则下 3 页域内无槽）。
- 收口判定：**CERTIFICATE（真不可行证书路径）** —— 未达 `FEASIBLE_ALL`；
  残余项已全部转入上游变更请求卡（第 5/6/7 项），不在 W3 内调参。

## 3. 纪律核对

冻结四源 MATCH（`0bd52ed4` / `a8ef3ea8` / `f6273de6` / `0a459839`）；零搜索 G-M1 令牌 0 命中；
`work_units = 534 = 11·32 + 2·72 + 6·2 + 3·6 + 8(gate)` 自洽。
