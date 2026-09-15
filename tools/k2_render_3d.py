#!/usr/bin/env python3
import os
import re

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
MDL = "/home/fila/jqdDev_2025/ic_hw/AppDir/share/kicad/3dmodels"
WORK = "/tmp/opencode/k2render"

STEP = {
    "Capacitor_SMD:C_0402_1005Metric": "Capacitor_SMD.3dshapes/C_0402_1005Metric.step",
    "Capacitor_SMD:C_0603_1608Metric": "Capacitor_SMD.3dshapes/C_0603_1608Metric.step",
    "Capacitor_SMD:C_0805_2012Metric": "Capacitor_SMD.3dshapes/C_0805_2012Metric.step",
    "Resistor_SMD:R_0603_1608Metric": "Resistor_SMD.3dshapes/R_0603_1608Metric.step",
    "LED_SMD:LED_0603_1608Metric": "LED_SMD.3dshapes/LED_0603_1608Metric.step",
    "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm": "Package_SO.3dshapes/SOIC-8_5.3x5.3mm_P1.27mm.step",
    "ForgeOS:PinHeader_1x02": "Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x02_P2.54mm_Vertical.step",
    "ForgeOS:PinHeader_1x04": "Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x04_P2.54mm_Vertical.step",
    "ForgeOS:SOT23_BAT54C": "Package_TO_SOT_SMD.3dshapes/SOT-23.step",
    "ForgeOS:SOIC8_FRU": "Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step",
    "ForgeOS:OPTO_LTV356T": "Package_SO.3dshapes/SOP-4_4.4x2.6mm_P1.27mm.step",
    "ForgeOS:MCU_STM32G0_LQFP48": "Package_QFP.3dshapes/LQFP-48_7x7mm_P0.5mm.step",
    "DS320PR1601": "Package_DFN_QFN.3dshapes/QFN-64-1EP_9x9mm_P0.5mm_EP4.1x4.1mm.step",
}

PLASTIC = "0.07 0.07 0.08"
SHELL = "0.52 0.55 0.59"

CONN = {
    "ForgeOS:MCIO_4i_SFF-1016_RASide": dict(w=16.0, d=7.0, h=4.6, shell_t=0.8),
    "ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide": dict(w=25.0, d=6.0, h=5.2, shell_t=0.8),
}

U = 2.54


def _t(cx, cy, cz, sx, sy, sz, color, shin=0.15):
    return (
        "Transform { translation %g %g %g children [ Shape { appearance Appearance {"
        " material Material { diffuseColor %s specularColor 0.45 0.45 0.45 shininess %g } }"
        " geometry Box { size %g %g %g } } ] }\n"
        % (cx / U, cy / U, cz / U, color, shin, sx / U, sy / U, sz / U)
    )


def connector_wrl(w, d, h, shell_t):
    body_h = h - shell_t
    out = ["#VRML V2.0 utf8\n"]
    out.append(_t(0, 0, body_h / 2, w, d, body_h, PLASTIC))
    out.append(_t(0, 0, h - shell_t / 2, w + 0.4, d + 0.4, shell_t, SHELL, 0.6))
    out.append(_t(0, -(d / 2) - 0.2, body_h / 2, w + 0.4, 0.4, body_h, SHELL, 0.6))
    out.append(_t(0, d / 2 - 0.55, body_h * 0.55, w - 2.0, 1.1, body_h * 0.5, "0.03 0.03 0.03"))
    for sx in (-1, 1):
        out.append(_t(sx * (w / 2 - 0.6), -(d / 2) - 0.35, body_h * 0.5, 0.9, 0.7, body_h * 0.9, SHELL, 0.6))
    return "".join(out)


def find_close(text, start):
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced")


def model_block(path):
    return (
        '\t\t(model "%s"\n'
        "\t\t\t(offset (xyz 0 0 0))\n"
        "\t\t\t(scale (xyz 1 1 1))\n"
        "\t\t\t(rotate (xyz 0 0 0))\n"
        "\t\t)\n" % path
    )


def main():
    board = os.path.join(K2, "hw", "k2_v4_8L.l4.kicad_pcb")
    boxdir = os.path.join(WORK, "conn")
    os.makedirs(boxdir, exist_ok=True)
    conn_files = {}
    for libid, p in CONN.items():
        f = os.path.join(boxdir, re.sub(r"[^A-Za-z0-9]+", "_", libid) + ".wrl")
        open(f, "w").write(connector_wrl(**p))
        conn_files[libid] = f

    src = open(board).read()
    out, pos, stats = [], 0, {}
    missing = []
    pat = re.compile(r'\t\(footprint "([^"]+)"')
    while True:
        m = pat.search(src, pos)
        if not m:
            break
        libid = m.group(1)
        end = find_close(src, m.start() + 1)
        block = src[m.start():end + 1]
        if "(model " not in block:
            if libid in STEP:
                path = os.path.join(MDL, STEP[libid])
                if not os.path.exists(path):
                    missing.append((libid, path))
                block = block[:-1] + model_block(path) + "\t)"
                stats[libid] = stats.get(libid, 0) + 1
            elif libid in conn_files:
                block = block[:-1] + model_block(conn_files[libid]) + "\t)"
                stats[libid] = stats.get(libid, 0) + 1
            else:
                missing.append((libid, "无映射"))
        out.append(src[pos:m.start()])
        out.append(block)
        pos = end + 1
    out.append(src[pos:])
    dst = os.path.join(WORK, "k2_render.kicad_pcb")
    open(dst, "w").write("".join(out))

    total = sum(stats.values())
    print("副本 ->", dst)
    print("注入 %d 个模型，覆盖 %d 种封装" % (total, len(stats)))
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print("  %-44s x%d" % (k, v))
    if missing:
        print("未映射:", missing)


if __name__ == "__main__":
    main()
