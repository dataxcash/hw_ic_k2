# MANIFEST · **l9 P4 标准调用册**（canonical 19 · 判据 rev=6 在岗）· ENG R410

> 触发：R270《R4 复测闸就绪度 v2》§一 项1（**19 维判定器 · l9 同口径重跑**）· 项4（ref_plane_continuity @l9）· 项9（平面/铺铜/钻孔 @l9）。
> 代理：本机 **KiCad 10.0.5 复原可用**（`AppDir/bin/kicad-cli` 10.0.5 + `AppDir/bin/python3.11` pcbnew 10.0.5）⇒ 先前「本机无 pcbnew ⇒ 未做全量 LoadBoard/DRC」（R376 自陈）之缺口**本轮补齐**。
> 边界：**只读取证件**。未改受审板/pro/生成器/SPEC/真源/`criteria/**`/冻结件/`_shared`；未派 WORKER；临时仅 `/tmp/opencode`；未烙板。

## 锚
| 项 | 值 |
|---|---|
| 受审板 | `k2/hw/k2_v4_8L.l9.kicad_pcb` **`77aaa63fe016b450`** |
| pro | `k2/hw/k2_v4_8L.l8.kicad_pro` **`c009058005829f09`**（**如实标注**：l9 落件**未含**同批 pro；搬迁不改规则 ⇒ 沿用 l8 pro。此项属口径缺口，见 R410 §四） |
| SPEC | `L3/SPEC_k2_v4.spec-rev-55.json` **`964101b19015f6d7`**（**声明性回填** · #K2-137 §二(甲)） |
| 网表 | `k2/hw/data/k2_sch.errata-3.yaml` **`5dc7b82a901d11c8`** |
| 判据 | **rev=6 COUNTERSIGNED**（`manifest.k2.yaml 727d09953cf9bd78` · `adjudicate.py 1937a40ae68bc288` · `CHANGELOG eb3da49f2ad97e37`）—— 本轮 ENG 独立复算，与 handoff 逐字节吻合 |
| 冻结四源 | `d4e81f647be7f980` / `fb07d25ac426ff84` / `dd794c54f7ce7417` / `0a459839e15960b8`（4/4 未动） |

## 结论（先给）
- **标准调用 verdict @l9 = `16 OK / 3 FAIL`**（l8 同仪器 = `19 OK / 0 FAIL`）⇒ **l9 未过 P4 标准调用门**。
- 三条 FAIL 全部落在 **#K2-137 已准之「项2 落搬迁」在 l9 上新生/改动的铜**（`DS320_STRAP_B_ADDR1_7-0` · `DS320_STRAP_B_ADDR0_15-8` · `I2C1_SDA`）；**l8（搬迁前）为 0 error**。
- ⇒ **结论句**：l9 之搬迁**尚未成为合格落地**（DRC error=59、含短路/交叉；且未回填铺铜）。

## 一、19 维读数（`verdict_19dim_rev6_board_l9_77aaa63f.json`）
| 维 | l9 判 | l9 读数 | l8 对照 |
|---|---|---|---|
| **non45_segments** | **FAIL** | **11/5456** | 0/5180 |
| **drc_errors** | **FAIL** | **error=59**（违规总 233 · unconnected 0）：`clearance 21` · `shorting_items 19` · `hole_clearance 13` · `tracks_crossing 6` | error=0（170 全 warning） |
| **density_and_clearance** | **FAIL** | 最小铜间距 **`None`**（<0.100）；密度峰 7（≤8）· 横带 0.07586 · 孔环 0.075 · pad 到边 0.38 | `[0.100, 0.105]` ⇒ OK |
| zone_filled | OK | 铜区 10/10（keepout 8 另计） | OK |
| drill_count | OK | **NPTH=4 · PTH=16** | OK |
| ref_plane_continuity | OK | `non_antipad_gap = 0.0 mm²` @R=0.5（antipad 20.9552 / split 0.0 / keepout 0.0062） | 0.0 mm² |
| pads_within_outline | OK | AABB 0 · 接口件 0 · 真框多边形 0（676 pad，inset 0.3） | OK |
| lib_electrical_level | OK | 电气级差异 **0**（原 2，B 口径豁免 2） | OK |
| unconnected_zero | OK | unconnected_items = 0 | OK |
| 其余 7 维 | OK | `device_has_pads` · `rule_severity_manifest` · `net_declared_realized` · `pin_map_complete` · `refdes_sets_equal` · `pipeline_present` · `drc_warning_dispositions` · `fp_lib_table_present` · `keepout_active` · `verdict_schema` | OK |

