# CO-17 —【L2/L3 停机】CO-16 O4 双段蛇形：**容量模型可闭合，几何实现不可行**（列/层距不足）

> 2026-09-12｜裁判：ARCHER（L2 走廊/等长/过孔策略，自裁；无需 owner）｜性质：**否定结果 + 模型缺口**
> 触发：handoff `k2-v57-co16-fullboard-32of32-20260912c.md` §8「引擎 rev bump → ECO → 一次求解 → G4..G7」。
> 引擎：`tools/p3_v57_w3_constructive.py`（**默认 t2 路径逐字节不动**；新 `--r1-5-shape co16` = W3-CN.31）。

## 0. 四句结论
1. **CO-16 拓扑已实现且几何自洽**：`--r1-5-shape co16` 产出 320 via / 320 段，逐项 == `CO16-ALLOC.1`（`21ae78f8276d8df4`）；
   独立复核器 `p3_v57_co11_placement_verify.py` 对本引擎输出 **320/320, 0 违规 PASS**；`same_layer_crossings=0`；A-CN.9=0。
2. **O4 等长蛇形几何不可行**：`CO16-ALLOC.1` 的通道净距（西 lane 1.1265 / 东 J2 列 0.6）**小于**「相邻通道双侧蛇形」所需
   `2·A_min + TT = 2·0.269 + 0.38 = 0.918`；单侧 45° 蛇形亦受 `A + TT ≤ 通道净距` 限制。⇒ 引擎无法产出 FEASIBLE_ALL（verdict=CERTIFICATE，30 张 O4 证书）。
3. **DFM 实质改善但未归零**（拓扑-only、无蛇形；kicad-cli 10.0.5 + shop `k2_v4_8L.kicad_pro`）：
   `new_total 426 → 175`（clearance 176→19 / shorting_items 108→11 / solder_mask_bridge 103→42 /
   hole_clearance 24→0 / tracks_crossing 4→1；copper_edge_clearance 10→**29**）。
4. **本会话未改任何冻结原件**；canonical 保持 W3-CN.30 `05f7bd10ab3b45b6`（未 promotion）；无 sign-off；无 tag。

## 1. 几何根因（闭式，可复算）
西侧（`CO16-ALLOC.1` lane_y = 33.3 + idx·1.1265，POL_OFF=0.25）：
- 同页 P/N 分隔 0.5；**相邻 lane 的近极性轨间距 = 1.1265 − 0.5 = 0.6265**。
- 单侧 45° 锯齿：自净距 = 1.414·A ≥ TT(0.38) ⇒ **A ≥ 0.269**；横向不撞邻轨需 `A ≤ 0.6265 − 0.38 = 0.2465`。**无解**。
- 若相邻两条 lane 同向蛇形（本板 16 条 lane 全部需补偿）：`A ≤ (0.6265 − 0.38)/2 = 0.123`，更劣。
东侧 J2（`CO10_J2STEP=0.6`）：
- stub 竖段（In2）同侧邻列 0.6 ⇒ `A ≤ 0.22`（< 0.269）⇒ 45° 无解；退让为浅齿（A=0.22, a=0.3769）密度仅 **0.158**（45° 为 0.414）。
- 逃逸竖段（E 层）同侧邻距 0.7（东侧 up）⇒ `A ≤ 0.32`，容量 **够**（如 DN1/DN2）。
- **例外 `PCIE_UP0/out_J2 N`**：lane_y=56.41，而 E=B 的 via1 stack 在 In6 位于 y=55.82（仅 0.587 下方）⇒ lane-run 鼓出 `A ≤ 0.135` 无解；
  可用 lane 窗口被 stack 截断到 x≳94 ⇒ 容量 ≈ 13.2mm，需求 18.14mm；stub 浅齿容量再 +~2.0 ⇒ 仍缺 ~3mm。→ 该页为硬缺口。

## 2. 证据
| 项 | 值 |
|---|---|
| 引擎 co16 求解 | `m13_v57_w3_joint_assignment_W3-CN.31.json` `edf45d8e78ee4f0b`，verdict=**CERTIFICATE**，certs=30（O4），crossings=0，A-CN.9=0 |
| 独立复核（引擎输出） | `tools/p3_v57_co11_placement_verify.py` → **n_vias=320, n_segs=320, n_violations=0 PASS**（逐层/跨页/616 pad 场） |
| DFM（拓扑-only board） | kicad-cli 10.0.5 + `k2_v4_8L.kicad_pro`：new=**175**（baseline 42 → candidate 217）；分解见下 |
| canonical | `m13_v57_w3_joint_assignment.json` = **05f7bd10ab3b45b6**（W3-CN.30，**未 promotion**） |
| 冻结四源 | 4/4 MATCH（原件未改） |

DFM new 分解（co16 拓扑-only）：
`solder_mask_bridge 42 / copper_edge_clearance 29 / clearance 19 / shorting_items 11 / tracks_crossing 1 /
hole_to_hole 1 / holes_co_located 72(新增类型) / hole_clearance 0`

## 3. 附带发现（须并入下一周期）
1. **`holes_co_located` 72（新）**：L4 对 (vx,vy) 的 F↔In2 + In2↔In6 + In6↔B 叠层按 3 个独立 via 发射；
   物理等价于**单支贯通 F↔B 钻孔**。L4/引擎须合并同点叠层为单 via（含 span）后重测。
2. **净距口径缺口（handoff §8f）为真**：修「同页跨极性被 base(pid) 豁免」后，**W3-CN.30 canonical 的 A-CN.9 不再为 0**
   ⇒ 旧口径的 0 部分依赖该豁免。本会话已把该修正**限定在 shape=co16**，默认 t2 路径逐字节保持（否则 canonical 失真/回退）。
3. **`copper_edge_clearance` 10→29 恶化**：东侧 outer 列 142.6/135.0 接近板边，需 CO-17 一并裁。

## 4. CO-17 建议（L2，ARCHER 自裁范围）
- **(A) 放宽通道**：西 lane pitch 1.1265 → ≥ 2·0.269 + 0.38 + 0.5 = 1.418（或 POL_OFF 回收）；东 J2 列 pitch 0.6 → ≥ 0.918。
  工具现成：探针 `CO10_WSTEP` / `CO10_J2STEP` → 重派生 `CO16-ALLOC.2` → 复核器复算 → 引擎 FROZEN_SHA 同步。
- **(B) 容量感知着色**：置换仅对「短极 lane-run 容量不足」的页取小 offset（现口径按 max chip-pad x 排序，UP0 取到 k=8）
  ⇒ 可解 DN0/DN2/UP0 的 lane-only 闭合，仅 DN1 需第二段。
- **(C) 蛇形模型**：若接受浅齿（非 45°，密度 0.158）可部分闭合；不建议（SI/酸角）。
- **(D) 先做 3（叠层合并 + copper_edge）**：即便 O4 未闭合，也可先把 DFM 收敛（拓扑-only 已 426→175）。

## 5. 红线遵守
只读消费冻结四源（未改）；canonical W3-CN.30 未 promotion；默认 t2 路径逐字节不动；引擎零坐标搜索（AST while=0/enumerate=0）；
未放宽任何阈值；无 partial pass；无 sign-off；结论=否定（几何不可行）+ 模型缺口。
