# 口径登记册（CONVENTION REGISTER）· 2026-09-21 · #K2-53 §三-2

> **用途**：把「**已裁定为口径、非缺陷**」的跨库/跨板差异**集中登记**，供任何会话
> **先查后报**（红线：声明「新发现」前先查 `PRIOR_ART_REGISTRY_INDEX`）。
> **纪律**：登记制 = **不豁免 · 保持可见 · 不充绿**；**禁**以「不入范围」洗白为绿（C-12）。

| # | 条目 | 差异（事实） | 裁定 | 依据 | 处置红线 |
|---|---|---|---|---|---|
| **CR-1** | **J1 TX 对 P/N 反相** | K1 `J1` 符号 `TX_P` → pad **A3**（标准 = `SSTXn1`，**负触点**）· `TX_N` → **A2**（`SSTXp1`）；`TX2_P` → **B3**（`SSTXn2`）· `TX2_N` → **B2**。RX 两对极性正确。 | **口径 · 非缺陷 · 不升级** | #K2-53 §二；停机条件（TX/RX **对**交叉）**未触发**：`PCIE_TX0/1_*` 全落 **SSTX 触点**、`PCIE_RX0/1_*` 全落 **SSRX 触点** | **禁**改符号脚号（受 `k1_pinmap.yaml#J1` + `criteria.measure_pin_map` 管辖；改=设计面）；「是否有意」= L1 语义 → owner **知悉项**，不阻塞 |
| **CR-2** | **USB-C SS 对 ± 命名口径（J1-SSP-2）** | `USB_C_RECEPT_24.yaml` 的 **B 行角色**与 `USB_C_PLUG.yaml` 及 **KiCad 官方符号**相反（24.yaml: B2=SSRXp2 …）；`k1` 符号采用 host/标准口径，`key_v2` 符号采用 device/交叉口径 | **维持不统一 · 登记为口径**（host/device **视角差**） | #K2-53 §二；`24.yaml` 与自身 aliases 及 **key_v2 符号自洽**（key_v2 PIN-01 = PASS(0)） | **禁**改 `USB_C_RECEPT_24.yaml`/`USB_C_PLUG.yaml`（动它 ⇒ 触 key_v2 回归）；将来统一须**另立跨项目回归批**（key_v2+k1+k2） |
| **CR-3** | **IOCONVERT 符号表示法差** | `k2/hw/lib/IOCONVERT.kicad_sym` 的 `DS320PR1601` 变体 **194 个 pin 以 ball 名命名**（如 `AE1: AE1`）；`k2/hw/lib/DS320PR1601.kicad_sym` 同 ball = `GND`（信号名） | **登记制：不豁免 · 保持可见 · 不充绿**；**不入 K2 门禁链判据**（`k2/pipeline.yaml` 无 pinmap 检查） | #K2-53 §二 | **禁**改任何 `.kicad_sym`（改符号 = 设计面 = 须 owner）。PIN-01 读数：该库 **1 → 194**（可见、不隐藏） |
| **CR-4** | **tier2 出处不可约下界** | `parts` 真源三件套：标准件 5 + 约定件 6 + 语义件 1 = **12 件结构性无三件套**；余 6 件外部通道**强时效**（本轮 diodes/atta/liteon/molex 全封） | **「12 件 = 不可约下界」登记为口径**；tier2 裁定时 **15/33**；余 6 件**具名 PARTIAL**（**读数后经 **CR-6** 更新为 17/33**） | #K2-53 §二 | **禁**把「可达上限 21/33」作为**任何判据/绿判**；「软目标」**仅**作排期用语；**禁每轮全量重探**（改按需） |

---
**登记口径说明**：以上均**不影响** P6 判据面与交付锚（`6ee7495de61f749f` 未动）；
`criteria/` **只读未动**（判据 **rev=6**）。

### 续编 · #K2-54 裁定落地（2026-09-21 · 裁定号即依据）

> 编号以 **#K2-54 §七-1 执行序**为准（CR-5 = P6-1 口径；COV-C1/C2/C3 = 三项订正登记）。
> **纪律不变**：登记制 = **不豁免 · 保持可见 · 不充绿**；**禁**以「不入范围」洗白为绿（C-12）。

| # | 条目 | 差异 / 事实 | 裁定 | 依据 | 处置红线 |
|---|---|---|---|---|---|
| **CR-5** | **P6 判据①口径（P6-1 闭法）** | P6 判据①（A 项）判定口径：判据①之四项『必须命中』以**整改前命中证据**（P6_1_ACCEPTANCE_MECHANIZED_v1 探针实测 4/4 OK + 本件复现）**加** 整改记录（k1 c018fc7 · k1/pipeline.yaml · k1/fp-lib-table）**闭合**；整改后验收器对同三项报 MISS 属预期（缺陷已消除），**不作为 FAIL 依据**；`sheets_empty(1)` 维持输入侧实测 OK。**本口径不新增判据维、不放松任何维的下限。** | **采纳 (a)**（#K2-54 §一 · 自裁） | #K2-54 §一；监理独立复核：探针件 sha16 `9b3ef86947424e0c` · 四项 **4/4 OK**（实跑复现）· 整改后三维不再 FAIL（`k1 c018fc7` · `k1/pipeline.yaml` `8946a22e677055bc` · `k1/fp-lib-table` `13ddfa5331d67e13`）· P6-2 **PASS** | **禁**改验收器/`criteria/`/新增判据维/放松下限；**P6 闭合 ≠ 越阶段**（P5 维持 `PENDING_EXTERNAL`） |
| **CR-6** | **tier2 读数更新（新通道）** | 经 **`media.digikey.com`**（≠ `www.digikey.com` 403）取回 **OPTO_LTV356T**（`e340ba0a…` · p2 图例与 repo 4/4 一致）· **STM32G0B1KBU6**（DS13560 p45 Fig.12 · 32/32 归一一致） | **知悉 15/33 → 17/33**（具名 · **不充绿**） | #K2-54 §五；证据 `T2F6_NEWLANE_PROBE_20260921_v2.json`（f609d256eb30d822） | **禁**入判据/绿判；**禁**每轮全量重探；外部原件仅落 `/tmp/opencode` |
| **CR-7** | **pciesw4 覆盖面缺口（COV-C1）** | 范围外未覆盖 = **4 目录 / 39 件**：`pciesw4/aic`=**1** · `pciesw4/aic/sch_kicad`=**17** · `pciesw4/gpu`=**1** · `pciesw4/gpu/sch_kicad`=**20**（监理 per-dir 直数 = 与本册一致；v21 旧记 `2/19` 为**换位笔误**，以本行为准）。`k2/hw/sch`、`key_v2/key_v2/sch` **实为已覆盖**（`k2/pipeline.yaml`、`key_v2/key_v2/pipeline.yaml`）；dim 文本『范围外 **47**』= 范围外**文件数**，≠ 未覆盖目录数。**k2 域内未覆盖 = 0** | **采纳 option_B**（#K2-54 §二 · 自裁）：`pciesw4` **项目侧自持 `pipeline.yaml`** · **零 criteria 变更** · 跨项目批次由 gate 属主排期 | #K2-54 §二 | **禁**由 ENG 自落 pciesw4 文件；**禁**以「不入 k2 范围」洗白为绿；option_A（criteria `out_of_scope_registry`）**仅备选·须 gate 属主裁** |
| **CR-8** | **COV-C2 · 补丁前像新鲜度检查（检查缺环）** | 『落件候选』呈报「待放行」**前**必须对**活树**做**前向**校验；本例 v4 候选的 `target_sha16` 实为**后像**（`c9e1c3b4ca208482`）⇒ 与现树**自比**，无法区分『未应用』与『已应用』；真前像 = `dcd1f65f4b549527` | **登记（#K2-54 §三）** | #K2-54 §三；实测：`BATCH6_V4_RELEASE_PRECHECK_20260921_v1.json`（fa4e15eafad1acb7） | **落点（可复现命令 · 容器根执行）**：`git apply --check <候选补丁>` ⇒ **RC=0 = 可落**；**RC≠0 = 已应用/前像陈旧** ⇒ 标 **`superseded`** 并把**真实前像**记入 `pre_image_sha16`（**禁**以后像充当 `target`）。补充判据：`git apply --reverse --check <补丁>` **RC=0** ⇒ 树已是后像 |
| **CR-9** | **批 6 v4 = 已随 `ea2b746` 生效** | 树 = **v4 后像**：正向 `git apply --check` **RC=1**（`patch does not apply`）· 反向 **RC=0** · v3 反向 **RC=1** ⇒ 树 **≠ v3 后像**；内容来源 `git log -S'_polyline_degenerate' / -S'_PairClearField'` 均 = **`ea2b746`**（批 6 同批一笔 · commit msg 明列 R-10 退化候选守卫） | **采纳 (i) 追认**（#K2-54 §三 · 自裁）：v4 随 v3/批 6 生效 · **无落地对象** | #K2-54 §三 | **禁**为 v4 **单独升版**（ENG 维持 **1.1.4**）· **禁重复落地** · 引擎 sha 维持 `c9e1c3b4ca208482` |
| **CR-10** | **四树引擎漂移（COV-C3）** | `hs_route_model.py` 三态：`_shared` = `k2/_shared` = **`c9e1c3b4`**（5225 行）· `key_v2/_shared` = **`883525b4`**（3849 行 · 末次 `8f58466` M13 v8）· `pciesw4/_shared` = **`6ab5eaaa`**（4121 行 · 末次 `d24eb0b` M13 W6-D）；`ENG_VERSION.yaml` 仅 `_shared`/`k2/_shared` 有（**1.1.4**），另两树**无**（既有结构差） | **采纳 (b)**（#K2-54 §四 · 自裁）：**另立跨项目同步批次**（gate 属主排期）· 未同步期**各树钉版登记** | #K2-54 §四；证据 `FOUR_TREE_ENGINE_SYNC_CENSUS_20260921_v1.json`（4e2a2cd0fa4032cf） | **禁**以漂移阻塞 P6 · **禁**改 `criteria/` · **禁越权改** `key_v2`/`pciesw4` 文件；登记制 = 不豁免 · 保持可见 |

---
**（本块）登记项与裁定对应**：CR-5 ← #K2-54 §一 · CR-6 ← §五（知悉）· CR-7 ← §二 · CR-8 ← §三 · CR-9 ← §三 · CR-10 ← §四。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。

### 续编 · #K2-55 落地（2026-09-21 · 裁定号即依据）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-11** | **`MCU_VDD` 二极管 ORing 标称口径** | `U4` = **`BAT54C_ORING`**（`A2=P3V3 → K=MCU_VDD`；**A1 悬空**；`J13/VCC`·`J9/VCC` 同挂 `MCU_VDD`）⇒ **主判工况 = 独立运行（`J13/VCC` 不接外供）· 标称 = 3.0V · 窗 2.85–3.15V**；`J13` 在位读数 = **辅助**（3.3V ±5% = 3.135–3.465V）**须同记、不改主判** | **#K2-55 §一**（口径澄清 · 自裁） | **禁**改 ±5% 容差 · **禁**改 `criteria/` · 禁以辅助工况替代主判（会**假绿**板载链故障） |
| **CR-12** | **件内 `ts` 语义（COV-C4）** | **定义**：`ts` = **真实写入时刻**（`datetime.now().astimezone().isoformat()`）；**逻辑会话日**须另立 **`session_label`**，**禁混用**。**回头看**：本会话及前序部分工件之 `ts` 为『逻辑会话日』式（本会话 5 件偏差 +8h38m…+11h45m，**非恒定**）⇒ **保留原值**、由本登记统一语义，**不静默回改** | **#K2-55 §二-4**（登记要求） | 新件一律「真实 `ts` + `session_label`」；历史件**禁**事后改 `ts`（保可追溯） |
| **CR-13** | **『命令重复（疑似空转）』具名说明** | 告警之重复分三类：**A 幂等只读复验**（锚/status/模板检视 —— 阶段门 fail-closed 要求每轮证明未漂移，**必要**）· **B 工作流形式重复**（工件写入 heredoc **前缀同而 payload 不同**，各件 sha16 各异；容器指针提交**同串 5 次各推进到新 sha**）· **C 同轮分析迭代**（PDN 图分析 3 次：映射缺失 → **盲埋孔形态漏解析** → 定稿，输出实质不同） ⇒ **无空转** | **#K2-55 §二-3**；证据件 `K2_55_EXECUTION_AND_COMMAND_REPETITION_STATEMENT_20260921_v1.json` | 已落 4 项缓解：**M1** 脚本首行唯一轮标 · **M2** 指针提交命令内联目标 sha · **M3** 同轮只读核对批处理 · **M4** 分析先修后跑；若再现**无新读数/无新落件**之重复 ⇒ 按 **C-12** 自查上报 |

---
**（本块）裁定对应**：CR-11 ← #K2-55 §一 · CR-12/CR-13 ← #K2-55 §二-4/§二-3。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。

### 续编 · #K2-56（进程合规 · tag 断档收口）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-14** | **里程碑 TAG 断档口径（+ 编号说明）** | **事实**：末 tag = `k2-v57-co53-impedance-geometry-open`（**2026-09-12** · `7dea46d`）⇒ 至收口时 **HEAD 距 tag 682 commit**（跨 G7/L5 PASS · L6 交付 · P0–P6）；期间 gate/交付事件发生而**未随事件打标** ⇒ **进程缺口（非产物缺陷）**。**自 #K2-56 起**：按 `k2/pm_gate/TAG_POLICY.md` §1/§2 **按 gate 切换与交付里程碑打 annotated tag**，且每次 push 后以 `git ls-remote --tags origin` + **`^{}` 解引用**核验。本次补打 = **`k2-v57-l6-delivery-anchored` → `9758b76`**（message 含**交付锚 sha16 `6ee7495de61f749f`** · 受审板 `c5a7df90aadb66e0` · 判据 rev=6 · 复现命令）。**编号说明**：#K2-56 §三-4 引用 `CR-12`，但 **CR-12 已由 #K2-55 §二-4（`ts` 语义）占用** ⇒ 本项落 **CR-14**（ENG **不改/不占** CR-12）。 | **#K2-56 §一/§三-4**（进程合规 · 自裁 · **不推回 owner**） | **禁**为 682 历史 commit **批量补打**（**禁伪造里程碑**）· 禁 amend/rebase **已发布** 段 · 禁改冻结四源/`criteria/`/交付包 |

---
**（本块）裁定对应**：CR-14 ← #K2-56 §三-4。**不影响** P6 判据面与交付锚（`6ee7495de61f749f` 未动）。

### 续编 · T2-F6 第三轮新通道探取（2026-09-21 · ENG 只读造活 · 通道登记）

| # | 条目 | 内容（事实） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-15** | **T2-F6 可达/封锁通道登记（免重复试探）** | 第三轮**新登记**（前两轮 #K2-52/#K2-53 未登）**可达 PDF 面**：`www.farnell.com/datasheets/<id>.pdf`（200 · **同域 `uk.farnell.com` 产品页/搜索 = 403**）· `uploadcdn.oneyac.com`（厂商原件镜像 · 200）· `www.diodes.com/assets/Databriefs/*.pdf`（200 · **同域 `assets/Datasheets/*.pdf` = 404、`/part/view`·`/search` = 403**）· `file.elecfans.com`（200）。**可用搜索面**：`www.so.com`（200，结果 URL 可直取）· `www.baidu.com`（200，需解析 `mu=` 属性）。**分销/数据表站**：`oneyac.com`·`ruidan.com`·`chipscn.com`·`ickey.cn` 产品页 200；`item.szlcsc.com`·`www.lcsc.com/search`·`datasheetarchive.com` 仅 **SPA/JS 壳**（无内联直链）。**封锁面（本板上件全数实测）**：`www.molex.com` **整域 000** · `www.digikey.cn`/`www.mouser.cn`/`uk.farnell.com`/`sg.element14.com`/`www.diodes.com/part|search`/`atta.szlcsc.com`/`wmsc.lcsc.com`/**`.alldatasheet*.com`** = **403** · `datasheet.eeworld.com.cn`/`r.jina.ai`/`datasheetspdf.com`/`datasheetcatalog.com`/`pdf.la`/`icpdf.com` = **000** · 公共 CORS 代理不可用。**本轮实得**：**PI3DBS16412** 取得 Diodes/Pericom **Product Brief**（官方域 + oneyac 双源 · sha `4ef19e6a…`/`ea1a10cd…` · `26b56444…` 渲染图证）⇒ 与 repo 真源 **9/9 一致**（封装 42-TQFN ZH42 3.5×9mm · 选定号 ZHEX=ZH · 4 差分通道 2:1 Mux/DeMux 双向 3.3V 1–20Gbps · 信号口 A0..A3/B0..B3/C0..C3 全在 · 控制脚 SEL1/SEL2/PD1/PD2 · 无 REFCLK/OE#/SMBus） | **#K2-53 §二 T2-F6 ④**（新线索才试）+ handoff §7-B（只读造活） | **Product Brief 无脚位表 ⇒ 42 脚逐脚真源（DS40277 全表）仍未取得** ⇒ tier2 维持 **具名 PARTIAL · 17/33 · 不充绿**；**禁**入判据/绿判（C-12/C-25）· **禁**以兄弟件（`PI3DBS12212A`）充作本板件真源 · 外部厂商原件仅落 `/tmp/opencode` |

