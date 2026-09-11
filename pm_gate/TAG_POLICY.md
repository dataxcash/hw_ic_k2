# TAG 政策（k2 版本门禁）— v1（2026-09-11，整改通知 #04）

> 依据：监理整改通知 #04「里程碑 TAG 缺失 + COMMIT/PUSH 未核验」。
> 效力：本政策为本仓里程碑打标与提交/推送核验的**强制规则**。

## 1. 何时打 tag（必打）
- **每次 gate 切换**（G0..G7 任一 gate 的 PASS/FAIL/REOPEN 冻结）；
- **大里程碑**：机制/契约修订、层意图派生、叠层采用、独立验证 PASS、reopen/rollback；
- **发布候选/交付**（rc、交付包）。

## 2. 命名
`k2-v57-<gate|milestone>-<desc>`（annotated，非 lightweight）。
已打：
| tag | 目标 commit | 含义 |
|---|---|---|
| `k2-v57-g3-freeze-rc1` | (09-10) | G3 冻结 rc1 |
| `k2-v57-g4-w3-feasible-all` | `06be35d` | G4/W3 FEASIBLE_ALL（W3-CN.25, c17c5a42） |
| `k2-v57-g5-w4-pass` | `fc38854` | G5/W4 PASS |
| `k2-v57-g6-l4-pass` | `09bceed` | G6/L4 PASS |
| `k2-v57-g7-l5-fail` | `56395cd` | G7/L5 FAIL → reopen W3 |
| `k2-v57-m03-layer-intent-derived` | `ba16057` | #03 层意图容量闭合派生（LID.1） |
| `k2-v57-lid1-8l-adopted` | `558b0ce` | 8L 采用（LID.1 落地） |

## 3. tag message 必含
`gate` 判定 + **关键工件路径/revision + sha16** + `date`（可选：复现命令）。

## 4. COMMIT / PUSH 纪律
- 里程碑 commit **必 push**（先 `k2` 再父仓 bump）。
- 打 tag 后 **`git push origin --tags`**；核验 `git ls-remote --tags origin` 含该 tag 且 `^{}` 指向目标 commit。
- 里程碑前核验：`git status` 干净（除已声明的既有偏差，如 `? _shared`）；冻结四源 SHA 不变。
- **不得** rewrite 已 push 的里程碑 commit（禁 amend/rebase 已发布段）。

## 5. 自动核验（里程碑收尾必跑）
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
git rev-list --left-right --count origin/main...HEAD   # 期望: 0	0
git tag -n1 | tail
git ls-remote --tags origin | grep k2-v57
sha256sum pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json \
  pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json \
  k2_v4.kicad_pcb _shared/eda_core/drc_rules.json | cut -c1-16
# 期望四源: 0bd52ed48e720b8c / a8ef3ea8ecff99d7 / f6273de613f43d05 / 0a459839e15960b8
```

## 6. 归档
每次打 tag 在 `.omo/start-work/ledger.jsonl` 记 `tag 名 + 目标 commit hash + gate`。
