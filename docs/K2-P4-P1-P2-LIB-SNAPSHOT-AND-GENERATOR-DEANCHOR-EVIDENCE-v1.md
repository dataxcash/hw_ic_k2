# K2 · P4 · **#K2-26 唯一工作包（P1 库快照重建 + P2 生成器去锚板）· 证据件 v1**

> 依据：监理 **#K2-26 §三**（聚焦令：本轮只做 `P1+P2` 两件耦合；§四 其余全部排队禁动）。
> 判据锚 rev=1（MATCH）· 冻结四源未动 · `criteria/` 只读 · 未派 WORKER · 临时仅 `/tmp/opencode`。

## 0. 一句话结论

**P1 完成（库快照按「以板为准」重建并落库：20 → 36 文件 = 24 件快照 mod + 12 件保留旧件；`J3/J4` pad 名集 = 板；两次连跑同 sha）**；
**P2 完成（生成器 ref 清单 ← 真源 YAML、pad 几何 ← 库快照，**源码级零板依赖**：产物 `refs 54/54 == 真源`、带号 pad `672/672 == 受审板` 且逐件名集 **0 差异**、两次连跑逐字节同）**。
**具名偏差 1 项**：验收文字「库件数 `20 → 27`」在本轮**不可达** —— `27` 是 **⑥+⑦ 复合**后的快照件数（courtyard 属封装内容），而 **⑥ 被 §四 排队禁动**；`⑦` 单独 = **24**（见 §1.4，具名上报，不缩口径）。

---

## 1. P1 · 库快照重建（⑦「以板为准」，#K2-26 §3-1）

### 1.1 载体
| 件 | 前 | 后 |
|---|---|---|
| 工具 `k2/tools/k2_p4_lib_snapshot_v1.py` | `91c9f5a1138a9825` | **`afa9be4bf599626b`**（新增 `--lib-only`：只落库、不动板；见 §1.5） |
| 库 `k2/hw/lib/ForgeOS.pretty` | **20 文件**（dir digest `efcd…` 见 §1.3 口径：`3a7e253891635107`） | **36 文件**（24 快照 mod + 12 旧件保留） |
| `k2/hw/fp-lib-table` | `d731638859be9a08` | **未改**（已指向 `${KIPRJMOD}/lib/ForgeOS.pretty` = 新库） |
| 受审板 `k2/hw/k2_v4_8L.l5.kicad_pcb` | `dae8dc8d48ff5b81` | **未改**（`--lib-only`，板/pro 逐字节不动） |

### 1.2 出处（逐类具名）
- **来源 = 受审板 `dae8dc8d48ff5b81` 的 58 颗 footprint 本体**（`pcbnew FootprintSave` 原样落库，`Reference`/`Value` 归一为 `REF**`/件名，uuid 原样）——即 **KiCad 板内嵌 footprint = 具名出处**（`Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`（`U2`）等由板内嵌落库，非外部下载）。
- 分组口径 = 工具的 **land pattern 指纹**（去 `Reference`/`Value` 块 + 归一 uuid）⇒ 同件名但 land pattern 不同者**各自成件**（`C_0402_1005Metric__1/__2/__3`、`R_0603_1608Metric__1/__2`、`R_0402_1005Metric__1/__2`、`MCIO_4i_SFF-1016_RASide__1/__2`）。
- `J3/J4`：库件 pad 名集 = **`A1..A19/B1..B19`（38）** = 板（原库件 `1..38` 已消除）。

