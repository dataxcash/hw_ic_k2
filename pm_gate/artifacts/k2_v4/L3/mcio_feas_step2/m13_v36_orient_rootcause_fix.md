# M14 v36 芯片摆向根因调查 — session 记录（**含结论更正**）

> 承接 m13_v35_session_handoff（学参考设计真解 → 判摆向/侧对应 → 确定性修复）。
> 本 session 纯前台自跑、无委派、禁暴力迭代；结论以 EVM 视觉 + datasheet 球图 + 几何/引擎实测三重证据落地。
> 合规：ECN-009 已建（open，L3）；板文件已恢复 rot90（sha f6273de6 还原）；冻结区 lock 0/0/0；
> 备份 `k2_v4.kicad_pcb.bak_v35` 保留。

> ## ⚠ 结论更正（v36 实测证伪，必读）
> 初版本文把结论定为 **case A（芯片要转 90° rot90→rot180，横穿根因）**。但随后两次全量实测**证伪该方向**：
> - **run#1**（板 rot90→rot180，未带芯片落点表）：`solved=[], 18 IFF`。
> - **run#2**（板 rot180 + 重生成的 rot180 芯片落点表）：`solved=[DN6], 17 IFF`。
> - 决定性证据：run#2 挡路 `pad:GND` 为 **rot180 板上真实 DS320 GND 球**（L35/U34 距逃逸点 0.52mm）——**GND 三明治是 DS320 BGA 天生、任意摆向都有**；且走廊/band（tracks_y）是现行 rot90 布局的（rot90 基线 v33g 解出 UP1+DN0，rot180 反而只 1 对），**旋转会打破走廊对齐**。
> - **故正确路径 = case B（保持 rot90）**：残留 16 对 = 共享顺序/gutter 调度（引擎/分配），REFCLK0/1 = MCIO 连接器区独立缺口；引擎逃逸区须紧贴 DS320 的 GND 穿插游走（col_stack/内层逃逸方向），而非转芯片。
> - 详细实测数据见 §5（run#1）、§6、§9。
> 下文从 §1 起为调查全过程记录，**最终结论以 §9 为准**。

---

## 1. 结论（一句话）

**U6 摆向错 90°（rot90），导致 DS320 的 host/device 两族球在板上"同列重叠"，device 球被迫横穿芯片被挡——这是之前一直堆 col_stack 却解不开的真正根因。解法=摆正到 rot180（host 朝东 J2、device 朝西 MCIO），但必须连同 SPEC 全部 rot90 派生输入（control 球位/逃逸区/走廊/障碍）一起重生成 + 引擎逃逸区适配 DS320 的 GND 穿插，属设计层输入协调重建，非引擎单点改动。**

## 2. 现象 → 根因

- **现象**：18 对 (DN0-7/UP0-7/REFCLK0-1) 求解差；之前 `col_stack`（球旁 via 内层穿）只能绕过个别段，全量仍 16/17 失败；孤立单段全 SOLVED = 共享调度挤占；REFCLK0/1 独立失败（MCIO 连接器区缺口）。
- **根因（本 session 新锄）**：
  1. DS320PR1601 是**流透式**（datasheet Fig 7.2：`A_PER → CTLE → Linear Driver → A_PET`，上下行各自同向收发）。
  2. 球图（datasheet Fig 5-1..3 / Table 5-1，全 ch0-15 一致）：每 lane 8 球分 4 列带封在**短轴两侧**——
     - host 球带：`A_PER@列1-2` + `B_PET@列7-10`（短轴一侧）
     - device 球带：`A_PET@列26-29` + `B_PER@列34-35`（短轴另一侧）
  3. 本板 U6 rot90 把芯片**短轴对到 Y**，两族球**同列（X 间隔 0.00mm）仅沿 Y 分带**；但连接器 J2(host) 东 x≈133.8 / MCIO(device) 西 x≈59.5 按 **X 分离**。
  4. → device 球（住芯片东侧 x≈102.9）被硬拉向西边 43mm 的 MCIO，**必然横穿芯片、被同列邻族 pad 挡死**（v34"DIRECT 球列 F.Cu 被同列邻族 pad 挡死"即此）。col_stack 只是让横穿改走内层，没消除"横穿"本身。

## 3. EVM 参考设计真解（视觉 + 文本）

