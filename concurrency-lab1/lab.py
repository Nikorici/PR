import io
import os
import queue
import resource
import sys
import threading
import time
from array import array
from pathlib import Path

BLOCK = 64 << 10
BATCH = 10_000
QUEUE_BATCHES = 100

USAGE = """usage:
  lab.py 1a <file> <threads>
  lab.py 1b <file> <version 1|2|3> [threads]
  lab.py 1c <file> <workers>
  lab.py 2  <folder> <threads>"""


def count(nums):
    neg = pos = zero = 0
    for n in nums:
        if n < 0:
            neg += 1
        elif n > 0:
            pos += 1
        else:
            zero += 1
    return neg, pos, zero


def total(parts):
    neg = pos = zero = 0
    for n, p, z in parts:
        neg += n
        pos += p
        zero += z
    return neg, pos, zero


def blocks(f, size):
    carry = b""
    while size > 0:
        chunk = f.read(min(BLOCK, size))
        if not chunk:
            break
        size -= len(chunk)
        buf = carry + chunk
        cut = buf.rfind(b"\n") + 1
        carry = buf[cut:]
        yield buf[:cut]
    yield carry


def count_stream(f, size):
    return total(count(map(int, b.split())) for b in blocks(f, size))


def run_threads(target, n):
    threads = [threading.Thread(target=target, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def line_start(f, pos):
    if pos == 0:
        return 0
    f.seek(pos - 1)
    f.readline()
    return f.tell()


def task_1a(path, threads):
    size = os.path.getsize(path)
    results = [None] * threads

    def work(i):
        with open(path, "rb") as f:
            start = line_start(f, size * i // threads)
            end = line_start(f, size * (i + 1) // threads)
            f.seek(start)
            results[i] = count_stream(f, end - start)

    run_threads(work, threads)
    return total(results)


def load(path):
    nums = array("i")
    with open(path, "rb") as f:
        for b in blocks(f, os.path.getsize(path)):
            nums.extend(map(int, b.split()))
    return nums


def task_1b(nums, version, threads):
    counts = [0, 0, 0]
    lock = threading.Lock()
    results = [None] * threads

    def part(i):
        return nums[len(nums) * i // threads : len(nums) * (i + 1) // threads]

    def unsynchronised(i):
        for n in part(i):
            k = 0 if n < 0 else 1 if n > 0 else 2
            counts[k] += 1

    def locked(i):
        for n in part(i):
            k = 0 if n < 0 else 1 if n > 0 else 2
            with lock:
                counts[k] += 1

    def per_thread(i):
        results[i] = count(part(i))

    run_threads((unsynchronised, locked, per_thread)[version - 1], threads)
    return total(results) if version == 3 else tuple(counts)


def task_1c(path, workers):
    q = queue.Queue(maxsize=QUEUE_BATCHES)
    results = [None] * workers

    def reader():
        try:
            with open(path, "rb") as f:
                batch = []
                for line in f:
                    batch.append(line)
                    if len(batch) == BATCH:
                        q.put(batch)
                        batch = []
            if batch:
                q.put(batch)
        finally:
            q.shutdown()

    def worker(i):
        parts = []
        while True:
            try:
                batch = q.get()
            except queue.ShutDown:
                break
            parts.append(count(map(int, batch)))
        results[i] = total(parts)

    r = threading.Thread(target=reader)
    r.start()
    run_threads(worker, workers)
    r.join()
    return total(results)


def task_2(folder, threads):
    files = sorted(Path(folder).glob("numbers_*.txt"))
    if not files:
        sys.exit(f"no numbers_*.txt files in {folder}")
    results = [None] * threads

    def work(i):
        parts = []
        for path in files[i::threads]:
            with open(path, "rb") as f:
                buf = f.read()
            parts.append(count_stream(io.BytesIO(buf), len(buf)))
        results[i] = total(parts)

    run_threads(work, threads)
    return total(results)


def main(argv):
    if len(argv) < 3 or argv[0] not in ("1a", "1b", "1c", "2"):
        sys.exit(USAGE)
    task, path = argv[0], argv[1]
    if task == "1b":
        version = int(argv[2])
        threads = int(argv[3]) if len(argv) > 3 else os.cpu_count()
        if version not in (1, 2, 3):
            sys.exit(USAGE)
        nums = load(path)
        name = f"1b-v{version}"
        run = lambda: task_1b(nums, version, threads)
    else:
        threads = int(argv[2])
        name = task
        run = lambda: {"1a": task_1a, "1c": task_1c, "2": task_2}[task](path, threads)
    if threads < 1:
        sys.exit(USAGE)

    start = time.perf_counter()
    neg, pos, zero = run()
    ms = (time.perf_counter() - start) * 1000
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"{name},{threads},{ms:.1f},{peak_kb},{neg},{pos},{zero},{neg + pos + zero}")


if __name__ == "__main__":
    main(sys.argv[1:])