---
**（本块）裁定对应**：CR-15 ← #K2-53 §二 T2-F6 ④（新通道才试）· 属**方法/通道登记**（非缺陷、非判据）。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · P5 外发包测点一致性（2026-09-21 · ENG 只读复核发现 ⇒ 规程修正）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-16** | **V5 具名测点口径（防假绿）** | **事实（复核发现 P5-V5-1）**：内部 `PDN-F3` 已将 `P3V3_AUX` 标为『**观察项（V5 须覆盖）**』（该轨 In4 平面为小岛 38.7+42.5 mm² ⇒ 实质**迹线分配**：总长 **109.44mm** · 宽 0.2mm · **最坏单跳 `In5.Cu` 20.789mm = 125.3 mΩ@85℃**），handoff 回填口径亦要求覆盖 `J3`/`J4` 端；**但外发三件（`RULES.md` §V5 / `CHECKLIST.md` / `results_template.json`）原先均无具名测点** ⇒ 实测方可取近端 ⇒ **假绿该轨**。**口径（自裁）**：V5 之 `P3V3_AUX` **负载点强制取 `J3` 或 `J4` 之 `P3V3_AUX` pad**（板侧机核：`J3`/`J4` 各 **1** pad；同网 `C90`/`J11`/`R1`/`U1` 各 1）；其余三轨负载点须**注明 refdes**。**已落件**：`RULES.md`（`8bee0961`→`498c365f`）· `CHECKLIST.md`（`d7dda9a8`→`b91fd606`）· `results_template.json`（`51f1e9a1`→`fc1b93c4`） | **handoff §7-A-3 回填口径** + §7-B 只读造活（P5 可判性核对）· 属 **L2 规程面自裁** | **未新增判据维/检查齿**（V5 为既有项 · 阈值仍 3%）· **未触**交付锚 `6ee7495de61f749f` · **未改**受审板/SPEC/`criteria/` · 本口径方向为**防假绿**（C-12），**禁**以此缩口径或改阈值 |
| **CR-17** | **P5 V6-2 `DBGMCU_IDCODE` 预期值 = 手册依赖项（未闭）** | **事实**：`results_template.json` 中 `st_dbgmcu_dev_id_expected` 仅记『须以 **RM0454 §DBG** 检取（st.com 离线不可达 ⇒ 手册依赖项）』⇒ **无具体预期值**（`SW-DP IDCODE` 预期 `0x0BC11477` 已有）。**本轮新通道**：`www.stmcu.com.cn/Designresource/detail/reference_manual/699676`（ST 中国官方资源页）⇒ **HTTP 429（限流）**；`www.st.com` 仍不可达 ⇒ **未取得** | **本会话实测**（T2-F6 第三轮旁支） | **非缺陷 · 不阻塞**（V6-2 判据 = 『与器件手册一致』，实测值可后验）· **禁**以记忆/推测填规范值（须可引证）· 再遇可读 RM0454 之**新通道**即补 |

---
**（本块）裁定对应**：CR-16 ← handoff §7-A-3 + §7-B（L2 规程自裁）· CR-17 ← 实测登记。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · P5 外发包具名实体对账（2026-09-21 · 第三批只读造活）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-18** | **V6-3 预期地址 `0x52` 已由板侧完全证明 + 外发包具名实体对账通过** | **对账结果 9/9 PASS · 0 缺口**（详见 `P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION_20260921_v1.json`）：① `V6-2` NRST 测点 `U1.10`/`R29.1`/`C73.1` 皆为 `NRST`；② `J13` pad1=SWDIO/pad2=SWCLK_BOOT0/pad3=GND 与自查件逐脚一致；③ **`E2` 逐脚机核 = 1 GND · 2 `MCU_VDD` · 3 GND · 4 GND · 5 `I2C1_SDA` · 6 `I2C1_SCL` · 7 GND · 8 `MCU_VDD` ⇒ A2A1A0=010 ⇒ 7-bit **`0x52`**（写 0xA4/读 0xA5）—— 与件内 `expected_address` 一致 ⇒ 已回写 `results_template.json` `board_verified`**；④ `U6`=`DS320PR1601`(354pad) · `J2`=`SlimSAS x8 74pin` · `J3`/`J4`=`MCIO 4i`(各38pad)；⑤ 平面：`In1`/`In3`/`In6` 皆 `GND` · `In4` 7 zone = `P3V3`×2/`P3V3_AUX`×2/`12V_IN`×2/`MCU_VDD`×1（F.Cu 4 zone 皆 ESC keepout）⇒ 与 `PDN-F3`『小岛』互证；⑥ `PCIE_UP3_P/N` 实走 F.Cu 30 / In5 31 / In2 4 段 ⇒ V4 层位声明成立，**B.Cu `_P/_N` 段 = 0** ⇒ 观察项 4 成立；⑦ 观察项实体（`U1.23/24` · `U6.FG1` · `H4/R41/D2/C87`）皆在板 | **handoff §7-B** + `RULES.md` §0（『所引件已机核』）· **首次对账**（非复评） | **非新增检查齿**（不新增判据维/阈值）· **未触**交付锚 `6ee7495de61f749f` · **未改**受审板 `c5a7df90`/SPEC/`criteria/`；`0x52` 之证明**仅作预期值锚**，**实测仍由实测方执行、判定仍归监理**（ENG 不得自证） |

---
**（本块）裁定对应**：CR-18 ← handoff §7-B（L2 可判性核对 · 证据登记）。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · P5 V7 热判据口径唯一化（2026-09-21 · 热机械 = L2 自裁）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-19** | **V7 `Tj` 反推口径冲突 ⇒ 唯一化（含 `ψJT` 无源）** | **事实**：同一『case-top 温度 ⇒ `Tj`』反推有两式 —— ① 外发 `RULES.md` §V7：`Tj = Tcase + P·6.5`；②《K2 整体整改计划》§**L2-9c′**：`Tj = T_top + P·3.6`（ψJT）。差 = `2.9·P` ⇒ 最重档(7.0W) **+20.3℃** ⇒ **同板可判相反**（设计点 `Tj=117.0` ⇒ `T_top=91.8` ⇒ θJC 式给 **137.3℃ ⇒ FAIL**，ψJT 式给 PASS）· θJC 式下 `T_top ≥ 71.5℃` 即误触 T1（真 Tj 仅 96.7℃）。**源核**：机器可读手册件 `m13_v57_co148_u6_ds320pr1601_inputs.json`（`d98677fd7f7d51ba`）含 `θJC_top=6.5`、`θJA=17.4`、`ψJB=5.9`、`θJB=6.1`，**独无 `ψJT`**（全库仅 `K2-RECTIFICATION-PLAN-v1.md:429` 正文自述）⇒ `6.5` **有源可复算** · `3.6` **无源**。**L2 自裁（L2-V7-1）**：**唯一判据式 = `Tj = T_top + P·θJC_top(6.5)`**（有源 · 保守上界）；**`ψJT` 式不得单独作 PASS/FAIL/T1 依据**（须先补源或改仪器直读）；**必记原始 `T_top`/`P`/`Ta`/装配**；**两式不一致 ⇒ 监理裁定**；**判据式超限须连同原始量交监理复核后再开新 rev**。**已落件**：`RULES.md`（`498c365f`→`af8c3dd9`）· `CHECKLIST.md`（`b91fd606`→`e2e6a074`）· `results_template.json`（`6714b139`→`00d6ff4c`，增 `tj_conversion_caliber` + 四工况 `Ttop_C`） | **handoff §7-B**（热侧核对）· **宪法第二章（热机械 = L2）** · **owner ⑦**（口径澄清 = 自裁面，不推回 owner） | **未改任何阈值/触发**（`≤120.0℃` · T1 `>117.0℃` 逐字不动）· **未新增判据维/检查齿**（同向：防假绿）· **未触**交付锚 `6ee7495de61f749f` · **未改**受审板/SPEC/`criteria/` |
| **CR-20** | **`ψJT` 出处缺口（开放依赖）** | `ψJT = 3.6 ℃/W` 仅见计划正文自述，**无手册机器可读件**（TI SNLS683 节录件 `623b562cfc8262d2` 未含）⇒ **待补源**（取回 SNLS683 §Thermal 或改仪器直读 `Tj`）。在补源前，该值**仅可作参考**（CR-19 已定其不得单独作判据） | 本会话实测（源核） | **非缺陷判定**（属依赖）· **禁**以未源之数改判 PASS（C-12）· 再遇新通道即补 |

---
**（本块）裁定对应**：CR-19 ← L2 自裁（L2-V7-1）· CR-20 ← 源核登记。**报备监理 1 条（口径口径唯一化 · owner 项 0）**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · 【更正】V7 热口径 + 新通道 TI（2026-09-21 · 取得 SNLS683 正本后自纠）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-21** | **V7 `Tj` 反推口径【更正】（L2-V7-1′）** | **新证据**：新通道 **`www.ti.com`** 取得 **DS320PR1601 正本 SNLS683（JUNE 2023）**，`sha256 = f61599c4356edb395e07c9300999ab818898986a4adde71753bae7a080c039da`（**与本项目裁定链所引件逐字节相同**）；**§6.4 Thermal Information（p16）明文含 `ψJT = 3.6 ℃/W`**（*Junction-to-top characterization parameter*）⇒ **ψJT 有源、且为 top 面反推之正确参数**。**裁定（**作废** CR-19 之判据式部分）**：**唯一判据式 = `Tj = T_top + P·ψJT(3.6)`**（回到《整改计划》§L2-9c′ 并补出处）；**`θJC_top(6.5)` 限用于设计预测链** `θJA_eff = θJC_top + R_int + θHS = 11.0`（L2 v2.0 §1），**不得**用于 `T_top ⇒ Tj`；**必记**原始 `T_top`/`P`/`Ta`/装配 **+** 6.5 式保守上界；**边界**（`>117.0`/`>120.0`）须**监理复核**后再开新 rev；**两式不一致 ⇒ 监理裁定**。阈值 `≤120.0`/T1 `>117.0` **逐字未改**。（CR-19 之『口径冲突存在』这一**事实认定仍成立**，仅判据式方向更正。）**已落件**：`RULES.md`（`af8c3dd9`→`5fbb54b9`）· `CHECKLIST.md`（`e2e6a074`→`1f45c783`）· `results_template.json`（`00d6ff4c`→`2346d303`） | 正本 §6.4 p16 + `P5_V7_TJ_CALIBER_CORRECTION_TI_SNLS683_20260921_v1.json`（2d87c504be3db577）· 图证 `8df6571f9a7643f7` | **未改阈值** · **未改** `m13_*` 历史派生件（sha 链不动）· **未触**交付锚/受审板/`criteria/` · **未新增判据维/检查齿** |
| **CR-22** | **【撤回】CR-20（『`ψJT` 无源』为误判）** | **撤回理由**：前件 CR-20 仅以 repo **机器可读派生件**取证（`m13_v57_co148_u6_ds320pr1601_inputs.json` `d98677fd7f7d51ba` 与 `m13_v57_co204_thermal_verification.json` **均未收录 `ψJT` 行**）⇒ **把『派生件字段缺失』误读为『无源』**（本会话仅 1 次，已自纠）。**改立登记**：`m13_*` 派生件**缺 `psi_jt` 字段** ⇒ 后续会话引 U6 热参数时**须并引正本 SNLS683 §6.4**；**禁**改该两件（其 sha16 已被 L2 v1/v2 裁定引用，改即断链） | 本会话自纠 · 正本比对 | **非缺陷判定**（登记级 · 不阻塞）· **禁**静默回改前件/ledger（保留原值，以本件 amend） |
| **CR-23** | **新通道：TI 官方数据表直链（T2-F6 登记）** | `https://www.ti.com/` **200** · `https://www.ti.com/lit/ds/symlink/<part>.pdf` **200 application/pdf**（首测 `ds320pr1601.pdf` 2,225,981 B）—— 此前通道登记**从未包含 ti.com**（只封过 `st.com` 567 / `diodes.com` 部分面）⇒ **纳入可达面**；**待办潜力**：本板 TI 器件族（`DS320PR1601` · `DS160PR810` · `TPD2E001` · `TPS22919` · `TPS22965` · `TPS22990` · `TS3USB221A` 等）之**零件真源**可经此通道补证 | 本会话实测 | 外部厂商原件仅落 `/tmp/opencode`（**未入库**）· 入库仅派生证据（sha256 + 抽取文本 + 小图） |

---
**（本块）裁定对应**：CR-21 ← 正本 SNLS683 §6.4（L2-V7-1′ 自裁更正）· CR-22 ← 自纠/撤回 · CR-23 ← T2-F6 新通道登记。**报备监理 1 条（口径更正）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · TI 通道 tier2 补证（2026-09-21 · 只读造活）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-24** | **TI 正本批量补证：文献号核对（9 件）+ 引脚表逐脚核对（7 件 / 114 脚 / 0 冲突）** | **① 文献号**：逐字一致 6 件（`SLLS684I` · **`SLVSBO7O`** · `SLVSEN5B` · `SLVSBJ0F` · `SLVSDK1C` · **`SCDS277C`**）⇒ **T2-F1 之两处订正（`TPD6E05U06`·`TS3USB221A`）已获厂商正本独立确认**（待批状态 → **有外部锚**）。**② 新引证问题 3 项（登记待批 · 同 T2-F1 族 · 禁 ENG 擅改 `_shared`）**：`TI-CIT-1` `DS320PR1601` 引 **`ZDG0354A`**（实为**封装图号**；真文献号 = **`SNLS683`**，§5 Table 5-1 内容引用本身正确）· `TI-CIT-2` `DS160PR810` 引「`SNLS658` **Rev B**」而正本页眉为 `SNLS658 – DECEMBER 2020`（**无 `B`**）· `TI-CIT-3` `TLV61046A` 引 `SLVSD82` 应为 **`SLVSD82B`**。**③ 引脚表**：`TLV61046A` 6/6 · `TPD2E001` 6/6（含 DRL/DZD 变体登记相符）· `TPS22919` 6/6 · `TPS22965` 8/8+热焊盘 · `TS3USB221A` 10/10 · `TPD6E05U06` 14/14（RVZ Table 4-3）· `DS160PR810` **64/64**（VCC 6/18/38/50 · VREG1 3/47 · VREG2 15/35 · GND EP+9/12/21/24/32/41/44/53/56/64）⇒ **114 脚逐脚一致 · 0 冲突**。**④ 未做**：`DS320PR1601` **354 ball** 未逐脚（列下一步；本轮已核 §6.4 热参 + §6.5 PACT 一致） | 本会话实测 · `T2F6_TI_LANE_TIER2_VERIFICATION_20260921_v1.json`（6accfd86336d103e）· 外部 PDF 仅落 `/tmp/opencode/ti`（未入库） | **只读件**：**未改** `_shared/eda_core/**`（引证订正仅登记待批）· 未改冻结四源/`criteria/`/交付包/受审板 · **未新增判据维/检查齿** · **不充绿**（tier2 读数仍 17/33，本件为**真源勘验**非计数变更） |

---
**（本块）裁定对应**：CR-24 ← T2-F6 新通道（CR-23）利用 · handoff §7-B。**报备监理 1 条（引证订正待批 3 项）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · U6 354 球全量核对（2026-09-21 · 只读造活）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-25** | **`DS320PR1601`（U6）354-ball **全量**逐球核对 = 354/354 一致（独立复算）** | **方法（独立重解析）**：TI 正本 `SNLS683`（sha256 `f61599c4…`，**与 yaml `doc_sha256` / `m13_...inputs.json` `pdf_sha256` 三方同值**）§5 Table 5-1（p6–p14 共 9 页）逐页 `pdftotext -layout` + **行锚定正则**（`re.M`）建 `ball→name`，再与 `DS320PR1601.yaml` **双向**比对。**结果**：PDF 行 **354** · 唯一球 **354** · **重复冲突 0**；对 yaml = **matched 354 / conflict 0 / 未解析 0 / PDF-only 0 / yaml-only 0** ⇒ **U6（板内最复杂器件）之球名真源获厂商正本独立锚**；yaml 自述『ball 集合与符号库 354/354 无缺无重』之 **PDF 侧前提成立**。**登记（待批）**：yaml `doc_url` 记『公开直链未获』而**现已知** `https://www.ti.com/lit/ds/symlink/ds320pr1601.pdf`；`_shared` 件改动属 **T2-F1 族待批** ⇒ **仅登记 · 禁擅改**。**环境教训（+1）**：`pdftotext -layout` 续页缩进不同 ⇒ 行锚定须 `re.M` + `^\s*`（漏 `re.M` 会得 0 行） | 本件 `T2F6_DS320PR1601_BALL_MAP_VERIFICATION_20260921_v1.json`（730e1030611d19b8）· 外部 PDF 仅落 `/tmp/opencode/ti` | **只读**：未改 `_shared/**`（`doc_url` 仅登记待批）· 未改冻结四源/`criteria/`/交付包/受审板 · **未新增判据维/检查齿** · **不充绿**（tier2 仍 17/33） |

---
**（本块）裁定对应**：CR-25 ← T2-F6（CR-23 通道）收口 · handoff §7-B。**报备监理 1 条（`_shared` 引证/`doc_url` 待批）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · 【缺陷 HIGH】U4 BAT54C 电源 ORing 反接（2026-09-21 · 厂商正本核出）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-26** | **【缺陷 · HIGH】`U4` BAT54C 电源 ORing 二极管**物理反接**（根因 = 脚位真源错）** | **事实**：`_shared/eda_core/sch_gate/datasheets/BAT54C.yaml` 记 `1=A1`·**`2=K`**·**`3=A2`**（`source` = 无引证之『标准脚位』）⇒ **两厂商正本一致否证**：**Nexperia BAT54C §5 Table 2** `1=A1 · 2=A2 · **3=K1,K2（共阴）**`（正本 sha16 `38d4cf5982dcaaa3`）· **Diodes `DS11005 Rev 34-2`** 首页拓扑图同为『两阳极下侧两脚 / 共阴上侧单脚』（图证 `63a4c3a22ab1e671`）⇒ **K 与 A2 对调**。**传播链**：① 真源错 ⇒ ② 符号 `IOCONVERT.kicad_sym#BAT54C_ORING`（`K→pin2`·`A2→pin3`）⇒ ③ 受审板 l7 `U4`：**`pad3 → P3V3`**·**`pad2 → MCU_VDD`**·pad1 NC；而 footprint 焊盘坐标 = `pad1 左下(−0.95,+0.95)`·`pad2 右下(+0.95,+0.95)`·`pad3 上中(0,−0.95)`（**JEDEC TO-236 标准编号**）⇒ 实体板上**共阴(pin3)接 `P3V3`**、**阳极2(pin2)接 `MCU_VDD`** ⇒ **仅 `MCU_VDD → P3V3` 可导通，`P3V3 → MCU_VDD` 被截止**。**影响**：按 **CR-11** 主判工况（独立运行 · `J13/VCC` 不接外供）`MCU_VDD` **无供电（≈0V）** ⇒ **V6-1 主判 FAIL · V6-2 FAIL · 板不上电**；仅外供 `J13/J9` 时表面正常 ⇒ 内部比对（板 ↔ **同一错源**）**必然看不见**（与 CR-8 COV-C2 自比盲区同类）。**同类排查（本轮）**：`FRU_EEPROM`(`AT24C02` 标准图) 与板 `E2` **逐脚一致（无缺陷）**· `OPTO_LTV356T` 前轮已 4/4 一致· `2N7002` 本轮 3/3 一致 ⇒ **本轮未再发现第二例**。**处置（须监理批）**：修 `BAT54C.yaml`(`2:A2 / 3:K`) ⇒ 同步修符号 pin 号 ⇒ 重生成网表 ⇒ 交换 `U4` pad2/pad3 网络 ⇒ 重出 Gerber ⇒ **新 rev**；**在处置前不应下首件单**（按 fail-closed『P4 未全绿不下单』—— 本件证明 l7 板**不满足**其设计意图之 ORing 功能）。**是否 owner**：**否**（非拓扑/接口/信号流向架构变更 · 属真源缺陷修复 = **监理批面**） | 本件 `DEFECT_U4_BAT54C_PIN_SWAP_20260921_v1.json`（affa0c5d2c3b7491）+ 两厂商正本 · 外部 PDF 仅落 `/tmp/opencode` | **只读取证**：未改 `_shared`/符号/网表/PCB/交付包 · **未**自裁开 ECO/新 rev · **未**派 WORKER · **禁**在获批前改设计面 |

