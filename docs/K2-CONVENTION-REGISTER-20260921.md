# 口径登记册（CONVENTION REGISTER）· 2026-09-21 · #K2-53 §三-2

> **用途**：把「**已裁定为口径、非缺陷**」的跨库/跨板差异**集中登记**，供任何会话
> **先查后报**（红线：声明「新发现」前先查 `PRIOR_ART_REGISTRY_INDEX`）。
> **纪律**：登记制 = **不豁免 · 保持可见 · 不充绿**；**禁**以「不入范围」洗白为绿（C-12）。

| # | 条目 | 差异（事实） | 裁定 | 依据 | 处置红线 |
|---|---|---|---|---|---|
| **CR-1** | **J1 TX 对 P/N 反相** | K1 `J1` 符号 `TX_P` → pad **A3**（标准 = `SSTXn1`，**负触点**）· `TX_N` → **A2**（`SSTXp1`）；`TX2_P` → **B3**（`SSTXn2`）· `TX2_N` → **B2**。RX 两对极性正确。 | **口径 · 非缺陷 · 不升级** | #K2-53 §二；停机条件（TX/RX **对**交叉）**未触发**：`PCIE_TX0/1_*` 全落 **SSTX 触点**、`PCIE_RX0/1_*` 全落 **SSRX 触点** | **禁**改符号脚号（受 `k1_pinmap.yaml#J1` + `criteria.measure_pin_map` 管辖；改=设计面）；「是否有意」= L1 语义 → owner **知悉项**，不阻塞 |
| **CR-2** | **USB-C SS 对 ± 命名口径（J1-SSP-2）** | `USB_C_RECEPT_24.yaml` 的 **B 行角色**与 `USB_C_PLUG.yaml` 及 **KiCad 官方符号**相反（24.yaml: B2=SSRXp2 …）；`k1` 符号采用 host/标准口径，`key_v2` 符号采用 device/交叉口径 | **维持不统一 · 登记为口径**（host/device **视角差**） | #K2-53 §二；`24.yaml` 与自身 aliases 及 **key_v2 符号自洽**（key_v2 PIN-01 = PASS(0)） | **禁**改 `USB_C_RECEPT_24.yaml`/`USB_C_PLUG.yaml`（动它 ⇒ 触 key_v2 回归）；将来统一须**另立跨项目回归批**（key_v2+k1+k2） |
| **CR-3** | **IOCONVERT 符号表示法差** | `k2/hw/lib/IOCONVERT.kicad_sym` 的 `DS320PR1601` 变体 **194 个 pin 以 ball 名命名**（如 `AE1: AE1`）；`k2/hw/lib/DS320PR1601.kicad_sym` 同 ball = `GND`（信号名） | **登记制：不豁免 · 保持可见 · 不充绿**；**不入 K2 门禁链判据**（`k2/pipeline.yaml` 无 pinmap 检查） | #K2-53 §二 | **禁**改任何 `.kicad_sym`（改符号 = 设计面 = 须 owner）。PIN-01 读数：该库 **1 → 194**（可见、不隐藏） |
| **CR-4** | **tier2 出处不可约下界** | `parts` 真源三件套：标准件 5 + 约定件 6 + 语义件 1 = **12 件结构性无三件套**；余 6 件外部通道**强时效**（本轮 diodes/atta/liteon/molex 全封） | **「12 件 = 不可约下界」登记为口径**；tier2 裁定时 **15/33**；余 6 件**具名 PARTIAL**（**读数后经 CR-5 更新为 17/33**） | #K2-53 §二 | **禁**把「可达上限 21/33」作为**任何判据/绿判**；「软目标」**仅**作排期用语；**禁每轮全量重探**（改按需） |

---
**登记口径说明**：以上均**不影响** P6 判据面与交付锚（`6ee7495de61f749f` 未动）；
`criteria/` **只读未动**（判据 **rev=6**）。

### 续编（本会话 · 2026-09-21 · 状态列已注明「待监理裁定」者以裁定为准）

