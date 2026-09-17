# 判据草案 v3（= v2 + J-8 出框 + V3 机制）· ENG 起草区（**未安装；`criteria/` 未动**）

| 文件 | 说明 |
|---|---|
| `adjudicate.draft-v3.py` | **v2 草案的严格超集**（对 `k2/docs/drafts/K2-P4-criteria-draft-v2/adjudicate.py` `7cf8a50eb832c284` 的 diff 仅 **3 处 hunk**：新增 2 个 `--*-json` 参数、2 个测量装载、2 个检查块）。**未就地改 v2** |
| `manifest.k2.v3.yaml` | 安装件清单：`pads_within_outline` = `enabled: true`（消费 `pads_outline_json`）；`ref_plane_continuity` 仍 `enabled: false, pending: <阈值待监理>`（机制已实现，启用仅需一行 + `thresholds`） |
| `manifest.k2.control-v3.yaml` | **仅用于正负控**（把 `ref_plane_continuity` 置 `enabled: true` + `thresholds.ref_plane_continuity: {scope: nominal, min_coverage: 1.0}`）；**非安装件** |

## 两步跑法（gate 侧安装后）

```bash
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j8-v3-measurement-v1; C=k2/docs/drafts/p4-j8-v3-criteria-v3
# ① 测量（两件均为「无 verdict」测量件）
$K $D/measure_pads_within_outline.py --board <board> --json /tmp/pwo.json
$K $D/measure_ref_plane_continuity.py --board <board> --json /tmp/v3.json
# ② 判定（v3）
python3 $C/adjudicate.draft-v3.py --board <board> --manifest <manifest> … \
  --pads-outline-json /tmp/pwo.json --v3-plane-json /tmp/v3.json
```

- **证据陈旧即 FAIL**：两份测量 JSON 的 `board_sha16` 必须 == 受审板 sha16（同 `lib_electrical_level` 口径）；缺件亦 FAIL（fail-closed）。
- **V3 应然值待监理**（计划 §3.2）：可选 `scope: nominal`（zone 轮廓，本板 3653/3653）或 `scope: strict_filled` + `min_coverage`（含反焊盘空洞，本板 0.95 → 3162/3653）。ENG 只交测量与机制，不代定阈值。

详见 `k2/docs/K2-P4-CRITERIA-V3-INTEGRATION-EVIDENCE-v1.md`。