---
**（本块）裁定对应**：CR-26 ← 厂商正本核对（T2-F6 通道附带产出）。**报备监理 1 条（缺陷 HIGH · 请求处置裁定）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）——但**本件影响 l7 板之功能性**，P5 首件单**建议暂缓**至处置裁定。
### 续编 · D1 LED 极性与全板极性普查（2026-09-21 · 只读造活）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-27** | **【缺陷 · LOW-MED】`D1` LED 符号脚号与所引 footprint 约定不一致（疑反接）+ footprint 副本丢丝印** | **链**：① 项目符号 `k2_sch.yaml#LED` = **`A→pin1`（左）· `K→pin2`（右）**；② 原理图声明 `footprint: LED_SMD:LED_0603_1608Metric`，而**本机 KiCad 官方件**（`AppDir/share/kicad/footprints/LED_SMD.pretty/LED_0603_1608Metric.kicad_mod`）焊盘 `1=左(x−0.7875)`/`2=右(+0.7875)`、**丝印阴极标记（竖条+三角尖）在左**（渲染图证 `93aa22594349b8c7`）⇒ **pad1 = K**；③ 板上 `D1`（fp `ForgeOS:LED_0603_1608Metric`，同布局副本）**pad1 → `LED_A`** · pad2 → `GND` ⇒ **阴极落 `LED_A`、阳极落 `GND` ⇒ 反偏 ⇒ 指示 LED 不亮**；④ **同库反例**：项目 `D_SCHOTTKY` = `K→pin1` 与 `Diode_SMD:D_SMA`（pad1=K）**相符** ⇒ `D2/SS34` **正确**。**附**：`ForgeOS` 副本**丢失全部丝印** ⇒ 无极性标记（贴装不可辨）。**置信**：高（footprint 侧实证）但**本机未装 KiCad 符号库**、GitLab 符号库直链 404 ⇒ 符号侧系推得 ⇒ **并入 CR-26 批次由监理确认** | 本件 `DEFECT_D1_LED_POLARITY_AND_POLARITY_CENSUS_20260921_v1.json`（8d214f3ace25beec）· 图证 `93aa22594349b8c7` | **只读取证**（未改符号/footprint/PCB/交付包）· **不改**（Gerber 不因 LED 需改）· **禁**未批擅改 |
| **CR-28** | **全板极性/方向敏感件普查（l7）** | 逐件核 (a) 符号 pin 号 ↔ (b) footprint 物理焊盘 ↔ (c) 项目符号定义 ↔ (d) 官方 KiCad 约定：**`U4` BAT54C ✗（CR-26 HIGH）** · **`D1` LED ✗（CR-27 LOW-MED）** · `D2` SS34 ✅ · `U5` OPTO_LTV356T ✅（Lite-On 正本 4/4）· `E2` FRU_EEPROM ✅（AT24C02 逐脚）· `U2` DCDC ✅（TI 6/6）· `U1` STM32G0B1CBT6 ✅ · `U6` DS320PR1601 ✅（TI 354/354）⇒ **除 U4/D1 外无第三例**；**普查覆盖全部极性敏感件**（二极管 ×3 · 光耦 · 电源器件 · 主芯片） | 同上件 §polarity_census_l7 | 登记制 · **不充绿** · 禁重复普查同类件 |

---
**（本块）裁定对应**：CR-27/CR-28 ← handoff §7-B（只读造活）+ 厂商正本补证附带产出。**报备监理 1 条（并入 CR-26 处置批次）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · U2 双重性质澄清（2026-09-21 · **先查册命中 ⇒ 不重复上报**）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-29** | **`U2`（`DCDC_12V_3V3`）两个维度须分开读：真源 pin 表 ✅ ／ land pattern = 既有 P4 登记（owner 闸边界）** | **本轮查册结果（命中既有登记 ⇒ 不作新发现上报）**：本会话 `CR-28` 写「`U2` DCDC ✅（TI 6/6）」仅指**真源 pin 表**（TI `SLVSD82B` 6 脚逐脚一致）；`U2` 之**封装指派 / land pattern** 另有**既有登记**：`K2-P2-E2-directed-pad-registry-v1.md`（符号 6 脚 vs 板 8 pad ⇒ 余量 2 = `7,8`，记『结构性余量，登记即闭』· **该件只谈 pin 数口径**）与 `K2-P4-W8-J7-TRIGGER-ISOLATION-v1.md` §7 / `K2-P4-CONVERGENCE-STATUS-v1.md` §六（板 land `0.6×0.9 @x∓1.95` 行距 **3.9mm** vs 上游 `1.625×0.65 @x∓3.5875` 行距 7.175mm；**焊盘 x 域 [1.65,2.25] 全落在 5.3mm 体宽内 ⇒ 与鸥翼引脚落点无交集 ⇒『按所冠包名不可焊』**；并同表登记 29 件上游名件之板 land 系统性小于 IPC（0603 趾外伸 −0.05mm 等））。**裁定（登记制 · 澄清）**：二者为**不同维度**（pin 数口径 ≠ land 几何），**勿混读**；`U2` land/封装指派**处置边界已由 P4 明列**：① 判据侧若改判『容忍 pad 级差异』⇒ **判据维度/阈值变更**；② 源侧若按库重落 land pattern/改生成器 ⇒ **须改生成器** ⇒ 二者均**非 ENG 自裁面**。**ENG 本轮只读复核命中既有登记 ⇒ 不重复上报、不擅动** | 既有件：`K2-P2-E2-directed-pad-registry-v1.md` · `K2-P4-W8-J7-TRIGGER-ISOLATION-v1.md` §7 · `K2-P4-CONVERGENCE-STATUS-v1.md` §六 · 本会话 `CR-28` | **禁**重复上报（`K2-REG-1` ≈ `K1-GAP G-5` 已判重复）；**禁**擅动 land/生成器/判据；**本件不改任何文件**（仅口径澄清） |

---
**（本块）裁定对应**：CR-29 ← 本会话『先查册』命中既有登记后之**澄清登记**。**报备监理 1 条（维度澄清）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · U1 真源核验（MCU · 2026-09-21 · 只读造活）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-30** | **`U1`（`STM32G0B1CBT6`，LQFP48）真源 **48/48 逐脚一致**（厂商正本 · 新通道取得）＋ 引证待核** | **新通道**：`https://pdf.elecfans.com/STMicroelectronics/STM32G0B1CBT6.html`（200）⇒ 直链 `https://file1.huaqiu.com/web2/M00/00/43/wKgZomatSW-AHL42ACgp7LGnHP8064.pdf` ⇒ 取得 **ST DS13560 Rev 1（Nov 2020）· 159 页**，`sha256 = 9fc2cfec9a1c8d5c8a281df64ee03d1769949de32ae629ff707a709e5d406924` = **与本项目 KBU6 核验所引件逐字节同值**。**核验**：`DS13560 Rev 1` **Figure 9 `STM32G0B1CxT LQFP48 pinout`（p42 · GP version `_RxT`）** 逐脚比对 `_shared/eda_core/sch_gate/datasheets/STM32G0B1CBT6.yaml` ⇒ **48/48 一致 · 0 冲突**（左列 1–12 · 下排 13–24 · 右列 25–36 · 上排 **48=PB9 … 37=PA15**）。**引证待核**：yaml 记「**DS13560 Rev 6 — Table 12 (Figure 5)**」，而 Rev 1 对应为「**Figure 9**（p42）· Table 12 非 pinout 表」⇒ 若 Rev 6 重编号则 yaml 无误，否则须订正（**同 TI-CIT 族 · `_shared` 件 ⇒ 登记待批 · 禁 ENG 擅改**）。**注**：`U1` 之 **land/脚数冲突**（板 33 pad vs 符号 LQFP48 编号）属**既有 P4 登记**（`K2-P2-E2-directed-pad-registry` v1.1「板侧缺陷 2-A″」）⇒ 本件**只核真源表**，**不触及**该登记（CR-29 同旨） | 本件实测 · 正本 sha 与项目件**逐字节同** · 外部 PDF 仅落 `/tmp/opencode/ven`（未入库） | **只读**（未改 `_shared`/符号/网表/PCB/交付包）· 引证项**登记待批** · **禁**以本件覆盖既有 land 登记 |
| — | **（附）板内器件真源核验收口** | 本会话至此：`U1` ✅48/48 · `U6` ✅354/354 · `U2` 真源 ✅6/6（land 属 P4 既有登记）· `U5` ✅4/4 · `E2` ✅8/8 · `D2` ✅ · `U4` ✗（CR-26 HIGH）· `D1` ✗（CR-27 LOW-MED）· `J2/J3/J4` 规格类（P2-E2 登记）· `J6/J9/J11/J12/J13` 设计定义件 ⇒ **板内器件真源核验面已尽**（除已登记且涉 owner 闸之 land 议题） | 本会话各件 | 登记制 · 不充绿 |

---
**（本块）裁定对应**：CR-30 ← handoff §7-B（只读造活 · 真源核验收口）。**报备监理 1 条（引证待核）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · E2/AT24C02 真源独立厂商复核（2026-09-21 · **关 CR-26 同类残余自比盲区**）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-31** | **`E2`（`FRU_EEPROM` · AT24C02 类）真源 **8/8 厂商正本一致** —— 为 `CR-26` 暴露之『**无引证标准脚位 + 板↔真源自比**』盲区补**独立**核（**非新增检查齿**）** | **缘起**：`CR-26`（`U4` BAT54C）证明『**板 ↔ 同一错源** 比对必然看不见错源』（同 `CR-8` COV-C2）；而 `FRU_EEPROM.yaml` 之 `source` = **无引证**之『AT24C02 类标准脚位』，其此前核法**仅板↔真源自比**（`CR-28` 记 ✅）⇒ **残一自比盲区**。**独立核**：新通道 **`ww1.microchip.com`**（首次登记 · 200）⇒ `downloads/en/DeviceDoc/doc0180.pdf` = **Atmel/Microchip AT24C01A/02/04/08A/16A**（`0180Z1–SEEPR–5/07` · 20 页 · `sha256 a084aa10aada64d7ea1b7717705e9d5c01f19028cad805724a14ee6552a432ca`）· **Table 1 Pin Configuration · 8-lead SOIC** = `1=A0 · 2=A1 · 3=A2 · 4=GND · 5=SDA · 6=SCL · 7=WP · 8=VCC`。**全链逐层核**：① `FRU_EEPROM.yaml` 真源 **8/8 一致**；② 符号 `IOCONVERT.kicad_sym#FRU_EEPROM` pin 号（1/A0·2/A1·3/A2·7/WP·6/SCL·5/SDA·4/VSS·8/VCC）**8/8 一致**；③ `ForgeOS.pretty/SOIC8_FRU.kicad_mod` 焊盘几何（pad1 左上…pad4 左下…pad5 右下…pad8 右上 = **JEDEC SOIC 逆时针**）与厂商图同构；④ 板 l7 `E2` pad→net `1=GND 2=MCU_VDD 3=GND 4=GND 5=I2C1_SDA 6=I2C1_SCL 7=GND 8=MCU_VDD` **逐脚自洽**。**附带增益**：`A0=0/A1=1/A2=0 ⇒ 7-bit 地址 `0x52``，**为 `CR-18`/`V6-3` 预期地址提供独立厂商依据**（地址脚接 GND/VCC 为厂商允许；`WP=GND ⇒ 正常读/写`，符合正本 p1 语义）⇒ **`E2` 无缺陷 · 非第二例 BAT54C** | 本件实测 · `T2F6_AT24C02_FRU_EEPROM_VERIFICATION_20260921_v1.json`（`a7499c6b9e8284ca`）· 外部 PDF 仅落 `/tmp/opencode`（**未入库**） | **只读**（未改 `_shared`/符号/网表/PCB/交付包）· **禁**以本件覆盖既有 `U1` land 登记（`CR-29` 同旨）· **非**新增判据维/阈值/检查齿 |
| — | **（附）同类残余枚举 ⇒ 自比盲区清零** | 按 `symbol:` 清单枚举 l7 **实际实例化**之厂商脚位类器件：`U1`/`U2`/`U6`（ST/TI 正本已核）· `U4` ✗`CR-26` · `U5`（Lite-On 正本 · `CR-6`）· **`E2` ✅ 本件** · `D1` ✗`CR-27` · `D2`（KiCad 官方 footprint 约定）⇒ **除 `U4`/`D1` 外无第三例，且唯一残余自比件（`E2`）已补齐独立核**。`24MHz_9pF`/`LED_DUAL`/`USB_C_RECEPT`/`USB3.0_Type-A_90`（同为『无引证』件）经核对 = **本板未实例化**（库内定义；`USB_C_RECEPT` 属 KEY 卡/另板）⇒ 不在本板核验面（**登记制 · 不充绿**） | 本件 · `symbol:` 清单（l7 设计源） | 登记制 · 不充绿 · **禁**重复普查同类件 |

---
**（本块）裁定对应**：CR-31 ← handoff §8-B（只读造活 · 关 `CR-26` 同类残余）。**报备监理 1 条（同类收口）· owner 项 0**。
**不影响** P6 判据面（`criteria/` rev=6 只读）与交付锚（`6ee7495de61f749f` 未动）。
### 续编 · #K2-57 裁定落地（CR-26 修复执行 + CR-27 并入 + 引证 5 项 + 过程口径 CR-32）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-26**（**状态更新：已裁 → 已落**） | **`U4` BAT54C 电源 ORing 反接 · 根因链已订正并复算** | **裁定**：监理 **#K2-57**（自裁 · §11）批准 ① 真源订正 ② 开新 rev。**已落**：① `_shared` 四树 `BAT54C.yaml` = `1:A1 · 2:A2 · 3:K`（旧 `2:K/3:A2` 系无引证『标准脚位』）· `source` 改引 Nexperia §5 Table 2 + Diodes DS11005 Rev 34-2；② 生成器实际消费之 pin 映射经 **`hw/data/k2_sch.errata-3.yaml`**（版本 bump；`k2_sch.yaml` **逐字节未改** = `dd794c54f7ce7417`）订正 `K→3 · A2→2`；③ 符号层 `IOCONVERT.kicad_sym#BAT54C_ORING`（及内嵌该符号之 sch）同订正。**复算（gates ③）**：`k2_gen_v5` 于 errata-2 = `U4 pad2→MCU_VDD / pad3→P3V3`（**复现缺陷**）；于 errata-3 = **`pad2→P3V3` · `pad3→MCU_VDD`** ⇒ 实体 `A2→P3V3` / `K→MCU_VDD` ⇒ **`P3V3→MCU_VDD` 正向导通** ✅ | 监理 #K2-57 R1/R2/R3；件 `DEFECT_U4_BAT54C_PIN_SWAP_20260921_v1.json`（affa0c5d2c3b7491） + 两厂商正本 | **未改** `k2_sch.yaml`/冻结四源/`criteria/` · 未改交付包旧锚 · 修复件走 **新 rev** |
| **CR-27**（**并入同批 · 已落**） | **`D1` LED 极性（LOW-MED）· 符号 pin 号对齐 footprint** | **ENG 独立复核**（R4 前置）：本机官方 `LED_SMD:LED_0603_1608Metric` pad1 在 **x=−0.7875（左）**，丝印阴极竖条在 **x=−1.485（左）** ⇒ **pad1=K**（阴极）⇒ 板用 footprint（`ForgeOS` 副本，同左/右序，**无丝印**）pad1=K。**意图**（nets）= `LED_A: [R21/B, D1/A]` · `GND ∋ D1/K` ⇒ 需 `A→pad2 · K→pad1`。**已落**：符号 pin 号 `A→2 · K→1`（`IOCONVERT.kicad_sym#LED` + `mcu_sideband.kicad_sch` 内嵌件 + errata-3）。**复算**：`D1 pad1→GND · pad2→LED_A`（正向）✅ | 监理 #K2-57 R4；本机官方 footprint 丝印实证 | 意图未变 · 不新增判据维 |
| **CR-32**（**本裁立 · 过程口径**） | **「待裁信号真空」——新待裁项一经发现即须结构化，禁只写 handoff/ledger** | **事实**：CR-26 于 23:19 发现，但**只**记于 `ledger.jsonl` + handoff §4，**未**落 `PENDING_RULINGS_DELTA_*.json` ⇒ 哨兵 `pending_rulings_blocked()` 恒 **False** ⇒ **900s 自动拉起监理之梯子永不触发**（= 2026-09-20『无信号⇒不拉起监理』事故同型）。**口径（#K2-57 R6）**：待裁项**一经发现即结构化**入 `k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/PENDING_RULINGS_DELTA_*.json`。**已按此纠正**：本会话落 **v23**（`833d419e4b9464ae`）⇒ 23:32:06 > 22:51:35+300s ⇒ 阻塞信号生效 ⇒ 监理 925s 拉起并出 #K2-57 | 监理 #K2-57 R6；`watch.py:191/203` · `sup.py status` | **非判据维 · 非检查齿**（属 §12 自动化优先之过程口径） |
| **CR-33**（**口径澄清 · 非齿**） | **脚位真源之「有效杠杆层」——生成器消费 **netlist pin map**，非 `.kicad_sym`** | **事实（本会话实证）**：`k2/tools/k2_gen_v5.py::parse_yaml→build_device_table` 之 `pin_map` 取自 **nets_yaml（`spec["symbols"][*].pins`）**（`assign_nets` 以 `REF/PINNAME` 经该表解析 pad 号）⇒ **PCB/Gerber 侧的有效杠杆 = 网表 pin 映射**；`hw/lib/IOCONVERT.kicad_sym` 为 `k2_sch_gen_v1.py` **再生件**（且现行件含后置补丁，与从头再生**不逐字节同**）。**故**：订正 `.kicad_sym`（R2 字面目标）**单靠自身不改板**；须同订正网表 pin 映射（本会话经 errata-3）。**登记目的**：供后续会话**先查册**，避免「改了符号却没改板」之假绿 | 本会话实证（`k2_gen_v5.py` 代码 + errata-2/errata-3 双跑对照） | **非判据维 · 非检查齿**；**禁**以符号层订正宣称板已修（须以网表 pin 映射 + 板 pad→net 机核为证） |

