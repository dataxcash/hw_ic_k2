# CO-112 — L2 声明式施加：3 个 bridge zone = **B.Cu 桥**（step ②c）+ In5 区域条件参考口径 + 走廊 worklist

- 判定：**`L2_DECLARED_NO_SPEC_CHANGE`**（CO-105 先例：声明式施加、零 SPEC/板改动、**不重基线**）
- 触发：CO-109/110/111 确立「bridge zone = B.Cu、In4 走廊空洞按设计」后仍缺声明式施加
- 复现：`python3 tools/p3_v57_co112_bcu_bridge_declaration.py`

## 1. 四项声明（坐标只取自声明源，零坐标搜索）

**D1 3 个 bridge zone = B.Cu 桥**（`layer` 字段 `In4.Cu` 仅为 In4-可达性簿记）：

| zone | bridge 层 | 声明几何带 | 来源 |
|---|---|---|---|
| `P3V3_BCU_BRIDGE_IN4` | B.Cu | 1 带 `y[33.3,35.0]×x[23.3,90]` | basis 文本正则抽取 |
| `P3V3_AUX_BCU_BRIDGE_IN4` | B.Cu | 2 带 `y[47.75,52.35]×x[46,62]`、`y[61.9,64.35]×x[53.75,62]` | basis 文本正则抽取 |
| `MCU_VDD_BCU_RESISTORS_IN4` | B.Cu | 1 带 = 已声明 **via palette 的轴对齐 bbox** `y[40.0,70.5]×x[50.2,57.55]` | 声明 via（固定规则；**provisional**，L3 细化） |

**D2** 这 3 个 zone 的 targets 经 B.Cu 桥接 ⇒ In4-平面可达性 requirement 对其**语义不适用（N/A）**（镜像 CO-105 V1，≠「未覆盖」）；其 `polygons=[]` **不构成缺陷**。

**D3 In5 区域条件参考口径**（口径声明，**不改 SPEC 字节**）：In4 有铜处 `refs=[In4,In6]`（symmetric stripline）；走廊 x∈(49.8,88.37) 处 **`refs=[In6]` 单参考**。覆盖长 1632.5mm / 走廊长 1094.8mm。

**D4 走廊 worklist**：16 个 PCIe 网的走廊长度（合计 1094.8mm）⇒ 交 SI9000 + 板厂阻抗券终判。

## 2. 机判 + 牙齿
`D1`/`D2`/`D3`/`D4` 全 True；牙齿 `synthetic_no_bcu_flagged`、`band_extraction_nonvacuous`（≥3 带）通过。

## 3. 关键非声明（防误读）
- **In5 PCIe 走廊阻抗暴露（CO-111，40.1% / 1094.8mm）不因本件减轻**；本件只把 bridge 几何与参考口径**声明化**。
- 零 SPEC/板/阈值/冻结源改动；不改 CO-98/CO-106 记录字节；终判 = 外部（SI9000 + 板厂券）。
- `MCU_VDD` 带为**声明的 provisional bbox**（basis 无 band），须 L3 细化；P3V3/P3V3_AUX 带为 basis 明文。
