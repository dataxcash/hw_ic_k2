#!/bin/sh
# eda_eng —— K2 独立确定性 EDA 工程软件入口（#K2-358）。无 LLM 在场可完整运行。
K2="$(cd "$(dirname "$0")/.." && pwd)"
exec "${EDA_ENG_PY:-python3}" "$K2/tools/eda_eng_run.py" "$@"