---
**（本块）裁定对应**：#K2-57（R1/R2/R3/R4/R6）。**报备监理 1 条（有效杠杆层口径）· owner 项 0**。
**不影响** 旧交付锚（`6ee7495de61f749f` / `0e88e107e2da8192` 未动）与 `criteria/`（rev=6 只读）。
**待续（R3 后半 + ⑥）**：`k2_route_segment_v1 --upto all` → 新 rev 板 → 重跑 P4 锚/19 维 → 新交付包。
### 续编 · 新 rev `l8` 生成（#K2-57 R3 后半 · 载体）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-34** | **新 rev `l8` 生成完成（CR-26/CR-27 修复载体）· 19 维重锚与交付包重出待续** | **链**：`k2_gen_v5.py`（`bc5dbda2`，与 l7 链同版）→ `k2_route_segment_v1.py --upto all`（`f28a4b5a`，同版）；输入 = `hw/data/k2_sch.errata-3.yaml`（`5dc7b82a901d11c8`）。**保真对照**：同链于**未订正** nets（errata-2）跑 → out = **`c5a7df90aadb66e0` = 在岗 l7 逐字节同** ⇒ 链可确定复现 l7，新 rev 差异**可完全归因输入变更**。**产物**：`k2/hw/k2_v4_8L.l8.kicad_pcb` **`7a5c89913d6e5d0a`** · `…l8.kicad_pro` `c009058005829f09`。**差异（唯一 4 条，672 pad/58 fp 全同）**：`U4/2 MCU_VDD→P3V3` · `U4/3 P3V3→MCU_VDD` · `D1/1 LED_A→GND` · `D1/2 GND→LED_A` ⇒ U4 `P3V3→MCU_VDD` **正向导通** ✅、D1 **正向** ✅。**DRC（初步）**：`error 0` · `unconnected 0` · `schematic_parity 0` · 违规 204 **全 warning**、**类集合与 l7 登记 9 类一致**（±局部重布致 `via_dangling 4→6` · `track_not_centered_on_via 33→34`；`lib_footprint_issues 54` 系本件未套判据侧 severity/exclusion 配置，l7 册为 `lib_footprint_mismatch 20`）⇒ **正式读数须由判据侧标准调用复核**。**未做**：canonical 19 对 l8 重锚 · 交付包重出（旧锚 `6ee7495de61f749f`/`0e88e107e2da8192` 仍为 l7 件、未动） | 监理 #K2-57 R3；本件 `REV_L8_GENERATION_EVIDENCE_20260921_v1.json`（现行 `ff23e7774dca74f5`） | **只增新 rev 件**·**未改** l7/旧包/冻结四源/`criteria` · **STOP-1 维持**：l8 经监理复核前**不下首件单** |

---
**（本块）裁定对应**：#K2-57 R3（后半·载体）。**报备监理 1 条（新 rev 待复核）· owner 项 0**。
**待续**：canonical 19 重锚 → 交付包重出（判据 ⑥ 新锚）。

> **【CR-34 补充 · 2026-09-21 本会话】**：l8 板件**落库被门禁拒**（`check_pcb_spec_correlation`：含 `.kicad_pcb` 变更须同含 SPEC 变更，防直改板绕过 pipeline）。**处置（守门，未绕）**：l8 板 **held 于 `/tmp/opencode/rev8/held/`**（`7a5c89913d6e5d0a` / pro `c009058005829f09`），**未入库**；本会话只落证据件 `REV_L8_GENERATION_EVIDENCE_20260921_v1.json`（**`ff23e7774dca74f5`** = 含 `landing_gate` 节之现行件；初版 `4087a07a69fdf8c5` 已被本补充更新）。
> **l8 落库之正确路径 = 方案先行**：先立新 **SPEC rev** 件（`SPEC_k2_v4.spec-rev-53.json` 或等价 · 版本 bump 新文件）→ 再随批落 l8 板 + 重建交付包。**是否需实质改 SPEC**（本次为**网表引脚映射**变更、几何未变）属**监理/判据侧口径**，ENG 不擅定。

> **【CR-34 补充 2 · 本会话】**：**l8 已落库** —— `SPEC_k2_v4.spec-rev-53.json`（`4e92b3a05cd5a223`，仅 3 处 `board_sha16` 声明 + 卡；旧 rev 逐字节不改）+ `pm_gate/project.yaml::spec_name` → rev-53 + `hw/k2_v4_8L.l8.kicad_pcb`（`7a5c89913d6e5d0a`）/ pro（`c009058005829f09`）同批 ⇒ **PCB↔SPEC 门禁已满足**（方案先行范式）。仍待：canonical 19 重锚 + 交付包重出。

### 续编 · 新 rev `l8` 之 **P4 重锚**（canonical 19 · #K2-57 R3）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-35** | **`l8` 通过 canonical 19 标准调用：`19 OK / 0 FAIL`（判据 rev=6 在岗）—— P4 锚在 CR-26/CR-27 修复后**不回退**** | **标准调用**（`criteria/adjudicate.py` · `--drc-work-dir` 全新 · 6 件测量输入为本会话实测）：**PASS · n_pass 19 · n_fail 0 · provisional=False**。关键读数：`zone_filled 10/10` · `non45 0/5180` · `drc error 0`（违规 170 全 warning）· `unconnected 0` · `未登记 warning 类型 0/9` · `电气级差异 0`（B 口径豁免 2）· `出框 0`（676 pad）· `non_antipad_gap 0.0 mm²` · 密度峰值 7（≤8）· 最小铜间距 0.10（≥0.10）· 横带 0.07586 · pad 到边 0.38。**与 l7 册逐项同**（l7 = 19/0）⇒ **无回退**。**测量册**：新建 `L4/E3-standard-call-l8-20260921/`（`MANIFEST.md a6faf8374918fef0` + 8 件；fail-closed 自检：12 处 `board_sha16` 全 = 受审板 `7a5c89913d6e5d0a`，**BAD 0**）。**仪器口径**：W-8/pads/v3-plane/min-clearance 四器 sha16 与 l7 册所用**逐位相同**；**`measure_density_and_clearance.py` 已漂移**（l7 册 `dccaaa476c807def` → 今 `ff763e6865bac843`）⇒ 已登记，读数同号（0.07586 / 0.38）**无回退** | 监理 #K2-57 R3；本会话标准调用实测；册 `L4/E3-standard-call-l8-20260921/` | **只增册**·**未改** l7 册/旧交付包/冻结四源/`criteria`（rev=6 只读）· 仪器漂移**登记不掩盖** |
| — | **（附）P4 门态（l8）** | **P4 全绿（19/0）** ⇒ 按 `#K2-57` R3「重跑 P4 锚」**已完成**；**P5 仍 `PENDING_EXTERNAL`**（外部首件回件未到）；P6 CLOSED ⇒ **未越阶段**。**待续**：交付包对新 rev 重出（判据 ⑥ 新锚）。 | 本册 | 登记制 · 不充绿 · **STOP-1 维持**（l8 经监理复核前不下首件单） |

---
**（本块）裁定对应**：#K2-57 R3（P4 重锚）。**报备监理 1 条**（仪器漂移登记）· **owner 项 0**。

### 续编 · 新 rev `l8` 交付包重出（#K2-57 R3 · 判据 ⑥）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-36** | **`l8` 交付包已重出（判据 ⑥ 新锚）—— 8 叠层 Gerber/钻孔/叠层图/阻抗表/裁定副本/披露/MANIFEST 齐** | **新工具**（**新增**，非改既有）：`tools/k2_p5_jlc_package_l8_v1.py`（`7f1cb9e9b91a7ba6`，由 l7 版**机械派生**：BOARD/PRO→l8 · SPEC→rev-53 · 册→`E3-standard-call-l8-20260921` · **OUT→`L6/jlc_package_l8`** · **DELIVERY→`L6/DELIVERY_l8`** · 交付记录→`docs/K2-P5-DELIVERY-RECORD-l8-v1.md`；**冻结锚 `L6/jlc_package` / `L6/DELIVERY` / l7 记录 一律未触碰**）。**产物**：`L6/jlc_package_l8/` **`MANIFEST.json` = `427a42534af002b4`**（53 件 + MANIFEST · `board_sha16 7a5c89913d6e5d0a` · `pro_sha16 c009058005829f09` · `criteria_anchor rev=6` · drill 754）；`L6/DELIVERY_l8/k2_v4_8L.l8_gerber_package.tar.gz` **`f8f143c96ffef9e2`**（422,798 B · 固定 mtime/uid/gid）。**DFM 对 JLC HDI 通道：16 PASS / 1 ACCEPT / 0 FAIL**（N-01 平面层 4/4 `G36>0` · In4 9 区）。**确定性**：**4 连跑 MANIFEST 逐字节同**（`427a42534af002b4`）。**唯一 ACCEPT = 阻焊桥/阻焊-铜净距**（`JLC 限 DRC solder_mask_bridge = 9`），**承自 l7 之既有已裁项且有证明**（`07_verify/mask_accept_fix_proof.json`）—— 其根治（ECO-1 `pad_to_mask_clearance 0.05→0.02`）**不在本 rev 授权范围** ⇒ 维持 ACCEPT、**非新引入**。 | 监理 #K2-57 R3（判据 ⑥）；本件实测 | **旧交付锚 `6ee7495de61f749f` / `0e88e107e2da8192` / l7 记录 `73fca3aaa360a179` 逐字节未动** · **禁**以 l8 包覆盖冻结包 · **STOP-1 维持**（监理复核前不下首件单） |

---
**（本块）裁定对应**：#K2-57 R3 判据 ⑥（新交付包）。**报备监理 1 条（新 rev 包待复核）· owner 项 0**。
**至此 #K2-57 §四判据 ①②③④⑤⑥⑦ 全达成**（⑧ 见 COV-C3 跨项目批）。

> **【CR-36 补充 · 2026-09-21】**：**交付包自洽性核验发现并订正一处数字失真** —— 派生构建器自 l7 版继承了**具名披露的 DRC 数字（167 + 类型表）**，而 l8 之在册 canonical DRC = **170**（`track_not_centered_on_via 33→34` · `via_dangling 4→6`）⇒ 已按 l8 实测订正 `DISCLOSURE.md`/`ORDER_NOTES.md`，并**如实加入 l8 vs l7 差异注**（+3 归因 = 4 条 pad→net 变更致相关网局部重布、+5 过孔/+143 段；**error 0 · unconnected 0 · 类型集不变**）。**新锚**：`MANIFEST.json` `4b610baed4f4752c`（原 `427a42534af002b4` 作废）；`DELIVERY_l8` tarball 同步更新。**旧交付锚仍逐字节未动**（`6ee7495de61f749f` / `0e88e107e2da8192` / l7 记录 `73fca3aaa360a179`）。

### 续编 · 脚位真源**缺陷类**收口（CR-26 族 · 以官方 PIN-01 双路校验）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-37** | **`CR-26` 缺陷类**在 **Gerber 驱动层**收口：网表 pin 映射 ↔ 真源表 **零实质分歧**（官方 PIN-01 双路校验）** | **缘起**：CR-26 根因 = 脚位真值**两层各存一份**（`_shared` sch_gate 真源表 ↔ `k2_gen_v5` 实际消费之**网表 pin 映射**）；分歧即同类潜在缺陷，且**单层自洽看不见**。**方法**：以**项目自带官方校验器** `_shared/eda_core/sch_gate/checks/pinmap.py`（规则 **PIN-01**，含 `aliases` 语义 + 无源豁免）校验三路：**A** `hw/lib/IOCONVERT.kicad_sym` · **B** `hw/lib/DS320PR1601.kicad_sym` · **C** 由 `errata-3` **已实例化** symbols 合成之 lib（= 生成器消费层）。**结果**：A = **FAIL 194 / warn 17**，194 **全为 `DS320PR1601`**（= `CR-3` 既有登记，数目逐字同）· 17 为无源 ≤2 脚豁免通告；B = **PASS 0/0**；**C 与 A 逐项同**（194 全 DS320PR1601 + 17 豁免）⇒ **网表层 ≡ 符号层 ≡ 真源表**。**关键器件全 PASS**：`BAT54C_ORING`(K→3/A2→2) · `LED`(A→2/K→1) · `FRU_EEPROM` · `OPTO_LTV356T` · `MCU_STM32G0_C2`(U1) · `DCDC_12V_3V3` · `MCIO_4i` · `SlimSAS_x8` 等 ⇒ **新发现 = 0** | 本件 `PINMAP_CLASS_CLOSURE_AUDIT_l8_20260921_v1.json`（`52321bcabecfaf83`）· 官方校验器 PIN-01 | **只读**·**复用既有校验器**（**非新增判据维/检查齿**）· DS320PR1601 194 项属 `CR-3` 登记 ⇒ **不充绿 · 不重复上报** |
| — | **（附）层间比对之必要性（承 CR-33）** | **两层一致性非必然**：A/B = 符号库层，C = 网表层；CR-33 已证生成器**只**消费 C ⇒ 须**层间比对**方能防『改了符号却没改板』之假绿。本件即该比对的**机械化实现**（可复现、零单板特判） | 本件 · CR-33 | 登记制 · 不充绿 |

---
**（本块）裁定对应**：CR-37 ← CR-26 缺陷类收口（ENG 只读造活）。**报备监理 1 条（类别收口）· owner 项 0**。

### 续编 · P5 首件外发包 **rev 对齐（l7 → l8）**（当前阶段 · 外发面就绪）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-38** | **P5 首件外发包与投递说明已对齐至现行 rev `l8`**（原全套为 **l7** 引用 ⇒ 外发前必然错配） | **缘起**：`#K2-57` 开新 rev `l8` 后，`L6/first_article/`（RULES/CHECKLIST/results_template/INSTRUMENT_SELFCHECK）与 `K2-P5-FIRST-ARTICLE-TRANSMITTAL-v1.md` **仍全套指 l7**（`board c5a7df90` · 锚 `6ee7495d`/`0e88e107`）⇒ 外部实测方将拿 **l8 实物对 l7 文档**。**处置（新目录/新文件名，l7 件**逐字节保留**）**：新建 `L6/first_article_l8/`（`RULES.md 00fc0f19fbaddf2e` · `CHECKLIST.md b97ac43fc0f99c31` · `results_template.json c7c8be4ecd5cd691` · `INSTRUMENT_SELFCHECK.json 432125b50d6f5590`）+ `docs/K2-P5-FIRST-ARTICLE-TRANSMITTAL-l8-v1.md`（`fa17aa92bf06a706`）；board→`l8 7a5c89913d6e5d0a` · 交付锚→`4b610baed4f4752c`/`36a6b276b4f7e465` · 路径→`jlc_package_l8`/`DELIVERY_l8`。**测点自查按 l8 板重跑（机核）**：16 网全在 ✅ `all_nets_present` · 引用件全在 ✅ `refdes_all_present` · `J13` SWD 网 ✅ · `J2` PCIe 网 ✅。**V5 具名测点正向对照（本件独立机核）**：**`J3 A9 → P3V3_AUX` · `J4 A9 → P3V3_AUX`** ⇒ 外发包之强制具名测点在 l8 上**真实存在**。**阈值/测点零变更**：l8 与 l7 **几何相同**，仅 `U4/2,3`（`A2→P3V3`/`K→MCU_VDD`）与 `D1/1,2` 之 pad→net 不同 ⇒ 8 项验收阈值、V6-1 主判工况（独立运行 · 标称 3.0V）、V6-3 地址 `0x52` **全部照旧适用** | 监理 #K2-57 R3/R7；本件机核 | **只增新件**·**未改** l7 版 `first_article/` 与 `…TRANSMITTAL-v1.md`（逐字节保留）· **未覆盖**任何交付锚 · **STOP-1 维持**（监理复核 l8 前**不下首件单**） |

---
**（本块）裁定对应**：CR-38 ← 当前阶段外发面 rev 对齐。**报备监理 1 条（外发包 l8 就绪待复核）· owner 项 0**。

> **【CR-38 补充 · 2026-09-21】**：**l8 交付包结构与完整性实测复核（判据⑥ 收口）** —— ① `sha256sum -c DELIVERY_l8/SHA256SUMS.txt`（自 `L6/` 运行）= **55/55 OK · rc=0**（l7 对照亦 55/55 OK ⇒ **冻结锚未受扰**）；② **结构奇偶校验**（文件名 `.l7`/`.l8` 归一后）：l7 包 54 件 ↔ l8 包 54 件，**各子目录计数逐项同**（`01_gerber_rs274x 14` · `02_drill_excellon 15` · `03_stackup 2` · `04_impedance 2` · `06_rulings 8` · `07_verify 9` · 顶层 4），**唯一差异 = DFM 卡文件名 `jlc_dfm_hdi_l7.*`→`jlc_dfm_hdi_l8.*`（预期）** ⇒ 派生构建器**无漏件/多件**；③ **阻抗 as-built 对照**：l8 之耦合主 run 采样与 l7 **逐项同**（`F.Cu|0.205` 113 段 · `In2.Cu|0.16` 26 · `In5.Cu|0.16` 325）⇒ 本次修复（`U4`/`D1` 局部网）**未触及高速耦合几何**，V4 就绪度不变。

