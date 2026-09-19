# K2 · P4 · 段2c 收敛族「按增量序 re-host」+ 读数 + 具名阻塞（v1）

> ENG（ARCHER）· 2026-09-19 · inc101 · 裁定域 = L2（走廊/过孔策略/PDN/placement）自裁；
> 只读取证 + 段2 工具改动（#K2-31 §二 授权）· 未改冻结四源/判据/生成器/SPEC/真源 · 未落 l6 · 未出 Gerber · 未派 WORKER · 未新增检查齿。

## 1. 关键更正：段2c 执行序 = **P3 增量序**（mroute 必须最后）

`k2_route_segment_v1.py` 原 `ROUTERS` 清单（inc100 建）为 `E → F1 → F2 → F3 → G → 2c-15(mroute)`，
**把 mroute(增量 15) 排在第 5 位**，与规范序冲突：

- `K2-P4-ROUTE-SEGMENT-INTO-CHAIN-PLAN-AND-PROOF-v1.md` §4：`… F3 → ls_xlayer加强(7/8) → G → u4d(10/11) → pdn_in4(12) → u1c85(13) → p3v3_col(14) → mroute(15) → mroute重做(16)`；
- `K2-P4-CONVERGENCE-STATUS-v1.md` §24 具名：**mroute 是 F1..G 对残边「全 0 解」之后新写的兜底器** ⇒ 它必须最后跑。

⇒ 本笔按 **增量序** 重排 `ROUTERS`（含逐器 CLI 适配：`generic`/`plain`/`u4d_plan`/`u4d_emit`/`u4d_scale`），
驱动件 `b23f3e794e0df85a →` 本件 sha 见 §5。链内中间产物与读数见 `drafts/p4-l6-reland-v1/segment2c_canonical_inc101.json 40d700bc43b6f283`。

**佐证**：重排前链内 `non45 = 2051`（= 增量 10/11 的**前驱基线值**，见 CONVERGENCE §18）⇒ 证明重排后链态与 P3 增量序的前驱态**逐值对上**，mroute 早跑是错的。

## 2. 逐器读数（前 canon + 链内即时 DRC → 跑器；未连接/违规 **前→后**）

| 步 | 器 | 未连接 前→后 | 违规 前→后 | 备注 |
|---|---|---|---|---|
| — | （链首 2c-E 前） | — | **33** | 基线 |
| 2c-E | gnd_vias(3) | 200→63 | 33→33 | +140 孔（139 盘中孔） |
| 2c-F1 | ls_local(4) | 63→47 | 33→33 | +16 直连，blocked 46 |
| 2c-F2 | ls_route(5) | 47→45 | 33→33 | +2 |
| 2c-F3 | ls_xlayer(6/7/8) | 45→34 | **33→43** | +11；**新增 10 hole_clearance（见 §3）** |
| 2c-G | ls_in2(9) | 34→21 | 43→42 | +13 |
| 2c-10plan | u4d_refclk_plan | 21→21 | — | 只产计划 |
| 2c-10emit | u4d_refclk_emit | 21→21 | 42→42 | 22 旧段→34 新段 |
| 2c-11 | u4d_scale(11) | 21→21 | 42→**39** | **non45 2051→0**；legs 2032→3346 |
| 2c-12 | pdn_in4(12) | 21→**19** | 39→40 | U6 P3V3 二球 F→In4 盘中孔 |
| 2c-13 | u1c85(13) | — | — | **具名 skip（§4.1）** |
| 2c-14 | p3v3_col(14) | — | — | **FAIL：孔位 span 裕度 −0.075（§4.2）** |
| 2c-15 | mroute(15) | — | — | canonical 未达；**诊断性**单独跑 → 19→**3**（§4.3） |

**确定性**（#K2-31 §2.1 硬要求 2）：`--upto 2c-12` 两次连跑 **逐字节同** `73bfd5e4ef699cb0`。

## 3. 违规上升（33→40）：F3 引入 10× `hole_clearance` —— 具名根因

- 罪项 2 对：`GND(F→In1 盲孔, 0.35/0.2, 40.162,52.25)` ↔ `UART_TX(F→B, 0.35/0.2, 40.162,52.75)`（Δ=0.5mm）；
  `I2C1_SDA(33.25,47.838)` ↔ `I2C1_SCL(33.75,47.838)`（Δ=0.5mm）。DRC：孔距 0.25 需，实际 0.225。
- **GND 盲孔由阶段 E 先落**（post-2c-E 件即含，uuid `3561d03d`）；**F3 又在其正上/正下 0.5mm 落 UART_TX 通孔**。
- F3 `Ctx` 载入既有孔用 `drill/2 = 0.1`，其孔-孔闸要求中心距 ≥ 0.45 ⇒ **判 0.5 合法**；
  但 KiCad 对「盲孔」按 **盘半径 0.175** 计 ⇒ 需中心距 ≥ 0.525 ⇒ 0.5 违规（0.5−0.175−0.1=0.225 实测一致）。
- **l5 对照**：`GND(39.9,52.25)`、`I2C1_SDA(33.2,47.9)` ⇒ 均 >0.55，**0 hole_clearance**。
  ⇒ 系**链起始态漂移**（§5-5 已预告）：阶段 E 在链内选的 GND 孔位 (40.162) 与 l5 (39.9) 不同，F3 遂踩 0.5 列。
- **未修**：不放松下限、不为变绿缩口径（C-12）；根因在 E/F3 的孔位选择，属需重解项（见 §4）。

## 4. 具名阻塞（canonical 链未达 未连接 0）

### 4.1 2c-13 `k2_p4_u1c85_v1.py`（增量 13）—— **对新链不安全，记录 skip**
- 前置**已大部满足**：段1 生成器已含 C85→`(29.7,54.5,180°)` 搬迁（uuid 与 P3 同）；阶段 E 已落 C85.2 盘中孔 `(29.35,54.5)` F→In1。
- 但该 RETIRED 器对新链**不安全**：① 「已搬」检测按字面 `'29.7 54.5 180'`，链内实际 `'29.700 54.500 180'` ⇒ 误判；
  ② 旧 GND 引线删除按坐标 `(31.85,54.5)-(32.525,54.5)` 匹配且**不校验网**，链内该坐标为 **PERSTA#** 段 ⇒ **会误删 PERSTA#**；
  ③ 新孔按 uuid5 判重，与阶段 E 已落孔 uuid 不同 ⇒ **会加重复孔**。