### 1.3 机判（原始输出）
```
$ AppDir/usr/bin/python3.11 k2/tools/k2_p4_lib_snapshot_v1.py --board k2/hw/k2_v4_8L.l5.kicad_pcb \
    --pro k2/hw/k2_v4_8L.l5.kicad_pro --kicad-cli AppDir/bin/kicad-cli --work-dir <W> --apply --lib-only --confirm-repo-write
before: {"warning:lib_footprint_mismatch": 34, "warning:missing_courtyard": 39}
after : {"warning:missing_courtyard": 39}
snapshot: fps=58 land_patterns=24 mods=24
candidate: <W>/k2_v4_8L.l5.libsnap.kicad_pcb sha16 559cb00ca974f1d9 | text_diff_lines 1892
placement_equiv: 58 fps, mismatches 0
gates: {"passed": true, "failures": []}
```
- **快照 24 件 digest（两次连跑同）** = `efcd88b35d6d846c`（dry-run#1 与 apply#2 逐字节同）⇒ **「两次连跑 sha 同」PASS**。
- **落库后库目录 digest** = `078f7dc78d980696`（36 文件）；**8 件原地改写**（`DS320PR1601` `MCU_STM32G0_LQFP48` `OPTO_LTV356T` `PinHeader_1x02` `PinHeader_1x04` `SOIC8_FRU` `SOT23_BAT54C` `SlimSAS_x8_…`）+ **16 件新增**；**12 件旧件保留未删**（`MCIO_4i_…_RASide` 裸名 / `MCU_STM32G0_QFN32` / `OCuLink_SFF8612` / `PI3DBS16412` / `TLV61046_*`×2 / `TPD6E05U06_RVZ` / `TPS22919` / `TS3USB221A_UQFN10` / `USB3_TYPEA_90` / `USB_A_MUSBR` / `WQFN-64_10x5.5mm_P0.4mm`）——**删除须监理另裁**（工具纪律）。
- **板文本守恒闸**：本模式不写板 ⇒ 该闸**不适用**，实测值已登记（`board_text_gate={"applicable":false,"observed":"text_change_outside_footprint_header"}`）——**逐项登记、非静默丢弃**（该 `observed` 源于 inc87 用 pcbnew 重存板后的序列化差异，与库内容无关）。

### 1.4 ⚠ 具名偏差：验收「`20 → 27`」在本轮不可达
- `27` = **⑥+⑦ 复合**快照件数（`K2-P4-COMPOSED-CANDIDATE-6PLUS7-EVIDENCE-v1.md` §1：「库快照 27 件；较纯 ⑦ 的 24 件多 3 件 —— **补 CrtYd 后**同件名件的 land pattern 再分化」）。
- 本轮 **⑦-only = 24**；**⑥（L2 placement + CrtYd）被 #K2-26 §四 明令排队**，故 24 为**授权内可达上限**。
- **不缩口径声明（C-12）**：本件不宣称 27 已达成，也不把 24 记作 27；请监理裁 (a) 认可 ⑦-only=24 为本轮 P1 交付 / (b) 待 ⑥ 落件后由复合链重出 27。

### 1.5 工具改动的闸语义（不放松）
`--lib-only` 仅：①跳过写板；②在该模式下**不把「板文本守恒」计入 `bad`**（不写板 ⇒ 该闸不适用），并把实测值写入报告；**其余闸（`lib_footprint_mismatch`=0 / error=0 / unconnected=0 / 违规类型不增 / 铜几何集合 / 计数 / `placement_equiv`）一律照旧执行且本轮全过**。默认（不带 `--lib-only`）行为逐字节不变。

---

## 2. P2 · 生成器去锚板（#K2-26 §3-2）

### 2.1 改动（载体）
| 件 | 前 | 后 |
|---|---|---|
| `k2/tools/k2_gen_v5.py` | `796bd7a48947ec7c` | **`ef514bd3afac701f`** |
| `k2/hw/lib/ForgeOS.refmap.json`（新件） | — | **`5a58ce727826df6c`**（54 ref → 库件 mod + 冻结坐标锚点） |

