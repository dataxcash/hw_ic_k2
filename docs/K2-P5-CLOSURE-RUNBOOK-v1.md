# K2 · **P5 关门执行序（ENG 侧 runbook）** · v1 · 2026-09-21

> 依据：`k2/docs/K2-RECTIFICATION-PLAN-v1.md` §P5 · owner **#14③**（完工定义）· 验收计划 §5 **责任边界（实测方执行 · 判定归监理）** · 监理 **#K2-60 R1 / #K2-61 §四-5 / #K2-63**（CR-17 i-a · CR-75 i-a · CR-74 保留）。
> **本件只写 ENG 侧执行序**（材料打包 / 回件受理 / 判后落件）；**不定义判定标准**——**判定权归监理**（`results_template.json::judged_by = 监理`）。零新增判据维 / 零检查齿。

## 0. 一句话
外部首件回件到达 ⇒ **(1) 先跑守卫做成受理件** ⇒ **(2) 交监理判定** ⇒ **(3) 判定为 PASS 后按 §3 机械落件关门**。任一环节 fail-closed ⇒ **不静默放过**。

## 1. 回件受理（ENG · 每次回件必跑）
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
python3 tools/k2_p5_results_intake_guard_v1.py <回件.json> --json-out /tmp/opencode/p5_guard/<id>.json
```
- **rc = 0（可判）** ⇒ 把回件 + 守卫报告（含 sha256）**连同原始证据件**交监理判定。
- **rc = 1（不可判）** ⇒ 按报告逐条**向实测方追问补件**（**补件 = 补充件 + sha256；补件 ≠ 重出包 · 零锚**）：
  | fail-closed 项 | 处置 |
  |---|---|
  | `delivery_anchor.manifest_sha256`/`tarball_sha256` 不符 | **停**：首件可能非出于本包 ⇒ 先澄清实测量的是哪一包（**冲突即停机**） |
  | `measured_by` 空 / 疑为 ENG | 补具名实测方（**不得 ENG 自证** · 验收计划 §5） |
  | `V6-1.condition` 空 | 补主判工况（`#K2-55`：独立运行 · `J13/VCC` 不接外供） |
  | `V5.P3V3_AUX` refdes 缺 / 非 `J3`/`J4` | 补测点 refdes（**CR-75 零锚处置**） |
  | 证据缺 sha256 / 不符 | 补原始件 + sha256（RULES §0.2） |
  | 状态仍 `NOT_RUN` / 读数缺失 | 补测或声明 `INCONCLUSIVE`（**禁留空**） |
- **仅 warn 项**（不阻断可判）：`DBGMCU_IDCODE` 未载（模板无该槽）· V5 电流来源未声明 · V6-1 辅助读数未记 ⇒ **建议一并追问**。

## 2. V6-2 判读口径（`#K2-63` 采纳 i-a · **仅判读层**）
- `SW-DP IDCODE` 期望 **`0x0BC11477`**（Cortex-M0+ CoreSight）。
- `DBGMCU_IDCODE`(**0x40015800**) 取 **DEV_ID（低 12 位）** 期望 **`0x467`**（STM32G0B1 = G0Bx/G0Cx = ST 分类 CAT3）；**REV_ID（高位）随批次不计**。
- **引证等级（须并列标注）**：`上游工具件共同值 · 非原厂手册`（stlink `inc/stm32.h` `STM32_CHIPID_G0_CAT3=0x467` · `config/chips/G0Bx_G0Cx.chip` `chip_id 0x467` · OpenOCD `tcl/target/stm32g0x.cfg` DBGMCU@`0x4001580x`；RM0454 原厂页 567/429 不可达）⇒ **不充绿**。
- **不符处置**：**不直接判 FAIL**（引证等级非原厂）⇒ 记『异常读数 · 须复测/查原厂手册确认』。

## 3. 判后落件（监理判 PASS ⇒ 机械执行；判 FAIL ⇒ 走 §4）
1. **TAG**（`pm_gate/TAG_POLICY.md` §1「发布候选/交付」+ §3 message 必含）：
   ```bash
   cd /home/fila/jqdDev_2025/ic_hw/k2
   git tag -a k2-v57-p5-first-article-pass -m "P5 first-article PASS · 交付锚 <MANIFEST sha16>/<tarball sha16> · 受审板 7a5c89913d6e5d0a · SPEC <SPEC sha16> · criteria rev=6 · 判据 <裁定号> · <date>"
   git push origin --tags && git ls-remote --tags origin | grep k2-v57-p5-first-article-pass
   ```
   **核验**：`^{}` 解引用须指向目标 commit（§4·§5）。
2. **关门记录**：落 `P6_execution/P6_OPEN_READINESS/K2_P5_CLOSURE_<date>_v1.json`（含：裁定号 · 守卫报告 sha256 · 回件与全部原始证据 sha256 · 8 项读数与监理判定 · 具名披露（CR-17 引证等级 · CR-75 补件 · ACCEPT 项））。
3. **册面**：`K2-CONVENTION-REGISTER-20260921.md` 记『P5 关门』条目 + 现行交付锚（**锚不变**：`19d637c4e9ed35be`/`488e90a47d088d06`；**未重建包**）。
4. **推送核验**（TAG_POLICY §5）：`k2` 先 `0/0` ⇒ 父仓 pointer bump ⇒ 父仓 `0/0`；冻结四源 SHA 不变。
5. **ledger**：`.omo/start-work/ledger.jsonl` 记 `tag 名 + 目标 commit + gate`（§6）。

## 4. 判 FAIL 的处置（计划 §313–314）
- 按**失败项回 P3/P4**（**不回退 P5 之前的绿**）；**已花的打样费 = 已购买的证据，不隐藏**。
- **禁**为变绿**缩口径**（C-12）· **禁**调阈值替代整改 · **禁**改 `criteria/`。

## 5. 边界
- ENG **不自证**（验收计划 §5）；判定归监理。
- 本序**不动**交付包/交付锚（判 PASS 亦**不重建包**）。
- 临时/外部落点仅 `/tmp/opencode`；正式落件在仓库内。
