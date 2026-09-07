# M14 v44 承接 — chip 侧 input 8 段定点完成：真凶=去耦电容墙(C79-C83) 非球列 + 形态修复候选两轮 tail 已验证 + 停止

> 承接 v43。唯一必读 = 本文件。v43 handoff §1-§2 仍有效（钉死事实未回退）。
> 产出物 = 整体 EDA TOPO ENG；K2 仅验证；能力都是 ENG 的。
> **本 session 状态 = 按停止判据停**（chip 侧定点第 2 次仍非全 SOLVED，带 col_stack 候选矩阵停）。
> 停止时无落地改动：ENG `_shared` 已还原 HEAD + freeze 0/0/0（脏文件仍仅 pre-existing 两只，勿 commit）。

---

## 0. 一句话状态

chip 侧 8 段（DN0-3,5 input + UP2/4,7 input）逐段定点完成：**真凶不是 v43 N8 所述
U6 P3V3/GND 球列，而是 U6 东侧去耦电容墙 C79-C83（F.Cu，x90.45-91.55 / y58.75-64.25）**。
col_stack 全候选矩阵实证：DN0-3,5 的 col_stack 死于 **F.Cu 尾段横穿电容墙**（fcu_tail_seg，
dist -0.07~+0.24，轨行带内行全拒）；UP2/4,7 input 实际是 **J3/J4 连接器侧横排 VIA 对级交叉**
（无 landing，非 col_stack 族——v43 分类错标）。形态修复候选「col_stack 尾段载体两轮
(F.Cu→走廊层)」在段级探针验证 DN0-3 SOLVED + DN4 无回归；但全量 e2e 贪婪顺序下把
REFCLK1 挤出（孤立可解，顺序假象），且 REFCLK-first 反全灭 → 需跨层 via 协调，超出本形态。

---

## 1. 钉死事实（v43 增量；勿重推）

| # | 事实 | 依据 |
|---|---|---|
| O1 | **chip 侧 DN0-3,5 input 真凶 = 去耦电容墙**：U6 东侧 C79/C80/C81/C82/C83（P3V3/GND 网，F.Cu 0402/0603，x90.45-91.55，y 各 span 58.75-64.25）。v43 N8 的"U6 球列 x90.2-90.9 y59-64"是错标（同一 x 带错认对象）。F.Cu 表层 15-19mm 水平尾段（pad 列 x84.85-91.15 → 走廊入口 sx=105.25，轨行 ty±0.19）横穿电容墙必拒 | v44 探针候选矩阵（5040/段×双 flip 全 fcu_tail_seg 拒，nearest=pad:P3V3/GND dist -0.07~0.24） |
| O2 | **已解 lane DN4/6/7 = 轨行恰落电容间隙**：DN4 ty63.1（行 62.91/63.29 在 C83 顶 62.35 与 C82 底 63.75 之间）；DN6/7 ty65.5/66.7 全在 C82(≤64.25) 上方。非形态优，纯行位运气 | v44 电容 y-span 查询 + 轨行对比 |
| O3 | DN5 特有死角：col-top F.Cu via（In1→走廊层切换点）与 C82 P3V3/GND 净空 0.24 < 0.475（via 中心到 pad 边要求）。P 列 x90.85 被邻 GND 球（x90.25/91.45/91.75/92.95 y57.x）封死仅剩 jx=0 竖腿，无法东移出墙 | v44 探针：DN5 flip×2 全 3360 fcu_coltop_pt 拒 + U6 pad 邻域查询 |
| O4 | UP2/4,7 input 非 chip 侧 col_stack 族：实际死端 = J3/J4 连接器侧横排对（dy=0/dx≥0.5）VIA 对级交叉，无 landing 记录（J3/J4 网不带 `_MCIO` 后缀 → MCIO region landing 不收）。v43 §2 的 8 段 chip 侧分类含 3 段错标 | v44 pair_endpoints + landing 表 + fail_forms（cross @ x57.1/55.2 连接器区） |
| O5 | col-stack 尾段载体错用 F.Cu 是**结构缺陷**：In1/In2 内层在 x86-105 全 8 轨行净空（探针逐行 ok=True）；但尾段改走 **In1（col 同层）不可行**——后续 lane col 竖腿会与先解 lane 的 In1 尾段同层相交；尾段须走**走廊层 In2**（col In1 竖腿 + via 切 In2 尾段，跨层不相交） | v44 层净空探针 + 设计 A 段级验证 |
| O6 | 全量 e2e（形态候选落码后）：seg 12→17 SOLVED（+DN0-3 input、+UP2 out_J2、+UP7 全链），**solved_pairs 仍 2**：贪婪顺序共享累积把 REFCLK1（In6 ty50.5 横贯 U6 UP 列区 x87-93）挤出——REFCLK1 **孤立解 SOLVED**（顺序假象非几何不可行）；REFCLK-first 顺序反致 16 数据 lane 全灭 → REFCLK 与数据 lane 在 U6 列区/J2 落点需**跨层 via/顺序协调**，超出 col-stack 形态范畴 | v44 e2e×2 轮 + 孤立/换序探针 |

