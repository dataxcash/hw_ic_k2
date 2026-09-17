# k2/docs/drafts/p4-manifest-completion-v2/ —— P4 判据缺口补齐草案（ENG 草案件）

> 状态：**未安装、未签认**（`not_countersigned: true`）。`criteria/`（0444, owner=ic_hw_gate）逐字节未动。
> 依据：监理 `#K2-20 §二`（`criteria/manifest` 不予签认 ⇒ 须先补齐转写）+ `§五-2`（ENG 起草 → 监理正/负控复验 → 版本 bump 安装 → 监理签认）。
> 提交与证据说明见：`k2/docs/K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md`。

## 件清单（sha256/16）

| 件 | sha256(16) | 说明 |
|---|---|---|
| `manifest.k2.draft-v2.yaml` | `360b3d1cf377bedb` | 转写补齐版判据清单草案（含 `null` = 待监理填的取值） |
| `adjudicate.draft-v2.py` | `f7b23e99dc277ec6` | 判定器草案（实现；自跑 kicad-cli DRC，防伪造绿） |
| `make_negatives_v2.py` | `8a000f5c294e3a8d` | 负控造件脚本 v2（格式无关括号匹配；m6 改电气级 pad 尺寸突变） |

## 修订（v2.2 · 2026-09-17）

- **C5b/IN-7 口径对齐**：`board_frame_and_keepout` 的回避区腿改为按已裁口径（`#K2-17 §五`：**5 开关含 copperpour，每区 ≥1 非 allowed**），并并列上报「仅 copperpour 受限」/「更严 4 开关口径」两个强度指标。v2.1 曾注「copperpour 不计」= 比裁定更严，且实测在本板**不可达**（`pads→not_allowed` ⇒ 199 条 `items_not_allowed`）⇒ 会使 P4 结构上不可闭。见 `k2/docs/K2-P4-C5B-IN7-SCOPE-ALIGNMENT-v1.md`。
- 正控随之 **PASS 11 / FAIL 7**（唯一变化项 = `board_frame_and_keepout`）。

## 修订（v2.1 · 2026-09-17）

- 依 **#K2-19 §二 W-9**（k2 门 = k2-scoped）实现 `pipeline_present` 的 scope：新增 `manifest.pipeline_scope: [k2]` + 判定器按 scope 过滤 sch 目录 ⇒ 报 `k2/hw/sch` 1 目录（原 6 目录）。
- 两者 sha 随之为上表 v2.1 值；`make_negatives_v2.py` 未变。

## 与 `/tmp` 副本的关系

本目录是 `/tmp/opencode/p4/draft/` 中同名草案件的**仓库耐久副本**（`/tmp` 为易失区）。
`manifest.k2.draft-v2.yaml` 与 `adjudicate.draft-v2.py` 与 `/tmp` 原件**逐字节同**（sha 一致）；
`make_negatives_v2.py` = `/tmp/opencode/p4/draft/make_negatives.py` 的 v2（2026-09-17 修：适配增量 16 板的新封装头格式 `\t(footprint "LIB:NAME"`，旧正则致 m6 未注入）。

## 变更纪律

`criteria/` 是只读冻结件（`897e8bfd…` / `7ce08757…`）。本目录的草案只有在监理完成正/负控复验后，才由**属主侧**以版本 bump 安装并签认。
