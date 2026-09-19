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

## 22. inc113：§6-D **排针面别定案**（L2）= **F.Cu**（同冻结交付板 l4 / 设计源板 / 段1）

### 22.1 待裁事实

`J6 / J9 / J11 / J12 / J13`（5 件 THT 2.54mm 竖直排针）的器件面别：

| 来源 | 面别 |
|---|---|
| 容器冻结**交付板 l4**（`d4e81f64…`，永不改） | **F.Cu** |
| 设计源板 `k2_v4_8L.kicad_pcb` | **F.Cu** |
| 段1 生成器产物（= 本链 `l6` 候选；inc112 产物实测） | **F.Cu** |
| 受审板 l5（P4 期） | B.Cu |

### 22.2 证据（判 B.Cu 为**谱系/放置约定产物**，非制造意图）

1. **全仓无任何工具会翻面**：`grep -rn "SetLayer|\.Flip(" k2/tools/*.py` ⇒ 仅 `k2_p4_lib_snapshot_v1.py:200`（**只读等价证明**用，不落板）与 `k2_w8_trigger_isolation_v1.py:106`（**负控触发器**）。
   `k2_p4_build_l5_v1.py` 重装排针时只设 `SetPosition`/`SetOrientationDegrees`，**不 Flip** ⇒ l5 的 B.Cu 系其上游谱系（anchor/`board.bak`）继承。
2. **电气/铜 0 差异**：`K2-P4-P1-P2-LIB-SNAPSHOT-AND-GENERATOR-DEANCHOR-EVIDENCE-v1.md:122` 具名——
   「5 件排针面别：板 = B.Cu、产物 = F.Cu；其 pad 为 **THT 全层**（`*.Mask` + 全 Cu）⇒ **铜/电 0 差异**，面别属 ⑥ L2 placement」。
3. **判据侧已定性为「放置帧约定」**：`K2-P4-LIB-SNAPSHOT-AND-REPOINT-EVIDENCE-v1.md` §4 表列 `J9/J11/J13` 与 `J6/J12` 的**面 = B**、`fp_rot = 90°`，误报字段为 `dy`/`rot`，成因为「**背面镜像**后偏移/朝向按板坐标系存储，与库局部坐标系异号」；W-8 v2「放置帧归一」正负控证明其**物理等价**（`59/59 全等`）。
4. **SPEC 无冲突**：`SPEC_k2_v4.spec-rev-49.json` 对 `components.pin_headers` 仅给 `column_x` / `positions[*]` / `rot` / `pad_diameter`，
   **无 side/layer** 字段；全 SPEC 文本检索 `单面贴/双面贴/assembly/正面/背面/mounting side/装配` **0 命中** ⇒ **不存在 SPEC 冲突**（故不触发停机条件）。

### 22.3 裁定（L2 · 依 handoff §6-D「按 canonical SPEC/L2 定制造事实」）

**制造事实 = `F.Cu`（正面）**，即与**冻结交付板 l4**、设计源板、段1 生成器、以及本链 `l6` 候选**完全一致**。

**fail-safe 依据**：判 F.Cu = **对已交付板 l4 零变更**；判 B.Cu 需凭空引入一次**面别变更**，而仓内**无任何**机械/装配/SPEC 依据支持该变更（且无工具产生它）。
⇒ 取"不改变已交付事实"的一侧。l5 的 B.Cu 记为**谱系产物**，不作为制造事实。

**影响**：链（段1→段2→段3）**已经**产出 F.Cu ⇒ **本笔无需改任何板/工具/SPEC**；§6-D 由"待裁"转"已裁"。

### 22.4 边界与残留

**未改**：冻结四源（l4 `d4e81f64` 永不改）· 判据 rev=2 · SPEC 原件 · 真源 · 生成器 `1ca5ac79` · 受审板 l5 · `criteria/**` · `_shared/**`；未出 Gerber；未派 WORKER。
**残留（供监理）**：若装配/机械口径另有依据要求背面（B.Cu），属**接口面机械事实**的变更，须 owner/监理裁定后由 ENG 落一次面别变更并重跑全链；本笔按"零变更于已交付板"取 F.Cu。


