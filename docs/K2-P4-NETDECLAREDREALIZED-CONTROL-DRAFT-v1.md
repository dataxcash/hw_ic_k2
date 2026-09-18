# K2 · P4 · **`net_declared_realized` 正/负控补齐 ＋「声明口径 ≠ 实判口径」结构发现** · v1 · 2026-09-18

> 缘起：handoff inc73 §6-3-**(ee)**「`net_declared_realized` 正/负控补齐（inc71 只读扫描未命中其控制语境 ⇒ `/tmp` 造件补正控+负控）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读取证 + /tmp 造件 + 纯文档**，仓库判据/真源/共享层零改动（仅新增本证据件）。
> 锚：在库判据 `criteria/adjudicate.py` **`897e8bfde60e2cfe`** · 在库清单 `criteria/manifest.k2.yaml` **`7ce08757eff25557`**（9 维、`not_countersigned: true`）·
> v4 草案判定器 `k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py` **`1cda68521d0e56be`** · 受审板 `6ff49da5678c2108` · 真源 `dd794c54f7ce7417`。

## 0. 结论（4 条；第 2 条为新结构发现）

1. **正/负控已补齐（4 案）**，全部由**真判定器** `criteria/adjudicate.py` **端到端**跑出（非自造复现），两次独立复跑**逐字节相同**：
   | 案 | 构造 | 期望 | 实测 |
   |---|---|---|---|
   | **正控** | 声明 3 网、板上 2 pad/网全落地（`nets_with_zero=0`） | PASS | `net_declared_realized` **OK** · rc=**0** |
   | **负控（0 焊盘）** | 同声明，板上 1 网 pad 无 net（`nets_with_zero=1`） | FAIL | **FAIL**「板上 0 焊盘的声明网 = 1；<2 焊盘 = 1」· rc=**1** |
   | **负控（缺网表，fail-closed）** | 不传 `--nets` | FAIL | **FAIL**「缺少网表（fail-closed）」· rc=**1** |
   | **分歧案（1 焊盘）** | 1 网声明 2 节点、板上仅 1 落地（`nets_with_zero=0`、`nets_with_lt2=1`） | **（本应 FAIL）** | **OK / rc=0** ⇒ 见第 2 条 |
2. **【结构发现】该维「声明口径 ≠ 实判口径」**：manifest `expect: "every_declared_net_pads >= 2"`，但判据**只 gate** `nets_with_zero == 0`；`nets_with_lt2` **仅出现在 detail 串、从不入门**（`criteria/adjudicate.py:230-233`；v4 草案 `adjudicate.draft-v4.py:258-261` **同型**）。
   ⇒ **声明"每网 ≥2 焊盘"被违反时判据仍 PASS**。实板复算（真源）：`nets_with_zero=0`（OK）而 **`nets_with_lt2=1`**（`PWR_5V_KEY` 仅 `C89/A`）⇒ 与 owner 铁律 §一「以**关判据 / 缩口径**达成绿 ⇒ C-12 同型，禁」**同族**，且**同时存在于在库判定器与 v4 草案**（不是草案新引入）。
3. **须监理择一（ENG 不择一）**：
   - **(a) 改判据**：gate 收紧为 `nets_with_zero == 0 ∧ nets_with_lt2 == 0` ⇒ 实板**必转为 FAIL**（先决 = ⑤ 裁定 `C89/A`）；
   - **(b) 改清单**：`expect` 改为 `every_declared_net_pads >= 1`（或「0 焊盘的声明网 == 0」）⇒ 承认单节点网为**具名注记**（须与 ⑤ 的「伪网」定性一致）。
   两案都**须监理落 `expect` 文字 + 锚 rev**；本件只把分歧摆平，不代裁。
4. **控制装置与复跑命令已备**（§3；`/tmp` 易失可重建）。

## 1. 判据实现（行号定位，两树同型）

| 文件 | 计算 | gate |
|---|---|---|
| `criteria/adjudicate.py`（在库） | `:145` `nets_with_lt2 = sum(1 for r in rows if r['realized'] < 2)` · `:146` `nets_with_zero = ...` | `:230` `if C.get('net_declared_realized',{}).get('enabled')` · `:232` `chk(..., nr['nets_with_zero'] == 0, f"...；<2 焊盘 = {nr['nets_with_lt2']}")` |
| `adjudicate.draft-v4.py`（草案） | `:172` / `:173`（同式） | `:258` / `:260`（同式） |
| 测量来源 | `measure_declared_nets_realized(nets_yaml, board_m)`：逐声明网按 符号 pin_name→ball 映射 统计板上落地 pad 数 | — |

