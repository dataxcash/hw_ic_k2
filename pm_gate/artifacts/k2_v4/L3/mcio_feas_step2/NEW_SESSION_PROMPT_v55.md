# NEW SESSION PROMPT — v55 Phase 3（flip=True 展开 bug 修复 = K2 自动布线的总钥匙）

## 任务
定位并修复 `_shared/eda_core/hs_route_model.py` `_escape_pair` flip=True 分支的
P/N 出口极性/展开 bug。**本卡是引擎形态 bugfix，不是新增形态、不是绕过、不是改输入。**

## 钉死证据（v54 gate 后只读复核，勿重推）
- 18 条 INFEASIBLE 段中 **12 条 reason 含 `min 边缘距 -0.2050 < 0.175`**（恒 −0.2050
  = −线宽 0.205 → P/N 两线段中心距 0，完全重叠/同线展开）；另 5 条 flip=True
  "对级对称逃逸无净空 (M→cv pn_dist=0.600)"、1 条 DN7 input 133.825 落点堆叠（alloc 已知账）。
- 交叉点坐标 = 各段 pad 列/出口行附近（例 DN0 @(84.660,52.919)、UP0 @(85.005,49.820)…），
  全部发生在 flip=True 分支；已解 16 段中无任何一段 flip=True 成功 → 分支疑似从未产出正确解。
- 结论：K2 "连连看" 主钥匙 = 修复该确定性展开 bug（预计 16 SOLVED → 30+），非物理墙。
- 源位置：`hs_route_model._escape_pair`（L1255 起）`_escape_expand`/`p_line/n_line`/
  `flip` 轨道行分配（L1375-1385 区）+ via 换层 Form A 出口排序；`_pad_row_dip`/`_col_stack`
  调用点 flip 语义联动。

## 施工（单测先行，禁暴力迭代 ≤2 次带依据）
1. freeze_ctl.sh unlock。
2. 读 `_escape_pair` flip=True 全窗口 + `_escape_expand` + `_sym_via`，复现：构造
   P/N pad 对角/正排 + flip=True 的最小合成用例，断言两出口行分列（P/N 中心距 ≥0.525
   或轨道行差 0.38 且同层段 min_edge ≥0.155）——先写红测。
3. 修出口排序/极性（p_line/n_line 或展开基线选错），锁绿。
4. 跑全量回归（含 v53/v54 新单测）→ 保失败集 pre≡after。
5. K2 e2e 前台跑 ≤2 → 期望 INFEASIBLE 段批量转 SOLVED；产出 m13_v55_audit.json。
6. 若某 lane 修后仍 INFEASIBLE 且 reason 变为真·净空 → 才是形态/输入账，记 NO_ESCAPE。

## 合规
- 本卡可改 hs_route_model（引擎形态 bugfix 属问题回模型）；禁改 column_book/escape_table/
  construction_fact/escape_allocator/alloc/landing/SPEC/板文件。unlock→改→单测→e2e≤2
  →lock 0/0/0→commit（双仓）→push→handoff。
- 全前台零委派；禁 task()/禁 oracle/禁后台；勿读 v43-v54 handoff 全文（本 prompt 已含裁决）。
- 改完必须给出"为何旧代码把 P/N 放同线"的根因一句话，禁止"试试改对"式修复。

## 勿做 / 勿加载
- 勿碰 flip=False/DIRECT/直连逻辑（已解 16 段字节零变更底线）。
- 勿改 EscapeAllocator 方案层输出语义；勿把 NO_ESCAPE 变 ASSIGNED。
- 勿整读 hs_route_model（grep 定点 + 函数窗口）；勿全量 pytest（26+15+v55 新组指定文件）。
