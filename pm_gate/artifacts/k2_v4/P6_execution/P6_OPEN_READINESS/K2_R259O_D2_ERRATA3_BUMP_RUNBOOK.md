# D2 runbook · `errata-3` 版本 bump 落库（**备件** · 不落库）· 2026-09-22

**授权**：#K2-132 **D2 准**（`errata-3` = `5dc7b82a901d11c8` 作 adjudication 输入 · **版本 bump 新件** · **禁覆盖冻结原件** `dd794c54f7ce7417` · 与 l9/`spec-rev-55`/`criteria` rev=7 **同批**）。

## 同批清单（缺一不落）
| 件 | 动作 | 属主 |
|---|---|---|
| `criteria/` **rev=7** | 落件（齿 `layout_and_assembly_quality` + courtyard/pth_inside_courtyard 豁免 + EX-1） | **gate 属主** `ic_hw_gate` |
| `SPEC_k2_v4.spec-rev-55.json` | 新增（在册最新 = rev-54） | 监理/ENG 执行 · 监理签 |
| `k2/hw/k2_v4_8L.l9.kicad_pcb` | 落 `hw/`（②-UP 收口后） | ENG 执行 |
| **网表 bump 新件** | 由 `k2_sch.errata-3.yaml` `5dc7b82a901d11c8` **逐字节复制**为新版本名（建议 `k2/hw/data/k2_sch.v2-errata3.yaml`）；`k2_sch.yaml` **逐字节不动** | ENG 执行 · 监理签 |
| 具名豁免表（EX-1 + courtyard/pth_inside_courtyard） | 落件 | 监理 |

## 落库后即时复跑（验收 · #K2-132 §五）
1. `python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l9.kicad_pcb --pro <l9 pro> --nets <bump 件> --sch-dir k2/hw/sch --gerber-dir <fresh> --root . …`
2. 期望：**19/19 @bump 件**（并**分列** @冻结原件 读数留档）。
3. 冻结四源 4/4 逐字节复核（`dd794c54…` 等）。

## 现状（备件未执行）
- `errata-3` 在库（`5dc7b82a901d11c8`）；bump 新件**未创建**（待同批指令）。
- `criteria/` rev=6 MATCH（ENG 只读未碰）；rev=7 **未落**（gate 属主）。
- `spec-rev-55` **未落**；`l9` **未落**（②-UP 未收口）。