---

## 23. inc114：#K2-32 §一/§二 **落件**（受审板换 `l6` + pro 两补丁 + 同笔 SPEC bump rev-50→rev-51）+ §一-5 重锚 + §五-3 之 `M-14` 实证

> 授权：**#K2-32 §一-1（放行 = (a) 同笔 SPEC 版本 bump）** · §二（`top_level_sheets`=`k2_sch.kicad_sch` + 消 `sheets: []`）· §三（段2/段3 判定 PASS）。
> 落件提交：k2 **`2b4792c`**（pre-commit pipeline 全 PASS：`PCB 变更 1 项对应 SPEC 变更 1 项` · meta-gate · k2 verify 3/3）。
> 本笔**未**改：冻结四源（l4 `d4e81f64` · 设计源板 `fb07d25a` · 真源 `dd794c54` · 判据 rev=2 `d251bea7`/`1cda6852`/`568d2e93`）· 历史件 `l5`（保留）· `criteria/**` · `_shared/**` · 生成器 `1ca5ac79` · 段2 器 `f28a4b5a` · 真源 yaml；未出 Gerber；未派 WORKER。

### 23.1 构造链复现（两次连跑逐字节同）

| 段 | 读数 |
|---|---|
| 段1 `k2_gen_v5.py`（`1ca5ac79`） | `s1.kicad_pcb` **`d67c0f048f0d0423`**（G10 输入层 8 keepout / 10 有网铜区 / 4 NPTH；与前次记录一致） |
| 段2+段3 `k2_route_segment_v1.py --upto all`（`f28a4b5a`） | **`30fa849641323f98104f`**（`zone_filled` 10/10 · tracks+vias 5854 · nets 101 · fps 58） |
| 确定性 | 本会话 **2 次连跑逐字节同**；加 inc112 已记 4 跑 = **6 跑同 sha** |

### 23.2 落件逐件（前 → 后）

| 件 | 前 | 后 |
|---|---|---|
| `k2/hw/k2_v4_8L.l6.kicad_pcb` | `<absent>` | **`30fa849641323f98104f`**（新增） |
| `k2/hw/k2_v4_8L.l6.kicad_pro` | `<absent>` | **`12ad219b9f66b7b3`**（新增） |
| `k2/pm_gate/artifacts/.../SPEC_k2_v4.spec-rev-51.json` | `<absent>` | **`e96f2df07fe1d764`**（新增；rev-50 原件 `ed0950687e5aec97` 逐字节不改） |
| `k2/pm_gate/project.yaml` | `56583331599fab0f` | `c8bc9efd669f3c2d`（`spec_name` 指针 rev-50→rev-51） |
| `k2/tools/k2_jlc_template.kicad_pro` | `fbd9f99…` | §二 修链 pro 生成（`top_level_sheets` `k2_eco22.kicad_sch`→`k2_sch.kicad_sch`；消 `sheets: []`）；**仅影响链 pro，不影响 pcb 字节**（已由 6 跑同 sha 佐证） |

**`l6` pro = 链 pro + 两补丁**（基 = 链 pro，因其为唯一含 9 条 `ignore` 者）：① `rule_severities` 9 条 `ignore`→`warning`（`copper_sliver` / `footprint_filters_mismatch` / `footprint_type_mismatch` / `missing_courtyard` / `silk_over_copper` / `silk_overlap` / `track_not_centered_on_via` / `tuning_profile_track_geometries` / `via_dangling`）② `top_level_sheets=[{filename: k2_sch.kicad_sch, name: k2_sch}]` + 消 `sheets: []`；另 `meta.filename` 命名派生 `k2_v4_8L.l6.kicad_pro`。

### 23.3 §一-3「允许集外差异」——具名、全量枚举（**供监理裁**）

