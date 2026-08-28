# K2 v4 新拓扑可布性预检报告（M13 v6 M-C，修订版）

> 生成：2026-08-26，M13 v6（M-A 探针建成 → M-B 验尺子 → M-C 预检 → M-D 实施修正）
> 探针：`probe_link_topology` / `link_topology_virtual_map`（HSRouteModel 方法，
> 确定性 + 落盘 + 数据驱动，零 revA 特判）
> 证据：`model_solves/hs_rebuild_v6/link_topology_old_topology.json`（M-B）
>       `model_solves/hs_rebuild_v6/link_topology_new_topology_precheck.json`（M-C）
> 修订：2026-08-26 M-D 实施后修正——J2 端 RX/TX 为**方向语义**（非 lane 分组），
>       最终网表映射见 §4（MCIO 端 lane 分组 + J2 端方向保持）

## 1. M-B 验尺子（旧拓扑：方向分工）—— 探针真能发现问题

| 链路 | MCIO 端 | 芯片端 | 判定 | y_delta(mm) | 障碍证据 |
|---|---|---|---|---|---|
| UP0-3 | J3（上排 y=43.25） | U7 输入（40.7..49.1） | **ALIGNED** | 2.25~5.85 | — |
| UP4-7 | J4（下排 y=63.95） | U7 输入（40.7..49.1） | **CROSSING** | 19.65~23.25 | 撞 U3 区域 + mcio 电容墙 |
| DN0-3 | J3（上排 y=45.75） | U3 输出（58.7..67.1） | **CROSSING** | 12.35~16.1 | 撞 U7 区域 + mcio 电容墙 |
| DN4-7 | J4（下排 y=61.45） | U3 输出（58.7..67.1） | **ALIGNED** | 0.55~3.55 | — |
| REFCLK0/1 | J3/J2 | — | ALIGNED（In6 层贯穿） | — | — |

**8 对 CROSSING（UP4-7 + DN0-3）精确命中**。阈值数据驱动：cross_tol=9.0mm
（排中心距 18mm/2）、align_tol=8.4mm（芯片排带跨度，与实测 pad 对中心一致）。

## 2. M-C 预检（虚拟映射，改网表前验证）

建议映射（MCIO 端 lane 分组，模型输出）：
- lane0-3（J3 上排）↔ **U7**（上排）：UP0-3 + DN0-3
- lane4-7（J4 下排）↔ **U3**（下排）：UP4-7 + DN4-7

| 链路 | chip | conn | y_delta | 判定 |
|---|---|---|---|---|
| UP0-3 | U7 | J3 | 0.6 | **ALIGNED** |
| UP4-7 | U3 | J4 | 0.4 | **ALIGNED** |
| DN0-3 | U7 | J3 | 0.2 | **ALIGNED** |
| DN4-7 | U3 | J4 | 0.0 | **ALIGNED** |

**16 链路全 ALIGNED**；交叉验证旧映射正确判 CROSSING（防假成功）。

## 3. M-D 实施修正（J2 端方向语义——关键修订）

**J2 连接器 RX/TX 是方向语义，不是 lane 分组**：
- J2/RX 引脚（物理上半 y 42.9..53.1）= host 接收端 = **UP 输出**用（ReDriver TX → J2/RX）
- J2/TX 引脚（物理下半 y 54.3..64.5）= host 发送端 = **DN 输入**用（J2/TX → ReDriver RX）
- 错误尝试（DN0-3 输入改用 J2/RX4-7 上半）→ 方向反 + LOGIC-05 差分链无驱动 FAIL
- **修正：J2 端保持方向映射（UP 输出 → J2/RX0-7、DN 输入 ← J2/TX0-7）**

J2 端物理约束：U7（上排）的 DN0-3 输入从 J2/TX（下半）到 U7 上排、U3（下排）
的 UP4-7 输出到 J2/RX（上半）——走 J2_TO_U 走廊两排间隙（非拓扑必交叉），
**布线层验证（M-E 容量地图）**，探针 J2 端段标 EVIDENCE_ONLY（不判拓扑交叉）。

## 4. 最终网表映射（M-D 实施，节点归属已验证）

| 链路 | MCIO 端 | 芯片端 | J2 端 | 方向 |
|---|---|---|---|---|
| UP0-3 | J3/TX0-3 | U7/RX0-3 | U7/TX0-3 → J2/RX0-3 | UP（MCIO→J2）|
| DN0-3 | J3/RX0-3 ← U7/TX4-7 | U7/RX4-7 | J2/TX0-3 → U7/RX4-7 | DN（J2→MCIO）|
| UP4-7 | J4/TX0-3 | U3/RX0-3 | U3/TX0-3 → J2/RX4-7 | UP |
| DN4-7 | J4/RX0-3 ← U3/TX4-7 | U3/RX4-7 | J2/TX4-7 → U3/RX4-7 | DN |

验证：节点归属 10 网全 PASS + 100 PCIE 网完整 + U7/U3 各 32 引脚全接入 +
LOGIC-05 PASS + ERC 0 + 出图门禁 PASS（M-D 全部通过）。

## 5. 待 M-E 验证（布线层）

- U7 的 DN0-3 输入（J2/TX 下半 → U7 上排）走廊容量
- U3 的 UP4-7 输出（U3 下排 → J2/RX 上半）走廊容量
- 16 对全量求解 SOLVED + P/N 断言 + 等长 <0.15 + 单对 <5s
