# m13 v57 — D0 Decision Card（L2 裁决，G2 出口）

> 门控位：v2 §2 G2 行。本卡记录 L2 裁决，**不夹带任何冻结文件修改**（SPEC 修订另开专项卡）。
> 签署：L2 owner 委托架构师代裁（用户 2026-09-10 授权"你来定"），架构师据证据裁决并署名。
> 日期：2026-09-10（Asia/Taipei）｜k2 HEAD：`1a7391e`（W0R-FIX B1.5 PASS + R1 矩阵已签收）。

## 0. 决策输入指纹（签收时点）

| 输入 | SHA-256 |
|---|---|
| W0-R model（`m13_v57_big_w0r_corridor_model.json`） | `fee23ebe3aa6fed838441fbbb7e57c552dd025fc4f506a36cc49bc52b60741a2` |
| W0-R validation | `63993e6d3ed2af317a27d6c54a2926342c3a187660e3b07c000b0696c59d2112` |
| R1 矩阵（`m13_v57_r1_schema_gap_matrix.md`，含审核注记） | 已提交 `1a7391e` |
| SPEC / board / manifest / rules（冻结四源） | 与 W0-R inputs_sha256 一致（`3bdecb10…` / `f6273de6…` / `87c4c973…` / `0a459839…`） |

## 1. 裁决

### D0-1（F-9，R4 AC 墙）— 裁 R4 出链（SPEC 修订）

- 事实：SPEC.capacitor_walls 声明 32 只（C17–C32 / C49–C64），板面 0/32 放置、0/32 在网表
  （板面实际 18 只 C73–C90，无一落墙带）。R1 独立实测成立。
- 裁决：**MVP 范围内 R4（AC 墙穿越）出链**。西页模板由"connector→墙 pad→chip"改为
  "connector→chip 直连"；R4 相关守恒/强节点不进入 W3 输入白名单。
- 理由：AC 墙是 L2 声明、L1 无实体的悬空层，不构成当前 MVP 的冻结输入；补放置属上游输入
  重构且会使 W0-R 可行包络翻转（R1 C-1 已预警）；裁出链后 W0-R 终态不被推翻（其 span
  本就未把墙算入 blocker）。
- 落地动作：专项卡 **SPEC-REV-1**（修订 SPEC.capacitor_walls 为"out-of-scope for MVP"，
  保留原声明为附录存证，不动其余字段）。本卡不直接改 SPEC。
- 回滚：若日后恢复 AC 墙，须先 L1 补网表 + L2 补放置，并重跑 W0-R 全链。

### D0-2（F-10，REFCLK 层语义）— 定 F.Cu

- 事实：三源冲突（S1 设计=In2.Cu｜board-intent={F.Cu,In2}｜W0-R=F.Cu 候选）；
  SPEC.corridors 旧记 In6.Cu（栈中不存在）。
- 裁决：**REFCLK 资源层 = F.Cu**，与数据层 In2.Cu 分离。
- 理由：层间隔离消除 S-6（REFCLK J2 行 45.9/51.3 落 EAST/up 数据行区 [42.9,53.1]）的同层
  争 lane；W0-R 终态已按 F.Cu 通过，不重发；In6.Cu 视为 SPEC 笔误。
- 落地动作：SPEC-REV-1 同卡将 refclk 层记录校正为 F.Cu。
- 回滚：若改 In2，须 W0-R 按 In2 重发 REFCLK 证书并重新过 G1。

### D0-3（I-3，corridor x-ranges）— 确认

- 裁决：确认 `EAST_CHIP_TO_J2=[105.25,132.65]`、`WEST_MCIO_TO_CHIP=[65.05,82.35]`。
- 依据：R1 只读实测——WEST.west 65.05=J3/J4 体包围盒东缘（精确）、WEST.east 82.35≈U6
  西缘+0.35、EAST.east 132.65=J2 内列 pad x、EAST.west 105.25≈U6 东缘−0.35，与放置几何一致。
- 落地动作：无需改文件；G3 冻结契约引用本裁决即可。

## 2. 门控效应

- G2 = **continue**（D0 已签）。
- G3 解封：冻结 R1 矩阵 + W1/W2 契约；前置项 F-9/F-10/I-3 已裁，F-10b/F-1 已闭；
  剩余 F-2/F-3/F-4/F-5/F-6/F-7/F-8/F-11/F-12/F-13 按排程执行。
- G4 仍 sealed，直至 G3 冻结完成。
- W3 开工授权 = G3 完成之后，且必须消费 D0 本卡的 R4 出链 + F.Cu 裁决。

## 3. 禁令（本卡）

本卡不改 SPEC、不改冻结放置、不改 `_shared`、不改 W0-R/W1/W2 产物、不改 PCB 铜。
SPEC-REV-1 为独立专项卡，未开工。
