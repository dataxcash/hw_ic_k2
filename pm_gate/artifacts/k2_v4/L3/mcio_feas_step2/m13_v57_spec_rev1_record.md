# m13 v57 — SPEC-REV-1 修订记录（SPEC_k2_v4.json）

> 门控位：v2 §2 G2 出口落地。落地 D0 裁决卡的 D0-1（R4 出链）与 D0-2（REFCLK=F.Cu）。
> 授权：D0 L2 裁决卡 `ad5c20817b5892848f25f524a0cf8366814c7535`（k2 子模块，G2 continue）。
> 日期：2026-09-10（Asia/Taipei）｜k2 基线 HEAD：`39f0c13`（D0 卡 `ad5c208` 之后一笔）。
> 角色：本卡为**唯一会改冻结文件（SPEC）**的卡；本记录为 SPEC 修订归属声明。

## 1. 修订内容（主链唯一改动，逐字段）

| 字段 | 旧值 | 新值 | 依据 |
|---|---|---|---|
| `spec_version` | `1.1.v28-eco` | `1.1.spec-rev-1` | 本卡版本 bump |
| `corridors[EAST_CHIP_TO_J2].bands[refclk].layer` | `In6.Cu` | `F.Cu` | D0-2（In6.Cu 栈中不存在） |
| `corridors[WEST_MCIO_TO_CHIP].bands[refclk].layer` | `In6.Cu` | `F.Cu` | D0-2（同上） |
| 两处 refclk band `layer_note`（新增） | — | `per D0-2` | D0-2 加注 |
| `capacitor_walls` | 32 只 AC 墙完整声明 | `{out_of_scope_for_mvp: true, basis, original_preserved_in}` | D0-1（R4 出链） |
| `appendix.capacitor_walls_original`（新增） | — | 修订前 `capacitor_walls` **原文**（键名/顺序/取值不变） | D0-1「保留原声明为附录存证」 |
| `_spec_rev_1`（新增） | — | 本卡修订条目（引 `ad5c208`） | 加修订记录条目 |

原文未删除、未重排：`capacitor_walls` 原声明完整移入 `appendix.capacitor_walls_original`
（字段名与顺序不变）；其余顶层字段（`board`/`stackup`/`constraints`/`corridors` 的
`x_range` 等）**未触碰、未重排**。

## 2. 修订性质判定

- **输入层修正，非 workaround**：
  - D0-1：`capacitor_walls` 是 L2 声明、L1 无实体的悬空层（板面 0/32 放置、0/32 在网表，
    R1 独立实测成立）。MVP 内 R4（AC 墙穿越）出链；标记 `out_of_scope_for_mvp` 后，
    下游（W3 输入白名单）按 G3 冻结契约 §6 删除 R4 相关字段。
  - D0-2：三源冲突（S1 设计=In2.Cu｜board-intent={F.Cu,In2}｜W0-R=F.Cu 候选），SPEC 旧记
    `In6.Cu` 为笔误（6L 栈 F/In1/In2/In3/In4/B，无 In6）。校正为 `F.Cu`，与数据层
    `In2.Cu` 分离。
- **不改变 W0-R 可行包络**：W0-R 只消费 `board.outline_y` / `stackup` 的 `.Cu` 键 /
  `constraints.m3_keepout_mm`（`SPEC.corridors` 为显式非输入）；本次三处均未动，故
  模型语义零变化（见双跑记录 §4）。

## 3. 指纹后果

- SPEC SHA-256：`3bdecb10…` → `0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233`。
- 指纹沿链传播：信封 `inputs_sha256.spec` → 信封 SHA → 模型 `input_artifact_sha256`
  → 模型 SHA → 验证 `model_sha256`（详见 `m13_v57_spec_rev1_doublerun.md`）。
- G3 冻结契约 §6：F-11 按新 SPEC 指纹重补（独立 worker 卡）。

## 4. 禁令合规

本卡未改：SPEC 的 board outline / stackup / constraints / corridor x-ranges / 其他字段；
`_shared`；冻结放置；PCB 铜；W0-R/W1/W2 产物（W0-R 三产物为**重跑再生成**，非人工编辑，
且差异仅指纹字段）。`git status` 核对见双跑记录 §6。

## 5. 回滚

- 恢复 `SPEC_k2_v4.json` 至 `spec_sha256_before = 3bdecb10…`（`git 39f0c13`），并重跑
  W0-R 全链；若日后恢复 AC 墙，须先 L1 补网表 + L2 补放置（D0-1 回滚条款）。

End of SPEC-REV-1 revision record.
