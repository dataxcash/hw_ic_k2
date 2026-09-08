# M13 v51 承接 — DN out_MCIO 两件套落地实证（+1 对 +2 段级；dip 首hit + 归属门解锁；DN7 同列堆叠回退归 alloc 协调）

> 承接 v50。任务（NEW_SESSION_PROMPT_v51.md）：最小可证两件套 = kb 模板 + ENG-α pad-row dip
> + ENG-β 消费归属门 + 合成单测 + e2e≤2。**v51 结论：两件套实证有效（部分净增）** —
> solved_pairs 2→3（DN6 全解，右逃逸 PAD_ROW_DIP 首hit）+ 段级 15→17（+DN5/DN6 out_MCIO）；
> 代价 DN7 input 段同列 via 堆叠回退（DN6 全解共享 J2 列）——按 v51 记下一卡（alloc 重锚 B1/
> 段级占用协调），本卡不暴力迭代。

---

## 1. 钉死事实（v51 增量；勿重推）

| # | 事实 | 依据（e2e 报告 p3_real_board_e2e_report.json，run 1/1） |
|---|---|---|
| F8 | solved_pairs **2→3**：DN6 全解 = input(右 LANDING 字节不变) + out_MCIO（左 LSWAP_V + **右 PAD_ROW_DIP** 首hit，drop 列 82.75/82.35、pad 行 52.37/51.67 In2 横走 8.45mm） | report stages.solve results/solved_pairs + escape.segments kind |
| F9 | 段级真解 15→**17**：+DN5 out_MCIO（右 **COL_STACK**——ENG-β 门移除错锚 landing 消费后 col_stack 自搜解锁，非 dip）+DN6 out_MCIO；DN5 base 仍 INFEASIBLE（input 段 pre-existing 卡 @97.748,64.299） | report results segments + segstat |
| F10 | **字节锚零变更**：28 已解 P/N 段端 pre≡new（diff changed=0）→ REFCLK0/1 全保、UP0-3/6/7 out_J2 保、DN0-4/6 input 保；DN0-4/6 out_MCIO 仍 INFEASIBLE（DN0/1/3 chip 侧 via 极性交叉 @84.66/85.79/84.38，dip 亦无候选；DN2/4/7 J3 左逃逸卡） | solve_base_reasons + 段 path diff（git show HEAD vs new） |
| F11 | **DN7 input 段回退**（SOLVED→INFEASIBLE）：根因 = **同列 via 堆叠**——DN6 全解后其 input 段共享进 solve_all 池，J2 落点列 x133.825 F.Cu stub 竖线（y63.3→65.31）穿过 DN7 落点 via (133.825,63.9/64.5) → point_ok 拒（v51 明示"DN7 北行+同列堆叠高风险"同源） | DN7 reason + DN6 段 path 几何叠查 |
| F12 | 零新增 REFCLK 冲突；alloc 34/34 无回归；landing FEASIBLE 52/52（MCIO 区 16 记录 used=16 未被消费——归属门拒绝后仍 ASSIGNED，alloc 不改） | report stages alloc/landing |

## 2. 根因定案增量

- **ENG-α dip 有效但窄**：DN6 命中（drop 列枚举 0.1 步 + P/N 错列防堆叠）。DN0/1/3 chip 列
  (84.4-85.8) 邻族/共享障碍使 dip 候选全净空失败（同 F5 col_stack None 域）→ 该列需更西 drop 或
  载体层变体（下一卡形态候补）。
- **ENG-β 门两级收益**：①移除 chip 侧错锚消费 → col_stack 自搜解锁 DN5/6；②DN0/1/3 门后
  自搜仍无解（F5 反证守恒）。
- **DN7 回退 = 共享占用协调缺口（v49 UP4 out_J2 同源）**：base 级 solve 只在全 SOLVED 时才
  共享前馈 → DN6 从 INFEASIBLE 变 SOLVED 即把整链几何压进 DN7 场。J2 GAP 列 133.825 被 alloc
  复用于 DN6/DN7 双记录（同列堆叠）→ 修复归 alloc 重锚/占用协调，非本卡 ENG 域。

## 3. 施工账（v51 交付物）

- kb：`landing_pair_geometric_padrow_dip_vjog`（category connector_escape，v2 validation 已更新，
  记录 α/β 两形态 + 构造前提 + 缺口）——artifacts json（m14_v51_kb_*.json）+ kb.sqlite3 PUT。
- ENG（_shared eda_core/hs_route_model.py）：`_pad_row_dip_escape`（加性 dormant，门 direction<0 &
  pad 东于 corr_x & band层==esc层；stub 0.3/0.6/0.9 → via@pad 行 → In2 西行 → drop 0.1 步枚举 +
  pn_ok≥0.155 防同列堆叠）+ `_escape_pair` col_stack None 后挂钩 + `_landing_pair_usable`/
  `_fcu_stub_ok`（归属 ε0.02 + H/V-jog stub 可达门）+ `_solve_pair_centerline_v4` landing_pair
  侧自适应（双端传参，归属门决定消费）。
- 单测：+8（TestPadRowDipEscape 3：解/东向 dormant/带层不符 dormant；TestLandingAttributionGate 5：
  过/归属失败/缺失 pad 字段/stub 不可达/V-jog 兜底可达）；全量失败集 pre≡after 16（环境/工具链，
  含 test_t5 pre-existing），**零新增**。
- e2e：1 次（run_all 全链）。净增<7 → 停机，不跑第 2 次（确定性引擎重跑结果同）。

## 4. 下一卡（v52 候选，勿本卡续）

- **B1 alloc 重锚**（region MCIO 窗口吞芯片列 → 记录 pad 锚芯片 pad / J2 GAP 列 133.825 双记录
  同列堆叠）→ 解 DN7 input 回退 + 让 MCIO 记录真正可被 J3 侧消费（V-jog stub 消费形态）。
- J3 左逃逸（DN2/4/7）+ chip 列 84.4-85.8 dip 净空候选缺失 → 载体层/更西 drop 变体。
- 均不得在本卡暴力迭代。

## 5. G5 自检

- 消费资产：v51 prompt + v50 handoff F1-F7 + report solved/落点表 + kb 模板 v2。
- 纪律：零 alloc/channel_alloc 改动；零 K2 坐标/网名特判；合成单测零真板依赖；e2e=1 次全链；
  无 task()/oracle/后台；回归比对走 git HEAD report diff（28 段字节零变更实证）。
- 未 commit 前状态：freeze lock 后 commit（_shared ENG+kb + k2 report/handoff/kb-json）→ push 两仓。