| 差异 | 内容 | 影响评估 |
|---|---|---|
| pro `net_settings.netclass_assignments` | `l5` pro（145 键）→ `l6` pro（100 键）：**54 键为旧命名死键**（`*_U3` / `*_U7`，板上 **0 命中**，实测）+ **补 9 键** `DS320_STRAP_*`→`LOW_SPEED`（与 SPEC `net_classes` 一致） | **类定义逐字段相同**（`Default`/`LOW_SPEED`/`PCIe85`/`POWER`）；两 pro 对 **68 个 `PCIe85` 网归类完全相同**；**无任何网的 clearance 改变**（`Default` 0.1 == `LOW_SPEED` 0.1）⇒ **对 DRC 无影响** |
| pro `board.design_settings.meta.filename` | `board_design_settings.json`（链模板自带；`l5` pro 无此键） | KiCad 版本痕迹，无判据消费 |

> ENG 判定：上表差异**非 ENG 手工编辑**，而是「落件基 = 链 pro（§一-3 补丁① 的唯一可施行基）」之**必然产物**；#K2-32 §一-3 字面允许集只列「换板 + pro 两补丁」⇒ **本项按「冲突即上报」具名列出**；若监理判其越界，**一次提交即可回退/重做**（l5 pro 原件未动）。

### 23.4 §一-5 全测量链**一次重锚**（受审板 `l5 dae8dc8d` → **`l6 30fa849641323f98`**）

| 测量 | 前（l5） | 后（l6） | 判 |
|---|---|---|---|
| 19 维标准调用 | 15 OK / 2 FAIL | **15 OK / 2 FAIL** | 同类 2 FAIL（见下） |
| └ `drc_errors` | OK（error 0） | **OK（error 0；违规总 164，全 warning）** | 不回退 ✅ |
| └ `unconnected_zero` | OK | **OK（unconnected 0）** | 不回退 ✅ |
| └ `zone_filled` | 10/10 | **10/10** | 不回退 ✅ |
| └ `rule_severity_manifest` | ignore 0 | **ignore 0/62** | 补丁① 生效 ✅ |
| └ `non45_segments` | 0/4720 | **0/5125** | ✅ |
| └ `lib_electrical_level` | **FAIL 差异 28** | **FAIL 差异 5** | 显著改善（未闭） |
| └ `drc_warning_dispositions` | FAIL | **FAIL：未登记 warning 类型 7/9**（`copper_sliver`/`silk_edge_clearance`/`silk_over_copper`/`silk_overlap`/`track_dangling`/`track_not_centered_on_via`/`via_dangling`；已登记 2 = `lib_footprint_mismatch`/`missing_courtyard`） | 未闭（J-1 余项） |
| 5 件测量 ① `w8_footprint_audit`（58 件） | 4 / 28 / 24 / 2 | **49 / 5 / 4 / 0** | 显著改善（`identical` 4→49） |
| ② `pads_within_outline` | 出框 0/0/0 | **0/0/0**（685 pad） | ✅ |
| ③ `ref_plane_continuity` | 名义 3653/3653 | **名义 3795/3795**（段数随链自产布线增加） | 信息项（严口径统计为 owner 面，见 §四-5） |
| ④ `density_and_clearance` | 10mm frame 峰 7 | **10mm frame 峰 7** · 异网 pad 最小 0.20 · 孔环 0.075 · 最小孔钻 0.8 | ✅ |
| ⑤ `min_clearance_drc`（bracket） | [0.100, 0.105] | **[0.100, 0.105]**（T=0.100 ⇒ 0 违规） | ✅ |
| `engine verify k2` | 4/4 | **4/4 PASS**（`project_sch_coverage` + `sch_structural` + `netlist_connect` + `bom_consistent`） | ✅ |

### 23.5 §一-6 撤板三臂 + 确定性

