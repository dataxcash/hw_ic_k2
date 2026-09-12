# m13 v57 — W3 Boundary **v2.11**（文件名沿用 v1.82 以保持 co77 身份链；CO-121/121.1/122/122b + CO-124..CO-132（D-6 定案 + rev-17 退役 B.Cu 载体 + rev-18 R1 In4 承载几何派生）+ **CO-133（L2 自裁 · 施工期物理施加：rev-18 声明 PDN 铜落板 `d4e81f647be7f980` + 幂等/板实合规机判）已登记**；**CO-134（整改通知 #09：③ 重新定性 = 工程换算错误 → REQ-R3-2 忠实实现（铜边 ≥ 2w 按层）+ 需求/实现分家规矩 + co124 K9）已登记**）（+ **CO-135（非执行者复评 rev-19 + CO-134｜L2 声明/工具卫生修正：co77 覆盖扩至 markdown 表格行、链路 pin 全量刷新、co78/co81/co84 对 rev-19 重跑、L5 fab pin 刷新）已登记**；**CO-136（L2 自裁 · 闸卫生续：co106 陈旧牙齿改数据无关合成控 / co124 定义件版本派生 / co77 表格行 citation 负控牙齿 / 登记簿 +2 TOOL_DEFECT）已登记**；**CO-137（L2 只读分析：as-built 对间偏差几何修正可行性 = MIXED）已登记**；**CO-138（L2 只读分析：偏差耦合几何画像 —— B.Cu/F.Cu = 长平行在域内；In5 = 21.8° 斜交扇出）已登记**；**CO-139（L2 自裁 · K9 硬化：豁免域须 hash-pin 依据 + 负控 T9）已登记**；**CO-140（L2 只读分析：as-built 偏差归因 —— 1 接口固有 / 1 路由可改 / 1 斜交）已登记；F.Cu 项升 L1（J2 接口节距）**；**CO-141（L2 只读审计：对间 2w 符合性全量 —— 原「3 处」为下界，实为 24 个平行对-对；根因 = 路由器列距基准漏 3W）已登记**；**CO-142（L2 只读：对间 <3W 违规逐条明细 + 构造阶段归因 —— B.Cu 14 逃生竖列 / F.Cu 10 J2 land）已登记**；**CO-143（L2 只读：纠正 CO-141 附记2 的 f13 pair_xorder 定位 → 真实所在 = escape-fan 落位判据 `p3_v57_co10_west_fan_probe.py:check()`；施加可行性 = 3W 可满足但单遍贪心+PDN 障碍下无法 32/32，须重派生扇落位策略；登记簿该项保持 OPEN）已登记**）（+ **CO-117（L2 自裁）：band In4 铺铜归属 + SPEC rev-15**；**CO-114 非执行者对抗复评 rev-14 = PASS_WITH_FINDINGS（6 发现）**；W3-CN.41 收口 + CO-67..CO-71 方案(a) 全链执行/判据/判定接口 + CO-72 PDN 平面对齐 rev-6 + CO-73 层角色声明一致性终扫（rev-7）+ CO-74 B.Cu 电力铜退役/In4 承载（SPEC rev-8）；CO-72-PDN-1 归口 L1→L2 并闭合 + CO-75 西侧 1.580 未覆盖维搜索（负结果，L1 ① 证据补强）+ **CO-76 非执行者侧对抗评审 pass 1/2（F1/F2/F3 发现并修复）** + **CO-77 收口声明件当前态身份引用校正** + CO-78 层角色漂移回归闸（F1 缺陷类关闭） + CO-79 探针空真通过加固（守卫负控 A10） + CO-80 L4 工程文件规则对齐 + 独立 kicad-cli 复现 DFM + CO-81 受控工程文件规则回归闸 + CO-82 L4 工程文件网类缺失修复 + 闸覆盖补全（net_settings） + CO-83 工程网类↔红线 SPEC net_classes 交叉校验 + **CO-84 DRC 放宽域一致性闸（dru↔域工件↔板 rule area↔SPEC）** + **CO-85 非执行者侧对抗评审 pass 2/2（V1 全链 12/12 逐字节复现 + V2 闸牙齿复核 + F1 F.Cu 行更正 + F2 连接器焊盘场 0.6mm 硬限）** + **CO-86 L2 备选闭合判定（铜跨 0.705→0.585/0.407 均不可达 0.875：WEST 差 +0.232 / 焊盘场差 +0.682）** + **CO-87 L2 合格标准覆盖性机判（ch.5 §4 PDN 压降 / ch.2 热 = NOT_DEMONSTRATED：缺输入，已登记）** + **CO-88 PDN live 字段板实性机判（FAIL：55 孤儿 entry / 184 板实 pad 无决策 / 解耦零板实落点；修复候选+波及清单已派生）** + **CO-89 SPEC rev-9 PDN 板实化（ppc 重生成 223+86=309/309 覆盖、旧 BOM 退役留存；板逐字节不变；全链重基线）** + **CO-89b 复现重跑产物入库（12/12 逐字节一致）** + **CO-90 非执行者侧对抗评审 pass 3/3（对象 rev-9 新基线；全链 12/12 逐字节复现 + CO-88/89 事实独立复核 + 闸注入突变 4/4；F1/F2 修复（CO-88.2）+ F3 覆盖口径登记）** + **CO-91 PDN 计划坐标权威净距闸（pdn_apply 实落集 × 冻结规则源 `drc_rules.json`；判 FAIL：ppc via 35/223、stitch via 41/69、zone via 7/20、F.Cu 短段 75/223；修复候选 35/35 可重定位、PDN 覆盖不退化；覆盖缺口补齐）** + **CO-91.2 规则源唯一性 fail-closed（`K2/_shared` ↔ 容器 `_shared` 的 `drc_rules.json` 同字节断言；实测同值 `0a459839e15960b8`；漂移即不可判）** + **CO-91.3 闸/修复分离（移除内嵌 fix_candidate；其 8 向×半径梯读数违「零坐标搜索」红线，已作废）** + **CO-92 PDN rev-10 修复候选（声明式有限 palette 机判；ppc 223 → kept 188 / relocated 1 / blocked 34；stitch 28/12/29；zone 13/4/3；短段 0.5→75、0.2→13）** + **CO-95 In4 平面可达性机判 + 陈旧 keepout band 退役（premise 已被 CO-74 判失效）→ SPEC rev-11 `d85f10f722ba22b0`：55 power entry = 35 显式 polygon / 8 桥区 target / 6 L3 可达性义务 / 6 需区域裁决；新增 plane_reachability_requirement；全链重基线 PASS、板逐字节不变** + **CO-94 blocked pad 可连接性闭合判定 + 裁定（维持 blocked：34 中 15 在宽松有限家族内可连，但余量低至 13.6µm 且 7 个仅在家族上限命中 ⇒ 采用即把「搜索」写进决策，违零坐标搜索红线；故 34 判为 L2 手段内不可连接，升级 L1/工艺）** + **CO-93【L2 自裁 · PDN 权威净距重落 = 施加 rev-10】SPEC rev-10 `4416e42eed10cb8c`：ppc 223→189 entries（blocked 86→120，已连接 223→189）、stitch 69→40 落/60 blocked、zone 20→17/3、短段宽 0.5→声明 0.2；CO-91 对 rev-10 = PASS（0/0，牙齿 4/4）、CO-92 对 rev-10 = 不动点；全链 G4→G7 重基线 PASS、板逐字节不变；新基线非执行者复评欠（CO-94）** + **CO-96 非执行者侧对抗评审 pass 4/4（对象 rev-11 基线：6 项发现 F1..F6 —— F1 退役键谱系断裂 / F2 可达性要求不可机判闭合 / F3 文本依赖 / F4 scope 缺口 / F5 陈旧 board_realized / F6 latent bbox；V1/V2/V3/V4 复核 OK；CO-94/CO-95 复评义务已履行）** + **CO-97 退役留存完整性闸 + 显式登记册（把红线『退役决策须显式留存』机判化；CO-96 F1 的『静默』面以显式登记关闭；L2 自裁：不解冻 `_shared`，施工侧改项目内承载、施工期激活）** + **CO-98 In4 平面可达性义务状态报告（机判化 CO-96 F2/F3/F4：三态 35/14/6 + scope 排除 40/17/0 + 裁决依据 5 机判/1 文本；co95 PIP 行为中性加固关闭 F6）** + **CO-99 PDN 计划集互相冲突闸 + 施工 dry-run（两个覆盖缺口 G1 计划集互判 / G2 孔距 net-agnostic；实测 FAIL_MUTUAL_SHORT：7 异网重叠 + 35 净距 + 39 孔距；pdn_apply 实落 DRC 42→274）** + **CO-100 互障感知修复候选（residual 重叠 0；新增 blocked **5** 项 = 4 ppc + 1 stitch —— CO-103 校正原「6 项 / 全在 U6 0.5mm 场」为过期读数）** + **CO-101【L2 自裁 · 施加】rev-11 → rev-12 计划集互障重导（ppc entries 189→185 / relocated 61 / 新增 blocked 4；stitch relocated 5 + blocked 1；zone relocated 4；退役留存 + F5 同步 + F1 回填；全链重基线 PASS、板逐字节不变；CO-99 由 FAIL → PASS）** + **CO-102【L2 自裁 · 项目内引擎承载】修正版 PDN 施加器（短段宽读 SPEC 0.2 + via 去重 + blocked 口径对齐；scratch 三态 DRC：baseline 42 / 冻结 76(+34) / 项目内 42(+0)）** + **CO-103 非执行者对抗复评（对象 rev-12 = CO-99/100/101/102 + 链 pin + 收口声明；verdict `PASS_WITH_FINDINGS`；F-A 声明漂移 / F-B 升级证据不足 / F-C co95 身份引用陈旧）** + **CO-108 非执行者对抗复评（rev-13 基线 = `PASS_WITH_FINDINGS`；F-A 记录内 provenance pin 漂移已校正 + F-B 信息性 + F-C 登记）** + **CO-108 补记 F-D（bridge zone 层归属张力 = L3 派生前未决前提）** + **CO-109（L2 自裁）In5←In4 走廊空洞 = 按设计（非待 L3 派生）；bridge zone = B.Cu；step ② 重定范围 + owner 升级** + **CO-110（L2 施加）参考平面入 CO-87 矩阵 + CO-106 D 读径修复 + In4 走廊空洞按设计定案（R5'）** + **CO-111（L2 量化）In5 PCIe 走廊参考缺失 = 40.1%（1094.8/2727.3mm）；L5 未签阻抗 ⇒ 外部终判** + **CO-112（L2 声明）3 bridge zone = B.Cu 桥（step ②c）+ In5 区域条件参考口径 + 走廊 worklist** + **CO-113（L2 施加）SPEC rev-14：裁定写入 canonical SPEC；几何与板逐字节不变** + **CO-115（L2 更正）In4 走廊空洞 = 失效 keepout 残留（待 L3 派生），非按设计；归属界面 = L1（owner）**）

> 契约 `m13_v57_w3_kickoff_card_v1_28.md`（冻结，未改 `0ae3016379cd1db2`）｜引擎 rev **W3-CN.41**
> ｜**取代 v1.37**（本件补 CO-59：**残余②（B.Cu/In6 并行）机器闭合 PASS** + **口径出处再基** —— 机判 `route_model_config.json` 证 1.08 是 `channel_alloc.pitch_fallback`（回退值）**而非要求量**；要求量语义 = R3-2 **铜边 0.875**，1.46 为其在冻结铜跨 0.585 下的换算 ⇒ CO-58「走廊与冻结口径一致」结论**更正**：EAST 1.449 / WEST 1.050 在 1.46 与 0.875 两读数下**均不达标**）。
> 授权：CO-05..CO-56 各变更单 + **CO-59..CO-66（L2：口径对账 + 可达性/策略穷举 + B.Cu 承载审计 + LID 重入 ECN + 叠层厚度自洽推导）**；**L1 仅剩** 方案(b) 层数裁决 + **① 对间净空**（CO-57/59）；方案(a) 属 L2 自裁（执行清单见 CO-66 §3）。**CO-74 补授权（L2 PDN：B.Cu 电力铜退役 + In4 承载；`CO-72-PDN-1` 归口 L1→L2 并闭合）**。**冻结四源未动（4/4 MATCH）**。里程碑 tag `k2-v57-g7-l5-pass`（k2 `b5afe47`）。

## 1. 收口结论（机器可判 + 工件可独立重算）

