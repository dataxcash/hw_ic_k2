# K2 · P4 · **`(i-a)` 干跑实证（纯证据）**：µm 量化修复**必要但不充分**，残余 3 项**非量化** · v1 · 2026-09-19

> 授权：**#K2-30 §2.3**（`U-03`/`M-09`/`J-7`）· handoff `k2-p4-handoff-20260920-inc114-context-handoff.md` **§7-3「裁定前可做的纯证据项」**。
> **本件不施行任何载体改动**（生成器/SPEC/板/库/判据/`criteria/**` 均未动）；全部演算在 **`/tmp/opencode/arc_r1/`**。
> ENG（ARCHER）· 2026-09-19 · 判据锚 **rev=2（MATCH）** · 工具 `k2/tools/k2_w8_footprint_audit_v1.py` **`75404d706413d546`**（== 在册测量册同器）

---

## 〇、一句话（决策相关）

**`(i-a)`（3 处 `:.3f`→`:.6f`）干跑后，喂 `lib_electrical_level` 的 W-8 电气级审计由 `49 / 5 / 4 / 0` 变为 `51 / 2 / 4 / 1`** —— 量化类差异（`L1`·`U6`·`U1` 坐标）**归零**，但 **`lib_electrical_level` 期望（`n_electrical_diff==0 ∧ n_pad_name_set_only==0`）仍未满足**：残余 = `C85`/`J3` 的 pad `rot` 0 vs 库 180（矩形对称，`rel_geom_same=True`）+ `U1` 库侧**无号 `F.Paste`** pad（生成器**明文**跳过）。
⇒ **#6「`U-03`/`M-09`/`J-7`」的选项 ① (i-a) 单独不足以关 FAIL-2**；须 (A) 扩生成器范围 或 (B) 判据侧具名口径（须版本 bump + 签认），否则 FAIL-2 维持。

---

## 1. 方法（干跑，零载体改动）

1. **基线**：直接跑在册生成器 `k2/tools/k2_gen_v5.py`（`1ca5ac79698f5873`）→ 产出 **`d67c0f048f0d0423`**（逐字节 == 段1 在册产物 `s1`），**确定性/无漂移复核通过**。
2. **变体 1 `(i-a)`**：生成器副本 + 3 处 `:.3f`→`:.6f`（`:319` 原点 · `:339` thru_hole pad · `:345` smd pad）→ **`1c707fbeccc5b69f`**。
3. **变体 2 `(i-a′)`**：同 3 处改 `f"{v:.6f}".rstrip("0").rstrip(".")`（去尾零）→ **`67f0290a0b631c09`**。
4. 两变体同跑 W-8 电气级审计（同一工具 sha `75404d70`、同一库根 `hw/lib`）→ 与基线、与在册 `w8_audit_seg1_output_d67c0f04.json` 逐数比对。

**生成器自检**：两变体均 **6/6 PASS**；**54 器件 · 672 pads · 100 网 · 128 NO_CONNECT · G10 keepout=8/copper=10/npth=4** 全同基线 ⇒ **无拓扑/网表/语义变更**。

---

## 2. 结果 A —— 量化分量（与根因件 `94d259bf` 逐数吻合）

逐分量差（变体 − 基线，按 ref/pad 解析）：

| 项 | 值 |
|---|---|
| 位置分量差 **x** | **164** |
| 位置分量差 **y** | **52** |
| 分量合计 | **216**（== 根因件 216/1232） |
| 受影响 pad | **216 / 672** · 逐 ref = **`L1` 2 · `U1` 48 · `U6` 166** |
| **max\|Δ\|** | **0.5000 µm** |
| footprint 原点（`:319`）变化 | **0 / 54** ⇒ **`:319` 对现行输入为 no-op** |

⇒ **有效最小补丁 = 2 处**（`:339` · `:345`）；`:319` 属一致性冗余（改与不改等价）。`(i-a)` 与 `(i-a′)` 在**全部读数上等价**（仅板文本形式不同）⇒ 变体选择**不影响**本节任何结论。

---

## 3. 结果 B —— W-8 电气级审计（**喂 `lib_electrical_level` 的同一器**）

| 读数 | 基线（`d67c0f04`） | 在册 s1 件 | **(i-a) `1c707fbe`** | **(i-a′) `67f0290a`** |
|---|---|---|---|---|
| `n_electrical_identical` | 49 | 49 | **51** | **51** |
| `n_electrical_diff` | **5** | **5** | **2** | **2** |
| `n_pad_name_set_only` | **0** | **0** | **1** | **1** |
| `n_no_library_link`（`H1..H4`） | 4 | 4 | 4 | 4 |
| diff refs | `C85 J3 L1 U1 U6` | 同 | **`C85 J3 U1`** | **`C85 J3 U1`** |

