# m13 v57 — 基线交接纠偏（架构师审计对齐，2026-09-09）

> 架构师审计三点偏差经机器核实**全部成立**；本文件为纠偏记录（不改代码/不夹带工件）。

## 1. 版本与领先数（纠错）
- k2 HEAD = **137332f**；相对 origin/main **领先 12 个提交**（非 16）。
  本会话自 3b19459 起共 12 commit：6dd43cd / 348c67d / 38d7220 / 987a42b /
  85d2fcc / 8da09ad / 1b429d1 / 0c62c48 / bef60cb / a611c59 / 084960d / 137332f。
- NEW_SESSION_PROMPT_v58.md 记的 8da09ad 已过期 6 个提交 → 以本文件为准。

## 2. B1.5 状态（纠错：未交付）
- BIG 现有实证 = **合成 frame 核**（B1.1 120/120、B1.2/B1.3/B1.4 PASS）。
- **B1.5（真实 K2 走廊/lane frame 派生与证书）无脚本/无报告**：此前"数据帧可行 /
  REFCLK 证书"仅为交互式 shell 演示，**非工件**，不计入证据。
- B1.5 为 W0 的交付物（下方排程）。

## 3. 工作树状态（须记录/隔离，禁混入提交）
- tracked dirty：`? _shared`（子模块）。k2 记录 gitlink = **b48d3f4**；容器
  `_shared` 实际 checkout = **6ab6308**（v57 运行真源）+ 冻结机制 chmod
  （4 文件 mode 755→644，内容零变更）。属**已知冻结/快照偏差**，非代码漂移；
  隔离方式 = 保持不动 + 本记录，禁把 _shared 指针变更混入 k2 提交。
- untracked：**142 文件**（14 松散 + model_solves/{hs_rebuild_v11 45,
  hs_rebuild_v12 81, channel_alloc_diag 2}）。均为历史/备份工件 → 记录并隔离，
  不进新提交（留专门 housekeeping）。

## 4. 已核实的可信证据（本会话）
- 34 页 manifest（双跑一致）；A1.1 140/140；A1.3/A1.4 PASS；
- B1.1 120/120；B1.2/B1.3/B1.4 PASS；
- R1 32/32 ESCAPABLE；chip_landing_rows 64 行（权威 VIA_IN2 落点）。
- **注意**：chip_landing 的 P/N 对为**逐页 canonical 选择**（137332f）＝临时；
  W3 联合指派将取代之，届时需重发射（顺序耦合禁入）。

## 5. 架构师排程（worker 接受，见回执）
W0 真 K2 frame（串行前置）→ W1 联合指派契约（并行只读）/ W2 R3/R4 候选域
（并行只读）→ W3 联合求解 + 34 页 JSON → W4 独立真图验收。
