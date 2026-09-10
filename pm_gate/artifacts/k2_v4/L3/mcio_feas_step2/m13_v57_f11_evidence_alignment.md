# m13 v57 — F11-EVID 证据协议补齐与全链 64hex 对齐记录

> 门控位：v2 §2 G3 前置项 **F-11**（R1-REVIEW 矩阵 §6；关联字段 W1-8/W2-9/V-2/M-8）。
> 性质：**G3 冻结件修订**（证据协议补齐）。只改证据字段，不改算法语义。
> 依赖：**SPEC-REV-1**（commit `019de2a`）已落地 → 串行依赖解除。
> 日期：2026-09-10（Asia/Taipei）｜k2 基线 HEAD：`019de2a`。
> 授权口径（用户裁决）：① manifest 证据字段可改 + 重跑 W0-R 全链；② 全链 5 处 12hex
> + 对应生产者（保可重放）。

## 1. 目标与口径

- 消除全链 12hex 截断，统一为 SHA-256 全 64hex；补齐证据协议 v1 §3 条 1/2（schema/版本、
  producer、源指纹）。
- **不改算法语义**：所有产出的构造算法逐字节不变；仅证据字段新增/扩位。
- **不改冻结输入**：SPEC / board / drc_rules 未触碰；manifest **仅** `inputs_sha` 扩位，
  `pages` / `anchors` / `tally` / `authority` 逐字节不变。
- **不改 W0-R**：W0-R 生成器/验证器代码 SHA **逐字节不变**；三产物为生成器/验证器
  **重跑再生成**（非人工编辑），模型语义字节不变（§5）。

## 2. 交付物指纹（before → after，全 64hex）

| 工件 | SHA-256（before） | SHA-256（after） |
|---|---|---|
| `m13_v57_s1_page_manifest.json` | `87c4c97378ff6f151fad214e6c63c64094f921fa5ab6f6cc0e269c3ac6c03360` | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` |
| `m13_v57_s1_r1_via_verdict.json` | `f20cfe24fcb7986b8da9a065139fb49015d8b789415c6312d97cc644780ad85a` | `2a3c8cf465c0ac1f808c1fdf7409725ab04862e4a8002f7ff71cfa299770bb5b` |
| `m13_v57_s1_chip_landing_rows.json` | `08e2b8348e7152578eb3466c74f42a4239ca95eb02bf842cbbd1688bc7486660` | `0d100f9c8246fd2b3daaa8dfe6358d437c1ec8dd21d4e3351e2e8e843569fca1` |
| `m13_v57_big_w0_k2frame.json` | `63c448929feb49abd0f4719b74e5bcca5a6b3b6b391011d4a5aa45fbf551dd6f` | `ff64c3ab345e325910aee61bbd98d89dff63863b78aeadd82ffd49a44f8e9feb` |
| `m13_v57_big_w2_connector_cols.json` | `b3bbbfe26d9f6c555b54cdb6f7e7908b16c1cf7806f025ee2a6435dab2e59ab0` | `e12d7c7e63a2198403ed2678b603adbe82ca3f96e8554fe32789f2199b3682a9` |
| `m13_v57_big_w1_report.json` | `554094cae313dfa62a893e8408a13605ca64c46117eed0e9fef1ecc9f6baa3ad` | `57d0c9228bf48efd63e07eec8a04bb526523650567c62a0db8c432c916ef459a` |
| `m13_v57_big_w0r_inputs.json` | `cb7ad397aed1c0eac1a68273c6153c2b3090f6f06700d2f75b52b5260c696e27` | `9fe738c3172ca78ed042a3e92a6ed8ed7cfb4a6863c06292244c7beec3552166` |
| `m13_v57_big_w0r_corridor_model.json` | `244024aa2a3cbfcc426e08f1e0ad7ad61692a1e7657ae5ba5d48e7fdb0e1ec47` | `80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa` |
| `m13_v57_big_w0r_validation.json` | `94e1962bf222174ca488bea2f0fa4b604590fa79b6c98441fdedf9d3d957a815` | `05148d08b24829232bf3486f01d10bfc3f6c1c75526dea42c2e208e5de3f0cd0` |

冻结源（未触碰，跑前 == 跑后）：

| 冻结源 | SHA-256 |
|---|---|
| `SPEC_k2_v4.json`（SPEC-REV-1 后） | `0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233` |
| `k2_v4.kicad_pcb` | `f6273de613f43d05555d12d6c3492b1e70f383761d8db5121f12b2ca0695af9a` |
| `_shared/eda_core/drc_rules.json` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` |

