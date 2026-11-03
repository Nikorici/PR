import random
import tempfile
from pathlib import Path

import lab


def check(nums, trailing_newline=True):
    expected = lab.count(nums)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "numbers.txt"
        text = "\n".join(map(str, nums)) + ("\n" if trailing_newline else "")
        path.write_text(text)
        for i in range(8):
            (Path(d) / f"numbers_{i + 1}.txt").write_text("\n".join(map(str, nums[i::8])) + "\n")
        loaded = lab.load(path)
        assert list(loaded) == nums
        for threads in (1, 2, 3, 4, 7, 16, 64):
            assert lab.task_1a(str(path), threads) == expected, ("1a", threads)
            assert lab.task_1b(loaded, 2, threads) == expected, ("1b-v2", threads)
            assert lab.task_1b(loaded, 3, threads) == expected, ("1b-v3", threads)
            assert lab.task_1c(str(path), threads) == expected, ("1c", threads)
            assert lab.task_2(d, threads) == expected, ("2", threads)


if __name__ == "__main__":
    rng = random.Random(1)
    lab.BLOCK = 7
    lab.BATCH = 3
    check([rng.randint(-1_000_000, 1_000_000) for _ in range(500)] + [0, 0, -5, 5])
    check([0, -1, 1, 1000000, -1000000], trailing_newline=False)
    check([42])
    print("ok")