---

## 2. col_stack 候选失败矩阵（停止判据交付物）

段级探针（输入与 e2e 同构 alloc/landing/场）：每段双 flip 全候选遍历，拒因分类 + 代表证据。

| base(input) | 轨行 ty | 死因 | 证据（nearest：kind:net:dist） |
|---|---|---|---|
| DN0 | 58.3 | fcu_tail_seg ×5040 | P=pad:P3V3:0.19 / N=pad:PCIE_DN1_N:0.24（C80 下缘 + 邻 lane pad） |
| DN1 | 59.5 | fcu_tail_seg ×5040 | P=pad:P3V3:-0.01 / N=pad:P3V3:-0.01（C80/C81 间缝 0.06 不足） |
| DN2 | 60.7 | fcu_tail_seg ×5040 | P=pad:P3V3:-0.07 / N=pad:P3V3:-0.07（C79/C81 带内行） |
| DN3 | 61.9 | fcu_tail_seg 3600 + fcu_pt_track 1200 | pad:P3V3:-0.07（C83 带内行 + col-top 点） |
| DN5 | 64.3 | fcu_coltop_pt ×3360（双 flip） | C82 y63.75-64.25 带内 col-top via；P 列被邻 GND 球封仅 jx=0 |
| DN4(SOLVED) | 63.1 | — | 对照：C83/C82 间隙行，F.Cu 尾段净空 |
| DN6/7(SOLVED) | 65.5/66.7 | — | 对照：C82 上方，净空 |

genP/genN 存活腿数（_gen 已滤 stub/via₁）：DN0 4/14-21、DN1 4/21、DN2 21/4、DN3 20/4、
DN5 4/14。sx 全扫 0..60 步 ×0.3mm 至 bound 132.65。

---

## 3. 形态修复候选（已验证，未落码——v45 主线）

**候选 C-1（col-stack 尾段载体两轮）**：`_col_stack_escape` 尾段层两轮 = F.Cu（旧形态，
已解 lane 字节不变）→ band_field.layer（走廊层 In2，层名取 field.layer 免线轴）。尾段校验
随之切 tail 层场；col-top F.Cu via 点检查保留（through via annulus）。段级探针实测：
DN0-3 input SOLVED（COL_STACK，len 52.9-56.9）+ DN4 无回归；DN5 仍死（O3，col-stack 上限）。
**候选 C-2（DN5 行位）**：DN5 ty 须 ≥64.54（col-top via 清 C82 需行带避让）——当前 frozen
alloc DN5=64.3 不可行，涉 alloc 行序（勿动，另卡）。
**候选 C-3（REFCLK 跨层协调）**：REFCLK1 In6 ty50.5 横贯 U6 UP 列区（x87-93,y49.76-50.28
lane via 区）→ 需与数据 lane chip 侧 via 的净空协调（错列/错行或顺序），非 col-stack 范畴。

已解 12 seg 在 C-1 下全部保 SOLVED（段级抽检 UP0/1/3/5/6 input、UP4/7 out_J2、DN6/7 input、
REFCLK0/1 input 均独立可解；DN4 实证）。

---

## 4. 下一步主线（v45）

1. **落 C-1 进 ENG**（_shared hs_route_model `_col_stack_escape` tail_layer 两轮，backup 已留
   /tmp/opencode/hs_route_model.py.bak_v44，diff 见 §5 引用）。ECN-009 全流程。
2. **解 REFCLK1 顺序/跨层冲突**（C-3）再全量 e2e —— C-1 单独落码会让 REFCLK1 在贪婪序下
   被挤出（证据 O6），必须先并 C-3（如 REFCLK chip 侧列区与 UP lane via 错行）才可 e2e 收口。
3. connector 侧落点对级（16 段 out_* + UP2/4,7 input 的 J3/J4 端）仍未开始——v43 主线 2。
4. 目标不变：18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。

---

## 5. 资产 / 停止态

| 项 | 状态 |
|---|---|
| ENG `_shared` | **还原 HEAD**（git diff 空）；freeze 0/0/0 已 lock；pre-existing 脏仅 escape_closure_analysis.py/install.sh（mode-only，勿 commit） |
| k2 报告 | p3_real_board_e2e_report.json 已还原（v43 da4569c 态）；板 sha f6273de6 未动 |
| 探针（用后即弃） | /tmp/opencode/probe_colstack_dn1.py、probe_colstack_multi.py、probe_designA.py、hs_route_model.py.bak_v44（C-1 落码参考 diff） |
| 停止判据 | chip 侧第 2 次定点（设计 A 段级）DN0-3 解、DN5 硬限 + e2e REFCLK1 顺序冲突 → 停，带 §2 矩阵 |

**勿做**：勿把 C-1 单独 commit 后跑全量 e2e 当绿（REFCLK1 必被挤出，O6）；勿动
capacity/alloc/landing/SPEC 走廊层；勿恢复 /tmp 基线板；勿试 PEX8748。
