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
