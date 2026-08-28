# M-E 重解一次（--all-v4）纯方向分工最终验证 — session_report

> 结论先行：**验收 FAIL — 17/18 INFEASIBLE，按验收⑤ 停机上报（本报告即停机报告）**。
> 已执行唯一一次求解，未改 SPEC/alloc/求解器，未手补走线，未重跑，未触碰 git。

---

## 1. 求解执行记录

- 求解器：`eda_core.hs_route_model --all-v4`（model v4.0，确定性，固定序 UP0→UP7 → DN0→DN7 → REFCLK0→1）
- 求解进程：**1 次**（单进程单次 `solve_all_v4`；每 base 一次 `solve_chain_v4`）
- 执行参数：与任务命令逐字一致（board/spec/alloc/rules/pro/config/out 全同）
- **环境说明（唯一偏差）**：任务命令含 `cd _shared`，但 `_shared/` 内不存在 `strix-halo-ioconvert/`（实测 `ls` 拒绝），相对路径仅能自容器根解析；故 CWD=容器根 `/home/fila/jqdDev_2025/ic_hw`（`eda_core -> _shared/eda_core` 软链即为此设），参数零改动。若按原 CWD 执行必在 `open(spec)` 处 FileNotFoundError 崩溃。
- 模型自报 `solve_time_s = 16.079`（18 链全量）；`input_fp = 9b6e28c3…`（= k2_v6.kicad_pcb sha256，与输入指纹一致）
- 落盘：`hs_rebuild_summary.json` + `hs_rebuild/` 18 个 base json + 逐段 P/N json（模型 main() 正常完成）
- 逐对耗时：**未落盘**（测量封装序列化缺陷，见 `per_pair_timing.json`；求解本体不受影响）。按⑤+MUST NOT 不重跑补采。

## 2. 输入指纹（sha256，求解前采集）

