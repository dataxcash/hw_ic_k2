# CO-145 — lane-run 蛇形幅度守卫并入对间 3W（L2 自裁）

- verdict：**PASS**

## 根因
- 工具：`tools/p3_v57_w3_constructive.py:co16_o4_amp_table`
- 旧守卫：`gap = |Δy| - VT_TRACK(0.4525) - MARGIN(0.02)（无 3w 项）`（**无 3w 项**）
- 新守卫：`gap = |Δy| - max(VT_TRACK, 3w(In5)=0.48) - 0.005（仅异对邻道）`
- 为何须动 lane 步距：meander_zig 在幅度 <~0.071(DN0/out_MCIO)/~0.075(UP6/input) 时无法在 run 内实现等长 ⇒ 仅压缩幅值会退化（实测 SI 0.2062）；故增 lane 步距留空间

## 机判（板级）
- In5 对间最小铜边：0.3125 → **0.325 ≥ 0.32**（ok=True）
- B.Cu：{'min_edge_mm': 0.445, 'ok': True}
- L5 SI：0.13（ok=True）；DRC 42(+0)（CO-133 B_drc_neutral）

## 残留（非本件）
- **F.Cu J2 landing（connector 0.6 节距 < 3w=0.615 ⇒ 接口固有不可达）⇒ L1/owner**。