> **本轮（CO-67..CO-69，L2 叠层分配自裁）**：① **CO-67** 一次性裁定「方案(a)（In5 GND→信号）vs 历史红线」= **L2**（机判不变量：层数 8、平面数 4、电源域划分 3×GND+1×P3V3、信号层 4 **全不变**）`m13_v57_CO67_L2_redline_ruling.md` `c562419d70a41ab9`；
> ② **CO-68** 修正 CO-66 铜厚口径（介质预算 1.425 = 1.6-0.175）⇒ 设计点 w_outer 0.205 / **w_inner 0.16**、闭合 1.6000（标准料 2116 / core 0.25）⇒ **LID REV6** `05009687a3f01583` + **SPEC rev-5** `1f351194b3e22b7e`；
> ③ **CO-69** 引擎 bump（`LAYER_PALETTE`=F/In2/**In5**/B、In6→In5 全量、`CO16-ALLOC.7` `a765af4c9bf61e64`、rev W3-CN.41）+ **全链重导**（G4 `87ef07f280e4dffb` / G5 PASS / G6 板 `0e636a67c1472462` / G7 DFM new=0 + SI PASS）；
> ④ **SI 判据升级**为**按层加权电气长度**（CO-62 §4）：升级前 max skew **0.9807** > 0.15 ⇒ FAIL（REFCLK1：P 全 F.Cu vs N F.Cu+In2 8.745mm）；**L2 等长整改**（补偿目标由物理长度改为电气长度）⇒ max **0.1300** ≤ 0.15 ⇒ **PASS**；物理量报告 max 1.1046mm（层补偿之预期；判据为电气/时延）。
> ⑤ **对抗评审**（执行者侧独立证伪探针 A1..A9：不变量/阈值不变/闭合/阻抗/引擎无 In6/板按层线宽/冻结/独立重算等长/DFM）= **全 PASS（10/10）** `m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`（CO-76 加固 A5 + CO-79 空真加固/A10 守卫负控；原 `50ff390f2803f25d`、`6daec5df8bf0d118` 已取代）；**非执行者双路对抗评审**：pass 1/2 = CO-76；**pass 2/2 = CO-85 已完成**（`m13_v57_co85_nonexecutor_review_pass2.json` / `m13_v57_CO85_nonexecutor_adversarial_review_pass2.md`；V1 全链 12/12 逐字节复现、V2 闸牙齿复核、V7 逐层几何独立复算、F1 更正、F2 新硬限）⇒ **双路闭合**（L2_STRUCTURE_v2.0.md:137）。
> ⑥ **① 再判（handoff §6.2 子项）**：在方案(a) 现状下复跑 CO-60/CO-61，**逐字节复现**（`m13_v57_co60_corridor_pitch_frontier.json` `e2d74c7afaae0d45` / `m13_v57_co61_l2_search_exhaustion.json` `b4ef0063188b6ec6`，二者 `baseline_faithful=true`）：西侧 >1.05 落位破裂、东侧 1.580 可落位但越板边、无策略维解 ⇒ **① 负结果不变**。理由：落位(r1/r3)为**面内几何**、信号层数不变（4）、走廊/通道输入冻结 ⇒ 层集 In6→In5 不改变 pitch 可达性。① 仍属 **L1 包络冲突**。
> ⑦ **CO-70（L2 等长窗口裁定）**：对内 skew **判据 = 按层加权电气长度**（mm-eq @ er_ref=3.99），**物理长度为报告量、非并列闸**：CO-62 §5.2「保留物理长度判据」= 保留**报告**。证据：电气 max 0.1300 ≤ 0.15 PASS；物理 9/34 页 >0.15（max 1.1046@REFCLK1）属层补偿之预期；同时满足物理+电气需 2 变量（P 蛇形置 In2 ≈8.745mm + 2 过孔，N 蛇形置 F ≈9.849mm@REFCLK1）——额外铜/过孔、SI 劣化，非默认。记录 `m13_v57_CO70_L2_si_skew_criterion_ruling.md` `f104a102ae2a2caf`。
> ⑧ **CO-72（L2 PDN）**：SPEC **rev-6** `9e8fb5bae4a33207` —— `pd.gnd_planes`/`zone_defs.gnd_planes` 的 GND 平面由 **In5→In6**（LID REV6：In5=信号、In6=GND），解耦规则文本与 REFCLK In2 判据理由同步更正；**几何不变性机判**（route_geometry/pages/decision_contract/layers 逐字节同）+ 全链重基线 PASS。并登记既有冲突 `CO-72-PDN-1`（`pd.power_zones[2..4]` 的 **B.Cu 铺铜** vs 8L B.Cu 信号层，重规划属 **L1 电源域/层数**，仅登记不擅改）。记录 `m13_v57_co72_pdn_align.json`。
> ⑨ **CO-73（L2 PDN/叠层分配）**：SPEC **rev-7** `a15ffcd104d82f43` —— 层角色声明**一致性终扫**（当前态，不动历史件）：`pd.zone_defs.gnd_stitch_via`（note + 各 coordinates[*].basis）32 处『GND 回路由 **In1/3/5** 平面承担』→ **In1/3/6**；`constraints.j2_escape_topology.outer_basis` 更正『B.Cu 释放给低速』（REV6 下 B.Cu=高速信号层、由 In6 参考）；`layer_plan.in6_usage` 更正为 REV6 In6=GND 平面；`layer_plan.strap_domain_v32.deps` 平面清单补 In6。**几何不变性机判**（route_geometry/pages/decision_contract/layers 逐字节同）+ 全链重基线 PASS。记录 `m13_v57_co73_layer_role_consistency.json`。
> ⑩ **CO-74（L2 PDN，归口更正）**：**`CO-72-PDN-1` 由 L1 更正为 L2 并闭合** —— 机判前提消失：引擎 `LAYER_PALETTE=F/In2/In5/B`（In4 非布线层）+ 交付板 **`In4.Cu` 段数 0** ⇒ 6L 时代『In4 走线带 x∈[50,88.17] 阻断跨带铜皮』不存在，T2-ECN-1/2 绕行前提失效 ⇒ **B.Cu 电力铜（`power_zones[2..4]`）全部退役**、改由 **In4 承载**；`power_zones[3].in6_segments`（REV6 下 In6=GND ⇒ 短路）一并退役。6L 几何原样留存 `retired_*_bcu`（禁止静默放弃）；新几何 = L3 施工确定性派生。**SPEC rev-8** `3ec8e35e676cf89d`；**L2 不变量全不变**（层数 8 / 平面数 4 / 域集合 3 / 信号层 4 / `power_plane_layer=In4.Cu`）⇒ 属 L2（CO-67）；备选 b（增设电源层）/c（B.Cu 信号改层）仍属 L1，未选。**几何不变性机判 + 全链 G4..G7 全 PASS、板逐字节同**。记录 `m13_v57_co74_pdn_bcu_rehost.json` `8e3bbfb0e197cf67` / 链 `m13_v57_co74_chain.json` `51dbb2076bc379e4`（CO-76 F1 后重基；原 `9b1a284d2bb61e67` 已取代） / 卡 `m13_v57_CO74_L2_pdn_bcu_rehost.md` `8c1cec7fb48ad2ab`。
> ⑪ **CO-75（L2 走廊分配/过孔策略 · 负结果）**：补足 CO-60/61 的**未覆盖维** —— 二者 WLO 恒钉 33.70（单旋钮）；WSTEP=1.580 下 lane 块仅跨 11.06mm 而板边可用带高 45.2mm ⇒ WLO 是独立自由度。以**真发射器**扫 `WLO(12) × WSWAP/COLMODE(3) × FANY_J3(5) × HOLE_GAP(3) = 23 组合`，**0 组 32/32 落位**（保真断言：1.05@33.70 = 32/32 PASS）；失败签名恒在芯片输入 via 区 `x∈[84,93]/y∈[50,58]`（`vt_intra`/`pad_via`/`vv_placed`/`vt_placed`，行扫 1.4e4~1.8e4 耗尽）⇒ **球栅逃逸硬限**，与 WLO/fan 旋钮无关。**① 仍维持 L1**（剩余自由度 = 逃逸层重导/球重映射/落列/板框/层数）。记录 `m13_v57_co75_west_pitch_origin_search.json` `c59e9955d344d75f` / 卡 `m13_v57_CO75_L2_west_pitch_origin_search.md`。
> ⑫ **CO-76（非执行者侧对抗评审 pass 1/2，CO-67..CO-75）**：宪法 `L2_STRUCTURE_v2.0.md:137` 要求重开层重过对抗评审，CO-69 仅执行者侧。本会话与 CO-67..73 执行者**非同一会话** ⇒ 具非执行者资格。**发现 3 项并修复**：**F1（中）** 引擎把陈旧层角色 `up=In6.Cu` 写进**生产图纸** `decision_contract.r1_5_layer_rule`（REV6 下 In6=GND，而实现本即 `up->In5.Cu`）⇒ 与 CO-72/73 同类缺陷但落在引擎/图纸；**F2（中）** CO-69 A5 只断言**带引号** `"In6.Cu"`，CO-68 改字面量后恒真 ⇒ 结构上漏检**未加引号**层角色文本（实测 14 处裸 `In6`）；**F3（低）** 10+ 处注释与同行代码矛盾。修复 = 文本类零几何（11 处改 In5；A5 改**裸 token 扫描** + 豁免 `In6->In5` 迁移注）。**机判 11/11 PASS** （C1..C11：层集/图纸字段/板层卫生/探针/引擎输入/①负结果/四源/while-free/阈值/rev-8 PDN）。全链重基线 G4 `22c2a158` / G5 `eac5eee6` / G6 板**逐字节同** `0e636a67` / G7 DFM new=0 + SI 0.1300；delta 精确 = `pages`/`route_geometry` 逐字节同、`decision_contract` 仅一字符串。记录 `m13_v57_co76_nonexecutor_review.json` `cf5b4ec0e880e5d2` / 卡 `m13_v57_CO76_nonexecutor_adversarial_review.md` `32d5868a1a2880b4`。**残余：pass 2/2（另一非执行者）仍欠**。
> ⑬ **CO-77（L2 声明一致性）**：把 CO-76 的判据扫到**收口声明件** —— boundary 中凡以「现行/主件/交付」口径引用的 sha16 必须等于当前实际文件。机判 `tools/p3_v57_co77_closure_declaration_sweep.py`（12 项身份断言）实测 v1.41 **4 项陈旧**：§6-1『现行 L4 板』`cdcb869e9827ec87`（实为 `0e636a67c1472462`）、§1 ⑤ 执行者对抗评审记录 `50ff390f2803f25d`（实为 `6daec5df8bf0d118`）、§1 ⑩ 链记录 `9b1a284d2bb61e67`（实为 `51dbb2076bc379e4`）、§1 CO-69 卡 `d472f16e73a57f3e`（实为 `661ad6c57e0e2418`）；且 v1.41 §1 与 §7 互不一致（同一工件两个 sha）。**本件全部校正并显式标注历史**，扫描 v1.42 = **PASS/0 陈旧**。记录 `m13_v57_co77_closure_declaration_sweep.json` / 卡 `m13_v57_CO77_closure_declaration_sweep.md`。
> ⑭ **CO-78（L2 声明一致性 · 回归闸）**：把 CO-72/73/76 的缺陷类固化为**可重复闸** —— 当前态工件中「平面层当信号层」或「信号层当平面层」的角色声明一律 FAIL（口径：signal=F/In2/In5/B；GND plane=In1/In3/In6；PWR=In4）。范围 = boundary §2 现行输入 + 链输出 + 引擎源码（共 22 件）。结果：**当前态 0 flag（PASS）**；阳性对照（历史 `SPEC_k2_v4_8L_LID1.json`，LID.1 下 In6=信号层）**DETECTED**（`/stackup/In6.Cu` = `"signal (PCIe + escape)"`）⇒ 闸有齿。**自检教训**：首版 walker 只扫字符串*值*，漏掉 `key->value` 编码的角色声明（对照件 0 命中 ⇒ 无齿），修正为同时扫 key 后才成立 —— **无阳性对照的闸不得宣称有效**。⇒ CO-72/73（SPEC）+ CO-76（引擎/图纸）+ CO-78（全范围闸）**关闭 F1 缺陷类**。记录 `m13_v57_co78_layer_role_drift_gate.json` `1235a9a957fcc0cd` / 卡 `m13_v57_CO78_layer_role_drift_gate.md` `0185363ec8ddf5f7`。
> ⑮ **CO-79（L2 验证质量 · 空真加固）**：把 CO-76 F2/CO-78 的教训（断言只查"它恰好知道的东西" ⇒ 未知输入被静默跳过）系统审计 A1..A9，发现并修 3 处空真路径：**H1 A6** `wmap.get(L); if exp is not None` ⇒ 线宽表外的层被静默跳过；**H2 A8** `sqer()` 未知层静默 `return 2.0`（伪装 er=4.0）且未断言真测到页面；**H3 A2/A4** 无覆盖下限。加固 = 守卫纯函数（`width_coverage_guard`/`map_scope_guard`/`numeric_floor_guard`/`unknown_layer_guard`）同时用于实检与负控；A6 另**显式计数**被跳过的 PCIE 过孔（实测 **252**，原静默）。新增 **A10 守卫负控**：坏输入必被抓到（如 `width_coverage_guard({"F","In6"},WM) → (False,['In6.Cu'])`），好输入必通过 ⇒ 守卫**自带可执行牙齿证明**。套件 **10/10 PASS**。记录 `m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de` / 卡 `m13_v57_CO79_probe_vacuity_hardening.md`。
> ⑯ **CO-80（L2 可审计性）**：`k2_v4_8L.l4.kicad_pro` 是**受控**工件且被 `kicad-cli` 对 L4 板 DRC 时**自动选取**，但其设计规则与工艺意图不一致（`min_track_width` 0.09→**0.2**、`min_via_diameter` 0.35→**0.5**、`min_via_annular_width` 0.075→**0.1**、`min_through_hole_diameter` 0.2→**0.3**、`min_copper_edge_clearance` 0.3→**0.5**、`min_clearance` 0.1→**0.0**；另 4 项 silk/copper/via severity 由 ignore 变 warning）⇒ **最自然的独立命令**报 **880 条违规**（annular_width/drill_out_of_range/track_width/via_diameter 各 199 + copper_edge 11 + silk 警告），审计者会误判板子不合格。**先证伪自己**：在正确 staged（工程=意图件 + `.kicad_dru`）下用外部工具独立重跑并自算多重集差 —— 基线 42 / L4 42、**new=0 / disappeared=0** ⇒ 项目 DFM 判定被外部复现，880 条确系**规则设置产物**。**修复** = 把意图规则/severity 对齐进 `.l4.kicad_pro`（`62132712a65853b0` → `4704dec4dd043c59`，方向为采用意图件既有值，**未放宽任何阈值**）；修复后最自然的命令实测 42/42、new=0。**链不受影响**：板 sha `0e636a67` 不变、DFM `40445f87`/SI `73f9b59e` 逐字节不变、L4 applier 不覆写工程文件。记录 `m13_v57_co80_l4_project_rule_align.json` `d617a4c5e4e4523f` / 卡 `m13_v57_CO80_l4_project_rule_align.md`。
> ⑰ **CO-81（L2 可审计性 · 回归闸）**：把 CO-80 的 F-80-1 固化为闸 —— 每个**受版本控制**的 `*.kicad_pro` 的 DRC 设计规则必须等于**红线规则源** `_shared/eda_core/drc_rules.json`（`manufacturing` + `hole_clearance:min`，7 项，含键映射 `min_via_annular_width↔min_annular_width`），且 `rule_severities` 必须等于 JLC 模板 `tools/k2_jlc_template.kicad_pro`。理由：`kicad-cli` 对 `<board>.kicad_pcb` **自动选取**同名 `.kicad_pro`，规则不符则最自然的独立核查命令大面积误报。结果：**5/5 受控工程文件 PASS**（含模板与 CO-80 修复后的 `.l4.kicad_pro`）；牙齿：负控（`min_track_width=0.2`）抓 1 项、**历史对照 = F-80-1 修复前实测原值 → 抓 6 项失配**，即闸对真实发生过的缺陷状态可复现报警。记录 `m13_v57_co81_project_rules_gate.json` `a9161a86271c068b`（历史·CO-82 补网类后；原 `1f25c6a9db6923f0` 已取代）/ 卡 `m13_v57_CO81_project_rules_gate.md`。
> ⑱ **CO-82（L2 可审计性 · 补闸）**：`k2_v4_8L.l4.kicad_pro` 的 **net_settings 与意图件不一致** —— 仅 `Default` 一个网类、**`netclass_assignments` 为空**（意图件 4 类 + **146 条指派**），且 `Default` 自身偏严（clearance 0.2 vs 0.1、track 0.2 vs 0.09、via 0.6/0.3 vs 0.35/0.2）⇒ 用该受控文件跑 DRC 时 **PCIe85/LOW_SPEED/POWER 语义完全不生效**。**本件同时自认**：CO-81 的闸只覆盖 `design_settings.rules` + `rule_severities`，**未覆盖 `net_settings`**，故这条同类缺陷从闸下漏过 —— 本件一并**补闸**（新增 `netclass_guard`：按网类名逐字段 + 指派全量比对；模板显式豁免网类检查并记录理由）。修复：`.l4.kicad_pro` `4704dec4dd043c59` → **`ce2c2bf0da79a1ff`**（网类 1→4、指派 0→146）。**关键验证**：对齐后用最自然的命令重跑 = 基线 42 / L4 42、**new=0**，即施加完整 netclass 语义后板仍零新增违规 ⇒ 缺陷确系工件层；链不受影响（板 `0e636a67` 逐字节不变、DFM `40445f87`/SI `73f9b59e` 不变）。闸结果 **5/5 PASS**，牙齿：F-80-1 原值抓 6 项、**F-82-1 原状态抓 4 网类键 + 146 指派失配**。记录 `m13_v57_co82_l4_project_netclass_align.json` `0c8745064785ee57` / 闸 `a9161a86271c068b` / 卡 `m13_v57_CO82_project_netclass_gap.md`。
　同时**补强 CO-77 闸**：由「12 项 claim 模式」扩展为**全量 sha16 引用校验**（文中任何 `file` `sha16` 必须等于实际文件，除非显式标注历史或为「before → after」记法）—— 起因是发现 CO-82 卡片 sha 曾被写错而旧闸覆盖不到；v1.47 **65 条引用全数匹配 PASS**，牙齿：v1.46（引用被取代的 CO-81 闸记录）判 **CITATION_MISMATCH**。过程中我首次写该正则时双重转义致其匹配为空、v1.46 反而 PASS（**又一次空真**），已改正并加**非空真下限** `CITE_FLOOR=30`。
> ⑲ **CO-83（L2 可审计性 · 补最后一向）**：工程文件闸此前只比「工程 ↔ 意图工程」，未与**红线条文**交叉校验。本件令工程网类的 DRC 相关字段（`LOW_SPEED.clearance/track_width`、`PCIe85.clearance/track_width/diff_pair_gap/diff_pair_width`、`POWER.clearance/track_width`）必须等于 **SPEC `net_classes`**。结果：**0 失配**（PCIe85 clearance 0.175 / width 0.205 / p_gap 0.175 / p_width 0.205 等全中）。**疑似分歧已排除**：工程 `PCIe85.track_width=0.205`（标量）vs SPEC 内层交付 0.16 —— SPEC `p_width_scope` 已显式声明为设计意图（CO-68 对称叠层 85Ω 闭合），非缺陷。牙齿：**SPEC 侧负控**（篡改 `PCIe85.clearance`→0.2）被抓到 `[0.175, 0.2]`；连同 CO-81/82 的规则/网类负控，工程文件闸现覆盖 4 向（rules↔红线规则源 / severities↔模板 / net_settings↔意图工程 / **net_settings↔红线 SPEC**）。记录 `m13_v57_co81_project_rules_gate.json` `adba2152d4f10fd4`（CO-83 时值为 `ebd163058efaad14`，已取代） / 卡 `m13_v57_CO83_netclass_vs_spec_gate.md`。
> ⑳ **CO-84（L2 可审计性 · 放宽域闸）**：`k2_v4_8L.l4.kicad_dru` **放宽**逃逸区净距至 0.075（SPEC ECN-001）；**放宽类规则作用域过宽会掩盖真实违规**，故其必须与授权来源逐项一致。本件四向机判：净距（SPEC `escape_clearance_mm` = 域工件 = dru `min 0.075mm`）、域集合（dru `intersectsArea` = 域工件 `domains[].id` = **板内 4 个 rule area 名**）、层（全 F.Cu）、REFCLK 排除（域工件 `excluded_nets` = dru 条件）、溯源（dru 注释引用 sha256 = 域工件实件）、几何（域工件 `rect_mm` 与板内 zone bbox **逐值一致** tol 1e-6）—— **0 失配**，即放宽范围恰好等于被授权域。牙齿：4 个定点负控各命中 1 项（作用域过宽 / 净距 0.075→0.1 / 丢 REFCLK 排除 / 矩形漂移）。过程中自捕获一次**我自己的比较口径错**（`rect_mm` 序 `[x0,y0,x1,y1]` vs 我构造的 `[minx,maxx,miny,maxy]`）—— 归一后 0 失配，否则会把「一致」误报为「不一致」。记录 `m13_v57_co84_dru_domain_gate.json` `6f1a2ccfaf916627` / 卡 `m13_v57_CO84_dru_domain_gate.md` `996bee590912e823`。
> ㉑ **CO-85（非执行者侧对抗评审 pass 2/2）**：对象 CO-67..CO-84（含 pass 1 因执行者身份排除的 CO-74/CO-75）。**V1 全链复现**（handoff §9 命令，G4→G7）：**12/12 交付件逐字节一致** —— drawing `22c2a15835857f99`（**CO-89 重基线后已取代**，现 `3d452429bbc934c3`；板/DFM/SI 仍逐字节同）、板 `0e636a67c1472462`、DFM `40445f87be664f31`、SI `73f9b59ed5f6f3ce` 等；**CO-89 已按新基线重跑全链并机判几何不变（板逐字节同）**；非执行者 pass 2/2 对**新基线**的复评仍欠（CO-85 复现基线随 rev-9 失效）；applier 复跑确为落盘重写（mtime 更新）非缓存短路；`git status` 零 tracked 漂移。**V2 闸牙齿**：co77（61/71 引用、floor 30、0 mismatch）/ co78（0 flag + 历史 LID.1 阳性对照 DETECTED）/ co81 / co84（4 定点负控各命中 1）/ co69 A1..A10 全 PASS。**V3 板事实独立直解**：2523 段（In4/In6 = 0）/ 252 via / zone 4 个全为 ESC_ 规则域 ⇒ **铜 zone = 0**。**V4** SPEC rev-8：power_zones=In4.Cu、`bcu_power_copper_policy=PROHIBITED`、`escape_clearance_mm=0.075`、`inter_pair_spacing_mm=0.875` 未放宽。**V5** CO-75 负结果独立复跑（23 探针 / 0 命中，基线 32/32）。**V6** 图纸 lane.y 独立复算：EAST 1.449（铜边 0.744）/ WEST 1.050（0.345）；1.580 重锚 ⇒ EAST y_max 80.284 > 78.5975 ⇒ 越板边 ≥1.687mm。**V7 逐层对间几何独立复算**：In5 0.550/+0.345、In2 0.580/+0.375、B 0.550/+0.345 **复现**；**F.Cu 实测 0.4921/+0.2871（板）/ 0.4627/+0.2577（图纸）**（见 F1/F2 与 §6-6）。**F1（中）**：原 F.Cu 行 1.124/+0.919「达 0.875」**不可由任何口径复现**（含全局/走廊内/长并行/水平等 7 种口径）⇒ 违反层数 **3/4 → 4/4**，文本已更正（零几何/零阈值）。**F2（高，裁决相关）**：J2/J3/J4 **焊盘节距 0.6mm** ⇒ 焊盘场同层对间铜边净空上限 0.6−0.205 = **0.395 < 0.875** ⇒ R3-2 作绝对规则在连接器引脚场**几何不可达**（与走廊轨距无关）。**自我捕获**：S1 via 首计 256≠252（`(vias` 记号误计，改精确块解析）；S2 intra-pair 伪 0.0（未排除同网共享端点）—— 均自捕获。本件零几何/零阈值/零冻结源改动，**不做 L1 裁定**。记录 `m13_v57_co85_nonexecutor_review_pass2.json` / 卡 `m13_v57_CO85_nonexecutor_adversarial_review_pass2.md`。
> ㉒ **CO-86（L2 自裁 · 走廊分配/叠层 SI）**：机判 handoff §6.6 Q1 的「备选」（铜跨 0.705→0.585 使 1.46 给 0.875，原注「L2 但需重定 8L 阻抗」）是否成立。判据闭式：**对间铜边 = 走廊轨距 − 铜跨 ⇒ 需 pitch ≥ span + 0.875**；硬上限全部取自 CO-85 独立实测（WEST 1.050 / 焊盘场 0.600 / EAST 1.449，机判保真断言）。结果 **`n_pass_all_caps = 0`**：span 0.705→需 1.580（WEST 差 +0.530、焊盘场 +0.980）；span 0.585（SPEC p_gap，w 不变）→需 1.460（WEST +0.410、焊盘场 +0.860）；gap 0.175 且重解 w 回 85Ω：外层 span'=0.561→需 1.436（WEST +0.386）、内层 span'=0.407→需 1.282（WEST **+0.232**、焊盘场 **+0.682**）。**焊盘场 0.600 < 0.875 与 span 无关 ⇒ 恒不可达（L1 级硬限）**；牙齿：可行 span 区间 [0.407, 0.705] 以 1µm 网格**全量**验证所需轨距 > WEST 上限（真下界非抽样）+ 3 项保真断言。附加发现：备选非免费 —— gap 0.295→0.175 在 w 不变下 Zdiff 88.4/82.0 → **81.9/74.1Ω**（内层出 85±10% 带）⇒ 须重解 w/叠层 + 券。⇒ **L2 侧无出口**；R3-2 0.875 只能由 L1 或红线口径修订解决。记录 `m13_v57_co86_l2_span_option_closure.json` `d0a59f85b74687d5` / 卡 `m13_v57_CO86_l2_span_option_closure.md` `0d1fd3b33fb802fe`。
> ㉓ **CO-87（L2 自裁 · 合格标准覆盖性）**：按《宪法》ch.5 §4（数学闭合：容量/长度/过孔/**PDN 压降**）与 ch.2（L2 裁判含 **热**）机判覆盖性：**CLOSED 3**（容量 `verdict=FEASIBLE_ALL`/failed=[]；长度 SI skew 0.13 ≤ 0.15；过孔 L4-F True/over=[]/total 252）+ **NOT_DEMONSTRATED 2**（**PDN 压降**、**热**：SPEC rev-8 全字段扫描 **0 命中**，扫描字段 3962）⇒ 显式登记为已知限制（§6-8），**不宣称 PASS、不判 FAIL、不以假设值代填**。牙齿：合成件注入 `load_currents` ⇒ 命中 ≥2（证明 0 命中是真缺）；宪法文本确含 `PDN 压降达标`（证明条款存在）；非空真下限 = 实扫 3962 字段；记录复跑逐字节一致。所需输入清单由 SPEC `power_zones[*].targets` **机器提取**。⇒ 本件不改变 G4..G7 判定，不触 L1；缺的是**数据**（PM/owner 提供），不是拓扑裁决。记录 `m13_v57_co87_l2_acceptance_coverage.json` `46d15557477d164b` / 卡 `m13_v57_CO87_l2_acceptance_coverage.md` `322baa098740b259`。
> ㉔ **CO-88（L2 自裁 · PDN 板实性）**：机判 `pd.zone_defs.power_pad_connect` 与 `pd.decoupling(_via_to_plane)` 的**板实性**（这三者是机读且被 `pdn_apply.py` 消费的铺铜决策）—— 三项全 **FAIL**：**A** 55/173 entries + 2 blocked 引用板上不存在的 ref（35 孤儿：C65-C72/R4-R12/R17-R27/**U3**/**U7**）；**B** 板实 SMD 电源/地 pad **309** 个，现行 SPEC 仅 118 覆盖 + 7 blocked ⇒ **184（60%）静默待定**（违 ch.5 §1）；**C** `pd.decoupling=C67_C68_C72_via_to_plane` 的 **3/3 ref 板上不存在** ⇒ 解耦规则零板实落点，而板实去耦集（C74-C83/C84/C90，见 `components.must_add`）无解耦决策。根因可追溯：红驱动 **U3(DN)+U7(UP) → U6(DS320PR1601, 354 球)** 合并，ppc 冻结基准自述为「101 fp 重建板，U3=DN/U7=UP」，从未板实化。**修复候选已派生**（项目自带确定性发生器 `pad_connect_gen` 对交付板重生成，scratch 即用即删）：entries 173→**223**、blocked 9→**86**、决策总数→**309/309=100%** 覆盖；候选 blocked 中 **U6 占 63/86**（GND 球在 0.5mm 球栅场内落不下 pad→via，属规则允许的显式 blocked；改判为可连接则需器件资料+SI/PI 依据）。**本件只判定+备料、不施加**：施加 = SPEC **rev-9** + 全链重基线，波及 **27 个文件**（引擎 `FROZEN_SHA`/validator/`co69` 探针/`co77` 引用闸(钉 `spec-rev-8`)/`co84`/`co81/83`/L4/L5），会重基线**刚过非执行者评审（CO-85）**的链 ⇒ 按冻结/评审纪律须作**独立变更单 + 重新过对抗评审**（禁 partial pass）。自我捕获：首版以正则数板实 pad 得 127（漏 U6 354 球 BGA 块），改用 pcbnew 真值 309 方得正确分母，否则会把 184 个无决策误报成 9 个（假 PASS）。本件不改 SPEC/板/阈值；不触 L1（3 域/4 平面/8 层不变）。记录 `m13_v57_co88_pdn_board_reality_gate.json` `17719cf7f8e3e702`（CO-88.3；原 `f90d65369cab92dc` 已取代） / 卡 `m13_v57_CO88_pdn_board_reality_gate.md` `50aa8c67d7b10438`。
> ㉕ **CO-89（L2 自裁 · PDN 板实化 / SPEC rev-9）**：施加 CO-88 的修复候选。**SPEC rev-9** `77f5c54df88bb0ca`：① `pd.zone_defs.power_pad_connect` 对**交付板**重生成（entries 173→**223**、blocked 9→**86**、决策 **309/309=100%** 覆盖、**0 孤儿 ref**）；旧 173/9 条（含 55 孤儿 entry + 2 孤儿 blocked）转 `retired_superseded_bom` 留存对账（不销毁可追溯性）；② `pd.decoupling` 由 `C67_C68_C72`（板上不存在）改为**板实按网集合**（P3V3{C74-C84}/MCU_VDD{C85,C86}/12V_IN{C88}/P3V3_AUX{C90}，机器派生），旧串转 `decoupling_legacy_retired`；③ `decoupling_via_to_plane.vias`（旧 C67/C68/C72 坐标）转 `retired_vias_superseded_bom`，改 `targets`=板实去耦集 + `geometry_status=L3_CONSTRUCTION_DERIVED`（坐标留 L3，不臆造）。**不变量机判**：L2 不变量（层数 8 / 平面 4 / 域集合 3 / 信号层 4）全不变，且 `pd` 以外**逐值等于 rev-8**（unexpected=[]）⇒ 属 L2。**全链重基线**：G4 `3d452429bbc934c3`（几何段与旧基线**逐字节同**，唯一 delta=`inputs_sha.spec`）/ G5 PASS frozen=True `7acb3186c3b68848` / G6 PASS viol 0（**板逐字节不变 `0e636a67c1472462`**）/ G7 DFM new=0（`40445f87be664f31` 不变）+ SI 0.1300（`73f9b59ed5f6f3ce` 不变）。**闸态**：co78 `b736a0df7226f155` / co81 `16b262663238a60a` / co84 `b927acbe46ec3007` 均 PASS（已随 rev-9 重扫）；co87 3 CLOSED/2 open 不变（扫描字段 3962→5995）；**co88 由 FAIL → PASS**（A/B/C 全过：0 孤儿 / 223 覆盖 + 86 显式 blocked / 解耦目标全板实）；co69 探针 10/10（`18a86c998dd6b4de` 不变）。**残余（如实）**：① 86 blocked 中 **U6 占 63**（0.5mm 球栅场内 GND 球落不下 pad→via；改判为可连接需器件资料+SI/PI）；② 本次重基线使 CO-85 复现基线失效 ⇒ **新基线非执行者复评欠**；③ PDN 压降/热仍缺输入（CO-87）。记录 `m13_v57_co89_pdn_board_realize_rev9.json` `4f94df5981aaab45`。
> 记录 `m13_v57_CO69_L2_option_a_chain.md` `661ad6c57e0e2418`（原 `d472f16e73a57f3e` 已取代）。**注意**：`CO-60` 候选 `..._v6.json`（`2ebda54c…`）为走廊 1.580 实验件，**未触碰**。
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`；`status` PASS。
- **A-CN 全 PASS**：1d 32/32、1a 0 miss、1b 0、2a/2b 0、3a 72/72、3b/3c 0、4 交叉 0、5a keepout 0、
  5b 页间 True、**5d REFCLK 同层交叉 0（P/N + 页间）**、6 序无关（验证器 3 枚举序 byte-identical）、
  7 重发射 satisfied、8 证书归因 0 unattributed、**9 完整净距 0/0/0（tt/vt/vv）**、method `work 546/546`。
- 规模：**34 页**（32 data 含 3D nodes + 2 refclk）、`route_geometry` **320 段**、页级 via **320**、`same_layer_crossings = 0`。
- REFCLK 2/2：见证 `kind=direct_channel`；图纸内 P/N 残余 skew **0.0**（P 轨等长幂绕补偿 3.5635/1.3635 见 CO-45）；
  板上 SI 实测 max intra-pair skew **0.0031 ≤ 0.15**（34 页全查，含 REFCLK）。
- F-12 原子重发射 `m13_v57_w3_chip_landing_rows.json`（64 行），`authority.main_sha256 == sha256(主件)`。
- **字节可复现（CO-49）**：L4 板 `cdcb869e9827ec87`；构建×3 与全链（构建→L4→L5）×2 均**逐字节一致**（板/construction/validation/fab/dfm/si/G7 记录 共 7 件）。
- **PDN 事实核验（CO-50）**：平面层为**保留层、尚未铺铜**（冻结源与 L4 的铜铺铜 zone 均为 **0**，机器统计）；L4 仅新增 4 个非铜 rule area + tracks ⇒ 无平面铜被改写（原 `planes_present` 断言已改为可机判事实）。
- **DFM 判据强化（CO-51）**：`new` 由「按类型计数差」升级为**多重集差**（键 = type + 参与者 description）⇒ 同类型对调不再被掩盖；并显式机判**基线消失项 = 0**（即验收项「无 <0.075 项消失」），实测 new=0 / disappeared=0。
- **过孔预算闭合（CO-52，宪法第五章第 4 条）**：L4-F 逐网对比 SPEC 显式上限（bandX 4 / bandY 6 / REFCLK 2）⇒ 实测 max 4 / 4 / 2，**全部合规**；`total_vias = 252`（68 网）。
- **⚠ 阻抗几何开放项（CO-53/CO-54）**：交付 34/34 对对内中心 **0.500**（边距 0.295）vs SPEC `diff_pair.p_gap 0.175`；对间最小中心 0.550（SPEC `inter_pair_spacing_mm 0.875`）；SPEC `stackup/impedance` 仍 **6L** 而板为 8L ⇒ 阻抗符合性原判 `NOT_DEMONSTRATED`（CO-55 后见下）。
- **CO-54（本件新增）**：把 CO-53 从单点扩展为**机判漂移清单**（audit `ba87413ae4d8c7b4`）：F2 对间最紧 0.550@In6 长平行带（29.1mm，归因更正）、**F3 SPEC 自身不自洽**（`net_classes` 派生 PITCH 1.46 vs `corridors.tracks_y` 1.20，Δ0.26）、F5 三处“85Ω 基准”互不同（79.9 vs 85.1 vs JLC 官方 prepreg εr）、F6 34 对中 32 对的决定性平行段在 **In2/In6（带状线）**而 SPEC 模型为微带、F7 交付对内 0.5/0.6/0.58 并存；交付步距集合 {0.5,0.55,0.58,0.6,1.2,1.45} 与 SPEC 三项（0.175/0.875/1.2）**无一自洽**。**门判定不变**（零几何/阈值改动）。
- **CO-55（本件新增，L2/SI 自裁）**：由**交付几何反解 8L 叠层要求**（不再索取板厂表）：`d(F.Cu–In1.Cu)=0.1164`（JLC 2116×1）、`d(In5.Cu–In6.Cu)=0.0994`（3313×1）、`b(In1.Cu–In3.Cu)=0.72`（对称 0.36+0.36 core）；余隙按 1.6mm 闭合（机判 delta=0.000）。此叠层下交付各档（gap 0.295/0.395…）落 **82.1–91.2Ω ⇒ 全部 85±10%**（一阶 IPC-2141，datum 85.05 vs 85.1）⇒ **几何零改动、无需 re-open**。回退：若板厂 b<0.582 则 In2 须按 `w*(b)` 重导（表见 CO-55 §4 R2）。**B.Cu 判非阻抗控制层**（参考层为信号层 In6）；In6 下方 B.Cu 不得并行铺铜/走线。**CO-53/CO-54 的输入缺口取消**（改下达要求 + 板厂券终判）。**已由 CO-56 落盘**。
**已由 CO-56 落盘**（见下）。
- **✔ CO-58（本件新增，L2/L3 对账 · 更正 CO-57 表述）**：并排换算四档口径 —— R3-2「0.875」（v1.1 requirement）/ v22 容量口径 1.46（=0.585+0.875）/ **冻结轨距 1.08**（v2.0 硬约束 2「冻结轨距仍 1.08（实际排轨居中值）」+ `mcio_learning_gate.md` §4.2「模板参数（生产过/结构冻结）track_pitch 1.08」）⇒ 铜边 **0.495** / 交付走廊 1.20+0.705 ⇒ 铜边 **0.495**（**与冻结口径同值 ⇒ 走廊不构成对冻结口径的偏离**）/ 交付芯片侧 In6 带 1.05+0.705 ⇒ 铜边 **0.345**（低于冻结 0.15）。⇒ **更正**：CO-57 的「交付违约 R3-2」属表述过当；0.875 在 v2.0 语境是 **capacity 口径**，实排轨距冻结值 = 1.08。**收窄待裁**：**Q1（L1）** R3-2 是 realized 要求还是 capacity 口径（realized ⇒ 需 1.580 全链重导，几何可行 12.64<N16.2/S20.8；capacity ⇒ 仅芯片侧 In6 带需重导至 ≥1.08）；**Q2（L2-ready，待 Q1 定标）** 芯片侧 In6 带重导。见 `m13_v57_CO58_interpair_baseline_reconciliation.md` `267621cdcfae1bbc`。
- **✔ CO-59（本件新增，L2 自裁 · 残余闭合 + 更正 CO-58 基线）**：① **残余② 闭合 PASS** —— L4 板 B.Cu×In6 并行耦合 **0 对**（夹角≤10°/重叠>0.3mm/横向<0.5mm），全板最小并行横向距 **20.3mm**，B.Cu 实体 70 段/32 网/**0 zone**，与 In6 为**垂交**关系 ⇒ CO-55「不得并行」已满足。② **口径再基（机判）**：`route_model_config.json` `71c001125959b24b` 的 `capacity_audit.inter_pair_spacing=1.46` + note「语义 = 0.875 对间铜边净空」为**要求注入点**；**1.08 是 `channel_alloc.pitch_fallback`（回退值）** ⇒ CO-58 以 1.08 为基线的「走廊一致」结论**成立性不足**。③ **交付板级实测**：EAST 对间距 **1.449**（铜边 0.744：vs 1.46 **−0.011** / vs 0.875 **−0.131**）、WEST **1.050**（铜边 0.345：**−0.410 / −0.530**）⇒ **两读数下均不达标**；CO-57 的 0.345 事实保留。④ 四方口径互不自洽（SPEC `tracks_y` 1.20 / SPEC 派生 1.46 / config 1.46 / 文本「口径统一 1.46」/ 模板 1.08）⇒ 收窄为 owner 单一问句：**是否授权走廊对间距 → 1.580**（= 0.705+0.875，歧义无关目标，同时满足 1.20/1.46/0.875；带高 7×1.580+0.705 = 11.765 ≤ N16.2/S20.8）。见 `m13_v57_CO59_L2_residual_closure_and_interpair_target.md` `0fdb19fec39bf110`；附：CO-54 audit 在 rev-4 下已重基线为 `69fcbcdd19025874`（v1.27/CO-58 引用的 `ba87413ae4d8c7b4` 为 rev-3 值，本件更正引用而不改工件）。
- **✔ CO-60（本件新增，L2 走廊分配 · 可达性机判 / 负结果）**：lane 步距为合法 L2 旋钮（重发 ALLOC.5 **逐字节复现** `0bf6cdc203887a48`）。冻结包络内机判：**西侧对间距 >1.05 即落位失败**（余量 <0.05；失败集中于芯片逃逸区 x≈93.2 球栅，`PCIE_UP6/UP7 input`，行扫 15148~15150 耗尽）；**东侧 1.580 可落位 32/32 且放置净距 0 违规**，但全链 **G4/G5/G6 PASS、G7 DFM FAIL new=84（copper_edge_clearance 83）** ⇒ 破板边铜距；**恢复冻结对铜跨 0.585（POL_OFF 0.19）⇒ 0/32 落位**。⇒ R3-2 realized 0.875（⇒ 中心距 1.580）在冻结 L1 包络内**不可达**，两端皆 L1 决策 ⇒ **L1 冲突**，依《LAYOUT_CONSTITUTION》第三章第 2 条升 owner。见 `m13_v57_CO60_L2_corridor_pitch_reachability_and_L1_conflict.md` `71dfd8f7d9dcd96d`。
- **✔ CO-61（本件新增，L2 · 策略维穷举 / 负结果）**：把搜索从"单旋钮"扩到 L2 **策略维**：① 西侧 对间距{1.20,1.46,1.58} × {无/有落列交换} × {colmode pol/默认} **9/9 全部落位失败**（失败点均为芯片逃逸区，行扫 ~15150 耗尽）⇒ 与策略无关，受**球栅逃逸硬限**；② 东侧 1.580 在 4 个走廊平面锚定（EDELTA −0.10/+1.0/+2.0/+3.0）下：3 个可落位但走廊 y_max 80.5~82.6 **越板边可用上限 78.5975**，第 4 个起 J2 侧逃逸落位失败 ⇒ **无可行锚定**（东侧 1.580 需 24.4mm > 可用 22.3mm）。⇒ L2 侧无可再自裁动作，L1 冲突成立。见 `m13_v57_CO61_L2_search_exhaustion_and_L1_conflict.md` `e11ef05202a578c6`。
- **✔ CO-62（本件新增，L2/SI 裁定 · 负结果）**：补核 CO-55/CO-56 残余条款**前半句**（「B.Cu 不得承载阻抗关键网」）。机判：本阶段 **68 条高速网中 32 条**在 B.Cu 上有铜，合计 **290.21mm**，单网最长连续 **17.87mm**；差分对 **P/N 的 B.Cu 长度失配最大 1.443mm**（5 对同值，系统性）。一阶 Zdiff（同 CO-55 模型）：F 88.4 / In2 82.0 / In6 85.5 均落 85±10%，**B.Cu 单参考(In6 信号层, h=0.1836) = 119.1Ω ⇒ 超出带（+34）** ⇒ B.Cu 无法承载 85Ω。二阶：层混合致电气 skew 一阶 0.03~0.16mm 内层等效（悲观档超 0.15mm 预算），现有 SI `skew`（纯物理长度 0.0031）**未覆盖**该机制。⇒ **L2 裁定：维持并强化 CO-55 条款，现交付违反**；整改 = 16 张 dn 带页逃逸/stub 层移出 B.Cu（LID 新修订 + 全链重导 + SI 判据改按层加权）。见 `m13_v57_CO62_L2_Bcu_impedance_carrying_ruling.md` `691ed6991c9957fe`。
- **✔ CO-63（本件新增，L2 → 更正为 L1）**：按 L2 权限直接试做 CO-62 的整改（层分配）：两个 **B.Cu-free** 逃逸层计划均 **FAIL** —— A（dn→In2/up→In6）**18/32 落位 + 1 违规**；B（east→In6/west→In2）**12/32 + 11 违规**（违规均为 F.Cu 段-焊盘 `sp`）。根因：4 信号层中 F.Cu 被 SMD 焊盘占用、In6 为 lane 层（逃逸入 In6 必自交）、In2 已给西侧逃逸 ⇒ **B.Cu 是唯一剩余逃逸资源**，其使用是**承载性**的。⇒ **更正 CO-62 的定层**：该项整改**不能由 L2 完成**，根因是「外层 B.Cu 无邻接平面」这一**包络/拓扑**事实 ⇒ **第二项 L1 冲突**。见 `m13_v57_CO63_L2_Bcu_free_layerplan_infeasible.md` `50f1c0913788044d`。
- **✔ CO-64（本件新增，L2 叠层分配 · ECN）**：依 L2_STRUCTURE_v2.0.md:126「8L 重入 ECN 触发条款」（三条实质条件已由 CO-60/61/63 机判成立）发起 ECN。根因：冻结派生 `total=2*L_signal` + 家族 `F/G/S/G/[P/G]/S/B` **必然**使最外层 B.Cu 无邻近参考平面，而 B.Cu 又是逃逸所需第 4 信号层 ⇒ 自相矛盾。叠加修正规则（每信号层须有参考平面）后重推：**8L 有解但须重排平面位置**（与冻结平面用途红线冲突，属**电源域划分=L1**）；若保留冻结平面用途则最小 **10L**（`F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(G)/In6(S)/In7(G)/In8(S)/B(G)`，B.Cu→GND，多 1 层内部信号层，对 ① 亦有利，属**层数裁决=L1**，文档 :136 明文）。⇒ 两项 L1 冲突统一为二选一决策。见 `m13_v57_CO64_L2_LID_reentry_ECN_stackup.md` `02051da11ce89e7f`。
- **✔ CO-65（本件新增，L2 收口 + L1 决策请求）**：①**修正 CO-62 铜厚口径**——B.Cu 按外层 1oz（t=0.035）重算为 **113.0Ω**（CO-62 记 119.1Ω，结论同为超带），且达 85±10% 需 **d(B.Cu–邻平面) ≤ 0.127mm**（现 0.1836）⇒ 仅加参考平面不够，叠层**厚度**亦须重推。②**机助证明 8L 不可兼得**：冻结平面 4 层 + 需 4 信号层恰为 8 层，而 B.Cu 唯一邻层是 In6 ⇒ B 有参考则 In6 必为平面，与 In6∈信号层矛盾；穷举全部 6561 个层序列，满足条件的 8L 解 16 个、**保留冻结平面用途的 0 个**。⇒ 两条整改：(a) 8L 重排平面用途（板厂成本不变，须放宽平面用途红线）/ (b) 8L→10L（保留全部平面用途、多 1 层内部信号层对 ① 亦有利，属层数裁决）。**建议 (b)**。见 `m13_v57_CO65_owner_decision_brief_stackup.md` `f1306a91ce8c98a4`。
- **✔ CO-66（本件新增，L2 叠层分配 · 归口更正）**：**更正 CO-65 §3** —— 方案(a) 层数/平面数/电源域**均不变**（仍 3×GND + 1×P3V3 同网），只改平面**位置与厚度** ⇒ 属 **叠层分配 = L2**（与 `L2_STRUCTURE_v2.0.md:136` 一致）；**仅方案(b) 需 L1（层数裁决）**。并经机判给出 8L 对称叠层（`F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)`）的**厚度自洽解**（10 组可行；例：外层 w=0.205/h=0.1101，内层带状线 w=0.130/b=0.4134，自由余隙 0.553，1.6mm 闭合，各层 85.0Ω）⇒ 代价 = **内层线宽 0.205→0.13~0.19 的几何协同变更**。执行清单（LID REV6 / SPEC rev-5 / 几何重解 / 引擎 bump / G4..G7 / SI 按层加权 / 重新对抗评审）见 CO-66 §3。见 `m13_v57_CO66_L2_option_a_stackup_derive.md` `72ec6c4dbdb4a75c`。
- **⚠ CO-57（本件新增，L1 升级 · owner 待裁）**：L1 冻结强条 R3-2『**对间铜边净空 ≥0.875mm**』（`L1_TOPOLOGY_v1.0.md` 硬约束 3 / `v2.0.md` 硬约束 2「口径统一 = 1.46」，v22 用户裁决）vs 交付实测：走廊轨距 **1.200**（−0.260）、对内铜跨 **0.705**（使 1.46 只给 0.755 净空）、对间最紧铜边 **0.345**（In6 长平行带）。按现行铜跨满足 R3-2 所需中心距 = **1.580mm**（8×1.580 = 12.64 < N16.2/S20.8 ⇒ 几何可行但需全链重导）。三选项：**A** 重开 W3 走廊至 ≥1.580（L1 裁，触及落列/球行派生走廊行）/ **B** 回退铜跨 0.705→0.585 恢复 1.46 口径（L2 可执行但与 CO-10 裁定冲突）/ **C** 正式修订 R3-2 阈值（**L1/owner 明示**）。**本件零几何/阈值改动、不预判**；裁定前**不得声称对间间距合规**。见 `m13_v57_CO57_L1_escalation_interpair_clearance.md` `e99f58e06730daaf`。
- **CO-56（本件新增，L2/SI 自裁 · SPEC ECO rev-4）**：`SPEC_k2_v4.spec-rev-4.json` **`1c4eecb0edf4a446`**（**纯加性**：8L 声明 + `stackup.dielectric_8l` 逐层介质表 + `impedance.per_layer` 分层口径 + `p_gap_semantics=lower_bound`/`inter_pair_spacing_scope`；**所有数值阈值未改**）。同步 bump：引擎 `F.spec`/`FROZEN_SHA`、validator 冻结集、L5 记录 rev **L5-SI.5**。**几何不变性机判**：新图纸 `4e7497daf97cebd1` 与原 `dfa1d7c4a811b0da` 的 `route_geometry`/`pages`/`decision_contract`/`layers`/`method` **逐字节相同**（仅 `inputs_sha`/`frozen_sha_check` 指纹重基线）；**板 `cdcb869e9827ec87` 逐字节不变**。**复跑**：G4 FEASIBLE_ALL、G5 PASS（frozen=True）、G6 PASS（viol 0）、G7 PASS（new=0 / 在册未连 0/68 / skew 0.0031）；**重跑零漂移（不动点）**。PI 项状态 → `DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`（终判=板厂券）；**残余**：对间串扰复核（0.345 vs 基线 0.875）与 B.Cu 非阻抗控制层声明（见 CO-54 F2/F3）。

> ㉖ **CO-93（L2 自裁 · PDN 权威净距重落 / SPEC rev-10）**：CO-91 判 rev-9 计划坐标违反冻结规则源（via 83/312、短段 75/223）后，**依 LAYOUT_CONSTITUTION 第二章自裁 L2**（via 策略/PDN 承载属 L2，不升 owner）：① 一律按权威口径重落（`required=max(netclass a,b,board_min)` + `min_hole_clearance` + **层语义**，via 亦为障碍、支持盲/埋孔）；② **无合法位者转显式 `blocked`**（**不放宽任何阈值**；旧坐标退役留存 `retired_superseded_clearance_v1`）；③ **不默认采用 via-in-pad**（需工艺能力 + SI/PI 证据）；④ pad→via **短段宽度 0.5 → 声明 0.2mm**（= `min_track_width` 可制造下限），短段不合法则该 pad 亦 blocked（`entries` 语义收紧为「整条连接合法」）；⑤ 候选 palette **声明固定、确定性序、无坐标搜索**（原位 → 4 正交 @(via_r+0.3) → 4 正交 @0.6）。**SPEC rev-10** `4416e42eed10cb8c`：ppc entries **223→189** / blocked **86→120**（决策覆盖仍 **309/309**；**已连接 223→189，−34 如实登记**）、`gnd_stitch_via` 69→**40 落（28 原位+12 移位）/ 60 blocked**、`power_zones[].vias` 20→**17（+4 移位）/ 3 blocked**；`pd` 以外**仅 `spec_version` 变**。**验证**：CO-91 对 rev-10 **PASS（via 246 目标 0 违规、短段 189 目标 0 违规、牙齿 4/4）**；CO-92 对 rev-10 = **不动点**（189/0/0、40/0/0、17/0/0）⇒ 声明策略自洽稳定。**全链重基线**：G4 `FEASIBLE_ALL` `9c099dd7ba0c3478`（几何段逐字节同，delta=`inputs_sha.spec`）/ G5 PASS frozen=True `c6a9e0fd4291a8b3` / L4 construction `3f8aa96b4f39a793` + val `fbe5d7a72c08860`（viol 0）/ G7 fab `4586dd4263d9e9cb` + **DFM new=0（`40445f87be664f31` 不变）** + **SI 0.1300（`73f9b59ed5f6f3ce` 不变）**；**板逐字节 `0e636a67c1472462` 不变**。**闸态（随 rev-10 重扫）**：co78 `3609268f4267053a` / co81 `ecb12c992ae514a3` / co84 `49e0aa218527daac` / co87 `21b740182f4a2869`（3 CLOSED/2 open 不变）/ co88 `679de2b7a23b8885` PASS / co69 10/10（`18a86c998dd6b4de` 不变）。**残余（如实）**：① 已连接 −34（多为 U6 0.5mm 球栅场电源/地球）在冻结 8L 通孔工艺下无合法连接位 ⇒ 保连接数需 via-in-pad（工艺）或 HDI/微孔（**L1：层数/叠层**）；② `_shared` 引擎（容器副本**只读冻结**）未改 ⇒ rev-10 生成器 = k2 决策层工具，引擎通用化 + `gnd_stitch_gen` 障碍集改实际铜 + `pdn_apply` 短段宽度读 SPEC 登记为后续；③ **本次重基线 ⇒ 非执行者复评欠（CO-94）**。记录 `m13_v57_co93_pdn_rev10_derive.json` `663cb40e827984dd` / 卡 `m13_v57_CO93_pdn_rev10_authoritative_clearance.md` `9d9aaab835ba31a9`。

> ㉗ **CO-94（L2 自裁 · PDN 可连接性闭合判定 + 裁定）**：rev-10 把 34 个 pad 转 `blocked`（已连接 223→189）后，L2 必须回答「在 L2 手段内（外部通孔 + F.Cu 短段，**不含** via-in-pad / HDI）这 34 个是否真的不可连接」。以**存在性判定**（宽松有限家族：8 向 × r=0.30…1.80 step 0.05；判据 = CO-91 同一权威检测器，via **且** 短段合法）逐 pad 取最小可行半径：**全部 120 blocked 中 28 可连 / 92 不可；本轮关注的 34 中 15 可连 / 19 不可**。**裁定 = 维持 `blocked`**，三条理由：① 可连位只存在于**未声明的 31 档半径搜索式家族**中（且 **7 个仅在家族上限 1.80mm 命中**）⇒ 采用即把「搜索」写入决策，**违「零坐标搜索 / 一次求解」红线**；② 可连者净距余量低至 **0.0136mm（13.6µm）**、短段余量低至 **0.012mm**，属「规则内、工艺外」贴线解；③ 需 **1.35–1.80mm** 长 F.Cu 短段穿越 0.5/0.6mm 节距球栅场（电感/回流一阶影响，未经 SI9000/券），换 15 pad 不划算。⇒ **34（及 92/120）在 L2 手段内判为不可连接**（`blocked` 为诚实处置，非 PASS）。**升级（L1/工艺）**：U6（0.5mm 节距 354 球）与 J2/J3/J4（0.6mm 节距）的 blocked 电源/地球若须连接，只能靠 **via-in-pad（板厂工艺能力 + SI/PI 证据）** 或 **HDI/微孔（层数·叠层裁决，属 L1）** ⇒ 监理升级人工。记录 `m13_v57_co94_blocked_recoverability.json` `617e0973e6132e46` / 卡 `m13_v57_CO94_blocked_recoverability_ruling.md` `cbfb27c1f0db0fc5`。

> ㉘ **CO-95（L2 自裁 · PDN）In4 平面可达性 + 陈旧 keepout band 退役 / SPEC rev-11**：`power_pad_connect.entries` 的 via 必须落在**本网 In4 铜**上才构成真实连接，而既有闸（CO-88/89/90/91）**只判引用/覆盖/净距**，无闸判**平面可达性**。机判（`co95_in4_reachability`，牙齿 2/2）55 个 power entry：**35 `covered_explicit` / 8 `covered_bridge_target` / 6 `l3_obligation` / 6 `needs_region_ruling`**。**L2 裁定**：① `in4_pcie_keepout_band` 的启用前提（「wp1_escape_nets 在 In4 有 14 段走线」）**已被 CO-74 判定失效**（引擎 palette 无 In4 / 交付板 In4 段数 0 / layer_plan 仅把 In4 声明为 PDN 平面）⇒ **退役**（band 范围 + void 理由留存 `retired_in4_keepout_band_6l`）；② 废止 `P3V3_EAST` 由 band 推导的西界（88.17+0.2），改由**「与异网 In4 铜边 ≥0.2mm」**决定、落点 L3 派生；③ 新增 `plane_reachability_requirement`（via 须被本网 In4 铜覆盖 / 同网连续 / 异网 ≥0.2mm / L3 确定性派生）；④ 登记残余 12 项。**效果**：6 个 U6 P3V3 球（AC17/AC20/AK17/AK20/T17/T20）原被失效 band 排除在 In4 之外 ⇒ 退役后转为 **L3 可达性义务**。**SPEC rev-11** `d85f10f722ba22b0`（`pd` 外仅 `spec_version` 变）。**验证**：G4 `FEASIBLE_ALL` `e0a4dfd7936372f9` / G5 PASS frozen=True `a252ba52d0d05442` / L4 viol 0 `09ed9530f6da65f3` / L5 fab `afe849cfd5228515` + **DFM new=0（不变）** + **SI 0.1300（不变）**；**板逐字节 `0e636a67c1472462` 不变**；闸态 co78 `25f72d58a6a68b06` / co81 `8e7f4108610d4a5d` / co84 `18ffce1d876f53fc` / co87 `f9fd3f87cea224b0` / co88 `4db0a5d796d75f28` 全 PASS、co69 10/10 指纹不变、**CO-91 对 rev-11 PASS（0/0）**、CO-92 对 rev-11 不动点、CO-95 = `OPEN_needs_region_ruling`。**升级（一句话，L1/区域划分）**：6 项 `needs_region_ruling` ⇒ `12V_IN` **无任何 In4 区**（C88.1/U2.4/U2.6，且板上无该网铜）需裁承载；`P3V3_AUX` 西侧 3 pad（C90.1/R1.2/U1.15）所需区域与**西区名义网 MCU_VDD** 冲突需裁归属。记录 `m13_v57_co95_in4_reachability.json` `4525e38330ee599f` / `m13_v57_co95_spec_rev11_band_retire.json` `0ec682d3d15f84d5` / 卡 `m13_v57_CO95_in4_plane_reachability.md` `0bdac108e4563238`。
> ㉙ **CO-96（非执行者侧对抗评审 pass 4/4 · 对象 rev-11）**：独立会话（非 rev-10/rev-11 执行者）对 CO-91/92/93/94/95 + 全链 + 不变量做对抗复核，判 **`REVIEW_DONE_FINDINGS_OPEN`**（基线身份 OK / 牙齿 OK）。**指定三问**：Q1 `plane_reachability_requirement` **不可机判闭合**（几何真覆盖仅 35/55，14 待 L3、6 待 L1；gate 恒不返回 PASS）；Q2 两次重基线间**有 1 处未登记漂移**（F1）+ 1 处陈旧（F5）；Q3 CO-95 分类**完整**（55=35+8+6+6）。**6 项发现**：**F1**（中·谱系/红线邻近）rev-10 重建 ppc 时**静默丢弃** CO-89 的退役留存键 `retired_superseded_bom`（pre-rev-9 冻结 BOM 173/9 + 孤儿 55/2；`p3_v57_co93_pdn_rev10_derive.py` 零引用、变更说明未登记）⇒ 现行谱系断链，数据可由冻结源 + CO-89 记录找回；**F2**（中）可达性要求为「声明可闭合」——8 个 `covered_bridge_target` 命中桥区 `polygon=None`（几何未建）；**F3**（中）`needs_region_ruling` 对 P3V3_AUX 西侧 3 pad 依赖 `why` 自由文本子串（改文本即 L1→L3 静默降级）；**F4**（中）可达性 scope 仅 ppc entries，`gnd_stitch_via` 实落 40 / `power_zones[].vias` 17 无闸；**F5**（低）`board_realized` 仍记 223/86（决策 189/120，未被 pdn_apply 消费）；**F6**（低·潜在）co95 `in_poly` 用 bbox 非真 PIP（现行 polygon 均轴对齐矩形 ⇒ 无实害）。**复核 OK**：V1 rev-9→rev-10→rev-11 `pd` 外**递归深比 0 变更**；V2 分类完整；V3 SPEC stitch blocked schema 与 `pdn_apply` **对齐**（60 跳过/40 施加；§6-16「schema 未对齐」仅指上游 `gnd_stitch_gen`）；V4 gnd_stitch 重复坐标 (133.83,59.1)×2 系**声明共享单孔**（非缺陷）；V5 冻结四源 4/4 MATCH。**只读；不改 SPEC/板/阈值/冻结源/引擎；F1 须 rev-12 变更单闭合。** 记录 `m13_v57_co96_nonexecutor_review_pass4.json` `8b591e5030aca11d` / 卡 `m13_v57_CO96_nonexecutor_review_pass4.md` `56d1a1b421dda943` / 工具 `p3_v57_co96_nonexecutor_review_pass4.py` `4fc740b459624691`。
> ㉚ **CO-97（L2 自裁 · 可审计性）退役留存完整性闸 + 显式登记册（关闭 CO-96 F1 的『静默』面）**：把红线「退役几何/决策必须**显式留存**（不得静默放弃）」固化为**可重复机判闸**——逐版枚举退役留存块（首段含 `retired`）、逐相邻版本求 drop，**任一 drop 必须在登记册显式登记**（键 + `from_rev→to_rev` + reason + recovery），另拒**陈旧登记项**与**不可解析找回指针**；另带牙齿 3/3（未登记 drop 必抓 / 已登记必放行 / 陈旧项必抓，均合成注入）。**L2 自裁**：选 CO-96 F1 的『**或显式登记其移除**』分支，而非为纯溯源字段单独重基线——该键与 `board_realized` **均不被 `pdn_apply` 消费**（无几何/功能影响），重基线会使刚出具的 CO-96 证书失效并新增复评债 ⇒ **不成比例**；「SPEC 内回填」列为可选后续、随下一次构建期 SPEC bump 一并处理。**结果**：退役块 rev-8 5 → rev-9 8 → rev-10 13 → rev-11 15；**drop 恰 1 处**（`power_pad_connect.retired_superseded_bom`，rev-9→rev-10）**已登记 + 3 条找回指针全可解析** ⇒ **verdict PASS**（undeclared 0 / stale 0 / recovery_bad 0）。**附带**：登记册显式记 `board_realized` 为 CO-89 派生记录（非现行决策），消除 CO-96 F5 的误读。**零 SPEC/板/阈值/冻结源/引擎改动**；不重跑链路。**L2 自裁（`_shared` 处置）**：**不解冻冻结副本**；施工侧三项（`gnd_stitch_gen` 障碍集改交付板实际铜 / `pdn_apply` 短段宽度读 SPEC / blocked schema 对齐）**改由项目内引擎承载**，且**仅在 PDN 施工期激活**（当前板逐字节不变、PDN 未施工 ⇒ 非在役缺口）。记录 `m13_v57_co97_retirement_retention_gate.json` `4b1ee8924147a4f4` / 登记册 `m13_v57_retirement_registry.json` `4b13b538ba8e28ce` / 卡 `m13_v57_CO97_retirement_retention_gate.md` `2bc80fbe0c62bfd4` / 工具 `p3_v57_co97_retirement_retention_gate.py` `e9427f0f18087a18`。
> ㉛ **CO-98（L2 自裁 · PDN 可审计性）In4 平面可达性义务状态报告（机判化 CO-96 F2/F3/F4；关闭 F6）**：**F6 修复** —— co95 `in_poly` 由 **bbox 近似**改为**真·射线法 PIP**（工具 `tools/p3_v57_co95_in4_reachability.py` `4d87484ff2f1ecc7`，取代 `a2e16d6e08eef731`）；现行 2 个显式 polygon 均轴对齐矩形 ⇒ **输出逐字节不变**（co95 记录 sha 于该时点为 `61db48a283beeaae`（已取代；现行 = `f1c0c17ee7b379a4`），CO-95/CO-96 该次引用不失效）= **行为中性加固**。**F2/F4 机判化（不改 requirement；改 scope/谓词属 SPEC 变更 = 后续 rev-12）**：新增只读报告闸 co98（**不改 co95 记录字节**），输出 **三态** `geometric_covered` **35** / `declared_pending_l3` **14**（8 桥区 target 声明 + 6 band 退役义务，几何待 L3 派生）/ `ruling_pending_l1` **6**，`machine_closable_today=false`（verdict **永不 PASS**）；**scope 排除** `gnd_stitch_via_realized` **40** / `power_zones_vias` **17** / `decoupling_vias` **0**（本 requirement 只覆盖 ppc 非 GND entry）。**F3 裁决依据分解**：6 项 ruling 中 **5 机判可判**（3× `net_has_no_in4_region`(12V_IN) + 2× `via_inside_other_net_in4_polygon(MCU_VDD:MCU_VDD_WEST)`(P3V3_AUX 西侧 C90.1/U1.15)）、**1 仅文本**（`P3V3_AUX R1.2` @[51.725,37.0]）⇒ 建议改机判谓词并补 R1.2 判据。牙齿 2/2（PIP 拒 bbox 假阳 / 完整性抓计数不符）。**零 SPEC/板/阈值/冻结源改动**；**不改 co95 记录字节**。记录 `m13_v57_co98_reachability_status_report.json` `a29b802163bca3d9` / 卡 `m13_v57_CO98_reachability_status_report.md` `84a609e6f5e54503` / 工具 `p3_v57_co98_reachability_status_report.py` `2091c72253930b08`。
> ㉜ **CO-99（L2 自裁 · PDN 施工就绪性）计划集互相冲突闸 + 施工 dry-run（两个覆盖缺口）**：既有 PDN 闸（CO-88/91/92/95/98）与 CO-96 复评**都只判「计划几何 vs 板*已有*铜」** ⇒ 两处盲区：**G1** CO-91 `Scene` 仅由板构造 ⇒ **via-via / stub-via / stub-stub 互相零判**；**G2** 项目规则源 `drc_rules.json` 的 `hole_clearance.same_net_exempt=True` **不含** KiCad 板配置 `min_hole_to_hole=0.25`（net-agnostic）⇒ 同网 stitch 靠太近不可见。⇒ **CO-91 PASS 不蕴含可施工**。本件把工件驱动过真实消费面（`eda_core.pdn_apply` + `kicad-cli pcb drc`，scratch，交付板逐字节不变）：**verdict = `FAIL_MUTUAL_SHORT`** —— SPEC 宽 0.2 ⇒ **7 异网重叠（3 via-via + 4 stub-via）+ 35 净距 + 39 孔距（含 2 同址）**；引擎实落宽 0.5 ⇒ 13 + 127。7 个重叠全在 **U6 0.5mm 球栅场**（如 `P3V3@(84.775,53.5)` vs `GND@(84.574,53.59)`，d=**0.2202 < 0.35**）；2 同址孔 = CO-96 记为『声明共享单孔』的 `(133.83,59.1)`/`[47.0,49.0]`（声明可解释、`pdn_apply` 仍落两 via）。**施工 dry-run**：DRC **42→274（+232）**、未连 348→191（逐类型参考：clearance ~124–131 / shorting_items ~43–47 / hole_to_hole 37 / hole_clearance ~19–22 / holes_co_located 2）。**根因**：① 计划集互避缺失；② 短段宽 0.5 未读 SPEC；③ stitch 互距/去重缺失；④ 规则源缺 `min_hole_to_hole`。**修补未施加**（见 CO-100）。牙齿 2/2。记录 `m13_v57_co99_pdn_mutual_conflict_gate.json` `1d256de815b1ed87` / 卡 `m13_v57_CO99_pdn_mutual_conflict_gate.md` `c47249d3538c1d8c` / 工具 `p3_v57_co99_pdn_mutual_conflict_gate.py` `78762b3d9de90fd4`。
> ㉝ **CO-100（L2 自裁 · PDN）CO-99 互冲的互障感知修复候选 —— rev-12 能否自解？**：用与 CO-92 同一套**声明 palette**（ppc：current → pad 4 正交 @(R+0.3) → @0.6；stitch/zone：current → 原位 4 正交 @0.6）+ **互障 = 板已有铜 + 已接受计划件** + **孔距 net-agnostic ≥0.45**，按**声明固定序**确定性重放（零 while/零搜索）。**结果 = `PARTIAL`**：残余异网重叠 **0**（互冲可清）；ppc kept **124** / relocated **61** / blocked **4**，stitch 34/5/**1**，zone 13/4/0 ⇒ **5 项新增 blocked（4 ppc + 1 stitch）**（**CO-103 校正**：原记 kept 126 / relocated 58 / blocked 5 ⇒「6 项、全在 U6 0.5mm 场」为过期读数；CO-100 记录 tally 重跑**逐字节可复现**）。**裁定**：互冲本身 **L2 可解**。**CO-103（证据链校正）**：4 项 U6 ppc 新增 blocked 的自身 rev-11 位置对板铜**干净**，阻塞全为**同网 GND 相邻 U6 计划孔距互障**（d=0.180–0.403 < 0.45mm），另 1 项为 J2 扇出 GND stitch 同址重孔对 ⇒ 属**同网冗余竞争**，与 CO-94 的 120 项板铜阻塞**不同类**；固定序探针（同 palette/同检测器仅换序）显示 canonical 的 4 项为所试最优、但每对幸存成员随序翻转 ⇒「保连接数须 via-in-pad/HDI」**未被证明**。⇒ rev-12 决策点：`(a)` 显式登记接受 5 blocked（纯 L2）或 `(b)` L2 冗余归并裁定（相邻 GND 球择一/桥接）；**不得**未加证明即升 owner 取裁 HDI（层数）。**本件不施加**。记录 `m13_v57_co100_pdn_mutual_repair_candidate.json` `11e21f3b97bac66b` / 卡 `m13_v57_CO100_pdn_mutual_repair_candidate.md` `ff1c267f74f578dc` / 工具 `p3_v57_co100_pdn_mutual_repair_candidate.py` `341314590ceb154a`。
> ㉞ **CO-101（L2 自裁 · PDN 施加）rev-11 → rev-12 计划集互障重导**：把 CO-100 的候选**施加**为 SPEC rev-12 —— ppc entries **189→185**（kept 124 / **relocated 61** / **新增 blocked 4**；blocked 120→**124**）、`clearance` 按板侧 Scene 重算；stitch **relocated 5 + 新增 blocked 1**（原 60 blocked 保留）；power_zones vias **relocated 4**；rev-11 原坐标显式留存（`retired_superseded_mutual_conflict_v1` / `power_zones_via_retired_mutual_conflict_v1`，禁静默放弃）；**F5** `board_realized` 同步为 rev-12 决策数；**F1** 自 rev-9 回填 `retired_superseded_bom`。**验证**：G4 `FEASIBLE_ALL` `cb955e9af8782d08`（34 页/crossings 0/work 546/546）、G5 PASS frozen=True、L4 viol 0、L5 DFM new=0 + SI 0.1300；**板逐字节 `0e636a67c1472462` 不变**；**CO-99 由 `FAIL_MUTUAL_SHORT` → `PASS`**（重叠/净距/孔距 全 0）；CO-91 PASS、CO-92 `CANDIDATE`、CO-95/98 不变、co88/co97 PASS。**残余（非 PASS）**：引擎 `add_track(width=0.5)` 字面量 + 不去重 ⇒ dry-run 仍 **+34**（rev-11 = +232），属施工侧项目内引擎承载；**5 项新增 blocked（4 ppc + 1 stitch；同网孔距竞争，见 CO-103 F-B）** 需 L2 冗余归并或显式登记接受（**不得**未加证明即称需 via-in-pad/HDI）。**review debt = CO-102**（本件为执行者，不得自评；co96 对 rev-11 的证书随之失效、现按 fail-closed 报 BASELINE_MISMATCH）。零几何搜索（坐标全来自 CO-100 声明 palette 重放）；历史件不改。SPEC rev-12 `1a381b06454dbe2c`；记录 `m13_v57_co101_pdn_rev12_derive.json` `cdeea6a3950f04f6`；卡 `m13_v57_CO101_pdn_rev12_derive.md` `d47eda01e3092114`；工具 `p3_v57_co101_pdn_rev12_derive.py` `977ee54f0ecdb414`。
> ㉟ **CO-102（L2 自裁 · 项目内引擎承载）修正版 PDN 施加器 —— 施工侧闭合**：冻结 `_shared/eda_core/pdn_apply.py`（容器副本只读）有三处施工侧缺陷（① `add_track(..., width=0.5)` 字面量、不读 SPEC `stub_width_mm`；② via 不去重；③ blocked 口径）⇒ rev-12 dry-run 仍 +34。依既定自裁（**`_shared` 不解冻**、施工侧**改由项目内引擎承载**）新增**项目内**施加器：坐标**逐字取自 SPEC**（零搜索），仅修三处（短段宽 = SPEC `0.2`、via 去重 `(net,x,y)`、blocked 口径对齐）。**验证（scratch 三态 DRC，确定性）**：baseline **42** / 冻结引擎 **76（+34）** / 项目内引擎 **42（+0）** ⇒ **rev-12 PDN 施工 DRC-clean**；统计 = zones 5 / vias 241 / tracks 185 / stub_w 0.2 / deduped 0 / 跳 blocked 61。不改冻结副本/SPEC/板/阈值；`gnd_stitch_gen` 生成端缺陷不在在役路径（施工只用 SPEC 坐标）。工具 `p3_v57_co102_pdn_apply_local.py` `945b7ae7942102be`；记录 `m13_v57_co102_pdn_local_apply.json` `44002f7eac6cfa49`；卡 `m13_v57_CO102_pdn_local_apply.md` `1df2be1ef5fc0e64`。

> ㊱ **CO-103（L2 · 非执行者对抗复评）rev-12 新基线（对象 CO-99/100/101/102 + 链 pin + 收口声明）= `PASS_WITH_FINDINGS`**：9 项机判（V1 幂等重导逐字节 / V2 palette 归属+固定序独立重放 / V3 登记完整性 / V4 clearance 与 CO-91 一致 / V5 计划集互判 / V6 CO-102 发射集等价 + 三态 DRC 42 / 76(+34) / 42(+0) / V7 blocked 成因分类 / V8 声明漂移扫描 / V9 链 pin）**全过**，牙齿 7/7；**0 项 pin 漂移**。**发现**：**F-A（中）**声明漂移 —— 原记「6 项新增 blocked（5 ppc + 1 stitch，全在 U6 0.5mm 场）」实为 **5 项（4 ppc + 1 stitch）**，第 5 项在 **J2 扇出** `(133.83,59.1)`；v1.69 已校正。**F-B（高）**4 项 U6 新增 blocked 的自身位置**对板铜干净**、阻塞全为**同网 GND 计划孔距互障**（相邻 U6 GND 计划 via，d=0.180–0.403 < 0.45）⇒「须 via-in-pad/HDI」**缺乏存在性证据**（换序探针 8/13/13 且每对幸存成员翻转）；与 CO-94 板铜类不同。**F-C（中）**收口件 §1 ㉛/§6-20 的 co95 现行身份引用陈旧（`61db48a283beeaae` → 现行 `f1c0c17ee7b379a4`）、CO-96 证书未声明自身失效，且 CO-77 的 `CITE` 抓不到散文式引用；v1.69 已注明已取代。**另记**：同网孔距口径经**合成注入实测**验证（kicad-cli 对同网 GND 孔对报 `hole_to_hole`，0.080 < 0.2495）⇒ CO-99 A4 口径忠实。工具 `p3_v57_co103_rev12_nonexecutor_review.py` `5e3f91d39130b83a` / 记录 `m13_v57_co103_rev12_nonexecutor_review.json` `7f481be259865941` / 卡 `m13_v57_CO103_rev12_nonexecutor_review.md` `6ac046a885508dc6`。

> ㊲ **CO-104（L2 自裁 · 过孔策略/PDN）rev-12 新增 5 项 blocked 的裁定 = `ACCEPT_L2_NO_HDI`**：依 `LAYOUT_CONSTITUTION` 第二章（过孔策略 / PDN 承载 = L2；层数 = L1）对 CO-103 F-B 的 4 项 U6 ppc + 1 项 J2 扇出 stitch 作裁。**三条出路逐条量化**：**A 共享单孔**（两 pad 中心**中点**派生位 + 双短段；零自由度、非搜索）仅 **1/4 对**可行（`FB34~FA32` 可行；其余 3 对的中点正落在 U6 另一球 pad `FF11`/`FF18`/`E11` 上）⇒ 收益 = 1 个 GND 球；**B 改声明固定序**（同 palette、同检测器）canonical **4** vs 13 / 8 / 13 ⇒ canonical 已最优、无免费解；**C 加宽 palette / via-in-pad / HDI** ⇒ 违零坐标搜索红线（CO-93/94 已驳）/ 无工艺 + SI-PI 证据 / 属 L1 且本件已证「须 HDI」不成立。**裁定 = 接受**（与既有 120 项 blocked 同类处理，显式登记不静默），**不升 owner、不重基线、rev-12 不变**；本项**不再构成 L1 问题**（若日后要求「U6 GND 球 100% 独立 via」为硬需求，须走 SPEC 变更 + 全链重基线 + 换会话复评）。**附带加固（CO-103 F-C 收口，fail-closed）**：co96 默认落点改为**重跑件**，显式指向历史证书即**拒绝写入（rc=2）**，除非 `--overwrite-canonical`⇒ 历史证书 `8b591e5030aca11d` 不再会被静默改写；重跑件 `m13_v57_co96_nonexecutor_review_pass4_rerun.json` `636b1ad728f0fa91` 即 CO-96 失效的**机判化声明**（verdict `BASELINE_MISMATCH`，`co95_json` 61db48a283beeaae → f1c0c17ee7b379a4）。工具 `p3_v57_co104_pdn_blocked_ruling.py` `7b2f3ff18e0ede04` / 记录 `m13_v57_co104_pdn_blocked_ruling.json` `7254226692cb8f93` / 卡 `m13_v57_CO104_pdn_blocked_ruling.md` `ed2587023fe05ed6`。
> ㊳ **CO-105（L2 自裁 · PDN 建模）CO-96 F4 落定 = `CLOSE_NO_SCOPE_EXTENSION`**：把 CO-98 的「声明排除」机判化。**V1 语义不可适用**：requirement 判据 =「落于本网 In4 铜」，而 GND 平面层 = `In1/In3/In6`、In4 仅 `P3V3/MCU_VDD/P3V3_AUX` ⇒ 对 **130 GND ppc entry + 40 GND stitch via** 无可判定（≠『未覆盖』）；requirement 对象 = 非 GND ppc entry **55**。**V2 几何待 L3**：17 个 `power_zones[].vias` **17/17** 位于 3 个 bridge zone（`P3V3_BCU_BRIDGE_IN4` 3 / `P3V3_AUX_BCU_BRIDGE_IN4` 8 / `MCU_VDD_BCU_RESISTORS_IN4` 6），其 `polygons=[]`、`geometry_status=L3_CONSTRUCTION_DERIVED` ⇒ 与 CO-98 `declared_pending_l3` 同桶；扩 scope 只并入待派生清单、不新增可判缺陷。**V3** 施工路径对 `gnd_stitch_gen` 的**代码引用 = 0**（散文复盘 1）⇒ 生成端缺陷 latent、不在在役路径。**V4** `R1.2` 判据根因 = 电源域/区域归属 = **L1**（不在本件）。**裁定 = 关闭 F4，不做 scope 扩展**；零 SPEC/板/阈值/冻结源改动、不需重基线、不需新复评。牙齿 2/2（GND 平层不含 In4 而 In4 确被占 / 17 项空几何而存在有几何 zone）。工具 `p3_v57_co105_f4_scope_disposition.py` `f357f81142161e61` / 记录 `m13_v57_co105_f4_scope_disposition.json` `116f83fae67d1bb8` / 卡 `m13_v57_CO105_f4_scope_disposition.md` `c40b94566b0ba3e9`。
> ㊴ **CO-106（L2 · 合格标准覆盖性补全）参考平面判据 + 参考平面连续性机判 = `INDETERMINATE_REGION_SCOPED`**：ch.2 的 L2 裁判标准含「参考平面」，而 CO-87 记录**自报**的判据集含该词、覆盖矩阵却只有五行（参考平面无决策行/无闸）⇒ 本件补上判据并机判：**A 板框一致性**（声明多边形 = 冻结板框按 `edge_copper_min` 内缩）＋ **B 参考平面连续性**（每条规划走线每点须落在其 `impedance.per_layer[layer].refs` 任一参考层声明铜内；分类 `declared_copper_missing`（GND 整面层缺铜=缺陷）vs `region_scoped_indeterminate`（In4 按电源区裁剪/桥区待派生））＋ **C 板实佐证** ＋ **D 覆盖性补全声明**；牙齿 3/3（合成负控/正控）。**rev-12 判 `FAIL_DECLARED_COPPER_MISSING`**：60 点/36 段（In2 24 + In5 12）；根因 = 3×GND + 2×In4 多边形下边 **70.7 = 33+38−0.3**（旧 38mm 板框）而现行板框 `outline_y [33,79]`（v28 ECO y 38→46mm）⇒ 按自身 basis 应为 **78.7**；后果 = 框内平面外 **8.3mm 带无参考平面**，而施工已用该带（板实 **In5 316 段 + In2 12 段 + 24 via**，PCIe `PCIE_DN2..DN7` 蛇形恰在其中）。修复 = CO-107。工具 `p3_v57_co106_reference_plane_gate.py` `84eeea00d8e987cb` / 记录 `m13_v57_co106_reference_plane_gate.json` `9f131d72e4780afb` / 卡 `m13_v57_CO106_reference_plane_gate.md` `08b46fff2a07e45a`。
> ㊵ **CO-107（L2 自裁 · PDN/平面分配）SPEC rev-13 = 平面随板框对齐（CO-106 FAIL 的施加）**：把 3×GND(In1/In3/In6) + 2×In4(`P3V3_EAST`/`MCU_VDD_WEST`) 多边形下边 **70.7 → 78.7**（与各自 basis「整面铺铜 + 板边内缩 0.3」一致），rev-12 原多边形**退役留存** `pd.zone_defs.retired_superseded_frame_extent_v1`；**只改 polygon 顶点 + `spec_version`**（阈值/网/层角色/坐标集/短段宽/blocked 台账/冻结源未动）。**几何不变性机判**：新图纸 `route_geometry`/`pages`/`landing_rows` 与 rev-12 **逐字节同**（仅 `inputs_sha.spec` 与 `frozen_sha_check` 变）⇒ 板 **`0e636a67c1472462` 逐字节不变**。SPEC rev-13 `7943be727a4f8ef9`；G4 **FEASIBLE_ALL**（34 页/crossings 0/work 546/546）主件 `73c0066df83fa8c2`；G5 PASS frozen=True；G6 PASS viol 0；G7 FAB ok + DFM new=0 + 在册未连 0/68 + SI skew 0.1300；**CO-106 复判 → `INDETERMINATE_REGION_SCOPED`（`declared_copper_missing`=0）**；链 pin 同批前移（引擎 `/FROZEN_SHA`、validator `/prefix`+`FROZEN`、闸默认 spec co78/81/84/91/92/95/98/99/102/104/105/106、co77 正则）。**复评债 = CO-108（须另一会话）**。工具 `p3_v57_co107_spec_rev13_frame_align.py` / 记录 `m13_v57_co107_spec_rev13_frame_align.json` / 卡 `m13_v57_CO107_spec_rev13_frame_align.md`。
> ㊶ **CO-108（L2 · 非执行者对抗复评）rev-13 新基线 = `PASS_WITH_FINDINGS`**：独立（不复用执行者断言）机判六面全 True —— **A** rev-13 vs rev-12 标量差分恰为 10 polygon 顶点 + `spec_version`（无增删键）；**A2** 退役留存 5 项（`old_polygon`=rev-12 逐值 / `new_polygon`=rev-13 逐值 / 无 70.7 未登记 / 无残留）；**B** `route_geometry`/`pages`/`landing_rows` 与 rev-12 **逐字节同** + 板 `0e636a67c1472462` 逐字节不变 + frozen drift=∅；**C** 无工具仍以 rev-12 为现行（仅 CO-103 历史件合法持有 `1a381b06454dbe2c`）、记录内 `inputs.*_record` provenance pin 全数一致；**D** 参考平面独立**点级全量**重算 GND 整面层缺铜 **0**、残余 54 段/1260 点 **100%** 落 L3 桥带 x∈(49.8,88.37)；**E** rev-12 FAIL 独立复现（60 项/36 段；板实 (70.7,79.0] = In5 316 / In2 12 / VIA 24）⇒ CO-107 为真修复；**F** 牙齿 3/3。**发现**：**F-A（low，已校正）** CO-105 记录 provenance pin `inputs.co98_record` 在执行者提交态 `04d0ee1` 为 `267f86b5…`（非当时 co98 `48b5bd29…`、亦非任何已提交版本）⇒ 确定性重跑既有工具（无新代码路径）恢复一致，boundary v1.73 同批更新引用；**F-B（信息性）** CO-106 记录字段实计 (段,参考层) 项数而非采样点数（判据成立性不受影响）；**F-C（low，已声明）** co87 矩阵仍无「参考平面」行（登记册缺口）。**F-D（medium，未决前提）** 3 个 bridge zone `layer=In4.Cu` 但名含 `BCU`、`basis` 明文经 **B.Cu** 桥接（P3V3 明示『In4 走线带不跨』）⇒ CO-106 归 `region_scoped_indeterminate` 的『几何待 L3 派生』前提**未证实且与 basis 冲突**；须在 L3 桥区派生 work order 前先裁 bridge zone 派生层归属（若取 basis 口径则 54 段 In5←In4 为**永久**参考缺失 ⇒ 升级 L2 参考平面/阻抗裁定）。工具 `p3_v57_co108_rev13_nonexecutor_review.py` `a745c2695e92b0e6` / 记录 `m13_v57_co108_rev13_nonexecutor_review.json` `f1ff40a43614a9e8` / 卡 `m13_v57_CO108_rev13_nonexecutor_review.md` `a00d7d89a5106c7d`。
> ㊷ **CO-109（L2 自裁 · 参考平面/PDN）In5←In4 走廊空洞 = 按设计（非「待 L3 派生」）；bridge zone = B.Cu**：触发 = CO-108 F-D。客观证据：3 个 bridge zone（`layer=In4.Cu` 但名含 `BCU`、basis 明文经 B.Cu）声明的 3 条 band 仅覆盖 In5←In4 miss 点 **6.0%**（75/1260），而 In4 走廊 x∈(49.8,88.37) 覆盖 **100.0%**；板 L4 zone 数 0（平面未落）⇒ 无声明走廊 In4 几何可派生。**裁定**：**R1** 3 bridge zone 桥接层 = **B.Cu**（`layer` 字段仅 In4-可达性簿记）；**R2** 走廊空洞 = 按设计（basis 记 PM T2-ECN-1/2『In4 走线带不跨』）；**R3** 桥区几何派生**不能**清除 In5←In4 残余；**R4** ⇒ CO-106 `region_scoped_indeterminate` 前提不成立 —— 该带 In5 实为**仅 In6 参考**、与 declared `symmetric_stripline(refs=[In4,In6])` 不符，应改判『按设计 In4 空洞』并登记 SI 待验项（终判 = SI9000 + 板厂券，不得代填）；**R5（OWNER，停）** 走廊补 In4 铜 = 反转已记录 PM 裁决 ⇒ owner。**step ② 重定范围**：②a 声明修正（L2，新 rev 重基线）/②b 走廊 In5 SI 终判（外部）/②c bridge zone B.Cu 几何声明（L2，**缺 palette**）/②d 换会话复评。工具 `p3_v57_co109_in4_void_l2_ruling.py` `2e35c139476ae016` / 记录 `m13_v57_co109_in4_void_l2_ruling.json` `dd562f526705abef` / 卡 `m13_v57_CO109_in4_void_l2_ruling.md` `583ac243a4cf3428`。
> ㊸ **CO-110（L2 自裁 · 施加）参考平面判据入 CO-87 矩阵 + CO-106 D 读径修复 + In4 走廊空洞按设计定案（R5'）**：触发 = CO-108 F-C/F-D + 本件新发现 **F-E**。**(a) F-C**：CO-87 覆盖矩阵原 5 行、缺 ch.2 判据「**参考平面**」⇒ 补第 4 行（`INDETERMINATE`，证据机取自 CO-106 记录：`declared_copper_missing=0`、残余 `In5←In4` 54 段 = 按设计走廊空洞），新增牙齿 `ch2_criteria_all_have_rows=true`（n_closed=3/n_open=3）。**(b) F-E（新发现）**：CO-106 D 项原读 `co87["inputs"]["matrix"]`，而 CO-87 记录无 `inputs` 键 ⇒ `KeyError` 被吞 ⇒ 覆盖性检查**恒空真**、行缺失从未被校验；已改读 `constitution.ch2_l2_criteria` + 顶层 `matrix`，复跑后 `co87_has_reference_plane_row=true`。**(c) F-D/R5'**：**不开 In4 走廊铜 = 确认 PM T2-ECN-1/2 既有设计（非反转）** ⇒ CO-109 的 OWNER 升级**撤回**；In5 在该带 = **In6-单参考域**，SI 终判 = 外部。**零 SPEC/板/阈值/冻结源改动 ⇒ 不重基线**（先例 CO-105）。工具 `p3_v57_co110_l2_coverage_closure.py` `354aef88cdac7634` / 记录 `m13_v57_co110_l2_coverage_closure.json` `6564e51f6ade544e` / 卡 `m13_v57_CO110_l2_coverage_closure.md` `82d2b176d45d1527`。
> ㊹ **CO-111（L2 自裁 · 参考平面/阻抗）In5 PCIe 走廊参考缺失量化为 40.1%**：触发 = CO-110 关闭 F-D 后仍缺「量」。In4 走廊 x∈(49.8,88.37) 无声明 In4 铜 ⇒ In5 走线在该带的**长度** = **1094.8/2727.3mm = 40.1%**，受影响 **16 网全部为 PCIe 差分对**（`PCIe85`，target_zdiff 85Ω），最差 `PCIE_UP4` **108.7mm/50.5%**。**关键**：L5 SI 记录**只签 intra-pair skew**（`skew_ok=true` max 0.13mm）、**声明**阻抗模型但**无逐线阻抗核验** ⇒ 走廊内 In5 PCIe 阻抗暴露**未被现行 G7 签核覆盖**。**裁定**：Q1 量化如上；Q2 受影响网全为阻抗受控 ⇒ declared `symmetric_stripline(refs=[In4,In6])` 在走廊**不成立**；Q3 该暴露**未验**须显式登记；Q4 终判 = **SI9000 + 板厂阻抗券**（不得代填）；Q5 若超规补救层级 = (a) 走廊补 In4 铜（**OWNER**/PM）/(b) 改线换层（信号流向 ⇒ 或 **L1**）/(c) 走廊段宽-隙补偿（**L2**，须场解）。工具 `p3_v57_co111_in5_pcie_corridor_exposure.py` `c586f2a49742e137` / 记录 `m13_v57_co111_in5_pcie_corridor_exposure.json` `9ae53dbf3cfc48e1` / 卡 `m13_v57_CO111_in5_pcie_corridor_exposure.md` `09fb8d2656b5b27d`。
> ㊺ **CO-112（L2 自裁 · 声明式施加）3 bridge zone = B.Cu 桥（step ②c）+ In5 区域条件参考口径**：按 CO-105 先例（零 SPEC/板改动、不重基线）。**D1** 3 zone（`P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4` / `MCU_VDD_BCU_RESISTORS_IN4`）桥接层 = **B.Cu**，几何带只取自声明源：前两者 band 由 basis 文本正则抽取（1 带 / 2 带），MCU_VDD 取已声明 via palette 的轴对齐 bbox（固定规则，**provisional**）。**D2** 其 targets 经 B.Cu 桥接 ⇒ In4-平面可达性 requirement 对其**语义不适用（N/A）**（镜像 CO-105 V1），`polygons=[]` 不构成缺陷。**D3** In5 **区域条件参考口径**：In4 有铜处 `refs=[In4,In6]`、走廊 x∈(49.8,88.37) 处 **`refs=[In6]` 单参考**（1629.5/1094.8mm）。**D4** 走廊逐网 worklist（16 网，合计 1094.8mm）⇒ SI9000 + 板厂券终判。**非声明**：In5 PCIe 阻抗暴露（CO-111，40.1%）**不因本件减轻**。工具 `p3_v57_co112_bcu_bridge_declaration.py` `4bda33760ad2d196` / 记录 `m13_v57_co112_bcu_bridge_declaration.json` `5f621c3c1003be00` / 卡 `m13_v57_CO112_bcu_bridge_declaration.md` `e36fc9ad1a244425`。
> ㊻ **CO-113（L2 自裁 · 施加）SPEC rev-14 = CO-105/109/110/111/112 裁定写入 canonical SPEC**：**仅新增声明键**（既有标量仅 `spec_version` 变）——① `pd.zone_defs.in4_corridor_void_by_design_v1`（走廊 x∈(49.8,88.37) 按设计无铜 + CO-111 量化）；② 3 个 `L3_CONSTRUCTION_DERIVED` power_zone 增 `bridge_layer="B.Cu"` + `bcu_bridge_bands`（band 只取自声明源：basis 文本 / 已声明 via bbox）；③ `plane_reachability_status.na_scope_v1`（GND entry = CO-105 / bridge targets = CO-112 语义 **N/A**）。新键**无消费者** ⇒ 引擎/L4/L5/各闸读数不变。**几何不变性**：新图纸 `route_geometry`/`pages`/`landing_rows` 与 rev-13 **逐字节同**（`c27d9f5b…`/`2535f330…`/`74234e98…`），板 `0e636a67c1472462` **逐字节不变**；G4 **FEASIBLE_ALL**（主件 `0e74718b1e31dca5`）/ G5 PASS frozen / L4 viol 0 / L5 DFM new=0 + SI 0.1300 / co99 0-0-0-0 / co102 42-76-42 / co106 INDETERMINATE。链 pin 同批前移（引擎/validator/闸默认 spec co78/81/84/91/92/95/98/99/102/104/105/106 + co77 正则）；历史件 co107..co112 仍 pin rev-13。工具 `p3_v57_co113_spec_rev14_declare.py` `4c885825a6cecf60` / 记录 `m13_v57_co113_spec_rev14_declare.json` `261fa00af228be4a` / 卡 `m13_v57_CO113_spec_rev14_declare.md` `29554ef222ec2e79`。
> ㊼ **CO-115（L2 自裁 · 事实更正）In4 走廊空洞 = 失效 keepout 残留（待 L3 派生）**：**更正 CO-109 R2 / CO-110 / CO-113**。机判：`retired_in4_keepout_band_6l.band = x[50.0,88.17]`（CO-95 退役；premise=「铜皮东西两区**禁止跨越此带**，两侧各留 0.2」）；走廊边界 `MCU_VDD_WEST` 东缘 **49.8 = 50.0−0.2**、`P3V3_EAST` 西缘 **88.37 = 88.17+0.2** ⇒ 空洞 = 该退役约束的**两侧 0.2mm 内缩残留**；CO-95 `effect` 明文「退役后 **In4 铜可在原 band 区内按网归属铺设**」⇒ 空洞**属待 L3 派生**（handoff §4-2 原判正确）。**更正后推论**：CO-111 的 In5 PCIe **40.1% 参考缺失可修**（按网归属铺 In4 铜）；rev-14 的 `in4_corridor_void_by_design_v1` 键须 **rev-15** 更正；CO-98 `declared_pending_l3` 语义回到「待派生」。**唯一硬停点（OWNER/L1）**：band x∈(50.0,88.17) 内 In4 铺铜的**区域归属界面**（MCU_VDD/P3V3_AUX/P3V3）——界面未定则无法 L2 唯一确定铺铜几何（不得代填）；即既有 L1 项「P3V3_AUX 西区归属」同族。工具 `p3_v57_co115_corridor_stale_keepout_correction.py` `f5d0007766677616` / 记录 `m13_v57_co115_corridor_stale_keepout_correction.json` `b200828cb797817e` / 卡 `m13_v57_CO115_corridor_stale_keepout_correction.md` `700f4c6d6c226059`。
> ㊽ **CO-114（L2 · **非执行者**对抗复评）SPEC rev-14 新基线 = `PASS_WITH_FINDINGS`（6 发现）**：独立六面机判（A 差分 / B 不变性 / C pin / D CO-115 更正 / E CO-111 复算 / F 新键无消费者）**全 True** + **9 牙齿全触发**。**证实**：rev-14 仅新增声明键（既有标量只 `spec_version` 变）、几何与板**逐字节不变**（rev-13 git blob `73c0066df83fa8c2` → 主件 `0e74718b1e31dca5`）、SPEC pin 全数前移、新键零消费者；CO-115 更正算术成立；CO-111 **40.14%** 独立复算逐位一致。**发现**：F-1（high）rev-14 键 `in4_corridor_void_by_design_v1` 已定性错误（CO-115）⇒ 待 **rev-15**；F-2（medium）co87「参考平面」行证据文本仍含「按设计」；**F-6（medium）4 记录 5 处 `inputs.*_record` provenance pin 因 rev-14 重基线而陈旧**（co98←co95 / co105←co98 / co109←co106 / co110←co106 / co110←co87；CO-108 check C 不变量被打破、CO-77 盲区）；F-3（low）CO-113 `new_keys` 少声明 `bcu_bridge_bands_source`；F-4（low）CO-111「无逐线阻抗核验字段」措辞不精确（SI 实含 `per_layer_impedance`，真缺口=区域无关性）；F-5（info，已由本件 v1.81 更正）。工具 `p3_v57_co114_rev14_nonexecutor_review.py` `6642f8156e349c24` / 记录 `m13_v57_co114_rev14_nonexecutor_review.json` `20adc9fb67e62c63` / 卡 `m13_v57_CO114_rev14_nonexecutor_review.md` `ab0da32774a0714d`。
## 2. 冻结栈与关键输入（现行）
| 项 | 件 | sha16 |
|---|---|---|
| 叠层（L2） | `m13_v57_layer_intent_rev6.json`（**LID REV6 / CO-68**：signal = F/In2/**In5**/B；In1/In3/**In6**=GND，In4=P3V3） | **`05009687a3f01583`** |
| 走廊/见证（L2） | `m13_v57_big_w0r_corridor_model.json`（W0-R，未改） | `80ee9adb78a7e9ad` |
| 通道分配（L2/L3） | `m13_v57_co16_channel_allocation_v9.json`（CO-145：lane 步距 1.07；CO-144 carry + PDN 障碍场） | **`d3cd1e5a312f253a`** |
| 逃逸域（L2/L3） | `m13_v57_co37_escape_domain.json`（CO-37）＝ `.kicad_dru` 引用 `5616a9f873c9b844` | `5616a9f873c9b844` |
| SPEC（红线原件） | `SPEC_k2_v4.json`（未动） | `0bd52ed48e720b8c` |
| SPEC（引擎消费 ECO，**现行**） | `SPEC_k2_v4.spec-rev-19.json`（**CO-132 施加：R1 In4 承载几何（P3V3 桥区多 target + P3V3_AUX J4.A9 + 12V_IN），`fill_priority=1`；MCU_VDD 电阻区 = covered_by_host（CO-131）；stackup In4 文本含 12V_IN；可达性 unresolved 清空**） | **`5f72182a2616392c`** |
| SPEC（引擎消费 ECO，历史） | `SPEC_k2_v4.spec-rev-17.json`（**CO-130 施加：D-6 网类 `12V_IN`→POWER + 退役三 zone 的 B.Cu 载体声明（`bridge_layer` B.Cu→In4.Cu）+ `stackup[In4.Cu]` 文本对齐实际网集；仅声明键；板逐字节不变**） | `9fea9fd20149c736`（已取代） |
| SPEC（引擎消费 ECO，历史） | `SPEC_k2_v4.spec-rev-16.json`（**CO-122b 施加：CO-121【L2 自裁】西区 P3V3_AUX In4 承载 = 追加 `P3V3_AUX_WEST` 单环 zone + 可达性归口更正；前序 CO-117 更正错误键 + 按网归属铺入 band；前序 CO-113**：CO-105/109/110/111/112 裁定写入 canonical SPEC —— In4 走廊空洞**声明**（**CO-115 更正：非按设计**，属失效 keepout 残留、待 L3 派生）+ bridge zone = B.Cu（声明带）+ 可达性 N/A scope；**仅新增声明键**） | `5748828a23161250`（已取代） |
| SPEC（历史 ECO） | `SPEC_k2_v4.spec-rev-13.json`（CO-107 平面对齐；已被 rev-14 取代） | `7943be727a4f8ef9`（已取代） |
| SPEC（历史 ECO） | `SPEC_k2_v4.spec-rev-12.json`（CO-101 互障重导；已被 rev-13 取代） | `1a381b06454dbe2c`（已取代） |
| SPEC（历史 ECO） | `SPEC_k2_v4.spec-rev-3.json`（ECS-001，CO-40；保留未动） | `2d6dbd8bd8d667d7` |
| 规则 | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8` |
| manifest | `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7` |
| 冻结板（8L 基线） | `k2_v4_8L.kicad_pcb` | `fb07d25ac426ff84` |

