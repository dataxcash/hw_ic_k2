# K2 · P4 · **待裁事项一张纸**（ENG 侧已收敛；供监理逐项一句话裁定 / 升级人工）· v1 · 2026-09-19

> 来源：`inc107–inc114` 交付物；每条给「现象 → 载体现状 → 证据（sha16）→ 一句话选项 → 代价」。**ENG 不择一**。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2（MATCH）· 受审板 `l6 30fa849641323f98` · k2 `806e7d5`

| # | 事项 | 现象 / 载体现状 | 证据 | 一句话选项（ENG 不择一） | 代价 |
|---|---|---|---|---|---|
| 1 | `ref_plane_continuity` **判别半径 `R`** | 主判 `non_antipad_gap==0` 的结论随 `R` 翻转：`R=0.25` ⇒ **20.8905 mm²（FAIL）**；`R=0.5/1.0` ⇒ **0.0（PASS）**；缺口腔尺度集中 0.5–1.0 mm | `K2-P4-REFPLANE-NONANTIPAD-GAP-MECHANISM-AND-DISTRIBUTION-v1.md` `bc91256a` | ① 钉死 `R`；② 或改采**成因派生定义**（antipad = pad/via 按 zone clearance 外扩并集） | ① 零改造（只定阈值）；② ENG 实现新定义（非新增齿）+ 重测 |
| 2 | `l6` pro **`net_settings` 允许集外差异** | 相对 `l5` pro：54 键旧命名死键（`*_U3`/`*_U7`，板上 0 命中）+ 补 9 键 `DS320_STRAP_*`→`LOW_SPEED`；**类定义逐字段同 · 68 个 PCIe85 网归类同 · 无任何网 clearance 改变 ⇒ DRC 中立** | 报告 §23.3 · 提交 `2b4792c` | ① 接受；② 一次提交回退（`l5` pro 原件未动） | 回退 = 1 commit（但会带 54 死键/9 网误类） |
| 3 | **`M-14` 无判据类口径** | 三臂实证：**坏指针时 `red_team.R13` 静默 `[]`（fail-OPEN）**；`check_qa.py:22` 基址 `_shared` ⇒ 恒 FAIL | 闭环表 §16.2 | ① 钉死「`board_path` 基址 = 项目根」+ 既有消费者加 fail-closed 断言（非新增齿）；② 或维持未闭 | ① 改 `_shared` 消费者（须授权）；② P4 关门被阻 |
| 4 | **`#K2-31 §四-4` L2 载体整改授权** | refplane ④-**后**读数需整改（反焊盘阵列/补缝合孔）⇒ **改受审载体** | 报告 §24 · `bc91256a` | ① 授权整改；② 维持 `enabled:false`（不阻 Gerber，阻 P4 关门） | ① 改板 ⇒ 重落件 + 全链重锚；② 保持未闭 |
| 5 | **`NG-1`（新）** | SPEC `corridors_clearance_basis_v24` 在册 `U6 board_measured = 82.76/105.00`（δ **0.16**）在 **4 板 × 4 口径**下皆不可复现（恒 `82.60/104.84` ⇒ δ=0.00） | `K2-P4-F9-CORRIDOR-CALIBER-QUANTIFICATION-v1.md` `a316c49a` | ① 具名该 0.16 的测量口径；② 或更正为 82.60/104.84 | ② 改 SPEC（须 owner/监理；ENG 只读） |
| 5b | L2 冻结表回改（`F-9`） | 冻结表用**器件体宽**、SPEC/板侧用**焊盘外接框**（差 0.25/0.41 mm，**不影响制造**） | 同上 | ① 回改冻结件；② 或具名「以 SPEC 口径为准」 | 改冻结件 ⇒ **须 owner 批** |
| 6 | `U-03`/`M-09`/`J-7` **四路择一** | 残余 5 件亚微米差 = **生成器 `{:.3f}` µm 量化**（库侧 216/1232 分量非 µm 对齐；逐分量吻合 `U1`10/10·`L1`4/4·`C85`4/4·`J3`12/12） | `K2-P4-LIB-ELECTRICAL-LEVEL-ROOTCAUSE-MICRON-QUANTIZATION-v1.md` `94d259bf` · **修复规格** `K2-P4-GENERATOR-MICRON-QUANTIZATION-FIX-SPEC-v1.md` | ① **(i-a) 生成器 3 处 `:.3f`→`:.6f`**（或 `(i-a′)` 去尾零变体）；② 库按 µm 网格重建；③ 判据侧具名量化容差（须版本 bump+签认）；④ 维持 FAIL | ① 全链 sha 全变 ⇒ 重落件 `l7` + 全链重锚；③ 改判据 |
| 7 | `J-1` **7 类 warning 处置登记** | `l6` DRC **164 全 warning / error 0 / unconnected 0**；7 类未登记共 **90 条**（`silk_over_copper`37·`track_not_centered_on_via`30·`silk_overlap`15·`via_dangling`4·`silk_edge_clearance`2·`track_dangling`1·`copper_sliver`1），已逐类给归属 + **不豁免**建议 | `K2-P4-J1-WARNING-DISPOSITION-LEDGER-AND-U03-REMAINDER-v1.md` `a53a8550` | ① 批准登记（gate 属主安装 `criteria/**`）；② 或指定不同处置 | ① 改 `criteria/**`（须签认 + 版本 bump） |
| 8 | 「**无判据类**」批量改判 | `M-02`（README/architecture 双 DS160PR810 = 0 命中，载体已修）· `M-14`（见 #3）· `F-3`/`N-02`（SPEC rev-50/指针载体已修）· `N-03`（`l6` pro `top_level_sheets=k2_sch.kicad_sch`（存在）+ `sheets` 键已消 ⇒ 载体已修） | 闭环表 §15.1 · §17.1 · §16.2 | ① 批定「无判据类」根闭口径 ⇒ 5 条转根闭；② 逐条另定 | ① 口径裁定（零改造）；② 续留未闭 |
| 9 | `density_and_clearance` **rev=3 启用** | 测量件已通达标（`l6`：10mm frame 峰 **7 ≤ 8**；最小铜间距 bracket **[0.100,0.105] ≥ 0.100**） | E3 件 `e861fd9d` · 报告 §23.4 | ① 启用（gate 属主 rev bump + 签认 + 锚 rev=3）；② 或调阈值 | ① 改 `criteria/**`（须签认） |
| 10 | **`L-1` 具名接受（C4）** | 54 件中 **28 件仅板来源**（canonical 布局解 = 已批准落位捕获，非独立求解） | 闭环表 §14.1 · §17/§23.8（C1 `dfbf65c5` + `086d453d` 未动） | ① P4 关门时具名接受；② 或转 owner 授权 (c) | ① 零改造（须具名留痕） |

