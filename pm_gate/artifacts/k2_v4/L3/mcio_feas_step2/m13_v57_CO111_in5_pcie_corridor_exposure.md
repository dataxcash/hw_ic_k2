# CO-111 — L2 量化裁定：In5 PCIe 走廊参考缺失 **40.1%**（1094.8mm / 2727.3mm）

- 判定：**`L2_DECLARED_SI_EXPOSURE_EXTERNAL_TERMINAL`**
- 触发：CO-110 关闭 F-D（走廊空洞按设计）后仍缺「量」；本件把「54 段」量化为**长度占比**，并核对 L5 签核覆盖面
- 输入：SPEC rev-13 `7943be727a4f8ef9`｜图纸 `73c0066df83fa8c2`｜L5 SI 记录
- 工具 `tools/p3_v57_co111_in5_pcie_corridor_exposure.py`｜记录 `m13_v57_co111_in5_pcie_corridor_exposure.json`
- 复现：`../AppDir/usr/bin/python3.11 tools/p3_v57_co111_in5_pcie_corridor_exposure.py`

## 1. 量化（声明数据，无坐标搜索）

In4 走廊 x∈(49.8, 88.37) 内无声明 In4 铜（西区 x≤49.8 / 东区 x≥88.37）。In5 走线落在该带的**长度**：

| 指标 | 读数 |
|---|---|
| In5 走线总长 | 2727.3 mm |
| **无 In4 参考长度** | **1094.8 mm = 40.1%** |
| 受影响网 | 16 个，**全部为 PCIe 差分对**（PCIE_DN0–DN7 / PCIE_UP0–UP7；net_class `PCIe85`，target_zdiff **85Ω**） |
| 最差网 | `PCIE_UP4` **108.7mm / 50.5%**（其余 26–52%） |

## 2. 关键事实：L5 签核未覆盖阻抗

`m13_v57_l5_si_pi_emc_record.json` 的 SI 部分**只签** intra-pair skew（`skew_ok=true`，max 0.13mm ≤ 0.15），
并**声明**了阻抗模型（`impedance_model=JLC_SI9000_H1_5.0mil_Er1_4.3`，target 85Ω），但**无逐线阻抗核验字段**
⇒ 走廊内 In5 PCIe 的阻抗暴露**未被**现行 G7 签核覆盖（**不得视为已验**）。

## 3. 裁定（L2 自裁）

- **Q1（L2）** 走廊暴露 = **1094.8/2727.3mm = 40.1%** 的 In5 PCIe 走线长度（16 网；最差 `PCIE_UP4` 108.7mm）。
- **Q2（L2）** 受影响网**全部**为 PCIe85 阻抗受控差分对 ⇒ 走廊内 declared `symmetric_stripline(refs=[In4,In6])` **不成立**，属**实际阻抗暴露**，非可忽略项。
- **Q3（L2）** L5 SI 只覆盖 skew、**未**核验阻抗 ⇒ 该暴露在现行签核中**未验**，须显式登记。
- **Q4（EXTERNAL）** 终判 = **SI9000 + 板厂阻抗券**（不得以假设值代填）。
- **Q5（OWNER/LAYERED）** 若超规，补救层级：**(a)** 走廊补 In4 铜（**OWNER**：反转 PM T2-ECN）／**(b)** 改线或换层避开走廊（信号流向 ⇒ 或 **L1**）／**(c)** 走廊段宽-隙补偿（**L2**，须场解）。

## 4. 结论
- CO-108 F-D 从「未决前提」升级为**已量化的阻抗暴露**：In5 PCIe 有 40.1% 长度缺 In4 参考，且不在现行 SI 签核范围内。
- 该暴露的**消除或接受**取决于外部 SI 终判与（若需）owner 的走廊补铜决策；在此之前**不得**当作已闭合。
- 非声明：只读；不做阻抗数值计算；不改 SPEC/板/阈值/冻结源。