## 二、最小铜间距（item9 之核心证据 · DRC bracket）
| 阈值 T | l9 违规 | l8 违规（同工具对照跑） |
|---|---|---|
| 0.100 | **16** | **0** |
| 0.105 | 22 | 6 |
| 0.110 | 22 | 6 |
| 0.120 | 26 | 9 |
| 0.150 | 37 | 16 |
| 0.200 | 259 | 233 |
| 实达区间 | **`[None, 0.100]`** | `[0.100, 0.105]` |

最紧三例（l9）：`ADDR1_7-0(In2) ↔ GND via` **0.0390mm** · `I2C1_SDA(B.Cu) ↔ PCIE_DN_OUT7_P_MCIO via` **0.0405mm** · `ADDR1_15-8(In2) ↔ ADDR1_7-0(In2)` **0.0415mm**。
（l8 对照最紧例：`R28 pad1 [SWCLK_BOOT0] ↔ NRST(F.Cu) track`，T=0.100 无违规。）

## 三、铺铜回填归因（具名 · R410 §三）
对 l9 **副本**（`/tmp/opencode/k2r410/refill/l9_refilled.kicad_pcb`，pcbnew `ZONE_FILLER` 填 18 区）复跑 DRC：

| 类型 | l9 原样 | l9 回填后 | 判 |
|---|---|---|---|
| clearance | 21 | 14 | 7 属陈旧铺铜假违例 |
| hole_clearance | 13 | 5 | 8 属陈旧铺铜假违例 |
| shorting_items | 19 | 16 | 3 属陈旧铺铜假违例 |
| tracks_crossing | 6 | 3 | 3 属陈旧铺铜假违例 |
| **error 合计** | **59** | **38** | **21 = 陈旧铺铜（落搬迁后未回填）** |

⇒ **38 处为真几何冲突**（交叉/短路/孔间距），与铺铜无关。**注意**：回填件仅落 `/tmp`，**未入库**（#K2-142 §四 禁烙板在效）。

## 四、缺陷归因（l8 → l9 差分 census · 只读文本解析）
| 对象 | l8 | l9 | Δ |
|---|---|---|---|
| 段 总数 | 5180 | **5456** | +276 |
| `PERSTA#` In5 | 59 | **324** | **+265** |
| `DS320_STRAP_B_ADDR0_15-8` B.Cu / F.Cu | 24 / 7 | 35 / 14 | +11 / +7 |
| `DS320_STRAP_B_ADDR1_7-0` In5 / In2 | 11 / 18 | **0** / 22 | −11 / +4 |
| `I2C1_SDA` B.Cu / In5 | 103 / 47 | 105 / 45 | +2 / −2 |
| 孔 总数 | 742 | 740 | −2 |
| 非 45° 段 | 0 | **11** | 全在两条 strap 网：`ADDR1_7-0(In2)`×4（4.58°/176.32°/50.48°/138.81°）· `ADDR0_15-8`（F.Cu×3 · B.Cu×4） |

**真冲突三簇**（回填后 38 error 之去向）：
1. `DS320_STRAP_B_ADDR1_7-0`（In2）**穿越/短路** `PCIE_UP0_N/1_N/2_P/3_P/4_N/5_N`（In2 走线 + `F.Cu→In2` 盲孔）及 `DS320_STRAP_B_ADDR1_15-8`（In2）—— `tracks_crossing` + `shorting_items`；
2. `I2C1_SDA` via（F.Cu–B.Cu）+ B.Cu stub **短路** `PCIE_DN_OUT7_P_MCIO`（B.Cu）及 U6 pad `BT29`；
3. `DS320_STRAP_B_ADDR0_15-8`（B.Cu/F.Cu）spacing vs `PCIE_DN_OUT7_N_MCIO`（B.Cu）· `P3V3` via（F.Cu→In4 盲孔）· `GND` via。

## 五、人类工程语义（第十三条）
**「施工队照这张图能不能直接连？」→ 不能。** 3 簇**真短路/交叉**（strap ↔ PCIE_UP In2 束 · I2C1_SDA via ↔ DN_OUT7 B.Cu · strap0 ↔ P3V3/GND 过孔）+ 21 处**陈旧铺铜**假短路 + 11 段非 45°。⇒ **图纸层缺图，且板层有短路缺陷**。

