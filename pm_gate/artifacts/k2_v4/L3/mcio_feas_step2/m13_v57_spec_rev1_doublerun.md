# m13 v57 — SPEC-REV-1 双跑与指纹链记录（W0-R 重跑）

- 日期：2026-09-10（Asia/Taipei）
- 卡片：SPEC-REV-1（落地 D0 裁决卡 `ad5c208`：D0-1 R4 出链 / D0-2 REFCLK=F.Cu）
- 修订：W0R-FIX.1（生成器/验证器**未改**，revision 不变；仅冻结源 SPEC 变更）
- 本文件角色：SPEC 修订后 W0-R 重跑的双跑字节一致性 + 最小 delta 证明 + 冻结不变性记录

## 1. 交付物指纹（重跑后最终状态）

| 文件 | SHA-256（新） | SHA-256（修订前） |
|---|---|---|
| `SPEC_k2_v4.json`（冻结源，已修订） | `0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233` | `3bdecb10ab4747a9280131c89cb5a25b64466b62966b3354c4780c5fbf9a0d7a` |
| `m13_v57_big_w0r_inputs.json`（输入信封） | `cb7ad397aed1c0eac1a68273c6153c2b3090f6f06700d2f75b52b5260c696e27` | `4ca3e134407634dd8fb4fb396d35aebcbe2893c1548119566f0ff0913771eb17` |
| `m13_v57_big_w0r_corridor_model.json`（模型） | `244024aa2a3cbfcc426e08f1e0ad7ad61692a1e7657ae5ba5d48e7fdb0e1ec47` | `fee23ebe3aa6fed838441fbbb7e57c552dd025fc4f506a36cc49bc52b60741a2` |
| `m13_v57_big_w0r_validation.json`（独立验证） | `94e1962bf222174ca488bea2f0fa4b604590fa79b6c98441fdedf9d3d957a815` | `63993e6d3ed2af317a27d6c54a2926342c3a187660e3b07c000b0696c59d2112` |
| `tools/p3_v57_big_w0r_corridor_model.py`（生成器，未改） | `1283d2b68a5d3459436c922d5f2ecb9b2ae35c7979de7482598267f43585d31b` | 同左 |
| `tools/p3_v57_big_w0r_validator.py`（验证器，未改） | `4b8b90dd618f1ee860cb5a15be55c9fa4c9ff575ef6e19a334955a2c34fcb8e8` | 同左 |

## 2. 冻结源不变性（跑前 == 跑后 == 信封声明）

| 冻结源 | SHA-256 |
|---|---|
| `SPEC_k2_v4.json`（**已修订**，新指纹） | `0bd52ed4…`（信封 `inputs_sha256.spec` 同值） |
| `k2_v4.kicad_pcb`（未触碰） | `f6273de613f43d05555d12d6c3492b1e70f383761d8db5121f12b2ca0695af9a` |
| `m13_v57_s1_page_manifest.json`（未触碰） | `87c4c97378ff6f151fad214e6c63c64094f921fa5ab6f6cc0e269c3ac6c03360` |
| `_shared/eda_core/drc_rules.json`（未触碰） | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` |

## 3. 双跑字节一致性

- 生成器连跑 2 次：`inputs.json` 与 `corridor_model.json` 两次 SHA-256 完全一致（上表值）。
- 验证器连跑 2 次：`validation.json` 两次 SHA-256 完全一致，verdict=`PASS`，failures=`[]`。
- 规范化契约不变：canonical JSON（sorted keys、indent=1、结尾换行）。

## 4. 最小 delta 证明（SPEC 修订只触及非消费字段）

对修订前（git `39f0c13`）与新产物逐字节 diff：

| 产物 | diff 结果 |
|---|---|
| `inputs.json` | 仅 1 行：`inputs_sha256.spec` `3bdecb10…` → `0bd52ed4…` |
| `corridor_model.json` | 仅 1 行：`input_artifact_sha256` `4ca3e134…` → `cb7ad397…` |
| `validation.json` | 仅 1 行：`model_sha256` `fee23ebe…` → `244024aa…` |

**指纹链完整**（逐环实测 MATCH）：
`SPEC(0bd52ed4…) → 信封.inputs_sha256.spec → 信封 SHA(cb7ad397…) → 模型.input_artifact_sha256
→ 模型 SHA(244024aa…) → 验证.model_sha256`。board/manifest/rules 三源声明值均与磁盘一致。

结论：SPEC 修订未触及 W0-R 消费字段（`board.outline_y` / `stackup .Cu` 键 /
`constraints.m3_keepout_mm`），模型语义逐字节不变，仅指纹链更新。

## 5. 终态 verdict

- **`model.verdict = B1.5 PASS`**，`certificates = []`；两走廊 `refclk_resource_domain.status
  = SATISFIED`；passage witness 两页 `WITNESSED`。
- 独立验证器：exit 0，`verdict = PASS`，`failures = []`。
- W0-R 终态未被 SPEC 修订推翻（与 D0-1 理由一致：其 span 本就未把 AC 墙算入 blocker）。

## 6. 禁令合规（git status 范围核对）

`git -C k2 status --short` 改动仅限本卡交付物：

```
 M pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json
 M pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_big_w0r_inputs.json
 M pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_big_w0r_corridor_model.json
 M pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_big_w0r_validation.json
```

（W0-R 三产物为生成器/验证器**重跑再生成**，非人工编辑。）未改 `_shared`、冻结放置、
PCB 铜、W1/W2 产物、生成器/验证器工具。

End of SPEC-REV-1 doublerun record.