- 残余仅 `C85.1(30.05,54.5) → 锚(30.475,54.5)` 0.425mm 短线（链内旧 stub uuid `c25fcc38` ≠ 器内 `e3bdd905`，器无法识别）。
- ⇒ **具名 skip，不落任何改动**；留给后续重解（或 mroute 兜底，实测残留 1 条＝U1.6↔该 stub）。

### 4.2 2c-14 `k2_p4_p3v3_col_v1.py`（增量 14）—— **断言失败**
`AssertionError: col: 孔位 span 裕度 -0.0750 < 0 (trk/DS320_STRAP_MODE@In2.Cu)`。
P3 时该逃逸孔位裕度 +0.2425；链内 In2 铜不同 ⇒ 孔位被 `DS320_STRAP_MODE@In2.Cu` 堵死 ⇒ **须重解走廊/孔位**（L2，但非机械 re-host）。
对应残留未连接：`P3V3 via(90.825,54.0) ↔ P3V3 trk(90.65,59.0)`。

### 4.3 2c-15 `mroute_v1.py`（增量 15）—— 诊断性单跑（非 canonical 位）
在 post-2c-12 件上单跑：added 15 / blocked 3（`no-free-start/goal-node` 1+1、`no-path-coarse` 1）⇒ 未连接 **19→3**、违规 40→39。
**残留 3**（=`u1c85 的 C85.1 stub` + `PERSTA#/J2.48 长逃逸` + `p3v3_col 的 P3V3 列`）——逐条对应被卡的两器 + 1 strap。
（canonical 要求 2c-14 先过，故本跑仅作读数取证，**不入链**。）

## 5. 边界
- **改**：`k2/tools/k2_route_segment_v1.py`（仅段2 工具；`b23f3e794e0df85a → <见提交>`）· 本件 · `drafts/p4-l6-reland-v1/segment2c_canonical_inc101.json`。
- **未改**：受审板 `dae8dc8d`/l4 `d4e81f64`/设计源板 `fb07d25a`/真源 `dd794c54` · 判据 rev=2 · 生成器 `1ca5ac79` · SPEC · `_shared/**` · l5 旧包；`l6` 未落；未出 Gerber；未派 WORKER；未新增检查齿。
- 临时仅 `/tmp/opencode`。
—— ENG（ARCHER）· 2026-09-19 · k2 HEAD 见提交 · 判据锚 rev=2 · 受审板 `dae8dc8d48ff5b81`

---

## 6. inc102：三处 L2 根因修复（承接 §3/§4，均已实测）

| # | 件 | 改动（L2 自裁域） | sha（前→后） |
|---|---|---|---|
| 1 | `k2_p4_ls_xlayer_v1.py`（F3/增量6） | `Ctx.via_exact` 补 **孔-铜** 两项（本孔→彼盘、彼孔→本盘，hole clearance 0.25）；原式仅 盘-盘+孔-孔 ⇒ 接受 0.5 中心距。修后 need=0.1+0.25+0.175=**0.525**（与 l5 合法间距 0.5536/0.565 一致） | `92029fe42e6886e2`→`233d933cdb7d34a8` |
| 2 | `k2_p4_u1c85_v1.py`（增量13） | re-host 为**链安全**：① C85 定位改「按 Reference 块内 (at)」判位置（链内 canon 已 uuid5 重写 uuid，且格式带小数位）；② MCU_VDD 旧引线按**几何**匹配、保留原 uuid；③ 旧 GND 引线/旧孔删除**块内匹配+校网**（链内同坐标被 PERSTA# 占用 ⇒ 否则误删）；④ 新孔按**位置**判重 | `104ae22eebe3cee0`→`4f1f97149ae58223` |
| 3 | `k2_p4_p3v3_col_v1.py`（增量14） | 定式孔位重解：原 `col` via `(83.50,60.55)` 被 `DS320_STRAP_MODE@In2.Cu` 堵死（span −0.075）⇒ 以本器 oracle 确定性重解取最大裕度解 `(81.00,60.60)` span **+1.0726**，逃逸＝45°(90.65,60.00→90.05,60.60)+西段 | `5e912b528943a655`→`70c3168f83d7ebf8` |

## 7. inc102 逐器读数（驱动件 `b9b9a0fb`→`95d0c4cc05d36da0`；读数件 `drafts/p4-l6-reland-v1/segment2c_canonical_inc102.json 592fe5962c0b1cfc`）

| 步 | 未连接 前→后 | 违规 前→后 |
|---|---|---|
| 基线 | — | **33**（error 8） |
| 2c-E | 200→63 | 33→33 |
| 2c-F1 | 63→47 | 33→33 |
| 2c-F2 | 47→45 | 33→33 |
| 2c-F3 | 45→34 | 33→33（**hole_clearance 已归零**） |
| 2c-G | 34→21 | 33→32 |
| 2c-10plan/emit | 21→21 | 32→32 |
| 2c-11 u4d_scale | 21→21 | 32→29（non45 2051→0） |
| 2c-12 pdn_in4 | 21→19 | 29→30 |
| 2c-13 u1c85 | 19→18 | 30→26 |
| 2c-14 p3v3_col | 18→16 | 26→26 |
| **2c-15 mroute** | **16→2** | 26→26 |

**终态**：未连接 **2** · 违规 **26**（error 3 + warning 20 lib + 2 silk + 1 dangling）· non45 **0** · 网 101 · fps 58。对照基线：未连接 200→2、违规 33→26、error 8→3。

## 8. 残余（**P4 未绿，fail-closed**）