## 3. 整链门禁（G4..G7，全部实测）
| 门 | 判定 | 证据（sha16） |
|---|---|---|
| G4/W3 | **PASS（FEASIBLE_ALL）** | 主件 **`60cbd331836e52b7`**（rev **W3-CN.41**；CO-101 重基线：`route_geometry/pages/decision_contract/layers/method/gate_status/verdict` 与 CO-85 基线 `22c2a15835857f99` **逐字节同**，唯一 delta = `inputs_sha.spec`（rev-8→rev-9）与 `frozen_sha_check` 指纹）；landing `da21d0186a9c643c` |
| G5/W4 | **PASS** | `m13_v57_w3_validation.json` `8b385d6c554ac527`（validator v2；G-M1..6 True、A1.2/A1.3/A1.4 True、frozen=True；冻结集含 `spec=77f5c54df88bb0ca`） |
| G6/L4 | **PASS** | 板 **`d4e81f647be7f980`**（68 网/**2523** 图纸段 + PDN 施工 185 短段 = **2708** track / **493** via（252 图纸 + 241 PDN）/ **13** zone（4 逃逸域 + 9 PDN）；track 宽度按层 F/B 0.205、In2/In5 0.16）；construction `305a42a890593552`；`m13_v57_l4_validation.json` `aa666a49e36883c7`（L4-A..**F** True、viol 0） |
| G7/L5 | **PASS** | fab `6d85160413770fa5`（2523 tracks/252 vias）；si `73f9b59ed5f6f3ce`（rev **L5-SI.6**：**按层加权电气 skew 0.1300 ≤ 0.15**、physical 报告 1.1046、pdn_status=reserved_not_poured）；**dfm `40445f87be664f31`（L5-DFM.6：多重集 new=0 / disappeared=0 / 在册 0 未连）** |

**CO-107（rev-13）注**：G4 主件/`inputs_sha` 指纹重基线；`route_geometry`/`pages`/`landing_rows`/`decision_contract`/`layers`/`method`/`gate_status`/`verdict` 与 rev-12 基线 **逐字节同**；板 **`0e636a67c1472462` 逐字节不变**；G5/G6/G7 与 PDN/回归闸重跑读数不变（唯一例外 = CO-106 由 FAIL 转 INDETERMINATE、co77 对象随本 boundary 更新）。

DFM 收敛轨迹（v1.15 之后）：**D1/D2 归零（CO-23；W3-CN.37）→ 73（CO-23）→ 60（CO-37 D3c）→ 54（CO-41）→ 38（CO-43）→ 0（CO-45）**。
L4 板 `kicad-cli` 实跑：仅冻结基线 42 条 lib/silk，**铜层违规 0**（clearance/shorting/solder_mask_bridge/tracks_crossing 全 0）；基线铜违规数 = 0 ⇒ `new_total=0` 等价于「零铜层新增」。

## 4. v1.15 → v1.16 取代沿革（rev 与变更单）
- **W3-CN.27 → .36**（ROOT-16 线）：CO-05..CO-11（O4 落列可行性、安全 hop 拓扑、pair 域 v1.4/1.5、lane 平面）；
  CO-16/CO-18/CO-19/CO-22（东侧重派生、O4 有界幅值闭式蛇形、板内 J3 fan、lane 平面重整）⇒ 全板 **32/32 有效**（W3-CN.34/.35/.36）。
- **W3-CN.37**（CO-23）：板边真带（Edge.Cuts y=33/79、x=143）⇒ D1 copper_edge / D2 hole_to_hole 归零。
- **D3b 收官**（CO-25..CO-36，L2 自裁）：connector 落列器改「land 段长升序」（CO10_LXPRIO=landlen）⇒ CO16-ALLOC.5。
- **D3c**（CO-37）：SPEC 逃逸区规则域 `.kicad_dru`（0.075 + 4 具名 rule area，**显式排除 `PCIE_REFCLK*`**）。
- **L1 更正**（CO-38→CO-39）：D3a 非引脚缺陷，J2 侧 REFCLK 引脚由原理图网表 + SFF-8654 pinout 真源锁定 ⇒ 闸口 CLOSED。
- **W3-CN.39**（CO-40/CO-41）：SPEC-REV-3 ECS-001（J2 外列 N 单次换层 F.Cu→In2→F.Cu，每线 2 via）⇒ DFM 60→54。
- **W3-CN.40**（CO-42..CO-45）：远端带内接入（禁沿 A 排平行）＋ 对内偏移 `{P:0.0,N:-0.5}` ＋ dip 解耦 ＋
  图纸/nodes 一致化 ＋ P 轨等长幂绕 ＋ `A-CN.5d` ⇒ **DFM 38→0、G7 PASS**。

## 5. 覆盖性声明（宪法第五章第 1 条）
管辖对象 = 34 页（32 MCIO lane 页 + 2 REFCLK 页）/ 68 网 / 2 远端连接器（J3/J4）接入；**无「待定/暂不管」对象**。
每对象均有机器可读决策：`pages[*].nodes`（3D）+ `pages[*].vias` + `route_geometry` + `decision_contract`
（corridor_x / 分层链 / max_vias_per_line / pair_rule / REFCLK 层契约）。
**本声明范围 = 高速走廊结构**；《宪法》ch.5 §4「数学闭合」四项之 **PDN 压降** 与 ch.2 L2 裁判标准之 **热**在本项目**无输入/无证据 ⇒ NOT_DEMONSTRATED（缺输入，见 §6-8 与 CO-87）**，不得由本声明读作已闭合。

## 6. 已知限制与豁免（如实声明，不得当作 PASS 依据掩藏）
1. **板字节已可复现（CO-49 解除）**：原 `pcbnew` 保存使 `segment/via/zone` 块的**顺序与 uuid** 每次重建漂移（其余块逐字节稳定）；
   CO-49 在 L4 applier 内做确定性规范化（连续同类 run 内排序 + 由内容派生 uuid5，只碰这三类块）⇒ **构建→L4→L5 全链 7 件逐字节可复现**；
   现行 L4 板 **`d4e81f647be7f980`**（方案(a)/LID REV6 重基线，CO-68/69 起；**CO-133 施工后** = 图纸几何 + PDN 声明铜；施工前 `0e636a67c1472462`）；
   历史（规范化前/方案(a) 前）板 `cdcb869e9827ec87`、`4d36212f6492262b` 等见 git 与 CO-45..CO-48 各 commit；
   **几何内容身份** = 现行 drawing `3d452429bbc934c3`（CO-89 重基线；CO-85 基线 `22c2a15835857f99` 已取代；W3-CN.41；`route_geometry` 与 W3-CN.40 `dfa1d7c4a811b0da` / rev-4 重基线 `4e7497daf97cebd1` 逐字节同，见 CO-56 §2）。
2. **CO-16 层跨不相交豁免**：独立验证器 G-M4 记录 `span_blind_min_mm = 0.163083 < 0.175`、`span_blind_violations = 3`，
   依 CO-18 §1b/§4-2「同层跨不相交 ⇒ 物理净距不适用」豁免；`kicad-cli` 实跑同层净距 0 违规（与该豁免一致）。
3. **DFM `new`：已升级为多重集差（CO-51 解除原限制）** —— 键 = `(type, items[].description)`，并显式报 `disappeared_total`（基线消失，L4=tracks-only ⇒ 须为 0）；
   实测 new=0 / disappeared=0（42 条 lib/silk 基线全部在册）。
4. **未路由网 348 项**（冻结基线 416）：v57 范围为 68 条高速网；其余网不属本阶段（不得据此判 FAIL，也不得声称整板已布完）。
5. **阻抗几何（CO-53→CO-56 已收口：一阶在设计带内，终判=板厂券）**：交付对内中心 0.500（边距 0.295）≠ SPEC `p_gap 0.175`；对间最小 0.550 中心（0.345 边距）vs SPEC `inter_pair_spacing_mm 0.875`；SPEC `stackup/impedance.model` 仍 6L 而板为 8L 且板内无介质叠层定义 ⇒ **阻抗符合性 NOT_DEMONSTRATED**（既非已证合规、也非已证违反）：**CO-55 已取消 (a)**（改为反向下达叠层要求，见上）；余 **(b) SI9000 校验（板厂券已声明）+ SPEC ECO rev-4**（stackup/impedance 分层口径/p_gap 语义）**（c）走廊口径已记录**。**已由 CO-55（下达 8L 叠层要求）+ CO-56（SPEC ECO rev-4 + 复跑）收口**：详见 `m13_v57_CO53_intrapair_geometry_impedance_open.md`、`m13_v57_CO54_spec_delivery_drift_inventory.md` `23d22ea76c0b95ff`、`m13_v57_CO55_layer_aware_impedance_build_ruling.md` `f9c45071c5d9141c`、`m13_v57_CO56_spec_eco_rev4_apply_record.md` `5b8b86ed789b5678`（含 **8L 叠层输入缺口可达性实测**与 Zdiff 重导 harness `tools/p3_v57_si_zdiff_rederive.py`）。
   **CO-47 已把该声明升级为谓词**：L5 记录 `dft.in_scope_unconnected_items == 0`（在册网按 kicad-cli 未连项网名解析）；实测 基线 68/68 在册网未连 → L4 **0/68**。
5. **G5 冻结集已校正（CO-46）**：原独立验证器的 `frozen_sha_check` 只钉 ECO spec + **历史 6L 板**，未覆盖红线 SPEC 原件与 8L 冻结板；
   CO-46 以「只增不减」补入 `spec_orig=0bd52ed4` / `pcb=fb07d25a`（并保留 `pcb_6l=f6273de6`）后 G5 仍 PASS。记录：`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98`。

6. **⚠ L1 待裁（CO-57 → CO-58 → CO-59 再基）**：R3-2『对间铜边净空 ≥0.875』的**时效/绑定范围**。
   - **口径出处（CO-59 机判）**：要求注入点 = `route_model_config.json` `capacity_audit.inter_pair_spacing=1.46`（note：语义 = 0.875 铜边净空 → 1.46 = 0.585+0.875 的中心距换算）；**1.08 属 `channel_alloc.pitch_fallback`（回退值）**，非要求量。**CO-58 以 1.08 为基线的「走廊与冻结口径一致」结论按 CO-59 更正**（原文保留不改）。
   - **交付实测（板级）**：EAST 对间距 **1.449**（铜边 0.744）/ WEST **1.050**（铜边 0.345）⇒ 在 **1.46 中心距**与 **0.875 铜边**两种读数下**均不达标**（EAST 在中心距口径下差 0.011）。板厂口径四方不自洽（1.20 / 1.46 / 1.08）。
   - **残余②已闭合**：B.Cu 与 In6 无并行耦合（0 对；最小并行横向距 20.3mm；B.Cu zone = 0）⇒ CO-55 的 B.Cu 约束满足。
   - **Q1（L1，单一问句）**：是否授权走廊对间距 → **1.580**（= 交付铜跨 0.705 + 0.875，**歧义无关**，同时满足 1.20/1.46/0.875）？授权 ⇒ L2/L3 重导 + （若需）J2/J3/J4 落列/焊盘场变更（L1）；备选：铜跨回退 0.705→0.585 使 1.46 给 0.875（L2 但需重定 8L 阻抗）——**CO-86 已机判闭合：该 L2 出口不成立**（任一可行铜跨下所需轨距 ≥1.282 均 > WEST 上限 1.050 且 > 焊盘场 0.600；焊盘场 0.600<0.875 与 span 无关 ⇒ L1 级硬限；且备选非免费：gap 0.295→0.175 使 Zdiff 88.4/82.0→81.9/74.1Ω，内层出带）。
   - **CO-70/71 补强证据（逐层实测，L4 construction，方案(a) 现状）**：对间同层最小中心 / 铜边净空 —— `In5.Cu` 0.550 / +0.345（最长并行 55.97mm）、`B.Cu` 0.550 / +0.345（14.22mm）、`In2.Cu` 0.580 / +0.375（20.35mm）、`F.Cu` **0.4921 / +0.2871**（板；witness `PCIE_UP_OUT6_N_J2` vs `PCIE_UP_OUT7_P_J2`；图纸 route_geometry 0.4627 / +0.2577）（**CO-85 F1 更正**：原记 1.124 / +0.919「达 0.875」经 7 种口径复算均不可得，已废）。⇒ **R3-2 0.875 在 4 个信号层中 4 层全部违反**（CO-85 更正：原『3 层』以不可复现的 F.Cu 行为据）；因其同时出现在 In2/In5/B（走廊轨距根因）与 F.Cu（连接器焊盘场根因，见 F2）（4 层全违反，非单一层分配所致），**层分离（channel 重分配）不能作为 L2 解**：根因 = 交付轨距（WEST 1.050 / EAST 1.449）× 对内半边距 0.25 ⇒ 邻线净距 0.345；达 0.875 需中心距 1.580，与冻结 L1 包络（球栅逃逸 / 板边 78.5975）互斥（CO-60/61 复现）。⇒ ① 维持 **L1**。
   - **CO-75 补强证据（本件新增，L2 未覆盖维搜索）**：WLO(12)×WSWAP/COLMODE(3)×FANY_J3(5)×HOLE_GAP(3)=23 组合、WSTEP=1.580 **全 0 命中**（保真 1.05@33.70=32/32）；失败恒在芯片输入 via 区，行扫 1.4e4~1.8e4 耗尽 ⇒ 硬限非旋钮。另注：本件**未**扫逃逸层分配（per-ball 冻结拓扑 ⇒ L2 ECN 级重导）与球栅/落列/板框（L1），故非「L2 全空间」数学完备证明。
   - 裁定前：不得声称对间净空合规、不得放宽 R3-2/冻结口径。G4..G7 现状与判定不因此件改变。**CO-85 追加（裁决相关）**：违反层数更正为 **4/4**；且 **J2/J3/J4 连接器焊盘节距 0.6mm ⇒ 焊盘场同层对间铜边净空上限 0.395mm < 0.875**（F2）⇒ **owner 选项 A（走廊重开至 1.580）单独不能使整板满足 0.875**：须限定 R3-2 口径到走廊/长平行区，或改连接器引脚场（L1）。**CO-86 追加**：L2 侧最后一条出口（对内铜跨回退）已量化排除（`n_pass_all_caps=0`，最小缺额 WEST +0.232 / 焊盘场 +0.682）⇒ L2 六域**无剩余可行变量**；R3-2 0.875 只能由 L1（引脚/球栅/板框）或红线口径修订解决。

7. **✅ `CO-72-PDN-1` 已闭合（CO-74，L2）**：原记 L1 系**归口过高**。前提（6L『In4 走线带阻断跨带铜皮』+ SPEC B.Cu=POWER_POUR）在 LID REV6 下机判失效（引擎层集无 In4；交付板 In4 段数 0）⇒ B.Cu 电力铜退役、改由 In4 承载，层数/平面数/电源域集合/信号层数**全不变** ⇒ L2。**B.Cu 电力铜自此禁止**（`pd.bcu_power_copper_policy=PROHIBITED`）。实体 In4 分区几何 = L3 施工（确定性派生 + DRC 核对），非本闸宣称已建。
8. **⚠ L2 合格标准覆盖缺口（CO-87，机判）**：《宪法》ch.5 §4 数学闭合明文含 **PDN 压降达标**，ch.2 把 **热** 列为 L2 裁判标准；L2 侧闸（CO-63..CO-86）覆盖 容量/长度/过孔/PDN **架构**，但 **PDN 压降** 与 **热** 全仓无输入（SPEC rev-8 全字段扫描 **0 命中**，扫描字段 3962）⇒ 两者状态 = **NOT_DEMONSTRATED（缺输入）**，既非 PASS 亦非 FAIL，**不得当作已闭合**。所需输入（机器提取自 `pd.zone_defs.power_zones[*].targets`）：① 各轨负载电流（U3/U7 redriver、MCU/存储、J3/J4 MCIO A9、去耦/上拉）；② 允许压降预算与采样点；③ In4 铜厚/温度修正 + L3 平面几何；④ 热：器件功耗/环境温度/风速/可接受温升与热阻路径。**属数据/需求输入（非 L1 拓扑裁决）**；禁止以假设值代填（不得伪造 sign-off）。记录 `m13_v57_co87_l2_acceptance_coverage.json` `46d15557477d164b` / 卡 `m13_v57_CO87_l2_acceptance_coverage.md` `322baa098740b259`。

9. **✅ L2 SPEC · PDN 板实性已闭合（CO-88 判定 FAIL → CO-89 施加 rev-9）**：原判据（CO-88）：`pd.zone_defs.power_pad_connect` 有 **55/173** 条引用板上不存在的 ref（35 孤儿，含 **U3/U7** — 红驱动已由 U3+U7 合并为 **U6**（DS320PR1601, 354 球））；板上 **309** 个 SMD 电源/地 pad 中仅 **118 覆盖 + 7 blocked**，**184（60%）静默待定**（违 ch.5 §1）；`pd.decoupling` 指向的 C67/C68/C72 **3/3 不存在** ⇒ 解耦规则零板实落点。**修复候选已派生**（`pad_connect_gen` 对交付板重生成：223 entries + 86 blocked = 309/309 覆盖；blocked 中 U6 占 63/86，为 0.5mm 球栅场内 GND 球无法 pad→via 直连的**显式** blocked），**波及清单 27 件**（含引擎 `FROZEN_SHA`、validator、`co69/77/81/83/84`、L4/L5）。**CO-89 已施加**：SPEC **rev-9**（`77f5c54df88bb0ca`）板实化 —— ppc 重生成 **223 entries + 86 blocked = 309/309 覆盖、0 孤儿**、解耦改板实集合、旧 BOM 转 `retired_*` 留存；**co88 复判 FAIL → PASS**；全链重基线后**板逐字节不变** `0e636a67c1472462`。**残余**：① 86 blocked 中 **U6 占 63**（0.5mm 球栅场内 GND 球无法 pad→via；改判需器件资料+SI/PI）；② **新基线非执行者复评已履行（CO-90 pass 3/3，`897ff5cc371d135d`）**：全链 12/12 逐字节复现（板 `0e636a67c1472462` 不变）、CO-88/89 事实独立复核通过（ppc↔板实 pad 双射 309=309、`pd` 外零变更、旧 BOM 退役 173/9 留存、解耦全板实、CO-89 幂等）、CO-88 闸注入突变 4/4 命中；**F1**（headline 未并入判据 C ⇒ 空解耦态 C=FAIL 而 headline=PASS 的 partial-pass）与 **F2**（teeth 恒真：只查 board_refs、`syn` 死代码）已修复 ⇒ co88 **CO-88.3**（F1/F2 + 续接发现的 **F4**：ripple 建议清单移出哈希体 ⇒ 记录恢复为 (SPEC, 板) 纯函数），记录 `f90d65369cab92dc` → **`bf69909aa64dc494`**（判定仍 PASS）；**F3** 见 §6-10，**F4/F5** 见 §6-11；③ PDN 压降/热仍缺输入（§6-8）。不触 L1。

10. **⚠ PDN 覆盖口径（CO-90 F3，登记不可静默放宽）**：CO-88/CO-89 的「板实 SMD 电源/地 pad **309/309 = 100%**」其分母 = `eda_core.pad_connect_gen.DEFAULT_PWR_NETS`（**内置常量**，非「板全电源网」）。交付板 `.kicad_pro` `netclass_assignments` 的 POWER 类另含 **`PWR_5V_KEY`**（板实落点 `C89.1`，SMD，0 走线；属 SPEC `layer_plan.low_speed_nets`、68 网范围外）⇒ 该 pad 不在分母亦无决策，**声明须限定为「内置网集口径」**。改分母（纳入该网）= SPEC rev-10 + 全链重基线，且「哪些网计入 PDN 覆盖」属**网范围/电源域口径 ⇒ 待 PM/owner**，不得由 L2 静默重定义。另 `pad_connect_gen` docstring 自称「PWR_NETS 从 SPEC constraints/net_classes 推导」而实现只读内置常量（**文实不符**，待共享层变更单）。

11. **✅ 闸可复现性（CO-90 F4）与引用闸牙齿（CO-90 F5）—— 已修复（续接 pane16 复评时发现并机判）**：
    - **F4（中｜可复现性）**：`p3_v57_co88…gate.py` 曾把 `ripple_checklist()`（扫描 `tools/*.py`）嵌入**记录哈希体** ⇒ 记录 sha 随**无关工具文件**增删而变。实测（两次对照）：移走 `p3_v57_co90…review_pass3.py` → `d320c81263733158`；放回 → `b9990766698af315`。
      后果：boundary 引用的 co88 记录 sha 在提交前即已不可复现（且是 CO-90 自身工具造成的）。**修复**：ripple 清单移出记录（记录 = (SPEC, 板) 纯函数）⇒ **CO-88.3**，稳定值 `bf69909aa64dc494`（三次含「移走/放回 CO-90 工具」对照均同值）。
    - **F5（中｜引用闸空真）**：`co77` 的历史豁免是**按整行**判定 ⇒ 「现行值 + 同行括号记录旧值已取代」这类行的**现行值**被一并豁免。实测：co88 记录漂移到 `b9990766…` 后，co77 仍报 `citation_mismatch=[]`（本应报警）。**修复**：豁免改为**按引用**判定（校验紧跟该 sha 之后的标记窗口），记录 revision **CO-77.3**；修复后该漂移被抓（负控）。
    - 边界：仅动闸/记录与声明件引用，**零几何、零阈值、零 SPEC**；F4 修复前后 co88 判定均 PASS（内容更严仍 PASS）。

12. **✅ PDN **计划坐标**净距缺口（CO-91 判 rev-9 FAIL → **CO-93 已施加 rev-10 闭合**；原判留档）**：`pdn_apply.py` 逐字实落 `pd.zone_defs` 的 via/短段坐标，但既有闸（CO-88 板实性 / CO-89 重基线 / CO-90 幂等）**均不判这些坐标的几何净距**。CO-91 以冻结规则源 `drc_rules.json`（netclass clearance + `min_hole_clearance`，语义核已对齐 kicad DRC 430/430 + 106/106）机判：**ppc via 35/223 + stitch via 41/69 + zone via 7/20 + F.Cu 短段(w=0.5) 75/223 违反**。
   - 根因（引擎侧）：① `clear_via_from_obstacles` **把 via 直接跳过**（从不作障碍）⇒ 计划 via 可与既有 via 铜重叠；② 净距用扁平 `0.1/0.05` 而非 netclass 派生 `required`；③ 无 `min_hole_clearance(0.25)` 概念；④ stitch/zone 孔位为更早阶段落盘、其后未随 v57 布线复核（漂移）；⑤ 短段默认 `w=0.5` 在 0.5–0.6mm 节距 ball field 内不可能合法。
   - **性质**：判的是**计划坐标**（交付板 `d4e81f647be7f980`，CO-133 施工后；施工前 `0e636a67c1472462`）；`kicad-cli` 铜层违规 **0**（42 条全为 lib_footprint_*/silk）⇒ **非**「已交付板不合格」。CO-133 已更正其 via-via 孔缘公式（见 §11）。
   - **修复候选（未施加）**：ppc 35 例 **35/35 可重定位、无新增 blocked**（⇒ 修引擎后 PDN 覆盖不退化）；stitch 41 / zone 7 需以当前板**重派生**并留存退役集；短段宽度须同批改口径。施加 = SPEC rev-10 + 全链重基线 + 重新过对抗评审。
   - 记录 `m13_v57_co91_pdn_planned_coord_clearance_gate.json` `3ede251a830108f1` / 卡 `m13_v57_CO91_pdn_planned_coord_clearance_gate.md` `1b83f41f37bf96f5`。
   - **附（U6 63 blocked 复核）**：在引擎自述设计政策（异网铜边 ≥0.3）下 **8/63 可解**（纯 DRC 口径 39/63）⇒ CO-89 §4.1「硬阻塞」结论成立；但其所称依赖「**需 DS320PR1601 器件资料**」**不成立** —— 354 球图 `ds320pr1601_ballmap.json` 与手册 `ref/ds320pr1601.pdf` **已在仓内**（v22 layer gate 已消费），真实瓶颈 = 工艺/口径裁决（via-in-pad 能力或判定域），非缺数据。

