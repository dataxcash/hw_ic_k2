# K2 · P4 · **`k2/fab/k2_v4_bom.csv` 生成骨架 ＋ 沙箱演练**（真 check 实测 · 含口径负控）· v1 · 2026-09-18

> 缘起：handoff inc64 §6-3-(n)「`k2/fab/k2_v4_bom.csv` **生成脚本骨架细化 + 沙箱演练**（§5-D(iv)，接 inc58/59；**只写 `/tmp`**，BOM schema＝每行一 ref）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 骨架/镜像**，仓库零载体改动（仅新增本证据件）。
> 锚：真 sch `k2/hw/sch/k2_sch.kicad_sch` · sch 真源 `dd794c54f7ce7417` · `errata-1` `17d540f058631a5e`；判据 `check_bom_consistent`（`_shared/eda_core/pipeline/checks.py`，pin `e88c70aaa56ce22f`）；kicad-cli **10.0.5**；全修共享树 `/tmp/opencode/inc58/shared_full`（checks `0cbd9a478c694a12`）。
> 装置（`/tmp`，易失）：骨架 `/tmp/opencode/inc63/bom_gen.sh` **`3a5575abb1b94707`** · 产出 `k2_v4_bom.r1.csv` **`9e4ddf4a44302b76`**（r1==r2）· 口径负控 `bom_packed.csv` `c18ccb8db5c6b88c` · 端到端镜像 `sandbox/mirror`（日志 `caseB.log` `fb019e8fd69c715f`）。

## 0. 结论（五条）

1. **骨架已成件并实测**：`kicad-cli sch export netlist --format kicadsexpr` → 取 `(comp (ref "…"))` 集 → 排序去重 → 写 `Ref\n<ref>\n…`。
   **产出 55 refs，两次运行同 sha `9e4ddf4a44302b76`（T-38 确定性）**；**ref 集与 j9 草案 BOM `ce2bb814f31be54b` 完全相同**（n=55，差集 ∅）。
2. **真 check 实测 PASS**：以**真 `check_bom_consistent`**（全修 `checks.py`）直跑 ⇒ `ok=True :: BOM 与 sch 同步 (55 器件)`。
3. **口径负控（决定性）**：把全部 ref 打包成 5 行逗号分隔（典型的「多 ref 同行且不加引号」写法）⇒ **FAIL**，`csv.reader` 实际只读到 **5** 个 ref（`netlist 独有 ['C78'…]`）。
   ⇒ **`schema` 必须每行一 ref**（`row[0]` 口径；inc58 §0-5 首次踩中，本件给出负控复现）。
4. **端到端镜像演练（容器式路径）**：`乙` 变体（`errata-1`）＋ 本骨架 BOM ＋ 修正 hook（`pre-commit.d3fix`）＋ 全修 engine ⇒
   `受影响项目: k2` · **`preflight/check[project_sch_coverage]: PASS`（＝D-4b 生效）** · `verify/sch_structural: PASS` · **`verify/netlist_connect: FAIL` 2 行（⑤ `C89/A`，唯一）⇒ 拒绝提交**。
   **注意顺序效应**：`cmd_verify` 首个 FAIL 即 `return 1` ⇒ `bom_consistent` 在该序下**不会被执行**，故 BOM 的 PASS 须由 §3 的直跑证明（本件已证）。
5. **落库归属属 §5-D(iv) 待裁**（`k2/fab/k2_v4_bom.csv` 的生成与落库归属）；本件**只出 `/tmp` 骨架与证据**，**未创建 `k2/fab/**`**、**未新增仓库内脚本**（避新增检查齿，owner ②）。
   **范围界定**：本件件只满足**判据消费口径**（ref 集）；**最终交付级 BOM**（含 Value/Footprint/Qty 的 fab BOM）属 P5 交付面，另件另裁——勿把本件当交付 BOM。

## 1. 骨架全文（`/tmp/opencode/inc63/bom_gen.sh` `3a5575abb1b94707`）

