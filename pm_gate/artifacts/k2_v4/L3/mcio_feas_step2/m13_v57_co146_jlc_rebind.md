# CO-146 卡 · 定性更正 + 登记（监理指令 #10 动作 5）

- 监理指令 #10 出处 `.omo/supervision/ledger/instruction-10-jlc-prototype-ready.md` `35aafe268ff52f89`
- 登记簿 `L2/input_defect_register_v1.json`：20 → **22** 项（OPEN 3）；CO-146 项：['implementation_deviation:asbuilt_via_strategy_requires_blind_buried', 'implementation_deviation:solder_mask_bridge_jlc_min_1x']
- SPEC 逐字节不变：`5f72182a2616392c`｜板 `d4e81f647be7f980`

## 定性更正（撤回「外部输入阻塞」）

### 阻抗终判
- 旧：SI9000 + 板厂阻抗券（`coupon_required=true`，语义 = 等外部券）
- 新：**JLC 阻抗控制服务**（免费标准阻抗测试 / ±10% 控制）+ 监理定值叠层 JLC08161H

### PDN 压降 · 热
- 旧：外部 PM 输入（CO-87 两项 NOT_DEMONSTRATED）
- 新：监理定值（压降 3% / 40°C 自然对流 / 外层 1oz+内层 0.5oz）+ CO-146 一阶确定性评估

### 「外部输入阻塞」表述
- 旧：「板厂券 / PM 数据 = 外部阻塞」（CO-105/CO-107/CO-133 等记录残留表述）
- 新：**撤回**（改绑 JLC 工艺 + 监理定值）。**同时登记新发现的真实阻塞项**：盲/埋孔 —— JLC 标准服务不支持（见登记簿 OPEN 项 + co146_through_via_probe）。

## 交付物 verdict

- impedance: **PASS**
- pm: **PASS**
- dfm: **FAIL**
- through_only_feasible: **False**
- orderable_at_jlc_standard: **False**