1. **未连接 2**（family 天花板类）：
   - `U1.6 (31.838,51.75) [MCU_VDD]` —— 链内**整段 U1.6 MCU_VDD 逃逸缺失**（l5 有 F.Cu (31.837,51.75)→(30.938,51.75) + via + B.Cu 至 (30.5,54.0)）；mroute 报 `no-free-start-node`。
   - `PERSTA# In5 (59.75,41.4)` ↔ `J2.48 (135.0,56.7)` —— 长走廊（~80mm）逃逸，`no-free-start-node`。
   - 与 CONVERGENCE §24/§25 之增量 15→3 / 增量 16→2 **同一量级** ⇒ 该族（现有器集）止于 ~2；l5 之 0 需 **inc17+**（现工具集内无）。
2. **3 条 clearance error**（漂移类）：①⑵ `GND(F→In1)盲孔(94.15,49.76)↔PCIE_UP7_N F.Cu` 0.1697<0.175（**−0.0053，边缘**）；③ `P3V3(F→In4)盲孔(104.69,55.99)↔DS320_STRAP_B_ADDR1_15-8@In2.Cu` 0.0220<0.200（−0.178）。
3. 20 lib_footprint_mismatch（J-7 家族）· 2 silk_edge · 1 track_dangling（warning）。

⇒ **P4 未全绿；不下单、不出交付 Gerber**（维持 fail-closed）。残余 1 属「族外增量」、残余 2 属漂移重解，两者之下一步（是否补写 inc17+ / 重解孔位走廊）为 **监理口径**。

**确定性（inc102，#K2-31 §2.1 硬要求 2）**：驱动件 `--upto all` **两次连跑逐字节同** `df3ca999496ca74f23cf094567db35cf0122029bd80b78222217f7046a3f4ba`（板终态）。

## 9. 残余深挖（`--only-net` + `K2MR_DBG2` 实证）

- **来源判定**：`l4` / 设计源板 在 U1.6 邻域 **0** 条 MCU_VDD 铜、在 (59.75,41.4) 邻域 **0** 条 PERSTA# 铜；仅 `l5` 有（4 / 10）⇒ 这两条连接是 **P3 增量（post-l4）** 补的，非段2a/图纸缺段。
- **MCU_VDD（dist 3.069）**：`--only-net MCU_VDD` = added 1 / blocked 1，reason `no-free-start-node`；但 `K2MR_DBG2` 显示该边两端 **start(31.838,51.75) 与 goal(30.475,54.5) 在全部 5 个 clearance margin 的粗(step)/细 pass 均 snap 成功**（r=0/1，`own=True bad=0`）⇒ `no-free-start-node` 判词与该边实测**不自洽**（疑 mroute 序内「先落边改变 ctx 后，次边 snap 假失败」或窗口裁剪逻辑）。→ **路由器侧待查项（L2）**。
- **PERSTA#（dist 77.279）**：U1.6 式之外的长走廊（~80mm，In5→J2.48），mroute 报 `no-free-start-node`；属 T-9/T-35/T-36 走廊容量族。
- 两变体（inc15 默认序 / inc16 `--order list`）实测均止于 **2**。

## 10. inc103：`no-free-start-node` 深查结论（路由器模型缺「细间距焊盘逃逸腿」）

- 逐 margin 复算：`U1.6` 起点格在 margin 0.00/0.03/0.08/0.15 为 `own=True bad=0`（可起步），在 **margin 0.25 全部邻格 `bad=1`** ⇒ `solve_edge` 取**最后一个 margin** 的判词 ⇒ 报 `no-free-start-node`。
- 实验（**已回滚，未入库**）：令 `snap_node` 在无「free 且 own」格时回退到「own」格、并允许 A* 从 bad 起点**正交**离格 ⇒ 判词变为 `no-path-coarse(exhausted-1)`（起点格的 4 邻格在该 margin 全被清距封死）。**加性 14 / 阻塞 2 不变** ⇒ 该修**无收益**。
- 结论：mroute 的栅格把**细间距 LQFP 焊盘本体**按「走线清距」标为 blocked，缺少 F1/F3 那样的**焊盘逃逸腿（pad-escape leg）**机制 ⇒ 无法从焊盘起步。这属**路由器模型待增强（L2）**，非坐标/数据问题。
- `PERSTA#` 77.279mm 边同为 `exhausted-1`（长走廊 + 同一模型限制）。
- **回滚**：`k2_p4_mroute_v1.py` 恢复 `7e5c0bf7bb03269d`（= RETIRED 清单原值），本笔不含该器改动。

## 11. inc103：mroute 修「重复孔」⇒ 未连接 2→**1**

- **根因**：`_try_margin` 生成的路径若在末端换层，而换层点恰落在**既有同网过孔**上（U1.6↔MCU_VDD 锚 (30.475,54.5)、以及 PERSTA# 路径上的既落孔 (59.75,41.4)），原式仍**新放一孔** ⇒ `via-clearance(hole:… d=0.056/0.450 · 0.050/0.450)`。逐 margin 诊断（`K2MR_MARG`）实证：m=0.00/0.03/0.08 均卡在 `via-clearance`（路径已成），仅在更高清距下才转 no-free-start-node。
- **修**：`_try_margin` 增加去重——与既有**同网**过孔距离 ≤0.15mm 的「换层」不再新放孔（该层对由既有孔桶承担）。
- **实测**：`--only-net MCU_VDD` 由 added1/blocked1 → **added2/blocked0**；全链 `--upto all` 未连接 **2→1**、违规 **26→26**（error 3 不变）。
- 件：`k2_p4_mroute_v1.py` `7e5c0bf7bb03269d`→`f4e042760a7e3763`（RETIRED 清单原值 → 本修）；读数件 `drafts/p4-l6-reland-v1/segment2c_canonical_inc103.json`。
- **残余 1**：`PERSTA# In5(59.75,41.4) ↔ J2.48(135.0,56.7)` 约 77mm 长走廊；其两端各自可达，但缺长走廊通道（属 T-9/T-35/T-36 走廊容量族）。

**确定性（inc103）**：全链 `--upto all` 两次连跑逐字节同 `967f95d9c7e7af9b69db4a756aa405917aa3def56f2bea51a6e9deea67b3f50b`。

