# K2 · P4 · **J-8/V3 判据测量实现 + M-02 文档载体修正** · v1 · 2026-09-17

> 缘起：监理自动续推「按已批准《K2 整体整改计划》推进**当前阶段**（P4，未全绿），阶段门未过不得越阶段」。
> 本轮只做**不需放行**的 ENG 面（`#K2-22 §三` 优先序 4「判据实现」+ 载体为**文档**的根因项）：
> ① J-8 `pads_within_outline` 测量实现（新草案区，**不动 `criteria/`**）；② V3 `ref_plane_continuity` 测量实现；③ M-02 文档载体修正。
> **未动**：生成器 / SPEC / 原理图 / 网表真源 / `criteria/` / 仓库板 / pro（均属待放行或不属本轮）。**未派 WORKER**；临时仅 `/tmp/opencode`。
> **禁新增检查齿（owner ②）**：两项均实现**已冻结维度**（登记册 §C J-8 / 计划 §3.3 V3），未新造维度。

## 1. 交付物

| 件 | sha256/16 | 内容 |
|---|---|---|
| `k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py` | **`1b177638cde3cd55`** | J-8 出框测量：Edge.Cuts AABB 内缩 + 逐 pad AABB（圆=半径；椭圆=矩形段⊕半圆**精确**；矩形/圆角/梯形=旋转外接框保守）+ 真外框多边形（`GetBoardPolygonOutlines` + `Inflate(-inset)`）双口径。**JSON 无 `verdict` 字段** |
| `…/measure_ref_plane_continuity.py` | **`7a3cc545c1447b04`** | V3 参考连续性测量：已填充内层平面并集 vs **zone 轮廓**并集（双口径）；逐高速段取「相邻上/下平面层」的覆盖比；输出阈值敏感性（供监理定应然值）。**JSON 无 `verdict` 字段** |
| `k2/README.md` | `d0c28708ba34fddf2`→**`dc28708ba34fddf2`** | M-02：删除「dual DS160PR810 (U7/U3)」；改单颗 `DS320PR1601`(U6)；AC 耦合标注「integrated in the device」 |
| `k2/docs/01-architecture.md` | **`e7a478b5420dc161`** | M-02 同上（EN） |
| `k2/docs/01-architecture.zh-CN.md` | **`6182d4a040d1cfc2`** | M-02 同上（ZH） |

## 2. J-8 `pads_within_outline` 实测（正/负控）

| 案 | 板 | sha16 | 焊盘 | AABB 口径出框 | 真外框多边形口径出框 | rc（`--fail-on-violation`） |
|---|---|---|---|---|---|---|
| **正控** | `k2/hw/k2_v4_8L.l5.kicad_pcb` | `6ff49da5678c2108` | 687 | **0** | **0** | 0 |
| 参照（冻结受审板） | `k2/hw/k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` | 616 | 0 | 0 | 0 |
| **负控**（合成：`D2` 北移 1.10mm，盘顶 32.60 < 内缩框 33.30） | `/tmp/opencode/l2/j8_neg.kicad_pcb` | `63a88da459817540` | 687 | **2**（`D2`.1 `P3V3`、`D2`.2 `SW_U2`） | **2** | **1** |

- 口径说明：`l4` 对该维度**不是**负控（其焊盘本就在框内）⇒ 负控用合成突变板，两口径**同时命中** ⇒ 判据有咬合。
- 接口件子集（`J2 J3 J4 J6 J9 J11 J12 J13`，P3-4）：`l5` 出框 **0**。

## 3. V3 `ref_plane_continuity` 实测（正/负控）

| 案 | 板 | sha16 | 已填充平面层 | 高速段(PCIe) | **名义口径**全长覆盖 | 严格口径 100% 覆盖 | rc |
|---|---|---|---|---|---|---|---|
| **正控** | `l5` | `6ff49da5678c2108` | `In1/In3/In4/In6` | 3653 | **3653/3653** | 3051（无 100% 602） | 0（无 `--fail-on-violation`） |
| **负控** | `l4`（冻结，8 铜层 Gerber `G36=0`） | `d4e81f647be7f980` | **（无）** | 2327 | **0/2327** | 0 | **1** |

