# m13 v57 — W3 Boundary **v1.8**（ROOT-15 收口：FEASIBLE_ALL，含 stub 度量修正）

> 契约 `m13_v57_w3_kickoff_card_v1_22.md`｜引擎 rev **W3-CN.10**（`0032e96669a13402…`）
> ｜取代 v1.7（`9b9697bc28c050a9…`，保留不动）。
> 授权来源：**ROOT-15 执行令（监督下发）**；仅项目工件层修订；**冻结四源未动**；零坐标搜索。

## 1. 收口结论（机器可判）
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`。
- **`same_layer_crossings = 0`，`crossings_by_class = {r1_5: 0, stub: 0}`（stub 类**实际有段**，非空集）**。
- R1 **32/32**（64 via 两两 ≥ 0.525）；R2 帧内严格递增 + 双端谓词 ≤ 45.4mm；
  R3 **72/72**（同 gap 列 ≥0.525 且落点 ∈ y_band）；REFCLK 2 页与 keepout 零交。
- 34 页图纸：32 data 页（连续路由节点 + 过孔）+ 2 refclk 页；每线 **4 via ≤ 5**。
- **F-12 原子重发射**：`m13_v57_w3_chip_landing_rows.json`（`d6aed98d2411683a…`，64 行，rev W3-CN.10），
  `authority.main_sha256 == sha256(m13_v57_w3_joint_assignment.json)`（`29fe51bc6e08f2b2…`）。
- **W4 解封**。引擎 wall ≈ **6.5s** ≤ 120s 护栏；`work_units = 534 == 公式`；`--scale` work(2)=1052 / work(4)=2104 = K×526。

## 2. 本版三处修正（相对上一已达交付态）
1. **ROOT-15 证书作废语义**：顺序确定性放置（单遍、固定键 argmin + 0.525 净空谓词，读 F-13 v1.2 对域）
   已把 3 页（`PCIE_DN4/input`、`PCIE_UP1/input`、`PCIE_UP6/input`）赋位；对已赋位页，原
   `CONSTRUCTION_INFEASIBLE` 证书即失效（实现：已赋值即作废）⇒ `certificates = []`。R1 由 29/32 → **32/32**。
2. **stub 度量缺口修正（独立验证器发现，已修）**：
   (a) R3 赋值键为 `"<conn_ref>|<net>"`，旧 stub 循环用 `pid` 判定，守卫恒真 ⇒ stub 段从未入 `paths`，
   `stub:0` 是**空集**（vacuous），非实测零；已修。
   (b) `same_layer_crossings` 旧实现只取 `cls["r1_5"]`，**未并入 stub**，与 C17「stub 纳入 same_layer_crossings」相悖；已修为全类求和。
   (c) 修正后实测真实残余 = **46 处连接器侧同层交叉**（全部 stub 类，F.Cu），并据此给出下方构造修正。
3. **连接器扇出改 T-2 river（闭合残余、零搜索）**：stub 由「F.Cu 单段斜线」改为与 R1.5 同源的连续 river 路由：
   `F.Cu pad → via1 → B.Cu 逃逸竖段 → corner via → In2.Cu 走廊 run（延至 R3 landing 列）→ via_drop → B.Cu 竖落 → via_land → F.Cu landing → connector pad`。
   段型分层（竖段 B.Cu / 横段 In2.Cu），同层段按构造两两异 x 或异 y ⇒ **stub 46 → 0**，`r1_5` 仍 0；每线 4 via（≤5），不新增层、不动层叠。
   （等价定理：2 层通道 + dogleg 对任意落点置换可平面化，即 T-2/river 定理。）

## 3. 方法门（G-M，验证证据）
- **G-M1** 静态零搜索：去注释/去字符串后 NAME 令牌 0 命中（含 `while`/`enumerate`/`itertools`/…）→ PASS。
- **G-M2** AST：`while`=0；函数自调用=0；`itertools/random` import=0 → PASS。
- **G-M3** 闭式复杂度：`work_units == 11·n_pages + 2·n_landing + 6·n_refclk + 3·n_frames + 8`；
  `--scale` 探针 work(2)=1052 / work(4)=2104 = K×526（线性）；wall ≈6.5s ≤ 120s 护栏。
- **G-M6** 零备选痕迹：工件无 `alternatives/options/tried/branch/attempts` 键。
- **G-M4**（已知漂移）：`m13_v57_w3_validation.json` 仍为 T-2 之前快照；card v1.3 已记录 197 处契约↔实现漂移；
  按「禁原地改」未就地修改。**下一项 D8**：版本 bump 出 T-2/river 感知的独立验证器并重生成该工件。

## 4. 诚实登记 / 未决
- 本节 2.(2) 的度量缺口与 46 残余由**独立子代理复核**发现，非自证；本条留痕。
- D8（T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`）未完成，记为唯一未清项。
- `_shared` gitlink 偏差与历史未跟踪工件持续隔离，未混入本提交。

## 5. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH，未变） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | `tools/p3_v57_w3_constructive.py` rev **W3-CN.10** `0032e96669a13402…` |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.10 `29fe51bc6e08f2b2…` |
| landing | `m13_v57_w3_chip_landing_rows.json` `d6aed98d2411683a…` |
| F-13 v1.2 pair 域（消费） | `3a08c4634bbd1d5c…` |
| resource / R-23 gate | `m13_v57_w3_resource_gate.json` `0a474617b6b42f73…`（SUFFICIENT）|

End of boundary v1.8.