13. **✅ PDN rev-10 修复候选（CO-92 → **CO-93 已施加**；原备料留档）**：CO-91 判定 FAIL 后，其 **CO-91.1 的 `fix_candidate`（8 向 × 半径梯 0.30–2.00）违「零坐标搜索」红线，已作废**（CO-91.3 移出）。
    以**可采纳的声明式有限 palette**（原位 → 4 正交点 @0.475 → 4 正交点 @0.6；优先原位、无迭代）重算：
    `power_pad_connect.entries` 223 → **kept 188 / relocated 1 / blocked 34**；`gnd_stitch_via` 69 → **28 / 12 / 29**；`power_zones[].vias` 20 → **13 / 4 / 3**。
    - **决策覆盖不退化**（板实 pad 仍有决策 309/309），但 **ppc 已连接数 223 → 189**；要保连接数须走 **via-in-pad / 平面直连** ⇒ **工艺/口径裁决**（owner/PM + 板厂能力），非引擎可自解。
    - 短段宽度梯（223 目标，权威口径）：`0.5 → 75` / `0.3 → 15` / `0.2 → 13`（`.kicad_pro min_track_width=0.2` ⇒ 可制造下限 0.2）；残余 13 与 ppc 同源（密集场）。
    - 根因归口：`gnd_stitch_gen` 障碍集 = `layer_plan` **规划段**（**不含交付板实际铜**）⇒ v57 改 In5 走线后漂移；另其 blocked 记为 `ok: False` 而 `pdn_apply` 只跳 `blocked`/`status=="blocked"` ⇒ **直接重跑会把 blocked 缝合 via 实落**（schema 须一并对齐）。
    - **施加 = SPEC rev-10 + 全链 G4..G7 重基线 + 全部回归闸 + 重新过对抗评审**（本件不施加）。
    - 记录 `m13_v57_co92_pdn_repair_candidate.json` `7aaacd8f34559763` / 卡 `m13_v57_CO92_pdn_repair_candidate.md` `6de3c9fb2b26d45d`。

14. **⚠ rev-10 已知限制与后续（CO-93）**：**已连接 pad 223 → 189（−34）**：34 个 pad（多为 U6 0.5mm 球栅场内电源/地球）在**冻结 8L 通孔工艺 + 声明 palette** 下无合法连接位（决策覆盖仍 309/309）。保持连接数只能靠 **via-in-pad**（需板厂工艺能力 + SI/PI 证据）或 **HDI/微孔**（**L1：层数/叠层**）⇒ 本件均不擅采，登记待裁。
    施工层未同步：`_shared` 引擎（容器副本**只读冻结**）与 `pdn_apply.py` 均未改 ⇒ rev-10 的生成器为 **k2 决策层工具** `p3_v57_co93_pdn_rev10_derive.py`；`pdn_apply.py` 短段宽度仍为 0.5（施工时须以 SPEC `stub_width_mm=0.2` 为准），且 `gnd_stitch_gen` 障碍集（只取 `layer_plan` 规划段）与 blocked schema（`ok:False` vs 消费者只认 `blocked`/`status`）须一并修 ⇒ 登记为后续变更单。
    **非执行者复评欠（CO-94）**：本件为 rev-10 执行者，按 `L2_STRUCTURE_v2.0.md:137` 不得自评；rev-9 的 CO-90 复评证书随本次重基线失效。 **CO-96（pass 4/4）已对 rev-11 履行非执行者复评（rev-10 义务随重基线并入）。**

15. **⚠ L1/工艺升级（CO-94，一句话）**：rev-10 的 120 个 blocked 电源/地球中，**34 个（原 entries）与 92 个**在 L2 手段内判为不可连接（可连位仅存在于搜索式家族且余量 13.6µm、需 1.35–1.80mm 长短段）⇒ 若须连接，只能靠 **via-in-pad（板厂工艺能力 + SI/PI 证据）** 或 **HDI/微孔（层数·叠层，L1）**。请监理升级人工取裁。
    另：本件为**家族内**判定（不含狗腿/多段绕行；后者属 `EscapeAllocator` 域，未展开）；rev-10 非执行者复评（CO-94 评审项）仍欠。

16. **⚠ L1/区域划分升级（CO-95，一句话）**：rev-11 的 55 个 power entry 中 **6 项无可达 In4 路径且本网无区/区域归属冲突** ⇒ `12V_IN`（3 pad，无 In4 区、板上无铜）需裁**承载**；`P3V3_AUX` 西侧（3 pad）需裁**西区归属**（名义 MCU_VDD vs basis 文本称 P3V3_AUX+MCU_VDD 同区）。另 6 项为 band 退役后的 **L3 可达性义务**（非死结）。
    施工/引擎侧未同步项（同前）：`pdn_apply` 短段宽度仍 0.5、`gnd_stitch_gen` 障碍集仍取 `layer_plan`、blocked schema 未对齐；`_shared` 容器副本**只读冻结**未改。**rev-11 非执行者复评：已由 CO-96 履行**（verdict `REVIEW_DONE_FINDINGS_OPEN`，6 项发现见 §6-17）。

