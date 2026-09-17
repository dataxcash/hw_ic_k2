# K2 · P4 · SPEC 卡内「工具 pin」勘误（ENG → 监理并入下一版 SPEC）· v1 · 2026-09-17

## 1. 勘误对象

| 项 | 值 |
|---|---|
| 承载块 | `SPEC_k2_v4.*.json` 叶 `_spec_rev_30`（= 增量 12 / 电源面接入，文件版本 `spec-rev-40`） |
| 出错叶 | `_spec_rev_30/changes[2]` 与 `_spec_rev_30/executor` |
| 卡内记 | `k2/tools/k2_p4_pdn_in4_v1.py = 9d67b8fc742ce884` |
| **实际提交件** | `k2/tools/k2_p4_pdn_in4_v1.py` = **`ea5af7e41eebd9347bdda50f2b2cbd12`** |

## 2. 证据（只读复算）

```bash
cd /home/fila/jqdDev_2025/ic_hw
sha256sum k2/tools/k2_p4_pdn_in4_v1.py                      # ea5af7e41eebd9347bdda50f2b2cbd12
git -C k2 show b73df92:tools/k2_p4_pdn_in4_v1.py | sha256sum # ea5af7e41eebd9347bdda50f2b2cbd12（提交时态即为此值）
git -C k2 diff --stat HEAD -- tools/k2_p4_pdn_in4_v1.py      # 空 ⇒ 工作区 = HEAD
grep -rl 9d67b8fc742ce884 k2/                                # 仅命中 SPEC rev-40..44 的卡内文本，无实际文件
```

- 该工具的**唯一提交**为 `b73df92`（增量 12）；此后无任何提交改写它 ⇒ **提交时态即 `ea5af7e4…`**，卡内 `9d67b8fc742ce884` 是**写卡时态的暂态值**（非任何已提交件的 sha）。
- 勘误**已传播**至 `SPEC_k2_v4.spec-rev-40..44.json`（五份文件同错）；canonical = `spec-rev-44.json`（`acc64b447ef55e90`）。

## 3. 处置建议（ENG 不擅改冻结件）

冻结件纪律：`spec-rev-19..44` **原件永不改**（修订走**版本 bump 新文件**）。故：

- **ENG 建议**：在**下一版** SPEC（`spec-rev-45`，或任何后续 bump）的留痕块中并入一条勘误，例如
  `errata: "_spec_rev_30 记 k2/tools/k2_p4_pdn_in4_v1.py = 9d67b8fc742ce884 → 实为 ea5af7e41eebd9347bdda50f2b2cbd12（提交 b73df92 时态）；判据/叠层/布线语义不受影响"`
- **影响面**：纯留痕/书目性错误 —— 该 pin 不参与任何判据、不参与布线/DRC/叠层推导；**不改变任何 gate 结论**。
- 是否单开 `spec-rev-45` 仅为此勘误，或并入下一增量同批 bump，**归监理/owner 定**（ENG 不因此单独 bump 版本）。

—— ENG（ARCHER）· 2026-09-17
