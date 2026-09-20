# K2 · 交付包 DFM 追溯审计 + job 文件口径一致性（2026-09-21 · 监理自动续推轮）

**性质**：只读审计（P6 当前阶段）。**不新增判据维**、**不动真源/判据/生成器**、**不重建包**、**未派 WORKER**。
**方法**：ENG 自建独立解析器复算 —— 板文件（segment/via/pad/zone/Edge.Cuts）· Gerber（孔径/外廓/G36）· Excellon（7 档孔数/刀径）· `.gbrjob` ⇒ 与 `06_rulings/dfm_raw_readings.json`、`07_verify/*` 逐项比对。

## A. DFM 报告逐项「标签非绑定」追溯 ⇒ **无自证**
- **16/16 数值块与 DFM 报告逐项相等**，**mismatch = 0**：
  `n_tracks 5037` · 线宽直方图 `{0.16:1875, 0.2:1276, 0.205:1886}`（和 = 5037 ✓）· `n_vias 729` · 过孔 全 `drill 0.2 / 直径 0.35` · 环宽 `0.075` · **非通孔 448** · 过孔类型普查逐层对相等 · `PTH 0.8×16` · `NPTH 3.2×4` · `n_zones 18`
- 交叉面：Gerber 圆孔径 min（In2/In5 = **0.16**）= 板内层最小线宽 ✓ · `all_track_widths_present=True` · 钻孔 xcheck **749 = 749 · all_match** · 7 档 `.drl` 孔数 = 板分类（168/128/4/19/92/37/301）· 8 铜层全 `within Edge.Cuts` · DRC 算术闭合（as-designed **201** + 阻焊桥 **9** = JLC 限 **210**）
- 阻焊 ACCEPT 项有确定性证据：见 `07_verify/mask_accept_fix_proof.json` 扫描（0.05→9 · 0.04→5 · 0.03→4 · **0.02→0**，总量回落 201）

## B. 交付件口径一致性（**2 项具名登记**，均信息级）
| # | 发现 | 根因 | 影响 / 修法 |
|---|---|---|---|
| **B-1** | `-job.gbrjob` 的 `MaterialStackup` = **铜厚全 0.035mm · 介质全 0.1857mm · FR4**，与包内 `03_stackup/JLC08161H_stackup.svg`/`ORDER_NOTES`（**外层 1oz / 内层 0.5oz · 介质 0.1164/0.25/0.1922 · 南亚 NP-155F**）**不一致** | 板文件**无 `(stackup)` 段** ⇒ `kicad-cli` 写入 KiCad **默认推导**叠层（0.1857×7+0.035×8+0.02=1.5999 凑 1.6mm） | JLC 以**叠层名 + 03_stackup 图 + ORDER_NOTES**为准 ⇒ 不改可制造性；修法 = 板 setup 补 stackup 再导出 = **触交付锚** ⇒ 需监理裁定 |
| **B-2** | 同 job 文件 `GeneralSpecs.Finish = "None"`，工艺要求 = **ENIG**（≥6 层不支持 HASL） | KiCad 默认值 | ORDER_NOTES §1 已明写 ENIG、下单页须勾选 ⇒ 实操无阻塞；同样只能「随单注明（接受）」或「重出包（需裁定）」 |
| B-3 | 板尺寸两式：Edge.Cuts **中心线** 120.0×46.0 vs **外廓** 120.1×46.1（含 0.1mm 框线宽） | 计量口径 | gbrjob Size / silk_overhang bbox / DFM 板尺寸**三处统一用外廓** ⇒ 内部一致，非冲突 |

## C. 结论
1. **DFM 链无标签非绑定**：17 项中全部可机算读数均能由交付包内原始件独立复现（census / 钻孔 / 孔径 / 外廓 / 算术），**未发现 DFM 报告与实物不符**。
2. 新增 **2 项信息级具名登记（B-1 job 叠层元数据、B-2 job Finish 字段）**：不改变「可制造」判定；**其修法均需重导出 = 触交付锚（红线：不重建包）** ⇒ 本轮**不擅自执行**，提请监理裁定（接受随单注明 / 授权重出包）。
3. 阶段门态不变：P0–P4 与前轮 P6 判据面已 PASS；**唯一未闭阶段门 = P5 外部实测**；**未越阶段**。

## D. 交件
`DFM_TRACEABILITY_AND_JOBFILE_CONSISTENCY_AUDIT_20260921_v1.json`（`0ad8913a548900ed`）
