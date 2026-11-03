#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=${PY:-python3.14t}
RUNS=${RUNS:-3}
THREADS="1 2 4 8 16 32 64"
expected=$(cat data/expected.txt)

new_csv() {
  mkdir -p results
  echo "task,threads,time_ms,peak_kb,negative,positive,zero,total,run" > "results/$1.csv"
}

measure() {
  local out=$1 check=$2 run=$3 line
  shift 3
  line=$("$@")
  if [ "$check" = yes ] && [ "$(cut -d, -f5-8 <<<"$line")" != "$expected" ]; then
    echo "WRONG TOTALS: $line (expected $expected)" >&2
    exit 1
  fi
  echo "$line,$run" | tee -a "$out"
}

case ${1:-} in
  1a)
    new_csv 1a
    cat data/numbers.txt > /dev/null
    for t in $THREADS; do for r in $(seq "$RUNS"); do
      measure results/1a.csv yes "$r" "$PY" lab.py 1a data/numbers.txt "$t"
    done; done ;;
  1a-gil)
    new_csv 1a-gil
    for t in $THREADS; do
      measure results/1a-gil.csv yes 1 "$PY" -X gil=1 lab.py 1a data/numbers.txt "$t"
    done ;;
  1b)
    new_csv 1b
    for v in 1 2 3; do for r in $(seq "$RUNS"); do
      measure results/1b.csv "$([ "$v" = 1 ] && echo no || echo yes)" "$r" "$PY" lab.py 1b data/numbers.txt "$v"
    done; done ;;
  1c)
    new_csv 1c
    for t in $THREADS; do for r in $(seq "$RUNS"); do
      measure results/1c.csv yes "$r" "$PY" lab.py 1c data/numbers.txt "$t"
    done; done ;;
  2)
    dir=${2:?usage: ./run.sh 2 <folder on the USB drive>}
    new_csv 2
    for t in 1 2 4; do
      read -rp "Eject, unplug and replug the USB drive, wait until $dir is mounted, then press Enter (threads=$t) "
      measure results/2.csv yes 1 "$PY" lab.py 2 "$dir" "$t"
    done ;;
  *)
    echo "usage: ./run.sh 1a | 1a-gil | 1b | 1c | 2 <folder on the USB drive>" >&2
    exit 1 ;;
esac
