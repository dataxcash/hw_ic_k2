# M14 v48 承接 — ①K2 启用 e2e 实证：alloc E2/E3 全通过无回归；剩余阻塞 = col 构造谓词（②），非 alloc 行位

> 承接 v47。唯一必读 = 本文件 + v47 handoff + 设计文档 §2.8。v45-v47 事实勿重推。
> 本 session 干了两件事：E3 芯片侧范围修复（同链连接器 pad 掩盖缺陷）+ K2 激活首跑。

---

## 0. 一句话状态

ENG `_shared` HEAD `97ce81c`（+chip_refs 芯片侧范围 + pads 带 ref）；K2 config 已激活
（`channel_alloc.half_pitch:0.19` + `escape_check`：chip_refs=["U6"]/band_spans refclk
[60,133]/keepout 0.37/pair_half 0.19）；freeze 0/0/0 lock。**K2 e2e 首跑（当前 In2 载体
SPEC）**：alloc 34/34（E2/E3 全过，无回归）→ solve solved_pairs=2（基线不变）。
**核心证据**：DN0-3/5 当前失败形态 ≠ v44 F.Cu 尾段撞电容墙（In2 载体已绕开墙），而是
col 构造层 P/N 相向交叉（x95-97 列区，如 DN5@(97.748,64.299)）——属 C-1/C-3 构造谓词
（②施工图层），与 kb 模板 limitation 字段（DN5=col-stack 构造上限）一致。

---

## 1. 钉死事实（v48 增量；勿重推）

| # | 事实 | 依据 |
|---|---|---|
| N1 | 真板芯片 = **U6**（x84-92 的 PCIE pad 50 个全属 U6 footprint）；C79-C83 电容墙 2 pad/个 于 x90-92/y58-65 | v48 BoardParser 实证 |
| N2 | E3 无 chip_refs 时：同链 J2 pad 合法 → 掩盖芯片 pad 被封 → DN5 假过（11 测含缺陷复现用例） | v48 单测 |
| N3 | K2 激活首跑：alloc solved 34/infeasible 0；E2/E3 证据 per net 全过（含 DN5）→ **alloc 行位层无回归** | p3_k2_real_board_e2e run |
| N4 | solve 基线 = solved_pairs 2；16 bases INFEASIBLE 主因 = col 构造 P/N 相向交叉
（chip 列区 x95-97/出端），DN0-3 input @(95.1-97.7, 58.3-64.3)、DN5 @(97.748,64.299)、
UP0-7 out_J2 @(85-92,55.7) 等 | e2e solve_base_reasons |
| N5 | N4 表明：当前 In2 载体下 DN 系列 chip 侧死因已从"F.Cu 尾段穿墙"（v44 口径，F.Cu
载体时代）转为 col 构造 P/N 交叉 → **v44 矩阵口径不可直接沿用**，归因以 N4 新证据为准 | v48 run（P4） |

---

## 2. v49 主线：把 N4 的 col 构造交叉形态补进 ②施工图层谓词（C-1/C-3 构造轮）

1. **归因定点**（真 shared，≤2 次）：取 e2e report 已落盘的 fail_forms/交叉坐标
   （x95-97 列区 @ 各轨行），确认交叉发生在 col 竖腿 In1 段、In2 尾段、还是 via 出口
   排序（flip）——需段级 trace（solve 已带 cross_evidence.point）。
2. **②施工图构造层首片规格**：col-stack 构造谓词（P/N 竖腿列差/出口排序 vs 轨行 + flip
   极性），以形态注册表行位可行性谓词接口（v47 §2.1）落地；C-1 载体两轮（F.Cu→In2）
   在当前 In2 载体下退化为"尾段恒 In2"（KB 模板 applicability 需按新 SPEC 修订）。
3. alloc E3 谓词对 N4 形态不可判（构造层上界已证 pass）——**勿再往 alloc 加构造逻辑**
   （§2.8 纪律）；E2/E3 维持现激活态（成本≈0，证据留档）。
4. 施工构造修通 → e2e 净增验证（≤2 次）→ lock → commit+push（ENG `97ce81c`+3 前 commit
   + kb 784034b + 本批 handoff）。

---

## 3. 资产 / 停止态

| 项 | 状态 |
|---|---|
| ENG `_shared` | HEAD `97ce81c`（3f33cbc→ce4a5a6→0b056e8→97ce81c）；freeze 0/0/0 lock；**未 push**（含 kb 784034b，建议 v49 绿后一并 push） |
| k2 config | 已激活 escape_check/half_pitch（route_model_config.json，非冻结区）；板 sha f6273de6 未动 |
| e2e 报告 | `k2/pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e/p3_real_board_e2e_report.json`（alloc track_validation E2/E3 证据 + solve_base_reasons 全量） |
| 单测 | test_escape_envelope.py 11 用例全绿；相关模块零新增回归 |

**勿做**：勿按 v44 旧口径（F.Cu 尾段/电容墙）推断当前失败——当前载体 In2，N4 交叉为新
形态（N5）；勿往 alloc 加构造逻辑（构造谓词归②，N3 已证 alloc 行位层无责）；勿在 v49
e2e 前 commit 行为生效改动。
