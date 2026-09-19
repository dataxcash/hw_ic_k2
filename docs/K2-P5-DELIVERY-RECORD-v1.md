# K2 · **P5 交付记录**（受审板 `l7 c5a7df90aadb66e0`）· v1 · 2026-09-20

> 依据：#K2-36（**P4 关门=通过 · P5 放行=批准**）+ owner **#14③**（完工定义 = 可制造 Gerber 包）。
> 本件 = **交付索引/记录**（人读）；机读锚见包内 `MANIFEST.json`。性质：只出交付物，未改任何载体。

## 0. 一句话
交付包 = **`k2/pm_gate/artifacts/k2_v4/L6/jlc_package/`**（**52 件 + `MANIFEST.json`**）
· `MANIFEST.json` sha256 **`96882cc7c4f0941e4e468ead54641ad8f92f60e299eae1cccfc098e26f01f07d`**
· DFM 对 JLC HDI 通道 **16 PASS / 1 ACCEPT / 0 FAIL**
· N-01 收口（平面层 4/4 `G36>0`）· 交付封装 `L6/DELIVERY/k2_v4_8L.l7_gerber_package.tar.gz` sha256 `7b2ebbc062d1eab54934ef272653cdddece6b18a1ac246fdba41bd02a4638dd2`（422,383 B）

## 1. 交付物
| 目录 | 内容 |
|---|---|
| `01_gerber_rs274x/` | **8 铜层**（F/In1..In6/B）+ 阻焊 F/B + 丝印 F/B + 边框 + **`.gbrjob`**（14 件） |
| `02_drill_excellon/` | Excellon **含 HDI 盲埋孔分对**（7 `.drl`）+ 7 drill-map SVG + `drill_report.txt` |
| `03_stackup/` | `JLC08161H_stackup.svg`（**由 SPEC rev-52 确定性绘制**）· `HDI_stage_diagram.svg`（l7 as-built） |
| `04_impedance/` | `impedance_table.{json,md}`（冻结 CO-146 两模型 + **l7 as-built 耦合 run 复验**） |
| `05_layer_sequence.txt` | 层序 + 层角色 |
| `06_rulings/` | L2 裁定副本（逐字节 parity=真）· `jlc_dfm_hdi_l7.{json,md}` · `dfm_raw_readings.json` |
| `07_verify/` | `n01_g36_census` · `drill_census` · `drill_board_xcheck` · `gerber_extents` · `silk_overhang` · `zone_refill_invariance` · `mask_accept_fix_proof` · `anchor_selfcheck` |
| `DISCLOSURE.md` / `ORDER_NOTES.md` | 具名披露 / 制造备注（JLC HDI 通道） |

## 2. 锚
- 受审板 `hw/k2_v4_8L.l7.kicad_pcb` **`c5a7df90aadb66e0`** · pro `33b4eb6cae8359a9` · SPEC rev-52 `42f8485ee4d6b566`
- 判据 **rev=3（COUNTERSIGNED）**：`eb244d811ad7859b` / `1937a40ae68bc288` / `e2b49fdd3aec0283`（ENG 只读）
- 冻结四源未动：`l4 d4e81f647be7f980` · 源板 `fb07d25ac426ff84` · 真源 `dd794c54f7ce7417`
- 闭环表 52 根闭 / 5 OUT / 2 未闭（`F-9` owner 另案不阻 · `N-01` 本包收口）

## 3. DFM（对 JLC HDI 通道 · 机器实测）
**16 PASS / 1 ACCEPT / 0 FAIL**（逐项见 `06_rulings/jlc_dfm_hdi_l7.md`）
- 关键读数：最小线宽 0.16mm · 线距 JLC 限违规 0 · 孔 0.2mm/盘 0.35mm/环 0.075mm · 孔到孔 0.25mm · 铜到边违规 0 · 板 120.1×46.1mm · 8 层 · 1.6mm。
- **ACCEPT（1 项）**：阻焊坝 9 处 < 0.09mm → `ACCEPT_L2_WITH_FAB_REVIEW`（承 CO-147 R3）；**修法已实证** = `pad_to_mask_clearance` 0.05→0.02mm ⇒ 缺口 **9→0**、无副作用（`07_verify/mask_accept_fix_proof.json`）；属改板 ⇒ 另开 rev。

## 4. 验证（均包内 07_verify/，可复现）
| 项 | 结果 |
|---|---|
| N-01 平面铜 | 平面层 **4/4 `G36>0`**（In1=1 · In3=1 · In4=9 · In6=1）；4 信号层无铺铜区 = 设计事实 |
| 钻孔 ↔ 板对账（fail-closed） | **749 = vias 729 + PTH 16 + NPTH 4**，**逐对精确相符**（通孔 301 · F-In1 168 · F-In2 128 · F-In4 4 · F-In5 19 · In5-B 37 · In2-In5 92） |
| Gerber 外接框 vs 边框 | 边框 **120.0×46.0mm**；**铜层 8/8 在框内** |
| 重铺不变性 | 与 `--check-zones` 导出 **14/14 逐字节同** ⇒ 存盘 fill 即最新 |
| 幂等 | 连跑两次 `MANIFEST.json` 与 tarball sha 逐字节同 |
| 锚自检 | 见 `07_verify/anchor_selfcheck.json` |

## 5. 具名披露（`DISCLOSURE.md`）
167 条 warning 全量 9 类（**不缩口径**）· OUT #5 族（`U-01/U-02/M-15/F-11/N-07` + `U-03` 残项）· `F-9` 走廊口径（owner 另案）·
`L-1` 具名接受 C4（28 件仅板来源）· 无判据类根闭 5 条 · **P5 新项**：阻焊坝 9 处 ACCEPT（附证明）· F.Cu 最紧耦合段 −4.24%（阻抗仍 ±10%）·
B.Cu 无 as-built 耦合 run（SPEC 对称声明）· **正面丝印 4 处越框**（H4/R41/D2/C87，max +1.848mm；铜层越界 0）· 重铺不变性已验证。

## 6. 待监理（ENG 不代判）
1. 阻焊坝 9 处 **ACCEPT** 是否接受（附确定性修法证明）；
2. **F.Cu 0.2825mm** < 名义窗下界 0.295mm（−4.24%）是否接受（阻抗仍落 ±10%）；
3. 「**23 条恒定 warning**」切分对账（库内为 167/9 类，本包按全量披露）；
4. 正面丝印 4 处越框（不影响制造）——是否需另开 rev 修。

## 7. 复现
```
PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p5_jlc_package_l7_v1.py
```
（构建器：清理 → 导出（/tmp 副本）→ 时间戳规范化 → 全量验证 → MANIFEST → DELIVERY 封装；**幂等**）

## 8. 边界
未改冻结四源/判据/生成器/SPEC/原理图/板 · 未派 WORKER · 无下单·报价·交期（商务，非 ENG）· 临时仅 `/tmp/opencode` · 未写 `.omo/supervision/**`。