| # | 条目 | 差异（事实） | 状态 / 裁定 | 依据 | 处置红线 |
|---|---|---|---|---|---|
| **CR-5** | **tier2 读数更新（新通道）** | 经新通道 **Digi-Key 媒体镜像 `media.digikey.com`**（≠ `www.digikey.com` 403）取回：**OPTO_LTV356T**（Lite-On 原厂 · sha256 `e340ba0a…` · p2 图例 1 Anode/2 Cathode/3 Emitter/4 Collector ⇒ 与 repo 4/4 一致）· **STM32G0B1KBU6**（DS13560 p45 Figure 12 · 32/32 归一一致 · EP=VSS） | **读数 15/33 → 17/33**（**具名 · 不充绿**）；余 4 件仍不可达 | #K2-53 §二 T2-F6 ④『按需重探（有新线索才试）』；证据 `T2F6_NEWLANE_PROBE_20260921_v2.json`（f609d256eb30d822） | **禁**把读数作判据/绿判；**禁**每轮全量重探；外部原件仅落 `/tmp/opencode` |
| **CR-6** | **pciesw4 覆盖面 · 口径订正（COV-C1）** | 范围外**未覆盖**目录 = **4 个（全在 pciesw4 · 39 件 .kicad_sch）**；此前 `handoff §3`/`P6_STAGE_FACE_RECHECK` 所列的 `k2/hw/sch` 与 `key_v2/key_v2/sch` **实为已覆盖**（`k2/pipeline.yaml`、`key_v2/key_v2/pipeline.yaml`）；dim 文本『范围外 **47**』= 范围外**文件数**，≠ 未覆盖目录数。k2 域内未覆盖 = **0** | **口径订正登记**；方案 **待监理裁定**（option_B：pciesw4 自持 pipeline.yaml ／ option_A：criteria 显式 out_of_scope 登记） | `PCIESW4_COVERAGE_MANIFEST_PROPOSAL_20260921_v1.json`（85f879087be9a943） | **禁**由 ENG 自改 `criteria/`；**禁**以「不入范围」洗白为绿 |
| **CR-7** | **补丁类证据须记「前像/后像」（COV-C2 · 检查缺环）** | v19/handoff 之『补丁目标 `_shared/…/hs_route_model.py` sha16 `c9e1c3b4ca208482` **仍匹配**』属**自比**（记录值 = 现树值）⇒ **无法区分**『未应用』与『已应用』；实测真前像 = `dcd1f65f4b549527`、现树 = 补丁**后像** | **登记为检查缺环**（证据工艺）；**不新增检查齿** | `BATCH6_V4_RELEASE_PRECHECK_20260921_v1.json`（fa4e15eafad1acb7） | 补丁证据须同时记**前像 sha** 与**后像 sha**，并以正/反向 `dry-run` 佐证可落/已落 |
| **CR-8** | **批 6 v4 已在树内（待裁-3 前提订正）** | 对已提交 `_shared/eda_core/hs_route_model.py`：正向 `patch --dry-run` ⇒『previously applied』**10/10 hunk 忽略**；反向 `-R --dry-run` ⇒ **RC=0** ⇒ 该文件 == `BATCH6_LANDING_CANDIDATE_v4.patch` **后像**；`git -C _shared log -1` = **ea2b746**（批 6 落件 · 提交信息含『R-10 退化候选守卫 · (d)对角线』） | **待监理裁定**：**(i) 追认** v4 已随 v3 生效（ENG 倾向）／(ii) 若 v4 须与 v3 区分 ⇒ 给出真实前像 | 同上（fa4e15eafad1acb7） | **禁**重复应用补丁（会失败/污染）；**禁**无裁定改动 `_shared` |
| **CR-9** | **四树引擎同步现状** | `hs_route_model.py`：`_shared` = `k2/_shared` = `c9e1c3b4…`（5225 行 · 批 6）✓；**`key_v2/_shared` = `883525b4…`（3849 行 · 末次 8f58466 = M13 v8）**、**`pciesw4/_shared` = `6ab5eaaa…`（4121 行 · 末次 d24eb0b = M13 W6-D）** ⇒ 落后 1823/1558 行 diff | **待监理裁定**：(a) 各自钉版（登记口径）／(b) 另立跨项目同步批次（ENG 倾向 b）；**K2 面无影响** | `FOUR_TREE_ENGINE_SYNC_CENSUS_20260921_v1.json`（4e2a2cd0fa4032cf） | **禁**由 ENG 越项目改 key_v2/pciesw4 树；登记制 = 不豁免 · 保持可见 |
