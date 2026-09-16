# K2 · P4 门前置 —— **判据可达性** 问题件 v1（ENG → 监理，请裁）

> **缘起**：续接会话按 handoff §7 执行（核监理两项 + L2 自裁域收口）时，用**冻结仪器**
> `criteria/adjudicate.py`（`897e8bfde60e2cfe`，**只读**）自跑交付板 `k2/hw/k2_v4_8L.l4.kicad_pcb`
> （`d4e81f647be7f980`），复核 **P4 完工前置（handoff §7.3「`criteria` 全 J 类绿」）的可达性**。
> **边界**：本件**不新增判据维度**、**不改** `criteria/`（ENG 只读）、**不加检查齿**；只报 1 处**结构不可达**
> 与 1 处**未点名**，请监理在 **P4 开工前**裁定 —— 否则 P4 完工后仍判 FAIL。
> **复跑**（纯只读，输出仅 `/tmp`）：
> `python3 criteria/adjudicate.py --board k2/hw/k2_v4_8L.l4.kicad_pcb --manifest criteria/manifest.k2.yaml --measure-out /tmp/opencode/k2u2/meas.json --out /tmp/opencode/k2u2/verdict.json`

## 1. 【A · 必改】`zone_filled` 判据**结构不可达**（口径转录错误；与 #K2-17 §二/§4-1 冲突）

- **应然（登记册，owner 批）**：`.omo/supervision/ledger/K2-DEFECT-REGISTER-v1.md` §C
  **J-3「铺铜全填充」现值写 `0/9`** ⇒ 目标 = **9 个铜区**全填充
  （= **#K2-17 §二** C7 修正口径 = **#K2-17 §4-1** 监理自纠「原 13 区口径为监理笔误」）。
- **判据实现（现状）**：`criteria/manifest.k2.yaml:20`
  `zone_filled: {enabled: true, expect: "filled_zones == total_zones"}`；
  `criteria/adjudicate.py:73-81` 的 `zones_total = len(全部 zone 块)` ⇒ **未排除 keepout rule area**。
- **冻结仪器自跑（l4）实测**：`zones_total = 13` / `zones_filled = 0`；13 = **4 个无网 `F.Cu` keepout**
  （`ESC_J2/J3/J4/U6`：`net = None`、`keepout = True`、`filled = 0`）
  + **9 个铜区**（`In1/In3/In6 = GND`；`In4 × 6 = 12V_IN / MCU_VDD / P3V3 × 2 / P3V3_AUX × 2`）。
- **不可达证明**：keepout rule area 在 KiCad 语义下**不可能**有 `filled_polygon`；
  且 **IN-7 / P3-5（板侧）要求这 4 区存在且 ≥1 非 `allowed`** ⇒ 这 4 区**既不能删、也不能填**。
  故 P4 铺满 9 铜区后，`zone_filled` 恒为 **`9/13` ⇒ FAIL**。
  ⇒ **P4 完工前置在现状判据下不可达。**
- **建议补丁**（判据归属方落；ENG 因红线只读 `criteria/` 不自行改）：
  ```python
  zc = [z for z in zf if z['net'] and not z['keepout']]     # 只计有网铜区（=9）
  m['zones_total'] = len(zc)
  m['zones_filled'] = sum(1 for z in zc if z['filled'] > 0)
  ```
  影响面已核：`zones_total` / `zones_filled` **仅**被 `:209-210` 的 `zone_filled` 消费（grep 零其他引用）；
  `keepout_all_allowed`（`:82`）继续用全量 `zf`，不受影响。
- **为何正/负控未抓到**：l4 现值 `0/13` 与应然 `0/9` 的**分子同为 0** ⇒ 负控只能证「未填 ⇒ FAIL」，
  无法区分分母；该转录缺陷**只在填充后**暴露（与 #K2-17 §4-1 同型：判据须可复现且不自指）。

## 2. 【B · 登记确认】5 件接口件 **0 pad** ⇒ `device_has_pads` 必 FAIL；请确认纳入 P4 批

- **实测 l4**：`J6 / J9 / J11 / J12 / J13`（`ForgeOS:PinHeader_1x02 / 1x04`）**`pad = 0`**（其余 37 件 ≥1）。
- **判据** `device_has_pads`（`every_footprint_pads >= 1`，`manifest.k2.yaml:21` / `adjudicate.py` 对应分支）
  ⇒ 现状 ``FAIL``；**若 P4 不补这 5 件的 16 pad，P4 完工后仍 FAIL**。
- **已登记（非新发现）**：`k2/docs/K2-P4-board-side-defect-register-v1.md`（`337a24a5ec4e70ee`）§3
  「5 排针 **16 pad**」（E3 板侧 57 项之一；同源 `K2-P2-E3-rootcause-breakdown-v1.md`）。
- **请求**：P4 输入前置 `K2-P4-INPUT-PREREQUISITES-v1.md`（v3 `20b6775f6daa1350`）的 **IN-1..IN-9 只点名 `U1`（IN-4）**，
  **未列这 5 件连接器** ⇒ 请**补录为 P4 输入项**（或明示由哪一 IN 承载），否则 `device_has_pads` 不可达。

## 3. 不需处置（登记册已录现值 ⇒ 属已知在册，非本件发现）

- **J-5 非 45° 段**：登记册 §C **已录现值 `2051`**（本轮实测 `2051/2512`，逐值一致）⇒ 已知在册。
- **J-2 连通（补铜后）`178`** · **J-4 丝印全 ignore** · **J-7 封装 mismatch `41`** · **J-6 `64 缺 / 3 幽灵`**：
  登记册 §C 均已录现值；`J-1 DRC 42 全 warning`、`J-8 器件位置合理性「未定义」`、`J-9 门禁接入「无」`
  亦在册 ⇒ 本件不重复报。

## 4. 边界与证据

- **未改**：`criteria/` 两份（`897e8bfde60e2cfe` / `7ce08757eff25557`，0444 只读）· 全部冻结件
  （`d4e81f64` / `fb07d25a` / `dd794c54` / `SPEC rev-19..24` 原件 / `L1·L2 frozen`）· 未写 `.omo/supervision/**` · 未派 WORKER。
- **本轮运行产物**（易失，仅留痕）：`/tmp/opencode/k2u2/{meas.json, verdict.json, cli.out}`（`rc=1`）。
