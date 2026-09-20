# W8-GEN-1 — 建板器补 FPID 库昵称（**已制备 · 沙箱实证 · 待批落地**）

**状态：未落地（NOT LANDED）**。落地 = 改生成器 `k1/tools/k1_board_builder.py`（红线：未获批不得改）
⇒ 载荷 = `k1_board_builder_fpid_W8GEN1.patch`，**待监理放行**后与落板/证据重出**同一批**执行。

## 根因（复核确认）
`k1_board_builder.py` 以 **目录路径** 调 `pcbnew.FootprintLoad(lib, name)` ⇒ 生成 footprint 的
**FPID 无库昵称** ⇒ 板件写成 `(footprint "C_0402_1005Metric")` 裸名
⇒ W-8 判据 `n_no_library_link = 42`（该维**空过**）。
真源 `boards/k1_board.yaml#devices[ref].footprint` **已带** `"LIB:NAME"`（42/42 均有前缀），
建板器只是**丢弃**了它。

## 补丁（2 处，共 33 行）
1. 新增 `_board_yaml_footprints()` / `fpid_for()`：昵称取**真源** `k1_board.yaml#devices[ref].footprint`；
   与 `COORDS` 件名不一致 ⇒ **RuntimeError（fail-closed，禁静默）**；缺真源则回退 `basename(lib).removesuffix(".pretty")`。
2. `build()` 内 `fp.SetFPID(pcbnew.LIB_ID(nick, nm))`。

## 沙箱实证（可复现 · 未触仓库）
沙箱 = `/tmp/opencode/k1gen/`（`tools/` 放补丁版与原件版 + `boards/` + `lib/` 副本），
`KICAD_FOOTPRINTS=<AppDir>/usr/share/kicad/footprints`，`AppDir/usr/bin/python3.11`。

| 项 | 原件建板器 | 补丁建板器 |
|---|---|---|
| footprint 总数 | 42 | 42 |
| **带库昵称** | **0** | **42** |
| 裸名（`n_no_library_link`） | **42** | **0** |
| 两次连跑 sha256 | — | **逐字节一致**（`b68105d2e8914aa7…`） |

**验收判据达成**：`n_no_library_link 42→0 ∧ n_footprints=42`（#K2-51 §二 W8-VAC-1 修法·验收条）。

**产物 vs 现役板差异 = 98 行** = 84 行 FPID（42 对）+ **14 行 U1 侧 net 重排**
（= 已按订正 pinmap 落位 ⇒ **同批可闭合 `K1-U1-BOARD-SYNC`**）⇒ 几何/焊盘/网表**零功能改动**。

## ⚠ 补丁的 fail-closed 断言**当场揪出一处真源漂移**（新发现）
```
RuntimeError: U10 footprint 真源不一致: k1_board.yaml='Package_TO_SOT_SMD:SOT-23' vs COORDS='SOT-23-5'
```
- `k1_board.yaml#devices.U10.footprint` 声明 **`Package_TO_SOT_SMD:SOT-23`（3 pad）**，
  而板件实测为 **`SOT-23-5`（5 pad，与 `sch_pins=5` 自洽）**；该件 `geometry.note` 自己写着
  「符号 5 pin vs SOT-23 3 pad 不匹配 (reconciliation **OPEN-2**)；实际器件应为 SOT-23-5」。
- ⇒ **声明未随 ② 换件复算** = 与 `K1-D10/D11/D12` 同族的『声明/实现漂移』**新实例**（记 **K1-U10-FP-1**）。
- **落地必带真源订正**：`k1_board.yaml#devices.U10.footprint` → **`Package_TO_SOT_SMD:SOT-23-5`**（1 行，声明订正，非设计变更）。

## 落地批（须监理放行 · 建议一笔）
1. 应用 `k1_board_builder_fpid_W8GEN1.patch`（生成器）
2. 真源订正 `k1_board.yaml#devices.U10.footprint`（K1-U10-FP-1）
3. 重建板 → **同批**重出 `pads_within_outline` / `density_and_clearance` / `min_clearance` / `w8` 证据
   （用 `k2/docs/drafts/p4-j8-*` 参数化工具；**禁** `k2_p4_j8_measure_v1.py`，K1 oval drill 崩）
4. 提交含 `pm_gate/artifacts/k1/L3/*` 建板记录（PCB↔SPEC 门禁）
5. 复算 K1 判定（4/6 收口）
