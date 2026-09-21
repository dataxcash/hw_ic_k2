# R4 复测闸 · 就绪度盘点（2026-09-22）

| # | 判据 | 状态 | 证据件 | 缺口 |
|---|---|---|---|---|
| 1 | 19 维判定器 | @l8 = **19/19 PASS**（@errata-3）· @冻结原件 17/19（2 FAIL 恰为授权 errata） | R259c 件 / E3-…-rerun/ | l9 须同口径重跑 |
| 2 | ②-UP (16/16 ≤2via 全In5) | ⛔ **未取得**：合法 12/16 · 全转落板 12/16(7err/4unconn) · ② 指派 FEASIBLE · 逐条可达 16/16 · 割线容量 42≥16 | R259c/e/g/h/j/m | **`C-B2UP-1` 限期**（同时性束布线） |
| 3 | ②-DN | #K2-73 具名豁免 **EX-1**（l8 拓扑） | #K2-73 | l9 落库同批豁免表 |
| 4 | ref_plane_continuity | @l8 = **0.0 mm²**（须==0 · R=0.5mm） | R259c（v3-plane/refplane-gap 测量） | l9 须重测 |
| 5 | 等长（In5 N/P skew） | @l8 **基线已测**：max skew 6.002mm@pair4 · ΣN409.5/ΣP396.0 | R259i 件 | **l9 须同口径重测**；阈值口径待具名 |
| 6 | 3W / 85Ω | 未测（85Ω 文档见 archive `04_impedance/impedance_table.md`；阻抗券属 P5 外部） | archive 04_impedance | ENG 可测 3W（l9）；85Ω = P5 |
| 7 | ⑪ 自报 sha16 | 约定A 已用（监理 #K2-133 §一 复算 MATCH） | R259b/c | · |
| 8 | ⑫ 尺度/pitch 变更附守恒级存在性 | **不适用**（本改无尺度变更 · 仅动本网几何） | · | · |
| 9 | 前置：平面落图/铺铜/钻孔 | **全 PASS**：In1/In3/In6 G36=1·In4=9 · 铜区 10/10 · NPTH=4 & PTH=16 | R259c | l9 须重测 |
| 10 | criteria **rev=7** | ⛔ 未落（gate 属主 `ic_hw_gate`）· 齿 `layout_and_assembly_quality` + courtyard/pth_inside_courtyard 豁免 + EX-1 | R259l 预核（l8：54 枚无 courtyard · error0/unconn0） | **与 l9 落库同批** |
| 11 | l9 落 `hw/` | ⛔ 待 ②-UP 收口 + rev=7 | · | 硬前置 rev=7（#K2-133 D3） |
| 12 | spec-rev-55 | ⛔ 未落（在册最新 = **rev-54**） | L3/SPEC_k2_v4.spec-rev-54.json | 与 l9 同批 |
| 13 | Gerber/钻孔/打包 | **管道就绪**（新导出 14 gerber + 8 Excellon 含 HDI 盲埋孔；在册包 owner#14③ 8 项齐备） | R259k 件 / tarx 包 | l9 须**同批重出包 + 重跑 DFM** |
| 14 | P5 打样 + 首件 bring-up | **外部/商务**（owner ④：不属 ENG 任务/阻塞项） | · | P4 全绿后方可下 |

**唯一硬卡点 = ②-UP**（其余全绿或仅待 l9 同批重测/落件）。**owner 闸口 = 0**。