即：**`nets_with_lt2` 是"报告项"，不是"判定项"**。

## 2. 实板复算（受审板 `6ff49da5678c2108`）

| `nets_yaml` | `net_declared_realized` 读数 | 判定 |
|---|---|---|
| 真源 `dd794c54f7ce7417` | 0 焊盘的声明网 = **0**；**<2 焊盘 = 1** | **OK**（声明 `>=2` 已违反） |
| `errata-2` 草案 `bdacbf944ca0c796`（删 `PWR_5V_KEY`） | 0 焊盘的声明网 = 0；<2 焊盘 = **0** | OK |

> 与 **(cc)** 件互补：删 `PWR_5V_KEY` 会让 `nets_with_lt2` 归 0 —— 这也解释了「为什么甲看起来"更干净"」；但**根因在判据口径**（第 2 条），不在真源。

## 3. 控制装置（/tmp）与四案输出

装置（`/tmp/opencode/inc74/ee/`，可重建）：

| 件 | sha16 | 说明 |
|---|---|---|
| `nets.yaml` | `b3ffddfc38a46767` | 声明 `NET_A/NET_B/NET_C`，各 2 节点；符号 `RES_2` 三引脚映射 |
| `manifest.min.yaml` | `bd93078c2ca730c2` | **只**启用 `net_declared_realized`（隔离该维） |
| `clean.kicad_pro` | — | 空 `rule_severities`（令无条件维 `rule_severity_manifest` 不干扰） |
| `board_pos.kicad_pcb` | `db96f34926d74f00` | 正控板：3 网全落地 |
| `board_lt2.kicad_pcb` | `f232e9504cb4c25f` | 分歧案：`NET_C` 仅 1 落地 |
| `board_neg.kicad_pcb` | `aeac6310166e482a` | 负控板：`NET_C` 0 落地 |
| `v_pos.json` / `v_neg.json` / `v_lt2.json` / `v_none.json` | `8a85811f9bcbcbf0` / `110410570771f47d` / `b9f767683c400a32` / `12043d42451a064e` | 判定输出（无假造；由真判定器生成） |

实测输出（节录，逐字来自 verdict JSON）：

```
正控 : [OK]   net_declared_realized | 板上 0 焊盘的声明网 = 0；<2 焊盘 = 0      => PASS
分歧 : [OK]   net_declared_realized | 板上 0 焊盘的声明网 = 0；<2 焊盘 = 1      => PASS   ← 声明 >=2 被违反仍 PASS
负控 : [FAIL] net_declared_realized | 板上 0 焊盘的声明网 = 1；<2 焊盘 = 1      => FAIL
缺网表: [FAIL] net_declared_realized | 缺少网表（fail-closed）                  => FAIL
      declared_nets rows(NET_C) = {"net":"NET_C","declared_nodes":2,"realized":1}
```

**确定性**：正/负/分歧三案各跑 2 次，`measure JSON` 与 `verdict JSON` 均 `cmp` **IDENTICAL**。

## 4. 复跑

```bash
cd /home/fila/jqdDev_2025/ic_hw
W=/tmp/opencode/inc74/ee                     # 易失：重建件
python3 /tmp/opencode/inc74/inc74_gen_boards.py $W   # 生成器；实测与 §3 三块板**逐字节相同**（cmp IDENTICAL）
for c in pos lt2 neg; do
  python3 criteria/adjudicate.py --project ee --manifest $W/manifest.min.yaml \
    --board $W/board_$c.kicad_pcb --nets $W/nets.yaml --pro $W/clean.kicad_pro \
    --root $W --measure-out $W/m_$c.json --out $W/v_$c.json ; echo "board_$c rc=$?"
done
python3 criteria/adjudicate.py --project ee --manifest $W/manifest.min.yaml \
  --board $W/board_pos.kicad_pcb --pro $W/clean.kicad_pro --root $W \
  --measure-out $W/m_none.json --out $W/v_none.json ; echo "no-nets rc=$?（期望 1）"
# 实板两口径
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --nets k2/hw/data/k2_sch.yaml --root k2 2>&1 | grep net_declared_realized
```

## 5. 边界

本件**只读取证 + `/tmp` 造件 + 纯文档**：未改 `criteria/**`（**未就地改判据**）、`_shared/**`、真源、板、pro、SPEC、生成器、模板、图纸、库、`fp-lib-table`、`pm_gate/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**（owner ②：本件不新增维度，只补既有维的控制与口径证据）。
—— ENG（ARCHER）· 2026-09-18 · 在库判据 `897e8bfde60e2cfe` · 受审板 `6ff49da5678c2108`