- EVM User's Guide **SNLU300**（产品页 DS320PR1601RSCEVM → "EVM User's Guide"）：
  - `Fig 4-1 Top Layer`（本 session 视觉读取）：U1 居中，**长轴横跨整卡 16-lane 宽度**；**顶部金手指 P1(host/root) 与底部 straddle P2(device/add-in card) 分置 U1 上下**；大量差分走线从 U1 向上下两连接器**对称扇出**；即**芯片短轴 = 数据流轴**，两连接器在短轴两端。
  - `Fig 4-2 Bottom Layer`：回流/背走线配套。
  - `Fig 9-7/9-8`（datasheet 布局例，同款 riser）标题：Top/Bottom Layer View of TI PCIe Riser Card Using DS320PR1601 with CEM Connectors。
- 结论：**EVM 里 host 球与 device 球分置封装短轴两侧、与连接器轴同向**——与本板"同列"相反 → **case A（摆向错）成立**。

## 4. 几何证明（改板 rot180 计算，引擎坐标系）

| 摆向 | HOST 族 X (A_PER+B_PET) | DEVICE 族 X (A_PET+B_PER) | 两族间隔 |
|---|---|---|---|
| **rot90（现状）** | 84.45–103.00 | 84.45–103.00 | **0.00mm（同列重叠）** |
| **rot180（改后）** | 95.23–97.74（东/J2） | 89.86–92.47（西/MCIO） | **5.41mm** |

改后：host 族全落**东侧**（朝 J2）、device 族全落**西侧**（朝 MCIO），中间隔 5.4mm 核心空地；lane（row 轴）转回沿 Y，对齐连接器行带（HS Y 展开 44.35–62.9，与 J2 行带 y42.9–64.5、MCIO J3 y44.5 / J4 y62.7 对齐）。→ 横穿根因在前端消除。

## 5. 实测 run#1（改板 rot90→rot180，`--all-v4`）

- 命令（CWD=容器根，`PYTHONPATH=_shared`）：`AppDir/sharun python3.11 -m eda_core.hs_route_model --all-v4 --board k2/k2_v4.kicad_pcb --spec k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json --alloc /tmp/alloc_v33e/channel_alloc.json --rules _shared/eda_core/drc_rules.json --pro k2/k2_v4.kicad_pro --config k2/pm_gate/artifacts/k2_v4/L2/route_model_config.json --out /tmp/solve_v35_rot180`
- 结果：`status=PARTIAL，solved=[], infeasible=18 全，solve_time_s=34.3，input_fp=b70dbdfd…`
- 判定：**引擎确实应用了 rot180**（UP0 输入球 M=(90.12,62.50)=N34@rot180，非 rot90 的 102.75,57.12）。
- 为何仍 18 全 IFF（诚实）：
  1. **只转芯片不够**——SPEC 里 rot90 时代硬编码的 control/strap 球 `ball_board_pos`、逃逸区/走廊/障碍全是 rot90 几何，未同步 → 引擎跑在「rot180 HS 球 × rot90 障碍」错配下，必崩。
  2. **DS320 BGA 场 GND/VCC 球穿插在信号组之间**——任何摆向逃逸区都必须正确穿越这些 GND（UP0 逃逸被 `pad:GND dist=-0.218` 挡即证），引擎逃逸区/障碍场须适配。

## 6. 解法（设计层输入协调重建，非引擎单点改动）

按 ECN-009 裁决，正式落地需：
1. **板**：U6 `rot90→rot180`（host 球朝东 / device 球朝西）。
2. **SPEC**：全部 rot90 派生的 control/strap 球 `ball_board_pos`、`bga_escape.per_ball` 逃逸区、走廊/band、障碍（GND/VCC 穿插）统一**重生成到 rot180**。
3. **引擎逃逸区**：适配 DS320 BGA 的 GND/VCC 穿插让位（本侧就近扇出，禁补横穿画法）。
4. **REFCLK0/1**：独立 MCIO 连接器区缺口（T2-ECN-2/本发现 §2 之外），需单独处理，旋转不覆盖。
5. 重建后 ≥1 次全量验证（≤2 次纪律），完成后 ECN-009 裁决/归档。

## 7. 证据与资产

- 视觉：`/tmp/opencode/evm/page-17.png`（SNLU300 Fig 4-1 Top Layer，本 session 视觉读取对照）。
- 文本：`/tmp/opencode/evm/snlu300.txt`（SNLU300 全文）、`/tmp/opencode/evm/ds320_ds.txt`（datasheet SNLS683 全文，Fig7.2/球图/Table5-1 已提取）、`/tmp/opencode/evm/u6_pads_engine.json`（U6 全 354 pad 引擎坐标解析）。
- 求解证据：`/tmp/solve_v35_rot180/`（run#1，18 全 IFF）。
- 备份：`k2/k2_v4.kicad_pcb.bak_v35`（rot180 试验前，=rot90 原文）。
- 合规：ECN-009 open；板已恢复 rot90 `f6273de6`；冻结 0/0/0。