17. **⚠ CO-96 的 6 项发现（非执行者侧对抗评审 pass 4/4，对象 rev-11；机判 + 牙齿；F1 已由 CO-97 显式登记关闭其『静默』面；余项见 §6-19）**：
    - **F1（中·谱系/红线邻近）**：rev-10 重建 `power_pad_connect` 时**静默丢弃** CO-89 的退役留存键 `retired_superseded_bom`（pre-rev-9 冻结 BOM **173/9** + 孤儿分析 **55/2**）；`p3_v57_co93_pdn_rev10_derive.py` 源码零引用、CO-93 变更说明未登记 ⇒ **现行谱系断链**，违「退役决策须显式留存」。数据可由冻结源 `SPEC_k2_v4.json`（spec-rev-1，173/9）与 CO-89 记录找回 ⇒ 非数据丢失。**处置：已由 CO-97 选『显式登记其移除』分支关闭其『静默』面**（登记册 + 找回指针全可解析；见 §1 ㉚ / §6-19）；『SPEC 内回填』列为可选后续（随下一次构建期 SPEC bump），不为纯溯源字段单独重基线。
    - **F2（中·可闭合性）**：`plane_reachability_requirement` 为**声明可闭合**：gate co95 恒不返回 PASS；8 个 `covered_bridge_target` 命中的桥区 `polygon=None`（几何未建）⇒ **几何真覆盖仅 35/55**（14 待 L3、6 待 L1）。**处置 = 三分态输出 + 补闭式判据。**
    - **F3（中·脆弱性）**：`needs_region_ruling` 对 P3V3_AUX 西侧 3 pad 依赖 `why` **自由文本子串**（`"须裁"/"需要"`）⇒ 改文本即静默把 3 pad 由 L1 降级为 L3。**处置 = 改机判谓词。**
    - **F4（中·范围）**：可达性要求 scope 仅 `ppc.entries`（55）；`gnd_stitch_via` 实落 **40** / `power_zones[].vias` **17** 无闸。**处置 = 扩展 scope 或声明排除理由。**
    - **F5（低·陈旧 live 字段）**：`power_pad_connect.board_realized` 仍记 CO-89 的 **223/86**（rev-11 决策 189/120），未被 `pdn_apply.py` 消费 ⇒ 无功能影响。**处置 = rev-12 同步。**
    - **F6（低·潜在·已关闭）**：co95 `in_poly` 用 bbox 非真 PIP ⇒ **已由 CO-98 改为真·射线法 PIP**（行为中性：现行 polygon 均轴对齐矩形 ⇒ co95 记录字节不变）。
18. **✅ CO-96 复核为 OK 项（对抗性验证通过）**：**V1** rev-9→rev-10→rev-11 的 `pd` 之外**递归深比 0 变更**（仅 `spec_version`）⇒ 重基线声明成立；**V2** co95 分类**完整**（55=35+8+6+6，无遗漏/重复）；**V3** SPEC `gnd_stitch_via` 的 blocked schema（`blocked`/`status=="blocked"`）与 `pdn_apply.py` 消费口径**对齐**（60 跳过/40 施加）—— §6-16 所记「blocked schema 未对齐」**仅指上游 `gnd_stitch_gen` 产出，非现行 SPEC**；**V4** gnd_stitch 重复坐标 `(133.83,59.1)`×2 系**声明共享单孔**（basis 明证：`PCIE_DN3_P`/`PCIE_DN4_N` 共享同一 GND via）⇒ **非缺陷**；**V5** 冻结四源 4/4 MATCH、板 `0e636a67c1472462` 逐字节不变。**基线身份 OK / 牙齿 OK。**

19. **✅ CO-97（L2 自裁）退役留存完整性闸 + 显式登记册 + `_shared` 处置自裁**：把红线「退役决策须显式留存」机判化（逐版枚举退役块 → 逐相邻版求 drop → 未登记即 FAIL；拒陈旧登记项与不可解析找回指针；牙齿 3/3 合成注入）。**结果 PASS**：退役块 rev-8 5 → rev-9 8 → rev-10 13 → rev-11 15；**drop 恰 1 处**（`power_pad_connect.retired_superseded_bom` rev-9→rev-10）**已登记**（reason + 3 找回指针，冻结源 173/9、CO-89 记录 55/2、rev-9 原件均可用）⇒ **CO-96 F1 的『静默』违反面关闭**；`board_realized` 显式记为 CO-89 派生记录（消除 F5 误读）。**L2 自裁两条**：① 选 F1 的『显式登记』分支，不为纯溯源字段单独重基线（该键/`board_realized` 均不被 `pdn_apply` 消费；重基线会作废刚出具的 CO-96 证书并新增复评债 ⇒ 不成比例）；② **`_shared` 不解冻**，施工侧三项 **改由项目内引擎承载**且**仅施工期激活**（当前板逐字节不变、PDN 未施工 ⇒ 非在役缺口）。**仍未闭合（登记待办，非 PASS）**：F2/F4（可达性几何闭合 35/55 与 scope 扩展，属 L3 施工期 + 闸扩展）、F6（co95 bbox→真 PIP，latent）。记录 `m13_v57_co97_retirement_retention_gate.json` `4b1ee8924147a4f4` / 登记册 `m13_v57_retirement_registry.json` `4b13b538ba8e28ce` / 卡 `m13_v57_CO97_retirement_retention_gate.md` `2bc80fbe0c62bfd4` / 工具 `p3_v57_co97_retirement_retention_gate.py` `e9427f0f18087a18`。

20. **✅ CO-98（L2 自裁 · PDN 可审计性）可达性义务状态报告 + F6 关闭**：① **F6** = co95 `in_poly` bbox→**真 PIP**（`d5b102a1f23bb5dd`），**输出逐字节不变**（该时点 co95 记录 sha `61db48a283beeaae`（已取代；现行 = `f1c0c17ee7b379a4`））⇒ 行为中性加固；② **F2/F4 机判化**：新增只读 co98 报告（不改 co95 记录字节）—— 三态 `geometric_covered` **35** / `declared_pending_l3` **14** / `ruling_pending_l1` **6**，`machine_closable_today=false`（verdict 永不 PASS）；scope 排除 `gnd_stitch_via_realized` 40 / `power_zones_vias` 17 / `decoupling_vias` 0；③ **F3**：6 项 ruling = 5 机判（3 无区 + 2 异网冲突）+ **1 文本**（`P3V3_AUX R1.2`）。牙齿 2/2。**仍未闭合（非 PASS）**：F2 几何闭合（14 = L3 派生）、F4 scope 扩展（SPEC 变更）、F3 R1.2 判据。记录 `m13_v57_co98_reachability_status_report.json` `a29b802163bca3d9` / 卡 `m13_v57_CO98_reachability_status_report.md` `84a609e6f5e54503` / 工具 `p3_v57_co98_reachability_status_report.py` `2091c72253930b08`；co95 工具 `p3_v57_co95_in4_reachability.py` `4d87484ff2f1ecc7`（取代 `a2e16d6e08eef731`）。

21. **⚠⚠ CO-99（L2 自裁 · PDN 施工就绪性）两个覆盖缺口 ⇒ PDN「可施工」= FAIL**：**G1** 既有闸只判 plan-vs-board（CO-91 `Scene` 仅由板构建）⇒ 计划集内部互冲零判；**G2** 项目规则源 `hole_clearance.same_net_exempt=True` 不含 KiCad 板配置 `min_hole_to_hole=0.25`（net-agnostic）⇒ 同网孔距盲。实测（scratch，交付板不变）：SPEC 宽 0.2 ⇒ **7 异网重叠（短路）+ 35 净距 + 39 孔距（2 同址）**；引擎宽 0.5 ⇒ 13 + 127；7 重叠全在 **U6 0.5mm 场**。**dry-run**：`pdn_apply` 实落后 DRC **42→274（+232）**、未连 348→191。**根因**：① 计划集互避缺失；② 短段宽 0.5 未读 SPEC；③ stitch 互距/去重缺失；④ 规则源缺 `min_hole_to_hole`。**影响**：布线链 G4..G7 PASS 不变；**PDN 可施工 = FAIL**。记录 `m13_v57_co99_pdn_mutual_conflict_gate.json` `1d256de815b1ed87` / 卡 `m13_v57_CO99_pdn_mutual_conflict_gate.md` `c47249d3538c1d8c` / 工具 `p3_v57_co99_pdn_mutual_conflict_gate.py` `78762b3d9de90fd4`。
22. **⚠ CO-100（L2 自裁 · PDN）互障感知修复候选 = `PARTIAL`**：声明 palette + 互障（板 + 已接受计划件）+ 孔距约束的确定性重放 ⇒ **残余异网重叠 0**，但 **5 项新增 blocked（4 ppc + 1 stitch）**（kept **124**/34/13、relocated **61**/5/4）（**CO-103 校正**：原记「6 项 / 5 ppc / 全在 U6 0.5mm 场」为过期读数）。**裁定**：互冲 L2 可解。**CO-103 校正**：该 5 项为**同网冗余竞争**（4 项 U6 相邻 GND 计划孔距互障 + 1 项 J2 扇出同址重孔对），与 CO-94 的板铜阻塞不同类；「须 via-in-pad/HDI」未被证明。**rev-12 决策点**：`(a)` 登记接受 5 blocked（纯 L2）或 `(b)` L2 冗余归并裁定。**未施加**。记录 `m13_v57_co100_pdn_mutual_repair_candidate.json` `11e21f3b97bac66b` / 卡 `m13_v57_CO100_pdn_mutual_repair_candidate.md` `ff1c267f74f578dc` / 工具 `p3_v57_co100_pdn_mutual_repair_candidate.py` `341314590ceb154a`。

23. **✅ CO-101（L2 自裁 · PDN 施加）rev-12 计划集互障重导（依 CO-99/CO-100）**：ppc entries **189→185**（kept 124 / relocated **61** / 新增 blocked **4**；blocked 120→124）；stitch relocated **5** + 新增 blocked **1**；zone relocated **4**；rev-11 坐标退役留存 `retired_superseded_mutual_conflict_v1`/`power_zones_via_retired_mutual_conflict_v1`；**F5** `board_realized` 同步 + **F1** `retired_superseded_bom` 回填。**链**：G4 `cb955e9af8782d08` / G5 PASS frozen=True / L4 viol 0 / L5 DFM new=0 + SI 0.1300 / **板逐字节 `0e636a67c1472462` 不变**。**PDN 闸**：**CO-99 = PASS**（0/0/0）｜CO-91 PASS(0/0)｜CO-92 CANDIDATE｜CO-95 OPEN(35/8/6/6)｜CO-98 OPEN(35/14/6)。**残余**：引擎 dry-run 仍 +34（施工侧短段宽/去重未同步）；5 项新增 blocked（4 ppc + 1 stitch）需 L2 冗余归并或显式登记接受（CO-103 F-B）。**复评债 = CO-102**。SPEC rev-12 `1a381b06454dbe2c`；记录 `m13_v57_co101_pdn_rev12_derive.json` `cdeea6a3950f04f6`；卡 `m13_v57_CO101_pdn_rev12_derive.md` `d47eda01e3092114`；工具 `p3_v57_co101_pdn_rev12_derive.py` `977ee54f0ecdb414`。

24. **✅ CO-102（L2 自裁 · 项目内引擎承载）修正版 PDN 施加器（施工侧闭合）**：冻结 `pdn_apply` 三处施工侧缺陷（短段宽字面量 0.5 / via 不去重 / blocked 口径）⇒ 新增**项目内**施加器（坐标逐字取自 SPEC、零搜索；短段宽读 SPEC `0.2`、via 去重、blocked 对齐）。**scratch 三态 DRC**：baseline **42** / 冻结 **76(+34)** / **项目内 42(+0)** ⇒ rev-12 PDN 施工 DRC-clean。**不改冻结 `_shared`**；`gnd_stitch_gen` 生成端缺陷不在在役路径。工具 `p3_v57_co102_pdn_apply_local.py` `945b7ae7942102be`；记录 `m13_v57_co102_pdn_local_apply.json` `44002f7eac6cfa49`；卡 `m13_v57_CO102_pdn_local_apply.md` `1df2be1ef5fc0e64`。

25. **✅ CO-103（L2 · 非执行者对抗复评）rev-12 新基线 = `PASS_WITH_FINDINGS`**：9 项机判（V1 幂等重导逐字节 / V2 palette 归属+固定序独立重放 / V3 登记完整性 / V4 clearance 与 CO-91 一致 / V5 计划集互判 / V6 CO-102 发射集等价 + 三态 DRC 42 / 76(+34) / 42(+0) / V7 blocked 成因分类 / V8 声明漂移扫描 / V9 链 pin）**全过**，牙齿 7/7；**0 项 pin 漂移**。**发现**：**F-A（中）**声明漂移 —— 原记「6 项新增 blocked（5 ppc + 1 stitch，全在 U6 0.5mm 场）」实为 **5 项（4 ppc + 1 stitch）**，第 5 项在 **J2 扇出** `(133.83,59.1)`；v1.69 已校正。**F-B（高）**4 项 U6 新增 blocked 的自身位置**对板铜干净**、阻塞全为**同网 GND 计划孔距互障**（相邻 U6 GND 计划 via，d=0.180–0.403 < 0.45）⇒「须 via-in-pad/HDI」**缺乏存在性证据**（换序探针 8/13/13 且每对幸存成员翻转）；与 CO-94 板铜类不同。**F-C（中）**收口件 §1 ㉛/§6-20 的 co95 现行身份引用陈旧（`61db48a283beeaae` → 现行 `f1c0c17ee7b379a4`）、CO-96 证书未声明自身失效，且 CO-77 的 `CITE` 抓不到散文式引用；v1.69 已注明已取代。**另记**：同网孔距口径经**合成注入实测**验证（kicad-cli 对同网 GND 孔对报 `hole_to_hole`，0.080 < 0.2495）⇒ CO-99 A4 口径忠实。工具 `p3_v57_co103_rev12_nonexecutor_review.py` `5e3f91d39130b83a` / 记录 `m13_v57_co103_rev12_nonexecutor_review.json` `7f481be259865941` / 卡 `m13_v57_CO103_rev12_nonexecutor_review.md` `6ac046a885508dc6`。

26. **✅ CO-104（L2 自裁 · 过孔策略/PDN）rev-12 新增 5 项 blocked 裁定 = `ACCEPT_L2_NO_HDI` + co96 fail-closed 加固**：依 `LAYOUT_CONSTITUTION` 第二章（过孔策略 / PDN 承载 = L2；层数 = L1）对 CO-103 F-B 的 4 项 U6 ppc + 1 项 J2 扇出 stitch 作裁。**三条出路逐条量化**：**A 共享单孔**（两 pad 中心**中点**派生位 + 双短段；零自由度、非搜索）仅 **1/4 对**可行（`FB34~FA32` 可行；其余 3 对的中点正落在 U6 另一球 pad `FF11`/`FF18`/`E11` 上）⇒ 收益 = 1 个 GND 球；**B 改声明固定序**（同 palette、同检测器）canonical **4** vs 13 / 8 / 13 ⇒ canonical 已最优、无免费解；**C 加宽 palette / via-in-pad / HDI** ⇒ 违零坐标搜索红线（CO-93/94 已驳）/ 无工艺 + SI-PI 证据 / 属 L1 且本件已证「须 HDI」不成立。**裁定 = 接受**（与既有 120 项 blocked 同类处理，显式登记不静默），**不升 owner、不重基线、rev-12 不变**；本项**不再构成 L1 问题**（若日后要求「U6 GND 球 100% 独立 via」为硬需求，须走 SPEC 变更 + 全链重基线 + 换会话复评）。**附带加固（CO-103 F-C 收口，fail-closed）**：co96 默认落点改为**重跑件**，显式指向历史证书即**拒绝写入（rc=2）**，除非 `--overwrite-canonical`⇒ 历史证书 `8b591e5030aca11d` 不再会被静默改写；重跑件 `m13_v57_co96_nonexecutor_review_pass4_rerun.json` `636b1ad728f0fa91` 即 CO-96 失效的**机判化声明**（verdict `BASELINE_MISMATCH`，`co95_json` 61db48a283beeaae → f1c0c17ee7b379a4）。工具 `p3_v57_co104_pdn_blocked_ruling.py` `7b2f3ff18e0ede04` / 记录 `m13_v57_co104_pdn_blocked_ruling.json` `7254226692cb8f93` / 卡 `m13_v57_CO104_pdn_blocked_ruling.md` `ed2587023fe05ed6`。
27. **✅ CO-105（L2 自裁 · PDN 建模）CO-96 F4 落定 = `CLOSE_NO_SCOPE_EXTENSION`**：把 CO-98 的「声明排除」机判化。**V1 语义不可适用**：requirement 判据 =「落于本网 In4 铜」，而 GND 平面层 = `In1/In3/In6`、In4 仅 `P3V3/MCU_VDD/P3V3_AUX` ⇒ 对 **130 GND ppc entry + 40 GND stitch via** 无可判定（≠『未覆盖』）；requirement 对象 = 非 GND ppc entry **55**。**V2 几何待 L3**：17 个 `power_zones[].vias` **17/17** 位于 3 个 bridge zone（`P3V3_BCU_BRIDGE_IN4` 3 / `P3V3_AUX_BCU_BRIDGE_IN4` 8 / `MCU_VDD_BCU_RESISTORS_IN4` 6），其 `polygons=[]`、`geometry_status=L3_CONSTRUCTION_DERIVED` ⇒ 与 CO-98 `declared_pending_l3` 同桶；扩 scope 只并入待派生清单、不新增可判缺陷。**V3** 施工路径对 `gnd_stitch_gen` 的**代码引用 = 0**（散文复盘 1）⇒ 生成端缺陷 latent、不在在役路径。**V4** `R1.2` 判据根因 = 电源域/区域归属 = **L1**（不在本件）。**裁定 = 关闭 F4，不做 scope 扩展**；零 SPEC/板/阈值/冻结源改动、不需重基线、不需新复评。牙齿 2/2（GND 平层不含 In4 而 In4 确被占 / 17 项空几何而存在有几何 zone）。工具 `p3_v57_co105_f4_scope_disposition.py` `f357f81142161e61` / 记录 `m13_v57_co105_f4_scope_disposition.json` `116f83fae67d1bb8` / 卡 `m13_v57_CO105_f4_scope_disposition.md` `c40b94566b0ba3e9`。
28. **⚠→✅ CO-106（L2 · 覆盖性补全）参考平面判据 + 连续性机判**：ch.2 的 L2 裁判标准含「参考平面」，而 CO-87 记录**自报**的判据集含该词、覆盖矩阵却只有五行（参考平面无决策行/无闸）⇒ 本件补上判据并机判：**A 板框一致性**（声明多边形 = 冻结板框按 `edge_copper_min` 内缩）＋ **B 参考平面连续性**（每条规划走线每点须落在其 `impedance.per_layer[layer].refs` 任一参考层声明铜内；分类 `declared_copper_missing`（GND 整面层缺铜=缺陷）vs `region_scoped_indeterminate`（In4 按电源区裁剪/桥区待派生））＋ **C 板实佐证** ＋ **D 覆盖性补全声明**；牙齿 3/3（合成负控/正控）。**rev-12 判 `FAIL_DECLARED_COPPER_MISSING`**：60 点/36 段（In2 24 + In5 12）；根因 = 3×GND + 2×In4 多边形下边 **70.7 = 33+38−0.3**（旧 38mm 板框）而现行板框 `outline_y [33,79]`（v28 ECO y 38→46mm）⇒ 按自身 basis 应为 **78.7**；后果 = 框内平面外 **8.3mm 带无参考平面**，而施工已用该带（板实 **In5 316 段 + In2 12 段 + 24 via**，PCIe `PCIE_DN2..DN7` 蛇形恰在其中）。修复 = CO-107。工具 `p3_v57_co106_reference_plane_gate.py` `84eeea00d8e987cb` / 记录 `m13_v57_co106_reference_plane_gate.json` `9f131d72e4780afb` / 卡 `m13_v57_CO106_reference_plane_gate.md` `08b46fff2a07e45a`。

29. **✅ CO-107（L2 自裁 · PDN/平面分配）SPEC rev-13 = 平面随板框对齐**：把 3×GND(In1/In3/In6) + 2×In4(`P3V3_EAST`/`MCU_VDD_WEST`) 多边形下边 **70.7 → 78.7**（与各自 basis「整面铺铜 + 板边内缩 0.3」一致），rev-12 原多边形**退役留存** `pd.zone_defs.retired_superseded_frame_extent_v1`；**只改 polygon 顶点 + `spec_version`**（阈值/网/层角色/坐标集/短段宽/blocked 台账/冻结源未动）。**几何不变性机判**：新图纸 `route_geometry`/`pages`/`landing_rows` 与 rev-12 **逐字节同**（仅 `inputs_sha.spec` 与 `frozen_sha_check` 变）⇒ 板 **`0e636a67c1472462` 逐字节不变**。SPEC rev-13 `7943be727a4f8ef9`；G4 **FEASIBLE_ALL**（34 页/crossings 0/work 546/546）主件 `73c0066df83fa8c2`；G5 PASS frozen=True；G6 PASS viol 0；G7 FAB ok + DFM new=0 + 在册未连 0/68 + SI skew 0.1300；**CO-106 复判 → `INDETERMINATE_REGION_SCOPED`（`declared_copper_missing`=0）**；链 pin 同批前移（引擎 `/FROZEN_SHA`、validator `/prefix`+`FROZEN`、闸默认 spec co78/81/84/91/92/95/98/99/102/104/105/106、co77 正则）。**复评债 = CO-108（须另一会话）**。工具 `p3_v57_co107_spec_rev13_frame_align.py` / 记录 `m13_v57_co107_spec_rev13_frame_align.json` / 卡 `m13_v57_CO107_spec_rev13_frame_align.md`。
30. **⚠→✅ CO-108（L2 · 非执行者对抗复评）rev-13 新基线 = `PASS_WITH_FINDINGS`**：独立机判 —— rev-13 差分恰为 10 polygon 顶点 + `spec_version`；退役留存 5 项完整（old=rev-12 / new=rev-13，无静默放弃）；几何（`route_geometry`/`pages`/`landing_rows`）与板 `0e636a67c1472462` 逐字节不变；链 pin 全数前移（记录内 provenance pin 全一致）；**参考平面独立点级全量重算 GND 面缺铜 = 0**、残余 54 段 100% 落 L3 桥带；**rev-12 FAIL 独立复现**（60 项/36 段 + 板实已用 8.3mm 带 In5 316 / In2 12 / VIA 24）⇒ CO-107 真修复；牙齿 3/3。**F-A（low，已校正）**：CO-105 记录 `inputs.co98_record` 在 `04d0ee1` 为陈旧值（非当时 co98）⇒ 确定性重跑恢复 `48b5bd29009a9eb8`、记录 sha→`a53f7e3b75d3d427`，本件 v1.73 同步引用。**F-B（信息性）** CO-106 字段计法非点数（不影响结论）。**F-C（low，已声明）** co87 矩阵无「参考平面」行。**F-D（medium，未决前提）** bridge zone `layer=In4.Cu` vs 名/`basis` 经 **B.Cu** 桥接（P3V3『In4 走线带不跨』）⇒『几何待 L3 派生』前提未证实；L3 派生 work order 须先裁派生层归属（若取 basis 口径则 54 段 In5←In4 为永久参考缺失 ⇒ L2）。工具 `p3_v57_co108_rev13_nonexecutor_review.py` `a745c2695e92b0e6` / 记录 `m13_v57_co108_rev13_nonexecutor_review.json` `f1ff40a43614a9e8` / 卡 `m13_v57_CO108_rev13_nonexecutor_review.md` `a00d7d89a5106c7d`。
31. **⚠→⏹ CO-109（L2 自裁 · 参考平面/PDN）In5←In4 走廊空洞 = 按设计；bridge zone = B.Cu**：由 CO-108 F-D 触发。证据：3 个 bridge zone 的声明 band 仅覆盖 In5←In4 miss 点 **6.0%**（75/1260），In4 走廊覆盖 **100%**；板 L4 无 zone ⇒ 无可派生的走廊 In4 几何。裁定：桥接层 = **B.Cu**；走廊空洞按设计（PM T2-ECN『In4 走线带不跨』）；CO-106 的 `region_scoped_indeterminate` 前提不成立（该带 In5 实为仅 In6 参考，与 `symmetric_stripline(refs=[In4,In6])` 不符）⇒ 应改判『按设计 In4 空洞』+ SI 待验登记。**OWNER（停）**：是否允许走廊补 In4 铜（反转 PM 裁决）。step ② 重定范围（②a 声明修正 / ②b SI 终判 / ②c B.Cu 几何声明缺 palette / ②d 换会话复评）。工具 `p3_v57_co109_in4_void_l2_ruling.py` `2e35c139476ae016` / 记录 `m13_v57_co109_in4_void_l2_ruling.json` `dd562f526705abef` / 卡 `m13_v57_CO109_in4_void_l2_ruling.md` `583ac243a4cf3428`。
32. **✅ CO-110（L2 自裁 · 施加）参考平面入 CO-87 矩阵 + CO-106 D 读径修复 + In4 走廊空洞按设计定案（R5'）**：(a) F-C — CO-87 矩阵补 ch.2「参考平面」行（`INDETERMINATE`，机取自 CO-106），牙齿 `ch2_criteria_all_have_rows`。(b) F-E（新发现）— CO-106 D 项读径错误致覆盖性检查恒空真，已改读 `constitution.ch2_l2_criteria`+顶层 `matrix`，复跑 `has_reference_plane_row=true`。(c) F-D/R5' — 不开 In4 走廊铜（确认 PM 既有设计）⇒ CO-109 OWNER 升级撤回；In5 该带 = In6-单参考域，SI 终判外部。零 SPEC/板改动 ⇒ 不重基线。工具 `p3_v57_co110_l2_coverage_closure.py` `354aef88cdac7634` / 记录 `m13_v57_co110_l2_coverage_closure.json` `6564e51f6ade544e` / 卡 `m13_v57_CO110_l2_coverage_closure.md` `82d2b176d45d1527`。
33. **⚠ CO-111（L2 自裁 · 参考平面/阻抗）In5 PCIe 走廊参考缺失 = 40.1%**：In4 走廊内无声明铜 ⇒ In5 走线裸露长度 **1094.8/2727.3mm（40.1%）**，16 网全为 PCIe85 差分对（最差 `PCIE_UP4` 108.7mm/50.5%）。L5 SI 只签 skew、**未签阻抗** ⇒ 暴露未验。终判 = SI9000+板厂券（外部）；补救层级 = 补 In4 铜（OWNER）/(b) 改线换层（或 L1）/(c) 走廊段宽-隙补偿（L2）。工具 `p3_v57_co111_in5_pcie_corridor_exposure.py` `c586f2a49742e137` / 记录 `m13_v57_co111_in5_pcie_corridor_exposure.json` `9ae53dbf3cfc48e1` / 卡 `m13_v57_CO111_in5_pcie_corridor_exposure.md` `09fb8d2656b5b27d`。
34. **✅ CO-112（L2 自裁 · 声明式施加）3 bridge zone = B.Cu 桥（step ②c）**：前两 zone band 取自 basis 文本、MCU_VDD 取声明 via bbox（provisional）；In4-可达性 requirement 对这 3 zone 的 targets **语义 N/A**（镜像 CO-105）；In5 区域条件参考口径（走廊 = In6-单参考）+ 走廊逐网 worklist。零 SPEC/板改动、不重基线。**In5 PCIe 阻抗暴露（CO-111）不因本件减轻**。工具 `p3_v57_co112_bcu_bridge_declaration.py` `4bda33760ad2d196` / 记录 `m13_v57_co112_bcu_bridge_declaration.json` `5f621c3c1003be00` / 卡 `m13_v57_CO112_bcu_bridge_declaration.md` `e36fc9ad1a244425`。
35. **✅ CO-113（L2 自裁 · 施加）SPEC rev-14 = 裁定写入 canonical SPEC（step ② ②a）**：仅新增声明键（走廊空洞按设计 / bridge center = B.Cu + 声明带 / 可达性 N/A scope），既有标量只 `spec_version` 变；新键无消费者 ⇒ 读数不变；几何与板逐字节不变；链 pin 同批前移。工具 `p3_v57_co113_spec_rev14_declare.py` `4c885825a6cecf60` / 记录 `m13_v57_co113_spec_rev14_declare.json` `261fa00af228be4a` / 卡 `m13_v57_CO113_spec_rev14_declare.md` `29554ef222ec2e79`。
36. **⚠ 更正 CO-115（L2 自裁 · 事实更正）In4 走廊空洞 = 失效 keepout 残留（待 L3 派生），非按设计**：走廊边界 49.8 = 退役 keepout 50.0−0.2、88.37 = 88.17+0.2；CO-95 effect「In4 铜可在原 band 内按网归属铺设」⇒ CO-109/110/113 的「按设计」判定**更正**；In5 40.1% 暴露**可修**；rev-14 键须 rev-15 更正。**OWNER/L1 停点**：band 内铺铜的区域归属界面。工具 `p3_v57_co115_corridor_stale_keepout_correction.py` `f5d0007766677616` / 记录 `m13_v57_co115_corridor_stale_keepout_correction.json` `b200828cb797817e` / 卡 `m13_v57_CO115_corridor_stale_keepout_correction.md` `700f4c6d6c226059`。
37. **⚠ CO-114（L2 · **非执行者**对抗复评）rev-14 = `PASS_WITH_FINDINGS`**：六面机判全 True + 9 牙齿；机械声明成立（仅新增声明键 / 几何与板逐字节同 / SPEC pin 前移 / 新键零消费者）。**6 发现**：F-1 high（rev-14 错误键，待 rev-15）｜F-2 medium（co87 证据文本陈旧）｜**F-6 medium（rev-14 重基线致 4 记录 5 处 inter-record provenance pin 陈旧**，与 CO-108 F-A 同族、CO-77 盲区）｜F-3 low（CO-113 new_keys 少声明 `bcu_bridge_bands_source`）｜F-4 low（CO-111 措辞）｜F-5 info（已由 v1.81 更正）。
## 7. 归档
变更单 CO-05..CO-46 记录与 DRC 明细（`m13_v57_co41_refclk_drc_after.json` / `m13_v57_co43_refclk_drc_after.json` /
`m13_v57_CO45_refclk_skew_meander_impl_record.md` `7b8cb5b1294d8c71` /
`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98` /
`m13_v57_CO47_l5_inscope_connectivity_predicate.md` `031fc91aa520cb92` /
`m13_v57_CO48_l5_g7_record_emit.md` `7e094c2db5bf3b3d` /
`m13_v57_CO49_l4_byte_reproducible.md` `6c27149fff749a1d` /
`m13_v57_CO50_pdn_fact_verified.md` `311e98163d49ac82` /
`m13_v57_CO51_dfm_multiset_metric.md` `922feaf4b5c8c143` /
`m13_v57_CO52_via_budget_closure.md` `eaaea6b5e4456ddc` /
`m13_v57_CO53_intrapair_geometry_impedance_open.md` `36f16620c7132da6` /
`m13_v57_CO58_interpair_baseline_reconciliation.md` `267621cdcfae1bbc` /
`m13_v57_CO59_L2_residual_closure_and_interpair_target.md` `0fdb19fec39bf110` /
`m13_v57_CO67_L2_redline_ruling.md` `c562419d70a41ab9` /
`m13_v57_CO68_L2_option_a_execute.md` `17965908fd5d5635` /
`m13_v57_CO69_L2_option_a_chain.md` `661ad6c57e0e2418` /
`m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`（CO-79 加固后，10/10） /
`m13_v57_co72_pdn_align.json` /
`m13_v57_co73_layer_role_consistency.json` /
`m13_v57_CO74_L2_pdn_bcu_rehost.md` `8c1cec7fb48ad2ab` /
`m13_v57_co74_pdn_bcu_rehost.json` `8e3bbfb0e197cf67` /
`m13_v57_co74_chain.json` `51dbb2076bc379e4` /
`m13_v57_CO75_L2_west_pitch_origin_search.md` /
`m13_v57_co75_west_pitch_origin_search.json` `c59e9955d344d75f` /
`m13_v57_CO76_nonexecutor_adversarial_review.md` `32d5868a1a2880b4` /
`m13_v57_co76_nonexecutor_review.json` `cf5b4ec0e880e5d2` /
`m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`（CO-79 加固后，10/10） /
`m13_v57_co77_closure_declaration_sweep.json` /
`m13_v57_CO77_closure_declaration_sweep.md` /
`m13_v57_CO78_layer_role_drift_gate.md` `0185363ec8ddf5f7` /
`m13_v57_co78_layer_role_drift_gate.json` `1235a9a957fcc0cd` /
`m13_v57_CO79_probe_vacuity_hardening.md` /
`m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`（CO-79 加固后） /
`m13_v57_CO80_l4_project_rule_align.md` `07cbdea3d139927a` /
`m13_v57_co80_l4_project_rule_align.json` `d617a4c5e4e4523f` /
`m13_v57_CO81_project_rules_gate.md` /
`m13_v57_co81_project_rules_gate.json` `adba2152d4f10fd4`（CO-89 重扫 rev-9 后；原 `ebd163058efaad14`、`a9161a86271c068b`、`1f25c6a9db6923f0` 已取代） /
`m13_v57_CO82_project_netclass_gap.md` `0d0d6e7640fa970e` /
`m13_v57_co82_l4_project_netclass_align.json` `0c8745064785ee57` /
`m13_v57_CO83_netclass_vs_spec_gate.md` `47ebff527cc431ef` /
`m13_v57_CO84_dru_domain_gate.md` `996bee590912e823` /
`m13_v57_co84_dru_domain_gate.json` `6f1a2ccfaf916627` /
`m13_v57_co85_nonexecutor_review_pass2.json` /
`m13_v57_CO85_nonexecutor_adversarial_review_pass2.md` /
`m13_v57_co86_l2_span_option_closure.json` `d0a59f85b74687d5` /
`m13_v57_CO86_l2_span_option_closure.md` `0d1fd3b33fb802fe` /
`m13_v57_co87_l2_acceptance_coverage.json` `46d15557477d164b` /
`m13_v57_CO87_l2_acceptance_coverage.md` `322baa098740b259` /
`m13_v57_co88_pdn_board_reality_gate.json` `f90d65369cab92dc`（已取代：CO-90 重生成 `bf69909aa64dc494`）/
`m13_v57_CO88_pdn_board_reality_gate.md` `50aa8c67d7b10438` /
`m13_v57_co89_pdn_board_realize_rev9.json` `4f94df5981aaab45` /
`m13_v57_CO89_pdn_board_realize_spec_rev9.md` `7ed85bbda42ad1b1` /
`m13_v57_co90_nonexecutor_review_pass3.json` `badba5d9ce39a022`（CO-90.2 实测值；v1.55 曾引 `897ff5cc371d135d` 为过期值 ⇒ co77 报 CITATION_MISMATCH，本版修正；原 `3ba2ca0ce3966fe8`、`98651571b93a07a9` 已取代） /
`m13_v57_CO90_nonexecutor_adversarial_review_pass3.md` `be00ceedae5f7786`（引用校正 + F4/F5 入册后） /
`m13_v57_co88_pdn_board_reality_gate.json` `17719cf7f8e3e702`（CO-90 F1/F2/F4 修复后，CO-88.3；原 `f90d65369cab92dc` 已取代）/
`m13_v57_co77_closure_declaration_sweep.json` / `m13_v57_CO77_closure_declaration_sweep.md` /
`m13_v57_co91_pdn_planned_coord_clearance_gate.json` `3ede251a830108f1` /
`m13_v57_CO91_pdn_planned_coord_clearance_gate.md` `1b83f41f37bf96f5` /
`p3_v57_co91_pdn_planned_coord_clearance_gate.py` `25be5b6053e67229` /
`m13_v57_co92_pdn_repair_candidate.json` `7aaacd8f34559763` /
`m13_v57_CO92_pdn_repair_candidate.md` `6de3c9fb2b26d45d` /
`p3_v57_co92_pdn_repair_candidate.py` `c9c86706fbab5aff`）已入库；**本件取代 v1.60**；v1.55..v1.58 原样保留不改（v1.55 的 co90 过期引用已在 v1.56 修正；CO-91 的 fix_candidate 已在 CO-91.3/CO-92 作废替代；CO-91 对 rev-9 的 FAIL 判定与 CO-92 备料读数均为留档，现行判定见本版）。
监理/tag 政策：`k2-v57-g7-l5-pass`（G7/L5 PASS）已 push；`git ls-remote` 核验 `^{}` → `b5afe47`。

End of boundary v1.61（含 CO-67..CO-95）。