- **静态**：链两器全文检索 `l4` / `l5` / `k2_v4_8L` / `k2_v4.kicad_pcb` ⇒ **0 处读板引用**（命中仅为 docstring 声明与 `p3_v57_l4_apply_drawing` 模块名）；链输入仅 `SPEC_PATH` / `YAML_PATH` / `LIB_DIR` / `REFMAP_PATH` / `PLACEMENT_PATH`。
- **动态（arm3，实跑）**：**同时移走** `l4`/`l5` 的 pcb+pro（存在性断言：移走后 4 件均 `STILL-PRESENT`=0）⇒ 段1 自检 **6/6 PASS**、器件 54 / pads 672 / NC 128 / G10 8-10-4 **未变** ⇒ 全链产物 **`30fa849641323f98104f`（逐字节同）**；`trap EXIT` 无条件还原成功（4 件 `restored`），l4 `d4e81f64` / l5 `dae8dc8d` / l5 pro `35c8f34b` 复核**未变**。
- **确定性合计**：本会话全链 **3 跑**（run1 / run2 / arm3）+ inc112 已记 4 跑 = **7 跑同 `30fa849641323f98104f`**。
- **§一-7**：`l5` 板/pro **保留为历史件**（未删）。

### 23.6 §五-3 之 `M-14` fail-closed 实证（三臂，实跑）

题目：`project.yaml::board_path` 置坏 ⇒ **链必须失败**（不得静默放行）。

| 臂 | 布景 | `config.board_path()` | cwd 相对存在 | `red_team.R13_pcb_guard` 读数 |
|---|---|---|---|---|
| ARM1 | 现行 `project.yaml`，cwd=k2 | `k2_v4.kicad_pcb` | **True** | `[]`（板被审到、registry 合法） |
| ARM2 | 坏指针（临时 root），cwd=k2 | `k2_v4_NOPE.kicad_pcb` | **False** | **`[]`（静默跳过）** |
| ARM3 | 合法名 + 空 registry（临时 root） | `k2_v4.kicad_pcb` | True | **有 findings**（`R13: PCB … 无合法写盘登记 (write_guard registry 缺失)`） |

**结论（实证，非推断）**：ARM3 证明该探测器**活着**（能报问题），ARM2 证明**置坏指针 ⇒ 零 findings = 链不失败** ⇒ `M-14` 所要求的「置坏指针 ⇒ 链失败」**在 `red_team` 消费者处不成立（fail-OPEN）**。

**另测**：`pm_gate/check_qa.py:22` 的 `PCB_PATH = join(dirname(dirname(check_qa.py)), config.board_path())` 在拆仓后基址 = `k2/_shared` ⇒ 解析到 `k2/_shared/k2_v4.kicad_pcb`（**永不存在**）⇒ 该 gate 恒 FAIL「施工产物缺失」（fail-closed 方向正确，但属**消费者基址缺陷**）。

**消费者盘点（`board_path` 全量）**：`check_qa.py:22`（基址=`_shared`，恒 FAIL）· `wp1_semantics_check.py:46` / `tools_measure_l1.py` / `tools_executor_single_pair.py:17`（同基址族）· `red_team.py:346,395`（**cwd 相对**；缺文件 ⇒ `return out` = fail-OPEN）· `cli.py:367`（cwd 相对）· `falsify_service.py:290`（`pcb_root` 拼接）。
⇒ `M-14` **不宜判根闭**：无判据（owner ② 禁新增齿）+ 消费者 fail-OPEN + 基址约定不一（三族）。**ENG 建议**（供监理裁）：以一句话口径钉死「`board_path` 解析基址 = 项目根（`artifacts.discover_project_root()`）」，并由 ENG 在**既有**消费者上做 fail-closed 断言（**非新增检查齿**）；否则 `M-14` 余④口径无法闭。

### 23.7 未闭 / 待监理（承 §五 串行）

