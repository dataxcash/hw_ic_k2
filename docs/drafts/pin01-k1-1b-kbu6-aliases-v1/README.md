# PIN01-K1-1b — KBU6 真源 aliases 补 `WORK_EN`/`KEY_DET_EN`（**已制备 · 沙箱验证 · 待批落地**）

**状态：未落地（NOT LANDED）**。落地点 = `_shared/eda_core/sch_gate/datasheets/STM32G0B1KBU6.yaml`
（`aliases:` 追加 2 键）；属 `_shared` 写 ⇒ 须监理放行（与 PIN01-K1-1a/c 同一笔）。

## 为什么
#K2-51 §三 3/6 验收项「pinmap 校验器 **U1 全 PASS**」未达成：脚**号**侧已全对（9→2 项），
剩 **2 项 = 引脚名未绑定物理端口** —— 符号 `MCU_STM32G0` 的 `WORK_EN`(pad 9) / `KEY_DET_EN`(pad 26)
在真源 `aliases` 中无对应键。#K2-51 §二② **逐字保留**该信号层决定：`WORK_EN=PA2` · `KEY_DET_EN=PA15`
（`{9,26}` 空脚集合 = `{PA2, PA15}`）⇒ 仅**补名绑定**，**不改 pins**。

## 载荷（1 文件）
`STM32G0B1KBU6.yaml` = 现行真源 + 末尾追加：
```yaml
  WORK_EN:
  - PA2
  KEY_DET_EN:
  - PA15
```
- `pins` **逐字未动**（`25: PA14` · `26: PA15` 等，实测复核）。
- 遵循该文件既有 `aliases` 风格（网名 → 物理端口列表）。

## 沙箱验证（可复现 · 未触 `_shared`）
真源目录副本 + 本载荷（叠加 PIN01-K1-1c 4 表）⇒ `pinmap.py` 对 K1 符号库：

| 配置 | PIN-01 FAIL |
|---|---|
| 现状（仓库真源） | **29** |
| +PIN01-K1-1c（4 表） | **25** |
| **+1c +1b（本载荷）** | **23** |

⇒ 本载荷单独贡献 **−2**（恰为 2 项名绑定）；余 23 = USB-C J1（**PIN01-K1-1a，受 J1-SSP-1 口径冲突阻塞**）。

## 落地批（须监理放行）
与 PIN01-K1-1c（4 表）**同一笔** `_shared` 升版 + 四树同步 ⇒ 随后 PIN-01 **29 → 23**；
待 1a 口径裁定后可达 **0**。
