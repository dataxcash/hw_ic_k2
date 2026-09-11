# CO-49 — 【L3 自裁】L4 板**字节可复现**（解除 pcbnew 保存的非确定性：segment/via/zone 顺序 + uuid）

> 2026-09-12｜性质：**施工/证据链修复**（零几何改动、零判据放宽）｜无 L1 变更
> 前置：CO-48 `7e094c2db5bf3b3d`｜触发：boundary §6.1 记载的已知限制「板文件字节不可复现」。

## 1. 现象（实测定位）
两次连续重建 `k2_v4_8L.l4.kicad_pcb`，sha 每次不同（`4d36212f6492262b` → `e8d447a9df101223` → `302ff95cdc29ed65`）。
逐块比对（对根块 `(kicad_pcb ...)` 的一级子块做括号/字符串安全扫描）结论：
- **完全相同**（含 uuid，逐字节）：`footprint`×42 / `gr_line`×4 / `setup` / `layers` / `general` / `paper` / `embedded_fonts`；
- **仅顺序 + uuid 漂移**：`segment`×2441 / `via`×252 / `zone`×4；
- 这三类块的**去 uuid 多重集**两次完全一致，且**连续同类 run 结构一致** ⇒ 内容确定、仅排列不确定。
违反宪法第三条证据标准（可复现：命令+原始输出）与第五章冻结性：签核件 sha 每次重建都变，无法复现。

## 2. 修正（L3 施工工具；不改几何）
`tools/p3_v57_l4_apply_drawing.py` 新增 `canonicalize_board()`，在 `pcbnew.SaveBoard()` 之后、计算 `dst_sha256` 之前：
1. 对 `segment`/`via`/`zone` 的**每段连续同类 run 内**按「去 uuid 文本」排序（内容确定 ⇒ 全序，实测无重复块）；
2. 以该文本派生**确定性 uuid5**（`uuid.uuid5(NAMESPACE_URL, canon)`）替换原 uuid；
3. 只触碰上述三类块，其余块逐字节保持；**幂等**（再跑一次字节不变）。
记录的 `application` 增记 `canonicalized_blocks = 2697`（2441+252+4）。

## 3. 验证（实测）
- **构建幂等**：连续 3 次构建同 sha **`cdcb869e9827ec87`**。
- **全链可复现**：`构建 → L4 validator → L5 signoff` 连跑两轮，7 件产出**逐字节一致**
  （板 / l4_construction / l4_validation / fab / dfm / si / g7 md）。
- **几何/判定不变**：L4 PASS（68 网 / 2441 段 / 252 via，L4-A..E viol 0）；
  L5 `FAB ok | DFM PASS new=0 | 在册 0/68 | SI PASS skew 0.0031`；板可被 `pcbnew.LoadBoard` 载入并被 `kicad-cli pcb drc` 正常检查。
- **冻结源未动**：`src_pcb_sha256 = fb07d25ac426ff84` 不变（仅规范化 dst）。

## 4. 指纹（现行）
| 件 | sha16 |
|---|---|
| applier `tools/p3_v57_l4_apply_drawing.py` | `16cc8f146c229325` |
| L4 板 `k2_v4_8L.l4.kicad_pcb` | `cdcb869e9827ec87` |
| l4_construction / l4_validation | `58ccf62e881f2a8f` / `5bdf42b50a34ed3f` |
| fab / dfm / si | `9a223923b029a1f9` / `f5a691f4cda234df` / `a3187aed93c48b6b` |
| G7 记录（L5-G7.6，自动重生成） | `4d3a6429945916e9` |

## 5. 备注
历史里程碑 tag（`k2-v57-g7-l5-pass` `b5afe47`、`co46` `ff09748`、`co47` `ab23eeb`、`co48` `e740033`）为其自身 rev 的不可变快照，
其中板 sha 为规范化前值；**本件不改写已发布段**，仅自本 rev 起提供可复现板。几何与判定与 `b5afe47` 完全一致（同 drawing `dfa1d7c4a811b0da`）。