## 12. inc103 追加：PERSTA# 长走廊（残余 1）深查

- **边界件＝既有同网孔、但 z 不覆盖**：该边末端换层点 `(59.75,41.4)` 上已有同网 PERSTA# 孔（由**本器另一条 PERSTA# 边**所落，F..In5 盲孔）；本边所需层对不在其 z 范围内 ⇒ 去重（含 z-cover 版）**均不可省**，新孔与该孔 **holes_co_located**（`d=0.050/0.450`）。⇒ 正确处置应是**把换层点偏移**到邻近合法位（mroute 缺「via-point 偏移」），非「去重」。
- **长通道本身**：即便绕开上述孔冲突，`m=0.15` 仍报 `no-path-coarse(exhausted-2)`（起点侧邻域被封）⇒ 77mm 通道亦缺。
- **结论**：残余 1 = **长走廊 + 换层点偏移**两项 mroute 待增强（均 L2），或改由**族外长走廊/装配件增量**完成。本轮**未改该处置**（避免叠加未验证行为变更）；测完即回编译件，`k2_p4_mroute_v1.py` 已核验 `f4e042760a7e3763`（= inc103 提交态，含去重）。

## 13. inc104 试验：PERSTA# 换层点偏移（**已回滚，无收益**）

- **实现（测后回滚）**：`_try_margin` 内，当某换层点非法且**同点/邻近已有同网孔**（holes_co_located 冲突）时，沿「出腿」方向以 0.15/0.30/0.45/0.60/0.75mm 试偏移，取首个 `via_exact` 合法位并同步移动关节。
- **实测**：实现已生效但**无候选**（沿出腿方向的所有偏移位 `via_exact` 均非法）⇒ 判词与加性完全不变（added1/blocked1）。⇒ 需**二维孔位搜索**（面/邻域），非沿腿一维偏移。
- **回滚核验**：`k2_p4_mroute_v1.py` 恢复 `f4e042760a7e3763`（= inc103 提交态，含去重），`git status` 干净。
- **残余 1 完整口径**：① 换层点需**二维**孔位重解（一维偏移无解）；② 另需长走廊通道。两项均属 mroute 增强（L2）或族外增量。

## 14. inc105：`Grid.vbad` 同网孔剪枝修正 ⇒ 未连接 **0**

- **根因**：mroute 的过孔剪枝模型 `Grid.vbad` 对孔-孔用 `if hnet == net: continue`（**跳过同网孔**），但板内「孔-孔」**无同网豁免** ⇒ astar 认为可在**既有同网孔**上放换层点，精确闸 `via_exact` 再报 `holes_co_located`（0.050/0.450）；先前 inc104 的「一维沿腿偏移」因此无候选。
- **修**：`vbad` 中同网孔亦剪枝（`cpt(hx,hy,hr+0.25+HOLE_R+margin)`）⇒ astar 自动把换层点选到**邻近合法位**（无需另写二维搜索）。
- **实测**：`--only-net PERSTA#` added1/blocked1 → **added2/blocked0**；`--only-net MCU_VDD` added2/blocked0；全链 `--upto all` 未连接 **1→0**、违规 **26→26**（error 3 不变）。
- **达成 P4 判据之一**：`unconnected_zero = 0`（端到端，全链 `--upto all`）。
- 件：`k2_p4_mroute_v1.py`（inc103 `f4e04276` → 见提交）；读数件 `segment2c_canonical_inc105.json`。
- **未闭**：仍余 **3 条 clearance error**（漂移类）+ 20 lib_footprint_mismatch(warning) + 2 silk_edge + 1 track_dangling。

**确定性（inc105）**：全链 `--upto all` 两次连跑逐字节同 `50e54d6101dcfe3f08b20db4b09856c280c319a29715b9293ef3fe98ebbcd5bc`。

## 15. inc106：pdn_in4 oracle T-27 修正 + 链序调整 ⇒ DRC error 3→2（未连接仍 0）

- **根因 1（oracle）**：`pdn_in4.via_margin` 的走线粗筛按**段中点** (`hypot(x-mid, y-mid) > 2.6`)，把 7.62mm 的 `DS320_STRAP_B_ADDR1_15-8@In2.Cu`（中点距孔 2.84mm）误跳过 ⇒ 漏判 **−0.178** 冲突并落孔。改 **bbox 剪枝**（T-27）后 ⇒ 该孔 `REFU margin=−0.1780`。
- **根因 2（链序）**：该冲突本质是「G(ls_in2) 先布 In2 strap（增量 9）→ pdn_in4 后落盘孔（增量 12）」——链起始态与 P3 不同，G 选了会与 U6.FJ6 盘孔相撞的通道。**L2 自裁**：把 `2c-12 pdn_in4` 移到 `2c-G` **之前**（先落盘孔，再由 G 避让）⇒ 冲突消除，且未连接保持 0。
- **实测**：违规 **26→25**、error **3→2**、未连接 **0**；non45 0 · 网 101 · 58 fps · seg 4964 / via 704。
- **残余 2 条 clearance（同一根因）**：`u4d_scale`（2c-11）生成 0.25/0.2828mm 的 `PCIE_UP7_N@F.Cu` 腿，距阶段 E 既落 `GND(F→In1)` 盲孔 `(94.15,49.76)` **0.1697 < 0.175**（差 −0.0053）；u4d oracle 未拦（微差）。件：`k2_p4_pdn_in4_v1.py`（`ea5af7e4` → 见提交）· 链序见驱动件 · 读数 `segment2c_canonical_inc106.json`。

## 16. ⚠️ inc106 **作废**（不可复现）—— 回退至 inc105