> **P4 关门前置**：上表 1–10 全部裁定 + 载体落地后，方得「全 14 条闭 ⇒ P4 关门判定」；**`N-01`（出 Gerber）属 P5，阶段门未过不得越**。

---

## 附录 A（inc114 追加，2026-09-19）：新事实两条

| # | 事项 | 内容 | 归口 |
|---|---|---|---|
| 11 | **P3 图集对新受审板无法干净重发** | `l6` 重生成图集 vs 在册图集（锚 `dae8dc8d`）键级差 34；实质差 = `J3`/`J4` `footprint_file=None`、`footprint_pads` 38→0 ⇒ `C3.unresolved_footprint` 0→**2** ⇒ 与 **#6（`U-03`/`M-09`/`J-7` ⑦ `lib_id` 未重指）同一根因**；在册图集**保留历史件**、**不**覆盖 | **与 #6 同批裁定**（#6 的收口路径同时解锁图集重发） |
| 12 | **rev-51 `board_sha16` 形式已自修** | rev-51 初版 8 处 20hex（`30fa849641323f98104f`）违反 16hex 约定 ⇒ `k2_p3_drawings_v1.py` 对 `l6` **fail-closed**；已修正为 `30fa849641323f98`（rev-51 `e96f2df0 → 522a904f`），复验：图集器 PASS · `engine verify` 4/4 · 19 维不变 | **ENG 自捕自修（已办，无需裁定）**——属同笔已授权 bump 内「记录新板 `board_sha16`」的正确形式 |

---

## 附录 B（inc115 追加，2026-09-19）：**#6 代价勘误** —— `(i-a)` 干跑实测「必要但不充分」

> 证据件：`K2-P4-U03-IA-DRYRUN-EVIDENCE-v1.md` **`004c48e3b187ce54`**（纯干跑，未施载体；`/tmp/opencode/arc_r1/`）。工具 = 在册同一 W-8 器 `75404d706413d546`。

| 事实 | 基线 `d67c0f04` | **(i-a) 干跑** |
|---|---|---|
| W-8 电气级审计（喂 `lib_electrical_level`） | `identical 49 · diff 5 · name_set_only 0 · no_link 4` | **`51 · 2 · 1 · 4`** |
| diff refs | `C85 J3 L1 U1 U6` | **`C85 J3 U1`** |

- **量化类归零**：`L1`·`U6`·（`U1` 的 48 处坐标）—— 分量差 **x=164 + y=52 = 216**（= 根因件 `94d259bf` 逐数），max\|Δ\| **0.5 µm**；受影响 pad = `L1`2·`U1`48·`U6`166。
- **`:319`（原点）对现行输入 = no-op（0/54 变）** ⇒ **有效最小补丁 = 2 处**（`:339`·`:345`）；`(i-a)` 与 `(i-a′)` **全读数等价**（变体选择不影响结论）。
- **残余 3 项非量化**：`C85`(2/2)·`J3`(38/38) = pad `rot` 板 0 vs 库 180（矩形自对称；`rel_geom_same=True`）· `U1` = 库侧 **无号 `F.Paste`** pad（无铜层；生成器 `load_mod_pads()` 明文跳过，登记「D 待裁」）。
- ⇒ **`lib_electrical_level` 期望 `n_electrical_diff==0 ∧ n_pad_name_set_only==0` 未被 (i-a) 满足**。选项 ① 需**加挂** (A) 扩生成器发射面（pad `rot` + 无号 `F.Paste`）或 (B) 判据侧具名「矩形 pad 0≡180」+「无号 `F.Paste` 非电气」（rev bump + 签认）；原选项 ③「判据侧具名量化容差」**范围偏窄**（量化已归零，无容差可具名）。
