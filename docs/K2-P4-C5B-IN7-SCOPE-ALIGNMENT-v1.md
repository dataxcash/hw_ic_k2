# K2 · P4 · C5b / IN-7「回避区开关」口径对齐 + 更强读法不可达证明 · v1 · 2026-09-17

## 0. 一句话结论

`ESC_J2/J3/J4/U6` 四区在 l5 板上**均已 `copperpour not_allowed`** ⇒ 按已裁口径（**5 开关 ≥1 非 allowed**）**IN-7 = 达成**。
「不含 copperpour」的更严读法**在本板几何上不可达**（实测：`pads → not_allowed` 触发 **199 条 `items_not_allowed`**，全板违规 51→250）。
本件据此把 manifest 草案的实现对齐已裁口径，并把「口径强度」作为待监理裁定项上报（**不做静默收窄**）。

## 1. 已裁口径（三处一致，均以 5 开关为准）

| 出处 | 原文要点 |
|---|---|
| `#K2-17 §三 补正 2` | 缺陷定义：「板侧 `ESC_J2/J3/J4/U6` **4 区 × 5 开关（tracks/vias/pads/copperpour/footprints）全部 = `allowed`** = 空操作」 |
| `#K2-17 §五`（P4 施工项） | 「4 个 `ESC_*` keepout 开关落为 **≥1 非 `allowed`**」 |
| `K2-RULING-p3-closure-and-p4-open-v1 §C5b` | 「板侧每区 ≥1 非 `allowed`」；ENG `K2-P4-CONSTRUCTION-STATUS-v1.md` 已据此记 **IN-7 达成**（`zone_fills = disallow`） |

**无任何裁定**把 `copperpour` 排除在开关集之外。

## 2. 板侧现状（l5 = `d9813bc554a2d611`，只读复算）

| 区 | bbox (mm) | tracks | vias | pads | copperpour | footprints | 达标 |
|---|---|---|---|---|---|---|---|
| `ESC_U6` | 82.10,49.11 – 105.34,58.29 | allowed | allowed | allowed | **not_allowed** | allowed | ✅ |
| `ESC_J3` | 53.45,42.40 – 65.55,46.60 | allowed | allowed | allowed | **not_allowed** | allowed | ✅ |
| `ESC_J4` | 53.45,60.60 – 65.55,64.80 | allowed | allowed | allowed | **not_allowed** | allowed | ✅ |
| `ESC_J2` | 131.50,42.225 – 136.15,65.175 | allowed | allowed | allowed | **not_allowed** | allowed | ✅ |

⇒ 不达标区 **0/4**（已裁口径）。

## 3. 更强读法不可达证明（实测）

| 更严选项 | 区内容物（实测） | 设为 `not_allowed` 的后果 |
|---|---|---|
| `pads` | 区内 pad 存在（`U6` 354 球 + `J2/J3/J4` 焊盘） | DRC `items_not_allowed` = **199**；全板违规 **51 → 250** ⇒ 不可行 |
| `tracks` | F.Cu 段 4 区 = **181 / 125 / 213 / 336** | 必然海量违规 ⇒ 不可行 |
| `vias` | via 4 区 = **46 / 15 / 17 / 258** | 必然海量违规 ⇒ 不可行 |
| `footprints` | 区即 `U6/J2/J3/J4` 的逃逸走廊（封装/庭院在内） | 不可行 |

⇒ **唯一可行的非 `allowed` 开关 = `copperpour`**，且语义正当：**逃逸走廊不得被铺铜填死**（铺铜会吃掉布线通道）。

> **方法学更正（留痕）**：本件初测「区内 pad = 0」为**错** —— 封装内 pad 的 `(at x y)` 是**相对坐标**，须先加封装原点。**判据以 DRC 为权威**（0 → 199 即由此暴露）。该错误未进入任何判据实现（v2.2 的实现只用 keepout 开关，不做 pad 包含判定）。

## 4. 处置与结果

- manifest 草案 / 判定器草案 **v2.2** 对齐已裁口径：`esc_keepout_unrestricted` = 「5 开关全 `allowed`」的 `ESC_*` 区数，要求 **== 0**；
  并**并列上报**两个强度指标：`esc_copper_only`（仅 copperpour 受限）= **4**、`esc_unrestricted_4sw`（更严 4 开关口径）= **4**。
- 正控（l5 板）：`board_frame_and_keepout` **PASS** ⇒ 判定器 **PASS 10 → 11 / FAIL 8 → 7**；唯一变化项 = 本项。
- 7 件负控（m1..m7）逐件复跑 **无回归**（各件增量与 v2.1 同）。

## 5. 待监理裁定（口径强度，非 ENG 可默定）

1. **认已裁口径** ⇒ 本项 PASS，J-8「回避区」腿闭合；或
2. **要更强齿** ⇒ 须把 `ESC_*` 区内铜**移出走廊**（L2 走廊重解；代价大，且与 T-32「南侧 y68..78 为唯一长距离通道」用途直接冲突）⇒ 须另裁。

## 6. 复跑命令

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 现状开关（只读）
python3 - <<'PY'
import re
t = open('k2/hw/k2_v4_8L.l5.kicad_pcb', encoding='utf-8').read()
for m in re.finditer(r'\n\t\(zone\n', t):
    s = m.start()+1; e = t.find('\n\t)\n', s); blk = t[s:e+4]
    nm = re.search(r'\(name "(ESC_[^"]*)"\)', blk)
    if nm: print(nm.group(1), re.findall(r'\((tracks|vias|pads|copperpour|footprints) (allowed|not_allowed)\)', blk))
PY
# ② 更强读法后果（在 /tmp 造变体后跑 DRC；勿动仓库板）
#    把 4 区 (pads allowed) → (pads not_allowed)，临时目录内配同名 pro + fp-lib-table + lib/ForgeOS.pretty
#    AppDir/bin/kicad-cli pcb drc --format json --severity-error --severity-warning --output /tmp/d.json <变体板>
#    期望：items_not_allowed = 199（总违规 250）
# ③ 判定器（仓库件）
python3 k2/docs/drafts/p4-manifest-completion-v2/adjudicate.draft-v2.py --project k2 \
  --manifest k2/docs/drafts/p4-manifest-completion-v2/manifest.k2.draft-v2.yaml \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --kicad-cli AppDir/bin/kicad-cli \
  --measure-out /tmp/m.json --out /tmp/v.json     # 期望 PASS 11 / FAIL 7
```

—— ENG（ARCHER）· 2026-09-17 · 依据 `#K2-17 §三/§五` + `K2-RULING-p3-closure §C5b`
