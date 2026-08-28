# Card 1.2 归属声明 — 层2 渲染卡域化 + 层3 Power 列修订 + 全页容量预扫

> 归属声明（AGENTS.md §2.2 铁律 3）
> 日期：2026-08-26

## 归属
- **ECO 任务**: M13 v8 Card 1.1 后续阻塞解除（层2 标签碰撞 + 层3 Power 溢出）
- **修复类型**: ① 模型层（_shared 渲染器） ② 输入层（yaml 单行） ③ 预扫发现页（逐页验算追加）

## ① 模型层: `_shared/schlib/layout/wirerouter.py` resolve_pins 卡域化
- **根因**: Card 1.0 组件层 (ref,card) 泛化完成，但 Net 对象仍 card 无关（@N 节点在 net.pins
  中丢失卡维度）；WireRouter.resolve_pins 按 net.pins 遍历 → master 渲染 U1(卡1 实例) 时，
  GND 网的卡2 专属节点（U1/PA7@2 等）也被画到卡1 引脚 → 与 MUX_PD/SBU1/TPS_EN 标签同槽碰撞。
- **修复**: 标签生成改遍历放置实例的组件卡域网集（该实例真实连接的 pin→net）；
  net.pins 仅保留 spans_sheets 判定（连通性语义不变）。
- **契约**: 遵循 Component.card（禁止按 ref 首匹配取卡域数据）；零硬编码；单卡行为逐字节一致；
  真标签碰撞仍 raise；新增双卡同 ref 标签单测。

## ② 输入层: `ioconvert_v2.yaml` Power 页 columns: 2 → 3（仅此行）
- **根因**: Power 页（A4, cols=2, 17 器件全小件）列高溢出 [15,195]（实测 (27.9,190.5)-(73.7,210.8)）。
- **验算**: 3 列右缘 50.8+2*99.1+... = 256 < 282；列高 17 器件 6 行 × 20.3 ≈ 122 ≪ 195 ✓

## ③ 预扫发现页修订（步骤 3 结果，逐页验算后追加）
- **预扫结果: 6/6 页 PASS，无新增修订页**（Power 页已由 ② 覆盖）

| 页 | paper | cols | n | big | x_extent | y_extent | 结论 |
|---|---|---|---|---|---|---|---|
| Connectors | A2 | 2 | 12 | J14/J2/U11 | [27.9,500.4] <579 | [17.8,147.3] <405 | PASS |
| AC-Coupling Downstream | A2 | 3 | 26 | U3 | [30.5,388.6] <579 | [15.2,231.1] <405 | PASS |
| AC-Coupling Upstream | A2 | 2 | 28 | U7/J3/J4 | [30.5,505.5] <579 | [15.2,332.7] <405 | PASS |
| MCU & Sideband | A3 | 3 | 25 | U1(31脚) | [25.4,393.7] <405 | [15.2,203.2] <282 | PASS |
| Power Decoupling | A4 | 3 | 12 | — | [30.5,269.2] <282 | [17.8,88.9] <195 | PASS |
| Power (12V) | A4 | 3 | 19 | — | [30.5,271.8] <282 | [17.8,162.6] <195 | PASS |

- 工具: /tmp/opencode/card1_2_prescan.py（一次性，复用 layout_sheet 干跑，零写盘）

## 口径
- M-D 基线数字全部作废；本次一切数字 = 真实首跑新基线。
- eco_state 停在 ECO-S3 未动（输入又改，S2 复证先行）。
