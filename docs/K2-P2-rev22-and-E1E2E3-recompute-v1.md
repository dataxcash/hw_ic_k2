# P2 · rev-22 落地 + E1/E2/E3 源侧面复算（交监理判「正式关门」）v1

> **依据**：监理 **#K2-14** §二（2-A′ 裁「是」：LQFP48/`STM32G0B1CBT6` 为设计意图，**不升级 owner**）+ §四 第 1/2 步。
> **边界**：本件只读复算 + 仅改 SPEC 版本链新件与重指向；**未动**板/原理图/真源 yaml/生成器/`criteria/`；未派 WORKER；输出（仪器）仅 `/tmp/opencode`。

## 1. rev-22 落地（仅 2 字段 + 溯源卡）

| 项 | 值 |
|---|---|
| 新件 | `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-22.json` |
| sha256(16) | **`9f0179e2afb7d766`** |
| 前身（逐字节未动） | `SPEC_k2_v4.spec-rev-21.json` `d46bd017aa560716` |
| canonical 重指向 | `k2/pm_gate/project.yaml: spec_name → SPEC_k2_v4.spec-rev-22.json`（`06a6038acf41cd2c`） |
| 指引更新 | `k2/pm_gate/artifacts/k2_v4/L3/README-canonical.md`（`b3ca8e5d4e2b8383`） |

**改动面（逐叶深比对，机器验证）**：变化 **3** 个叶 = `spec_version`（`1.1.spec-rev-21` → `-22`）、`components.mcu.U1.footprint`（`ForgeOS:MCU_STM32G0_QFN32` → `..._LQFP48`）、`components.mcu.U1.value`（`STM32G0B1KBU6` → `STM32G0B1CBT6`）；**新增 2 个留痕块** = `_spec_rev_12` 卡 + `components.mcu_entry_fix_v22`（更正依据：真源自洽 LQFP48 / 板 pad→网 = LQFP48 资产 7 命中 0 不符 / 板实例仅 pad 1..33 / K1 用 QFN32）；**删除 0**；其余全叶逐值相同。
**原件保护**：`rev-19` `5f72182a2616392c` / `rev-20` `37dcd9cde5ceed09` / `rev-21` `d46bd017aa560716` 复算**逐个未变**。
**解析链探针（经官方路径，非硬编码）**：cwd=`k2` 时 `pm_gate.config.spec_name('k2_v4')` → `SPEC_k2_v4.spec-rev-22.json`，`pm_gate.artifacts.path("L3", …)` → 命中该件 ✓（探针脚本读值见 §4）。

## 2. E1 复算（冻结仪器，`/tmp/opencode/k2p1/measure_source_reconcile.draft.py`）

| 等式 | 复算值 | 与前基线（handoff §6 固化） |
|---|---|---|
| E1 refdes | 板 **42** / 原理图 **55** / 网表 **55**；**板-图 = 0**；图-板 = **13**（= `D2,L1,R35–R39,R40,R41,R42–R45`，P4 补件 O2 登记） | **逐项一致** |
| E2 不符 refdes 数 | **10**（`J2/J3/J4/J11/J12/J13/J6/J9/U1/U2`） | 一致 |
| E3 逐引脚 | **489 = 一致 424 / 不一致 15 / 缺焊盘 50** | 一致 |

## 3. E2/E3 **源侧面**复算（含 U1 改归板侧）

### 3.1 E2 逐件（源侧 ⊆ 焊盘 + 余量逐条登记）

| ref | 符号 pin# | 板 pad# | 余量 | 源侧面判定 |
|---|---|---|---|---|
| `J2` | 74 | 74 | 0 | ✅ 源侧无缺陷（原「43」为口径假阳性，v1.1 已订正） |
| `J3` | 38 | 38 | 0 | ✅ 余量 0；对应关系 `pin i → A((i+1)//2)|B(i//2)` **逐网 38/38 命中**（登记项，非缺陷） |
| `J4` | 38 | 38 | 0 | ✅ 同 `J3` |
| `U1` | 27（LQFP48 编号） | 33 | **14**（13 未用脚 NC + `33`） + **缺脚 8** | ⚠ **源侧无缺陷**：真源自洽于 LQFP48（`MCU_STM32G0_C2` = CBT6/LQFP48），canonical SPEC 已由 **rev-22** 对齐 ⇒ 缺脚 8 = **板侧**（板 U1 实例仅 pad 1..33），归 P4（2-A″） |
| `U2` | 6 | 8 | 2（`7`,`8`，NC） | ✅ 登记即闭 |

**E2 源侧面结论**：源侧（真源 yaml + canonical `rev-22`）**无残余缺陷**；`U1` 的 14 余量 + 缺脚 8 中，**缺脚 8 与 `pad33` 几何（EP 尺寸）均属板实例**（P4），13 个未用脚为登记项。

### 3.2 E3 归因（65 条非一致节点，按 #K2-14 §二 更新归属）

| 归因 | 条数 | 归属（**#K2-14 裁定后**） |
|---|---|---|
| `U1` 符号脚号在 33 pad 实例上不存在（`35/36/42/43/44/47/48/49`） | **8** | **板侧 P4**（原记源侧 R2；#K2-14 §二 **确认**改归板侧） |
| `U6` 焊盘在位但无网/`NO_CONNECT` | 15 | 板侧 P4 |
| 5 排针 0 焊盘（`J11/J13/J9/J12/J6`） | 16 | 板侧 P4 |
| 13 件补件缺焊盘（各 2 pad） | 26 | 板侧 P4 |
| **合计非一致** | **65** | **65/65 = 板侧 P4**；**源侧 = 0** |

**核对**：板侧 57（P4 登记 §3：15+16+26）+ 8（U1 截断）= **65** ✓。
**仪器标签说明（诚实边界）**：`/tmp/opencode/k2p1/e3_rootcause.draft.py` 内该桶文本为**旧口径**「R2 源侧·口径冲突(U1 符号=LQFP48 vs 真源 QFN32)」，其**集合与条数不变（8）**，仅归属随 #K2-14 改判；本件据裁定更正归属，**未改仪器**（一次性取证脚本；改标签属另案）。E2 仪器对 `pad33` 的分类文本同理基于几何（3.2×3.2mm）。

### 3.3 源侧面归零声明

- **E1 图侧**：板-图 = **0**（图侧归零）；图-板 13 = P4 补件。
- **E2/E3 源侧面**：**0 缺陷**（全部 65 条残余 + E2 余量项 = 板侧 P4 登记）。
- **未以「接近 0」宣称**：13（图-板）与 65（板侧）**均为非零**，已逐条归口 P4，**不再作为 P2 归零条件**（P2 = 源侧同构，板侧项按 #K2-11 §一-1 `board_pending` 延 P4 —— #K2-14 §一 **确认**）。

## 4. 复跑（只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/k2p1/measure_source_reconcile.draft.py --board k2/hw/k2_v4_8L.l4.kicad_pcb \
    --sch k2/hw/sch --nets k2/hw/data/k2_sch.yaml --json /tmp/opencode/post2/recon_rev22.json
AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/e2_pad_registry.draft.py
python3 /tmp/opencode/k2p1/e3_rootcause.draft.py
# canonical 解析链探针（cwd=k2）
cd k2 && AppDir/usr/bin/python3.11 -c "import sys;sys.path.insert(0,'_shared');from pm_gate import config as c,artifacts as a;n=c.spec_name('k2_v4');print(n,a.path('L3',n))"
```

> **P2 关门前 ENG 侧无待办**：本件即 §四 第 2 步回件，**请监理判 P2 正式关门**；**P3 未批不开**。