## 8. m13_v35 → v36 主要结论增量

| 项 | v35 停滞状态 | v36 增量 |
|---|---|---|
| 全量 | 16 差，堆 col_stack | 根因=芯片摆向错90°（case A 实锤） |
| 残留分类 | 共享调度 + REFCLK 独立 | 共享调度源头=同列重叠横穿；REFCLK 独立仍有 |
| 修复方向 | 学 EVM 再判 | EVM Fig4-1 实锤：短轴=数据流、host/device 分置两侧 → rot90→rot180 |
| 落地 | — | 设计层输入协调重建（板+SPEC+逃逸区+障碍全量 rot180 + 引擎 GND 穿插适配） |

## 9. 结论更正 — case A 证伪，落回 case B（最终结论）

### 9.1 两次全量 run 实测（每步原始输出，禁暴力迭代，2 次已满）

| run | 输入 | solved | infeasible | 说明 |
|---|---|---|---|---|
| 若 rot90 基线 | v33g（col_stack In1 分层） | UP1, DN0 | 16 | （上 session 既有记录） |
| run#1 `/tmp/solve_v35_rot180` | 板 rot90→rot180（无 chip-landing） | **0** | 18 | input_fp=b70dbd…（rot180 板 sha） |
| run#2 `/tmp/solve_v36_rot180_landing` | 板 rot180 + 重生成 rot180 落点表 | **DN6** | 17 | input_fp=b70dbd…（同 rot180 板） |

### 9.2 关键取证（决定证伪）

1. **引擎板解析确实应用 rot180**（run#1 UP0 输入球 M=(90.12,62.50)=N34@rot180），非 rot90 的 102.75,57.12 → 实测非"引擎没吃到旋转"。
2. **chip_landing 重生成（gen_chip_landing_v33 逻辑，板 rot180）= `via_nets=32 deficits=0`** ——"找一个 via 落点"在 rot90/rot180 都可行，落点法**不能区分两摆向**（不判别性）。
3. **run#1/run#2 挡路 `pad:GND` 为 rot180 板上真实 DS320 GND 球**：L35(89.86,62.95)/U34(90.38,62.05) 距逃逸点 (90.12,62.50) 仅 **0.52mm**；K34/V35 @0.79mm。→ **GND 三明治是 DS320 BGA 天生（任意摆向），非 rot90 SPEC 旧障碍**。0.175 净空 vs 0.5mm GND = 必然超限，逃逸必须内层穿。
4. **走廊/band（tracks_y）为现行 rot90 布局设计**：rot90 基线 v33g 解出 UP1+DN0 > rot180 只解 1 对 → 旋转打破走廊对齐，其方向**不可行**。

### 9.3 最终结论（修正）

- **case A（旋转芯片 rot90→rot180）证伪**：无论是否带 rot180 芯片落点表，全量都不到 18 对（0 / 仅 DN6），且打破走廊对齐。
- **正确路径 = case B（保持 rot90）**：
  1. 16 对数据残留 = **共享顺序/gutter 调度**问题（每段孤立可解，缺逃逸区 gutter 资产分配）→ 引擎/分配层。
  2. **REFCLK0/1** = MCIO 连接器区独立缺口（handoff §1.4，T2-ECN 相关），与芯片摆向无关。
  3. 引擎逃逸区需**紧贴 DS320 的 GND 穿插游走**（±0.52mm 三明治 → 内层 col_stack/分层已接入方向，需继续深化到全部 lane），非转芯片。
- 我早前"case A 实锤"判断**错误**，凭两次全量实测证伪并收回；证据以 §9 为准。

### 9.4 资产/纪律

- 板保持 rot90（sha `f6273de6`），未改权威板；`k2_v4.kicad_pcb.bak_v35` 保留。
- ECN-009 已建（open，L3）——记录本案查证过程与证伪；**建议 ECN-009 结论改为 case B 方向**（引擎逃逸区紧贴 GND 游走 + 共享 gutter 调度 + REFCLK 独立处理），或由上层裁决续修方向。
- 全量 run 已满 2 次，按纪律停；不再加跑。临时产物：`/tmp/opencode/boards/k2_v4_rot180.kicad_pcb`、`chip_landing_rot180.json`、`/tmp/solve_v35_rot180`、`/tmp/solve_v36_rot180_landing`。
