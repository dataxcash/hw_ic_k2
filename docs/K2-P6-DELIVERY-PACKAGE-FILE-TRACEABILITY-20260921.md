# K2 · P6 §8.2② —— 交付包 **53 件逐件用途/追溯表** + 十项覆盖核对

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/DELIVERY_PACKAGE_FILE_TRACEABILITY_20260921_v1.json`（sha16 `7f0adeb70af167f0`）
- 性质：**只读**。仅读 `L6/jlc_package/MANIFEST.json` + 包内目录；**不重出包、不动交付锚**；不新增判据维/检查齿。
- 包锚（未动）：`MANIFEST.json` `6ee7495de61f749f` · `n_files=53` · `revision=rev-52` · 板 `l7 c5a7df90…` · DFM `16 PASS / 1 ACCEPT / 0 FAIL`
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
交付包 53 件**逐件归类到 16 个类别**，每件给出「用途 → 判据/验证出处」；owner **#14③ 十项全部覆盖**（8 铜层 / 阻焊 / 丝印 / 边框 / job / Excellon 含 6 个 HDI 层对 / 叠层图 / 阻抗表 / MANIFEST）；并**独立重算 53/53 sha256 = 盘上一致**、盘上**无 MANIFEST 之外多余件**。

## 1. 类别汇总（53 件）
| 类别 | 件数 | 用途 | 追溯出处 |
|---|---|---|---|
| `copper` 铜层图形 | 8 | F/In1–In6/B 共 **8 铜层** | 图元保真审计（draw/via 逐层相等）· 十项'8 铜层' |
| `drill` Excellon 钻孔 | 7 | 通孔 `l7.drl` + **6 个盲/埋层对**（front-in1/in2/in4/in5 · in2-in5 · back-in5） | 钻孔坐标级保真 749/749 + `drill_board_xcheck` · 十项'Excellon 含 HDI' |
| `drill-map` 钻孔图 | 7 | 分层对钻孔图（含总图） | 钻孔保真审计 |
| `drill-report` | 1 | Excellon 工具/孔档报表 | `drill_census.json` |
| `mask` 阻焊 | 2 | F/B 阻焊图形 | DFM 阻焊 + 图元保真 · 十项'阻焊' |
| `silk` 丝印 | 2 | F/B 丝印图形 | `silk_overhang.json` + 图元保真 · 十项'丝印' |
| `edge` 板框 | 1 | Edge.Cuts | DFM 外形 + 图元保真 · 十项'边框' |
| `job` | 1 | Gerber job 元数据（叠层/Finish/清单） | DFM job 一致性审计 · 十项'job' |
| `stackup` 叠层图 | 2 | HDI 阶数图 + JLC08161H 叠层 | 十项'叠层图' · N-1 B-1 叠层口径 |
| `impedance` 阻抗表 | 2 | `impedance_table.json` + `.md` | 十项'阻抗表' · 阻抗判据 85Ω±10% |
| `layer-seq` | 1 | 层序列 | SPEC `layer_plan` |
| `ruling` 裁定留档 | 4 | 工艺冻结A · 过孔通道域 · U6 热机械 | owner #14① + L2 裁定向导 |
| `dfm-report` | 3 | JLC HDI DFM 读数/报告 + 副本一致性 | DFM 可独立复算审计 |
| `parity` | 1 | 包内副本一致性 | 锚完整性核验 |
| `verify` 自检证据 | 9 | 锚自检 · 钻孔↔板对账 · 孔径普查 · 图元范围 · 阻焊修法留证 · G36 普查 · 丝印越框 · 铺铜重填不变性 | 交付五面核验的证据基座 |
| `doc` 随单件 | 2 | `DISCLOSURE.md`（§5b-1 阻焊坝 / §5b-2 最紧段）· `ORDER_NOTES.md` | 十项'随单件' · N-1 |

## 2. owner #14③ 十项覆盖（机械核对）
| 项 | 命中 | 判定 |
|---|---|---|
| 8 铜层 | 8（F_Cu + In1–In6 + B_Cu） | ✅ |
| 阻焊 | 2（F/B_Mask） | ✅ |
| 丝印 | 2（F/B_Silkscreen） | ✅ |
| 边框 | 1（Edge_Cuts） | ✅ |
| job | 1（`-job.gbrjob`） | ✅ |
| Excellon 钻孔 | 7（`*.drl`） | ✅ |
| HDI 盲埋孔（层对） | 6（† 见下） | ✅ |
| 叠层图 | 2 | ✅ |
| 阻抗表 | 2 | ✅ |
| MANIFEST | 1 | ✅ |

† 层对 = `front-in1`(L1-2) · `front-in2`(L1-3) · `front-in4`(L1-5) · `front-in5`(L1-6) · `in2-in5`(L3-6) · `back-in5`(L8-6)（与钻孔保真审计的 6 个层对档一一对应）。

## 3. 独立重算（本件现场）
- **53/53 件 sha256 与盘上逐件一致**（`missing=0` · `hash_mismatch=0`）。
- 盘上文件数 = 54（53 件 + `MANIFEST.json`），**无 MANIFEST 之外的多余件**。
- ⇒ 与既有「锚完整（53/53 + tarball 等价）」读数**独立相符**。

## 4. 边界
只读；未改包内任何件、未动 `MANIFEST.json`/tarball 锚、未动 `criteria/`。本件为**文档化追溯**，不新增判据维（owner ②）。
