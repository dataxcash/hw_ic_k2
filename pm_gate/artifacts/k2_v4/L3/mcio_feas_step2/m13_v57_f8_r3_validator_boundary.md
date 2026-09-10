# m13 v57 — F8-R3GEN 独立验证器边界声明（R3 隙候选域）

> 卡：**F8-R3GEN**（R1-REVIEW 矩阵 §6 F-8；W2-4/W2-7/W2-8）。门控位：G3 后 W3 前置卡。
> 性质：W2 后继（R3 资源域生成器），**只产 R3 候选域**，不分配、不产 W3 输出。
> 日期：2026-09-10（Asia/Taipei）｜k2 基线 HEAD：`289b5de`。
> 输入权威：`manifest a8ef3ea8…` / `SPEC 0bd52ed4…` / `drc_rules 0a459839…`（**零板读**）。

## 1. 交付物与指纹

| 交付物 | SHA-256 |
|---|---|
| 生成器 `tools/p3_v57_f8_r3_gap_candidates.py` | `12dd1f1f99cdcdace39e05951002a583d42069d1f4a3beab8b031a8081e76918` |
| 独立验证器 `tools/p3_v57_f8_r3_validator.py` | `fd217e213eb14b31d6852c905babfecbfb85aa18d3f91e1d19a52c02c15d4c61` |
| 产物 `m13_v57_f8_r3_gap_candidates.json` | `8a31632907b171483cd40a053231c702e378f944af33f92598a6141bd052cdeb` |

冻结源（生成器自声明，独立验证器复算一致）：

| 源 | SHA-256 |
|---|---|
| `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` |
| `SPEC_k2_v4.json` | `0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233` |
| `_shared/eda_core/drc_rules.json` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` |

## 2. R3 模型（生成器权威口径）

- **列/行/条目**：manifest 连接器锚（`pad_global`）纯重聚合；**REFCLK pad 纳入**
  （数据页 `anchors.conn`；REFCLK 页 `anchors.conn`+`conn2`），不再按 `kind!="data"` 过滤。
- **pad 铜**：具名常量（板 footprint 实测冻结，运行时零板读）——J2 `1.3×0.35`、
  MCIO_4i_SFF-1016 `0.3×0.7`；行距由 manifest 相邻行 y 差派生（J2 0.6 / MCIO 2.5）。
- **隙候选**：pad 列相邻的水平净空隙列（相邻列铜边间中心，或连接器外侧
  `pad_w/2+clearance+via_od/2`），要求 `隙宽 ≥ via_od+2·clearance (=0.7)`；
  落点 y ∈ `pad_y ± 半行距`。
- **出逃拓扑**：J2 内列左出/外列右绕（`SPEC.constraints.j2_escape_topology`）；MCIO 东向走廊。
- **守恒**：每 pad 恰 1 落点（每 pad ≥1 候选列）。
- **冲突图**：同列（同一隙列）相邻落点 `y 距 ≥ via_od+clearance (=0.525)`。

## 3. 独立验证器边界（可重放断言）

独立验证器 `p3_v57_f8_r3_validator.py` **不 import 生成器**，从冻结源重新派生并断言：

| 可重放断言 | 方法 | 结果 |
|---|---|---|
| 输入指纹（manifest/SPEC/rules）== 磁盘 | 重哈希 | ✓ |
| 生产者指纹 == 生成器工具 SHA | 重哈希 | ✓ |
| 每 pad 的隙候选 == 独立重派生（同常量/净空口径） | 逐 pad 集合对照 | ✓ |
| 条目数 == manifest pad 数；每 pad ≥1 候选 | 计数 + 逐 pad | ✓ |
| 守恒 verdict == FEASIBLE | 重派生 | ✓ |
| 冲突图边集 == 独立重派生（同 `required=0.525`） | 集合对照 | ✓ |
| REFCLK pad 全部在列（8/8：J2 4、J3 2、J4 2） | 集合对照 | ✓ |
| 无分配/W3 选择字段泄漏 | 键扫描 | ✓ |

验证器实测：`PASS | checks: all`（exit 0）。

**不可重放 / 边界外**（验证器不得断言）：

- 任何 page→隙列 的**选择/指派**（属 W3，R3 只给候选域）；
- R4 墙 pad 锚（D0-1 已出链，本卡不生成）；
- 依赖 W0-R 终态的字段（lane 帧/LEG 预算等，属 R2/W3）。

**禁止反推**（继承 `w0r_inputs.explicit_non_inputs`）：`SPEC.corridors.tracks_y`、
板铜 tracks/vias/zones、旧 lane 簿、max-x/x-window 反猜端点。

## 4. 禁令合规

- **不分配**：产物无 `selected/assigned/allocation` 字段（验证器键扫描 ✓）。
- **不产 W3 输出**：无 lane/track_y/drawing/chip_landing。
- **不改冻结文件**：manifest/SPEC/rules/W0-R/W1/W2 均未触碰。
- **零板读**：生成器/验证器仅读 manifest+SPEC+drc_rules；pad 尺寸为具名常量。

End of F8-R3GEN validator boundary statement.

---

## 架构师签收（2026-09-10，审核注记）

独立复验：

- **禁令合规**：产物无 `selected/assigned/allocation/chosen` 字段（零分配）；生成器零板读；
  无 R4 墙 pad 锚。
- **§4-B 反推禁令**：出逃 x 由 `pad_x + w/2 + clearance + via_od/2` 派生
  （`131.65 = 132.65 − (0.65+0.175+0.175)`；`136.0 = 135.0 + 1.0`；`133.825 = 两列中点`），
  **非**取 SPEC 求解器反演 vx 区间 `[131.7,136.0]`（代码中无 `vx/solver/131.7`）。仅取
  拓扑方向语义（inner=left/outer=right）。**通过。**
- **独立验证**：validator 只 import 标准库（不 import 生成器），实跑 `PASS | checks: all`。
- **数字核对**：72/72 pad 有候选、8/8 REFCLK pad、22 条冲突边、双跑 `8a316329…`。
- **输入指纹**：spec `0bd52ed4` / manifest `a8ef3ea8` / rules `0a459839` == 磁盘。

**F8-R3GEN = 验收通过。**