### 附：CO-114 本件产物（v1.81 新增）
`p3_v57_co114_rev14_nonexecutor_review.py` `6642f8156e349c24` /
`m13_v57_co114_rev14_nonexecutor_review.json` `20adc9fb67e62c63` /
`m13_v57_CO114_rev14_nonexecutor_review.md` `ab0da32774a0714d`

End of boundary **v1.81**（含 CO-67..CO-115；+ CO-114 非执行者对抗复评）。

---

## 附：CO-117（L2 自裁 · band In4 铺铜归属 + SPEC rev-15）当前态引用

现行 L4 板 **`d4e81f647be7f980`**（CO-133 施工后）。收口件内 sha 一律为**当前文件实测值**。

- SPEC rev-15（CO-117 施加件） `SPEC_k2_v4.spec-rev-15.json` `48d6fc7c565c8862`（已取代，历史）
- SPEC rev-16（已取代，历史；CO-122b 施加） `SPEC_k2_v4.spec-rev-16.json` `5748828a23161250`
- SPEC rev-17（**现行**；CO-130 施加：D-6 网类 12V_IN→POWER + 退役三 zone 的 B.Cu 载体声明 + stackup In4 文本对齐） `SPEC_k2_v4.spec-rev-17.json` `9fea9fd20149c736`
- G4 主件图纸 `m13_v57_w3_joint_assignment.json` `60cbd331836e52b7`
- G5 校验 `m13_v57_w3_validation.json` `8b385d6c554ac527`
- L4 施工 `m13_v57_l4_construction.json` `d11a38519482b0cf`
- L4 校验 `m13_v57_l4_validation.json` `aa666a49e36883c7`
- L5 fab `m13_v57_l5_fab_record.json` `791012e88b514faa`
- L5 SI `m13_v57_l5_si_pi_emc_record.json` `261b58e745c67aea`
- co95 记录 `m13_v57_co95_in4_reachability.json` `4525e38330ee599f`
- co98 记录 `m13_v57_co98_reachability_status_report.json` `a29b802163bca3d9`
- co87 记录 `m13_v57_co87_l2_acceptance_coverage.json` `46d15557477d164b`
- co105 记录 `m13_v57_co105_f4_scope_disposition.json` `116f83fae67d1bb8`
- co106 记录 `m13_v57_co106_reference_plane_gate.json` `9f131d72e4780afb`
- co99 记录 `m13_v57_co99_pdn_mutual_conflict_gate.json` `1d256de815b1ed87`
- co91 记录 `m13_v57_co91_pdn_planned_coord_clearance_gate.json` `3ede251a830108f1`
- co92 记录 `m13_v57_co92_pdn_repair_candidate.json` `7aaacd8f34559763`
- co104 记录 `m13_v57_co104_pdn_blocked_ruling.json` `7254226692cb8f93`
- co102 记录 `m13_v57_co102_pdn_local_apply.json` `44002f7eac6cfa49`
- co69 记录 `m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`
- co117 记录 `m13_v57_co117_band_allocation_rev15.json` `957c7c5ffd8e8a81`
- co117 卡 `m13_v57_CO117_band_allocation_rev15.md` `0b8a747960ce0fe1`

- 工具 `p3_v57_co117_band_allocation_rev15.py` `f1db632708f66f7d`

**L2 判定**：band In4 铺铜归属 = 走廊分配/PDN 架构（《宪法》ch.2 = L2），且 L2 **裁判标准**含『参考平面』；冻结 L1 仅**粗分区 + 域集合**，域集合不变 ⇒ L2（先例 **CO-74**）。**分配（零搜索）**：`MCU_VDD_WEST` 东缘 49.8→**57.75**（R29/R31-R34 57.55 + 0.2）；`P3V3_EAST` 西缘 88.37→**57.95**（余下走廊归东侧权域）；**In5 单参考暴露 40.14%→0.21%**（残余 = 强制 0.2mm POWER 异网净距缝）。**SPEC rev-15**：`in4_corridor_void_by_design_v1`（CO-115 判错）→ 退役留存 `retired_in4_corridor_void_by_design_v1`；新增 `in4_band_copper_allocation_v1`；P3V3 由 `unresolved` → `resolved_by_co117`（U6 6 球）；co98 三态 **45/4/6**（原 35/14/6）。板/G7 DFM/SI 不变。**复评债 = CO-114 rev-15 半程（另一会话）。**

---

## 附二：L2 闭合声明 + L1 待裁（决策就绪；本段不代填、不推荐分区）

**L2 闭合**：band In4 铺铜归属（CO-117，rev-15）+ In5 走廊参考缺失已闭合至外部终判；co95 复算 = `covered_explicit` **45** / `covered_bridge_target` **4** / **`l3_obligation` = 0** / `needs_region_ruling` **6**；co98 三态 **45 / 4 / 6**。L2 侧**无可自裁剩余项**。

**L1 待裁（《宪法》ch.2：电源域划分；域集合变更 ⇒ L1）**（**② 已由 CO-121 判为 L2 并于 CO-122b 施加 ⇒ 下表 ② 行已被更正行取代**；第 ④ 项为 CO-118 新发现）。以下为 owner 决策所需的**声明事实 + L2 结构可行性预检**（机判，零搜索；不代填、不推荐分区）：

**西区 via 布局（rev-15 声明，机判）** —— `12V_IN`：C88.1(28.275,41.5) / U2.4(31.05,39.83) / U2.6(35.725,37.635)；`MCU_VDD`(10)：C86.1(30.275,56.0) / C85.1(30.475,54.5) / U1.6(36.75,49.775) / U4.2(40.95,38.775) / E2.2(41.275,59.365) / E2.8(45.95,57.17) / R31-R34.2(56.725, 66.5/67.5/68.5/69.5)；`P3V3_AUX`：C90.1(28.975,53.0) / U1.15(39.425,53.25) / R1.2(51.725,37.0)（J4.A9 已由桥区声明覆盖）。

| # | L1 议题 | 声明事实（rev-15 机判） | L2 结构可行性预检（机判） |
|---|---|---|---|
| ① | `12V_IN` 承载 | 3 pad 无任何 In4 区（C88.1/U2.4/U2.6，簇于 x28–36 / y37–41.5）；`pd.decoupling` 含 `12V_IN{C88}`、`power_pad_connect.board_realized.pwr_nets` 含 `12V_IN` ⇒ **是 PDN 网**（非 scope 伪项） | 若定为 In4 新区 ⇒ **域集合 +1（L1）**；pocket 几何余量充足（`MCU_VDD_WEST` 内 x/y 边距 ≥4.1mm）**但**簇 bbox `[28.275,37.635]–[35.725,41.5]` **内夹 `U2.5`(P3V3) + `C88.2`(GND)** ⇒ 凸 pocket 围异网 via ⇒ 形状非闭式（依赖走线搜索）⇒ **与 ④ 同源、L2 不可自裁**；另一路径（改 F.Cu 走线承载）⇒ 网范围/电源域口径 ⇒ owner |
| ② | `P3V3_AUX` 西区归属 | **已闭合：CO-121【L2 自裁】裁定 + CO-122b 施加（SPEC rev-16）** | **层级更正**：冻结 L1 实测仅含域集合 + 粗分区，本件二者不变 ⇒ L2（先例 CO-74；判据同 CO-117 `level_basis`）；原列『L1 待裁』系过高归口。**机判**（声明式有限家族，零搜索）：净距 **0.375** 系闭式（POWER 0.2 + via_od/2，孔规则更松）；行内异网 via（C90.2/U5.2）与之同 y、且 R28.2(GND) 与 R1.2 同 x ⇒ 直连带/柱必重叠 ⇒ 取绕行侧 below + 柱绕；**五测全过**、worst margin **0.100mm**、min_merge 0.300、牙齿 **3/3**。**施加**：`P3V3_AUX_WEST` 单环 zone（6 声明矩形闭式并集；co95 读 singular `polygon`）+ `in4_west_aux_allocation_v1` + `resolved_by_co121`；**L4 板逐字节不变** |
| ③ | ~~L1① 对间净空 0.875~~ | **已闭合（CO-134，L2 自裁）**：③ = **工程换算错误**（非需求）；REQ-R3-2「3W 原则」忠实实现 = 对间铜边 ≥ 2×w（按层：外层 0.410 / 内层 0.320）⇒ SPEC rev-19 施加 + 0.875 退役；**撤回 owner 升级（无 owner 项）**；域外板实偏差 3 处已登记为工程开放项 ⇒ SI/板厂券 或后续几何迭代 |
| ④ | **B.Cu 桥冲突（CO-118）** | CO-74 `bcu_power_copper_policy=PROHIBITED`（『不得铺电力铜/**搭桥**』）↔ CO-112 三桥区 `bridge_layer="B.Cu"` + `na_scope_v1.bcu_bridge_zone_targets` N/A 裁定（同批 zone 的 `carrier_change` 又写 `B.Cu→In4.Cu`） | 若禁令成立 ⇒ **4 target 无载体**：P3V3 `C84.1/U2.5/U4.3` **落在 `MCU_VDD_WEST` 内**、P3V3_AUX `J4.A9` 落在 `P3V3_EAST` 内 ⇒ **R1**（L2 In4 pocket，受 requirement ④ 同网连通约束、可能不可行）或 **R2**（owner 放宽红线）。**CO-118 追加机判**：`P3V3_BCU_BRIDGE_IN4` 簇 bbox 内夹异网 via `U4.2`(MCU_VDD)/`U2.6`(12V_IN) ⇒ 凸 pocket 会围住异网 via ⇒ 形状非闭式（依赖走线搜索）⇒ **R1 不能在 L2 自裁** ⇒ 本项闭合归 owner（R2/红线或 L1） |

**板实旁证**：交付板 `k2_v4_8L.l4.kicad_pcb` `d4e81f647be7f980`（**CO-133 施工后**）= 图纸 2708 track/252 via **+** PDN 185 短段/241 via/9 zone（In4 含 `12V_IN_IN4_CARRIER`/`P3V3_AUX_WEST`/两桥区，3 区 `fill_priority=1`）；**施工前** `0e636a67c1472462` 为零 PDN 铜 ⇒ 本议题的承载/归属裁决仍属 **SPEC 声明层**，板实为其确定性物理实现。

**L2 过程闸（CO-120，新）**：`p3_v57_co120_provenance_pin_gate.py` `0775970667f2552f`、记录 `m13_v57_co120_provenance_pin_gate.json` `c1b0cb595438f381`、卡 `m13_v57_CO120_provenance_pin_gate.md` `bc6ca56de45fda27` —— 关闭 CO-108/CO-114 **F-6 盲区**（记录内 inter-record provenance pin 一致性）；首跑 **PASS**（pins 12：match 8 / 豁免历史 3 / 未声明陈旧 0 / 解析歧义 1；牙齿 2/2）。

## 11. CO-133（L2 自裁 · 施工期物理施加）当前态引用

**结论**：rev-18 SPEC 声明的 PDN 铜**已物理落板** ⇒ 板 `0e636a67c1472462` → **`d4e81f647be7f980`**。
板实 vs SPEC **逐项相等**（9 zone 含 `fill_priority` / 241 via / 185 F.Cu 短段）；kicad-cli `--severity-all` 违规**类型逐项同**（42/42）、未连项 348→179；
L4-A..F 仍 **viol 0**；L5 FAB ok / DFM new=0 / SI 0.1300；co95 55/55、co98 55/0/0；G4/G5 不动。

**施加机制**：项目内 applier 追加④ **幂等 purge-then-add**（删本阶段将重发的 PDN 网铜；pcbnew 删除走 `RemoveNative` —— `Remove` 会泄漏并使 `GetTracks()` 退化）+
CO-49 `canonicalize_board` ⇒ 净板/已施工板两次投喂**同一字节**（实测重跑后板 sha 不变）。

**连带更正（显式登记，见 `input_defect_register_v1.json`）**：
1. **co91 孔缘分支多扣一次 `via_r`**（与其自身 `drc_rules.json` geometry_translation 相悖）⇒ 施工后 14 项假阳性；更正后 0/0（真值 +0.284 / req 0.25；copper gap +0.209）。
2. **co104 replay 场景**改排除计划自身网（板态无关）+ V3 断言/verdict 改数据派生；残留：canonical replay 3 vs 声明 blocked 4 ⇒ 声明**偏保守 1 项**（无功能影响）。
3. **provenance pin**：co105←co98 随重跑刷新；co111←l5_si / co118←co95 属 point-in-time ⇒ co120 EXEMPT 明列理由。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co133_pdn_construction_apply.py` | `1947f3c0332d57fc` |
| 记录 `m13_v57_co133_pdn_construction_apply.json` | `62a9931227281c10` |
| 卡 `m13_v57_CO133_pdn_construction_apply.md` | `d3ba4233a61403c0` |
| applier `p3_v57_co102_pdn_apply_local.py`（幂等+RemoveNative） | `945b7ae7942102be` |
| 板 `k2_v4_8L.l4.kicad_pcb`（施工后） | `d4e81f647be7f980` |
| `m13_v57_l4_validation.json` | `aa666a49e36883c7` |
| `m13_v57_l5_fab_record.json` | `791012e88b514faa` |
| `m13_v57_l5_si_pi_emc_record.json` | `261b58e745c67aea` |
| `m13_v57_co91_pdn_planned_coord_clearance_gate.json` | `3ede251a830108f1` |
| `m13_v57_co104_pdn_blocked_ruling.json` | `7254226692cb8f93` |
| `m13_v57_co97_retirement_retention_gate.json` | `4b1ee8924147a4f4` |
| `m13_v57_co98_reachability_status_report.json` | `a29b802163bca3d9` |
| `m13_v57_co99_pdn_mutual_conflict_gate.json` | `1d256de815b1ed87` |
| `m13_v57_co102_pdn_local_apply.json` | `44002f7eac6cfa49` |
| `m13_v57_co105_f4_scope_disposition.json` | `116f83fae67d1bb8` |
| `m13_v57_co106_reference_plane_gate.json` | `9f131d72e4780afb` |
| `m13_v57_co120_provenance_pin_gate.json` | `c1b0cb595438f381` |
| `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| `m13_v57_co88_pdn_board_reality_gate.json` | `17719cf7f8e3e702` |
| `m13_v57_co78_layer_role_drift_gate.json` | `1235a9a957fcc0cd` |
| `m13_v57_co81_project_rules_gate.json` | `adba2152d4f10fd4` |
| `m13_v57_co84_dru_domain_gate.json` | `6f1a2ccfaf916627` |
| `input_defect_register_v1.json`（含 CO-133 三条工具缺陷登记） | `dd9f79eb0aaec2a1` |

**未决（不变）**：非执行者复评（本件 + rev-18 新基线）；③ 已撤回 owner 升级（CO-134 判为工程换算错误并落地忠实实现）；外部输入（板厂券/SI9000、PM 压降·热）。

## 12. CO-134（L2 自裁 · 需求/实现分家｜整改通知 #09）当前态引用

**③ 撤回 owner 升级**：0.875 系**工程换算错误**（= 2×0.4375；本板无任何层/带使用该线宽），非需求。
**需求（冻结）** `REQ-R3-2` = 对间不串扰 ⇒ 3W 原则：对间中心距 ≥ 3×线宽 w。
**忠实实现（工程迭代）** `DV-INTPAIR-EDGE`：对间铜边净空 ≥ 2×w（按层：F/B 0.410、In2/In5 0.320；带内下界 0.180）⇒
SPEC **rev-19** `5f72182a2616392c`（白名单外 0 改动；0.875 退役留存 `retired_inter_pair_spacing_0p875_v1`）。
**可达性（闭式）** REACHABLE：域外 span_min 0.355 + 0.410 = 0.765 ≤ cap（WEST 1.05 / EAST 1.449）；焊盘场属 ECN-001 escape 域（已声明放宽）。
**板实（实测）** 域外偏差 3 处（工程开放项，非 owner）：F.Cu 0.3294（−0.0806）/ B.Cu 0.3450（−0.0650）/ In5.Cu 0.3125（−0.0075）⇒ 路由 SI/板厂券 或后续几何迭代。
**几何不动**：板仍 `d4e81f647be7f980`（rev-19 仅改声明定值）；G4 主件重基线（几何/交叉不变）。

| 工件 | sha16 |
|---|---|
| 规矩件 `REQUIREMENT_IMPLEMENTATION_SEPARATION_v1.0.md` | `0181186c4b4266e1` |
| 台账 `derived_value_ledger_v1.json` | `b88d69dbc7a0dd51` |
| 定义件 `BASIC_SKILL_VS_REDLINE_v1.1.md`（③ 重新定性 bump） | `348735156c9d9b1d` |
| 工具 `p3_v57_co134_req_impl_separation.py` | `8f59c5be82fe9d06` |
| 记录 `m13_v57_co134_req_impl_separation.json` | `1e5aa8503d211411` |
| 卡 `m13_v57_CO134_req_impl_separation.md` | `813e66a5eb4b0e60` |
| 登记簿 `input_defect_register_v1.json` | `dd9f79eb0aaec2a1` |
| `SPEC_k2_v4.spec-rev-19.json` | `5f72182a2616392c` |
| `m13_v57_w3_joint_assignment.json`（G4 重基线） | `60cbd331836e52b7` |
| `m13_v57_w3_validation.json`（G5） | `8b385d6c554ac527` |
| `m13_v57_l4_construction.json` | `d11a38519482b0cf` |
| `m13_v57_l4_validation.json` | `aa666a49e36883c7` |
| `m13_v57_l5_fab_record.json` | `791012e88b514faa` |
| `m13_v57_l5_si_pi_emc_record.json` | `261b58e745c67aea` |
| `m13_v57_co124_input_selfcheck_gate.json`（K9 + T5/T6/T7） | `9519e07d514766a8` |
| `m13_v57_co95_in4_reachability.json` | `4525e38330ee599f` |
| `m13_v57_co98_reachability_status_report.json` | `a29b802163bca3d9` |
| `m13_v57_co99_pdn_mutual_conflict_gate.json` | `1d256de815b1ed87` |
| `m13_v57_co104_pdn_blocked_ruling.json` | `7254226692cb8f93` |
| `m13_v57_co105_f4_scope_disposition.json` | `116f83fae67d1bb8` |
| `m13_v57_co106_reference_plane_gate.json` | `9f131d72e4780afb` |
| `m13_v57_co91_pdn_planned_coord_clearance_gate.json` | `3ede251a830108f1` |
| `m13_v57_co88_pdn_board_reality_gate.json` | `17719cf7f8e3e702` |

**未决（CO-136 后更新）**：外部输入（SI9000/板厂券 ⇒ 复核 as-built 3 处偏差 + ③ 的 w_min；PM 压降·热）；CO-135 报告项 F4（handoff pin 失准）/F5(a)（③ 根因叙述）＝点态叙述；F6 的 pad_field 声明豁免终判 = SI/板厂券。**无 owner 项**。

## 14. CO-136（L2 自裁 · 闸卫生续：关闭 CO-135 F5(b)/F6）当前态引用

**性质**：L2 自裁（工具/声明/登记卫生），无 L1 项。

- **F6 关闭**：co106 连续性检测器牙齿原把板内定点 `(60.0,50.0)` 钉为「In4 无铜」；`P3V3@P3V3_EAST` 铺铜随 CO-107（板框对齐 70.7→78.7）/CO-117 扩展后覆盖该点 ⇒ 牙齿**假阴性**、`teeth_ok=False` 长期带病。改为**数据无关的合成正/负控**（只测 `pip` 分类原语分「有铜/无铜」）⇒ rev **CO-106.2**，teeth **4/4** 全真（gate verdict 仍 `INDETERMINATE_REGION_SCOPED`，与本牙齿无关）。
- **F5(b) 关闭**：co124 记录硬编码定义件「v1.0 提议件」，实际在册件 = `L2/BASIC_SKILL_VS_REDLINE_v1.1.md` ⇒ 版本改由**文件名派生**（rev **CO-124.2**）；K1 docstring / scan_scope / 卡同步去硬编码。
- **F1 强化**：co77 表格行 citation 覆盖新增**负控牙齿**（合成表格行 + 漂移 sha ⇒ 必抓）⇒ rev **CO-77.5**，`teeth_ok=True`；正则退化即 verdict `TEETH_FAIL`。
- **登记簿**：新增并关闭 2 条 `TOOL_DEFECT`（co124 标签 / co106 陈旧牙齿）⇒ `TOOL_DEFECT` 4→6、总 17；`OPEN` 仍 1（as-built 偏差，待外部输入）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co106_reference_plane_gate.py`（CO-106.2） | `84eeea00d8e987cb` |
| 记录 `m13_v57_co106_reference_plane_gate.json` | `9f131d72e4780afb` |
| 记录 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.2） | `9519e07d514766a8` |
| 登记簿 `input_defect_register_v1.json`（17 项） | `dd9f79eb0aaec2a1` |
| 工具 `p3_v57_co77_closure_declaration_sweep.py`（CO-77.5） | `5459595adc50b392` |
| 工具 `p3_v57_co136_gate_hygiene.py` | `a5b712e48119fdfb` |
| 记录 `m13_v57_co136_gate_hygiene.json` | `065ed3f2fe2d2abb` |
| 卡 `m13_v57_CO136_gate_hygiene.md` | `10c52615002718cd` |


## 13. CO-135（非执行者复评 · rev-19 + CO-134｜L2 声明/工具卫生修正）当前态引用

**verdict：PASS_WITH_FINDINGS**（另一会话执行；非 CO-134 执行者，禁自评已满足）。实质：**全链独立复现** —— G4 `60cbd331836e52b7` / G5 `8b385d6c554ac527` / L4 val viol 0 `aa666a49e36883c7` /
L5 DFM new=0·SI 0.1300 / co124 findings 0（T1..T8）/ co95 55/55 / co98 55/0/0 / PDN co88/co91/co99/co102(+0)/co104/co105/co106 /
co69 10/10 / co120 PASS；冻结四源 **4/4**；SPEC rev-19 白名单外 **0** 改动。
**③ 定性**：`整改通知 #09`（监理指令）明确 ③ = 工程换算错误、撤回 owner 升级 ⇒ CO-134 属**执行指令**，非越权需求变更。
**as-built**：域外 3 处偏差独立重算复现（F.Cu 0.3294 / B.Cu 0.3450 / In5 0.3125）⇒ `OPEN_ENGINEERING` 处置妥当（路由 SI/板厂券 或另开几何 CO）。

**修正（L2 自裁）**：
- **F1** co77 收口扫描正则**未覆盖 markdown 表格行**（`| \`file\` | \`sha\` |`）⇒ 链表过期 pin 静默放过；已扩为**内联+表格**（revision **CO-77.4**）+ 候选解析补 `_shared`。修复后 co77 立报 22 处 mismatch ⇒ 本件链表 pin 已全量刷新。
- **F2** rev-19 重基线不完备：`co78/co81/co84` 提交态仍 pin **SPEC rev-18** ⇒ 已对 rev-19 重跑（全 PASS，见下表）。
- **F3** L5 fab 记录 pin 陈旧 L4 construction（`305a42a890593552`）⇒ 已重跑刷新为现行 `d11a38519482b0cf`。
- **F4/F5/F6**（报告项）：handoff pin 失准（G5 `4d5abd85e1d47705` 全仓无对应工件，实际 `8b385d6c554ac527`；co133 记录 `1fab64009ecb9048` 为旧值）；③ 根因叙述「2×0.4375」与来源件「5×线距」不一致（**不改退役结论**）；co124 定义件仍标 v1.0（实为 v1.1）；co106 `teeth_ok=False`（已自披露）；pad_field 可达性为**声明豁免**（终判 = SI/板厂券）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co135_review_hygiene.py` | `827a49520c8e2cd5` |
| 记录 `m13_v57_co135_review_hygiene.json` | `6167dea9c2fa84e0` |
| 卡 `m13_v57_CO135_review_hygiene.md` | `190f132391de44d1` |
| 工具 `p3_v57_co77_closure_declaration_sweep.py`（CO-77.4） | `5459595adc50b392` |
| `m13_v57_co78_layer_role_drift_gate.json`（对 rev-19 重跑） | `1235a9a957fcc0cd` |
| `m13_v57_co81_project_rules_gate.json`（对 rev-19 重跑） | `adba2152d4f10fd4` |
| `m13_v57_co84_dru_domain_gate.json`（对 rev-19 重跑） | `6f1a2ccfaf916627` |
| `m13_v57_l5_fab_record.json`（construction pin 刷新） | `791012e88b514faa` |
| `m13_v57_l5_si_pi_emc_record.json` | `261b58e745c67aea` |


## 15. CO-137（L2 分析 · 只读：as-built 对间偏差几何修正可行性）当前态引用

对 CO-134 登记的域外 3 处偏差做**确定性可行性判定**（最近邻闭式几何，零坐标搜索，只读）：
Δ = 2w(层) − 实测铜边；把该对整对沿「远离对方」方向平移 ⇒ 需该侧可用余量 ≥ Δ（否则转移违规）。

| 层 | 位置 | Δ(mm) | 远侧余量(mm) | 判定 |
|---|---|---|---|---|
| B.Cu | 92.15,47.912 | +0.0650 | 无远侧邻对 | `NO_FAR_NEIGHBOUR`（站点处于弯/端接，单侧判据不适用） |
| F.Cu | 137.24,59.575 | +0.0806 | 0.3438 | `FEASIBLE_SHIFT`（局部可平移） |
| In5.Cu | 74.75,40.8 | +0.0075 | −0.0075 | `INFEASIBLE_ONE_SIDE`（两侧均已紧贴，平移即转移违规） |

**结论**：几何路线**非一致可行**（`MIXED`）⇒ 维持 CO-134 处置（`OPEN_ENGINEERING`）：优先 SI/板厂券判**可接受性**；
若须消除，须按站点**构造性重路由**（F.Cu 局部可平移；In5 需换层/改走廊；B.Cu 需站点级构造），另开几何 CO。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co137_interpair_fixspace.py` | `730d7149fcf74dda` |
| 记录 `m13_v57_co137_interpair_fixspace.json` | `f94f61d8e014c694` |
| 卡 `m13_v57_CO137_interpair_fixspace.md` | `7e988b512a2082a7` |


## 16. CO-138（L2 分析 · 只读：偏差耦合几何画像）当前态引用

动机：SPEC `inter_pair_derivation_v1.scope` 明文「域外对间**长平行**」；co134 板实测量取「异对任意两段最小铜边」，**不区分平行/斜交**。
本件按声明步长 **0.02mm** 采样（确定性积分式测量，非搜索）给出客观画像（不改任何阈值/判定）：

| 层 | 位置 | 最小铜边 | req | 该点夹角 | 耦合长度 | 平行占比 ≤10° | 判定 |
|---|---|---|---|---|---|---|---|
| B.Cu | 92.15,47.912 | 0.3450 | 0.41 | 0.0° | 6.923mm | 1.00 | **长平行·在域内**（真偏差 −0.065） |
| F.Cu | 137.24,59.575 | 0.3295 | 0.41 | 1.1° | 3.766mm | 1.00 | **长平行·在域内**（真偏差 −0.081） |
| In5.Cu | 74.75,40.8 | 0.3125 | 0.32 | **21.8°** | 3.460mm | **0.00** | **斜交扇出**（≤20° 占比 0）⇒ 属「长平行」口径待定 |

**L2 裁定**：「长平行」的**量化阈值**工程未声明 ⇒ 属 **SI 域**（非 owner）。域内 2 处（B.Cu/F.Cu）为**真偏差**，
消除路径 = ① SI 判可接受性（外部输入），或 ② 走 G4 路由器管线的**构造性重路由**（走廊/间距，另开 CO，须全链重基线）。
本件不改几何/板，不改阈值，不自行退役 In5 偏差。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co138_interpair_scope_probe.py` | `fd00b0a3c1eda440` |
| 记录 `m13_v57_co138_interpair_scope_probe.json` | `7573907fdf3d0192` |
| 卡 `m13_v57_CO138_interpair_scope_probe.md` | `611ddb18f052821a` |


## 17. CO-139（L2 自裁 · K9 豁免锚定硬化）当前态引用

CO-135 F6 后半：K9 的「域外」豁免原本**只凭 regime 自由文本含 `ECN-001`** 即放行 —— 无依据、无 sha，改写文本即可让不可达域通过。
本件把豁免**机判化**：豁免域必须携带 `evidence_ref`（`path` 可解析 + `sha16` 与实件一致 + `basis` 非空），否则 FAIL；
`pad_field` 锚定 **SPEC `constraints.escape_transition_zone`**（`escape_clearance_mm=0.075`；焊盘场 0.4/0.6 节距为封装固有）。
新增**负控 T9**（移除豁免域的 `evidence_ref` ⇒ 必抓）。K9 牙齿 ⇒ **T1..T9 全触发**；`findings 0`。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.3） | `481311e30b77a1b0` |
| 记录 `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| 台账 `derived_value_ledger_v1.json`（pad_field 已锚定） | `b88d69dbc7a0dd51` |
| 登记簿 `input_defect_register_v1.json` | `dd9f79eb0aaec2a1` |


## 18. CO-140（L2 分析 · 只读：as-built 偏差归因）当前态引用

对域外 3 处偏差判定「**能否由路由消除**」：

| 层 | 位置 | 两网最近焊盘中心距 | 3w | 最小可达铜边 | 2w | 平行占比 | 归因 |
|---|---|---|---|---|---|---|---|
| B.Cu | 92.15,47.912 | 1.0583（U6 BGA） | 0.615 | 0.8533 | 0.41 | 1.00 | **ROUTING_FIXABLE**（走廊/间距可调） |
| F.Cu | 137.24,59.575 | **0.6000（J2 SlimSAS 接口）** | 0.615 | **0.3950** | 0.41 | 1.00 | **INHERENT_INTERFACE_PITCH**（数学不可消除） |
| In5.Cu | 74.75,40.8 | 1.0583（U6 BGA） | 0.48 | 0.8983 | 0.32 | 0.00 | **OBLIQUE_OUT_OF_LONG_PARALLEL** |

**裁定**：
- **B.Cu 项 = L2**：焊盘中心距 1.0583 ≥ 3w，且耦合区 100% 平行 ⇒ 属**路由可消除**；消除路径 = 消费走廊/lane 分配工件（`O(1)`、零搜索）的构造性重路由（另开几何 CO + 全链重基线）。
- **F.Cu 项 ⇒ L1/owner**：偏差落在 **J2 SlimSAS 接口焊盘墙**，连接器节距 0.6 < 3w=0.615 ⇒ 3W 在该接口**数学不可能**（最小可达铜边 0.395 < 2w 0.41）。此为**接口口径/需求适用域**问题 ⇒ 需 owner 裁定（或在 ECN-001 冻结逃逸域口径内明确处理）。
- **In5 项 = 待 SI**：21.8° 斜交、耦合区平行占比 0 ⇒ 「长平行」量化阈值属 SI 域。

（本件只读，不改板/SPEC/几何；零坐标搜索。）

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co140_deviation_attribution.py` | `3b9ad4a7a9a1cf05` |
| 记录 `m13_v57_co140_deviation_attribution.json` | `33410aefe4a20af3` |
| 卡 `m13_v57_CO140_deviation_attribution.md` | `a488b6853cce2064` |


## 19. CO-141（L2 审计 · 只读：对间 2w 符合性全量）当前态引用

co134 `as_built` 每层**只记一个最小值** ⇒ 登记簿「域外偏差 3 处」为**下界**。全量枚举异对段对并按夹角分类：

| 层 | 2w | <2w 且**平行(≤10°)** | <2w 且斜交(>10°) | 平行涉及对-对 | 平行最小 | co134 只报 |
|---|---|---|---|---|---|---|
| F.Cu | 0.4100 | **10** | 2 | 10 | 0.2577 | 0.3294 |
| B.Cu | 0.4100 | **14** | 0 | 14 | 0.3450 | 0.3450 |
| In5.Cu | 0.3200 | **0** | 1138 | 0 | — | 0.3125 |
| In2.Cu | 0.3200 | 0 | 0 | 0 | — | — |

**根因（新增 OPEN TOOL_DEFECT）**：`w3_constructive` 的 chip escape-fan / landing 列距基准取 via 净距（0.35+0.175=0.525 → 网格 0.6），
**未并入 REQ-R3-2 的 3W 下界 0.615**（该件自身 `MEANDER_PITCH = 0.615 # 2A>=3w` 已声明 3w）⇒ 逃生扇/落列实际列距 0.6 < 0.615，
造成 **24 个对-对**长平行 3W 不达标。**In5 的 <2w 组合全为斜交(>10°)** ⇒ 属 SPEC「长平行」口径外。

**裁定**：① L2（可确定性修）＝路由器 escape-fan/landing 列距基准改 `max(via 净距, 3w)=0.615`（另开几何 CO + 全链重基线）；
② L1＝J2 焊盘端 0.6 为**连接器节距**（接口固有，路由不可消除）；③ 外部＝SI 判可接受性 + 「长平行」阈值。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co141_interpair_conformance_audit.py` | `d7f2512c555ecc93` |
| 记录 `m13_v57_co141_interpair_conformance_audit.json` | `6f8535535a58aaf7` |
| 卡 `m13_v57_CO141_interpair_conformance_audit.md` | `37a3d9a943f47ebc` |

## 20. CO-142 / CO-143（L2 分析 · 只读：对间 <3W 违规明细 + 逃生扇 3W 定位修正与可行性）当前态引用

**CO-142（逐条明细 + 构造阶段归因）**：把 CO-141 的计数落成**逐条**证据 —— 全量枚举同层异对段对，
按夹角分类后对 <3W 中心距者给出坐标/网络/层/铜边距，并按 `manifest` 网络->页 与 CO16-ALLOC.7 端点点位
把每段归因到构造阶段。结果：**平行(<=10°) 且 <3W = 24 个对-对**，阶段直方图 =
`escape_vert|escape_vert` 7（B.Cu 西侧 DN out_MCIO）+ `land|land` 8 + `?|?` 7（B.Cu 东侧 UP out_J2，
同为逃生竖列）+ `land|?` 2 ⇒ **B.Cu 14 全为逃生竖列（路由可改）**，**F.Cu 10 全为 J2 land 段**（0.6 节距）。
平行重叠长度：B.Cu 1.0..12.7mm（DN 6.9..12.7 长；UP 1.0..9.7 递增），F.Cu 0.05..6.8mm。

**CO-143（定位修正 + 施加可行性）**：**更正 CO-141 附记2 的定位** —— 现行 G4 走 `--r1-5-shape co16`，
R1 逃生列由 `co16_prepare()` O(1) 消费 **CO16-ALLOC.7**；`r1_place()` / f13 `pair_xorder` 在 co16 路径
**不执行** ⇒ 附记2 的两次实验为 **no-op**，其「排除 VIA_VIA / 排除 R1 放置步 / 指向 f13 pair_xorder」结论**无效**。
**真实所在** = `p3_v57_co10_west_fan_probe.py` 的单遍落位判据 `check()`：track-track 用
`TT = WID + CLEAR = 0.38`（净距口径），**无 3*w(layer) 项** ⇒ 逃生竖列对间中心距 0.55/0.6 < 0.615。

机判（可行性）：

| 配置 | 落位 | B.Cu 对间最小中心距 | <3W 对数 |
|---|---|---|---|
| A 基线（= CO16-ALLOC.7 扇几何） | 32/32 | 0.55 | **14** |
| B 仅并入 3W（`CO10_IP3W=1`，opt-in） | 32/32 | 0.65 | **0** |
| C 并入 3W + PDN 障碍（`CO10_PDN_OBS=1`）rev | **31/32**（UP0/out_J2 失败） | 0.65 | 0 |
| C 同上、分带按 pad-x 升序（`--order xasc`） | **30/32**（UP3/input、UP7/input 失败） | 0.65 | 0 |

分带 DP（分析证据，非生产路径）机判：B.Cu 两带均**存在**满足 3W+pad+PDN 合法性的单调列分配
（EAST/up 8 页 dp_end_states 428；WEST/dn 8 页 386）⇒ **约束可满足，单遍贪心策略不足**。
另：存在「差分 0.0025mm vs 候选网格 0.05mm」的网格夹死（UP0 N/VT）。

**已还原的施加实验（不保留工件）**：把 3W 直接并入 `check()` 并重生成 ALLOC.8 → G4 `f649418ae0b712a2` →
L4 板 `9f7d6c62341df238` → co133 `--apply`：**DRC 42→45（+3 clearance）**，冲突 = UP0/out_J2 N corner via
× GND stitch via `(83.575,56.516)`，铜距 0.1587 < 0.175（中心距 0.5087 < VV 0.525）⇒ **无 PDN 障碍感知
即落板会引入 DRC 回归**。全部已还原：板 `d4e81f647be7f980`、G4 `60cbd331836e52b7`。

**裁定（L2，自裁）**：关闭 `tool_defect:k2_router_escape_fan_omits_3w` 须**重派生扇落位策略**
（闭式单调 carry / 分带次序 / PDN 障碍场），**非阈值参数追加**；F.Cu 10 项为 J2 接口 0.6 节距（L1，路由不可消除）。
opt-in 旋钮 `CO10_IP3W` / `CO10_PDN_OBS` / `--order xasc` 已入库（默认关 ⇒ ALLOC.1..7 逐字节可复现，机判 32/32 一致）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co142_interpair_violation_detail.py` | `69f3aa876b619631` |
| 记录 `m13_v57_co142_interpair_violation_detail.json` | `6a095e12f3b15ec5` |
| 卡 `m13_v57_CO142_interpair_violation_detail.md` | `c3a4f7ce841712df` |
| 工具 `p3_v57_co143_escape_fan_3w_feasibility.py` | `51f532e026f3670e` |
| 记录 `m13_v57_co143_escape_fan_3w_feasibility.json` | `0f9fd90cc0abd93c` |
| 卡 `m13_v57_CO143_escape_fan_3w_feasibility.md` | `3f9e35914b01a95c` |
| 探针 `p3_v57_co10_west_fan_probe.py`（+opt-in 3W/PDN 旋钮/xasc） | `d335ade502ceebcb` |
| 分配器 `p3_v57_co16_emit_allocation.py`（+CO16_IP3W 映射） | `64d75dd9f9d26875` |
| 登记簿 `input_defect_register_v1.json`（定位更正；OPEN 保持） | `dd9f79eb0aaec2a1` |

---

## 21. CO-144（L2 自裁 · 逃生扇落位策略重派生：分带单调 carry + PDN 障碍场）当前态引用

**事由**：`tool_defect:k2_router_escape_fan_omits_3w`（CO-141 定位 → CO-143 修正为 `p3_v57_co10_west_fan_probe.py:check()` 列距基准漏 3W）。
CO-144 以**分带单调 carry**（带内 (corridor,band) 连续 + 处理序自适应方向 + 游标 cur=已落位列极值 + 游标增量最小取首可行；仅外层逃逸带命中）
并入 **3w**，并注入 **PDN 固定障碍场**（`CO10_PDN_OBS`：zone vias / gnd_stitch / ppc / decoupling），重建 **CO16-ALLOC.8**。

**机判**：32/32 落位；B.Cu 对间平行(≤10°)最小中心距 **0.65 ≥ 0.615**（原 14 对-对 <2w ⇒ **0**）；In2 0.58 ≥ 0.48；
板级 DRC **中性**（kicad-cli `--severity-all` 42 → 42，0 新增）；L4 viol 0；L5 DFM new=0 / SI 0.1300 PASS。F.Cu J2 接口偏差仍属 **L1/owner**。

| 工件 | sha16 |
|---|---|
| 板 `k2_v4_8L.l4.kicad_pcb`（CO-144 后） | `d4e81f647be7f980` |
| G4 主件 `m13_v57_w3_joint_assignment.json`（W3-CN.42） | `60cbd331836e52b7` |
| 分配 CO16-ALLOC.8 `m13_v57_co16_channel_allocation_v8.json` | `3307d19a226f60fc` |
| CO-144 记录 `m13_v57_co144_escape_fan_carry_rederive.json` | `2a2689c4bc842158` |
| G4 主件 `m13_v57_w3_joint_assignment.json` | `60cbd331836e52b7` |
| G5 校验 `m13_v57_w3_validation.json` | `8b385d6c554ac527` |
| L4 施工 `m13_v57_l4_construction.json` | `d11a38519482b0cf` |
| L4 校验 `m13_v57_l4_validation.json` | `aa666a49e36883c7` |
| L5 fab `m13_v57_l5_fab_record.json` | `791012e88b514faa` |
| L5 SI `m13_v57_l5_si_pi_emc_record.json` | `261b58e745c67aea` |
| 引擎 `p3_v57_w3_constructive.py`（CO16_ALLOC→v8 / W3-CN.42） | `481617515038dad5` |
| 探针 `p3_v57_co10_west_fan_probe.py`（+carry/orientation） | `d335ade502ceebcb` |
| 分配器 `p3_v57_co16_emit_allocation.py`（+FAN_STRAT/PDN_OBS/ORDER 映射） | `64d75dd9f9d26875` |
| 登记簿 `input_defect_register_v1.json`（该 TOOL_DEFECT **CLOSED**；OPEN 1 = F.Cu/owner） | `dd9f79eb0aaec2a1` |
| 台账 `derived_value_ledger_v1.json`（as-built B.Cu ok；evidence pin 刷新） | `b88d69dbc7a0dd51` |

---

## 22. CO-145（L2 自裁 · 走廊分配/等长窗口：lane-run 蛇形幅度守卫并入 3W）当前态引用

**事由**：`tool_defect:k2_meander_amp_guard_omits_3w`（与 CO-141/143 逃生扇缺陷同族）——引擎 `co16_o4_amp_table`
lane-run 蛇形幅度守卫只按 `VT_TRACK=0.4525`（净距口径）限定邻道余量，**漏 3w(In5)=0.48** ⇒ 峰值侵入邻道 ⇒
实测 In5 lane-run 对间铜边 0.3125 < 2w=0.32（例 DN_OUT0_N × DN_OUT1_P）。

**L2 修复**：① 守卫对**异对**邻道改取 `max(VT_TRACK, 3w(In5))`（同对内维持 VT——3W 只约束对间），余量 0.005；
② 实测幅度 <~0.071/0.075 时 `meander_zig` 退化 ⇒ 不可单纯压缩幅值 ⇒ lane 步距 1.05→1.07 腾出空间；
③ 重发射 CO16-ALLOC.9 + G4 W3-CN.43 → L4 → 板 → L5。

**机判**：In5 对间最小铜边 **0.3125 → 0.325 ≥ 0.32**；B.Cu ok；SI 0.1300 PASS；板级 DRC 42(+0)；L4 viol 0。
**残留**：F.Cu J2 landing（connector 0.6 节距 < 3w=0.615，接口固有不可达）⇒ **L1/owner**。

| 工件 | sha16 |
|---|---|
| 板 `k2_v4_8L.l4.kicad_pcb`（CO-145 后） `k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` |
| 分配 CO16-ALLOC.9 `m13_v57_co16_channel_allocation_v9.json` | `d3cd1e5a312f253a` |
| CO-145 记录 `m13_v57_co145_meander_3w_guard.json` | `c731484773b2f771` |
| G4 主件（W3-CN.43） `m13_v57_w3_joint_assignment.json` | `60cbd331836e52b7` |
| G5 校验 `m13_v57_w3_validation.json` | `8b385d6c554ac527` |
| L4 施工 `m13_v57_l4_construction.json` | `d11a38519482b0cf` |
| L4 校验 `m13_v57_l4_validation.json` | `aa666a49e36883c7` |
| L5 SI `m13_v57_l5_si_pi_emc_record.json` | `261b58e745c67aea` |
| 引擎 `p3_v57_w3_constructive.py`（3W 蛇形守卫 + W3-CN.43） `p3_v57_w3_constructive.py` | `481617515038dad5` |
| 登记簿 `input_defect_register_v1.json`（+CO-145 项 CLOSED；OPEN 1 = F.Cu/L1） `input_defect_register_v1.json` | `dd9f79eb0aaec2a1` |

## 23. CO-146（L2 · 监理指令 #10「JLC 8 层打样就绪」）：阻抗表 / PM 评估 / 打样包 / DFM 闸 / 定性更正

> 依据：`instruction-10-jlc-prototype-ready.md`（监理定值：JLC08161H 1.6mm / 外层 1oz 内层 0.5oz / 85Ω±10% 勾阻抗控制 / ENIG / 压降 3% / 40°C 自然对流）。冻结四源 **逐字节未动**（SPEC `5f72182a2616392c`、板 `d4e81f647be7f980`）。

**动作 1 阻抗表**：JLC08161H 交付几何双模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）交叉核对 ⇒ as-built 对内净距下 85Ω±10% **PASS**；设计名义最宽间距（0.6mm 中心）下有 1 项 model-spread 越界 ⇒ 列入下单备注（请 JLC 阻抗表覆盖该几何）。终判 = JLC 阻抗控制服务。

**动作 2 PM 评估**：一阶确定性（平面 Rs·L/W + 过孔并联 + 热 ΔT=P/(h·2A)）。四轨压降 0.007%–0.69%（预算 3%）全 PASS；热 ΔT_board 29.0°C ⇒ T_board 69.0°C、热点 Tj(U6) 106.5°C < 125°C。**电流/功耗/θJA/对流系数为显式声明值（非实测）**，器件手册到位后替换重跑。

**动作 3 打样包**：`L5/jlc_package/`（Gerber RS-274X ×13 含 8 铜层 + Excellon 钻孔 ×5 + 叠层图 SVG + 阻抗表 + 层序 + 下单备注 + MANIFEST）；命令+sha 可复现（时间戳规范化；重跑逐字节同）。

**动作 4 DFM 闸（对照 JLC 公布能力）**：**FAIL** —— ① **盲/埋孔**：交付板 **220/493** 支非通孔（含 `In2.Cu→In5.Cu` **埋孔 88**），而 JLC 标准服务 *Blind/Buried Vias Not supported*；原地改通孔实测 **111 项 shorting_items** ⇒ 现行 W3 派生**结构依赖盲/埋孔**；② **阻焊桥 1 处**（JLC 0.09mm 下限，`PCIE_UP3_N`×`R3.pad2(PWR_BTN_ISO)`）。其余项（线宽 0.16≥0.09、孔 0.2/盘 0.35、环宽 0.075、孔距 0.25、板边 0.30、尺寸/层数/铜厚/板厚/表面处理）全 PASS。

**动作 5 定性更正**：**撤回「外部输入阻塞」**（阻抗终判改绑 JLC 阻抗控制服务；PM 改绑监理定值 + 本件评估）；SPEC `impedance.coupon_required=true` **字段不动**（改绑的是解释与签署路径）；登记簿 **+2 OPEN**（盲/埋孔 = 结构/工艺类别 ⇒ 需 owner 一句话；阻焊桥 = 可修）。

**残留（如实）**：① owner：盲/埋孔出路 (a) 走 JLC advanced 盲埋孔通道 / (b) 重开 W3 通孔化派生；② owner：J2 接口 3W 适用域（既有 L1）；③ 复评债 CO-142..145 + **CO-146 全部产物**（另一会话，禁自评）。

| 工件 | sha16 |
|---|---|
| 冻结 SPEC `SPEC_k2_v4.spec-rev-19.json`(未变) | `5f72182a2616392c` |
| 交付板 `k2_v4_8L.l4.kicad_pcb`(未变) | `d4e81f647be7f980` |
| 阻抗表 `m13_v57_co146_impedance_table.json` | `794132ded5a0ce61` |
| PM 评估 `m13_v57_co146_pm_eval.json` | `76a6b6860f071298` |
| DFM 闸 `m13_v57_co146_jlc_dfm_gate.json` | `1692424817eaa89f` |
| JLC 能力表 `m13_v57_co146_jlc8_capability.json` | `b35130f9303d9726` |
| 通孔化反证 `m13_v57_co146_through_via_probe.json` | `fd82d5200294919e` |
| 打样包记录 `m13_v57_co146_jlc_fab_package.json` | `7ccb47223c111ad9` |
| 定性更正 `m13_v57_co146_jlc_rebind.json` | `a0a0f6114223ef05` |
| L2 定值绑定 `jlc_prototype_parameters_v1.json` | `e9bf5019aeddbd16` |
| 登记簿 `input_defect_register_v1.json`(+2 OPEN) | `dd9f79eb0aaec2a1` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| 工具 `p3_v57_co146_jlc_dfm_gate.py` | `22fad27342bc0203` |
| 工具 `p3_v57_co146_impedance_table.py` | `a1a432504f7ff6f2` |
| 工具 `p3_v57_co146_pm_eval.py` | `214cd888f6f49be3` |
| 工具 `p3_v57_co146_jlc_fab_package.py` | `39ed4229274d3fe7` |
| 工具 `p3_v57_co146_through_via_probe.py` | `e6a53875c47319ae` |
| 工具 `p3_v57_co146_closeout.py` | `18220ee964ead702` |

## 24. CO-147（**L2 自裁** · 过孔策略/打样渠道 · J2 对间适用域 · 阻焊桥）：三题裁定 + 登记簿 3 项转 CLOSED

> 依据：LAYOUT_CONSTITUTION 第二章（L2 = 叠层分配/PDN/走廊分配/**过孔策略**/等长窗口/热机械 ⇒ ARCHER 自裁；L1 仅 器件分区/接口朝向/信号流向/电源域划分/球重映射）。需求（目的/原则）未变更；板/SPEC 逐字节未动。

