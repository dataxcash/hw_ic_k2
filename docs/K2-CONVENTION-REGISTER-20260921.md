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