| 输入 | sha256 |
|---|---|
| /tmp/opencode/boards/k2_v6.kicad_pcb（板，电容墙已复摆 DN y57.8/68.0、UP y39.4） | `9b6e28c31444149bd749395beda6bd1f18ea15031575a0cf96b503fa4b5110ff` |
| /tmp/opencode/boards/k2_v6.kicad_pro | `61ff7292720042eea525eb1341f0cf8b1f65a291d74e7d3e50b3a6ab43d6a143` |
| SPEC_k2_v4.json（corridors 已修订：J2_TO_U[98.83,131.5]、U_TO_MCIO[65.5,88.83]，实测一致） | `7eaad223cf691f7c8317435f9b69cbce59124f2ce0abda885d3570b03ac9e21e` |
| channel_alloc_v4/channel_alloc.json（18/18 SOLVED 未动） | `3f8fb6fc57715f0d2f4dc4e87d3e10377f9ef8a01a2c6643c0a7e49ee5f1bf44` |
| eda_core/drc_rules.json | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` |
| route_model_config.json (k2_v4/L2) | `54b187f7e78254fca08b239dfd85415c29a3e314862c3824d8c12b9cf176068b` |
| 求解器 hs_route_model.py（未改） | `5464d8f02670c5e4c931d63cecb16b501e51832ff88e502106d5e9a8baae272b` |

## 3. 逐对结果表（status/kind/length/skew/耗时）

- 段 status：`input:SOLVED(lenP/lenN)` 等；链 `lenP/lenN/skew` = 链级汇总；`skew_ok` 阈 0.15
- 耗时：全程 16.079s / 18 链（逐对秒数未落盘，见 §1；无暴力求解结构）

| base | 链 status | 各段 status（P/N 长度） | 链 lenP | 链 lenN | 链 skew | skew_ok | 失败原因 |
|---|---|---|---|---|---|---|---|
| PCIE_UP0 | INFEASIBLE | input:SOLVED(30.77/31.01); out_U7:SOLVED(11.27/10.36); out_J2:SOLVED(50.29/51.29) | 92.3273 | 92.6535 | 0.3262 | F | P/N 自交 -0.205 |
| PCIE_UP1 | INFEASIBLE | input:SOLVED(31.31/31.60); out_U7:SOLVED(12.66/11.76); out_J2:SOLVED(45.62/43.68) | 89.5857 | 87.0427 | 2.5430 | F | P/N 自交 -0.205 |
| PCIE_UP2 | INFEASIBLE | input:SOLVED(35.76/37.07); out_U7:SOLVED(14.05/13.16); out_J2:SOLVED(37.48/38.66) | 87.2959 | 88.8930 | 1.5971 | F | P/N 自交 -0.205 |
| PCIE_UP3 | INFEASIBLE | input:SOLVED(36.86/37.66); out_U7:SOLVED(15.44/14.57); out_J2:SOLVED(37.25/35.31) | 89.5470 | 87.5318 | 2.0152 | F | P/N 自交 -0.205 |
| PCIE_UP4 | INFEASIBLE | input:SOLVED(53.80/53.40); out_U7:SOLVED(16.82/15.97); out_J2:SOLVED(33.78/34.80) | 104.3983 | 104.1701 | 0.2282 | F | P/N 自交 -0.205 |
| PCIE_UP5 | INFEASIBLE | input:SOLVED(53.58/52.95); out_U7:SOLVED(18.60/17.24); out_J2:SOLVED(33.96/32.09) | 106.1393 | 102.2825 | 3.8568 | F | P/N 自交 -0.205 |
| PCIE_UP6 | INFEASIBLE | input:SOLVED(49.24/48.59); out_U7:SOLVED(19.88/18.62); out_J2:SOLVED(32.12/33.36) | 101.2388 | 100.5711 | 0.6677 | F | P/N 自交 -0.205 |
| PCIE_UP7 | INFEASIBLE | input:SOLVED(48.71/48.09); out_U7:SOLVED(20.99/20.18); out_J2:SOLVED(30.97/31.72) | 100.6665 | 99.9914 | 0.6751 | F | P/N 自交 -0.205 |
| PCIE_DN0 | INFEASIBLE | input:SOLVED(43.52/41.48); out_U3:SOLVED(13.41/14.20); **out_MCIO:INFEASIBLE** | 56.9358 | 55.6748 | — | F | 右逃逸无净空 |
| PCIE_DN1 | INFEASIBLE | input:SOLVED(40.69/42.17); out_U3:SOLVED(12.97/13.09); out_MCIO:SOLVED(34.97/33.58) | 88.6352 | 88.8423 | 0.2071 | F | P/N 自交 -0.205 |
| PCIE_DN2 | INFEASIBLE | input:SOLVED(40.42/39.00); out_U3:SOLVED(11.51/11.82); out_MCIO:SOLVED(45.23/44.06) | 97.1665 | 94.8763 | 2.2902 | F | P/N 自交 -0.205 |
| PCIE_DN3 | INFEASIBLE | input:SOLVED(39.53/40.99); out_U3:SOLVED(10.50/10.16); **out_MCIO:INFEASIBLE** | 50.0320 | 51.1518 | — | F | 右逃逸无净空 |
| PCIE_DN4 | INFEASIBLE | input:SOLVED(40.95/39.52); out_U3:SOLVED(17.64/18.96); out_MCIO:SOLVED(30.31/30.02) | 88.8958 | 88.5010 | 0.3948 | F | P/N 自交 -0.205 |
| PCIE_DN5 | INFEASIBLE | input:SOLVED(40.08/41.57); out_U3:SOLVED(13.86/14.65); out_MCIO:SOLVED(31.73/31.06) | 85.6751 | 87.2722 | 1.5971 | F | P/N 自交 -0.205 |
| PCIE_DN6 | INFEASIBLE | input:SOLVED(35.63/37.21); out_U3:SOLVED(10.11/10.78); out_MCIO:SOLVED(27.46/26.82) | 73.1952 | 74.8122 | 1.6170 | F | P/N 自交 -0.205 |
| PCIE_DN7 | INFEASIBLE | input:SOLVED(38.93/40.07); out_U3:SOLVED(6.25/8.40); **out_MCIO:INFEASIBLE** | 45.1791 | 48.4669 | — | F | 左逃逸无净空 |
| PCIE_REFCLK0 | **SOLVED** | input:SOLVED(74.2999/76.5106) | 74.2999 | 76.5106 | 2.2107 | **F** | 等长不达标（skew 2.21>0.15，蛇形未应用） |
| PCIE_REFCLK1 | INFEASIBLE | input:SOLVED(84.83/85.89) | 84.8342 | 85.8880 | 1.0538 | F | P/N 自交 -0.205 |

## 4. INFEASIBLE 证据表（验收⑤：哪网/哪段/最近障碍类型·网·距离 vs 需求）

### 4.1 类 A — 段内 P/N 线段自交（14 base：UP0-7, DN1, DN2, DN4, DN5, DN6, REFCLK1）

模型原子性断言 `_pn_spacing_check` 自报 `pn_spacing=-0.2050 < 0.175`（=中心距 0.000 − 线宽 0.205），
判定 **模型缺陷证明** → 链级 INFEASIBLE。交叉点由记录路径用模型同款 `_seg_seg_dist` 定位（读盘，非重解）：

| base | 段（P×N 交叉） | 交叉点坐标 | 层 | 障碍类型 | 障碍网 | 中心距 | 边缘距 vs 需求 |
|---|---|---|---|---|---|---|---|
| PCIE_UP0 | input × input | (64.317, 49.077) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP0_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP0 | out_J2 × out_J2 | (100.689, 48.650) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP0_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP1 | input × input | (63.414, 47.891) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP1_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP1 | out_J2 × out_J2 | (103.289, 47.452) / (132.666, 47.491) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP1_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP2 | input × input | (60.992, 46.698) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP2_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP2 | out_J2 × out_J2 | (105.889, 46.224) / (132.675, 46.303) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP2_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP3 | out_J2 × out_J2 | (108.489, 45.026) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP3_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP4 | input × input | (58.365, 44.303) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP4_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP4 | out_J2 × out_J2 | (111.088, 43.830) / (132.183, 43.907) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP4_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP5 | input × input | (59.221, 43.104) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP5_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP5 | out_J2 × out_J2 | (113.686, 42.636) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP5_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP6 | input × input | (62.635, 41.911) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP6_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP6 | out_J2 × out_J2 | (116.287, 41.447) / (130.179, 41.503) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP6_N | 0.000 | -0.205 vs 0.175 |
| PCIE_UP7 | input × input | (64.190, 40.733) | In2.Cu | 同对差分 P/N 自交 | PCIE_UP7_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN1 | input × input | (132.295, 59.493) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN1_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN1 | out_MCIO × out_MCIO | (62.819, 59.889) / (78.436, 57.631) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN1_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN2 | out_MCIO × out_MCIO | (59.675, 61.096) / (81.027, 57.642) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN2_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN4 | out_U3 × out_U3 | (75.988, 63.570) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN4_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN4 | out_MCIO × out_MCIO | (55.300, 61.640) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN4_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN5 | input × input | (132.542, 64.292) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN5_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN5 | out_U3 × out_U3 | (78.586, 64.764) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN5_N | 0.000 | -0.205 vs 0.175 |
| PCIE_DN6 | out_U3 × out_U3 | (81.187, 65.953) | In2.Cu | 同对差分 P/N 自交 | PCIE_DN6_N | 0.000 | -0.205 vs 0.175 |
| PCIE_REFCLK1 | input × input | (61.918, 50.506) | In6.Cu | 同对差分 P/N 自交 | PCIE_REFCLK1_N | 0.000 | -0.205 vs 0.175 |

**根因（代码级）**：`_solve_pair_centerline_v4` 构造期障碍场 `clear_hs_nets=(net_p, net_n)` 把本对 P/N 互清，
逃逸/走廊连接段 P/N 相向交叉在 `seg_ok` 中不可见；`flip` 极性枚举（False→True 固定序，取首个全 SOLVED）
未保证逃逸出口排序与走廊轨道分配（track_y±0.19）一致 → 逃逸带段（In2.Cu/In6.Cu）P/N 连接线交叉。
后置 `_pn_spacing_check`（原子性断言，阈值 0.155）捕获 → 自报「模型缺陷证明」INFEASIBLE。
非输入缺口：交叉点全在 P/N 自交（同对网），无外部障碍挤压；改 SPEC/alloc 不解决。

### 4.2 类 B — 逃逸对级无净空（DN0/DN3/DN7，模型自带 nearest 证据）

| base | 段 | 逃逸 | 最近障碍类型 | 障碍网（描述） | 距离 | 需求 | 缺口 |
|---|---|---|---|---|---|---|---|
| PCIE_DN0 | out_MCIO | 右逃逸 flip=True | via | PCIE_DN_OUT0_N_U3（F.Cu，同链 out_U3 段 N via） | -0.1888 | 0.175 | 0.3638 |
| PCIE_DN3 | out_MCIO | 右逃逸 flip=True | seg | PCIE_DN_OUT3_P_U3（F.Cu，同链 out_U3 段 P 线段） | -0.1200 | 0.175 | 0.2950 |
| PCIE_DN7 | out_MCIO | 左逃逸 flip=True | pad | GND（F.Cu 焊盘） | -0.0750 | 0.175 | 0.2500 |

（`pn_dist` 记录：DN0=1.300, DN3=1.300, DN7=0.600；障碍来自先解段累积/刚性焊盘。）

### 4.3 类 C — REFCLK0：链级 SOLVED 但等长不达标

- `input` 段 SOLVED（corridor=J2_TO_U, track_y=45.7, In6.Cu），P=74.2999 / N=76.5106，skew=**2.2108** > 0.15；
  蛇形补偿未应用（`skew_ok=False` 保持）。REFCLK 仅需状态记录，如实标注：SOLVED 但等长 ③ 不满足。

## 5. 验收结论表

| # | 验收项 | 结论 | 依据 |
|---|---|---|---|
| ① | 16 数据对 SOLVED + 2 REFCLK 状态记录 | **FAIL** | 0/16 数据对 SOLVED（16/16 INFEASIBLE）；REFCLK0 SOLVED、REFCLK1 INFEASIBLE（状态记录齐全） |
| ② | P/N 断言：每对 P、N 两条 SOLVED 且同段 | **FAIL** | 16 数据对链级全 INFEASIBLE（段内 P/N 自交/逃逸失败）；仅 REFCLK0 满足段级 P/N 同段 SOLVED |
| ③ | 对内等长 \|P−N\| < 0.15 | **FAIL** | REFCLK0 skew=2.2107；16 数据对链级 skew 均 ≥0.2071 且状态 INFEASIBLE |
| ④ | 单对求解耗时 < 5s（逐对秒数） | **N/A（停机路径）** | 全程总耗时 16.079s/18 链（模型记录）；逐对秒数因测量封装序列化缺陷未落盘；按⑤+MUST NOT 不重跑。无暴力求解结构（确定性折线+单次 VGraph） |
| ⑤ | INFEASIBLE → 证据表 + 停机上报 | **触发 → 停机** | 17/18 INFEASIBLE，证据表见 §4；本报告即停机报告 |

## 6. 停机声明（MUST NOT 合规）

- ✅ 求解命令仅执行 **1 次**（未改参重跑；唯一偏差=CWD 容器根，参数零改动，见 §1）
- ✅ 未改 SPEC / alloc / 求解器（各输入 sha256 求解前采集，见 §2）
- ✅ 未手补走线、未为求解改输入
- ✅ 未触碰 git
- ⛔ **按验收⑤ 停机**：17/18 INFEASIBLE，等待人工判定（类 A 为模型构造缺陷证明，类 B 为逃逸净空缺口，类 C 为 REFCLK 等长），不续跑、不修输入、不硬挤。
