#!/usr/bin/env bash
# K2 · (a) B.Cu 车道 —— **确定性复现链**（只读 → 工作令 → 套用 → DRC）
# 用法: tools/k2_p4_b2_bcu_repro_v1.sh <board.kicad_pcb> <workdir>
#   例: tools/k2_p4_b2_bcu_repro_v1.sh /tmp/opencode/w3/c.kicad_pcb /tmp/opencode/repro
# 说明: 输入板须与同名 .kicad_pro/.kicad_prl 同目录（kicad-cli DRC 需要）。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BOARD="${1:?board path}"; W="${2:?workdir}"
APPDIR="$ROOT/AppDir"
MOVABLE="I2C1_SDA,P3V3_AUX,DS320_STRAP_B_ADDR0_15-8,PERSTA#,PWR_BTN_ISO"
mkdir -p "$W"
echo "[1/4] dump（pcbnew 侧 · 解释器 AppDir/usr/bin/python3.11）"
PYTHONPATH="$APPDIR/shared/lib/python3.11/dist-packages" "$APPDIR/usr/bin/python3.11" \
  "$ROOT/k2/tools/k2_p4_b2_board_dump_v1.py" --board "$BOARD" --out "$W/dump.json"
echo "[2/4] 配对守恒布线器 v2（协商拥塞 + rip-up · 确定性 seed）"
python3 "$ROOT/k2/tools/k2_p4_b2_bcu_router_v2.py" --model "$W/dump.json" --out "$W/wo_v2.json" \
  --cell 0.2 --iters 16 --movable-nets "$MOVABLE"
echo "[3/4] 套用（换 span / 删腿 / 铺线 / stub / 铺铜重灌）"
PYTHONPATH="$APPDIR/shared/lib/python3.11/dist-packages" "$APPDIR/usr/bin/python3.11" \
  "$ROOT/k2/tools/k2_p4_b2_bcu_apply_v1.py" --in "$BOARD" --workorder "$W/wo_v2.json" \
  --out "$W/applied.kicad_pcb" --ledger "$W/apply_ledger.json"
cp -f "${BOARD%.kicad_pcb}.kicad_pro" "$W/applied.kicad_pro" 2>/dev/null || true
cp -f "${BOARD%.kicad_pcb}.kicad_prl" "$W/applied.kicad_prl" 2>/dev/null || true
echo "[4/4] kicad-cli DRC"
"$APPDIR/bin/kicad-cli" pcb drc --severity-all --format json --output "$W/drc.json" "$W/applied.kicad_pcb"
echo "sha256:"; sha256sum "$W/dump.json" "$W/wo_v2.json" "$W/applied.kicad_pcb" "$W/drc.json"
