# K2 · P2 决策单（**4 项，各一句话即可解缚**）v1

> 用途：把 P2 剩余阻塞压缩成**一次可回**的四问。每项均已备好机器证据 + 可原样执行的落地方案；
> 收到裁定后 **ENG 不需再取一次证**，按 §5 顺序直接落地。
> 边界：本件只汇总，不新增判据/检查齿；`criteria/`、冻结件、`.omo/supervision/**` 未动。

## 1. 四项待裁

| # | 问题（一句话） | ENG 建议 | 机器证据（sha16 / 实测） | 收到后立即执行 |
|---|---|---|---|---|
| **U1 / S1** | `SPEC rev-20` 的 `components.anchor_fixes` 含 `C64`/`C66`（**板上不存在**），生成器 `:649` 严格 fail ⇒ 放行 **rev-21**？ | **(a) 放行**：出 `rev-21` = rev-20 **去掉** `anchor_fixes.C64`/`.C66` **+** `spec_version 1.1.spec-rev-20 → 1.1.spec-rev-21` **+** 不带 `_draft_note`；`project.yaml` 重指向；rev-19/rev-20 原件不动 | **deep-diff 已证**：`/tmp` 草案 vs rev-20 差异 = **仅** `anchor_fixes.C64/C66` 的 5 个叶子删除 + 1 个草案注记键；**`值不同 = {}`**（其余内容逐字节承 rev-20）。（注：草案 `spec_version` 仍写 rev-20 ⇒ 真件须补 bump） | 写 rev-21 → 改 `project.yaml: spec_name` → 复出 sha 报监理 |
| **S2** | ReDriver sheet 真源 `paper=A2`，但 `U6=DS320PR1601` 单符号 **354 脚**（R136/L218、2.54mm）⇒ 几何放不下；纸张是否改 **A0**？ | **(a) 真源该 sheet `paper: A2 → A0`**（1 字段）。备选 (b) 符号拆 unit/多页（需新工具；牵动球↔脚表征则按 owner #14 属 L1）；(c) 越界绘制（不推荐） | `half_height 281.43mm`；A2 可行域 **空集**、A1 仅差 0.1mm；**A0 实测**：全 5 sheet + root 生成成功、C1 逐字节同。证据件 `K2-P2-R1-U2-sandbox-dryrun-and-stoplines-v1.md` `789c5e65c6896457` | 改 yaml 该 sheet paper → 跑 R1/R2 安装（§5） |
| **S3** | GND 网无 `power_out` 驱动 ⇒ 全图**唯一 1 条 ERC error**（`U6/AC4`）；按 (a) 给 driver 加电源旗标，还是 (b) 改真源地脚类型？ | **(b) 真源侧：U6 地脚 `power_in → passive`**（不动现行「零电源旗标」策略）。若选 (a)（driver 加 `PWR_FLAG`）= **策略变更，须备案** | U6 354 脚中 **152 脚 `power_in` 全在 GND**；GND 网 211 节点 = 152 power_in + 54 passive + 5 input，**无 power_out**；现行图基线 0 error（旧符号地脚即 passive） | 改 yaml 引脚类型 → 重跑 C1–C4 复验 |
| **O2** | E4 判据②「产物 refs==42」与真源 yaml K2 侧 **55** 件口径不一致，以哪个为准？ | **本阶段判据 = 42（对齐真源板）**；终局（P4）应为 55 —— 请确认；若确认终局 55，E4② 需改判并追加补件几何/定位 | 真源板 42 件；yaml `card ∈ {2, both}` = 55 件；差 13 = `D2, L1, R35–R39, R40, R41, R42–R45`（= E1「板 42 ⇒ P4 补 13」）。证据件 `K2-P2-U4-generator-g1g8-sandbox-evidence-v1.md` `9659f3e23b2aca4b` | 若维持 42：无动作；若改 55：E4② 改判 + 补件落位 |

## 2. 现状（已就绪，等上述裁定即可安装）

| 工作流 | 状态 | 沙箱证据（未入仓/未安装） |
|---|---|---|
| R1/R2 图落盘（路径 (ii)） | **沙箱全通**：C1 确定性 PASS、C2 网名 100/101（唯一差异 = `PWR_5V_KEY` 单节点网，见下）、C4 结构 PASS、ERC 残差全归因 | driver `k2_sch_gen_v1.draft.py` `9aa52762444851b8`（217 行） |
| §五 G1–G8 生成器 | **沙箱全通**：E4① 两次 sha 同 / ② refs 42 / ③ 边框 46mm / ④ 自检 6/6 / ⑤ `kicad-cli pcb drc` 0 违规 | 副本 `k2_gen_v5.gfix.draft.py` `c7a2887a58b5c789`（799 行） |
| 另项（**非阻塞**，随 R1 一并定） | 真源 `PWR_5V_KEY = {C89/A}` 为**单节点网** ⇒ 网名无法进 KiCad 网表（C2 唯一差异项）。须确认是**漏节点**还是**有意占位** | 证据同上（U2 doc §4） |

## 3. 收齐四裁后的落地顺序（ENG 一次执行）

1. **rev-21**（U1）+ `project.yaml` 重指向 + 复出 sha；
2. **R1/R2 安装**：driver 落 `k2/tools/` → 出图到 `K2_OUT_SCH` → 跑 C1–C4 → 备份 `hw/sch`+`hw/lib` 后安装（回退点 `git checkout -- k2/hw/sch k2/hw/lib`）→ 复跑 C1–C4；
3. **E1 复算**（删除 60 + T1 并网 32 对 + T3 重映 + 补 12 + 新增网 10）→ 交监理；
4. **§五 G1–G8 粘贴** + E4 复验（两次 sha / refs / 边框）；
5. 交监理判 **P2 门**（E1–E4 全 0 + Z1–Z4）。**P3 未批不开。**

## 4. 复现锚（全部可复跑）

- U2 件：`k2/docs/K2-P2-R1-U2-sandbox-dryrun-and-stoplines-v1.md` `789c5e65c6896457`
- U4 件：`k2/docs/K2-P2-U4-generator-g1g8-sandbox-evidence-v1.md` `9659f3e23b2aca4b`
- 冻结件（末次复测未变）：SPEC rev-19 `5f72182a2616392c`、设计源板 `fb07d25ac426ff84`、交付板 `d4e81f647be7f980`；仓内生成器 `7577a15a76a09a22`