### 续编 · 只读取证件**标签失真**订正（CR-39）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-39** | **`REV_L8_GENERATION_EVIDENCE` 之 `output.sha16` 标签失真（误填 **pro** 哈希）—— 已拆为 `board_sha16` / `pro_sha16`** | **缘起**（本会话**锚周期复核**）：该件 `output` 块仅一键 `"sha16": "c009058005829f09"`，而 **`c009058005829f09` = `k2_v4_8L.l8.kicad_pro` 之 sha16**；同块 `board` 字段所指 `k2/hw/k2_v4_8L.l8.kicad_pcb` 之 sha16 真值 = **`7a5c89913d6e5d0a`** ⇒ **标签指向错误对象**（数值皆为真值，唯标签错位）。**同类扫描（限定范围）**：全 `artifacts/k2_v4` 提及 `c0090580` 者共 **5** 件（`L6/jlc_package_l8/MANIFEST.json` · `…/DISCLOSURE.md` · `…/07_verify/anchor_selfcheck.json` · `L4/E3-standard-call-l8-20260921/MANIFEST.md` · 本件）—— **唯本件误置**，其余 4 件均正确标注为 **pro** ⇒ **孤立缺陷 · 非系统性**（不充绿）。**处置**：拆为显式 `board_sha16 7a5c89913d6e5d0a` + `pro_sha16 c009058005829f09` + 自述键 `label_fix_CR39`；**未改任何读数/结论**（仅修标签）。**新锚** `122e0021dc7745e3`（原 `8f990c357a08abe3`）。 | 本会话锚周期复核实测 · `k2_v4_8L.l8.kicad_pro` 实测 sha16 | **只改本件标签** · 未改板/判据/交付包/冻结四源 · 登记制（**不充绿 · 不重复上报**） |

---
**（本块）裁定对应**：CR-39 ← 只读取证件标签失真订正（ENG 只读造活）。**报备监理 1 条 · owner 项 0**。

### 续编 · 交付里程碑 TAG（TAG_POLICY §1 · 进程合规）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-40** | **`l8` 交付里程碑已打 annotated tag `k2-v57-l8-l6-delivery-anchored`** | **事件**：`#K2-57` R3 开新 rev `l8` ⇒ 判据 ⑥ 交付包重出（`L6/jlc_package_l8/MANIFEST.json` **`4b610baed4f4752c`** · tarball **`36a6b276b4f7e465`**）⇒ 属 `TAG_POLICY` §1「发布候选 / 交付」**必打**事件（承接 `CR-14` 断档口径后**首次按事件打标**）。**tag message（§3 必含项）**：`gate` 判定（P0–P4 **HOLDS** · P4 对 `l8` **19/0** · P5 `PENDING_EXTERNAL` · P6 **CLOSED** · **未越阶段** · **`STOP-1` 维持**：监理复核前不下首件单）· 受审板 **`7a5c89913d6e5d0a`** · 配套 pro `c009058005829f09` · SPEC rev-53 **`4e92b3a05cd5a223`** · 交付锚 **`4b610baed4f4752c`** · 判据 **rev=6** · 复现命令。**核验（§4/§5）**：`push origin main` + `push origin --tags` ⇒ `rev-list --left-right --count origin/main...HEAD` = **`0 0`**；`ls-remote --tags` **`^{}` 解引用**指向目标 commit；tag 后 HEAD 距 tag < `TAG_STALE_COMMITS(20)` ⇒ 哨兵 tag 断档告警**复位**。**登记**：`.omo/start-work/ledger.jsonl` 同轮记 tag 名 + 目标 commit + gate（§6）。 | `k2/pm_gate/TAG_POLICY.md` §1/§2/§3/§4/§5/§6 · 监理 **#K2-56**（自裁 · 进程合规 · **不推回 owner**） | **禁**为历史 commit 批量补打（**禁伪造里程碑**）· 禁 amend/rebase **已发布** 段 · 未改冻结四源 / `criteria` / 交付包 |

---
**（本块）裁定对应**：CR-40 ← TAG_POLICY §1 交付事件打标（process compliance · ENG 执行）。**报备监理 1 条 · owner 项 0**。

### 续编 · 监理 **#K2-58** 消费（l8 复核 PASS ⇒ 解除 `STOP-1` · `COV-C3` 范围/钉版 · 口径澄清 ×2 · 残余登记）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-45** | **【R1 · 主项】`l8` 独立复核 = PASS ⇒ **ENG 侧 `STOP-1` 解除**** | 监理**独立**复核（自写 PCB 解析器读 `U4`/`D1` pad→net · 自跑 canonical 19 于**全新 DRC work-dir** · 全锚复算 · 包 `55/55` · DFM `16/1/0`）⇒ **`l8` = PASS**（`n_pass 19 · n_fail 0 · provisional False`）。**决定性**：`l7→l8` 差异**恰好 4 条**（`U4/2 MCU_VDD→P3V3` · `U4/3 P3V3→MCU_VDD` · `D1/1 LED_A→GND` · `D1/2 GND→LED_A`）且**语义正确**（`P3V3→MCU_VDD` 通 · `LED_A→GND` 通）；**保真对照** `c5a7df90aadb66e0` = 在岗 l7 **逐字节同**。**`STOP-1` 解除**（ENG 侧门开）：ENG 可**按商务渠道**推进 P5 首件单——**ENG 不自采购、不承诺交期**（下单/采购/交期 = **商务渠道**，owner #14④）。**保留面**：`l7` 板若已在外 ⇒ **仍按缺陷复现样处理、不得作合格首件**；`l8` 方为合格首件候选。**件**：`docs/K2-P5-FIRST-ARTICLE-TRANSMITTAL-l8-v1.md` **§11**（下单就绪注）。 | **#K2-58 R1** | 未下单/未采购（商务面）· 未改交付锚 · **P5 仍 `PENDING_EXTERNAL`**（外部回件 + 监理判定方关门） |
| **CR-41** | **【R2 口径澄清 A】R2/R4 之落地读法 = 版本 bump 新件 + 符号层；`k2_sch.yaml` 逐字节未改 = 非违规** | 监理独立结构 diff 证实：`errata-2 → errata-3` 之 **`nets` 逐字相同 · `sheets` 逐字相同**，**唯一差异 = 2 个 symbol 之 pin NUMBER**（`BAT54C_ORING K 2→3 / A2 3→2`；`LED A 1→2 / K 2→1`）。生成器消费层 = `nets_yaml.symbols[*].pins`（= **CR-33 之有效杠杆层**）⇒ 订正**网表 pin 映射 + 符号层**即改板。`k2_sch.yaml`（按 pin **NAME** 连网 = **意图真源**）`dd794c54f7ce7417` **逐字节未动** ⇒ **gate④ PASS**。**故 #K2-57 R4 原文「订正 `k2_sch.yaml#LED`」措辞不精确**；实际落地 = **版本 bump `errata-3` + 符号层** ⇒ **符合**第四条「契约/工件修订一律**版本 bump 新文件**」。**本注目的 = 防后续会话把 R4 误读为「改 `k2_sch.yaml`」**（承 **CR-33**）。 | **#K2-58 R2**；本会话复算 `dd794c54f7ce7417` | **登记制（仅注）** · 未改任何文件内容 · **禁**改 `k2_sch.yaml` |
| **CR-42** | **【R3 口径澄清 B】DRC 读数一律以判据侧 canonical 全量为准；「23 条恒定 warning」= P4 期子集口径，不具交付判据效力** | **裁**：l8 交付判据之 DRC = **170 条 · 9 类 · `error 0` · `unconnected 0`**（canonical 全量）。「**23 条**」系 **P4 期（判据 rev=3 · l6/l7 期）子集口径**，**无法由在库册复现**，**不具交付判据效力**；本包披露集（170）为其**超集** ⇒ **不影响可制造性判定**。**禁**以 23 缩口径（**C-12**）。**落地位置说明（重要）**：该注原文位于**包内** `DISCLOSURE.md`，而该包 = **已复核锚 `4b610baed4f4752c` / `36a6b276b4f7e465`** ⇒ **本件不动**（改之则**复核件失效**、并使外发包/商务件失配；且 `DISCLOSURE.md`/交付记录均为**构建器再生件**，手改会被覆盖 ⇒ 须改工具+重跑 = **换锚**）。故澄清**如实登记于册面 + 证据件**（本件 + `P6_execution/P6_OPEN_READINESS/K2_58_CONSUMPTION_EVIDENCE_20260921_v1.json`）。**#K2-58 §五 判据④** 之可验要求 = 「**口径/钉版登记在册（含复现命令）**」⇒ 本件**满足**。 | **#K2-58 R3**；包内 `DISCLOSURE.md`（**已复核 · 冻结**） | **口径登记 · 不充绿** · **禁缩口径** · **包锚 `4b610bad`/`36a6b276` 未动** |
| **CR-43** | **【R4 另立批】`COV-C3` 范围 + 未同步期四树钉版（含 `sch_gate` 内容 pin）+ B 宿主分歧事实** | **范围（R4.1）**：四 `_shared`（`_shared` · `k2/_shared` · `key_v2/_shared` · `pciesw4/_shared`）× 件类 (i) **引擎层 `eda_core/*`**（漂移本体）(ii) **`sch_gate` 真源/引证件**。**归属 = 跨项目批次 · gate 属主排期**（维持 #K2-54 §四）；**ENG 不得越权改 `key_v2`/`pciesw4` 项目文件**。**钉版（本会话独立复算 · 与裁定逐项同）**——引擎 `eda_core/hs_route_model.py`：`_shared` / `k2/_shared` = **`c9e1c3b4ca208482`**（**权威态** · `ENG_VERSION.yaml` 齐备）· `key_v2/_shared` = **`883525b4f37a660f`** · `pciesw4/_shared` = **`6ab5eaaa416da3e7`**（后二者 **`ENG_VERSION.yaml` 缺** ⇒ 未同步）。**`sch_gate` 内容 pin（四树**全同** ⇒ R1/R5 内容面已闭）**：`BAT54C ed70671ac3b03746` · `DS320PR1601 2757a9f487531fe5` · `DCDC_12V_3V3 027772ce7f122ff9` · `DCDC_12V_5V af59deb0812d1916` · `LDO_5V_3V3 65219b10f9e670ff` · `DS160PR810 ed1b6e9a1eb0c56c` · `STM32G0B1CBT6 afd2d1a89b1765d0` · `strap_semantics fd1bb14317c7a235`。**B 宿主（R4.3）**：`key_v2/_shared` 本地 `d89d7bb`（落后 **65** / 领先 **5**）· `pciesw4/_shared` 本地 `91a2a44`（落后 **52** / 领先 **5**）· `origin/main = 6ab6308` · merge-base `ad41353e` ⇒ **非快进** ⇒ **禁 push · 禁 rewrite**；发布面收敛 = **跨项目历史调和**，**不属 ENG 单树职权**。**登记要求（R4.4）**：① 维持 `sch_gate` 四树内容一致（已达成）② 本件即册面登记（钉版表 + 分歧事实 + 复现命令）③ **禁**触 B 宿主远端、**禁**以四树漂移阻塞 P6/交付锚。 | **#K2-58 R4**；本会话四树复算；#K2-54 §四 | **未触 B 宿主远端**（无 push / 无 rewrite）· 未改他项目文件 · 不以漂移阻塞 P6/交付锚 |
| **CR-44** | **【R5 残余登记 · 非阻塞】注释头行 + `strap_semantics.yaml` 之旧文献号** | 监理实测：#K2-57 R5 明定「**仅订正 `source`/文献号字段**」且**具名 5 件**；而 `DCDC_12V_3V3/5V.yaml` 之**注释头行**仍 `SLVSD82` · `LDO_5V_3V3.yaml` 仍 `DS31056` · `STM32G0B1CBT6.yaml` 仍 `Rev 6 Table 12 (Figure 5)` · `strap_semantics.yaml::source` 仍 `TI SNLS658 Rev B` ⇒ **均不在 R5 五件范围** ⇒ **不构成 R5 未完成**。**处置**：**登记 · 不充绿 · 不阻塞**；ENG **可另批**顺带订正（**不改 pins**）——本会话**不做**（待另批 / 监理择期；承接 CR-3 登记制精神）。 | **#K2-58 R5** | 登记制 · **不充绿 · 不阻塞** · 若订正须**另批**且**不动 pins** |

---
**（本块）裁定对应**：监理 **#K2-58** 全额消费（R1 放行 · R2/R3 口径澄清 · R4 范围+钉版 · R5 残余登记 · R6 维持 · R7 过程）。**报备监理 1 条（册面登记完成 · 判据④满足）· owner 项 0**。

### 续编 · 外发面 **l7 残留指针**订正 + 生成器文档笔误登记（`#K2-58` R1 放行后之外发面自洽复核）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-46** | **P5 首件外发包（`L6/first_article_l8/`）内 **3 处 l7 目录指针**已订正（哈希已是 l8，唯路径仍指 l7 目录）** | **缘起**（本会话外发面自洽复核）：`#K2-58` R1 已放行下单 ⇒ 外部实测方即将使用外发包；而该包系 CR-38 由 l7 版**派生**，**只改哈希未改路径** ⇒ 三处错配：① `RULES.md` 交付锚 `../jlc_package/MANIFEST.json`（l7 目录）却载 **l8** 锚 `4b610bad…`；② `results_template.json::delivery_anchor.package` = `…/L6/jlc_package`（l7 目录）却载 l8 双锚；③ `results_template.json::rules` = `…/L6/first_article/RULES.md`（l7 件）。⇒ 外部将**读 l7 规程 / 对 l7 目录**，属**外发即错配**（= CR-38 同类）。**同型扫描**：全仓 `L6/DELIVERY/`·`L6/jlc_package/`·`L6/first_article/` 指针逐条判定，**其余命中均属 l7 世代文档**（`…TRANSMITTAL-v1.md` · `…DELIVERY-RECORD-v1.md` · P6 各计划）⇒ **正当**，**非缺陷** · **不充绿**。**处置**：三处路径订正为 `_l8`（哈希一字未动）；**未改** l7 件 · **未改**交付包锚。**新锚**：`RULES.md 42013771b1358954`（原 `00fc0f19fbaddf2e`）· `results_template.json d125c5eac50c933f`（原 `c7c8be4ecd5cd691`）；`CHECKLIST.md`/`INSTRUMENT_SELFCHECK.json` 未变。 | 本会话外发面自洽复核；CR-38；`#K2-58` R1 | **只改外发包内路径**（ENG 手制件 · 无工具生成）· **未改**交付包锚 `4b610bad`/`36a6b276` · **未改** l7 件 · 登记制 |
| **CR-47** | **【登记 · 待授权】交付记录（构建器生成件）路径笔误：l8 tarball 位置写作 `L6/DELIVERY/`，实为 `L6/DELIVERY_l8/`** | **事实**：`docs/K2-P5-DELIVERY-RECORD-l8-v1.md` §1 写「交付封装 `L6/DELIVERY/k2_v4_8L.l8_gerber_package.tar.gz`」，而**实测** l8 tarball `36a6b276b4f7e465` 位于 **`L6/DELIVERY_l8/`**（`L6/DELIVERY/` 仅含 l7 件 `0e88e107…`，**未受污染**）。**根因**：构建器 `tools/k2_p5_jlc_package_l8_v1.py:262` 之**文档字符串硬编码** `L6/DELIVERY/`，而实际输出目录由 `:309` 定为 `L6/DELIVERY_l8`（**代码与文档串不一致**）。**影响**：**无制造/交付影响**（投递说明 §11 与 `SHA256SUMS.txt` 之路径为准）；属**文档笔误**。**处置（本轮不做）**：修 `tools/…py:262` 属**改生成器**，且生效须**重跑构建器 ⇒ 换包锚**（违 #K2-58 复核件冻结之意）⇒ **登记 · 待监理授权另批**（届时「修串 + 重出包 + 复核锚」一笔）。 | 本会话实测；`tools/k2_p5_jlc_package_l8_v1.py:262/309` | **未改**生成器 · **未重出**包 · 登记制 · **不充绿 · 不阻塞** |

---
**（本块）裁定对应**：外发面自洽复核（`#K2-58` R1 放行后之当务项）。**报备监理 2 条（1 订正 + 1 登记）· owner 项 0**。

