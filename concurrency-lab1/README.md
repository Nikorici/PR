# Lab 1 — Concurrency in Practice

Python 3.14, free-threaded build (`python3.14t`, no GIL), so threads run Python code in parallel.
Standard library only; `matplotlib` is needed for the charts.

| File | What it does |
|---|---|
| `gen.py` | writes `data/numbers.txt` (50 000 000 ints), the 8 parts in `data/parts/`, and the reference totals in `data/expected.txt` |
| `lab.py` | the one program: every task and setting is a command-line argument |
| `test_lab.py` | self-check of every task on small files, many thread counts |
| `run.sh` | runs a whole task, checks every total against `data/expected.txt`, writes `results/<task>.csv` |
| `charts.py` | draws `charts/*.png` from `results/*.csv` |
| `report/` | the report (PDF) |

## Setup

```bash
uv python install 3.14t          # free-threaded CPython, puts python3.14t in ~/.local/bin
python3 gen.py data              # ~15 s, prints the reference totals
python3.14t test_lab.py          # prints "ok"
```

## Running one configuration

```bash
python3.14t lab.py 1a data/numbers.txt 8          # Task 1a, 8 threads
python3.14t lab.py 1b data/numbers.txt 1          # Task 1b version 1|2|3, threads = logical CPUs
python3.14t lab.py 1c data/numbers.txt 4          # Task 1c, 4 workers + 1 reader
python3.14t lab.py 2 /run/media/$USER/USB/parts 2 # Task 2, 2 threads
python3.14t -X gil=1 lab.py 1a data/numbers.txt 8 # same as 1a but with the GIL turned back on
```

Each run prints one CSV line: `task,threads,time_ms,peak_kb,negative,positive,zero,total`.
Time covers only the counting (for 1b, loading the array is not timed); peak memory is the
process's maximum resident set size (`getrusage`).

## Running every task

```bash
./run.sh 1a        # 1, 2, 4 … 64 threads, 3 runs each (RUNS=5 ./run.sh 1a for more)
./run.sh 1a-gil    # Task 1a again with the GIL on, for comparison
./run.sh 1b        # versions 1, 2, 3, 3 runs each
./run.sh 1c        # 1, 2, 4 … 64 workers, 3 runs each
python3 charts.py
```

## Task 2 (USB drive)

```bash
lsblk -o NAME,TRAN,SIZE,MODEL,FSTYPE      # find the drive, e.g. sda with partition sda1
lsusb -t                                  # 480M = USB 2.0, 5000M = USB 3.x
udisksctl mount -b /dev/sda1              # mounts at /run/media/$USER/<LABEL>
mkdir -p /run/media/$USER/<LABEL>/parts && cp data/parts/*.txt /run/media/$USER/<LABEL>/parts/ && sync
./run.sh 2 /run/media/$USER/<LABEL>/parts
```

Before each of the three runs the script waits for Enter. In between, eject, unplug and replug:

```bash
udisksctl unmount -b /dev/sda1 && udisksctl power-off -b /dev/sda
# unplug, plug back in
udisksctl mount -b /dev/sda1
```

Then `python3 charts.py` again for `charts/task2.png`.