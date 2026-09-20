# K2 · C-25 tier2 续证（batch4）：半自动通道重开 + 3 件新取证

- 机读件：`pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/C25_TIER2_PROVENANCE_BATCH4_20260921_v1.json`（sha16 `1fb516b75e7786a2`）
- 前置：batch1（9 件）+ batch2（USB-IF Type-C R2.5 ×3）= **12/33**；batch3 判 `automation_lane_closed=true`
- 授权依据：handoff §7-2『余 9 件人工/镜像取件』· 红线『外部取件仅落 /tmp/opencode』·『未改 criteria/』
- 日期：2026-09-20 · ENG（ARCHER）

## 一、新取证（3 件，12 → **15/33**）

| device | doc_url | sha256(前16) | bytes | doc_id 令牌命中 | 通道 |
|---|---|---|---|---|---|
| BAT54C | `diodes.com/datasheet/download/BAT54C.pdf` | `50b04e4e17bcf5db` | 502,635 | BAT54C×3 · "BAT54 /A /C /S"×10 | vendor download 路由 |
| FRU_EEPROM | `ww1.microchip.com/.../AT24C01C-AT24C02C-...-20006111A.pdf` | `b6466f4cce6d4ed5` | 1,203,643 | AT24C02C×80 · 20006111×46 | vendor 直链 |
| STM32G0B1CBT6 | `atta.szlcsc.com/upload/public/pdf/source/20210707/C2829307_….pdf` | `9fc2cfec9a1c8d5c` | 2,632,172 | **DS13560×159** · STM32G0B1×207 | **中文镜像通道** |

三件均：`%PDF` magic + `pdftotext` 可解析 + 文献号/产品名机检命中。**禁充绿**：未解析者一律不填 sha。

## 二、方法面发现（T2-F6，中）

**batch3 的 `automation_lane_closed=true` 不成立。** 存在两条**可复现的半自动取件通道**：

1. **vendor `.../download/<PART>.pdf` 路由** —— `diodes.com/datasheet/download/BAT54C.pdf`、`ww1.microchip.com/downloads/...` 实测 `200 application/pdf`。
2. **中文镜像通道** —— **Sogou**（可达）检索 → `atta.szlcsc.com`（PDF 直链）/ `file.elecfans.com`（PDF）实测 `200 application/pdf`；`item.szlcsc.com` / `21icsearch` 可反查 vendor 直链。

⇒ tier2 余量**不必纯人工**，可脚本+检索半自动推进至可达上限 **21/33**。

## 三、引证面发现（T2-F7，中）

`STM32G0B1KBU6` 引证文献号 **ST DS12872**，实测厂商表 **DS13560** 逐字列出 `STM32G0B1KB` 覆盖料号，且含专节 `STM32G0B1KxU UFQFPN32 pinout`(Fig 12) ⇒ 正确数据表 = **DS13560**（同 T2-F1 族，`_shared` 订正须批）。

> 本件同时触发高严重度发现 **KBU6-PINROT-1 / K1-D13**（该 YAML 脚 25..32 旋转），另见 `K2-STM32G0B1KBU6-PIN-ROTATION-DEFECT-20260921.md`。

## 四、batch4 后仍缺（6 件）

| device | 阻塞特征 |
|---|---|
| PI3DBS16412 | diodes 直链 500/404；alldatasheet 系 403 |
| OPTO_LTV356T | liteon 端点 000；elecfans 无条目(404) |
| USB3.0_Type-A_90 | usb.org 无 3.0/3.2 基规公开直链 |
| PMIC_P1 · SOM_B1 | SpacemiT 无公开直链 |
| USB_C_PLUG(Molex 105444-0001) | molex.com 网络面 000（21icsearch 可反查直链但端不可达）|

## 五、下一步

1. 沿 batch4 半自动通道续取 PI3DBS16412 / LTV356T / Molex（优先）。
2. T2-F7（及 T2-F1）引证订正：`_shared` `source:` —— **须批 + 同批升版**。
3. tier2 收口后由 gate 属主另立 criteria rev（标准件 5 + 约定件 6 + 语义件 1 = 12 结构上无三件套）。
