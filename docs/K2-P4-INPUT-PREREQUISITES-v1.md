# K2 · P4 输入前置登记 **v4**（#K2-16 权威件 + #K2-17 补正 + **#K2-18 P4 开工令**；IN-1..IN-11）

> **依据**：监理 **#K2-16 §二 R2/R3** + §四 · **#K2-17 §二/§三**（C7=9 铜区 / 板侧 ESC）· **#K2-18 §五**（**U3 = P4 开工令**，附 IN-1..IN-11）+ §三-2（IN-10）+ §七（IN-11）。
> **性质**：登记件（不改任何判据/源件）。**P4 已开**（P3 门 = 通过，#K2-18 §四）；本件为开工输入清单。
> **修订留痕（v4）**：v3（`20b6775f6daa1350`）→ 本版：新增 **IN-10/IN-11**；IN-2 的 owner 逐层角色待裁项**已由 U2 收口**（#K2-18 §八 认可）；P4 状态由「未批不开」改为「已开」。

| # | 前置 | 件（sha256 前 16） | 现状 / ENG 动作 |
|---|---|---|---|
| **IN-1** | **strap 封装 0603**（R2 裁定：BOM 一致性，与板上既有 9 颗 R 全同） | `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）—— 9 件 strap 符号统一 `Resistor_SMD:R_0603_1608Metric`（原件 `k2_sch.yaml` `dd794c54f7ce7417` **逐字节不动**） | 已出件；**P4 消费前须重指向**（`k2_gen_v5.py` 的 `YAML_PATH` 与判据 `--nets` 输入路径） |
| **IN-2** | **8L 口径 errata**（R3）：6L 文本标历史、8L = canonical（owner 2026-08-19 裁决）；**含 In5/In6 层角色收口** | `k2/pm_gate/artifacts/k2_v4/L2/L2-ERRATA-8L-v1.md`（`eb9354a6b8ffd535`）+ `L2/L2_RULING_in5_in6_role_v1.md`（`5835d392151a0b19`）+ `L2/README-canonical.md` §3（`f5b3bd6b952af81d`） | 已出件；**In5/In6 已收口**（canonical = GND `In1/In3/In6`、信号 `F/In2/In5/B`；owner 表 `F/G/S/G/P/G/S/B` 为历史口径/已被 #12+#14 取代）—— **#K2-18 §八 认可、不否决** |
| **IN-3** | **9 铜区全填充**（C7，口径按 **#K2-17 §二 补正 1** 修正：原「13 区」含 4 个无网 `ESC_*` keepout ⇒ 判据自指） | 台账 `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json` → `pour_zones`（`copper_zone_count`=9 / `excluded_non_net_zones`=4） | **未达 0/9** ⇒ P4 铺铜后复算 |
| **IN-6** | **板侧固定孔施工**：4×Ø3.2 NPTH + Ø6.0 keepout（L2-2 解：H1 26.10/75.60、H2 139.60/39.60、H3 26.10/36.10、H4 114.60/36.10） | 图 `01_board_frame_and_holes.svg` | 板 0 孔 ⇒ P4 打孔 |
| **IN-7** | **4 个 `ESC_*` keepout 开关**落为 ≥1 项非 `allowed`（**实测**：板侧 4 区 × 5 开关 `tracks/vias/pads/copperpour/footprints` **全 `allowed`** = 空操作，`any_non_allowed=0/4`；审计 §4.1 原缺陷未消） | 机读 `L3/drawings/p3_drawings.json → criteria.C5b_board_side_esc_switches`；图 `06_keepouts.svg` | **未达 ⇒ P4 施工项**（#K2-17 §三 补正 2）；**P3 门不因此受阻** |
| **IN-8** | **`column_x = 27.94` 守值**（P3-4 出框余量仅 **0.08mm**；若必须动 ⇒ 需重跑 P3-4 复算） | 图 `07_interface_pads_inframe.svg`；D1=位移后 0 冲突 | P4 布线须守 |
| **IN-10** | **`rev-25`：live 字段对齐 L2-4**（`bga_escape.per_ball.corridor_edge` = `104.84/82.60`；`layer_plan.strap_domain_v32.open_for_coords[1]` 文本 → `104.84`）—— #K2-18 §三-2 监理独立发现（rev-23/24 只回写 `corridors[]` 容器） | `L3/SPEC_k2_v4.spec-rev-25.json`（`74f31d08a8be2f17`）+ `pm_gate/project.yaml`（`fbed04b4569a46c7`，重指向 rev-25）；`rev-24 317140048c80a569` 原件不动 | **已落地（本轮，2026-09-16）**；判据（P4 完工用）= 全 SPEC stale 扫描（排 `_spec_rev_*` 与 `corridors_clearance_basis_v23`）对 `17.30/27.40/105.25/82.35` **零命中**（实测 rev-24 → 3 命中 / rev-25 → 0） |
| **IN-11** | **5 件接口件 pad 补录**：`J6/J9/J11/J12/J13` 共 **16 pad**（板现 **0 pad** ⇒ 判据 `device_has_pads` 必 FAIL）—— #K2-18 §七（U4-B 自裁；判据正确、板缺 pad） | 板侧清单 `K2-P4-board-side-defect-register-v1.md` §3（`337a24a5ec4e70ee`，同源 E3 57 项）+ `L3/drawings/p3_drawings.json` `criteria.C3` | **P4 施工项**：按 `ForgeOS:PinHeader_1x02/1x04` land pattern 落 16 pad；判据 = `device_has_pads` PASS（`footprints_without_pads = []`） |
| **IN-9** | **源侧修复已落**：errata yaml 经 `project.yaml:nets_yaml` 生效；sch sheet `c7099e2fae642bdd` / 符号库 `6b572ceb7ffc2e69`（按源重出；其余 sheet 逐字节未变） | `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`） | 已生效；P4 用 E1/E2/E3 仪器时 `--nets` 指向该件 |
| **IN-4** | **U1 板侧补齐**（2-A″）：pad `34..48` + `EP(49)`→`GND`；land pattern = LQFP48 | `k2/docs/K2-P4-board-side-defect-register-v1.md` §5（`337a24a5ec4e70ee`） | 未做（P4 批，与补 13 件同批） |
| **IN-5** | **落位解落板**：55 件坐标（40 锚点/SPEC+L2-3 + 15 L2 解） | `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json`（`faddc9de5519c5ec`） | 已解（selfcheck 五项全零）；P4 按此落板 |
