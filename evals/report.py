#!/usr/bin/env python3
import json
import math
import sys

Z = 1.96


def wilson_ci(p: float, n: int) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    denom = 1 + Z * Z / n
    center = p + Z * Z / (2 * n)
    margin = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    lower = (center - margin) / denom
    upper = (center + margin) / denom
    return (max(0.0, lower), min(1.0, upper))


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python evals/report.py <metrics.json>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    global_n = data.get("n", 0)
    metrics = {k: v for k, v in data.items() if isinstance(v, float) and 0 <= v <= 1 and k != "n"}

    print(f"{'metrica':<25} {'valor':>8} {'n':>6} {'IC 95% (Wilson)':>22}")
    print("-" * 65)

    for name, value in metrics.items():
        n = data.get(name + "_n", global_n) if isinstance(data.get(name + "_n"), int) else global_n
        if isinstance(data.get(name), dict):
            n = data[name].get("n", global_n)
        lo, hi = wilson_ci(float(value), n)
        print(f"{name:<25} {float(value):>8.3f} {n:>6} [{lo:.3f}, {hi:.3f}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())