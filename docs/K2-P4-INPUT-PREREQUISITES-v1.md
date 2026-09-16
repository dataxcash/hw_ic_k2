# K2 · P4 输入前置登记 v2（#K2-16 §五 登记；**开工前须落地**）

> **依据**：监理 **#K2-16 §二 R2/R3** + §四（P4 不开）+ P3 图集 C7。
> **性质**：登记件（不改任何判据/源件）。**P4 未批不开**；本件为开工时的输入清单。

| # | 前置 | 件（sha256 前 16） | 现状 / ENG 动作 |
|---|---|---|---|
| **IN-1** | **strap 封装 0603**（R2 裁定：BOM 一致性，与板上既有 9 颗 R 全同） | `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）—— 9 件 strap 符号统一 `Resistor_SMD:R_0603_1608Metric`（原件 `k2_sch.yaml` `dd794c54f7ce7417` **逐字节不动**） | 已出件；**P4 消费前须重指向**（`k2_gen_v5.py` 的 `YAML_PATH` 与判据 `--nets` 输入路径） |
| **IN-2** | **8L 口径 errata**（R3）：6L 文本标历史、8L = canonical（owner 2026-08-19 裁决） | `k2/pm_gate/artifacts/k2_v4/L2/L2-ERRATA-8L-v1.md`（`eb9354a6b8ffd535`） | 已出件；**含一项待监理裁**：owner 定案件逐层角色（GND=In1/In3/In5）vs canonical/板（GND=In1/In3/In6）In5/In6 互换 |
| **IN-3** | **9 铜区全填充**（C7，口径已按 **#K2-16 §四 监理自纠**修正：原「13 区」含 4 个无网 `ESC_*` keepout ⇒ 自指不可达） | 台账 `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json` → `pour_zones`（`copper_zone_count`=9 / `excluded_non_net_zones`=4） | **未达 0/9** ⇒ P4 铺铜后复算 |
| **IN-6** | **板侧固定孔施工**：4×Ø3.2 NPTH + Ø6.0 keepout（L2-2 解：H1 26.10/75.60、H2 139.60/39.60、H3 26.10/36.10、H4 114.60/36.10） | 图 `01_board_frame_and_holes.svg` | 板 0 孔 ⇒ P4 打孔 |
| **IN-7** | **4 个 `ESC_*` keepout 开关**落为 ≥1 项非 `allowed`（板侧现全 `allowed` = 空操作） | 图 `06_keepouts.svg` + `keepouts` 台账 | 板侧未落 ⇒ P4 |
| **IN-8** | **`column_x = 27.94` 守值**（P3-4 出框余量仅 **0.08mm**；若必须动 ⇒ 需重跑 P3-4 复算） | 图 `07_interface_pads_inframe.svg`；D1=位移后 0 冲突 | P4 布线须守 |
| **IN-9** | **源侧修复已落**：errata yaml 经 `project.yaml:nets_yaml` 生效；sch sheet `c7099e2fae642bdd` / 符号库 `6b572ceb7ffc2e69`（按源重出；其余 sheet 逐字节未变） | `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`） | 已生效；P4 用 E1/E2/E3 仪器时 `--nets` 指向该件 |
| **IN-4** | **U1 板侧补齐**（2-A″）：pad `34..48` + `EP(49)`→`GND`；land pattern = LQFP48 | `k2/docs/K2-P4-board-side-defect-register-v1.md` §5（`337a24a5ec4e70ee`） | 未做（P4 批，与补 13 件同批） |
| **IN-5** | **落位解落板**：55 件坐标（40 锚点/SPEC+L2-3 + 15 L2 解） | `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json`（`faddc9de5519c5ec`） | 已解（selfcheck 五项全零）；P4 按此落板 |