- 严格口径下「最大覆盖 ≥ 阈值」的段数：`1.0 → 3051` · `0.99 → 3071` · `0.95 → 3162` · `0.90 → 3196` · `0.50 → 3249`；相邻层覆盖比分布 `n=5530 / min 0.0 / p05 0.0 / p50 1.0 / p95 1.0`。
- **口径待监理定（一句话，非 owner）**：严格口径的缺口来自**反焊盘/过孔空洞**（不可消除），故「投影覆盖该段全长」需明确为 **(a) 名义口径**（zone 轮廓，`l5` = 100%）、**(b) 严格但设阈值**（如 ≥0.95，`l5` = 3162/3653）、或 **(c) 排除短段**。ENG 只交测量，应然值归监理（计划 §3.2）。

## 4. M-02 载体修正（`dual DS160PR810(U3/U7)` → 单颗 `DS320PR1601(U6)`）

- 依据：owner `#K2-10` D-2（单颗架构）+ 板实测（`U6` = `DS320PR1601`，无 `U3/U7`）+ 真源图件已改名 `redriver_ds320pr1601_sideband_strap.kicad_sch`。
- 改的是**用户面文档**（README / 01-architecture EN+ZH）；未动 `pm_gate/artifacts/k2_v4/L3/**`（历史证据链，只增不改）。
- 复算：三份文件 `DS160PR810` / `U3` / `U7` 命中 = **0**。
- **残余**：M-02 的 ④（防复发）仍「无判据」⇒ 按 #K2-22 口径 ⑤ 仍 = **未闭**（载体已修）。

## 5. 对《逐条根因闭环表》的增量（见该件 §9 v1.1 追加节）

- `M-02`：③ 由「未修」→「**载体已修**（三文件 sha）」；⑤ 未闭（判据仍缺）。
- `J-8`：④ 由「pending 未实现」→「`pads_within_outline` **已实现 + 正负控命中**（待安装/签认）」；`density_and_clearance` 仍 pending（待 P3 阈值）。
- V3（`ref_plane_continuity`）：由「设计」→「**测量已实现 + 正负控命中**（待安装/签认 + 待监理定阈值）」。
- 计数变化：载体已修 **15 → 16**；载体未修 **30 → 29**；`根闭 / OUT` 不变。

## 6. 本轮未做（红线/待放行）

① 生成器源码（G-ROOT-1/2/3 = G9/G10/G11）—— **未获批**；
② SPEC / 原理图 / 网表真源（含 errata-2 nc 声明、N-07 未标注 refdes）—— **未获批**；
③ `criteria/` 两份安装 + `k2/pipeline.yaml` —— **gate 属主侧**；
④ ⑥ L2 候选板 `b2cfb087839afd73` 落板 —— **待监理放行**；
⑤ ⑦ 库侧「按板重建 + 重指 `lib_id`」—— **待监理裁定**；
⑥ 仓库板 `6ff49da5678c2108` / pro `d5e0ca067a7b585e` **未动**。

## 7. 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j8-v3-measurement-v1
# J-8 正控（期望 AABB 0 / polygon 0）
$K $D/measure_pads_within_outline.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --json /tmp/opencode/l2/j8_l5.json
# J-8 负控（合成突变板；期望 2 条、rc=1）
$K $D/measure_pads_within_outline.py --board /tmp/opencode/l2/j8_neg.kicad_pcb --fail-on-violation
# V3 正控（期望名义 3653/3653）
$K $D/measure_ref_plane_continuity.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --json /tmp/opencode/l2/v3_l5.json
# V3 负控（冻结板；期望 0/2327、rc=1）
$K $D/measure_ref_plane_continuity.py --board k2/hw/k2_v4_8L.l4.kicad_pcb --fail-on-violation
# M-02 复算（期望 0 命中）
grep -rn "DS160PR810" k2/README.md k2/docs/01-architecture.md k2/docs/01-architecture.zh-CN.md
```

—— ENG（ARCHER）· 2026-09-17 · P4 施工中（未全绿，fail-closed 不变）