- ① **ref 清单 ← 真源 YAML**：`K2_REFS = sorted(_derive_k2_refs_from_true_source(YAML_PATH))`（读 `project.yaml::nets_yaml` = errata-2 的 `sheets[].placements[]`；原「从锚板正则取 refdes」已删）。
- ② **pad 几何 ← 库快照**：`load_mod_pads(mod)` 读 `k2/hw/lib/ForgeOS.pretty/<mod>.kicad_mod`（**唯一 pad 源**）；库件缺失 / 缺号 ⇒ `fail-closed`。原「锚板 pad 几何 + `G_0402/G_0603/G_0805` 兜底几何」已删。
- ③ **去锚板**：`PCB_REF_PATH`、`parse_ref_pcb()`、`ref_anchors_cache`、`OLD_REF_MAP` **整体移除**；坐标取自 `ForgeOS.refmap.json::placement_anchor`（P2 阶段坐标锚点；**P3「链起点改真源构造」接管**）。

### 2.2 机判（#K2-26 §3-2 四项验收）
| # | 判据 | 实测 | 判 |
|---|---|---|---|
| ① | 复跑不再报 `ref: ['C89']` | 原 `❌ 写盘阻断 … ref: ['C89']` → **消失**；自检 `6/6 PASS` | **PASS** |
| ②a | 产物 refs == 真源 | 产物 **54** refs == 真源 `sheets[].placements` **54**；且板有图无/图有板无 **0/0** | **PASS** |
| ②b | pad 合计 == 受审板（逐件对账） | **带号口径 `672/672`，逐件 pad 名集差异 `0`**；原始块口径 生成器 `676` vs 板 `685` ⇒ **−9 具名**（= `U1` 9 枚**无号** `F.Paste` EP 阵列，非电气性；属 **D 带号口径待裁**项） | **PASS（差异具名）** |
| ③ | 源码级不读锚板 | `grep -n "PCB_REF_PATH\|parse_ref_pcb\|k2_v4\.kicad_pcb" k2/tools/k2_gen_v5.py` ⇒ **仅注释/输出路径**，**无任何板路径读取** | **PASS** |
| ④ | 两次连跑逐字节同 | run1/run2 `cmp` ⇒ PCB **IDENTICAL**、JSON **IDENTICAL**；sha16 **`d67c0f048f0d0423`**（两次同） | **PASS** |

原始输出（摘要）：
```
k2_gen_v5 自检结果 (6/6): S1 焊盘重叠 / S2 refdes 对齐 / S4 缺失器件 / S5 坐标范围 / S6 网表一致性 / S8 排针坐标冻结 全 PASS
  器件数: 54    pads 总数: 672    使用网名数: 100 (YAML nets 共 100)    NO_CONNECT pads: 128
  G10 输入层: keepout=8 copper=10 npth=4  (源=SPEC 输入层，不读板)
```
绝对几何对账（板 `dae8dc8d` vs 产物）：**54 件中 49 件 0 差异**；具名 3 类见 §4。

### 2.3 逐件对账（差异具名）
- 带号 pad **名集**：**54/54 全等**（`0` 差异）。
- 绝对 pad 几何（位置/尺寸/形状/钻径）：**49/54 全等**；余 5 件为 §4-③ 面别项。
- pad 朝向存储约定：`U6` 354 枚板存**绝对** 90°、mod 存**局部** 0°（方形 pad，物理等价；= W-8 v1 误报项，W-8 v2 放置帧归一后归零）。

---

## 3. 守恒闸（#K2-26 §三 尾）
| 检查 | 结果 |
|---|---|
| 冻结四源 sha | `d4e81f647be7f980` / `fb07d25ac426ff84` / `dd794c54f7ce7417` / `897e8bfde60e2cfe`+`7ce08757eff25557` **逐项不变** ✅ |
| 受审板 / pro | `dae8dc8d48ff5b81` / `35c8f34bde7ac00c` **未改** ✅ |
| 判定器（`--nets errata-2`，新基线） | **PASS 7 / FAIL 3**，FAIL 集 = `zone_filled` + `refdes_sets_equal` + `pipeline_present`（与 inc87 基线**逐项同名**）⇒ **集合不退化** ✅ |
| DRC（受审板，同名 pro，`--severity-all`） | **73 warning / 0 error / 0 unconnected** = `missing_courtyard` **39** + `lib_footprint_mismatch` **34**（与 inc87 逐项同）⇒ **DRC 下限未放松** ✅ |
| 非 45° | 受审板 **0/4720** ✅ |
| C-12 | 不宣称任何未闭项已消；§1.4/§4 差异**全部具名** ✅ |

