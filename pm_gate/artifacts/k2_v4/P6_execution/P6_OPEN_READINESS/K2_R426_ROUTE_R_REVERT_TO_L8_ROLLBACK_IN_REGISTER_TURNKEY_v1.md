# K2 · R426 —— **路线 R（回退到 l8）之落地程序**：**在册即有回滚路径** · turnkey（只读）

- **ts** 2026-09-22T23:57:09 · **from** ENG·ARCHER（续接 · 承 handoff R423）· **to** 监理 · **owner 闸口 0**
- **authority**：owner #14⑥（不 park · 给下一阶段可执行计划并推进）· owner ⑧ · #K2-142 §四 · #K2-136 §三 · TAG_POLICY(#K2-56) · handoff R423 §8.4
- **边界**：只读普查。**未删件 · 未改 `project.yaml` · 未出包 · 未烙板 · 未派工**。
- **首动作**：已读全部 `K2-RULING-*` ⇒ 最新 **#K2-144** · 无更晚裁定 · 无 owner 回件。

## 0. 一句话
**回退（路线 R）不需要新板、不需要新设计，而且它的落地程序早就写在册上** —— 就写在**冻结 SPEC rev-55 自己**的 `rollback` 字段里。受审板 l8 已在库、铺铜已填、已过判据 19/19 与 DRC error=0。⇒ **监理裁「不保留 C-w 搬迁」之日，即可一笔同批落库。**

## 1. 在册回滚路径（**原文引用**）
> `SPEC_k2_v4.spec-rev-55.json` → `_spec_rev_55.rollback`：
> **删除本文件并把 pm_gate/project.yaml 之 spec_name 指回 SPEC_k2_v4.spec-rev-54.json；l9 删除即可（l8 未动）**

## 2. turnkey 清单（谁做 / 哪一步 / 现状）
| # | 动作 | 属主 | 现状 |
|---|---|---|---|
| 1 | 裁定「C-w 搬迁不保留」（owner 甲 **或** 监理走廊/搬迁处置） | owner / 监理 | **待**（= v65 Q1） |
| 2 | `pm_gate/project.yaml`：`board_path` → `hw/k2_v4_8L.l8.kicad_pcb`；`spec_name` → `SPEC_k2_v4.spec-rev-54.json` | ENG（放行后） | 现值 = l9 / rev-55（只读核对） |
| 3 | 删 `hw/k2_v4_8L.l9.kicad_pcb`（或移出 `hw/` 留证） | ENG（放行后） | l9 在库 `77aaa63fe016b450` |
| 4 | SPEC rev-55 件删除（或 bump 新 rev 重声明 l8）。**门禁**：`.kicad_pcb` 变更须同批含 SPEC 变更 ⇒ **2/3/4 必须同笔** | ENG（放行后） | rev-55 = `964101b19015f6d7` |
| 5 | P4 派生模型指纹重锚（R414 范式） | ENG | l9 现行 `d34362c4847ad9ba`（**O-1 禁引 `84f19701dfc1db31`**） |
| 6 | `criteria` rev=7 之内容与「l9 落库硬前置」是否随之重判 | **gate 属主** | 未落（rev=6 MATCH） |
| 7 | Gerber/Excellon/MANIFEST 随包重出 + DFM 重跑（R270 项13 · owner ③） | ENG（放行后） | 未做（管道就绪） |
| 8 | 里程碑 tag（TAG_POLICY §2/§3）+ push 至 `0 0` | ENG | **push 已 `0 0`**（本会话 · #K2-56）；tag 待落库时打 |

## 3. 回退后之验收（读数）
1. 判据 **rev=6** 对 l8 = **19 OK / 0 FAIL**（在册 E3-standard-call-l8）
2. DRC **error=0**（本会话同仪器同 pro 实测 · 204 warning · unconn 0）
3. DFM 逐项 **全 PASS**（R425）
4. 束间面 **≡ l9**（R424 F9 · caliber-free ⇒ R416 之 `0.4491` 在 l8 同值）
5. 16 网 ②-UP 在 l8 即 **F→In2→In5→B（4 孔）** ⇒ 与 owner 甲「放宽孔数/层数」**相容**

## 4. 只读核对之更正
- **O-4 已不复现（更正）**：#K2-137 O-4 记 `project.yaml::board_path` 滞后指 `l7`；**现值 = `hw/k2_v4_8L.l9.kicad_pcb`** ⇒ 已随 rev-55 落库一并修正。
- **rev-54 无板声明**（无卡、无 `board_sha16`）⇒ 回退后板声明由 **rev-53（`7a5c8991` = l8）** 承接，**无悬空声明**。
- **SPEC 内 l9 声明点 = 4 处**：`_spec_rev_55.board_sha16` · `board_file` · 及 `updated_board_sha16_declarations` 之 3 项（`keepout_geometry` / `pd.zone_defs.board_realized_zones` / `mounting_holes`），皆 `7a5c8991 → 77aaa63f`。

## 5. 声明
本件**不主张**路线 R 为唯一/首选解 —— 它是**成本最低**（零设计）的一条；路线 F（保留搬迁）仍待 Q2 指定设计归属。**裁定权在监理**（走廊/搬迁处置 = 监理自裁面 · owner #14⑦）。

---
—— ENG（ARCHER）· 2026-09-22T23:57 · 只读 · owner 闸口 0 · sha16 `4df6c5e63dd15ac8`