## 3. 生产者修订（6 CHANGED / 2 UNCHANGED）

| 生产者 | before | after | 修订 |
|---|---|---|---|
| `tools/p3_v57_s1_page_manifest.py` | `8ce2caec1df428a6…` | `06e76ce4d4a23638…` | `inputs_sha` 去 `[:12]` |
| `tools/p3_v57_s1_r1_via_verdict.py` | `523fc54de1fb45e6…` | `8766cc0cd904d099…` | `inputs_sha.ballmap` 去 `[:12]` |
| `tools/p3_v57_s1_chip_landing.py` | `66eb073e8b8fa0a9…` | `c2646745d6c29669…` | `inputs_sha.{manifest,verdict}` 去 `[:12]` |
| `tools/p3_v57_big_w0_k2frame.py` | `4cf52f47530b919f…` | `e3a2e8aa6e019059…` | `inputs_sha.manifest` 去 `[:12]` |
| `tools/p3_v57_big_w2_connector_cols.py` | `1a7c2d9adaa5e7d2…` | `ae8547bf592a472b…` | +`spec` 64hex / +`schema`+`producer`；`capacitor_walls` 读址改 `appendix.capacitor_walls_original` |
| `tools/p3_v57_big_w1_assign.py` | `9e12fd794b57f663…` | `6583a5520ba38427…` | +`schema`/`revision`/`seed`/`versions` |
| `tools/p3_v57_big_w0r_corridor_model.py` | `1283d2b68a5d3459…` | `1283d2b68a5d3459…` | **UNCHANGED** |
| `tools/p3_v57_big_w0r_validator.py` | `4b8b90dd618f1ee8…` | `4b8b90dd618f1ee8…` | **UNCHANGED** |

新增/补齐字段：

- **W2**：`schema=1`、`revision=W2-F11.1`、`producer.generator{path,revision,sha256}`、
  `inputs_sha.spec`（全 64hex）；`inputs_sha.manifest` 扩为 64hex。
  `connectors` 与 `ac_wall_declared` **逐字节不变**（值与前版一致，仅读址从
  `capacitor_walls` 迁到其存证原文 `appendix.capacitor_walls_original`）。
- **W1 报告**：`schema=1`、`revision=W1-F11.1`、`seed=20260909`、
  `versions.producer{symbol:kernel_feasible,…}`、`versions.validator{symbol:oracle_feasible,…}`。

## 4. 全链指纹验证（逐环实测 MATCH，全 64hex）

```text
manifest(a8ef3ea8…) ──┬─ landing.inputs_sha.manifest
                      ├─ w2.inputs_sha.manifest
                      ├─ w0_k2frame.inputs_sha.manifest
                      └─ w0r_inputs.inputs_sha256.manifest
verdict(2a3c8cf4…)  ─── landing.inputs_sha.verdict
SPEC(0bd52ed4…)     ──┬─ w2.inputs_sha.spec
                      └─ w0r_inputs.inputs_sha256.spec
board(f6273de6…) / rules(0a459839…) ── w0r_inputs.inputs_sha256.{board,rules}
w0r_inputs(9fe738c3…) ── w0r_model.input_artifact_sha256
w0r_model(80ee9adb…)  ── w0r_validation.model_sha256
w0r 生成器/验证器 SHA ── w0r_validation.{generator_sha256,validator.sha256}
W2 工具 SHA(ae8547bf…) ── w2.producer.generator.sha256
W1 工具 SHA(6583a552…) ── w1.versions.{producer,validator}.sha256
```

**全环 MATCH。** 终态：`w0r_model.verdict = B1.5 PASS`；`w0r_validation.verdict = PASS`
（`failures=[]`）；`w1.verdict = PASS`。

## 5. 最小 delta 证明（SPEC-REV-1 §4 同款纪律）

对修订前逐字段 diff（只列变化字段）：

| 工件 | 变化字段数 | 内容 |
|---|---|---|
| manifest | 2 | `inputs_sha.{s0_endpoint_model,sch}` 12hex→64hex |
| verdict | 1 | `inputs_sha.ballmap` 12hex→64hex |
| landing | 2 | `inputs_sha.{manifest,verdict}` 12hex→64hex |
| w0_k2frame | 5 | `inputs_sha.manifest` 64hex + refclk `old_layer/valid_6L`（§8） |
| w2 | 7 | `inputs_sha.{manifest,spec}` + `schema`/`revision`/`producer.*` |
| w1 报告 | 11 | `schema`/`revision`/`seed`/`versions.*` |
| w0r_inputs | 1 | `inputs_sha256.manifest`（新 manifest SHA） |
| w0r_model | 1 | `input_artifact_sha256`（新信封 SHA） |
| w0r_validation | 1 | `model_sha256`（新模型 SHA） |