## 六、可施工性（⑧ 字段）
| # | 动作 | 对象 | 审批 |
|---|---|---|---|
| 1 | **回填铺铜**（落搬迁后必做） | 全板 18 区（ZONE_FILLER） | 完成 #K2-137 项2 落地 |
| 2 | 移/改走 `ADDR1_7-0` In2（4 段 22.0742/9.7712/13.8474/15.5721mm） | 避 `PCIE_UP*` In2 束与盲孔 | 监理（L2）· **#K2-142 §四 禁烙板在效** ⇒ 需监理放行再落 |
| 3 | 移 `I2C1_SDA` via + 改其 B.Cu stub | 避 `DN_OUT7_P` B.Cu 与 U6.BT29 | 同上 |
| 4 | 移 `ADDR0_15-8` F/B.Cu stub | 避 `DN_OUT7_N` · `P3V3`/`GND` via | 同上 |
| 5 | 11 段 **45° 化** | 上述两条 strap 网 | 同上 |

## 八、件表（sha16）
| 件 | sha16 | bytes |
|---|---|---|
| `density_board_l9_77aaa63f.json` | `eceb795a73ef81b2` | 5,750 |
| `drc_raw_board_l9_77aaa63f.json` | `35359bac5f470364` | 150,190 |
| `measure_raw_board_l9_77aaa63f.json` | `b3b4c17fd991845b` | 2,255,848 |
| `min_clearance_drc_board_l9_77aaa63f.json` | `e8b425ffc34eb96f` | 1,587 |
| `min_clearance_drc_control_board_l8_7a5c8991.json` | `944c4add6a8bf518` | 1,528 |
| `pads_within_outline_board_l9_77aaa63f.json` | `c3da758fb71a7dde` | 165,139 |
| `ref_plane_continuity_board_l9_77aaa63f.json` | `9b3c7340c9c36953` | 1,909,414 |
| `refplane_nonantipad_board_l9_77aaa63f.json` | `baf8510d620a9143` | 3,084 |
| `verdict_19dim_rev6_board_l9_77aaa63f.json` | `a5686489ea54b5f8` | 3,709 |
| `w8_audit_board_l9_77aaa63f.json` | `d5058364372522f8` | 16,842 |

## 复跑命令（逐条）
```bash
A=/home/fila/jqdDev_2025/ic_hw/AppDir; B=k2/hw/k2_v4_8L.l9.kicad_pcb; O=/tmp/opencode/k2r410
$A/bin/python3.11 k2/tools/k2_w8_footprint_audit_v1.py --board $B --proj-lib k2/hw/lib --out-json $O/w8_l9.json --out-md $O/w8_l9.md
$A/bin/python3.11 k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board $B --json $O/pads_outline_l9.json
$A/bin/python3.11 k2/docs/drafts/p4-j8-v3-measurement-v1/measure_ref_plane_continuity.py --board $B --json $O/v3_plane_l9.json
$A/bin/python3.11 k2/docs/drafts/p4-refplane-nonantipad-v1/measure_non_antipad_gap.py --board $B --spec k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-55.json --json $O/refplane_nonantipad_l9.json
$A/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_density_and_clearance.py --board $B --json $O/density_l9.json
$A/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board $B --pro k2/hw/k2_v4_8L.l8.kicad_pro --kicad-cli $A/bin/kicad-cli --work-dir $O/minclr_wd --json $O/minclr_l9.json
python3 criteria/adjudicate.py --project k2 --board $B --pro k2/hw/k2_v4_8L.l8.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-3.yaml --sch-dir k2/hw/sch --root . \
  --drc-cli $A/bin/kicad-cli --drc-work-dir $O/drc_wd \
  --w8-audit-json $O/w8_l9.json --pads-outline-json $O/pads_outline_l9.json \
  --v3-plane-json $O/v3_plane_l9.json --refplane-gap-json $O/refplane_nonantipad_l9.json \
  --density-json $O/density_l9.json --min-clearance-json $O/minclr_l9.json
```

## 仪器 sha16（工具即仪器 · 逐件在册）
`k2_w8_footprint_audit_v1.py 75404d706413d546` · `measure_pads_within_outline.py 1b177638cde3cd55` · `measure_ref_plane_continuity.py 7a3cc545c1447b04` · `measure_density_and_clearance.py ff763e6865bac843` · `measure_min_clearance_drc.py 4386efde7451bf8e` · `measure_non_antipad_gap.py 2f5591352c5974d3`

---
—— ENG（ARCHER）· 2026-09-22 · 只读取证件 · 未烙板 · owner 闸口 0