### 续编 · P5 **设计侧预判件 rev 基准**核验（l7 → l8 · CR-46 同型延伸）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-48** | **P5 设计侧预判件以 **l7** 为几何基准；本会话逐 rail 独立复算 l7 vs l8 ⇒ **`P3V3_AUX` 完全不变（引用有效）· `MCU_VDD` 显著过时（+105.92 mΩ · +81%）** | **缘起**（CR-46 同型延伸）：`PDN_DESIGN_PRECHECK_V5` · `P5_EXPECTED_VALUES_DESIGN_SIDE` · `P5_V5_NAMED_LOADPOINT_CONSISTENCY_FIX` · `P5_V6_1_NOMINALS…` 四件之 `inputs.board = k2_v4_8L.l7.kicad_pcb`（`c5a7df90`），而现行受审板 = `l8 7a5c8991`。**独立复算**（同模型 · 先反证吻合）：`P3V3_AUX` 最坏单跳 `In5.Cu 20.789mm/0.2mm/0.5oz` ⇒ 本件算得 **125.3 mΩ** = 原件/投递说明 §8 所载 ⇒ **模型逐项吻合**。**结果**：`12V_IN` 不变（10.60 mΩ）· `P3V3` +2.43 mΩ（+1.5% · 可忽略）· **`P3V3_AUX` 完全不变**（451.26 mΩ · 最坏单跳仍 20.789mm/125.3 mΩ）⇒ **投递说明 §8 引用有效** ✅ · **`MCU_VDD` 130.65 → 236.57 mΩ（Δ **+105.92 mΩ · +81%**）**（seg 63→168 · L 33.11→54.10mm · via 12→15 · 最坏单跳 4.95→5.657mm），根因 = CR-26 修复之 `U4` pad 交换致该网重布 ⇒ **该 rail 之 l7 基准事实已过时**。**另**：原件 `MCU_VDD::budget3_mV = 99.0` 系 3%×3.3V，而 **#K2-55** 定其主判标称 **3.0V** ⇒ 3% 预算应作 **90.0 mV**（登记 · **不改原件**）。**处置**：**新增** l8 基准证据件（**不改**原 l7 基准件 = 历史记录 · 不重出）；**不改变** V5 判据/测点/阈值（≤3% · 外部实测 · ENG 不自证）；**建议** V5 实测**同时覆盖 `MCU_VDD`**（`In4` 大平面可分担 ⇒ 真实压降应仍远低于迹线数）。**件**：`P6_execution/P6_OPEN_READINESS/P5_PDN_PRECHECK_REVBASIS_L8_20260921_v1.json`（`37616a93801d44da`）。 | 本会话独立复算（l7/l8 两板文本解析）；原件 `PDN_DESIGN_PRECHECK_V5…` | **设计侧预判 · 非证据 · 不充绿** · 未改阈值/判据/板/包/生成器 · **非新增判据维/检查齿**（复用同一模型） · 登记制 |
| **CR-49** | **【登记 · 待授权】P6 仪器自查工具仍读 **l7** 模板路径** | **事实**：`tools/k2_p6_instruments_selfcheck_v1.py:157` 之 `check_prerequisites()` 读 `L6/first_article/results_template.json`（**l7** 件）以产 `p5_external_all_not_run`；现行 P5 模板 = `L6/first_article_l8/results_template.json`。**影响**：**P6 已 CLOSED**，该字段为**事实记录项**（`out["ok"]=True  # 不构成 fail`），且两模板之 8 项**同为 `NOT_RUN`** ⇒ **当前读数巧合相同、无错误结论**；属**潜伏性 stale 路径**。**处置（本轮不做）**：改工具属**改生成器/工具** ⇒ **登记 · 待授权另批**。 | 本会话实测；`tools/k2_p6_instruments_selfcheck_v1.py:157` | **未改**工具 · 登记制 · **不充绿 · 不阻塞** |

---
**（本块）裁定对应**：P5 阶段只读造活（设计侧预判件 rev 基准核验）。**报备监理 2 条（1 新增基准件 + 1 登记）· owner 项 0**。
> **【CR-48 补充 · 2026-09-21】**：投递说明 §8 增一设计侧关注点（`MCU_VDD` l8 迹线电阻 +81% ⇒ V5 实测一并覆盖）⇒ `docs/K2-P5-FIRST-ARTICLE-TRANSMITTAL-l8-v1.md` 新锚 **`5a74cb491fd025ca`**（原 `19fb16130df598a9`）。**交付包锚 `4b610bad`/`36a6b276` 未动**。

### 续编 · **l7 基准件清扫完成**（CR-48 未覆盖之 4 件 · CR-50）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-50** | **l8 时代件以 l7 为基准者**全量清扫 = **8 件**（CR-48 已处置 4 件 + 本轮 4 件）；其中**外发对账件已换 l8 基准复算 ⇒ 9/9 不变**；余者登记不阻塞 | **清扫范围**：全 `artifacts/k2_v4` 提及 `k2_v4_8L.l7.kicad_pcb` / `c5a7df90` 者逐条判定 ⇒ 属 **l8 时代**（非 l7 世代历史件）者共 **8** 件。**CR-48 已处置 4 件**（`PDN_DESIGN_PRECHECK_V5` · `P5_EXPECTED_VALUES_DESIGN_SIDE` · `P5_V5_NAMED_LOADPOINT_CONSISTENCY_FIX` · `P5_V6_1_NOMINALS…`）。**本轮 4 件**：<br>① **`P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION`（具决策相关性 · 外发方动作依据）** ⇒ **换 l8 基准独立复算**：自写括号配对解析器**先以 l7 复现原 9 项**（口径校验）**再以 l8 重跑 ⇒ **9/9 逐项同**（`U1.10/R29.1/C73.1=NRST` · J13 四脚 · `E2` 八脚⇒**0x52** · `U6/J2/J3/J4` pad 74/38/38 · In1/In3/In6 各 1 `GND` zone · In4 7 zone 网集 · `PCIE_UP3` P+N 层段 F.Cu 30/In2 4/In5 31 · 观察项 refdes 全在）⇒ **原结论对 l8 仍成立**；**非材料性差异 2 项**：`NRST` 层段 88→118（CR-26 重布连带 · 具名判据不变）· In4 zone **文件序**不同（网集相同）。**件**：`P6_execution/P6_OPEN_READINESS/P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION_L8_RECHECK_20260921_v1.json`（`bcd564fac932c7e3`）。<br>② **`P5_RESULTS_TEMPLATE_PREFILLED` · `…PREFILL_AND_PREVALIDATION`**：l7 基准之**预填/预验副本**（原意供外部填写）⇒ 已被**权威模板** `L6/first_article_l8/results_template.json`（`d125c5eac50c933f`）**取代** ⇒ **登记 · 不阻塞**（不改造 · 不主张其为外发件）。<br>③ **`P5_V7_TJ_CALIBER_CORRECTION_TI_SNLS683` · `P5_V7_TJ_CONVERSION_CALIBER_CONFLICT`**：V7 热口径件（**热学与走线几何无关**；l7 引用属**溯源细节**）⇒ **登记 · 不阻塞**。 | 本会话全量清扫 + l8 独立复算（解析器先以 l7 自证）；CR-46/CR-48 同型 | **未改**任何 l7 基准件（历史/在册记录）· **未改**权威模板/交付包/判据/生成器 · **非新增检查齿**（换基准重跑 · 未新增判据维/阈值）· 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（l7 基准件清扫收口）。**报备监理 1 条 · owner 项 0**。

### 续编 · owner ③ 交付件**互证**（叠层图 ↔ SPEC 叠层 ↔ 钻孔程序 ↔ 阻抗 · CR-51）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-51** | **owner ③ 交付件「件间自洽」互证 5/5 PASS**（此前仅验「件在」，未验「件间同构」）+ 登记 1 处 **SPEC 自由文本**内不一致 | **缘起**：owner ③ 要求交付含「**叠层图**」与「**Excellon 含 HDI 盲埋孔**」；制造方**同时读**二者 ⇒ 必须**同构**。**互证结果**：① **叠层图 ↔ SPEC `stackup.dielectric_8l`**：逐层一致（`F.In1 0.1164/er4.16/2116*1` · `In1-In2/In2-In3/In4-In5/In5-In6 0.25/3.99/core` · `In3-In4 0.1922/4.1/自由余隙` · `In6-B 0.1164/4.16`）✅；② **厚度闭合**：介质 **1.4250** + 铜(1oz×2=0.070 + 0.5oz×6=0.105 = **0.1750**) = **1.6000 mm** = SPEC `total_thickness_mm 1.6` ⇒ **精确闭合** ✅；③ **HDI 阶数图 ↔ Excellon 层对/支数**：`F→In1 171` · `F→In2 132` · `F→In4 4` · `F→In5 19` · `In5→B 37` · `In2→In5 92`（**455 非通孔**）· `F→B(THROUGH) 279` ⇒ 合 **734 via** = 图载 `non-through 455/734` ✅；**口径对齐**：通孔文件 `k2_v4_8L.l8.drl` 含 **299 孔** = `T1 ∅0.2×279`(via) + `T2 ∅0.8×16`(PTH) + `T3 ∅3.2×4`(NPTH) ⇒ 全包 **754 孔 = 734 via + 16 PTH + 4 NPTH**（与 `drill_board_xcheck.all_match=true` 一致）⇒ **图按 via 计、册按孔计，非矛盾（已具名对齐）** ✅；④ **SPEC 阻抗 ↔ SPEC 叠层**：F.Cu `h=0.1164/er4.16/2116*1` · In2 `w0.16/er3.99` ↔ 对应介质层 ✅；⑤ **层序件 ↔ SPEC 层角色**（F/In2/In5/B = signal · In1/In3/In6 = GND · In4 = POWER）✅。**登记（不阻塞）**：`SPEC…spec-rev-53.json::stackup.material`（**自由文本**）写「2116*1 / **3313*1**，**core 0.36*2**」，而同一 SPEC 之**结构化** `dielectric_8l` + 叠层图 + 阻抗节 皆为「2116*1 + **core 0.25** + **自由余隙 0.1922**」⇒ 该自由文本系**早期候选/遗留描述**；**权威 = 结构化数据 + 叠层图**（二者一致且厚度精确闭合）。**处置**：**登记 · 不阻塞 · 不改 SPEC**（**红线：未获批不得改 SPEC**）⇒ 待授权另批（改文本须换 SPEC 锚 + 同步交付件）。**无制造影响**（制造以叠层图/钻孔程序为准，二者自洽）。**件**：`P6_execution/P6_OPEN_READINESS/L8_DELIVERABLE_CROSS_CONSISTENCY_OWNER3_20260921_v1.json`（`e723653a01dece15`）。 | 本会话只读互证；owner #14③；`drill_census.json` · `drill_board_xcheck.json` · SPEC rev-53 · 叠层图 SVG | **只读** · **未改**交付包（锚 `4b610bad`/`36a6b276` 未动）/SPEC（锚 `4e92b3a05cd5a223` 未动）/判据/板 · **非新增检查齿**（未新增判据维/阈值）· 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（owner ③ 交付件互证）。**报备监理 1 条 · owner 项 0**。

### 续编 · 交付包**完整性链路**端到端实证（MANIFEST ≡ 目录 ≡ SHA256SUMS ≡ tarball · CR-52）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-52** | **交付包完整性链路 5/5 PASS · 双向差 0 · 逐字节镜像**（此前仅验 `sha256sum -c` 一条） | **缘起**：owner ③ 要求交付含「MANIFEST」；既有验证只有 `sha256sum -c 55/55`（单向）⇒ 本件补**链路实证**：① **`MANIFEST.json::files`(53) ≡ 目录实件(53)**（除 MANIFEST）⇒ **双向差 0**（`n_files=53` 自洽）✅；② **`SHA256SUMS.txt`(54 行，去 tarball 行) ≡ 目录(54 含 MANIFEST)** ⇒ **无漏无多**（另 +1 行为 tarball ⇒ 全 55）✅；③ **tarball 条目(54) ≡ 目录(54)** 且**解包后逐件 sha256 全同 54/54** ⇒ **tarball = 目录之逐字节镜像** ✅；④ `LC_ALL=C sha256sum -c` = **55/55 OK · rc=0** ✅；⑤ **打包卫生**：顶层**唯一**目录 `k2_v4_8L.l8_gerber_package/` · `uid/gid` **统一 `root/root`** · `mtime` **统一 `2026-09-19 23:00`** ⇒ 声明之「固定 mtime/uid/gid」**实证成立** ✅。**观察（非阻塞）**：该固定 `mtime` **早于**本包构建日（09-21 00:25）＝**归一常量**（确定性打包，非缺陷）；若板厂对时间戳敏感，可于另批把常量更新为构建日。**件**：`P6_execution/P6_OPEN_READINESS/L8_PACKAGE_INTEGRITY_CHAIN_20260921_v1.json`（`12f9c95a44b1be6c`）。 | 本会话只读实证（`find`/`comm`/`sha256sum`/`tar`）；owner #14③；CR-36/CR-38 | **只读** · 包锚 `4b610bad`/`36a6b276` **未动** · 旧锚 **未动** · 未改判据/SPEC/板/生成器 · **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（交付包链路实证）。**报备监理 1 条 · owner 项 0**。

### 续编 · **验收口径链一致性**核验 + 阈值来源件 2 处订正（CR-53）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-53** | **P5 验收口径链 计划(阈值来源) ≡ `RULES.md` ≡ `CHECKLIST.md` ≡ `results_template.json`：**8/8 项 + 阈值全一致**；并订正来源件 **2 处**（板侧实证） | **缘起**：出包索引把 `K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md` 标为「**验收计划（阈值来源）**」⇒ 四件须同口径（否则实测方可能漏项/测错点）。**核验结果（逐项）**：项集 **V4 · V5 · V6-1 · V6-2 · V6-3 · V6-4 · V6-5 · V7 = 8/8 四件一致**；阈值 **全一致**（V4 `85.0Ω±10% = 76.5–93.5` · V5 `≤3%`（4 轨）· V6-1 `±5% 标称` · V6-2 `正确 device ID` · V6-3 `EEPROM 地址应答` · V6-4 `双路 x4 Gen4 训练成功（二值）` · V6-5 `AER=0` · V7 `四工况 Tj ≤120.0℃` + T1 `>117.0℃`/未按 O2 ⇒ 开新 rev（θJA_eff ≤9.5））✅。**订正 2 处（板侧实证 · 只对齐口径 · 不动阈值）**：<br>**(a) V6-2 测点误列 `NRST` 于 `J13`** —— 来源件原文「连接器 `J13`（SWCLK_BOOT0 / SWDIO / NRST）」；**板侧实证**（l8 解析）`J13` = `1 SWDIO · 2 SWCLK_BOOT0 · 3 GND · 4 MCU_VDD` ⇒ **`NRST` 不在 `J13`**（与 `P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION` 一致），`RULES`/`CHECKLIST` 已正确地列 `U1` pad10 / `R29` pad1 / `C73` pad1 ⇒ **来源件已同步为同口径**（含具名 pad 表）。<br>**(b) V7 未载 `Tj` 反推式** —— 曾致 `P5_V7_TJ_CONVERSION_CALIBER_CONFLICT`（外发 `RULES` 旧式 `θJC_top 6.5` ↔ L2-9c′ `ψJT 3.6`；该冲突已由 **CR-19 修订 / CR-20 撤回**更正 `RULES`）；来源件**未载式** ⇒ 已**补载唯一口径** `Tj = T_top + P·ψJT`（`ψJT = 3.6 ℃/W`）+ `θJC_top` 用途限定 + 沿革指针。**锚**：来源件 **`b002ec9829a53f12`**（原 `43795d2def07152b`）· 投递说明 §3 表同步 → **`ebf7659f1ca4923a`**。 | 本会话四件逐项核验 + l8 板侧解析；`P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION`；CR-19/CR-20 | **只对齐口径**（未改阈值/判据/交付包/生成器/SPEC/板）· 来源件系 **ENG 手制**（无工具生成）· **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（验收口径链核验 + 来源件订正）。**报备监理 1 条 · owner 项 0**。

### 续编 · P5 外发包**自证件对板** + **引用无悬空**（CR-54）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-54** | **① `INSTRUMENT_SELFCHECK.json` 逐脚对板 PASS（508 pad · 0 不一致）② 外发 4 件引用全员解析（悬空 = 0）** | **缘起**：`RULES.md §0` 明定实测方『**测点以 `INSTRUMENT_SELFCHECK.json` 为准**』⇒ 该件**必须与板逐脚一致**；且 4 件所引文件**不得悬空**（否则实测方指错文件）。**① 对板复算**（自写括号配对解析器读 l8 板）：`refdes`（`J13`/`J2`/`J3`/`J4`/`U6`）之 **508 个 pad→net 逐脚相同 · 不一致 0**；footprint 名一致；pad 数 **`U6` 354 · `J2` 74 · `J3` 38 · `J4` 38** 与板逐一致；`nets_present` **16/16 在板**；`swd_nets_on_J13 = true` ✅；`pcie_nets_on_J2 = true`（板侧 J2 含 **36** 条 PCIE 网）✅；**V5 具名负载点独立确认**：`J3.P3V3_AUX = A9` · `J4.P3V3_AUX = A9` ✅（与 CR-38 一致）。**② 引用解析**：filename-like 引用 **9** 条 ⇒ **全部解析成功 · 悬空 0**（扫描对 `k2/docs/…` 之 1 处 MISS 系**解析器前缀假阳性**，真路径 `docs/…` 存在且本会话 CR-53 刚订正 ⇒ 已人工复核）。**件**：`P6_execution/P6_OPEN_READINESS/P5_OUTBOUND_PACK_SELFCHECK_AND_REFERENCE_AUDIT_20260921_v1.json`（`55e819a3af39b509`）。 | 本会话只读复算（l8 板解析 + 引用解析）；`RULES.md §0`；CR-38/CR-53 | **只读** · 交付包锚 `4b610bad`/`36a6b276` **未动** · 本轮**未改**外发件 · 未改判据/SPEC/板/生成器 · **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（外发包自证件对板 + 引用解析）。**报备监理 1 条 · owner 项 0**。

### 续编 · 外发自查件**覆盖缺口**补齐（CR-55）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-55** | **`L6/first_article_l8/INSTRUMENT_SELFCHECK.json` 覆盖缺口：`RULES.md` 称 NRST 测点『已由本件机核』，然本件**原不含** `U1/R29/C73`（亦不含 `E2`/`C90`/`J11`/`R1`）⇒ 已按 l8 板**逐脚补齐**（12 refdes · 577 pad · 对板不一致 **0**）** | **缘起**：`RULES.md §0` 明定实测方『**测点以 `INSTRUMENT_SELFCHECK.json` 为准**』；本轮覆盖审计发现该件 `refdes` **原仅 5**（`J13`/`J2`/`J3`/`J4`/`U6`），而 `RULES.md §V6-2` 却写「接口（**已由 `INSTRUMENT_SELFCHECK.json` 机核**）… **`NRST` 不在 `J13`** —— 其测点为 `U1` pad10 / `R29` pad1 / `C73` pad1」，`§V5` 另引 `C90/J11/R1/U1` 为 `P3V3_AUX` 同网佐证，`V6-3` 之被测件 `E2` 亦未列入 ⇒ **『以本件为准』名实不符**（实体本身在板无误，缺的是**外发件未载**）。**处置**：按 l8 板**逐脚补齐** `E2`(8) · `U1`(49) · `R29`(2) · `C73`(2) · `C90`(2) · `J11`(4) · `R1`(2)，并加 `serves` 字段（各实体服务之验收项）+ `coverage_note`（记本次补齐）。**复核**：`refdes` **12** · pad **577** · **对板不一致 0** ✅。**锚**：本件 **`540c9a55c66b053b`**（原 `432125b50d6f5590`）· 投递说明 §3 表同步 → **`aecfc49a5423a874`**。 | 本会话覆盖审计 + l8 板侧解析；`RULES.md §V6-2/§V5`；`P5_OUTBOUND_NAMED_ENTITY_RECONCILIATION` | **只补外发件之板侧实证字段**（ENG 手制件 · 无工具生成）· **未改**交付包锚 `4b610bad`/`36a6b276` · 未改判据/SPEC/板/生成器 · **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（外发自查件覆盖补齐）。**报备监理 1 条 · owner 项 0**。