1. **2 条 FAIL**：`drc_warning_dispositions`（7/9 未登记；J-1）· `lib_electrical_level`（差异 5；U-03/J-7 ⑦「重指 lib_id」待裁）；
2. **§一-3 允许集外差异**（§23.3）—— 需一句话裁定（接受 / 回退）；
3. **#K2-30 §2.2 `density_and_clearance` rev=3 启用**（gate 属主 + 签认 + 锚 rev=3）；
4. **#K2-30 §2.4 `N-03`**（`sheets`/`top_level_sheets` 一行 pro 键值）—— 本笔已由 §二 链侧修正，受审 pro 侧已按 §二 落值；
5. **#K2-30 §2.6 `F-9`**（走廊 0.25 vs 0.41 量化）；
6. **#K2-31 §四-5 `refplane` 4 项**（成因分离 / 机判+正负控 / `max_contiguous_gap_mm` 分布 / 整改前后读数）—— 机制已存在（`p4-j8-v3-measurement-v1` + `p4-refplane-strict-gap-v1`），拆类与分布为本轮续做项。

### 23.8 §一-5 之 `C1` / `C2` / `L-1` 复核（#K2-29 §7 同批项；本笔零改动）

| 项 | 定义（#K2-29 §7） | 落件后实测 | 判 |
|---|---|---|---|
| **C1** | `p3_placement_solution.json` rev=2 + L2 解 | `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json` **`dfbf65c5b456cdd2`**（rev=2；`solved_count` 15 · `all_pass` True · `selfcheck` 五类违规 0）· `k2/pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json` **`086d453d23c5fbff`** | **PASS（与 #K2-29 登记值逐字节同，未动）** |
| **C2 / L-1** | L-1 来源限制登记（闭得由 §14.1 载明） | 登记在库且未变：canonical 布局解 = **P4 已批准落位的 canonical 捕获，非独立求解**；54 件中 **28 件仅板来源** + 2 件曾陈旧（`C86`/`R42`）已由 C1 rev=2 补正 ⇒ **15 一致 / 0 陈旧** | **登记完好；本笔不改变它**（链条坐标仍取 `PLACEMENT_SOLUTION_v1.json`，未新增任何非板权威） |

> **对 P4 关门的含义（具名携带，勿隐）**：`C4` —— L-1 **若未获 owner 另行授权 (c)，须在 P4 关门时具名接受（或转 (c)）后方可进 P5**；**不得**在 P5 打样件中隐去。ENG 此处只登记事实，**不代 owner 接受**。

---

## 24. inc114：`ref_plane_continuity` **新口径机判 + 成因分离 + `max_contiguous_gap_mm` 分布**（#K2-31 §四-5 ①②③ + ④-前）

> 授权：**#K2-31 §四**（口径精化 `non_antipad_gap == 0`；面积率降信息项）。专件：
> `k2/docs/K2-P4-REFPLANE-NONANTIPAD-GAP-MECHANISM-AND-DISTRIBUTION-v1.md` **`bc91256aabdf0182`**；
> 新仪器 `k2/docs/drafts/p4-refplane-nonantipad-v1/measure_non_antipad_gap.py`（只读）。

- **主判**：`non_antipad_gap == 0`。受审板 `l6 30fa849641323f98`：`non_antipad_gap` = **0.0 mm²**（R=0.5 默认）⇒ **PASS**；若 `hole_keepout`（**0.006168 mm²**）亦计入 ⇒ ≠0（**未以「接近 0」宣称归零，如实并列**）。
- **⚠ 核心发现（须监理裁）**：结论对判别半径 **`R`** 敏感 —— `R=0.25` ⇒ `non_antipad_gap = 20.8905 mm²`（FAIL）· `R=0.5`/`1.0` ⇒ `0.0`（PASS）。本板缺口腔尺度集中于 **0.5–1.0mm**。两条出路：(1) 钉死 `R`；(2) 改采**成因派生定义**（antipad = 各 pad/via 按 zone clearance 外扩并集；本件未实现，可授权实现，**非新增检查齿**）。
- **正/负控**：正控（in-run，严格全长覆盖段 n=**3176**）⇒ `non_antipad_gap=0` 且 `max_contiguous_gap=0` ✅；负控（冻结 `l4`，zone 全未填充）⇒ **798.1724 mm²** / `max_contiguous_gap` **57.13 mm** / 严格覆盖 0% ⇒ FAIL ✅。
- **`max_contiguous_gap_mm` 分布（③）**：仅有缺口段（n=**619**）p50 **0.0938** · p90 **0.3755** · p95 **0.3755** · max **0.611**；全 3795 段 p90 0.0599 · p95 0.2687 · p99 0.3755。阈值归监理（不预设）。
- **④**：整改**前**读数 = 本件（受审板 `l6`）；整改**后**待 `#K2-31 §四-4` L2 载体整改（反焊盘阵列/补缝合孔，改受审载体 ⇒ 与落件同批）。
- 红线：只读；未改板/SPEC/判据/`_shared`/生成器；未放松下限；未派 WORKER。

