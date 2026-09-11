# W3 8L 重跑进展 v2 — 残余净距 43 → 12（波 1→2 续）

> 2026-09-11｜引擎 rev **W3-CN.26**｜LID.1 8L 派生叠层（signal=F/In2/In6/B）
> canonical `m13_v57_w3_joint_assignment.json` **未改**（W3-CN.25/FEASURE_ALL/c17c5a42）；四源 MATCH。

## 净距残余收敛（完整套件：tt 0.38 / vt 0.4525 / vv 0.525）
| 迭代 | crossings | R1 | tt | vt | vv | 合计 |
|---|---|---|---|---|---|---|
| 8L 初版（带分层） | 0 | 32 | 13 | 27 | 3 | 43 |
| + 域 v1.3（min+max） | 0 | 32 | 12 | 27 | 0 | 39 |
| + 域 v1.4（pad-proximate） | 0 | 32 | 12 | 24 | 1 | 37 |
| + 带向 x 偏置 ±0.3 | 0 | 32 | 6 | 15 | 0 | 21 |
| + 竖段同层间距 ≥0.38 | 0 | 32 | 3 | 10 | 0 | 13 |
| + pad 邻近主键 | 0 | 32 | 3 | 8 | 1 | **12** |

## 本轮改动（全部确定性，零搜索）
1. 通道层按带分层：dn→B.Cu / up→In6.Cu / run→In2.Cu（4 信号层）。
2. F-13 域升 **v1.4**（min-dist + max-dist + **pad-proximate** 实现/列对；producer `p3_v57_f13_pair_coupling_r2_v4.py`，537713 rows）。
3. R1 带向 x 偏置（dn +0.3 / up −0.3）→ 分离相邻行 F.Cu breakout。
4. 逃逸竖段**同层间距 ≥0.38**（`_esc_ok` 层感知）。
5. `_key` 主键 = pad 邻近（短 breakout）。

## 残余（12：tt 3 / vt 8 / vv 1）— 已定位
- **连接器 landing stub**（`DN6/DN7 out_MCIO @0.3162`、`UP0/UP1 input @0.3162`）：相邻 pad 的 F.Cu landing 段 <0.38。
- **同带相邻 breakouts**（`UP0/UP1 out_J2 @0.2458`）。
- 少量 via↔track（vt）。

## 下一步（同波）
R3 landing 加入 ≥0.38 间距约束（landing stub 分离）；R1 主键再加净距谓词 → 残余清零 ⇒ `FEASIBLE_ALL` ⇒ landing 重发射 ⇒ W4→L4→L5。