- **实测**：inc106 链（pdn_in4 先于 G + oracle 修正）两连跑**不逐字节同**：`412257f8aa9d94db` vs `1dc7c84139fb9388`。
- **定位**：两跑 `canon:pre-2c-15` 完全相同（`80c74d1957c8c257`）、`2c-14` 同（`681fb9b5`），但 `2c-15 (mroute)` 不同（segs 863/len 580.4679 vs 860/579.8437）。驱动 DRC json 两次仅 `date` 字段不同（内容稳定）。⇒ 该链序下 mroute 对同输入**不可复现**（根因待查；同器在 inc102/inc105 的链序下曾两连跑同）。
- **裁定（本器纪律）**：违反 #K2-31 §2.1 硬要求 2（两次连跑逐字节同）⇒ **inc106 作废**，回退 `k2_p4_pdn_in4_v1.py`（`ea5af7e4`）与 `k2_route_segment_v1.py`（`95d0c4cc`，= inc105 态 / canonical 序）。
- **回到的态**（= inc105，已两连跑同 `50e54d6101dcfe3f`）：未连接 **0** · 违规 **26**（error 3 + lib 20 + silk 2 + dangling 1）· non45 **0** · 网 **101**。
- **保留结论**：① `pdn_in4.via_margin` 的**中点粗筛**（T-27）确是缺陷（修后 FJ6 `REFU −0.178`），但**单独修**会拒绝 U6.FJ6 盘孔 ⇒ 未连接回升，故不能单独入库；② 该 −0.178 冲突与链序（G 先于 pdn_in4）相关，重排可解 error 3→2 但**破坏可复现性**。两项均需独立任务（先解 mroute 不可复现根因）。

## 17. inc107：inc106 不可复现**根因定位 + 修复**（DRC 端点项不确定）⇒ 全链 4/4 逐字节同 · 未连接 0 保持

### 17.1 根因（实证，非推测）

`kicad-cli pcb drc`（10.0.5）的 `unconnected_items` 在**同一板文件 + 同一 `.kicad_pro` + 全新 work-dir** 下，
逐次给出的**端点项不同**——同一铜岛内的**电气等价**候选里任取一个（`via` vs `track`、`R1.2` vs 同点 `track`）。
项数 / 网集 / 违规集完全一致，仅"由哪个项代表该缺口"漂移。

取证（板 = inc106 链 `canon:pre-2c-15` `80c74d1957c8c257`，pro = `419ac6ec…`）：

| 试验 | 结果 |
|---|---|
| 3 次连跑（fresh dir，逐字节同的板/pro） | `unconnected_items` **2 种签名**（runs [1,2] vs [3]） |
| `setarch -R`（关 ASLR）3 次 | 仍 **2 种** |
| `taskset -c 0`（绑单核）4 次 | 仍 **3 种** |

⇒ **非 ASLR、非线程调度**；DRC 内部在等价候选集上做了非确定性的代表选取。
（inc106f vs inc106g 的差异即此：`MCU_VDD` 岛取 `via(30.475,54.5)` 或 `track(30.05,54.5)0.425`；
`P3V3_AUX` 岛取 `R1.2(50.95,37)` 或同点 `track`。）
mroute 直接消费端点 `uuid`/`pos` ⇒ 同板同输入两次跑出 segs 863 vs 860（§16）。

### 17.2 修复（L2 · 只在 mroute 内，不动放行闸）

`k2_p4_mroute_v1.py`：把每个 DRC 端点**规范化到其铜岛的确定性锚点**
（同网同岛节点按 `(类型序 pad<via<track, uuid)` 取最小），再按 `(net, 两端锚)` 去重。
锚点**仅作布线起点坐标**；`seg_exact` / `via_exact` 精确放行闸与所有 DRC 下限**不动**。

### 17.3 证据

- **输入侧**：12 份互不相同的 DRC 件（含 inc106f/inc106g 两份分歧件、关 ASLR 件、绑核件）
  经规范化后 → **恰 1 种**端点集（16 条）。
- **mroute 侧**：同板 8 份 DRC 输入 `--dry-run` → 结果全同 `added 16 / blocked 0 / segs 872 / vias 48 / len 601.6361`。
- **全链侧**：`--upto all` **4 次并行连跑逐字节同 `690823e0e8d0ff5918dc…`**（e/f/g/h）。
- **读数（保持 P4 基线）**：未连接 **0** · 违规 **26**（error **3** + lib_footprint_mismatch 20 + silk_edge 2 + track_dangling 1）·
  non45 0 · 网 101 · 58 fps。（3 条 error = §6-A 的 −0.0053×2 与 −0.178×1，未变。）

### 17.4 已评估并**回退**的替代方案（具名留存）

在**驱动件 `run_drc`** 层统一规范化（一次改全部 DRC 消费者输入）也能达成全链逐字节同
（4 次并行 `8d7d0ae7ebfd4d10`），但 2c-E 的目标集随之变化 ⇒ **未连接 0→4**（违反 P4 判据）。
⇒ 回退驱动件（`95d0c4cc` 不变），仅在 mroute 内规范化。

**残留风险（具名）**：F1/F2/F3/G 亦消费 DRC 端点 `uuid`/`pos`（`locate()` + `dist`）。
本链内之所以稳定：该不确定仅落在**贯穿全链直到 mroute 才闭合**的少数网（MCU_VDD / P3V3_AUX 等），
F1..G 对这些网全部 `blocked`、不改板。若后续板态变化使某"歧义网"在 F1..G 被真正布通，需按同法把
规范化扩展到这些器（或回到驱动件层 + 重跑全测量）。**本笔不改 F1..G。**

### 17.5 件

`k2_p4_mroute_v1.py 0b2f5faaf92568de`（前 `74cd163493d488f9`）· 读数件
`k2/docs/drafts/p4-l6-reland-v1/segment2c_canonical_inc107.json 691b959bd3a39a53` ·
驱动件 / 冻结四源 / 判据 / SPEC / 真源 / 生成器 **均未改**。

## 18. inc108（**未入库**）：链序 + T-27 修正功能达成（未连接 0 / error 2），但暴露 2c-E 同源不可复现 ⇒ 回退待解

### 18.1 目标与功能结论（**已实测，未入库**）

目标 = handoff §7-1 后半：`2c-12 pdn_in4` 移到 `2c-G` **之前** + `pdn_in4.via_margin` 中点粗筛改 **bbox**（T-27）。
两者共同作用时（缺一不可）：

