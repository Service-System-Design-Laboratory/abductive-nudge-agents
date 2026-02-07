#!/bin/bash
# 実験進捗モニター
# 使い方: bash newresearch/check_progress.sh
#   または: watch -n 30 bash newresearch/check_progress.sh  (30秒ごと自動更新)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="${SCRIPT_DIR}/results/runs"
LOG="${SCRIPT_DIR}/results/rerun_remaining_log.txt"
TODAY="$(date '+%Y-%m-%d')"

echo "=========================================="
echo " 実験進捗モニター  $(date '+%H:%M:%S')"
echo "=========================================="

# 各条件の完了数
A=$(ls -d "$BASE/A/${TODAY}"* 2>/dev/null | wc -l)
B=$(ls -d "$BASE/B/${TODAY}"* 2>/dev/null | wc -l)
C=$(ls -d "$BASE/C/${TODAY}"* 2>/dev/null | wc -l)
D=$(ls -d "$BASE/D/${TODAY}"* 2>/dev/null | wc -l)
TOTAL=$((A + B + C + D))

echo ""
echo "  条件A (Full)   : ${A}/30"
echo "  条件B (−PKG)   : ${B}/30"
echo "  条件C (−RAG)   : ${C}/30"
echo "  条件D (Single) : ${D}/30"
echo "  ─────────────────────"
echo "  合計           : ${TOTAL}/120"
echo ""

# プログレスバー
PCT=$((TOTAL * 100 / 120))
BAR_LEN=40
FILLED=$((PCT * BAR_LEN / 100))
EMPTY=$((BAR_LEN - FILLED))
BAR=$(printf '%0.s█' $(seq 1 $FILLED 2>/dev/null))
SPACE=$(printf '%0.s░' $(seq 1 $EMPTY 2>/dev/null))
echo "  [${BAR}${SPACE}] ${PCT}%"
echo ""

# プロセス状態
PID=$(pgrep -f "newresearch.runner" 2>/dev/null)
if [ -n "$PID" ]; then
    echo "  プロセス稼働中 (PID: $PID)"
else
    echo "プロセス停止中"
fi

# 最新の実験
echo ""
echo "--- 最新のログ ---"
grep -E "Experiment|Pipeline complete|SinglePipeline complete|FAILED" "$LOG" 2>/dev/null | tail -3
echo ""
