# k2_v4_8L.l4 Gerber 交付包（可制造版）

交付物（文件 + sha 清单）：

- `k2_v4_8L.l4_gerber_package.tar.gz` — 打样包整树（解包得 `jlc_package/`）。
  - sha256 `4aa083f5077eef11df96791c4a48126e69d2ef7abe176c38cf822441bac3c7b7`
  - 确定性打包（`--sort=name --owner=0 --group=0 --numeric-owner --mtime=1789367940`，`gzip -n`）：重打包 sha256 不变。
- `SHA256SUMS.txt` — 顶层 sha256 清单（包 + 板 + 冻结四源 + 判据/裁定/DFM 证据 + 生成器 + runner）。
- `jlc_package/MANIFEST.json` — **逐文件** sha256+bytes 清单（40 payload），位于交付包内。

包内容：

| 目录 | 件数 | 内容 |
|---|---|---|
| `01_gerber_rs274x/` | 14 | 8 铜层（F_Cu / In1..In6_Cu / B_Cu）+ F/B_Mask + F/B_Silkscreen + Edge_Cuts + job.gbrjob |
| `02_drill_excellon/` | 11 | 通孔 `.drl` + 4 类 HDI 盲埋孔分片（front-in2 / front-in5 / in2-in5 / back-in5）+ 4 map svg + drl_map + drill_report |
| `03_stackup/` | 2 | `JLC08161H_stackup.svg`、`HDI_stage_diagram.svg` |
| `04_impedance/` | 2 | `impedance_table.json/.md`（85Ω 差分 ±10%） |
| `05_layer_sequence.txt` | 1 | 8 层层序 |
| `06_rulings/` | 9 | 随包工艺/DFM 裁定与证据（A 冻结 HDI、DFM 逐项、热机械、过孔域） |
| `ORDER_NOTES.md` | 1 | 制造备注（通道 / 参数 / 参数清单） |
| `MANIFEST.json` | 1 | 逐文件 sha256 清单 |

工艺：JLC HDI 盲埋孔（阶数 ≥2），工艺冻结 = A（owner 裁定 DIR-14）。
DFM 对 JLC HDI 通道：**16 PASS + 1 ACCEPT + 0 FAIL**（`PASS_HDI`）。
非阻塞披露：阻焊 1 处 `R3.pad2 ↔ PCIE_UP3_N` 开窗缘↔邻铜 = 0.0695mm（< 0.09mm）⇒ `ACCEPT_L2_WITH_FAB_REVIEW`，随单提交板厂评审，不触铜几何。
兜底修法（仅在板厂判不可行时触发）：对 `R3.pad2` 施**逐焊盘局部** `solder_mask_margin`（净距 ≥0.09mm），仅改交付板、不动冻结源，随后全链重基线。

范围：ENG 交付面到此为止。下单 / 报价 / 交期 / 凭据属**商务**，不在 ENG 范围。
