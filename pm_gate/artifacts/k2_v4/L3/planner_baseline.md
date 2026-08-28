# Planner 能力基线 (B4) — ls_in6_planner 对当前 SPEC 的重排能力

> 落盘: 2026-08-24 · 依据 `.omo/plans/k2-low-speed-infra-align.md` B4
> 被测对象: `eda_core/ls_in6_planner.py`（In6 走廊全局规划器，方案层）
> 输入: 当前 SPEC 副本 `/tmp/opencode/SPEC_b4_copy.json`（注入 pad 资产 524 条，
>       22 网全覆盖；**chip_escape 冻结缺失** = 当前 SPEC 真实状态）

---

## 1. 结论

**规划器不可用（14/22，63.6%）**。失败 8 网 = 6 网窗口阶段 0 y 可布（全 U3 侧）
+ 2 网分配阶段失败（STRAP_EQ1_U7 / STRAP_EQ1_U3）。
历史口径"22/22 收敛"经板/当前环境复核**证伪**；14/22 与计划文档基线一致。

| 判定 | 依据 |
|---|---|
| 不可用 | 8 网无法重排，且失败根因指向输入层缺陷（chip_escape 未冻结），非障碍场微调可解 |
| 修复路径 | 芯片侧接入必须消费 E3 冻结值（chip_escape）——即 E5/E6/B5 的"芯片侧冻结→既有走廊"路径，**不依赖全量重排** |

---

## 2. 运行记录（确定性输出）

```
[接入] 22 网 pad via 全部生成（2-6 个/网）
[窗口] 16 网有窗口（272~533 个 y 可布 / 11-19 区间）
[窗口] PD0_U3 STRAP_EQ0_1_U3 STRAP_EQ0_U3 STRAP_EQ1_1_U3
        STRAP_MODE_U3 STRAP_READ_EN_U3: 0 个 y 可布 / 0 区间
!! 规划失败 8 网: ['PD0_U3','STRAP_EQ0_1_U3','STRAP_EQ0_U3',
   'STRAP_EQ1_1_U3','STRAP_MODE_U3','STRAP_READ_EN_U3',
   'STRAP_EQ1_U7','STRAP_EQ1_U3']
```

---

## 3. 失败清单 + 根因分类

### 3.1 窗口阶段失败（6 网，全 U3 侧 — 下行卡 y≈62.7）

| 网 | 窗口 | 阶段 |
|---|---|---|
| PD0_U3 | 0 | 窗口 |
| STRAP_EQ0_1_U3 | 0 | 窗口 |
| STRAP_EQ0_U3 | 0 | 窗口 |
| STRAP_EQ1_1_U3 | 0 | 窗口 |
| STRAP_MODE_U3 | 0 | 窗口 |
| STRAP_READ_EN_U3 | 0 | 窗口 |

**根因（已定位，非猜测）**：
- planner 阶段 3 对每网设 `fcu_templates`（pad 中心→最近 pad via 的 F.Cu 接入段）。
- `_find_plan` 内 `fcu_stub_ok` 检查接入段 vs 冻结 F.Cu 段（`_fcu_idx`，
  wp1/j2/PCIe 逃逸域）净距 ≥0.25。U3 侧接入段（如 PD0_U3:
  pad 25 (95.225,59.7)→via (95.82,59.7)）与 U3 PCIe 逃逸 F.Cu 冻结段冲突 → 全部
  via 微调候选（±0.4 阶梯至 ±12mm）穷尽仍无净空 → `_find_plan` None → 窗口 0。
- **放大因素**：当前 SPEC 无 `chip_escape` 冻结（E5 未写回），planner 只能运行时
  `gen_pad_vias` 选位，选出的 via 与冻结段冲突时无"冻结值微调"抓手 → 死路。
- 单网复现对照：去掉 `fcu_templates` 后 PD0_U3 窗口 275（虚高），证明确认
  fcu_stub_ok 是唯一阻断点。

### 3.2 分配阶段失败（2 网）

| 网 | 窗口 | 阶段 | 分类 |
|---|---|---|---|
| STRAP_EQ1_U7 | 275 | 分配 | 走廊 y 饱和：U7 上方 y∈[35.85,39.25] 多网独占竞争，落定序后无可用 y |
| STRAP_EQ1_U3 | 299 | 分配 | 同左（U3 侧通道竞争 + R 列竖段过订阅） |

---

## 4. 输入层缺陷（planner 正确运行的前置条件，当前 SPEC 不满足）

1. **SPEC `components.pads` 为空**（entries: 0）：planner 空转（pad<2 全 SKIP），
   必须先 `pad_extract` 冻结 pad 资产进 SPEC。
2. **SPEC 22 网全部无 `chip_escape`**：planner 对含芯片 pad 的网本应 fail-closed
   （`[FAIL-逃逸域]`），但因 `chip_refs_active` 从 SPEC chip_escape 提取（空）→
   `has_chip` 恒 False → 静默退化到运行时 `gen_pad_vias`（违宪行为未被拦截）。
   该检测缺陷本身需修：`has_chip` 应从 pad 资产 ref 判定（U3/U7 为芯片），
   而非从 chip_escape 反推。

---

## 5. B5 决策依据

- **放弃 planner 全量重排**（14/22 不可用）。
- B5 走"板→方案同步器"：提取板上 22 网实测 B.Cu 段/via（真源）→ 芯片侧用
  E3 冻结值（escape_spec.low_speed_escape 18 条，含 U3 旋转修正）替换 →
  删死桩 → B3 断言全绿 → 审计落板。planner 能力缺口（U3 侧接入）由
  冻结值 + 板实测共同闭合，不依赖运行时选位。
