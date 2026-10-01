# K2 · **P5 交付记录**（受审板 `a14610e0542e6314`）· **由构建器生成**（勿手改）· 2026-10-01

> 依据：#K2-36（P4 关门=通过 · P5 放行=批准）+ owner #14③。机读锚见包内 `MANIFEST.json`；本件为索引/记录，随构建刷新。

## 0. 一句话
`k2/pm_gate/artifacts/k2_v4/L6/jlc_package_m7t6r2/`（**60 件 + `MANIFEST.json`**）
· `MANIFEST.json` sha256 **`e3d177db635f6bc621768e4a1763e11ea2a949fc438353f76f50ce4e1c54782c`**
· DFM 对 JLC HDI 通道 **16 PASS / 1 ACCEPT / 0 FAIL**
· N-01 平面层 4/4 `G36>0` · 钻孔 726 孔 · kicad-cli 10.0.5
· 交付封装 `L6/DELIVERY_m7t6r2/k2_v4_8L.m7t6r2_gerber_package.tar.gz`（见其 README/SHA256SUMS）

## 1. 交付物
`01_gerber_rs274x/`（8 铜层 + 阻焊 F/B + 丝印 F/B + 边框 + `.gbrjob`）· `02_drill_excellon/`（Excellon **含 HDI 盲埋孔分对** + drill map + report）·
`03_stackup/`（JLC08161H 叠层图 · HDI 阶数图）· `04_impedance/`（阻抗表 as-built 复验）· `05_layer_sequence.txt` ·
`06_rulings/`（L2 裁定副本 parity=真 · `jlc_dfm_hdi_m7t6.{json,md}`）· `07_verify/`（**9 件验证**）· `DISCLOSURE.md` · `ORDER_NOTES.md` · `MANIFEST.json`

## 2. 锚
受审板 `k2_v4_8L.m7t6.kicad_pcb` **`a14610e0542e6314`** · pro `e7e704ae8a4715b8` · SPEC rev-54 `f3a48b866983c8db` ·
判据 **rev=6（COUNTERSIGNED）**：`727d0995…`/`1937a40a…`/`eb3da49f…`（ENG 只读）· 冻结四源未动（见 `07_verify/anchor_selfcheck.json`）。

## 3. DFM（对 JLC HDI 通道）
**16 PASS / 1 ACCEPT / 0 FAIL**（逐项 `06_rulings/jlc_dfm_hdi_m7t6.md`）。
ACCEPT（1 项）= 阻焊坝 9 处 <0.09mm → `ACCEPT_L2_WITH_FAB_REVIEW`（承 CO-147 R3）；**修法已实证** `pad_to_mask_clearance` 0.05→0.02mm ⇒ 9→0、无副作用（`07_verify/mask_accept_fix_proof.json`）。

## 4. 验证（包内 `07_verify/`，全部 fail-closed 或二值）
| 项 | 结果 |
|---|---|
| N-01 平面铜 | 平面层 **4/4 `G36>0`**（In1=1 · In3=1 · In4=9 · In6=1）；4 信号层无铺铜区 = 设计事实 |
| 钻孔 ↔ 板对账 | 726 = vias 716 + PTH 6 + NPTH 4；**逐对精确相符**（all_match=True） |
| Gerber 外接框 vs 边框 | 边框 **120.0×46.0mm**；**铜层 8/8 在框内**（all=True） |
| 孔径一致性 | 各铜层走线宽度 ⊆ 该层圆孔径集 ⇒ **all=True**（板最小线宽 0.16mm） |
| 重铺不变性 | 与 `--check-zones` 导出 **14/14 逐字节同** ⇒ 存盘 fill 即最新 |
| 丝印越界 | 3 处（max 2.877mm）；**铜层越界 0** |
| 幂等 | 连跑两次 `MANIFEST.json` 逐字节同（构建器：清目录→导出→规范化→验证→MANIFEST→封装） |

## 5. 具名披露（`DISCLOSURE.md`）
170 条 warning 全量 9 类（不缩口径）· OUT #5 族 + `U-03` 残项 · `F-9` 走廊口径（owner 另案）· `L-1` C4（28 件仅板来源）· 无判据类根闭 5 条 ·
**P5 新项**：阻焊坝 9 处 ACCEPT（附证明）· F.Cu 最紧耦合段 0.2825mm（−4.24%，阻抗仍 ±10%）· B.Cu 无 as-built 耦合 run · **正面丝印 4 处越框** · 重铺不变性已验证。

## 6. 待监理（ENG 不代判）
① 阻焊坝 9 处 ACCEPT 是否接受；② F.Cu 名义窗 −4.24% 是否接受；③ 「23 条恒定 warning」切分对账（库内 170/9 类）；④ 正面丝印 4 处越框是否需另开 rev。

## 7. 复现
```
PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p5_jlc_package_m7t6r2_v1.py
```

## 8. 边界
未改冻结四源/判据/生成器/SPEC/原理图/板 · 未派 WORKER · 无下单·报价·交期（商务）· 临时仅 `/tmp/opencode` · 未写 `.omo/supervision/**`。