**R1 过孔策略/渠道**：交付板 220/493 支盲/埋孔为现行 W3 派生**结构必需**（原地通孔化实测 111 项 shorting_items）⇒ 维持策略、下单渠道绑定 **JLC advanced/盲埋孔**（DFM review + 重报价）；如需通孔板 ⇒ 另开 W3 通孔化重派生（L2 候选，前置 = 引擎通孔模型 + 可行性证明）。**不涉层数变更 ⇒ 属 L2（过孔策略），非 L1（HDI/层数）。**

**R2 J2 landing 对间 3W**：连接器 0.6 节距 ⇒ 接口固有不可路由（F.Cu 实测铜边 0.3294 vs 0.41）⇒ **ACCEPT_L2（声明偏差 + hash-pin 依据）**，需求目的「对间不串扰」不变，终判 = SI/JLC 阻抗控制服务；域声明与既有 ECN-001 逃逸豁免同族、口径一致。

**R3 阻焊桥 1 处**：`R3.pad2(PWR_BTN_ISO)` 开窗缘 ↔ `PCIE_UP3_N` 铜缘 **0.0695mm** < JLC 0.09mm（欠 0.0205）⇒ **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何）；回退修法 = R3 开窗 0.05→0.02mm。

| 工件 | sha16 |
|---|---|
| L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md` | `e8e16228bf1ea0eb` |
| 记录 `m13_v57_co147_l2_ruling.json` | `6d3b58ba530483f2` |
| 登记簿 `input_defect_register_v1.json`(3 项 CLOSED / OPEN 0) | `dd9f79eb0aaec2a1` |
| DFM 闸 `m13_v57_co146_jlc_dfm_gate.json` | `1692424817eaa89f` |
| 通孔化反证 `m13_v57_co146_through_via_probe.json` | `fd82d5200294919e` |
| 打样包记录 `m13_v57_co146_jlc_fab_package.json` | `7ccb47223c111ad9` |
| 工具 `p3_v57_co147_l2_ruling.py` | `fbc81bdff63fc0d3` |

## 25. CO-148（L2 · **PM 输入升级为器件手册值** ⇒ U6 热超限）：热裁定 + 登记 + 台账

> 触发：监理指令 #10 要求「各轨电流由设计/器件手册导出」。U6 = DS320PR1601，手册 **TI SNLS683（JUNE 2023）**已抓取入库（节录件 + PDF sha256；`mcio_feas_step2/m13_v57_co148_ds320pr1601_snls683_excerpt.txt` `623b562cfc8262d2`）。

**事实（机判）**：手册 PACT = 4.7–7.0W、θJA(high-K) = 17.4°C/W、ψJB = 5.9、Tj 上限 **120°C**；按监理定值 40°C 自然对流 ⇒ **Tj 121.8°C（U6_EQ0-2_typ）～161.8°C（U6_EQ5-19_max）全档超限**，ψJB+h 交叉路线 173.6°C 同判 FAIL。散热路径：U6 152 GND 球 / 域内 GND via 仅 66。（CO-146 的 U6 声明功耗 1.5W 偏低 3–4.7 倍 = PM 输入缺陷，已替换。）

**L2 裁定**：R4-1 PCB 散热路径义务（U6 域 GND via 阵列补强 / GND 平面覆盖 / 铜面最大化，随下一轮几何修订 + G4 重基线）；R4-2 **输入冲突上报**：40°C 自然对流与手册不相容 ⇒ 须重裁环境/风冷输入（选项：a 强制风冷/散热片使 θJA_eff ≤ 11.43–17.02°C/W；b 环境 ≤ 38.2°C；c 复核 EQ/功耗假设）。**PDN 侧不受影响**：手册电流（P3V3 2.23A）下四轨压降 0.007–0.69% ≪ 3%（I_max@3% 4.3–62.6A）。

**登记**：+2（`thermal_defect:u6_ds320pr1601_tj_exceeds_limit_at_40c_natural_convection` HIGH；`tool_defect:co124_k9_has_no_thermal_or_drop_domain_model` MED）⇒ 登记簿 65 项（现行值，CO-155 去下游快照后改读登记簿）；台账 DV-CO146-THERMAL = `UNREACHABLE_REGISTERED`。

| 工件 | sha16 |
|---|---|
| L2 裁定件 `L2_RULING_u6_thermal_v1.md` | `aa00f0207bc37e6f` |
| 记录 `m13_v57_co148_thermal_ruling.json` | `7b58f89fbe204131` |
| 手册输入 `m13_v57_co148_u6_ds320pr1601_inputs.json` | `d98677fd7f7d51ba` |
| PM 评估 `m13_v57_co146_pm_eval.json`（手册输入） | `76a6b6860f071298` |
| 登记簿 `input_defect_register_v1.json` | `dd9f79eb0aaec2a1` |
| 台账 `derived_value_ledger_v1.json` | `b88d69dbc7a0dd51` |
| 工具 `p3_v57_co148_u6_datasheet_inputs.py` | `b6eedc2bce42e85b` |
| 工具 `p3_v57_co148_thermal_ruling.py` | `968dac508e9b8218` |

## 26. CO-149 / CO-150（L2 自裁 · 热机械派生实现要求 + K9 热/压降域扩闸）：U6 散热要求 + 闸硬化

**CO-149（热机械派生，解 CO-148 R4-2；监理定值 Ta = 40.0°C 不变）**：
- 两路线互校：手册 θJA(high-K) 17.4 °C/W vs 本板一阶 ψJB+1/(h·2A) = **17.22 °C/W**（差 1.0%，模型可信）；其中**板→空气占 65.7%** ⇒ 瓶颈不在走线/via。
- 派生要求：θJA_eff ≤ **11.43**（最重档）～17.02 °C/W；或强制风冷 h_eff ≥ **8.14–16.38 W/m²K**；或顶部散热片预算 θJC+R_int+θ_HS ≤ **4.93–10.52 °C/W**。
- 方案（声明值）：O0 现状 17.22（0/4 档）、O1 风冷 11.56（3/4 档）、**O2 散热片+风冷 11.0（4/4 档 ✓）**⇒ **自然对流全档不可达 ⇒ 系统散热为必需项**（非可选项）。
- **R5-3**：PCB 侧**不改几何**（瓶颈为板→空气；U6 域热过孔仅影响 ψJB 项）⇒ CO-148 R4-1「GND via 阵列」由义务降为**可选**，避免为边际收益触发 G4 全链重基线。终判 = 实板热测/仿真。

**CO-150（闸硬化）**：co124 K9 扩 `thermal_option_domain`（∃ 声明散热方案覆盖最重工况；现状不达标须显式声明 required_mitigation）与 `drop_domain`（每轨 ΔV% ≤ 预算%）+ 负控 T10/T10b/T11/T11b ⇒ co124 rev **CO-124.9** verdict PASS findings 0；关闭 CO-148 登记的 K9 缺口项 ⇒ **登记簿 OPEN 0**。

| 工件 | sha16 |
|---|---|
| L2 裁定件 `L2_RULING_u6_thermal_mitigation_v1.md` | `bf029700941f5145` |
| 记录 `m13_v57_co149_u6_thermal_mitigation.json` | `206269d4bbc1a04b` |
| 记录 `m13_v57_co150_k9_domain_gate.json` | `00f82a241378d521` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| 登记簿 `input_defect_register_v1.json`(OPEN 0) | `dd9f79eb0aaec2a1` |
| 台账 `derived_value_ledger_v1.json` | `b88d69dbc7a0dd51` |
| 工具 `p3_v57_co149_thermal_mitigation_derive.py` | `c6b5915d43e2a292` |
| 工具 `p3_v57_co150_k9_domain_gate.py` | `33d4879bc13deeec` |

## 27. CO-151（**非执行者对抗复评** · rev-19 + CO-142..CO-150）：独立重算全复现 + findings 8

**复评人 = 非执行者会话**（未参与 CO-142..150 施加；context 隔离）；**verdict = PASS_WITH_FINDINGS**；只读（除自身记录）。冻结四源 4/4 + 交付板 `d4e81f647be7f980` 逐字节不变。

**独立确认（不复用执行者断言，自一次源重算）**：
- CO-146 阻抗双模型逐值复现（≤0.02Ω）；PDN 四轨 ΔV% 漂移 ≤0.0001%
- CO-146 DFM：自跑 DRC as-designed 42 / JLC 下限 43（solder_mask_bridge=1）；阻焊几何 0.0694 <0.09（回退 0.1004≥0.09）
- CO-146/147 过孔：自数 493 支 / 非通孔 220（0.05 与 DFM 表逐型一致）
- CO-147 R3 阻焊 FAIL；R1 盲埋孔『Not supported』出处 sha256 7d1d5a9193f3c212 ✓
- CO-148/149 热：手册解析 PACT=[4.7, 6.0]/[5.8, 7.0]、θJA=17.4、TJmax=120.0 ⇒ Tj 最劣 161.8°C > 120 ⇒ FAIL 成立
- CO-150 K9 两域本件自建 3 负控全触发、现行台账 0 findings（牙齿非空过）
- co120 豁免 10 条中 9 条确为陈旧（非空过）；名义多余 1 条（见 F-7）

**findings**：

| id | sev | kind | 内容 | 修法 |
|---|---|---|---|---|
| F-1 | low | doc/reproducibility | §6 记录 pin 为**时序快照**（记录内嵌下游 sha/状态计数）：按 §6 复现得**另一稳定不动点**，co124/co147/co148/co150 四条记录 pin 不可由 §6 复现（登记簿/台账 pin 可复现）；且 co148 重跑把 2 条已闭登记项重开（OPEN 0→2）。 | ① §6 标注「记录 pin = 时点快照，非复现目标」并给出时序；② 移交执行 CO：记录内嵌下游快照去留（登记簿 item 13 同族）。③ 复核 co120 是否需为这 4 条的 `sha16` 字段补 EXEMPT（现闸仅扫 `*_record` 键，不覆盖 → 见 F-1b） |
| F-1b | low | gate-coverage | co120 P1 正则仅抽 `"<x>_record"` 键 ⇒ 记录内 `register_sha16`/`sha16_after`/`sha16` 类**下游快照字段不在闸覆盖内**（CO-108/114 F-6 的另一半）；本件 4 条即为实例。 | co120 P1 增补白名单字段（或显式声明「非 *_record 快照不受闸管」并登记理由）。 |
| F-2 | medium | record-errata | CO-147 R2 `facts.as_built_edge_mm`=0.3294 非最劣值：本板 F.Cu 平行(≤10°)异对全量最小铜边=0.2577mm（中心 0.4627），欠 2w 达 0.1523mm；0.3294 系 CO-134 单值口径，已被 CO-141 判 UNDER_REPORTED。裁定结论（接口固有 ⇒ ACCEPT_L2）不受影响，但 R2 引文与其所引证据链（CO-141/142）自相矛盾。 | R2 facts 改列最劣 0.2577（另注 J2 侧最劣 0.2871）；doc + 记录 + boundary 同批重基线。 |
| F-3 | low | record-errata | CO-147 R3 `not_done_why` 称『0.0065mm 量级边际差距』，与其本件 `facts.shortfall_mm`=0.0205 差 3.2×（本件独立复算 shortfall=0.0205 ✓）。仅叙述，处置（ACCEPT_WITH_FAB_REVIEW）不变。 | 『0.0065mm』→『0.0205mm』。 |
| F-4 | low | advisory | CO-149 板侧路线以**表征参数 ψJB=5.9**作加性热阻；若改用同表**热阻 RθJB=6.1**，所需 h 由 [8.15, 16.38] 抬到 [8.29, 16.99]（+3.39%），θJA_eff 17.22→17.42（与手册 θJA=17.4 反而更贴合）。『两路线互校差 1.0%』因复用手册自身 ψJB + 声明 h，**非独立证据**。另：O0（自然对流）覆盖 0/4 对声明 h=8.0 敏感——h=8.5 时覆盖 1/4。结论（须系统散热）不变。 | 补 h/ψJB↔RθJB 敏感度行 + 把『互校』改称『一致性核对』。 |
| F-5 | low | advisory | CO-146 PDN `n_plane_vias` 实为**全网 via 计数**（P3V3 41、P3V3_AUX 12）而非 zone 内净匹配（本件实算 35/5）；口径未声明。因 R_plane 主导，ΔV% 影响 <0.02%（绝对），四轨 PASS 不变。 | 口径显式声明（或改用 zone 内计数 + 保守侧）。 |
| F-6 | info | advisory | CO-146 阻抗『两套独立闭式交叉核对』：M1 即 SPEC `dielectric_8l_basis.model` 同式同输入 ⇒ **非独立**（等价于复现 SPEC 一阶），真正独立第二模型仅 M2；结论（as-built ±10% PASS + 名义最宽 gap watch）仍成立（本件双模型逐值复现，差 ≤0.02Ω）。 | 标签改『一阶复现 + 单一独立模型交叉核对』。 |
| F-7 | info | registry-hygiene | co120 EXEMPT 注册表声明 10 条，闸记录 `n_exempt_historical`=9：`co110:co109_record` 的 pin 现与目标**相等**（不再陈旧）⇒ 该条为**多余登记**（清单虚高 1）。另 co111/co118 两条（登记簿 item 13 点名复核）无板级机判佐证，仅靠自由文本理由（本件佐证其 pin 确陈旧且与现引值一致 ⇒ 判**充分**）。 | 删/收紧 `co110:co109_record`；为 co111/co118 补可机判依据（如现引记录 sha 对应板/时点）。 |

> 复评**只读**：findings **未**写入登记簿（登记簿 scope = SPEC/drc_rules；本类属记录/闸/注册表卫生）⇒ 由后续执行 CO 决定登记与重基线（同 CO-108/114 先例）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co151_rev19_nonexecutor_review.py` | `0c6531f94869b1bb` |
| 记录 `m13_v57_co151_rev19_nonexecutor_review.json` | `195a8102720ed140` |
| 卡 `m13_v57_CO151_rev19_nonexecutor_review.md` | `512943d2bc24b463` |
| co120 provenance 闸 `m13_v57_co120_provenance_pin_gate.json` | `c1b0cb595438f381` |
| 登记簿 `input_defect_register_v1.json`(复评未改) | `dd9f79eb0aaec2a1` |
| 台账 `derived_value_ledger_v1.json`(复评未改) | `b88d69dbc7a0dd51` |

## 28. CO-152（**L2 自裁 · executor**：CO-151 findings 处置 = 记录/闸/语义卫生 + 2 项勘误）

来源 = CO-151 非执行者对抗复评（`PASS_WITH_FINDINGS`，findings 8）。本件**全部在 L2 内自裁**（记录/闸/派生物语义，非 L1 拓扑/接口/信号流向/球重映射）。**板 / SPEC / 冻结四源逐字节不变**。

| CO-151 finding | 处置 | 落点 |
|---|---|---|
| F-1（low）记录内嵌下游 sha ⇒ pin 不可复现 | **修**：移除 co124/co147/co148/co150 的下游快照（现行 sha 一律走本 boundary pin 表）；复核 §6/规范序连跑，4 件记录逐字节稳定 | co124/co147/co148/co150 工具 |
| F-1b（low）co120 不覆盖 `*_sha16` 快照键 | **修**：co120 → **CO-120.2** 新增 P5『下游快照声明册』（`*_sha16_after` 未声明即 FAIL + 负控/正控牙齿）；`SNAPSHOT_DECLARED` 声明 8 件历史件 | co120 |
| F-7（info）豁免注册表 10 条 vs 闸 9 条、2 条依据不可机判 | **修**：删多余豁免（co110←co109）；EXEMPT 增 `exemption_basis` 分级 → `board_superseded`（机判可证，4 条）/ `declared_historical`（计数明示，5 条）；依据不成立即 FAIL | co120 |
| F-2（**medium**）CO-147 R2 `as_built_edge_mm` 0.3294 非最劣 | **勘误** → **0.2577**（全量平行≤10°最小铜边；J2 侧最劣 0.2871；原值留 `as_built_edge_cited_prev`）。裁定结论（接口固有 ⇒ ACCEPT_L2）不变 | CO-147 工具/裁定件 |
| F-3（low）CO-147 R3 叙述 0.0065mm 与本件 `shortfall_mm` 0.0205 矛盾 | **勘误** → 0.0205（与 facts 一致） | CO-147 工具/裁定件 |
| F-4（low）ψJB 作加性热阻/『互校』措辞/ h 敏感度未披露 | **补**：CO-149 增 `sensitivity` 块（ψJB↔RθJB：所需 h [8.15,16.38]→[8.29,16.99]，更保守 +3.4%；h 敏感度：8.0→0/4、8.5→1/4、16→3/4）＋牙齿 t04/t05；文档 §1 改称『一致性核对（非独立证据）』；co148 解析器补 RθJB（七值牙齿） | CO-149 / co148 解析器 |
| F-5（low）`n_plane_vias` 口径未声明 | **标注**：增 `n_plane_vias_basis` + `method.via_count`（= 全网 net via 计数，非 zone 内净匹配；ΔV% 由 R_plane 主导，差异 <0.02% 绝对） | CO-146 PM 评估 |
| F-6（info）阻抗『两套独立』名不副实 | **正名**：『M1 = SPEC `dielectric_8l_basis` 同式同输入一阶复现（非独立）+ M2 单一独立模型交叉核对』 | CO-146 阻抗表 |

**本件新增约束（自本版起生效）**：

1. **R-CO152-1**：记录**不得**内嵌其**下游**工件 sha（`register_sha16` / `register.sha16_after` / `ledger.sha16_after` / 后续 CO 记录 sha）⇒ 现行 sha 一律由本 boundary pin 表单一承载。
2. **R-CO152-2**：任何记录若出现 `*_sha16_after` 类键，必须在 co120 `SNAPSHOT_DECLARED` 明文声明（未声明即 FAIL_UNDECLARED_DOWNSTREAM_SNAPSHOT）；现声明 8 件历史件（CO-68/72/73/74/80/82/133/146-rebind）。
3. **R-CO152-3**：co120 豁免必须择一依据类并成立（`board_superseded` 机判可证 / `declared_historical` 计数明示）。
4. **R-CO152-4**（复现序）：规范序 = `co146_imp → co146_pm_eval → co148_inputs → co148_thermal_ruling → co149 → co147 → co146_dfm → co152_register → co124 → co150 → boundary_append → co77 → co120 → co135 → co136 → boundary_append`，**循环 2–3 次至 sha 稳定**（boundary pin 表 ⊃ 闸记录 sha，闸记录 ⊃ boundary sha ⇒ 系统不动点，非缺陷；实测 2 轮收敛）。

**登记簿**：+3 项 TOOL_DEFECT（`records_snapshot_downstream_sha_causes_pin_drift` / `co120_pin_scope_omits_sha16_snapshot_keys` / `record_derived_value_semantics_unlabeled`）**全部 CLOSED**；`meta.counts` 复位（总 27 / OPEN 0）。F-2/F-3 属 L2 裁定件勘误，不在登记簿 scope，记于本 §28。

| 工件 | sha16 |
|---|---|
| co152 处置工具 `p3_v57_co152_findings_disposition.py` | `1a38f32effc7362a` |
| co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.2） | `c1b0cb595438f381` |
| co124 `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| co147 `m13_v57_co147_l2_ruling.json` | `6d3b58ba530483f2` |
| co148 `m13_v57_co148_thermal_ruling.json` | `7b58f89fbe204131` |
| co149 `m13_v57_co149_u6_thermal_mitigation.json` | `206269d4bbc1a04b` |
| co150 `m13_v57_co150_k9_domain_gate.json` | `00f82a241378d521` |
| co146 阻抗表 `m13_v57_co146_impedance_table.json` | `794132ded5a0ce61` |
| co146 PM 评估 `m13_v57_co146_pm_eval.json` | `76a6b6860f071298` |
| 手册输入 `m13_v57_co148_u6_ds320pr1601_inputs.json` | `d98677fd7f7d51ba` |
| L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md` | `e8e16228bf1ea0eb` |
| L2 裁定件 `L2_RULING_u6_thermal_mitigation_v1.md` | `bf029700941f5145` |
| 登记簿 `input_defect_register_v1.json`（27 项 / OPEN 0） | `dd9f79eb0aaec2a1` |
| 台账 `derived_value_ledger_v1.json` | `b88d69dbc7a0dd51` |

> **复评债**：本件（CO-152）自身须由**另一会话**复评（禁自评）：重点 = 三处语义标注是否足够、co120 P5 是否真能防复发、R2 最劣值勘误是否改变 R2 结论（预期不变）。

## 29. CO-153（**L2 自裁 · 闸硬化**：K9 `declared`/`conservative_ge` 判据 + 域生产者归一）

**执行前实测缺口**（证据）：co124 K9 对 `kind == "declared"`（含无 kind 的默认值）**无任何判据** ⇒ 9 个派生值中 **2 个零校验通过**（「声明即通过」）：`derived_value_declared_unpinned:DV-ENGINE-INT_PAIR_PITCH` 与 `...:DV-CO146-ZDIFF`（后者 `evidence_ref.sha16` 自 CO-146 起再未刷新，CO-152 改阻抗表记录后实测陈旧）。

**本件处置**：

1. **K9 新增 `declared` 判据**：`evidence_ref` 须可解析 + `sha16` 与现行一致 + `basis` 非空（与 `process_floor` 同口径）⇒ 陈旧/缺失证据必然被抓。
2. **K9 新增 `conservative_ge` 判据**：闭式重算 `faithful = span + 2·w_outer` 并证 `value ≥ faithful`、`cited` 一致 ⇒ 「保守实现」由断言升级为**证明**。
3. **台账域生产者归一**：`DV-ENGINE-INT_PAIR_PITCH.kind = conservative_ge`（生产者亦已同步：`p3_v57_co134_req_impl_separation.py` 直出该 kind）；`DV-CO146-PDN-DROP.kind = drop_domain` 改由 `p3_v57_co153_k9_domain_coverage.py` **具名产出**（此前系一次性写入、规范序内无生产者 ⇒ 任何台账重写即静默丢失、`T11_drop_domain_teeth` 失效）。
4. **`p3_v57_co146_ledger_add.py` 收窄**为**仅** upsert `DV-CO146-ZDIFF`（原三 DV 一并重写会 clobber CO-149/CO-150/CO-153 的归属），并**并入规范复现序** ⇒ 阻抗表记录变更即自动刷新证据 pin（此为其 pin 陈旧的根因）。
5. **牙齿**：`T12/T12b`（声明未锚定必抓 / 无假阳）、`T13/T13b`（保守未证明必抓 / 无假阳）；`T11_drop_domain_teeth` 回归恢复为 True。co124 牙齿总数 17，全 True。

