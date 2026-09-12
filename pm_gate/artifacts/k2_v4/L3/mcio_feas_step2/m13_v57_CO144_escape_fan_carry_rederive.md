# CO-144 — 逃生扇落位策略重派生：分带单调 carry + PDN 障碍场（L2 自裁）

- verdict：**PASS**（32/32；B.Cu 对间 3W 0 违规；板级 DRC 中性；L4 viol 0；L5 SI 0.1300）
- 关闭：`tool_defect:k2_router_escape_fan_omits_3w`（OPEN → CLOSED）

## 事由
CO-141 定位「逃生列距基准漏 3W」→ CO-143 修正真实所在 = `p3_v57_co10_west_fan_probe.py:check()`
（track-track 判据 `TT=WID+CLEAR=0.38` 无 `3*w(layer)` 项）；CO-143 机判「3W 可满足，但单遍贪心 + PDN 障碍下
31/32（rev）/30/32（xasc）⇒ 须重派生落位策略」。

## 实现（opt-in，默认关 ⇒ ALLOC.1..7 逐字节可复现）
- `CO10_FAN_STRAT=carry`：带内按 (corridor,band) 连续；处理序自适应方向（rev 序东→西）；
  游标 `cur` = 已落位列极值；候选须 `min(列x) ≥ cur+3w`（正向）/`max(列x) ≤ cur−3w`（反向）；
  按游标增量最小取首可行（零回溯/零坐标搜索）。仅外层逃逸带命中（3W 界 0.615；B.Cu）；
  内层 In2/In5（0.48）实测已合规且 carry 会扰动跨带 via 净距 ⇒ 保持 canonical。
- `CO10_PDN_OBS=1`：SPEC `pd.zone_defs`（zone vias / gnd_stitch 未 blocked / decoupling / ppc via+stub）
  作为固定障碍喂入 `check()`（此前扇对 PDN 视而不见）。
- CO-144b/c：carry 只搬列**不翻转对向**（`(px−nx)·(padP_x−padN_x) > 0`）——翻转会改对内拓扑（实测 DN7
  对向翻转 ⇒ SI skew 0.328）；carry 带锚页改用 pad 邻近序（`_ip3w_targets` 的 P=N+VT 与不翻转相悖）。

## 机判（`m13_v57_co144_escape_fan_carry_rederive.json`）
| 项 | 值 |
|---|---|
| 落位 | 32/32 |
| B.Cu 对间平行(≤10°)最小中心距 | **0.65 ≥ 0.615**（原 14 对-对 <2w ⇒ 0） |
| In2 | 0.58 ≥ 0.48（0 违规） |
| PDN 障碍 | 241 via / 185 seg |
| 板级 DRC（kicad-cli --severity-all） | **42 → 42（0 新增）** |
| L4 校验 | viol 0 |
| L5 | DFM new=0；SI 0.1300 PASS |

## 残留（非本件）
- **F.Cu J2 接口 10 对**（0.6 节距 < 3w，路由不可消除）⇒ **L1/owner**（J2 3W 适用域）。
- In5 斜交口径 / 板厂券 ⇒ 外部输入。
- `implementation_deviation:R3-2_asbuilt_interpair_edge` 保持 OPEN（范围已收窄）。

## 红线
不改 SPEC/阈值/冻结四源；carry/PDN 为 opt-in；板经 CO-133 PDN 施工 + canonicalize（字节可复现）。
