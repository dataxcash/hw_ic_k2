# `k2/fab/` —— 制造输入件（P4）

| 件 | sha256(16) | 口径 / 用途 | 生成器 |
|---|---|---|---|
| `k2_v4_bom.csv` | `9e4ddf4a44302b76` | **ref 集 BOM**（`Ref` 头 + **每行一 ref**，55 refs）：满足 `_shared/eda_core/pipeline/checks.py::check_bom_consistent` 的消费口径（`row[0].split(",")`），是 `k2/pipeline.yaml` 安装的**具名前置**（#K2-23 §四 优先序 5） | `k2/tools/k2_p4_bom_gen_v1.py` |

## 口径说明（勿误用）

- **「每行一 ref」是正确性前提，不是风格**：`check_bom_consistent` 逐行 `csv.reader(row)[0].split(",")` ⇒ 未加引号的多 ref 同行会被拆列、只读到第一个 ⇒ 实测误报「BOM 与 sch 不同步」（inc58 §0-5；inc63 §0-3 负控：打包成 5 行即 FAIL）。
- **来源 = 真 sch netlist**（`kicad-cli sch export netlist --format kicadsexpr`，经 `$SHARUN`），**不读板 / 不读 SPEC**（避 C-1）；并与真源 `project.yaml::nets_yaml`（乙 = `errata-1`）的 55 placements **交叉核对**，不一致即 fail-closed。
- **本件只是「判据消费口径」的 ref 集**；含 `Value`/`Footprint`/`Qty`/`LCSC` 的**交付级 BOM 属 P5 交付面**（另件另裁）——**勿把本件当交付 BOM**。
- 生成（dry-run 只打印/校验；写仓库须双闸）：

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
python3 k2/tools/k2_p4_bom_gen_v1.py --out /tmp/opencode/k2_v4_bom.csv          # dry-run/沙箱
python3 k2/tools/k2_p4_bom_gen_v1.py --apply --confirm-repo-write               # 落本目录（T-41/T-22）
```

授权：#K2-23 §四 优先序 5；骨架与实测见 `k2/docs/K2-P4-BOM-GENERATOR-SKELETON-AND-DRYRUN-v1.md`。