- **归零**：`L1`（2 pad，Δdx 0.5µm）· `U6`（166 pad，Δdx 0.4µm）· `U1` 的 48 处坐标差（`n_pad_diff` 由 48 → **0**）。
- **`0 → 1` 不是新增缺陷**：`U1` 由「电气级差异」**重分类**为「仅 pad 名集合不同」（原差异 = 坐标 48 处 + 库侧 1 无号 pad；坐标修复后只剩后者）。
- **段1→`l6` 无二次引入**：在册 `w8_audit_board_l6_30fa8496.json` 与 `w8_audit_seg1_output_d67c0f04.json` 读数**同为 49/5/4/0** ⇒ 段2/段3 不动 pad 几何（本干跑读数直接适用于 `l6`/未来 `l7`）。

---

## 4. 结果 C —— 残余 3 项：**均为非量化，且均属已登记口径**

| ref | 库件 | 差异 | 性质 |
|---|---|---|---|
| `C85` | `C_0402_1005Metric__2`（板 `fp_rot=180`） | pad `rot` 板 **0** vs 库 **180**（2/2 pad）；`rel_geom_same=True` · `uniform_translation=True` | **矩形 pad 180° 自对称** ⇒ 铜形/尺寸/位置全同（仅方向字段差） |
| `J3` | `MCIO_4i_SFF-1016_RASide__1`（板 `fp_rot=180`） | 同上（**38/38 pad**）；`rel_geom_same=True` · `uniform_translation=True` | 同上（矩形） |
| `U1` | `MCU_STM32G0_LQFP48` | 库 **50** pad vs 板 **49**：库侧多 1 个 **无号 pad** `(pad "" smd roundrect (at -1.2 -1.2) (size 0.97 0.97) (layers "F.Paste") (roundrect_rratio 0.25))` | **仅 `F.Paste`（无铜层）**，非电气；生成器 `load_mod_pads()` 明文跳过：*「仅取带号 pad（无号 F.Paste 阵列 = 非电气性；带号口径见 D 待裁登记）」* |

⇒ 残余项**不含任何 µm 量化**；`(i-a)` 之外还须对「pad 方向 0/180（矩形对称）」与「无号 `F.Paste`」二者**取口径或扩发射面**。

---

## 5. 决策影响（供 #6 一句话裁定；ENG 不择一）

| 路径 | 内容 | 代价 | 结果 |
|---|---|---|---|
| **(A)** 扩生成器范围 | 在 `(i-a)` 之上再改发射面：pad 行补 `rot`（来源 = 库 `(at x y rot)`）+（可选）发射无号 `F.Paste` pad | 改生成器（须授权）⇒ 全链 sha 变 ⇒ 重落件 `l7` + 全链重锚；`size/drill` 不动 ⇒ 铜形仍不变 | 预计 `n_electrical_diff=0 ∧ n_pad_name_set_only=0` ⇒ **FAIL-2 可关**（须 `l7` 实测确认） |
| **(B)** 判据侧具名口径 | 不改载体：判据具名「矩形 pad `rot` 0≡180（`rel_geom_same=True`）」「无号 `F.Paste` = 非电气」 | `criteria/**` rev bump + 签认（**非新增齿**，属口径具名） | `(i-a)` + 具名口径 ⇒ **FAIL-2 可关**（无需扩生成器范围） |
| **(C)** 维持现状 | 不修 | 零改造 | `n_electrical_diff=5`、`n_pad_name_set_only=0` ⇒ **FAIL-2 维持**（P4 关门被阻） |
| **(D)** 仅 (i-a)（决策纸原选项 ①） | 3 处精度补丁 | 全链重锚（贵） | **FAIL-2 仍红**（2 + 1）⇒ 单独不足 |

**勘误（对决策纸 #6 代价栏）**：原选项 ① 记「改 3 处 → 重落件 `l7` + 全链重锚」；实测**该代价换不到 FAIL-2 转绿**（尚差 (A)/(B) 之一）。原选项 ③（判据侧具名量化容差）**范围偏窄**：真正需要的具名不是「量化容差」而是「矩形 pad 方向等价 + 无号 `F.Paste` 非电气」两项。

---

## 6. 复现命令（只读；约 5 s）

```bash
K2=/home/fila/jqdDev_2025/ic_hw/k2; T=/tmp/opencode/arc_r1
$K2/../AppDir/usr/bin/python3.11 $K2/tools/k2_w8_footprint_audit_v1.py \
  --board $T/s1_6f.kicad_pcb --proj-lib $K2/hw/lib \
  --out-json $T/w8_6f.json --out-md $T/w8_6f.md
```
- 基线复现：`PM_GATE_PROJECT_ROOT=$K2 K2_OUT_PCB=$T/s1_base.kicad_pcb K2_OUT_JSON=$T/s1_base.json python3 $K2/tools/k2_gen_v5.py` ⇒ `d67c0f048f0d0423`。
- 干跑副本（含 3 处补丁）：`/tmp/opencode/arc_r1/k2root/tools/gen_6f.py` · `gen_strip.py`（**临时件，非仓库件**）。
- 本件读数件：`/tmp/opencode/arc_r1/w8_{base,6f,strip}.json`（`board_sha16` = `d67c0f04…/1c707fbe…/67f0290a…`；`tool_sha16` = `75404d70…`）。

---

## 7. 边界

未改生成器/SPEC/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿；未放松任何下限；未以「接近 0」宣称归零（残余 3 项**具名**）。临时仅 `/tmp/opencode/arc_r1/`。
