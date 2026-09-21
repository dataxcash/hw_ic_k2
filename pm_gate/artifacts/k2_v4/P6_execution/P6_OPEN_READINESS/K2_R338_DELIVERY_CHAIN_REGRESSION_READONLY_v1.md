# K2 · R338 · 交付链回归（只读 · 不重建旧包）

**件**：`K2_R338_DELIVERY_CHAIN_REGRESSION_READONLY_v1.json`（约定A `90f58073bcea1d26`）
**做法**：对 `k2/pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3` 内 MANIFEST 所列 **53** 件逐文件重算 sha256 比对；**不重建、不覆盖旧包**。

## 读数
| 项 | 值 |
|---|---|
| 文件数 | 53 |
| **ok** | **53** |
| bad | 0 |
| missing | 0 |

⇒ 交付包完整且自洽：逐文件 sha256 与 MANIFEST 全数吻合（53/53 · bad 0 · missing 0）。

**DFM**：{"pass": 16, "accept": 1, "fail": 0}（**watch**：owner #14③ 字面『全 PASS』⇒ ACCEPT 项须监理确认等效或给处置）。

## 边界
只读核对：未烙板 · 未改生成器/SPEC/原理图 · **未重建/未覆盖交付包** ⇒ 不动证明成立。冻结四源 4/4 未动 · `criteria` rev=6 MATCH。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
