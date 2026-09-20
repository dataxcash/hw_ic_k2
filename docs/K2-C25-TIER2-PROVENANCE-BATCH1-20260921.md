# K2 · **C-25 tier2 首批取证报告**（器件手册出处三件套）· 2026-09-20

- 授权链：**#K2-47 §三**（C-25 登记）→ **#K2-48 §一 N-5/C-25**「tier2（器件手册出处三件套）**排期**」；
  **本轮无新裁定**（最新仍 #K2-49），故按已批准计划推进 tier2 **数据面**（不改判据/生成器/SPEC/原理图，不越阶段门）。
- 证据件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/C25_TIER2_PROVENANCE_BATCH1_20260921_v1.json`
  （sha16 `465d2cc930ecfe2b`）· 草案 v3：`k2/docs/drafts/c25-external-truth-v1/criteria__parts_electrical_truth.yaml`
  （`c6de696df205c829` → `3d174baa3510f763`，**tier1 逐字节未改**，已断言）。
- 方法：`curl` 取厂商原件 → `%PDF-` magic + 尺寸 + `pdftotext` → **doc_id/产品名令牌机检命中** → `sha256`；
  失败者一律**不填 sha**（禁充绿），按类别具名登记。

## 一、读数（33 件 sch_gate 器件）

| 类别 | 件数 | 处置 |
|---|---|---|
| **三件套已取证**（`doc_url`+`doc_sha256`，机检命中） | **9** | DCDC_12V_3V3 · DCDC_12V_5V · DS160PR810 · TPS22919 · FUSB302 · LDO_5V_3V3 · SE050C2 · TPD6E05U06 · TS3USB221A |
| 付费/注册**标准件**（无合法免费全文） | 5 | JEDEC JESD84-B51 · PCI-SIG M.2 / OCuLink · SNIA SFF-TA-1016 / SFF-8654（以标准号 + 官方条目页为出处） |
| **设计约定/通用封装**件（无厂商件） | 6 | 24MHz_9pF · J_EC_HEADER · J_OOB_HEADER · LED_DUAL · UART_DEBUG · XO_100M |
| 厂商直链**自动化不可达**（待人工取件） | 12 | BAT54C · FRU_EEPROM · PI3DBS16412 · STM32G0B1CBT6 · STM32G0B1KBU6 · OPTO_LTV356T · USB3.0_Type-A_90 · USB_C_PLUG · USB_C_RECEPT · USB_C_RECEPT_24 · PMIC_P1 · SOM_B1 |
| 非器件（语义件） | 1 | `strap_semantics.yaml` |

- tier2 前：**0/33** 具三件套（REGISTRY ONLY）⇒ 后：**9/33 已取证** + 24 件**具名分类**（无一件含糊）。
- 独立复核：`python3 -m eda_core.truth_binding check-dimensions --manifest criteria/manifest.k2.yaml` ⇒
  **19/19 维已声明 · 违规 0 ⇒ PASS**（criteria 未动，装态零回归）。

## 二、发现（具名，供监理处置）

- **T2-F1（中）引用号与厂商当前件不符**：`TPD6E05U06` 仓内引 `SLLSE95` ⇒ 实测 **`SLVSBO7O`**（2024-08 Rev）；
  `TS3USB221A` 仓内引 `SCDS239A` ⇒ 实测 **`SCDS277C`**（2024-10 Rev）。两件**产品名**在 PDF 全文命中
  （89×/55×）⇒ 同件、文献号漂移/笔误。**修法** = `_shared/eda_core/sch_gate/datasheets/*.yaml` 的 `source:`
  订正（属 `_shared` 件 ⇒ 须监理批 + 同批升版）。
- **T2-F2（低）5 件标准件**（JEDEC/PCI-SIG/SNIA）**不可能有免费全文 sha** ⇒ 三件套对它们**不适用**；
  出路 = 标准号 + 官方条目页，或内部获授权副本（涉 owner/法务面）。
- **T2-F3（低）6 件设计约定件** ⇒ 三件套不适用（出处 = 设计定义 + 封装标准）。
- **T2-F4（中）12 件厂商直链不可达**（ST 端点 567 反自动化 · onsemi/Diodes 403/404 · Molex HTTP/2 中断 ·
  usb.org 版本化文件名 404 · SpacemiT 无公开直链）⇒ 出路 = **人工浏览器取件或分销商镜像**（半自动）。

## 三、边界与下一步

- 本轮**未写 `criteria/`**（ENG 只读）· 未改生成器/SPEC/原理图 · 未派 WORKER · 外部件仅落 `/tmp/opencode`。
- 完成度上限（诚实口径）：三件套最多可覆盖 **9 + 12 = 21/33**；另 12 件（5 标准 + 6 约定 + 1 语义）**永不可得**，
  须由监理裁定「以标准号/设计定义为出处」是否满足 C-25 三件套口径（**监理自裁项**）。
- 建议序：①T2-F1 引用号订正（须批）②12 件人工取件 ⇒ 达 21/33 ③tier2 收口后由 gate 属主**另立 criteria rev**。

—— ENG（ARCHER）· 2026-09-20 · `k2` 本次提交 · 判据 **rev=6**（只读未动）· 交付锚 `6ee7495de61f749f` 未动
