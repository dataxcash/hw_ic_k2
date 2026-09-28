#!/usr/bin/env python3
"""eda_eng 启动器（bootstrap）—— 把本目录入 sys.path 后调 CLI。
使 `-m` 与 PYTHONPATH 都不必需（含冻结/打包的 KiCad python 亦可）。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eda_eng.cli import main          # noqa: E402
sys.exit(main())
