# CO-135 — 非执行者复评（rev-19 + CO-134）+ L2 卫生修正

- verdict：**PASS_WITH_FINDINGS**
- 冻结四源：4/4 MATCH；SPEC rev-19 白名单外 0 改动：True
- 收口件 citation：mismatches 0（含表格行；计数不记录以免不动点）
- rev-19 重基线：co78/co81/co84 pin=rev-19 → True；L5 fab pin 现行 → True

| id | 类 | 判定 | 摘要 |
|---|---|---|---|
| F1 | TOOL_DEFECT | FIXED | co77 收口声明扫描的正则仅覆盖内联 `file` `sha`，**未覆盖 markdown 表格行**（`| `file` | `sha |
| F2 | PROCESS_DEFECT | FIXED | rev-19 重基线不完备：9185bc8 提交态 co78/co81/co84 记录仍 pin **SPEC rev-18**（未对 re |
| F3 | PROCESS_DEFECT | FIXED | L5 fab 记录 pin 陈旧 L4 construction（305a42a890593552），未随 L4 重基线（cb8874255 |
| F4 | CITATION_DEFECT | REPORT | handoff-z20 自身 pin 失准：(a) G5=4d5abd85e1d47705 在**全仓无对应工件**（实际 G5 工件 m1 |
| F5 | DOC_ACCURACY | REPORT | (a) ③ 根因叙述「0.875 = 2×0.4375」与来源件不符：`_shared/docs/PCB_DESIGN_RULES.md`  |
| F6 | DECLARED_SCOPE | CONFIRM_EXTERNAL | pad_field（cap 0.6）对间可达性为**声明豁免**（regime 串含 ECN-001 即豁免，无闭式 margin 判据）； |

## 实质结论

- 全链复现：G4 0074dad9067af737 / G5 75ce1c2af42de55e / L4 val 313666e68dd610e6 viol 0 / L5 DFM new=0·SI 0.1300 / co124 findings 0（T1..T8）/ co95 55/55 / co98 55/0/0 / PDN co88/91/99/102(+0)/104/105/106 / co69 10/10 / co120 PASS
- ③ 定性：整改通知 #09（监理指令）明确 ③=工程换算错误、撤回 owner 升级 ⇒ CO-134 属**执行指令**，非越权需求变更；0.875 退役结论不受 F5 叙述瑕疵影响
- as-built 处置：域外 3 处偏差（F.Cu 0.3294 / B.Cu 0.3450 / In5 0.3125）经本会话独立重算复现，登记 OPEN_ENGINEERING 妥当（路由 SI/板厂券 或另开几何 CO）