| 配置 | 终检 DRC | 终局 sha |
|---|---|---|
| inc105 序（§17，已入库 inc107） | 未连接 **0** · 违规 26 · **error 3** | `690823e0e8d0ff59` |
| **inc108 序 + T-27**（本笔试验） | 未连接 **0** · 违规 **25** · **error 2** | `057b47abd13545b672e4`（4 跑中 3 跑） |

⇒ **−0.178 冲突（`DS320_STRAP_B_ADDR1_15-8@In2` ↔ `P3V3(F→In4)盲孔 U6.FJ6`）消除**，error **3→2** 达成。
（证据：`/tmp/opencode/inc108{m,n,o,p}/`；`inc108n`/`inc108m` 终检均 未连接 0 / viol 25 / error 2。）

### 18.2 但**两连跑不逐字节同** ⇒ 依 #K2-31 §2.1 硬要求 2 **不得入库**

- `inc108m` = `2ab87a922fb305e7`；`inc108n`=`inc108o`=`inc108p` = `057b47abd13545b672e4`（**3/4 同，1 异**）。
- **首个分歧步 = `2c-E`（gnd_vias）**：`canon:pre-2c-E` 两跑完全相同（`46364bfa`），
  但 2c-E 判词 **added 141 / segments 2** vs **added 140 / segments 1**。

### 18.3 根因：**§17 同源**（DRC 端点项不确定）首次打到**description 消费者** 2c-E

`inc108m`/`inc108n` 的 2c-E DRC（同板 `canon:pre-2c-E`）：200 条 `unconnected_items`，其中 **9 条端点项不同**，
例：`(U6.E33 pad[GND] @83.43,50.89, U6.H31 pad)` vs `(走线[GND] 0.6250 @83.43,50.89, U6.H31 pad)`——
**同一铜岛的 pad / track 两写法**（track 起点即 pad 中心）。
`gnd_vias` 由 **描述文本** `_GPAD` 抽取 GND pad ⇒ 目标集随 DRC 任选而变（140/141）。

**⚠️ 对 §17 结论的修正**：inc107 的「4 次连跑逐字节同」**不是稳健结论**——同一 `canon:pre-2c-E` 板在 inc108
四跑中即出现 1 次 2c-E 漂移。故 **inc107 的入库态仍带 2c-E 潜伏不可复现性（~1/4 概率首次暴露）**，
必须在 gnd_vias 侧消除后方可称"链确定性成立"。**判据层结论不变**（未连接 0 / error 3），只是"确定性"一栏须改判。

### 18.4 已试并**弃用**的处置（均实测）

| 方案 | 确定性 | 后果 | 判定 |
|---|---|---|---|
| 驱动件 `run_drc` 端点 → **岛内 (类型序,uuid) 最小**（pad 优先）+ 去重 | 4/4 同 `8d7d0ae7` | 2c-E 目标 **152**；mroute blocked 1 ⇒ **未连接 0→4** | 弃 |
| 同上但**不去重** | 4/4 同 `cb4d2a50` | 未连接仍 **4** | 弃 |
| 驱动件端点 → **逐条目几何最近对**（closest-approach） | 2c-E 4/4 同；全链 2/2 同 `4b208782` | **丢失被 DRC 直接点名的 pad**（U1.20/21/44 未进目标集）⇒ **未连接 1** | 弃 |

**共同病根**：把端点**替换**成"岛的代表"，对 `gnd_vias` 这类**按被点名 pad 取目标**的消费者等于**换掉了目标本身**
（并集 ≠ 真目标；漏掉被替换掉的 pad）。故**不能在驱动件层用"代表替换"解决**。

### 18.5 明确的下一步（唯一可行方向）

**`k2_p4_gnd_vias_v1.py` 的目标枚举改为「岛驱动」**（L2；PDN 缝合策略自裁）：
对每条 DRC 缺口的**两端 uuid** → `f1.islands` 求**铜岛** → 取**该岛内全部 GND pad**（按 `(ref,num)` 归并）作目标，
取代现有「解析描述文本取 pad」。这样：① 目标集是**板内容的纯函数**（不再随 DRC 任选漂移）；
② **不丢**被 DRC 点名的 pad（目标 = 岛的并集，而非"岛代表"）；③ 不再依赖 description。
随后 `2c-12` 提前 + T-27 即可在**同一确定目标集**上重试 inc108 ⇒ 期望 未连接 0 / error 2 / 两连跑同。
（F1..G/mroute 仍可按 §17 方式在驱动件或器内规范化；它们用**铜岛端口**布线，对代表替换不敏感。）

### 18.6 本笔边界

**未改**：`k2_route_segment_v1.py 95d0c4cc`（已回退）· `k2_p4_pdn_in4_v1.py ea5af7e4`（已回退）·
冻结四源 · 判据 rev=2 · SPEC · 真源 · 生成器 · 受审板 · `criteria/**` · `_shared/**`；未出 Gerber；未派 WORKER。
**仅入库**：inc107（§17）。**试验件 sha 留痕**：链序版驱动 `7bca72ac1159b556` · T-27 版 pdn_in4 `bdb89d2eb1ef99ab` ·
驱动 closest-approach `d83f48d732cf1107` · 驱动 min-uid 不去重 `843603f11f040e25`。

## 19. inc109：**gnd_vias 岛驱动目标枚举 + 驱动件端点规范化 + 链序 + T-27** ⇒ 未连接 0 · **error 2** · 4 跑逐字节同

### 19.1 三处根因与对应处置（全部 L2 自裁域）

