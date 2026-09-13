# CO-172 — 非执行者对抗复评（CO-166..CO-171）｜as-found @ `7bffb75`

- verdict：**PASS_WITH_FINDINGS**｜findings：7

| id | sev | kind | what（摘要） |
|---|---|---|---|
| F-1 | medium | UNBOUND_RECORD_FIGURE | ORDER_NOTES §5「模型间 spread ≈4.8%」为**记录派生数字**但既无来源记录串、亦无牙齿（CO-171 的 t12 只绑 dev% +11.7%）⇒ R-CO171-1 在本备注内**仍有未绑定项**（P1 实证可规... |
| F-2 | medium | UNBOUND_RECORD_FIGURE | §2 非通孔过孔**逐 span 分解**（92/88/32/8）为硬编码字面量；来源 = DFM 记录 `as_built.via_type_census`。总量 220/493 由生成式绑定，但**分量无牙** ⇒ 过孔口径变更后可留陈... |
| F-3 | medium | UNBOUND_RECORD_FIGURE | §3 阻焊净距 0.0695mm / 欠 0.0205mm / 回退净距 0.0995 / 开窗 0.05→0.02mm 为硬编码；来源 = CO-147 记录 `mask_measure`（gap/shortfall/jlc_min/ma... |
| F-4 | medium | UNBOUND_RECORD_FIGURE | §6 U6 热数字（PACT 4.7–7.0W / θJA 17.4°C/W / Tj 限 120°C / Tj 121.8–161.8°C / ψJB 路线 173.6°C / Ta 40°C）为硬编码；来源 = CO-148 热裁定 +... |
| F-5 | low | UNBOUND_RECORD_FIGURE | §4 JLC 限值散文（≥3.5mil / 孔 ≥0.15 / 盘径 ≥0.25 / 孔径+0.15 / ≥0.2）源 = JLC 能力记录；「板规铜-板边 0.30mm」源 = **冻结** `drc_rules.manufacturin... |
| F-6 | medium | UNBOUND_RECORD_FIGURE | 叠层图（03_，**随单提交的制造输入**）的**铜厚矩形几何**为硬编码 0.035/0.0175mm，t11 只绑文本（P7 实证）⇒ 声明铜厚变更时图与声明在**几何上**脱钩，制造侧按图施工。... |
| F-7 | low | ORACLE_SENSITIVITY | runner `step_did_work` 快照为**单信号 mtime_ns**（P8 实证）⇒ 粗粒度/网络 FS 同刻重写、mtime 规范化/回写、时钟回拨下可**假停机**（fail-closed，不致假通过）；且受控集为全局集... |

独立确认：

- V1 as-found pin 逐件复核：7 件中 7 件与 handoff 声明一致（SPEC/底板/manifest/冻结规则/登记簿/boundary/备注）
- V2 as-found 打样包记录 revision = CO146-PKG.7；牙齿 17 项、全 True = True（牙齿名集不含任何 §2/§3/§5-spread/§6/§4/几何 类判据）
- V3 备注内 §2/§3/§4/§5-spread/§6 各数字**现态与来源记录一致**（逐项字面比对）：12/12 命中
- V4 as-found 登记簿 77 项 / OPEN 0；`meta.counts` 据 items 复算逐项一致 = True（关注点④裁定：键集为 `set(declared)|set(derived)` **并集**比对 ⇒ 多写/少写键均 fail-closed，属设计选择而非过严缺陷）
- V5 as-found 叠层图 sha16 44370475b258848f（与 handoff 一致）且几何 = 21.00/10.50 px（与 1oz/0.5oz 相符）⇒ F-6 属「无绑定（潜在漂移）」而非「现错误」
- V6 as-found runner revision = CO-169.1；`--check` 静态牙齿 t01..t11（含 t11 步产物 oracle）

负控（内存注入）：

- P1 §5 spread 漂移（F.Cu M1 90.61→94.0：spread 4.8%→1.0%，而 dev% 仍由 M2 的 11.69% 决定） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P2 §2 过孔分解漂移（F.Cu→In2.Cu 92→93） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P3 §3 阻焊净距漂移（0.0695→0.0694） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P4 §6 热数字漂移（worst Tj 161.8→165.0） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P5 §4 JLC 限值漂移（min track 0.09→0.10） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P6 §4 板规铜-板边漂移（0.30→0.25） ⇒ as-found 判据仍全 True（**未被覆盖**）：{'impedance_watch_dev_pct': True, 'drc_as_designed_total': True, 'drc_lib_footprint_sum': True}
- P7 as-found `stackup_svg['spec']` 不接收声明定值表；`stackup_svg_binding_checks` 键 = ['stackup_code', 'thickness', 'outer_copper', 'inner_copper']（**纯文本**）⇒ 铜厚矩形**几何**（0.035/0.0175mm 字面量）无任何牙齿覆盖
- P8 as-found `_snap_watched()` 的值为**标量 int（mtime_ns）** ⇒ 内容变化若无 mtime 前进（粗粒度/网络 FS 同刻重写、utime 规范化、时钟回拨）不可见；且受控集为**全局集合**、非步本地
