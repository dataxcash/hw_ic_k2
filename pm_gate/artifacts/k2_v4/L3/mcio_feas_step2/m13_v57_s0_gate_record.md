# m13 v57 — S0 门禁记录（权威端点模型 + 单向审计）

> 阶段验收（m13_v57_execution_plan.md S0）。全部谓词由机器产出，见两个工件：
> `m13_v57_s0_endpoint_model.json`（模型 + 派生一致性）、`m13_v57_s0_audit_derived.json`（审计）。
> 工具：`tools/p3_v57_s0_endpoint_model.py`、`tools/p3_v57_s0_audit_derived.py`。

## A0 谓词结果（全过 → 允许进 S1）
| 谓词 | 结果 | 机器证据 |
|---|---|---|
| A0.1 端点模型可复现 | ✅ | 同输入双跑全文件字节一致（sha 相同）；含 sch/ballmap/board 指纹 |
| A0.2 溯源完备（权威源单向） | ✅ | 68 网 = k2_sch 网表语义（connector-pin ↔ chip-ball）；芯片 64 数据网：期望球位(ballmap+放置) vs 板 pad 实测 **64/64 吻合(≤0.05)** 且 **pad#==球名 64/64**；连接器 68/68 网名到位；REFCLK 4 直通无芯片端。无任何端点来源="窗口扫描/反猜" |
| A0.3 差异清单落盘 | ✅ | escape_spec：32 引脚坐标帧不一致 + 32 引脚网名(*_U3/_U4 stub)不在网表；landing 行：J2 36/36 锚对、MCIO 6/16 对 + **10/16 错锚到芯片端**（DN_OUT0-4，B1 max-x 根因）、U3/U7 0 行 |
| A0.4 无未裁差异进入生成 | ✅ | 当前无图纸生成路径消费这些派生物；全部差异标记 authority-first（权威优先待改）；错锚/错帧源（escape_spec 引脚坐标、max-x 窗口锚）不进 S1 生成器输入 |

## 关键事实（本轮钉死）
- 板上 U6 封装 = DS320PR1601，354 pad == 手册 354 球 **1:1**（派生物忠实铁证之一）。
- KiCad 存储 rot ↔ 数学 rot 约定：**−rot**（A_PERP0 球实证 (84.85,57.12)）。
- 网名链 = k2_sch 全链名（含 `*_OUT*_MCIO/_J2`）；REFCK = J2↔J3/J4 直通不经芯片。

## 遗留（进 S1 前无需关闭，但记录）
- escape_spec：仅保留"逻辑芯片 U3/U7=DN/UP 分组"历史语义；其引脚坐标帧与 stub 网名
  不再作为任何几何/端点输入（authority-first 取代）。
- 现存 landing 行（连接器区）10 行错锚 = 旧生成逻辑缺陷；S1 生成器以权威端点为唯一锚源，
  不再消费窗口/max-x 派生。
