#!/bin/bash
# Parallel runner for Team Alpha HP fetching (multiple processes).
# Each batch runs in background. SQLite WAL mode is enabled to allow concurrent writes.

set -e

cd /Users/nishimura+/projects/research/jpms-db

# Enable WAL mode for concurrent writes
sqlite3 v2/jpms_v2.db "PRAGMA journal_mode=WAL;"

# Run alpha-01〜12 in parallel (6 at a time to stagger load)
PARALLEL=${PARALLEL:-3}

ALL_TASKS=(alpha-01 alpha-02 alpha-03 alpha-04 alpha-05 alpha-06 alpha-07 alpha-08 alpha-09 alpha-10 alpha-11 alpha-12)

mkdir -p v2/codex_progress v2/codex_logs

run_batch() {
  local task=$1
  local list="v2/codex_tasks/${task}_schools.jsonl"
  local log="v2/codex_logs/${task}.log"
  local progress="v2/codex_progress/${task}.json"

  echo "[$task] Started" > "$log"
  local total=$(wc -l < "$list")
  local completed=0
  local phil=0
  local tt=0

  while IFS= read -r line; do
    sid=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])")
    out=$(python3 v2/scripts/fetch_school_hp.py --school-id "$sid" 2>&1 | tail -1)
    echo "[$task] $sid → $out" >> "$log"
    completed=$((completed+1))
    # Parse phil/tt from output
    p=$(echo "$out" | grep -oE "philosophies_added.: [0-9]+" | grep -oE "[0-9]+" | head -1 || echo 0)
    t=$(echo "$out" | grep -oE "testimonials_added.: [0-9]+" | grep -oE "[0-9]+" | head -1 || echo 0)
    phil=$((phil+p))
    tt=$((tt+t))
  done < "$list"

  python3 -c "
import json
print(json.dumps({
  'task_id': '$task',
  'team': 'alpha',
  'total_schools': $total,
  'completed': $completed,
  'philosophies_added': $phil,
  'testimonials_added': $tt,
  'status': 'completed',
  'ts': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
}, ensure_ascii=False, indent=2))
" > "$progress"
  echo "[$task] DONE: $completed/$total schools, phil=$phil, tt=$tt"
}

export -f run_batch

# GNU parallel preferred, fallback to xargs
if command -v parallel >/dev/null 2>&1; then
  printf '%s\n' "${ALL_TASKS[@]}" | parallel -j $PARALLEL run_batch {}
else
  # Use xargs with -P
  printf '%s\n' "${ALL_TASKS[@]}" | xargs -P $PARALLEL -I {} bash -c 'run_batch "$@"' _ {}
fi

echo "All Alpha tasks completed"
