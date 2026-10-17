#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 1. Анализ временной сложности элементарных алгоритмов (Решение)."""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from pathlib import Path

SIZES = (1_000, 3_000, 10_000, 30_000, 100_000)
QUADRATIC_SIZES = (500, 1_000, 3_000, 10_000, 30_000)
EXPONENTS = (10**3, 10**4, 10**5, 10**6, 10**7)
POW_MOD = 1_000_000_007
POW_BASE = 3
REPEATS = 5
POW_CALLS = 20_000

# ---------------------------------------------------------------------------
# 1. Алгоритмы
# ---------------------------------------------------------------------------

def array_sum(a: list[int]) -> int:
    total = 0
    for value in a:
        total += value
    return total

def array_max(a: list[int]) -> int:
    if not a:
        raise ValueError("array_max: пустой массив")
    current_max = a[0]
    for value in a[1:]:
        if value > current_max:
            current_max = value
    return current_max

def count_equal_pairs(a: list[int]) -> int:
    count = 0
    n = len(a)
    for i in range(n):
        ai = a[i]
        for j in range(i + 1, n):
            if ai == a[j]:
                count += 1
    return count

def binary_pow(x: int, n: int, mod: int | None = None) -> int:
    result = 1 if mod is None else 1 % mod
    base = x if mod is None else x % mod
    while n > 0:
        if n & 1:
            result *= base
            if mod is not None:
                result %= mod
        base *= base
        if mod is not None:
            base %= mod
        n >>= 1
    return result

# ---------------------------------------------------------------------------
# 2. Данные и проверки
# ---------------------------------------------------------------------------

def find_data_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        if not explicit.is_dir():
            raise SystemExit(f"Каталог не найден: {explicit}")
        return explicit
    candidates = []
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for parent in (base, *base.parents):
            candidates.append(parent / "data" / "generated")
    for path in candidates:
        if path.is_dir():
            return path
    raise SystemExit("Не найден каталог data/generated с данными варианта.")

def check_variant(data_dir: Path, variant: int) -> None:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("variant") != variant:
        raise SystemExit(f"Данные сгенерированы для варианта {manifest.get('variant')}, а запущен {variant}.")
    print(f"Данные варианта {variant} (seed={manifest.get('seed')}) из {data_dir}")

def load_array(data_dir: Path, kind: str, n: int, limit: int | None = None) -> list[int]:
    path = data_dir / f"arrays_{kind}_{n}.txt"
    if not path.is_file():
        raise SystemExit(f"Не найден файл данных: {path}")
    values = [int(line) for line in path.read_text(encoding="utf-8").split()]
    return values[:limit] if limit is not None else values

def self_check() -> None:
    assert array_sum([]) == 0
    assert array_sum([7]) == 7
    assert array_max([3, 1, 2]) == 3
    assert count_equal_pairs([]) == 0
    assert count_equal_pairs([5, 5, 5]) == 3
    assert count_equal_pairs([1, 2, 3, 4, 5]) == 0
    assert count_equal_pairs([5] * 7) == 21
    assert binary_pow(2, 0) == 1
    assert binary_pow(2, 10) == 1024
    assert binary_pow(2, 10, mod=1000) == 24

    rng = random.Random(0)
    for _ in range(200):
        a = [rng.randint(-50, 50) for _ in range(rng.randint(1, 60))]
        assert array_sum(a) == sum(a)
        assert array_max(a) == max(a)
    for _ in range(200):
        x, n = rng.randint(2, 50), rng.randint(0, 64)
        assert binary_pow(x, n, mod=POW_MOD) == pow(x, n, POW_MOD)
    
    # Свои инварианты
    for _ in range(200):
        a = [rng.randint(-3, 3) for _ in range(rng.randint(0, 40))]
        freq = {}
        for val in a:
            freq[val] = freq.get(val, 0) + 1
        expected = sum(c * (c - 1) // 2 for c in freq.values())
        assert count_equal_pairs(a) == expected

    print("self_check: OK")

# ---------------------------------------------------------------------------
# 3. Замеры и графики
# ---------------------------------------------------------------------------

def bench(call) -> float:
    call()
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        call()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)

def log_log_slope(points: list[tuple[int, float]]) -> float:
    xs = [math.log10(n) for n, _ in points]
    ys = [math.log10(t) for _, t in points]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            / sum((x - mx) ** 2 for x in xs))

def run_benchmarks(data_dir: Path) -> dict[str, list[tuple[int, float]]]:
    results = {}
    random_arrays = {n: load_array(data_dir, "random", n) for n in SIZES}
    for name, fn in (("array_sum", array_sum), ("array_max", array_max)):
        points = []
        print(f"\n{name}:")
        for n in SIZES:
            a = random_arrays[n]
            t = bench(lambda: fn(a))
            points.append((n, t))
            print(f"  n={n:>7}  t={t:.6f} c")
        results[name] = points

    print("\ncount_equal_pairs:")
    points = []
    for n in QUADRATIC_SIZES:
        file_n = n if n in SIZES else min(s for s in SIZES if s >= n)
        a = load_array(data_dir, "dups", file_n, limit=n)
        t = bench(lambda: count_equal_pairs(a))
        points.append((n, t))
        print(f"  n={n:>7}  t={t:.6f} c")
    results["count_equal_pairs"] = points

    print(f"\nbinary_pow (по {POW_CALLS} вызовов на точку, mod={POW_MOD}):")
    points = []
    for e in EXPONENTS:
        def batch(e=e):
            for _ in range(POW_CALLS):
                binary_pow(POW_BASE, e, mod=POW_MOD)
        t = bench(batch) / POW_CALLS
        points.append((e, t))
        print(f"  n={e:>9}  log2(n)={math.log2(e):5.1f}  t={t:.9f} c")
    results["binary_pow"] = points
    return results

def plot_results(results: dict, out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib не установлен.")
        return

    power_law = ("array_sum", "array_max", "count_equal_pairs")
    fig, ax = plt.subplots(figsize=(7, 5))
    for name in power_law:
        points = results[name]
        ax.plot([n for n, _ in points], [t for _, t in points], marker="o", label=f"{name} (наклон ≈ {log_log_slope(points):.2f})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("размер входа n")
    ax.set_ylabel("время, с")
    ax.set_title("Время работы в осях log-log")
    ax.grid(True, which="both", linewidth=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "lab01_loglog.png", dpi=150)

    points = results["binary_pow"]
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.plot([math.log2(n) for n, _ in points], [t for _, t in points], marker="o")
    ax2.set_xlabel("log₂ n")
    ax2.set_ylabel("время одного вызова, с")
    ax2.set_title("Бинарное возведение: t(log₂ n)")
    ax2.grid(True, linewidth=0.3)
    fig2.tight_layout()
    fig2.savefig(out_dir / "lab01_binary_pow.png", dpi=150)
    print(f"\nГрафики сохранены в {out_dir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", type=int, required=True)
    ap.add_argument("--data", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path.cwd())
    args = ap.parse_args()

    data_dir = find_data_dir(args.data)
    check_variant(data_dir, args.variant)
    self_check()
    results = run_benchmarks(data_dir)
    for name in ("array_sum", "array_max", "count_equal_pairs"):
        print(f"  {name:20s} {log_log_slope(results[name]):.3f}")
    plot_results(results, args.out)

if __name__ == "__main__":
    main()