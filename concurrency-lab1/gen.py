import random
import sys
from pathlib import Path

N = 50_000_000
PARTS = 8
BLOCK = 250_000
SEED = 20261022


def main(out):
    out = Path(out)
    (out / "parts").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    neg = pos = zero = 0
    with open(out / "numbers.txt", "w") as whole:
        for p in range(1, PARTS + 1):
            with open(out / "parts" / f"numbers_{p}.txt", "w") as part:
                for _ in range(N // PARTS // BLOCK):
                    nums = [rng.randint(-1_000_000, 1_000_000) for _ in range(BLOCK)]
                    neg += sum(1 for n in nums if n < 0)
                    pos += sum(1 for n in nums if n > 0)
                    zero += nums.count(0)
                    text = "\n".join(map(str, nums)) + "\n"
                    whole.write(text)
                    part.write(text)
    assert neg + pos + zero == N
    (out / "expected.txt").write_text(f"{neg},{pos},{zero},{N}\n")
    print(f"negative={neg} positive={pos} zero={zero} total={N}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
