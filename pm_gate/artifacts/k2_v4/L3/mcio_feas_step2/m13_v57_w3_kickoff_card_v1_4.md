# m13 v57 — W3（G4）开工卡 **v1.4**（W3-C4：上游资源充分性门 + 升级语义）

> 版本 bump（v1–v1.3 原文与指纹不动）。依据：监督下发 W3-C4 整改工单（2026-09-10）。
> 天条落地：**发现上游问题立即停机回上层**；禁止在 W3 内调参绕过。

## R-13（新增：W3 入口「上游资源充分性门」）

**门定义（机器可判、闭式 O(n)，置于 `main()` 最前，先于 R1/R1.5 求解）：**
1. 层意图资源表：`F.Cu`=stub_only；`In2.Cu`/`B.Cu`=transition_eligible；`In4.Cu`=power_plane(SPEC)。
   `A := |transition_eligible|`。
2. 扇面组 = `(corridor, band)`（4 组）；每组 `fan_y_extent = [min(src_y ∪ lane_region_y), max(...)]`，
   `src_y` 取冻结 manifest chip 锚，`lane_region_y` 取 §R-9 分段区意图。
3. **层需求 D** := 同一 chip 过渡 x 带（`[82.35,105.25]`）内 `fan_y_extent` 的**最大重叠数**
   （区间图团数 = 端点扫描，O(g log g)，g=4）。
4. **容量**：每走廊 `lanes_needed(16) ≤ lanes_avail(32)`。
5. `verdict = SUFFICIENT ⟺ D ≤ A ∧ 容量 OK`；否则 **`UPSTREAM_CHANGE_REQUEST`**，
   **不进 R1/R1.5 求解**（不产出任何赋位/图纸）。

**实测（本卡基线）**：`D = 3`（y≈55.15 处 `EAST/up + WEST/up + WEST/dn` 三扇面重叠）、`A = 2`
⇒ **不足**，缺口 `Δ = 1` 层。

## R-14（升级语义 + 配套件）

- **`CERTIFICATE` = 升级触发器，不是终点**：出证书（或门失败）时**必须同时出**
  `m13_v57_w3_upstream_change_request.md`（上游变更请求卡）。
- 请求卡内容（每项附闭式依据）：① In4.Cu 可否作信号层（依据 `D ≤ A`）；② `no_90deg` 是否放宽
  （依据折线通道互斥谓词）；③ lane 序可否按源序排（依据 `sign(Δsrc_y)=sign(Δlane_y) ∀a,b`）；
  ④ R1 全局单调 x 是否放行（须放宽 ±1.5mm 逃逸域，依据 §R1 前缀单调可行性）。
- 门失败工件：`m13_v57_w3_joint_assignment.json` 内落 `resource_gate{...}` + `landing_rows_status=NOT_REEMITTED`。

## R-15（R1 极性同侧规则，随 v1.4 生效）

R1 的 N 侧吸附限定在 **与帧方向 `s` 同侧**（`(N_x − P_x)·s > 0 ∧ |Δx| ≥ SLOT_SEP − GRID`），
以消除同带内 P/N 反向导致的扇面交叉（闭式，非搜索）。

## R-16（纪律）

冻结四源（SPEC/manifest/PCB/rules）不动；零搜索纪律不变（G-M1 令牌扫描继续为 0）；
契约修订一律新文件（本卡即 v1.4，禁止原地改 v1–v1.3）。

End of W3-C4 v1.4.