**W0-R 模型语义字节不变**：`w0r_model` 仅 `input_artifact_sha256` 一行变化，其余
`corridors` / `certificates` / `refclk_passage_witness` / `verdict` 等全部逐字节相同。

## 6. 双跑字节一致性

生成器/验证器全链连跑 2 次：9 个工件两次 SHA-256 **完全一致**（上表 after 值）。
规范化契约不变：canonical JSON（sorted keys、indent=1；W0-R 另加结尾换行）。

## 7. 无 12hex 残留

对 9 个链工件做递归扫描（正则 `^[0-9a-f]{12}$`）：**NONE**。

## 8. 发现项：`w0_k2frame` 旧 SPEC 滞后（本次重跑刷新）

`m13_v57_big_w0_k2frame.json` 的 `diff_vs_old_spec.*/refclk.old_layer` 原记 `In6.Cu`
（`old_layer_valid_6L=false`），即 **SPEC-REV-1（refclk→F.Cu）后该工件未随 W0-R 重跑**。
本次按 F-11「全链重哈希/可重放」重跑，刷新为 `F.Cu` / `true`（共 4 字段）。此为上游 SPEC
变更沿派生链的**传播**，非算法语义变更；`frames` / `certificates` / `verdict` 不变。

## 9. 禁令合规（`git -C k2 status --short`）

改动仅限本卡交付物：6 个生产者 + 9 个链工件（见 §2/§3）。未触碰 `SPEC_k2_v4.json`、
`k2_v4.kicad_pcb`、`_shared/eda_core/drc_rules.json`、W0-R 生成器/验证器、PCB 铜、
`_shared` 指针（`? _shared` 为既有冻结/快照偏差，保持不动）。

## 10. 回滚

- 生产者：`git checkout 019de2a -- tools/<6 生产者>`。
- 工件：恢复至 §2 before SHA（`git checkout 019de2a -- <9 工件>`）。
- 回滚后 manifest 复为 `87c4c973…`，W0-R 三产物需同步回退（同一提交）。

## 11. 终态 verdict

- **F-11 = DONE**：全链指纹 64hex 对齐、可重放、无 12hex 残留。
- `w2.inputs_sha.spec == 0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233`
  （与磁盘 SPEC 一致）✓
- W0-R 终态未被推翻：`B1.5 PASS`（模型语义字节不变）。

End of F11-EVID alignment record.

---

## 12. 架构师签收（审核注记，2026-09-10）

独立复验（非采信转述）：

- **结构 diff 全 9 工件**：全部变化仅为证据/指纹字段。`w2.connectors` 与
  `ac_wall_declared`、`w0r_model.corridors/certificates/refclk_passage_witness/verdict`
  逐字段不变；唯一非哈希变更为 `w0_k2frame.diff_vs_old_spec.*/refclk.old_layer`
  In6.Cu→F.Cu（§8，SPEC-REV-1 下游传播，接受）。
- **无 12hex 残留**：递归扫描 NONE。
- **链一致**：`w2.inputs_sha.spec == 0bd52ed4…`；manifest `a8ef3ea8…` 传播至
  landing/w2/k2frame/w0r_inputs；W0-R 生成器/验证器 SHA 未变。

裁决：

1. **接受 manifest 证据字段修正 + W0-R 重跑**为一次**合法 re-baseline**：manifest 的
   `pages/anchors/tally/authority` 语义未变，W0-R 模型语义字节不变；故 B1.5 PASS 成立。
2. **当前权威 B1.5 PASS 基准** = `w0r_model 80ee9adb…` / `w0r_validation 05148d08…`（F11 后）。
   早前 W0R-FIX（`fee23ebe…`）与 SPEC-REV-1（`244024aa…`）的 doublerun 记录为**历史快照，
   已被本卡取代**；审计时以本记录 §2 after 与 §4 链条为准。
3. 历史文档中残留的旧 manifest SHA `87c4c973…`（spec_rev1_doublerun / r1 matrix /
   w0r_fix_doublerun）**属历史记录**，可保留；G3 冻结一律引用 `a8ef3ea8…`。

**F-11 = 验收通过。**