```bash
#!/usr/bin/env bash
# K2 · P4 · `k2/fab/k2_v4_bom.csv` 生成骨架（草案；来源＝真 sch netlist）
# 口径：**每行一个 ref**（`checks.check_bom_consistent` 用 csv.reader + row[0].split(",")
#       ⇒ 未加引号的多 ref 同行会被拆列、只读到第一个 ⇒ 实测误报不同步，见 inc58 §0-5）。
# 用法：K2_ROOT=<repo> bash k2_p4_bom_gen.sh [sch] [out]
set -euo pipefail
ROOT="${K2_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SCH="${1:-$ROOT/k2/hw/sch/k2_sch.kicad_sch}"
OUT="${2:-$ROOT/k2/fab/k2_v4_bom.csv}"
SHARUN_BIN="${SHARUN:-$ROOT/AppDir/sharun}"
[ -f "$SCH" ] || { echo "✗ sch 不存在: $SCH — fail-closed"; exit 2; }
[ -x "$SHARUN_BIN" ] || { echo "✗ SHARUN 不可执行: $SHARUN_BIN — fail-closed"; exit 2; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/opencode/k2_bom.XXXXXX")"; NET="$TMP/net.kicadsexpr"
"$SHARUN_BIN" kicad-cli sch export netlist "$SCH" --format kicadsexpr --output "$NET" >/dev/null
python3 - "$NET" "$OUT" <<'PY'
import pathlib, re, sys
net, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
text = net.read_text(encoding="utf-8")
refs = sorted({m.group(1) for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)', text)})
if not refs:
    raise SystemExit("✗ netlist 0 器件 — fail-closed")
if any("," in r or "\n" in r for r in refs):
    raise SystemExit("✗ ref 含逗号/换行 — 违反「每行一 ref」口径")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("Ref\n" + "\n".join(refs) + "\n", encoding="utf-8")
print(f"wrote {len(refs)} refs -> {out}")
PY
```
**设计约束**：① 来源＝**真 sch netlist**（不读板/不读 SPEC，避免 C-1）；② **fail-closed**（sch 缺 / SHARUN 不可执行 / 0 器件 / ref 含逗号换行 ⇒ 非零退出）；③ **确定性**（排序 + 去重 + 无时间戳 ⇒ 同输入同 sha，T-38）；④ **不新增检查齿**（只产数据，判据仍由既有 `bom_consistent` 承担）。

## 2. 产出实测

| 项 | 值 |
|---|---|
| 命令 | `K2_ROOT=<repo> bash bom_gen.sh <sch> <out>` |
| 产出 | `Ref` 头 ＋ **55** 行（每行一 ref）|
| sha16（两次运行） | `9e4ddf4a44302b76` == `9e4ddf4a44302b76` ⇒ **确定性 ✓** |
| 与 j9 草案 BOM（`ce2bb814f31be54b`，`"Refs","Value","Footprint","Qty"` 4 列）对照 | **ref 集相同**（n=55，差集 ∅）⇒ 两种 schema 的 `row[0]` 均安全，本骨架取**更小面**（Value/Footprint 需另源、易陈旧） |

## 3. 真 check 实测（`check_bom_consistent` 直跑）

| 案 | BOM | 结果 |
|---|---|---|
| **本骨架产出** | 每行一 ref（55 行） | **`ok=True :: BOM 与 sch 同步 (55 器件)`** |
| j9 草案（4 列带引号） | 每行一 ref 在首列 | `ok=True :: BOM 与 sch 同步 (55 器件)` |
| **口径负控** | 5 行逗号打包（`c18ccb8db5c6b88c`） | **`ok=False :: BOM 与 sch 不同步: netlist 独有 ['C78','C79',…]`**；`csv.reader` 实读 ref 数＝**5** |

⇒ 「每行一 ref」不是风格偏好，是 `row[0].split(",")` 口径下的**正确性前提**。

## 4. 端到端镜像演练（容器式提交路径）

装置：`/tmp/opencode/inc63/sandbox/mirror/`（真 `k2/hw/sch/*.kicad_sch` 复制为真文件 · `errata-1` · 本骨架 BOM 落 `k2/fab/k2_v4_bom.csv` · `k2/pipeline.yaml`＝变体② 且 `nets_yaml→errata-1` · `_shared → /tmp/opencode/inc58/shared_full` · `git init`）＋ 修正 hook `/tmp/opencode/inc51/pre-commit.d3fix` ＋ `K2_NC_SOURCES=top,placements`（＝`D-7a`① ②，③ 关）。