**闭合复核**：co124 = **PASS / findings 0 / 牙齿 17/17 True**（执行前 = FAIL_UNREGISTERED_INPUT_DEFECT / findings 2）。**登记簿**：+3 TOOL_DEFECT（`co124_k9_declared_kind_has_no_evidence_check` / `co146_ledger_add_schema_drift_and_out_of_order` / `k9_drop_domain_has_no_producer_in_reproduction_order`）**全部 CLOSED** ⇒ 30 项 / OPEN 0。

> **R-CO153-1**：K9 各域（`domain_cap` / `identity` / `process_floor` / `declared` / `conservative_ge` / `drop_domain` / `thermal_option_domain`）均须由规范复现序内**具名生产者**产出；**禁止一次性写入台账域**（否则任何台账重写会静默削掉机判覆盖面）。

> **R-CO153-2**（取代 R-CO152-4 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → **co146_ledger_add** → **co153_k9_domain_coverage** → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环 2–3 次至 sha 稳定**（实测 3 轮收敛：co124/co120/co135/co136/register/ledger 自第 2 轮起稳定，co77/boundary 第 3 轮稳定）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co153_k9_domain_coverage.py` | `89bb6506bc0adc6c` |
| 工具 `p3_v57_co146_ledger_add.py`（收窄） | `146a3c06d1a9a905` |
| 工具 `p3_v57_co134_req_impl_separation.py`（生产者直出 kind） | `8f59c5be82fe9d06` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.6） | `9519e07d514766a8` |
| co120 闸 `m13_v57_co120_provenance_pin_gate.json` | `c1b0cb595438f381` |
| 台账 `derived_value_ledger_v1.json`（9 DV 全域覆盖） | `b88d69dbc7a0dd51` |
| 登记簿 `input_defect_register_v1.json`（30 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

> **复评债**：本件（CO-153）自身须由**另一会话**复评（禁自评）：重点 = 新判据是否可被规避、`conservative_ge` 的 faithful 口径是否等同于 DV-INTPAIR-EDGE 的忠实下界、域生产者归一后是否仍存在「一次性写入」残留。

## 30. CO-154 / CO-155（**CO-154 非执行者对抗复评** · 另一会话 + **CO-155 findings 处置** · executor · L2 自裁）

- CO-154 verdict = **PASS_WITH_FINDINGS**｜findings = 7（**as-found**：重跑可得不同 findings/sha，勿作复现目标）
- 独立确认（非空过）：co124 = PASS / 0 findings / 牙齿 17-17；co120 = PASS（snaps 8 / undeclared 0 / basis_not_ok 0）；CO-152 R2 勘误已落实（0.2577，旧值 0.3294 留存）且**不改变结论**；两类新判据正控确抓（declared 陈旧 sha / conservative value<faithful）。

- CO-154 findings 与 CO-155 处置：

| # | sev | 摘要 | 状态 |
|---|---|---|---|
| F-1 | medium | CO-152 删 co150 记录 `register.open_total` 未同步消费者 ⇒ 规范序内崩溃 | **CLOSED**（CO-155 修） |
| F-2 | medium | 下游**计数/版本**快照未随 CO-152 清理（co147 `open_total` 使提交 pin 不可复现） | 工件侧已修；**闸覆盖侧 OPEN** |
| F-3 | low | 修订号标签失真（§29 pin 表 co124=CO-124.6 vs 实件 .5；CO-147.2 vs .1） | OPEN |
| F-4 | medium | R-CO153-1 不成立：三域生产者 co134 不在规范序、且整表重写台账 | OPEN |
| F-5 | medium | K9 无「域覆盖」牙齿：未列 kind / `domain_cap` 缺 `domains` 静默通过 | OPEN |
| F-6 | medium | CO-153 `declared` 判据只做证据 pin、与值无语义关联 ⇒ 钉无关文件即规避 | OPEN |
| F-7 | low | `conservative_ge` faithful 由自声明 inputs 重算、未与 DV-INTPAIR-EDGE 交叉 | OPEN |

> **R-CO154-1**：复评件（非执行者、另一会话）为**独立件**且为 **as-found** 快照，不作复现目标（同 CO-151 例）。
> **R-CO155-1**（取代 R-CO153-2 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → **co155_co154_findings_disposition** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。
> **R-CO155-2**：记录**不得**内嵌其下游工件的 sha **或下游计数/版本快照**（现行 sha/计数一律由本 boundary pin 表承载）；新增此类键须在 co120 `SNAPSHOT_DECLARED` 声明。⚠ 闸覆盖面（`*_sha16` / `register.*` / `open_total` / `items_total` / 嵌套 `sha16`）**尚未**机判化 ⇒ 列 OPEN 项 F-2b，实施前以人工复核承接（**不得**据此宣称已机判覆盖）。

| 工件 | sha16 |
|---|---|
| 复评件 `m13_v57_co154_rev19_co153_co152_review.json` | `2b795c8891058cb2` |
| 工具 `p3_v57_co154_rev19_co153_co152_review.py` | `8b72c74917769bdc` |
| 工具 `p3_v57_co155_co154_findings_disposition.py` | `8c8fac7a82969a0e` |
| 工具 `p3_v57_co150_k9_domain_gate.py`（修崩溃） | `33d4879bc13deeec` |
| 工具 `p3_v57_co147_l2_ruling.py`（去计数快照） | `fbc81bdff63fc0d3` |
| 工具 `p3_v57_co148_thermal_ruling.py`（去计数快照） | `968dac508e9b8218` |
| co147 裁定 `m13_v57_co147_l2_ruling.json`（修订号实件 CO-147.1） | `6d3b58ba530483f2` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（修订号实件 CO-124.5） | `9519e07d514766a8` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 31. CO-156（**L2 自裁 · 闸硬化**：CO-154 剩余 OPEN 6 项全部处置）

| # | 处置 | 判据/牙齿 | 状态 |
|---|---|---|---|
| F-5 | K9 **域覆盖**：`kind` ∈ 七域白名单 + `domain_cap` 必带非空 `domains` | `T14_unknown_kind_teeth` / `T14b_empty_domain_cap_teeth` / `T14c_..._no_false_positive` | **CLOSED** |
| F-6 | `declared` 升级为**值-证据绑定**：须带 `evidence_ref.key_path`，证据件在该路径须**递归包含** DV `computed` | `T15_declared_binding_teeth` / `T15b_..._no_false_positive`；生产者 `co146_impedance_table`(`dv_computed_zdiff`) + `co146_ledger_add` | **CLOSED** |
| F-7 | `conservative_ge` 的 faithful **引用权威 DV**（`span_src`/`w_outer_src` + 数值交叉 DV-PAIR-CROSS / DV-INTPAIR-EDGE） | `T16_faithful_provenance_teeth` / `T16b_..._no_false_positive`；生产者 `co153` | **CLOSED** |
| F-4 | `co134` 改**只 upsert 自有条目**（stub 复跑：9 DV 全保留）；`co153` 扩为**七域 kind 的规范序内具名生产者**（`KIND_EXPECT`） | R-CO153-1 成立 | **CLOSED** |
| F-2 | co120 升 **CO-120.3**：下游快照键 = `*_sha16_after` ∪ `register.*`/`ledger.*` 下的 `sha16*`/`items_total`/`open_total`/`n_items`，未声明即 FAIL | 新增 register-snapshot 负控/正控牙齿 | **CLOSED** |
| F-3 | co124 实件 revision **CO-124.6**（与 §29 pin 表标签一致，§26 `CO-124.5` 为历史陈述）；co147 以实件 **CO-147.1** 记 | — | **CLOSED** |

- 复核：co124 = **PASS / findings 0 / 牙齿 24/24**；co120 = **PASS**（snaps 8 / undeclared 0 / teeth 7-7）；登记簿 **65 项 / OPEN 0**。

> **R-CO156-1**（取代 R-CO155-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → co155_co154_findings_disposition → **co156_co154_open_disposition** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。
> **R-CO156-2**（取代 R-CO155-2 的闸覆盖缺口项）：下游快照键（sha **与**计数/版本）由 co120 CO-120.3 **机判**；记录不得内嵌下游 sha/计数/版本快照，新增须在 `SNAPSHOT_DECLARED` 声明。
> **R-CO156-3**：单板派生物（computed/domains/几何）的生产者**只准 upsert 自有条目**；禁止对台账/记录做整表重写（先例：co134 整表重写会静默删除他 CO 归属 DV）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co156_co154_open_disposition.py` | `064ac9a59645a9b7` |
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.6 / 牙齿 24） | `481311e30b77a1b0` |
| 工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.3） | `0775970667f2552f` |
| 工具 `p3_v57_co134_req_impl_separation.py`（只 upsert） | `8f59c5be82fe9d06` |
| 工具 `p3_v57_co153_k9_domain_coverage.py`（七域 kind 生产者） | `89bb6506bc0adc6c` |
| 工具 `p3_v57_co146_impedance_table.py`（+dv_computed_zdiff） | `a1a432504f7ff6f2` |
| 工具 `p3_v57_co146_ledger_add.py`（key_path 绑定） | `146a3c06d1a9a905` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.6） | `9519e07d514766a8` |
| co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.3） | `c1b0cb595438f381` |
| co147 裁定 `m13_v57_co147_l2_ruling.json`（CO-147.1 实件） | `6d3b58ba530483f2` |
| 台账 `derived_value_ledger_v1.json`（9 DV 全域覆盖） | `b88d69dbc7a0dd51` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 32. CO-157（**L2 自裁 · 查漏型闸硬化（第 3 轮）**：4 项实测缺口 H-1..H-4 全处置）

| # | 实测缺口（修前） | 处置 | 状态 |
|---|---|---|---|
| H-1 | K9 `process_floor`（`derived_value_evidence_bad`）与 `identity_unparsable` **无负控牙齿**（判据存在但无回归保护） | T17/T17b + **元牙齿** T18（逐 finder id 注入，断言全覆盖）/T18b/T18c ⇒ 牙齿 24→**29** | **CLOSED** |
| H-2 | 判据声明失实：CO-153 称 `declared`「与 process_floor 同口径」，实际后者不验 basis/key_path | co124 注释就地订正（declared **严于** process_floor）+ 本 §32 记录 | **CLOSED** |
| H-3 | co120 `board_superseded` 弱判：任意自由文本（`board="superseded"`）即可成立豁免 | 收严为**板 sha16 格式**（`[0-9a-f]{16}`）且 ≠ 交付板 + 负控/正控牙齿；co120 升 **CO-120.4** | **CLOSED** |
| H-4 | R-CO156-3（禁整表重写台账）**无机判**（仅声明） | co136 增源码守卫 `H4_ledger_upsert_only`（写台账须先读）+ 正负控；co136 升 **CO-136.1** | **CLOSED** |

- 复核：co124 = **PASS / findings 0 / 牙齿 29/29**；co120 = **PASS**（basis_not_ok 0 / teeth 9-9）；co136 = **PASS**；登记簿 **65 项 / OPEN 0**。

> **R-CO157-1**（取代 R-CO156-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → **co157_gate_hardening_3** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。
> **R-CO157-2**：新增 K9 判据须同时登记进 `K9_FINDER_IDS` 并提供负控（由元牙齿 T18 机判）；`board_superseded` 豁免须给可比对的板 sha16。
> **R-CO157-3**（R-CO156-3 的机判面）：台账写者必须先读台账 —— 由 co136 `H4_ledger_upsert_only` **源码级**把关；⚠ 该守卫为静态启发式（**部分机判**），不替代语义审查；整表重写须在 boundary 显式豁免。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co157_gate_hardening_3.py` | `f532051e46bc7001` |
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.7 / 牙齿 29 / T18 元牙齿） | `481311e30b77a1b0` |
| 工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.4） | `0775970667f2552f` |
| 工具 `p3_v57_co136_gate_hygiene.py`（CO-136.1 / H4 源码守卫） | `a5b712e48119fdfb` |
| co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.7） | `9519e07d514766a8` |
| co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.4） | `c1b0cb595438f381` |
| co136 闸卫生 `m13_v57_co136_gate_hygiene.json`（CO-136.1） | `065ed3f2fe2d2abb` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 33. CO-158（**L2 自裁 · 交付物完整性**：L5 打样包自足）

- 实测缺口（修前）：`ORDER_NOTES.md` §2 声明「随单提交 … L2 裁定件」，§3/§6 另引 DFM 记录与 U6 热裁定，但 `jlc_package/` 内**均无该等文件**（in-package=False）⇒ 下单时 silent omission；包内阻抗表副本亦为 CO-156 前陈旧件。
- 处置（**CO146-PKG.2**）：新增 `06_rulings/`（3 份 L2 裁定件 + DFM 记录）+ ORDER_NOTES 引用改**包内路径** + 牙齿 `t05_declared_rulings_packaged` / `t06_order_notes_refs_resolve_in_package`；打包工具**并入规范序**。
- 复核：**全 gerber/drill 逐字节未变**（纯增量）；MANIFEST n_files = **34**，teeth = {"t01_idempotent": true, "t05_declared_rulings_packaged": true, "t06_order_notes_refs_resolve_in_package": true, "t07_packaged_rulings_match_sources": true, "t07b_parity_detector_sensitivity": true, "t08_declared_dirs_present": true, "t09_order_notes_binding_params": true, "t09b_binding_param_detector_sensitivity": true, "t10_declared_binding_source_pinned": true, "t10b_binding_source_pin_discriminates": true, "t02_8_copper_gerbers": true, "t03_drill_present": true, "t04_all_hashed": true}；登记簿 **65 项 / OPEN 0**。

**同 CO 另处置 2 项闸卫生**（实测缺陷）：

- **J-2**：co77 的 citation 候选目录**不含 L5 打样包** ⇒ §33 一类引用必被误判 CITATION_MISMATCH（实测 mismatches = `['L5/jlc_package/MANIFEST.json','L5/jlc_package/ORDER_NOTES.md']`，并连带把 co135/co136 判 FAIL）⇒ **CO-77.6** 抽出 `citation_candidates()` 补入 L5 包 + 正控牙齿 `l5_packet_citation_resolvable`；复核 co77 = PASS（mismatches []）。
- **J-3**：**闸退出码不反映 verdict** —— co77（恒 0）/co124/co135/co136 无条件 `return 0` ⇒ shell/CI 复现序无法据 rc 发现 FAIL（实测 co136 FAIL 时 rc 仍 0）⇒ 四件改为 `PASS ⇒ 0 否则 1`（co135：`PASS`/`PASS_WITH_FINDINGS` ⇒ 0；对照 co120/co150/l4/l5 本已正确）。

> **R-CO158-1**（取代 R-CO157-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → **co146_jlc_fab_package** → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → **co158_l5_packet_selfcontained** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。
> **R-CO158-2**：交付物（L5 打样包）内**声明随单提交的附件必须落包内**，且记录内引用须用**包内路径**；新增此类声明由 t05/t06 把关（声明与包内容不一致即 FAIL）。
> **R-CO158-3**：凡规范序内的闸，**退出码必须反映 verdict**（FAIL/不一致 ⇒ 非 0），使复现序可 fail-fast；被 boundary 引用的交付物目录须在 co77 citation 候选目录内。

> **附记（记录卫生·非工件缺陷）**：历次 handoff 称「工作树仅 `_shared` 模式位 dirty」**归因有误** —— 经查 k2 侧 `_shared` 的 dirty 实为 `k2/_shared/knowledge/kb.sqlite3-{wal,shm}`（未跟踪 SQLite 运行时件）；而「模式位」（`eda_core/escape_closure_analysis.py` 100755→100644）在**容器侧 `_shared` 的独立 checkout** 内。二者均属共享子模块边界、非 k2 工件；本件不修改（跨仓/运行时件），仅订正归因以免后续会话误追。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co158_l5_packet_selfcontained.py` | `5f9a909c1dac2505` |
| 工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.2 / 06_rulings + t05/t06） | `39ed4229274d3fe7` |
| 工具 `p3_v57_co77_closure_declaration_sweep.py`（CO-77.6 / L5 citation + rc） | `5459595adc50b392` |
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（rc 反映 verdict） | `481311e30b77a1b0` |
| 工具 `p3_v57_co135_review_hygiene.py`（rc） | `827a49520c8e2cd5` |
| 工具 `p3_v57_co136_gate_hygiene.py`（rc） | `a5b712e48119fdfb` |
| 打样包 MANIFEST `L5/jlc_package/MANIFEST.json` | `4563f80c8cee034d` |
| 下单备注 `L5/jlc_package/ORDER_NOTES.md` | `42ffae9eb22db38a` |
| 打样包记录 `m13_v57_co146_jlc_fab_package.json` | `7ccb47223c111ad9` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 34. CO-159 / CO-160（**非执行者对抗复评 CO-156/157/158 + L2 自裁处置**）

- 复评（**CO-159**，as-found 钉在 k2 `c4e951c`；`git show` 重放受评基线 ⇒ 不随后续修复漂移）：**12 findings**（F-1..F-12）——① K9 `declared` 空 `computed` 绕过值-证据绑定；② `conservative_ge` 权威 DV 缺失即跳过交叉校验；③ T18 元牙齿只比电池触发集、源码条件分支 finder 可绕过；④ R-CO156-3「禁整表重写」无机判（H4 只拦未读即写）；⑤ co120 快照键判据依赖嵌套容器；⑥ `board_superseded` 仅格式判（任意 16-hex 成立）；⑦ **co146_jlc_dfm_gate verdict=FAIL 而 rc=0**（违 R-CO158-3）；⑧ 打样包 `06_rulings/` 无来源一致性牙齿；⑨ ORDER_NOTES 目录级声明未覆盖；⑩ co77/co135 候选表已现分歧面无一致性牙齿；⑪ §6 回归块 co78/co81/co84/co95/co98/co106 rc 恒 0；⑫ co135 内嵌 CO-134 时点链 pin + 硬编码 boundary 文件名。
- 处置（**CO-160**，逐项）：co124 牙齿 29→**33**（T15c/T16c/T18d/T18e，升 **CO-124.8**）；co120 升 **CO-120.5**（快照键名面判据 + `SUPERSEDED_BOARDS` 白名单 + 伪造 sha 负控）；co146_jlc_dfm_gate **rc 反映 verdict**（FAIL ⇒ rc=1）；co146_jlc_fab_package 升 **CO146-PKG.3**（`t07` 副本来源一致性 + `t08` 目录级声明）；co135 升 **CO-135.3**（co77 候选表交叉一致性 + 链 pin 由现行记录派生 + boundary 取最新版）；六件回归闸 rc 反映 verdict（CO-78.2/81.2/84.2/95.2/98.2/106.3，co98 按 `baseline_ok and teeth_ok`）。
- 复核：co124 = **PASS / findings 0 / 牙齿 33/33**；co120 = PASS（teeth 12-12）；co77 = PASS（mismatches []）；co135 = PASS_WITH_FINDINGS（候选表一致）；co136 = PASS；DFM 闸 rc=1（FAIL 属预期）；打样包 teeth **9/9**；登记簿 **65 项 / OPEN 0**。

> **R-CO159-1**：K9 `declared` 派生值须带**非空** `computed`（值-证据绑定不得空过）；`conservative_ge` 的权威 DV（`DV-INTPAIR-EDGE` / `DV-PAIR-CROSS`）缺失即 FAIL（不得静默降级）；K9 判据集另由 `T18d` 以**源码**面机判（新增 finder 未登记 `K9_FINDER_IDS` 即 FAIL）。
> **R-CO159-2**：R-CO156-3 的**机判面** = co136 `H4`（写台账须先读台账）+ CO-156 的 co134 stub 复跑证据；「整表重写」的**语义面**无自动判据（已声明，由复评/登记承接）——规则文本不得表述为已机判。
> **R-CO159-3**：下游快照键判据取**键名面**（`*_sha16_after` ∪ `register|ledger[_…]_sha16|items_total|open_total|n_items`），与嵌套位置无关；`board_superseded` 的板 sha16 须在 `SUPERSEDED_BOARDS` 白名单（未登记 16-hex 不成立）。
> **R-CO159-4**：复现序内**所有**闸（含 `co146_jlc_dfm_gate` 与 §6 回归块 co78/co81/co84/co95/co98/co106）退出码须反映 verdict/基线；`co98` 按 `baseline_ok and teeth_ok` 判定（三态报告不因 OPEN 状态返回非 0）。
> **R-CO159-5**（复现序，取代 R-CO158-1）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → **co159_rev19_co156_co157_co158_review** → **co160_co159_findings_disposition** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co159_rev19_co156_co157_co158_review.py`（as-found 复评） | `56e8a976e7b0c48c` |
| 记录 `m13_v57_co159_rev19_co156_co157_co158_review.json` | `ca37c1e0a90bff22` |
| 工具 `p3_v57_co160_co159_findings_disposition.py` | `5ba953dc4fdc4ddf` |
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.8 / T15c+T16c+T18d+T18e） | `481311e30b77a1b0` |
| 工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.5 / 键名面 + SUPERSEDED_BOARDS） | `0775970667f2552f` |
| 工具 `p3_v57_co135_review_hygiene.py`（CO-135.3 / 候选表交叉一致性 + 链 pin 派生） | `827a49520c8e2cd5` |
| 工具 `p3_v57_co146_jlc_dfm_gate.py`（rc 反映 verdict） | `22fad27342bc0203` |
| 工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.3 / t07+t08） | `39ed4229274d3fe7` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 35. CO-161（**L2 自裁 · 查漏型闸硬化 4**：K9 覆盖完备性 + identity fail-closed）

- 实测缺口（修前，均机判）：**G-1** K9 无「必需 DV 清单」牙齿 —— 台账删 `DV-CO146-THERMAL` / `DV-CO146-PDN-DROP` / `DV-ENGINE-INT_PAIR_PITCH` 任一项时 co124 K9 = 0 findings、co150 `t01` 仍 True（T10/T11 负控用合成注入，不依赖真 DV 存在）⇒ 热/压降/保守实现三域覆盖可被一次 upsert 误删**无声**抹掉；**G-2** `identity` 类 fail-open —— `form` 未识别（如 `q = a + b`）或缺失时无判据命中、静默通过。
- 处置（**CO-161**）：① co124 增 `REQUIRED_DV_IDS`（9 项）与 `derived_value_inventory_missing` 判据 + 负控 T19/T19b；② `co153.KIND_EXPECT` **提为模块级**（必需 DV 清单的单一真值）；③ co150 增 `t03`（两域 kind 断言）/`t04`（co124 `required_dv_ids` == co153 `KIND_EXPECT` 键集）/`t05`（漂移可辨）；④ co124 `identity` 改 **fail-closed**（缺 `form` ⇒ unparsable；未识别 ⇒ 新判据 `derived_value_identity_unhandled_form`，并入 `K9_FINDER_IDS`）+ 负控 T20/T20b。
- 复核：co124 升 **CO-124.9**（牙齿 33→**37/37**，PASS/0 findings）；co150 升 **CO-150.2**（5 牙齿 True，rc=0）；co153 升 **CO-153.2**；登记簿 **65 项 / OPEN 0**。
- 修订号对账：§30 的 CO-150 条与 §34 所记 `CO-124.8` 为各自时点陈述；co124 **现行 = CO-124.9**（本 §35）。

> **R-CO161-1**：K9 **必需 DV 清单**完备性 —— 台账须含全部 9 项必需 DV（`co153.KIND_EXPECT` 键集为**单一真值**）；缺任一项即 `derived_value_inventory_missing` FAIL；co124 的 `required_dv_ids` 须与 co153 `KIND_EXPECT` 逐项一致（co150 `t04`）。
> **R-CO161-2**：`identity` 类派生式 **fail-closed** —— `form` 缺失 ⇒ `derived_value_identity_unparsable`；`form` 未被重算分支识别 ⇒ `derived_value_identity_unhandled_form`（不得静默通过）；新增 identity 形式须同时提供机判重算分支。
> **R-CO161-3**（复现序，取代 R-CO159-5）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → **co161_gap_hardening_4** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co161_gap_hardening_4.py` | `0801529a77fdc812` |
| 工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.9 / REQUIRED_DV_IDS + identity fail-closed） | `481311e30b77a1b0` |
| 工具 `p3_v57_co153_k9_domain_coverage.py`（CO-153.2 / KIND_EXPECT 模块级） | `89bb6506bc0adc6c` |
| 工具 `p3_v57_co150_k9_domain_gate.py`（CO-150.2 / t03+t04+t05） | `33d4879bc13deeec` |
| 记录 `m13_v57_co124_input_selfcheck_gate.json` | `9519e07d514766a8` |
| 记录 `m13_v57_co150_k9_domain_gate.json` | `00f82a241378d521` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 36. CO-162（**L2 自裁 · 查漏型闸硬化 5**：verdict 基线约束 + 已声明承载区豁免）

- 实测缺口（修前，均机判）：**G-1** co106 的 verdict 阶梯 `PASS if hard else (... else PASS)` 在 `hard=False ∧ cls_count 空` 时仍判 **PASS** —— 记录自身即 `A_frame_inset_consistency.ok = False`（2 处内缩偏差）而 verdict=PASS；且把 `BASE['spec_current']` 改成伪值（基线 pin 漂移）后仍 verdict=PASS / rc=0（`pin_mismatch` 只记录、不参与判定）⇒ 「基线可复现」与「检查通过」同时失效。**G-2** 桥接承载区（`P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4`，T2-ECN-1/2 PM 裁决的局部承载 pour）被算作内缩偏差却只记录不判定 ⇒ 偏差被静默容忍（既无登记也无 pin，违 CO-139 口径）。
- 处置（**CO-162**）：① 抽纯函数 `verdict_of(checks_ok, teeth_ok, pin_mismatch, cls_count)` —— `pin_mismatch` 非空 ⇒ `BASELINE_MISMATCH`；`teeth_ok=False` ⇒ `FAIL(teeth)`；任一 check 失败 ⇒ `FAIL_DECLARED_COPPER_MISSING` / `INDETERMINATE_REGION_SCOPED` / `FAIL_CHECKS`（**不再回落 PASS**）；增牙齿 `baseline_pin_binding` / `fail_open_closed` / `verdict_positive_control`；② 增 `DECLARED_NON_FULL_PLANE` 注册表 + **冻结 SPEC pin 锚定**（SPEC pin 不成立则豁免自动失效）+ 牙齿 `carrier_exemption_declared_only`。co106 升 **CO-106.4**。
- 复核：真基线 **verdict=PASS / rc=0**（A dev=0、豁免 4 条：2 内岛 + 2 桥接承载、牙齿 8/8）；注入伪 spec pin ⇒ **verdict=BASELINE_MISMATCH / rc=1**。登记簿 **65 项 / OPEN 0**。

> **R-CO162-1**：凡记录内带 `base_pins` 的闸，其 verdict **必须显式消费 pin 漂移**（不等即 `BASELINE_MISMATCH`，非 PASS）；任一 check 失败不得回落 PASS（由 co106 `verdict_of` 纯函数 + 牙齿 `baseline_pin_binding`/`fail_open_closed` 机判）。
> **R-CO162-2**：非整面承载区（桥接/局部 pour）的板框内缩豁免须**登记进注册表**（`DECLARED_NON_FULL_PLANE`）并**锚定冻结源 pin**，豁免逐条入记录；不得静默容忍偏差（违者按 G-2 同族处理）。
> **R-CO162-3**（复现序，取代 R-CO161-3）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → **co162_verdict_binding** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co162_verdict_binding.py` | `03cfd9b937e6b32b` |
| 工具 `p3_v57_co106_reference_plane_gate.py`（CO-106.4 / verdict_of + DECLARED_NON_FULL_PLANE） | `84eeea00d8e987cb` |
| 记录 `m13_v57_co106_reference_plane_gate.json` | `9f131d72e4780afb` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 37. CO-163（**L2 自裁 · 查漏型闸硬化 6**：下单备注↔声明定值表绑定）

- 实测缺口（修前，均机判）：**G-1** `ORDER_NOTES.md` 的「下单参数」表把 `85Ω 差分 ±10%` / `JLC08161H` / `1.6 mm` / `外层 1oz 内层 0.5oz` / `沉金 ENIG` 写为**字面量**，与 L2 政策件 `jlc_prototype_parameters_v1.json`（监理指令 #10 定值绑定）无绑定、无牙齿 —— 实测把目标阻抗改成 100Ω 后重生成的备注**仍写 85Ω** ⇒ 定值变更会静默产出**客户可见**的陈旧下单备注；**G-2** 该定值表的 `supervisor_instruction.sha16` 声明链从未被核验。
- 处置（**CO-163**）：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.4** —— 载入声明定值表 + 纯谓词 `binding_params_in_note`/`binding_tokens`；牙齿 `t09_order_notes_binding_params`（备注须逐项命中叠层码/厚度/外内层铜/目标阻抗/容差/表面处理）+ `t09b` 漂移灵敏度 + `t10_declared_binding_source_pinned`（定值表来源 sha16 == 监理指令件 sha16 `35aafe268ff52f89`）+ `t10b` 判据可辨；记录落 `declared_binding`（含 `source_instruction`: path/available/declared_sha16）。
- 复核：打样包 teeth **13/13**（t01..t10b 全 True），订单备注正文与 gerber/drill 逐字节不变；注入定值漂移（100Ω/2.0mm）⇒ t09 立即 FAIL。登记簿 **65 项 / OPEN 0**。

> **R-CO163-1**：客户可见交付物（L5 打样包/下单备注）内的**工程定值**必须与**声明定值表**逐项一致，由 t09/t09b 机判；定值表变更而备注未同步即 FAIL（禁止字面量单向复制导致静默陈旧）。
> **R-CO163-2**：声明定值表的**来源 pin**（`supervisor_instruction.sha16`）必须可核验（t10/t10b）；跨仓来源不可达时 fail-closed 并在记录内显式登记 `available=false`。
> **R-CO163-3**（复现序，取代 R-CO162-3）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → **co163_binding_to_order_notes** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co163_binding_to_order_notes.py` | `d01c050fb1578c87` |
| 工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.4 / t09+t09b+t10+t10b） | `39ed4229274d3fe7` |
| 打样包 MANIFEST `L5/jlc_package/MANIFEST.json` | `4563f80c8cee034d` |
| 下单备注 `L5/jlc_package/ORDER_NOTES.md` | `42ffae9eb22db38a` |
| 记录 `m13_v57_co146_jlc_fab_package.json` | `7ccb47223c111ad9` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 38. CO-164（**L2 自裁 · 收敛判定硬化**：规范复现序 rc 机判执行器）

- 实测事故（CO-163 期间，机判）：`p3_v57_co146_boundary_append.py` 因 §37 文本内 f-string 花括号语法错误**每轮 rc=1 崩溃** ⇒ 第 37 节从未写入、boundary 停在 v2.08、pin 表陈旧（co77 = CITATION_MISMATCH、co135/co136 = FAIL）；而「幂等循环」只看 boundary/记录 sha ⇒ 报 CONVERGED。即 **「以 sha 稳定替代 rc 检查」= 假收敛**；本会话由一个独立 rc 复核发现（自查也据此复现并修复）。
- 处置（**CO-164**）：新增 `p3_v57_co164_order_runner.py`（**不在**规范序内运行，避免自递归；报告落 `.archer_tmp/`，**不被 boundary 引用** ⇒ 不构成下游快照/不动点）：① rc 策略 `EXPECTED_NONZERO = {co146_jlc_dfm_gate}`（verdict=FAIL 属预期），其余任一步非零 ⇒ **立即停机**并报门名/rc/stderr 尾；② **真收敛** = rc 全合规 ∧ 受控 sha 逐轮稳定；③ `--check` 静态体检 t01..t06（步骤存在/可编译/rc 策略/判据灵敏度/稳定性判据/序文本一致）。
- 复核：`--check` **6/6 True**（t06 当场抓到本文档序与执行器 ORDER 的短别名漂移 `co159_rev19_review`，已改为实际步骤名）；端到端负控：把 `co78` 步替换为 rc=3 合成件 ⇒ **abort（rc=1，iterations=1）不报收敛**；登记簿 **65 项 / OPEN 0**。

> **R-CO164-1**：复现序收敛判定**rc 优先** —— 除 `EXPECTED_NONZERO` 白名单（当前仅 `co146_jlc_dfm_gate`，其 verdict=FAIL 属预期）外，任一步 rc≠0 即**立即停机**；**禁止**以「sha 稳定」单独判收敛。
> **R-CO164-2**：规范序**文本**与执行器 `ORDER` 须**有序一致**（由 runner `--check` t06 机判）；新增/变更步骤须同步 runner 与本 boundary。
> **R-CO164-3**（复现序，取代 R-CO163-3；步骤集不变）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**（收敛判定须遵 R-CO164-1：以 rc 为准）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co164_order_runner.py`（rc 策略 + 真收敛 + `--check` t01..t06） | `25d706b4ba30ea3b` |
| 工具 `p3_v57_co164_disposition.py` | `47356d70e9d684c5` |
| 工具 `p3_v57_co146_boundary_append.py`（§38 + 序文本订正） | `3e23ea03d84cd2f8` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |

## 39. CO-165（**L2 自裁 · 收敛执行器加固**：白名单证据 + 受控 sha 全域）

- 实测缺口（修前，均机判）：**G-1** CO-164 执行器的白名单只按 `rc≠0` 放行 ⇒ 白名单步（当前仅 `co146_jlc_dfm_gate`）的**任何**非零——含崩溃/静默失败——都被当「预期 FAIL」。负控：把 DFM 闸替换为 `raise SystemExit('boom')`（rc=1、stderr 无 traceback）⇒ **旧判据放行**；仅加 Traceback 检测**仍不足**（不打印 traceback 的失败会让盘上**陈旧** FAIL 记录充当 verdict 证据 —— 由本会话自己的端到端负控当场证伪）。**G-2** 受控 sha 仅 7 件（漏 co106/co150/打样包件）⇒ 未受控文件的 2-循环/抖动对收敛判定**不可见**。
- 处置（**CO-165**，执行器升 **CO-164.2**）：白名单项改 `verdict/record/why` 结构化 + 纯判据 `allowlist_decision(step, rc, stderr, verdict, record_fresh)` —— 白名单步须 **rc≠0 ∧ 无 Traceback ∧ 记录由本次执行产出（mtime 新鲜）∧ 记录 verdict == 声明 verdict** 方判 `expected_nonzero`，否则判 `expected_step_returned_zero`/`expected_step_crashed`/`expected_step_record_not_produced`/`expected_step_verdict_mismatch` 并**立即停机**；`watch_paths()` 覆盖 boundary + **全部**记录 + 台账/登记簿 + 打样包 MANIFEST/ORDER_NOTES；`--check` 增 **t07**（四类伪通过负控 + 恒真正控）/ **t08**（受控集覆盖记录类产物）。
- 复核：`--check` **8/8 True**；负控 A（co78 步 rc=3 合成件）⇒ abort(rc=1)；负控 B（DFM 步 `SystemExit('boom')`）⇒ abort class=`expected_step_record_not_produced`；正控：真 DFM 闸（重写记录、verdict=FAIL）判 `expected_nonzero` 且整序 **converged（iterations 2 / rc=0）**。登记簿 **65 项 / OPEN 0**（注：`co148` 登记项在序内为 OPEN、由 `co150` 收口 ⇒ 中途 OPEN 属正常，须以整序收敛后为准）。

> **R-CO165-1**：`EXPECTED_NONZERO` 白名单步须给**双重证据** —— 期望 `verdict` **且** 记录由**本次执行产出**（mtime 新鲜）；`rc≠0` 本身不构成预期 FAIL 的证据（崩溃/静默失败不得被放行）。
> **R-CO165-2**：收敛判定的受控 sha 须覆盖**全部**序内产物（boundary + 全部 `m13_v57_co*.json` + 台账/登记簿 + 打样包件）；新增产物须落入 `watch_paths()`。
> **R-CO165-3**（复现序，步骤集与 R-CO164-3 相同）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2）。

| 工件 | sha16 |
|---|---|
| 工具 `p3_v57_co164_order_runner.py`（CO-164.2 / `allowlist_decision` + `watch_paths` + t07/t08） | `25d706b4ba30ea3b` |
| 工具 `p3_v57_co165_runner_hardening.py` | `3cb331ff39b0c824` |
| 登记簿 `input_defect_register_v1.json`（65 项 / OPEN 0） | `dd9f79eb0aaec2a1` |
