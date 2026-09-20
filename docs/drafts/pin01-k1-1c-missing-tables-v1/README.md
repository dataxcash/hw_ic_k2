# PIN01-K1-1c — sch_gate 缺失真源表 4 件（**已制备 · 待批落地**）

**状态：未落地（NOT LANDED）**。本目录 = 已从厂商原件逐脚转录、并**沙箱验证过**的
`_shared` 载荷；**落地点**为 `_shared/eda_core/sch_gate/datasheets/`（4 件新增）。
落地属 `_shared` 写 ⇒ 按常设红线须**监理放行**（与 `PIN01-K1-1a` 同一笔批 + 同批升版 + 四树同步）。

## 为什么存在（缺口）
`python3 _shared/eda_core/sch_gate/checks/pinmap.py k1/sch/K1_SCH.kicad_sym`
报 **PIN-01 FAIL(29)**，其中 **4 项 = 多引脚器件无 datasheet 真源表**（fail-closed 阻断）：
`TPS22990`(Q1) · `TPS22965`(U12) · `TPD2E001`(U13) · `2N7002`(Q2)。
本件把 4 表补齐 ⇒ 该 4 项消失（**29 → 25**；余 25 = J1 23 + KBU6 名绑定 2，属 PIN01-K1-1a/b）。

## 载荷（4 件）
| 文件 | 器件 | 封装 | 厂商原件 | 取回 sha256（= `doc_sha256`） |
|---|---|---|---|---|
| `TPS22990.yaml` | TI TPS22990 | DML WSON-10 | TI **SLVSDK1C** §6 Pin Functions | `ea198776524544eb…dde2a3` |
| `TPS22965.yaml` | TI TPS22965 | DSG WSON-8 | TI **SLVSBJ0F** §5 Pin Functions | `3300eef743d7871f…95a7e1` |
| `TPD2E001.yaml` | TI TPD2E001 | DRY 6-pin USON | TI **SLLS684I** §5 Pin Functions | `b648c5d12f3e5b48…98d79` |
| `2N7002.yaml` | Nexperia 2N7002 | SOT23 (TO-236AB) | Nexperia **Rev. 7 (2011-09-08)** §2 Table 2 | `cc9c275457670c3c…646475` |

- 前 3 件的 `doc_sha256` **与仓库既有 K1 投标输入层**
  （`k1/pm_gate/artifacts/k1/L1/inputs/datasheets/*.yaml`）**逐字节一致** ⇒ 出处自洽可反查。
- `TPD2E001` 按 **DRY** 编号登记（= K1 板所用变体，owner 裁决 L1-4）；DRS 同拓扑同编号；
  **DZD(4-pin) 编号不同**，已在 YAML 内显式警示「禁一套编号通吃」。

## 沙箱验证（可复现）
```bash
python3 -c "import shutil;shutil.rmtree('/tmp/.../dsdir',ignore_errors=True)"
cp -r _shared/eda_core/sch_gate/datasheets /tmp/opencode/sgaudit/dsdir
cp k2/docs/drafts/pin01-k1-1c-missing-tables-v1/*.yaml /tmp/opencode/sgaudit/dsdir/
# 调 check_symbol_library(k1 符号库, dsdir)
```
- **加表前**：FAIL(29)（4 项 = 上述无表）。
- **加表后**：FAIL(25)（**4 项无表全消**，无新增 fail）。
- **负控**：把 `NMOS_2N7002` 符号 D 脚号 `3→2` ⇒ **FAIL(26)** 且报 `D 允许 pin ['3']`
  ⇒ 新表**确实被强制**（非静默放行）。
- **零回归**：仅 K1 使用这 4 个 Value（全仓 `.kicad_sym` grep），k2/key_v2/pciesw4 不受影响。

## 转录红线
- 逐脚取自厂商 `pdftotext -layout` 输出的 **Pin Functions 表**（页码/表名见各 YAML 注释）。
- **不猜**：热焊盘按厂商表以 `—` 编号（**非编号脚**）登记在 `thermal_pad:` 字段，板侧焊盘号
  （Q1=11 / U12=9）只作注释，不进 `pins`。
- YAML 陷阱：`ON`/`OFF`/`Y`/`N` 等 **YAML 1.1 布尔词**必须加引号（`"ON"`），否则被转成
  `True` ⇒ 校验报「未绑定端口」。本批已规避。