| 步 | 输出 |
|---|---|
| `受影响项目: k2` | 容器式路径命中 ✓（D-3 修正生效） |
| `preflight/check[project_sch_coverage]: PASS` | **该行只在 D-4b 之后可能出现 ⇒ 提交期真强制已打通** |
| `verify/sch_structural: PASS` | 结构三基础 OK |
| `verify/netlist_connect: FAIL` | **2 行**：`网 'PWR_5V_KEY' 在 KiCad netlist 中不存在` ＋ `非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单` |
| 结论 | `rc=1` 拒绝提交；**失败项唯一＝⑤**（与 inc58 案 B 逐字一致）⇒ BOM 侧零贡献 |

**顺序效应提醒**：`cmd_verify` 在首个 FAIL 处 `return 1` ⇒ 本次 `bom_consistent` 未被执行；若监理采用「全 phase checks 都跑」的 `D-4b` 语义（§5-D(ii) 待裁），该序下才会看到 `bom_consistent: PASS`。**ENG 未据此改任何件**。

## 5. 落库归属与放行依赖（**待裁**）

| # | 事项 | 现状 | 归属 |
|---|---|---|---|
| 1 | `k2/fab/k2_v4_bom.csv` 生成与落库（§5-D(iv)） | 未落库（`k2/fab/` 不存在） | **待裁**；ENG 侧骨架已备 |
| 2 | 骨架的仓库位置（如 `k2/tools/k2_p4_bom_gen.sh`） | 未创建 | 待裁（**注意 owner ②：不得新增检查齿**；此件为数据生成器，非判据） |
| 3 | 是否保留 j9 草案的 Value/Footprint/Qty 列 | 未裁 | 若保留须另定**来源与新鲜度口径**（否则陈旧列反成隐患） |
| 4 | 与 `pipeline.yaml`/`errata-*` 的落库顺序 | 未裁 | **BOM 必须早于/同于 `pipeline.yaml`**（否则 D-2 `FileNotFoundError`，inc58 §0-1） |

## 6. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; W=/tmp/opencode/inc63
# ① 生成两次 → 比 sha（期望相同）
K2_ROOT=$PWD bash $W/bom_gen.sh $PWD/k2/hw/sch/k2_sch.kicad_sch $W/sandbox/a.csv
K2_ROOT=$PWD bash $W/bom_gen.sh $PWD/k2/hw/sch/k2_sch.kicad_sch $W/sandbox/b.csv
sha256sum $W/sandbox/a.csv $W/sandbox/b.csv | cut -c1-16         # 期望 9e4ddf4a44302b76 ×2
# ② 真 check 直跑（镜像内；期望 ok=True (55 器件)）
cd $W/sandbox/mirror && SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun PYTHONPATH=$PWD/_shared python3 -c "
import pathlib,sys; sys.path.insert(0,str(pathlib.Path('_shared').resolve()))
from eda_core.pipeline import checks
cfg={'_root':pathlib.Path('k2').resolve(),'_yaml_path':pathlib.Path('k2/pipeline.yaml')}
print(checks.check_bom_consistent(cfg, {'sch':'k2/hw/sch/k2_sch.kicad_sch','bom_csv':'k2/fab/k2_v4_bom.csv'}))"
# ③ 端到端（容器式；期望 rc=1 且失败项唯一＝⑤）
cd $W/sandbox/mirror && SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun K2_NC_SOURCES=top,placements \
  bash /tmp/opencode/inc51/pre-commit.d3fix; echo "rc=$?"
```

## 7. 边界

本件**只读 + `/tmp` 骨架/镜像**：未改真源/SPEC/图纸/生成器/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 骨架 `3a5575abb1b94707` · 产出 `9e4ddf4a44302b76` · 真 check pin `e88c70aaa56ce22f`（全修版 `0cbd9a478c694a12`）