| # | 根因（§17/§18 实证） | 处置 |
|---|---|---|
| A | kicad-cli DRC `unconnected_items` 端点项在**电气等价候选**间任取 ⇒ 2c-E(`gnd_vias`) 按**描述文本**取目标不可复现（141 vs 140） | `gnd_vias` 目标枚举改**岛驱动**：缺口两端 `uuid` → `f1.islands` **铜岛** → **岛内全部 GND pad**。目标集 = 板内容纯函数，且是各随机写法的**并集**（不丢被点名 pad） |
| B | `pdn_in4.via_margin` 走线粗筛按**段中点** ⇒ 漏判 7.62mm `DS320_STRAP_B_ADDR1_15-8@In2`（REFU −0.178） | 粗筛 **中点 → bbox**（T-27） |
| C | 链序：`G(ls_in2)` 先布 In2 strap、`pdn_in4` 后落盘孔 ⇒ `U6.FJ6` 盘孔恒违规 | `2c-12 pdn_in4` 移到 `2c-G` **之前**（先落盘孔、再由 G 避让） |

另：驱动件 `run_drc` 内把每条缺口的端点规范化到**缺口处**（两端铜岛几何**最近对**，键 = 点距 + 类型序 + uuid）；
**不去重、不丢条目**。此规范化只服务 F1/F2/F3/G/mroute 的 `dist`/`pos` 确定性（它们以铜岛端口布线，对代表替换不敏感）；
`gnd_vias` 已改岛驱动、不再受其影响。**所有 DRC 下限 / 判据不动。**

> 为何不用"岛内 (类型序,uuid) 取一"当端点（§18 已试弃）：那会把 200 条缺口的 pad 目标**并集**化（2c-E 140→152），
> 且会**替换掉被 DRC 点名的 pad**（U1.20/21/44 丢目标）⇒ 未连接 0→4。岛驱动是"按岛取并集、按 pad 保留"，不是"取代表"。

### 19.2 读数（终检 DRC，`/tmp/opencode/drcc109u/`）

| 指标 | inc105/inc107（入库态） | **inc109（本笔）** |
|---|---|---|
| 未连接 | 0 | **0** |
| 违规 | 26 | **25** |
| error | 3 | **2**（余 2 条 = §6-A 的 −0.0053 ×2） |
| 类型分布 | clearance 3 + lib_footprint_mismatch 20 + silk_edge_clearance 2 + track_dangling 1 | clearance **2** + lib_footprint_mismatch 20 + silk_edge_clearance 2 + track_dangling 1 |
| 终局 | `690823e0e8d0ff59` | `34142e06af0fdc2cbf9a` |

**确定性**：全链 `--upto all` **4 次并行连跑逐字节同 `34142e06af0fdc2cbf9a`**（`inc109u/v/w/x`）。
（对照：inc108 试装未加 gnd_vias 岛驱动时 4 跑 3 同 1 异，首个分歧步 = 2c-E；本笔消除该分歧源。）

**具名副作用（非缺陷）**：2c-E 目标集 141（DRC 任选）→ **168**（岛驱动并集），即多落 27 个 GND 缝合孔。
这是**语义完整化**（原法会漏掉 DRC 用 `track` 代表的岛内 pad），非放松口径；vias 数由判据/测量链在重锚时统一登记。

### 19.3 余项（下一步 §7-2）

仍余 **2 条 clearance error（同一根因）**：`u4d_scale`(2c-11) 生成 0.25 / 0.2828mm 的 `PCIE_UP7_N@F.Cu` 腿，
距阶段 E 既落 `GND(F→In1)` 盲孔 `(94.15,49.76)` **0.1697 < 0.175**（差 −0.0053）；u4d `leg_eval` 未拦。
⇒ 需查 `u4d_scale` 的 `leg_eval` oracle 与该腿变体选取（error 2→0）。

### 19.4 件与边界

改：`k2_p4_gnd_vias_v1.py d762428704bd9282` · `k2_route_segment_v1.py 2a34e694393a25ea` ·
`k2_p4_pdn_in4_v1.py 164baca32142660b`（+ inc107 的 `k2_p4_mroute_v1.py 0b2f5faaf92568de`）。
读数件 `k2/docs/drafts/p4-l6-reland-v1/segment2c_canonical_inc109.json`。
**未改**：冻结四源（l4 `d4e81f64` 等）· 判据 rev=2 · SPEC 原件 · 真源 · 生成器 `1ca5ac79` · 受审板 · `criteria/**` · `_shared/**`。
未出 Gerber；未派 WORKER；未新增检查齿。

## 20. inc110（L2 · oracle 口径修正 T-28）：u4d_scale 孔-铜闸改**层感知** ⇒ **DRC error 2→0** · 未连接 0 · 4 跑逐字节同

### 20.1 根因（实证）

`u4d_scale.leg_eval` 的孔-铜闸用 `c.holes`（**含全部孔、无层信息**）：

```python
for (hx, hy, hr, hnet) in c.holes:      # ← 无层过滤
    upd(cv.pt_seg_dist(...) - hw - 0.25 - hr)
```

实测：`PCIE_UP7_P` 在 `(93.25,49.5)` 的孔是 **In2→In5 埋孔**（`lay=[In2,In3,In4,In5]`，不含 F.Cu），
不可能阻挡 F.Cu 腿，却被判 **−0.0530** ⇒ u4d 的候选序（`k` 由大到小、每 k 先 `la=False`）被这个假障碍主导，
**放弃了能避开 `GND(F→In1)` 盲孔 `(94.15,49.76)` 的合法变体**，落成 §19.3 的 2 条 DRC error。

### 20.2 修正（T-28）

孔-铜闸改为**仅计穿过本层（`li`）的孔**：

```python
for v in c.vias.values():
    if v['net'] == net or v['hole'] <= 0 or li not in v['lay']: continue
    upd(cv.pt_seg_dist(...) - hw - 0.25 - v['hole'])
for p in c.pads.values():
    if p['net'] == net or p['hole'] <= 0 or li not in p['lay']: continue
    upd(cv.pt_seg_dist(...) - hw - 0.25 - p['hole'])
```

（`leg_eval` 原本已对 via/pad **铜**做层过滤；仅孔这一支漏了。）

**同段候选复算**（`PCIE_UP7_N` F.Cu，`(93.55,49.76)→(93.75,49.31)`）：