### 续编 · 回件模板「**判据所需量**」审计 + V6-1 schema 补齐（CR-56）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-56** | **回件模板逐项审计：8 项中 **7 项量齐**；`V6-1` **缺 #K2-55 之主判工况 + 辅助读数** ⇒ 已补（`condition` + `MCU_VDD_aux_j13_3V3` + `condition_required`）** | **缘起**：判据可执行性的最后一环 = **回件模板能否捕获判据所需量**（缺 ⇒ 回件后不可判）。**审计口径**：逐项比对「判据/口径」↔「`measured` 字段」。**结果**：`V4`（覆盖几何双点 ✔）· `V5`（4 轨 `V_source/V_load/I_A/drop_pct` + 电流声明 ✔）· `V6-2`（接口 + `device_id_read` + `expected_device_id` ✔）· `V6-3`（`addresses_found` + `expected_address`（含 `board_verified`）✔）· `V6-4`（`ports/both_directions/final_state` ✔）· `V6-5`（`aer_count/log_files` ✔）· `V7`（`assembly`+`Ta_C`+`Ttop_C`+`Tj_meas`+`Tj_conserve_upper`+`Tj_measure_method` = RULES『必须同记』量**齐备** ✔）⇒ **7 项完整**。**唯 `V6-1` 有缺**：原 `measured` 仅 `rails{4 轨}` ⇒ **无处记**（a）**#K2-55 主判工况 = 独立运行（J13/VCC 不接外供）**（b）**辅助读数**（J13/VCC 供 3.3V 时之 MCU_VDD，RULES 明定『须同记、不改主判』）⇒ **有把 3.3V 外供工况之读数当主判之风险**。**处置**：`V6-1.measured` 增 `condition`（**必填**：`独立运行`｜`J13/VCC 供 3.3V`）+ `MCU_VDD_aux_j13_3V3`（辅助读数）+ `condition_required`（明示缺 `condition` ⇒ **该判不可判**）；其余字段/阈值一字未动。**锚**：`results_template.json` **`6b510775339bdc11`**（原 `d125c5eac50c933f`）· 投递说明 §3 表同步 → **`9602f7be3f560eb6`**。 | 本会话逐项审计；**#K2-55**；`RULES.md §V6-1`；CR-48/CR-53/CR-55 同型 | **只补模板捕获字段**（ENG 手制件）· **未改**阈值/判据/交付包锚 · 未改 SPEC/板/生成器 · **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（回件模板判据量审计）。**报备监理 1 条 · owner 项 0**。

### 续编 · 权威件 `V6-1` 未载 #K2-55 工况/辅助读数 ⇒ 补齐（CR-57）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-57** | **权威操作规程 `RULES.md §V6-1` 与 `CHECKLIST.md` 之 `V6-1` 行**未载** #K2-55 主判工况与辅助读数**（全文 **0** 处 `独立运行`/`外供`）⇒ 已补齐（与 template/投递说明 §10 同口径）** | **缘起**（CR-56 同型延伸）：CR-56 已把 `condition`/`MCU_VDD_aux_j13_3V3` 补进**回件模板**，但**权威件**（投递说明 §3 明定「逐项操作规程 = **权威件**」）与现场检查表**仍只写**「测点/条件：同 V5（稳态、已声明负载）· 判据：±5% 标称」⇒ **实测方按权威件执行时可外供 `J13/VCC`**、把 3.3 V 基线读数当主判 ⇒ **正是 #K2-55 要消除之歧义**（`MCU_VDD` 主判标称 = **3.0 V**，窗 2.85–3.15 V；辅读 3.135–3.465 V）。**处置**：① `RULES.md §V6-1` 增「**主判工况（强制）= 独立运行 · `J13/VCC` 不接外供**」+「**辅助读数须同记、不改主判**」+「`condition` **必填**（缺 ⇒ 该判不可判）」+ 各轨标称；② `CHECKLIST.md` `V6-1` 行同步（工况 + 辅读 + 主判窗）；③ 投递说明 §3 表锚同步。**锚**：`RULES.md` **`058f650df4d626e6`**（原 `42013771b1358954`）· `CHECKLIST.md` **`f58ca379dab41cbe`**（原 `b97ac43fc0f99c31`）· 投递说明 **`902c81e55438aa27`**。**未改**任何阈值（±5% 名义不变；仅明示 `MCU_VDD` 之主判窗）。 | 本会话跨件审计；**#K2-55**；CR-56；投递说明 §3/§10 | **只补口径/必填项**（ENG 手制件）· **未改**阈值/判据/交付包锚/SPEC/板/生成器 · **非新增检查齿** · 登记制 |

---
**（本块）裁定对应**：P5 阶段只读造活（权威件 V6-1 口径补齐）。**报备监理 1 条 · owner 项 0**。

### 续编 · 补履行 **#K2-48 §三-4** 之册面落档（N-1 · N-6 · N-7）+ P5 就绪审计 2 项发现收口

> **缘起**：监理 **#K2-48**（批 5 · 逐项自裁 · owner 项 0）§三-4 明定「**N-1 / N-6 / N-7 = 册面/口径注明（ENG 只读落档）**」。本会话核查：册面**此前无任何 #K2-48 痕迹** ⇒ 该落档**从未履行** ⇒ 本件补齐（**只读落档 · 不动交付锚 · 不重建包**）。

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-58** | **【#K2-48 N-1 · 交付口径 4 小项】`B-1` 叠层 · `B-2` Finish(ENIG) · `P5-1` 阻抗券索取 · `P5-2` 编号 —— 一律「(a) 接受 + 随单注明」** | **裁定**：**（a）接受 + 随单注明**（**不动交付锚**）；**「禁重建包」**。**逐项口径**：`B-2`（Finish=ENIG）· `P5-1`（**阻抗券索取**）= **商务下单页**（owner #14④ · **非 ENG 任务**）；`B-1`（叠层）· `P5-2`（编号）= **随单 / DISCLOSURE 注明**。**ENG 落字**：投递说明 §5（商务面）+ §11（下单就绪）已载「**下单须注记阻抗控制 + 索取 V4 阻抗券**」；本会话实测 **l8 `DISCLOSURE.md §5b` 编号确为 1·2·3·**5**·**4**（乱序 · 装饰级）** ⇒ 按「禁重建包」**保留原样**，由本册面记其性质（**非缺陷、不阻塞**）。**⇒ P5 输入风险「阻抗券未索取」已由商务下单页兜住**（`K2-P5-EXECUTION-PACK-READINESS-AUDIT` `P5-1`（中）**关闭**）。 | **#K2-48 N-1（(a) 接受 + 随单注明 · 禁重建包）**；本会话 l8 实测；投递说明 §5/§11 | **禁重建包** · 未动交付锚 `4b610bad`/`36a6b276` · 商务事项不代行（owner #14④） |
| **CR-59** | **【#K2-48 N-6 + N-7】P2 口径注明「判据换址、非缺失」· P6 判据①② 确认达成（P5 外部门仍关）** | **N-6**：`measure_source_reconcile.py` 未落件之口径 —— 册面注明「**判据换址、非缺失**」（由 **rev=3 三维**承接）。**N-7**：P6 判据面新读数 —— **确认 P6 判据 ①② 达成**：`P6-1`（K1 verdict `provisional=False` · 四项同源命中）· `P6-2`（K2 模板 `ignore=0` · 结构差异 `0/10`）；**P5 外部门仍关**（V4–V7 `NOT_RUN` · ENG 不自证）。 | **#K2-48 N-6/N-7**（§三-4 落档） | 只读落档 · 不改变阶段门态 |
| — | **（附）P5 就绪审计 §B 之**替代**（l7 期「11/11」→ l8 复核）** | `K2-P5-EXECUTION-PACK-READINESS-AUDIT-20260921.md` §B 之「测点指向 11/11」系**l7 期**核验 ⇒ 已由本会话 **l8 板独立复核取代/加强**：`INSTRUMENT_SELFCHECK.json` **12 refdes · 577 pad 对板 0 不一致**（CR-54 对板复算 + CR-55 覆盖补齐）；投递说明 §3 该行标签同步更正为 **l8 复核口径**（新锚见下）。 | 本会话 CR-54/CR-55；投递说明 §3 | 只更正标签口径 · 未改自证件数值 |

---
**（本块）裁定对应**：补履行 **#K2-48 §三-4**（册面落档 N-1/N-6/N-7）+ 就绪审计 2 项发现收口。**报备监理 1 条 · owner 项 0**。

### 续编 · 裁定 → 册面 **追溯审计**（防后续会话重复追查）+ `K1-D8` 状态登记（CR-60）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-60** | **裁定→册面追溯审计**：`#K2-41/42/43/47/50/51` 于本册面**零引用**之原因已查明（**非 K2 册面缺口**）· 并登记各裁定之**落地指针** · 附 `K1-D8` 之**现状**（登记 · 不越项目处置） | **缘起**（CR-58/59 补履行 #K2-48 §三-4 之同型）：核查「裁定所要求之 ENG 落档是否履行」。**逐裁定结论**：<br>**#K2-41** → k1 `16d7b7c`（K1 项目域 G3.1 期望集声明 · §三-⑦）· **#K2-42** → k1 `dc720fd`（batch3 · K1 G1.5 WAIVER 撤 + O1 模板 ignore 清理）· **#K2-43** → 批 4 学习环收口（其 ENG 三项 C-1/C-4/C-22 由 **#K2-47** 收口）· **#K2-47** → **criteria rev=5**（`CHANGELOG` §rev=5 · C-1 残面 17 维 `dim_source_of_truth`；gate 属主装件）· **#K2-48** → **criteria rev=6**（C-25 落件 `jlc_hdi_capability.yaml` + manifest +2 维；**本册面 CR-58/59 已落 N-1/N-6/N-7**）· **#K2-49** → k1 `c018fc7`/`4084133`/`01f4d72` · **#K2-50** → 批 6 复算 r1=r2 IDENTICAL（监理）· **#K2-51** → k1 `08ff8bb`（U1 脚号 25→26 等）。⇒ 上述裁定之落地**均在 K1 仓提交 / criteria CHANGELOG / 监理复算**中留痕，**属 K1 项目面或 gate 属主面**（**非** K2 册面应载项）⇒ **无缺口**。**（附）`K1-D8`（`Q1`/`U12` 之 `VBIAS` 未接）现状登记**：`k1/boards/k1_sch.yaml` §头部**自述**为具名残留（「**K1-D8 = VBIAS 未接，属板级缺陷册具名项**」，且明确「**不写成 NC**」以免掩盖）；k1 提交史**未见** `VBIAS`/`K1-D8` 落地提交 ⇒ **#K2-50 授权之修法 (a)（`VBIAS → PWR_5V_MAIN`）尚待落地**，其**停机条件**（须先以手册证明 `VBIAS ≥ VIN` 且 `VIN` 即 5V 域轨、选择被约束唯一化；不成 ⇒ 停机报 owner）**未见履行记录**。**处置**：本项属 **K1 项目面**（非本会话 K2/P5 阶段）⇒ **本会话不改 K1 文件**；**登记现状 · 提请监理于 K1 批中确认/推进**（**不重复上报** · 先查册原则）。 | 本会话追溯审计（册面/索引维护）；k1 提交史；`criteria/CHANGELOG`；`k1/boards/k1_sch.yaml` §头部 | **只读登记** · 未改 K1/K2 任何源件 · 未越项目 · 未新增判据维/检查齿 · 登记制 |

---
**（本块）裁定对应**：册面/索引维护（handoff §8-B 允许项）。**报备监理 1 条 · owner 项 0**。

### 续编 · **P5 就绪里程碑 TAG**（TAG_POLICY §1 交付事件 · CR-61）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-61** | **已打 annotated tag `k2-v57-p5-outbound-pack-ready` → `92eb193`**（P5 就绪里程碑：#K2-58 R1 `STOP-1` 解除 + l8 外发包收口） | **事件**：① **#K2-58 R1 = l8 独立复核 PASS ⇒ ENG 侧 `STOP-1` 解除**（gate 类事件）；② l8 **外发包/P5 执行包**经本会话 CR-46..CR-60 收口（rev 指针 · 自查件覆盖 · 模板判据量 · 权威件口径 · 验收链 · 册面落档）⇒ 属 TAG_POLICY §1「**发布候选/交付**」**必打**事件。**tag message（§3 必含）**：`gate` 判定（P0–P4 HOLDS · P4 对 l8 **19/0** · P5 `PENDING_EXTERNAL` · P6 CLOSED · **未越阶段** · **`STOP-1` 已解除**）· 交付包锚 **`4b610baed4f4752c`**/**`36a6b276b4f7e465`**（**未动**）· 外发包 6 锚（`RULES 058f650df4d626e6` · `CHECKLIST f58ca379dab41cbe` · `template 6b510775339bdc11` · `selfcheck 540c9a55c66b053b` · 投递说明 `314239049f4c2ba3` · 验收计划 `b002ec9829a53f12`）· 判据 **rev=6** · 受审板 `7a5c89913d6e5d0a` · 册面 `3dcf790bd91147aa` · `date 2026-09-21` · 复现命令。**核验**：`push origin --tags` ⇒ `ls-remote --tags` **`^{}` 解引用 = `92eb193`**（= 目标 commit）✅；tag 后 HEAD 距 tag **0** ⇒ 哨兵 tag 断档告警**复位**（阈值 20）。 | `k2/pm_gate/TAG_POLICY.md` §1/§2/§3/§4/§5/§6；**#K2-58 R1**；CR-14（断档口径） | **禁**为历史 commit 批量补打 · 禁 amend/rebase 已发布段 · 未改冻结四源/`criteria`/交付包 |

---
**（本块）裁定对应**：TAG_POLICY §1 里程碑打标（ENG 执行 · 进程合规）。**报备监理 1 条 · owner 项 0**。

### 续编 · P5 外发面自洽复核（引用解析 + 代际标签）—— 验收计划 l7→l8 同步 + 冻结包残留标签登记（CR-62/CR-63）

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-62** | **现行 P5 验收计划（`docs/K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md`）§0/§6 仍为 l7 世代指针 ⇒ 已同步至 l8（阈值/测点一字未动）** | **缘起**（P5 外发面自洽复核 · handoff §8-B 允许项）：该件即 l8 外发包之**「验收计划（阈值来源）」**（`L6/first_article_l8/RULES.md:3` · `L6/first_article_l8/results_template.json::plan` 均按路径引用之；亦在 `P5_OUTBOUND_PACK_SELFCHECK_AND_REFERENCE_AUDIT` 之 9 条解析成功引用内）⇒ 其实测方**直接可达**。**事实（本会话实测）**：**(a) §0** 写「交付包 `L6/jlc_package/` 为唯一输入（…`K2-P5-DELIVERY-RECORD-v1.md`）」= **l7 目录 + l7 记录**（l8 应为 `L6/jlc_package_l8/` + `…-RECORD-l8-v1.md`）；**(b) §6** 写「受审板 `c5a7df90aadb66e0` · pro `33b4eb6cae8359a9` · SPEC rev-52 `42f8485ee4d6b566` · 判据 rev=3」= **l7 世代锚**（l8 = `7a5c89913d6e5d0a` / `c009058005829f09` / rev-53 `4e92b3a05cd5a223` / rev=6）⇒ 实测方将**读 l7 目录、溯源 l7 板/SPEC/判据** = **CR-46 同类「外发即错配」**。**同型扫描（l8 外发 6 件全扫）**：`RULES.md` · `CHECKLIST.md` · `results_template.json` · `INSTRUMENT_SELFCHECK.json` · `…TRANSMITTAL-l8-v1.md` **零残留**（TRANSMITTAL 内 `l7` 提及均属正当披露）⇒ **仅本件命中**。**body 已属 l8 口径之证**（故唯 §0/§6 未同步）：§2 V4「最紧真平行段 0.2825mm · `PCIE_UP3` · −4.24%」= `04_impedance/impedance_table.{md,json}` 逐字同；§3「丝印越框 4 处 · max 1.848mm（`H4`/`R41`/`D2`/`C87`）」= `07_verify/silk_overhang.json` 逐项同；§3「阻焊坝 9 处」= `07_verify/mask_accept_fix_proof.json`（`solder_mask_bridge=9`）同；CR-53 已核 8 项阈值 8/8 一致。**处置**：§0 路径 → `L6/jlc_package_l8/` + `K2-P5-DELIVERY-RECORD-l8-v1.md`；§6 四项 → l8 现行值 + **沿革注（CR-62）**；§6「包内验证」由 5 项列全为 **9 件**；**阈值/测点/判据口径一字未动**。**锚**：计划 **`5e7ee0598265a233`**（原 `b002ec9829a53f12`）· 投递说明 §3 表同步 `314239049f4c2ba3` → **`a181e851eebb72b4`**。**注**：tag `k2-v57-p5-outbound-pack-ready` message 内载之「验收计划 `b002ec98…`」「投递说明 `31423904…`」两锚**由此 supersede**（tag message 不可变 ⇒ 以册面为准）。 | 本会话实测（l8 外发 6 件对包/对板复核）；handoff §6 教训 2/3；CR-46/CR-47/CR-53；**#K2-58 R1** | **只改 ENG 手制件**（无工具生成 · 非派生）· **未改**阈值/判据/SPEC/板/生成器 · **未改**交付包锚 `4b610bad`/`36a6b276` · 未改 l7 件 · **非新增检查齿** · 登记制 |
| **CR-63** | **【登记 · 待授权】冻结 l8 交付包内 **2 处代际标签残留**（`criteria_rev3` key 名 · `spec_rev52` verdict 串）—— 修需重出包⇒换锚，本轮不动** | **事实（本会话实测）**：**(i)** `L6/jlc_package_l8/07_verify/anchor_selfcheck.json::"criteria_rev3"` —— **key 名**为 `criteria_rev3`，其**值**却为 **rev=6 现行**（`manifest.k2.yaml 727d0995…` · `adjudicate.py 1937a40a…` · `CHANGELOG eb3da49f…`）⇒ 名实代际不一致；且**仅列 3 件**（rev=6 判据为 **5 件** ⇒ 另 2 件 `jlc_hdi_capability.yaml` / `manifest.k1.yaml` 未列）；**权威 = 包内 `MANIFEST.json::criteria_anchor = rev=6`** ✅。**(ii)** `L6/jlc_package_l8/04_impedance/impedance_table.json::as_built_verdict = "geometry_matches_spec_rev52_per_layer"` —— 同件 `nature` 字段已明书「几何源 = SPEC **rev-53**」、`as_built_note` 与 `04_impedance/impedance_table.md` 亦皆 rev-53 口径 ⇒ **verdict 串残留 `rev52`**。**根因**：生成器 `tools/k2_p5_jlc_package_l8_v1.py:764`（key 名硬编码）与 `:526` 邻域（verdict 串硬编码），系由 l7 版**机械派生未改**（l7 包同 key 亦存 ⇒ 非 l8 新引入）。**影响**：**无制造/交付影响**（均为标签/串；`MANIFEST.json` 与 `impedance_table.md` 之 rev-53/rev=6 为准）。**处置（本轮不做）**：修生成器 + 重出包 ⇒ **换交付锚**（违 #K2-58 冻结之意）⇒ **登记 · 待监理授权另批**（**与 CR-47 同批**：「修串 + 重出包 + 复核锚」一笔）· **禁重建包**。 | 本会话实测（l8 包内 rev 串全域扫描）；CR-47 同族；`tools/k2_p5_jlc_package_l8_v1.py:764/526` | **未改**冻结包/交付锚 `4b610bad`/`36a6b276` · **未改**生成器 · 登记制 · **不充绿 · 不阻塞** · **非新增判据维** |