---

## 4. 边界 + 具名差异/旁证（未处理）
**本件已改（均有 #K2-26 §三 授权）**：`k2/hw/lib/ForgeOS.pretty/**`（24 快照 mod 落库；8 改 + 16 增，12 旧件保留）· 新增 `k2/hw/lib/ForgeOS.refmap.json` · `k2/tools/k2_gen_v5.py` · `k2/tools/k2_p4_lib_snapshot_v1.py`（`--lib-only`）· 本证据件。
**未改**：受审板 / pro · 冻结四源 · SPEC 原件（rev-47/48/49/50）· 真源 yaml（`k2_sch.yaml`/`errata-1`/`errata-2`）· `criteria/**` · `_shared/**` · `k2/fp-lib-table` · 模板 · `pm_gate/**` · L5 旧交付包 · `.omo/supervision/**`；**未装 `k2/pipeline.yaml`**；**未出 Gerber**；**未动 §四 排队项（P3 / E-4 / E-3 / ⑥ / refplane）**；未派 WORKER；未新增检查齿。
**具名差异（3 类）**：
① **`U1` 9 枚无号 `F.Paste` EP 阵列**：生成器按**带号口径**不产出 ⇒ 原始块口径 `676 vs 685`；属 **D（`C3.U1.footprint_pads` 带号 49 vs 原始 58）** 待裁项，与 W-8/J-7b 同源。
② **库快照件数**：⑦-only **24** ≠ 验收文字 **27**（= ⑥+⑦；见 §1.4）。
③ **5 件排针面别**：`J6/J9/J11/J12/J13` 板 = **`B.Cu`**、产物 = **`F.Cu`**；其 pad 为 **THT 全层**（`*.Mask` + 全 Cu）⇒ **铜/电 0 差异**，面别属 **⑥ L2 placement**（已排队）。
**旁证**：`k2/hw/k2_v4_8L.l5.kicad_prl` 仍**未跟踪**（KiCad 本地 UI 态，刻意不入库）。

---

## 5. 复跑链（确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# P1 库快照（dry-run；期望 snapshot: fps=58 land_patterns=24 mods=24；digest efcd88b35d6d846c 两次同）
AppDir/usr/bin/python3.11 k2/tools/k2_p4_lib_snapshot_v1.py \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/p1
# P2 生成器（两次连跑须逐字节同；期望 器件数 54 / pads 672 / 自检 6/6 / G10 8-10-4）
K2_OUT_PCB=/tmp/opencode/p2a.kicad_pcb K2_OUT_JSON=/tmp/opencode/p2a.json python3 k2/tools/k2_gen_v5.py
K2_OUT_PCB=/tmp/opencode/p2b.kicad_pcb K2_OUT_JSON=/tmp/opencode/p2b.json python3 k2/tools/k2_gen_v5.py
cmp /tmp/opencode/p2a.kicad_pcb /tmp/opencode/p2b.kicad_pcb
# 判定器（新基线：errata-2；期望 PASS 7 / FAIL 3，FAIL=zone_filled/refdes_sets_equal/pipeline_present）
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
# DRC（同名 pro；期望 73 warning / 0 error / 0 unconnected）
AppDir/bin/kicad-cli pcb drc --severity-all -o /tmp/opencode/drc.rpt k2/hw/k2_v4_8L.l5.kicad_pcb
```
**fail-closed**：P4 未全绿不下单、不出交付 Gerber；P5 未开。

—— ENG（ARCHER）· 2026-09-18 · #K2-26 工作包（P1+P2）· 库快照 digest `efcd88b35d6d846c` · 生成器 `ef514bd3afac701f` · 产物 `d67c0f048f0d0423` · 受审板 `dae8dc8d48ff5b81`（未动）