---

## 25. inc114：ENG 后台等待规约纠错（**#K2-33** 落地）

- 缺陷（ENG 上轮实际）：`pgrep -f <脚本名>` 轮询**自匹配**（轮询命令自身/父 `bash -c` cmdline 含 pattern）⇒ `|| break` 永不触发 ⇒ 每次白等满 20 分钟。
- 落件：`k2/tools/k2_wait_pid.sh`（**按 PID 判活**；pattern 形式在解析期排除自身+全部祖先进程，之后只查 `/proc/<pid>`）+ `k2/docs/K2-ENG-BACKGROUND-WAIT-CONVENTION-v1.md`（规约 + 禁用写法）。
- **对照实验实录（#K2-33 §五）**：OLD 自匹配臂 ⇒ 任务 20s 结束后仍死等，`timeout 32` 杀之 **rc=124**（并复现命中轮询自身）；NEW 按 PID 臂 ⇒ `sleep 15` 任务 **`用时 15s` rc=0**；NEW2 pattern 臂 ⇒ `sleep 12` 任务 **`用时 12s` rc=0** ⇒ 验收达标（≤1 个 poll 周期，实测 ≤3s 粒度）。
- 边界：只新增 ENG 工具/文档；未改板/SPEC/判据/`_shared`/生成器/冻结件。

---

## 26. inc114：`N-03` 载体复核（已修）+ `F-9` 走廊口径量化（专件）

- `N-03`：`l6.kicad_pro` `top_level_sheets = k2_sch.kicad_sch`（**存在**）、顶层 `sheets` 键**已消**；链 pro 生成根因亦已修（模板，`#K2-32 §二`）⇒ 载体已修 + 根因闭；判定待监理（「无判据类」同批）。
- `F-9`：专件 `k2/docs/K2-P4-F9-CORRIDOR-CALIBER-QUANTIFICATION-v1.md` —— 0.25/0.41 = 端点**参照物**差（体宽 vs 焊盘外接框），精确复算吻合；**四板 × 四口径**板侧恒为 82.60/104.84 ⇒ 揭出 **`NG-1`**：SPEC 在册 `U6 board_measured 82.76/105.00（δ0.16）`**不可复现**；影响量化 = 阻抗 ΔZ=0 · 制造无影响 · 容量两口径均过 ⇒ **不停机**；余项归 owner（冻结表回改/口径具名）。

---

## 27. inc114：`J-1` warning 逐类处置台账 + `U-03`/`M-09`/`J-7` 残余 9 件定位（专件）

- 专件 `k2/docs/K2-P4-J1-WARNING-DISPOSITION-LEDGER-AND-U03-REMAINDER-v1.md`：`l6` DRC **164 全 warning / error 0 / unconnected 0**，逐类 9 种（**7 类未登记共 90 条**）已给归属 + **不豁免**处置建议，小计数类逐条具名；w8 残余 **9 件**（5 `electrical_diff` = `U6`/`U1`/`L1`（≤0.5 µm）+ `J3`/`C85`（**物理等价**）· 4 `no_library_link` = `H1..H4` 纯机械件）。
- 边界：只出证据；未改 `criteria/**`（安装归 gate 属主+监理）、库、板、SPEC、生成器；未以「接近 0」淡化（如实列 1、1）。