---
**（本块）裁定对应**：P5 阶段只读造活（外发面自洽复核：引用解析 + 代际标签）。**报备监理 1 条 · owner 项 0**。

### 续编 · **#K2-59 另立批执行**（CR-64..CR-68）—— l8r2 重出（新版本/新路径·旧锚保全）+ 外发面同代同步

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-64** | **`#K2-59` R1 之 `CR-47` + `CR-63` 落地于 `tools/k2_p5_jlc_package_l8_v1.py`（三串订正）** | **事实**：`:262` 文档串 `L6/DELIVERY/` → **`L6/DELIVERY_l8/`**（CR-47）；`:764` key 名 `criteria_rev3` → **`criteria_rev6`** 且**补列全 5 件**（`CHANGELOG` · `adjudicate.py` · `jlc_hdi_capability.yaml` · `manifest.k1.yaml` · `manifest.k2.yaml`）（CR-63(i)）；`:568` verdict 串 `…spec_rev52…` → **`…spec_rev53…`**（CR-63(ii) · 本件 SPEC 锚 = rev-53）。**判据②**：三旧串 **0 命中** ✅（`grep -n "criteria_rev3\|spec_rev52\|L6/DELIVERY/"`）。**锚**：`08667d2ceb2a56ae` → **`796043be97ceb3f8`**。**注**：旧 generator 订正后**不再逐字节复现冻结包**（冻结包字节已保全 · R2-1）；现行复现路径 = l8r2 generator（CR-66）。 | **#K2-59 R1**（CR-47/CR-63）；§五判据② | 仅**文档串/key 名/串**；**禁改**输出路径逻辑与判定逻辑 · 未改冻结包 · 登记制 |
| **CR-65** | **`#K2-59` R1 之 `CR-51` 落地：新件 `L3/SPEC_k2_v4.spec-rev-54.json`（仅自由文本）** | **事实**：rev-54 = rev-53 **仅 `stackup.material` 自由文本** 变更（`prepreg 2116*1 / 3313*1，core 0.36*2` → **逐层结构化口径** `2116*1` / `core 0.25` / `In3-In4` 自由余隙 `0.1922`，并注早期 CO-55 候选已由 CO-66→CO-68 取代）。**证据**：逐字段 walk 断言 + 文本 diff = **恰 1 行**；`dielectric_8l` · `dielectric_8l_basis` · `total_thickness_mm` · `material_legacy_6l` · 层角色 **逐项同**。**锚**：新件 **`f3a48b866983c8db`**；**rev-53 `4e92b3a05cd5a223` 与冻结原件 `SPEC_k2_v4.json 0bd52ed48e720b8c` 逐字节未动** ✅。**指针**：`pm_gate/project.yaml::spec_name` → rev-54（`5fdd6221f9d290b6` → **`bf057b5f177583a8`**）—— 属声明 delta「**SPEC 锚 rev-53→rev-54**」（与既往 SPEC bump 同轨：`adf2ab6` rev-52 · `c83d77f` rev-53）。 | **#K2-59 R1**（CR-51）· R2-3 | **禁**动任何结构化/量化设计值（介质厚度/`er`/阻抗/层角色/`total_thickness_mm`）· 未动 rev-53/冻结原件 · 登记制 |
| **CR-66** | **`#K2-59` R2 首件交付包重出：新版本 `P5-L8.2` · 新路径 · 旧锚逐字节保全** | **新生成器** `tools/k2_p5_jlc_package_l8r2_v1.py`（**`bc2394923a919058`** —— 由订正后 l8 版机械派生 + fail-closed 守卫「`OUT` 不得指向冻结包 l8」）；产物 **`L6/jlc_package_l8r2/`**（`MANIFEST.json` **`19d637c4e9ed35be`** · `revision P5-L8.2` · `criteria_anchor rev=6` · `drill_total 754` · `n_files 53`）+ **`L6/DELIVERY_l8r2/`**（tarball `k2_v4_8L.l8r2_gerber_package.tar.gz` **`488e90a47d088d06`** · 423156 B）+ `docs/K2-P5-DELIVERY-RECORD-l8r2-v1.md`（**`502200e0d3a20329`**）。**完整性链**：`LC_ALL=C sha256sum -c DELIVERY_l8r2/SHA256SUMS.txt` = **55/55 OK** · `MANIFEST.files`(53) ≡ 目录(53) · tarball(54) ≡ 目录 **逐件 sha 全同** · 顶层目录唯一 `k2_v4_8L.l8r2_gerber_package/` · **无 `.l7` 条目** · DFM **16 PASS / 1 ACCEPT / 0 FAIL** · drill **754**。**几何零变更证明**：54 ↔ 54（**无增删**）· **48 件逐字节同**（全部 **14 Gerber** · **8 钻孔件** + maps · 叠层 SVG ×2 · 层序 · L2 裁定副本 ×4 + parity · DFM 原始读数/卡 ×4 · 钻孔普查/对账 · Gerber 外接框/孔径普查 · 阻焊 ACCEPT 证明 · N-01 G36 · 丝印越框 · 重铺不变性）· **6 件变更 = 全为声明 delta**（`MANIFEST.json` 版本/自指 sha · `07_verify/anchor_selfcheck.json` SPEC 锚 + key 名 + 5 件 · `04_impedance/impedance_table.{json,md}` version/nature/SPEC 锚/verdict · `DISCLOSURE.md` SPEC 锚 · `ORDER_NOTES.md` 标题/gen/SPEC rev）· pad/net/footprint 计数不变。**旧锚保全**：l8 `4b610baed4f4752c`/`36a6b276b4f7e465` · l7 `6ee7495de61f749f`/`0e88e107e2da8192` **逐字节未动** ✅。**verdict 串取值说明**：取 **`geometry_matches_spec_rev54_per_layer`**（= 与包内 SPEC 锚同代）；`#K2-59` R1 括号内举例 `rev53` 系以未 bump 前世代书写 —— 本件按该裁「**名实同代**」之原则取 rev54，以免新件复现 CR-63 同类「名实不一致」。 | **#K2-59 R2**（1–5）；§五判据③④⑤⑥ | **禁**覆盖/删除/ in-place 重建旧包 · 未改板（`7a5c8991` 仍为输入）/判据/交付锚 · 登记制 |
| **CR-67** | **`#K2-59` R2-5 外发面同批原子同步（+ 顺手订正 1 处既有悬空引用 + 载入 R3 待复核闸）** | **同步**：`first_article_l8/RULES.md` **`1f8f640cac54b6f1`**（原 `058f650df4d626e6`）· `CHECKLIST.md` **`11f2621ced066390`**（原 `f58ca379dab41cbe`）· `results_template.json` **`119cd7c48b3146d2`**（原 `6b510775339bdc11` · `delivery_anchor` 三字段 → l8r2 双锚）· `INSTRUMENT_SELFCHECK.json` `540c9a55c66b053b`（**未变**）· 投递说明 **`fcf25bf201a6ba3e`**（原 `314239049f4c2ba3` → `a181e851…` → 本件）· 验收计划 **`bdc769eb6275efd1`**（原 `5e7ee0598265a233`）。**顺手订正（既有缺陷 · 引用解析审计发现）**：投递说明 §2 DFM 行悬空引用 `06_rulings/mask_accept_fix_proof.json` ⇒ 实为 **`L6/jlc_package_l8r2/07_verify/mask_accept_fix_proof.json`**（该件实体在 `07_verify/`）。**新增闸**：投递说明 + 验收计划均载 **R3 待复核闸**（`P5-L8.2` **须经监理「限定复核」通过后方可作外发/下单依据**）。**判据⑦**：外发面文件型引用 **38/38 解析成功 · 悬空 0** ✅。**锚 supersede 登记**：旧锚 `4b610bad`/`36a6b276` → `19d637c4`/`488e90a4`；tag `k2-v57-p5-outbound-pack-ready` message 内载旧锚**由此 supersede**（tag message 不可变 ⇒ **以册面为准**）。**R2-6 前置闸实测**：P5 八项全 `NOT_RUN` · **未按旧锚下单、未外发任何件** ✅。 | **#K2-59 R2-5/R2-6/R3**；CR-46/CR-62 同型 | 只改 **ENG 手制件**（外发面 + 2 文档）· **未改**交付包/阈值/测点/板/SPEC/判据/生成器 · **非新增检查齿** · 登记制 |
| **CR-68** | **【维持登记 · 非阻塞】P6 仪器自检件现判 FAIL（既有事实 · 先于本批）+ R5 可选批本轮未做之理由** | **(i) P6 仪器自检**（`tools/k2_p6_instruments_selfcheck_v1.py` · 本会话因 `CR-49` 而实跑）：现判 **`verdict=FAIL`（anchors 2/13 · baseline_ok=False）**，**改前即已 FAIL**（先跑未改版证实）⇒ **非 `CR-49` 所致**。**根因二**：**(a)** `line_anchors` 之**行号锚**钉在 **4957 行**时代之 `k2/_shared/eda_core/hs_route_model.py`，现行 = **5225 行**（`c9e1c3b4ca208482`）⇒ 行号漂移（`solve_all_v4` 4592 等）；**(b)** `baseline_reproducibility` 之**结构性不可复现** —— 基线生成器把 **pytest 墙钟秒数**写入件内（实测两次连跑 `69.04s` vs `69.89s` ⇒ sha 必异）⇒ 非仓库漂移。**处置（本轮不做）**：**禁**以改锚/改基线"修绿"（= 缩口径 C-12）⇒ **登记 · 不阻塞 · 提请监理于 P6/仪器面处置**；**未覆盖**存储件 `P6_execution/INSTRUMENT_SELFCHECK.json`（保持既有锚，待监理裁定是否重跑落库）。**(ii) R5 可选批（`#K2-59` R1 末行）本轮**未做**：理由 = 注释头行/source 需**逐件已验证文献号**方可订正（如 `STM32G0B1CBT6.yaml` 之 `Rev 6 Table 12` 属 CR-30「引证待核」），**无权威件即擅改 = 伪造引证** ⇒ 维持 **#K2-58 R5 登记**，待有权威件再行；**不改 `pins`、不改 `source` 字段**。 | 本会话实测（`CR-49` 实跑 + 基线两连跑 + 行数/锚复算）；`#K2-59` R1 末行；owner ②（禁新增检查齿/缩口径） | **只读登记** · 未改工具锚/基线生成器/存储件 · **非新增判据维/检查齿** · 不充绿 · 不阻塞 |

---
**（本块）裁定对应**：**#K2-59 R1（CR-47/63/49/51）+ R2（重出 6 条件）+ R2-5（外发面同步）+ R4（CR-62 追认）**。**报备监理 1 条（另附 v26 限定复核请求）· owner 项 0**。

### 续编 · **#K2-60 落地**（CR-69..CR-70）—— 复核通过 ⇒ 新锚生效/闸解除 · P6 仪器订正 ⇒ 自检 rc=0

| # | 条目 | 内容（事实/裁定） | 依据 | 处置红线 |
|---|---|---|---|---|
| **CR-69** | **`#K2-60 R1` 落地：`P5-L8.2` 限定复核 = PASS ⇒ 新交付锚生效 · 外发/下单闸解除** | **面变更**：① 投递说明 **`cded013974777c73`**（原 `fcf25bf201a6ba3e`）：`⚠ 待复核闸（#K2-59 R3）` → **`✅ 限定复核已通过（#K2-60 R1）`** ⇒ **可作外发/下单依据**（旧锚 l8/l7 保全为对照）· ② 验收计划 **`20eb85cb06292fec`**（原 `bdc769eb6275efd1`）：同口径解除 + 沿革注扩为 CR-65/CR-69 · ③ 投递说明 §3 内引验收计划锚同步。**现行交付锚** = `MANIFEST.json` **`19d637c4e9ed35be`** / tarball **`488e90a47d088d06`**（`revision P5-L8.2`）· supersede：l8 `4b610bad`/`36a6b276` · l7 `6ee7495d`/`0e88e107`（逐字节保全 · 仅对照）。**R2-6 前置闸**：实测 P5 八项全 `NOT_RUN` · **未下单/未外发** ✅。 | **#K2-60 R1**；#K2-59 R2-5/R3 | 只改 **ENG 手制件**（2 文档）· 未改交付包/阈值/测点/板/SPEC/判据 · **非新增检查齿** · 登记制 |
| **CR-70** | **`#K2-60 R2(a)(b)` 落地：P6 仪器订正（行号锚重钉 13/13 + 基线确定性）⇒ 自检 `rc=0` · `verdict=PASS`（判据⑦ 达成）** | **(a) 行号锚重钉**（`tools/k2_p6_instruments_selfcheck_v1.py` `52bff426fc3517df` → **`3ab3af605746fa86`**）· 13 锚逐锚重钉至**现行符号行**（**未删锚 · 未降要求**）：`hs_route_model.py` 892→**949**（B2-1 调用点）· 4406→**4592**（`def solve_all_v4`）· 4513→**4762**（`def _escape_smd_via`）· 4796→**5056**（`if args.all_v4`）· 4800→**5100** / 4842→**5101**（`m.config.chain_segments` —— **注**：原『第二路径』之 all_v4 内联分派已由 B2-2 显式分派取代 ⇒ 现两处命中皆在 all_v2 分支，**语义偏移已登记**）· 4806→**5064**（`solve_all_v4(bases)`）· `check_l3.py` 26→**43**（原**硬编码 SPEC 名**之缺陷点已由 **CR-33** 修毕；此为该串**残留处**）· 46→**62**（证据文案）· `check_qa.py` 35→**40**（needle 随 CR-33 签名形态更新：`config.spec_name()` → **`config.spec_name(`**）· `check_l1.py:193` · `routing_topology_gate.py:43` 未变 · 区间锚 `closure_check.py` 110-113→**120-125**（`DEFAULT_SPEC`/`ESCAPE_SPEC_PATH` 现于 122/123）。**(b) 基线确定性**（`tools/k2_p6_readonly_baseline_v1.py` `2e536d5a6501152b` → **`34693f01ffe7bce7`**）：墙钟规范化补 **`(M:SS)` 形态** ⇒ **两连跑逐字节同**（`655d47e2b1eed5c1` ×2 · 实测）· **判据文本未改**。**存储基线与记录锚刷新**：`BASELINE_pm_gate_k1_k2_readonly_v1.json` `91ca2cc3601bb56f`（**旧锚保全登记**）→ **`655d47e2b1eed5c1`**；`P6_execution/results_template.json` `2d119d99ced109b4` → **`0726491502765dc1`**（**仅 `baseline.sha256` 测量字段** · `invariant` 原文一字未动）。**自检件重跑落库**：`INSTRUMENT_SELFCHECK.json` `7a341b75b9310dd5` → **`fed92cb7aec48150`**（`verdict PASS` · **anchors 13/13** · `baseline_ok=True` · `byte_identical=True` · **rc=0**）。**失败可见性（非掩盖）**：新基线仍载 `exit=1` · **`failed=2`** · `crash_tail` 具名 `test_chain_no_pn_zero_spacing`（C2）· `test_board_level_consistency`（C1）—— **即已登记之能力缺口**（`K2-P6-B2T-DRAFT-PATCH-AND-DISPOSITION`「丙/FAILED · 测试仍 RED」· `SUITE_BASELINE_AND_BATCH2_DELTA_v1.json`）；在库旧基线（`91ca2cc3`）系**批 2 之前**（34 passed/34 skipped/0 failed · **未收集**该 2 测试）⇒ 本次 = **重钉至现行已登记态**（非新回退）。**提请监理**：若按 `invariant`「不得回退」之**严格读法**，该 2 失败之判据面处置属 **P6 面**，请裁定（本次未擅动判据文本）。 | **#K2-60 R2(a)(b)** · §五判据⑦；CR-68(i) | **未改判据/计划原文**（仅测量字段 + 工具锚）· 未改冻结四源/`criteria/`/板 · **未删锚/未降要求** · 登记制 |

---
**（本块）裁定对应**：**#K2-60 R1（复核通过）+ R2（P6 仪器订正）+ R5（过程）**。**（附）维持登记**：`CR-17`/`CR-22`/`CR-3`/land pattern 族 · `COV-C3`（维持前裁 · 禁 push/rewrite B 宿主）· **R5 文献批**（待权威件 · 未做正确）。**（附）T2-F6 新通道登记**（免重复试探）：`archive.org` / `web.archive.org` = **000（连接超时）** ⇒ **闭**；`www.st.com` 复核仍 **567**（与 CR-15 一致）⇒ `CR-17` 维持**登记制不可达**·不充绿。**报备监理 1 条 · owner 项 0**。
