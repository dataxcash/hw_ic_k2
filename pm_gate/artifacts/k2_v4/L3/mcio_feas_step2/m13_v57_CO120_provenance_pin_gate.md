# CO-120 — **L2 过程闸**：记录内 **inter-record provenance pin** 一致性（关闭 CO-108 / CO-114 **F-6 盲区**）

- 判定：**`PASS`**（pins 12：match **8** / 豁免历史 **3** / **未声明陈旧 0** / 解析歧义 1；牙齿 2/2）
- 触发：CO-114 **F-6**（medium，根因 = **CO-77 只校验收口声明件引用，不覆盖记录内部 `*_record` pin**）
- 工具 `tools/p3_v57_co120_provenance_pin_gate.py`｜记录 `m13_v57_co120_provenance_pin_gate.json`
- 复现：`python3 tools/p3_v57_co120_provenance_pin_gate.py`

## 1. 判据

1. 扫描 STEP2 全部 `m13_v57_co*.json`，抽取 `"<x>_record": "<sha16>"` pin；
2. 由 key 前缀解析被引记录文件（`m13_v57_<x>*.json`；歧义 key 走显式 `PIN_TARGETS`，零搜索）；
3. 现行 pin 必须等于被引文件**当前** sha16；不等 ⇒ 必须是**已声明豁免**（仅限「记录本体已被后续 CO 取代 ⇒ pin 属历史」，理由明文注册）；
4. **牙齿**：注入未声明陈旧 pin 必须 FAIL（负控）；注入匹配 pin 必须 PASS（正控）。

## 2. 首跑读数

- `match` **8**；`exempt_historical` **3**（`co109←co106`、`co110←co106`、`co110←co87` —— 记录本体已被 CO-115 取代）；
- `stale_undeclared` **0**；`unresolved_key` **1**（co85 的裸 `record` key，歧义，入记录不计失败）；
- **CO-114 F-6 的 live 链 pin 已闭合**：`co98←co95`、`co105←co98` 均 match。

## 3. 意义

把 F-6 的**缺陷类**（记录内 provenance pin 陈旧）机判化 ⇒ 此后任何 rev 重基线若只前移部分 pin，本闸即 **FAIL_STALE_PROVENANCE_PIN**（不再依赖人工发现）。

## 4. 非声明

只读；不改任何记录/SPEC/板/阈值/冻结源；豁免仅限已取代记录且注册表明文；解析失败入记录不计失败。