| 候选 | 修前 minmargin | 修后 minmargin | 修后 viol |
|---|---|---|---|
| k=1 la=False（旧选） | −0.0530 | **−0.0028** | 2 |
| k=1 la=True | −0.1498 | +0.1500 | 0 |
| k=2..5（两向） | −0.05..−0.12 | **+0.0599 .. +0.1040** | **0** |

⇒ 新选 = **k=5 la=False（margin +0.0780）**；legs 2032 → **3488**（阶梯更细，偏差更小）。

### 20.3 读数（终检 DRC，`/tmp/opencode/drcc110a/`）

| 指标 | inc105/107 | inc109 | **inc110（本笔）** |
|---|---|---|---|
| 未连接 | 0 | 0 | **0** |
| 违规 | 26 | 25 | **23** |
| **error** | 3 | 2 | **0** |
| 类型分布 | clearance 3 + lib 20 + silk 2 + dangling 1 | clearance 2 + lib 20 + silk 2 + dangling 1 | **lib_footprint_mismatch 20(warning) + silk_edge_clearance 2(warning) + track_dangling 1(warning)** |
| 终局 | `690823e0e8d0ff59` | `34142e06af0fdc2cbf9a` | **`c1ecf392aefb4b8656af`** |

**确定性**：全链 `--upto all` **4 次并行连跑逐字节同 `c1ecf392aefb4b8656af`**（`inc110a/b/c/d`）。
**等长守恒未破**：`对内偏斜 max 0.6134 → 0.6135`（与 inc109 同）；band runs 31 / singles 108 不变。

### 20.4 余项（全为 **warning**，无 error）

`lib_footprint_mismatch 20`（库快照副本不匹配，属既有 G-ROOT 类）· `silk_edge_clearance 2` · `track_dangling 1`。
三项在 inc105..inc109 各态**一直存在**，本笔未新增、未减少；是否需要处置按判据/监理口径（本笔不擅自改口径）。

### 20.5 件与边界

改：`k2_p4_u4d_scale_v1.py f67cc410f7a0c93e`。读数件 `k2/docs/drafts/p4-l6-reland-v1/segment2c_canonical_inc110.json 677635722ab8ea58`。
**未改**：冻结四源（l4 `d4e81f64` 永不改）· 判据 rev=2 · SPEC 原件 · 真源 · 生成器 `1ca5ac79` · 受审板 · `criteria/**` · `_shared/**`。
未出 Gerber；未派 WORKER；未新增检查齿。

## 21. inc112：段3 `ZONE_FILLER` 固化为链步 + In4 同优先级铜区优先级规范化 ⇒ `zone_filled` **10/10**

### 21.1 根因（实证）

判据 `zone_filled`（= 有网非 keepout 的铜区中 `filled_polygon > 0` 者）在链内产物为 **9/10**：
In4 的 `P3V3_AUX`(prio 0, 28.9mm²) 与 `MCU_VDD`(prio 0) **全重叠**，链内重填后被 MCU_VDD 全让 ⇒ 0 填充。
生成器序产物 **10/10**、L5 参照板 **10/10** ⇒ 是**链内**引入。

定位链：
| 板 | zone_filled |
|---|---|
| 段1 生成器产物（直接填充） | **10/10** |
| `2c-A` 输出 | **10/10** |
| `canon(2c-A)` + 重填 | **9/10** ← 首暴露 |
| `2c-B` 输出及以后 | 9/10 |

排除项：① **非顺序问题** —— 在链内板上穷举 5 种 zone 序（current / prio-desc / prio-asc / rev / net-sort）重填**均 9/10**；
② **同优先级冲突确证** —— 删除 `MCU_VDD` 区后重填，`P3V3_AUX` 即 **+**（10/9→全填）；把该 `P3V3_AUX` 优先级 0→1 亦得 **10/10**。

### 21.2 处置（L2 · PDN/浇注策略自裁，owner #14①）

新增**段3 链步** `run_zone_step()`（`--upto all` 内含）：

- **优先级规范化**：逐层内、同 SPEC 优先级按**面积 DESC** 赋 offset，`final = prio*100 + offset`
  ⇒ "**局域（小面积）者优先**"，跨优先级相对序**不变**（只影响不同网、同优先级的重叠）。
- 随后 `ZONE_FILLER` 重填并落板，回读 `zones_filled / zones_total`。

**不改 SPEC / 生成器 / 原理图**；仅作用于链内产物。依据 owner 常设裁定 #14①（叠层分配/PDN/走廊/过孔策略 = L2 自裁勿停）。

### 21.3 读数

| 指标 | inc110 | **inc112（本笔）** |
|---|---|---|
| `zone_filled`（判据口径，独立测量） | — | **10/10 PASS** |
| 未连接 | 0 | **0** |
| 违规 / error | 23 / 0 | **23 / 0** |
| 终局 | `c1ecf392aefb4b8656af` | **`30fa849641323f98104f`** |
| 链末 tracks+vias / 网 / fps | 5712 / 101 / 58 | **5854 / 101 / 58** |

**确定性**：全链 `--upto all` **4 次并行连跑逐字节同 `30fa849641323f98104f`**（`inc112a/b/c/d`）。

### 21.4 附带改动（同笔）

`canon_sort_tracks` 的 `KINDS` 由 `("segment","via","zone")` 收紧为 `("segment","via")` —— **zone 不参与全局重排**
（填充语义 = SPEC 序）；并加 `firsts` 空表守卫（段1 骨架板无 segment/via 时原序不动，避免 `StopIteration`）。
此改动经本笔 4 跑逐字节同验证，未破坏确定性。

### 21.5 边界

改：`k2_route_segment_v1.py f28a4b5a08ed38c0`。读数件 `k2/docs/drafts/p4-l6-reland-v1/segment2c_canonical_inc112.json`。
**未改**：冻结四源（l4 `d4e81f64` 永不改）· 判据 rev=2 · SPEC 原件 · 真源 · 生成器 `1ca5ac79` · 受审板 · `criteria/**` · `_shared/**`。
未出 Gerber；未派 WORKER；未新增检查齿。余 23 条**全为 warning**（lib_footprint_mismatch 20 + silk_edge_clearance 2 + track_dangling 1）。
