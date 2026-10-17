#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 2. Рекурсивные функции; динамический массив, стек и дек (Решение)."""
from __future__ import annotations

import argparse
import collections
import functools
import json
import math
import random
import statistics
import sys
import time
import traceback
from pathlib import Path

FRONT_SIZES = (1_000, 3_000, 10_000, 30_000, 100_000)
FRONT_OPS = 1_000
FIB_NS = (5, 10, 15, 20, 25, 30)
REPEATS = 5
CALLS = {"fib_naive": 0, "fib_memo": 0}

# ---------------------------------------------------------------------------
# 1. Рекурсивные функции
# ---------------------------------------------------------------------------

def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n >= 0")
    if n == 0:
        return 1
    return n * factorial(n - 1)

def fib_naive(n: int) -> int:
    CALLS["fib_naive"] += 1
    if n < 0:
        raise ValueError("n >= 0")
    if n < 2:
        return n
    return fib_naive(n - 1) + fib_naive(n - 2)

def fib_memo(n: int, memo: dict[int, int] | None = None) -> int:
    CALLS["fib_memo"] += 1
    if n < 0:
        raise ValueError("n >= 0")
    if memo is None:
        memo = {}
    if n < 2:
        return n
    if n in memo:
        return memo[n]
    result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    memo[n] = result
    return result

def hanoi(n: int, src: str = "A", dst: str = "C", aux: str = "B", moves: list[tuple[str, str]] | None = None) -> int:
    if n == 0:
        return 0
    count = hanoi(n - 1, src, aux, dst, moves)
    if moves is not None:
        moves.append((src, dst))
    count += 1
    count += hanoi(n - 1, aux, dst, src, moves)
    return count

# ---------------------------------------------------------------------------
# 2. Структуры данных
# ---------------------------------------------------------------------------

class DynamicArray:
    INITIAL_CAPACITY = 4

    def __init__(self) -> None:
        self._capacity = self.INITIAL_CAPACITY
        self._size = 0
        self._buffer: list = [None] * self._capacity
        self.copies = 0

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    def _grow(self) -> None:
        new_capacity = self._capacity * 2
        new_buffer = [None] * new_capacity
        for i in range(self._size):
            new_buffer[i] = self._buffer[i]
        self.copies += self._size
        self._buffer = new_buffer
        self._capacity = new_capacity

    def append(self, value) -> None:
        if self._size == self._capacity:
            self._grow()
        self._buffer[self._size] = value
        self._size += 1

    def pop(self):
        if self._size == 0:
            raise IndexError("pop from empty DynamicArray")
        value = self._buffer[self._size - 1]
        self._buffer[self._size - 1] = None
        self._size -= 1
        if self._capacity > self.INITIAL_CAPACITY and self._size <= self._capacity // 4:
            new_capacity = max(self._capacity // 2, self.INITIAL_CAPACITY)
            new_buffer = [None] * new_capacity
            for i in range(self._size):
                new_buffer[i] = self._buffer[i]
            self.copies += self._size
            self._buffer = new_buffer
            self._capacity = new_capacity
        return value

    def get(self, index: int):
        if not 0 <= index < self._size:
            raise IndexError(f"index {index} out of range")
        return self._buffer[index]

    def set(self, index: int, value) -> None:
        if not 0 <= index < self._size:
            raise IndexError(f"index {index} out of range")
        self._buffer[index] = value

class Stack:
    def __init__(self) -> None:
        self._data = DynamicArray()

    def __len__(self) -> int:
        return len(self._data)

    def push(self, value) -> None:
        self._data.append(value)

    def pop(self):
        return self._data.pop()

    def peek(self):
        if len(self._data) == 0:
            raise IndexError("peek from empty Stack")
        return self._data.get(len(self._data) - 1)

class _Node:
    __slots__ = ("value", "prev", "next")
    def __init__(self, value, prev=None, next=None) -> None:
        self.value = value
        self.prev = prev
        self.next = next

class Deque:
    def __init__(self) -> None:
        self._head: _Node | None = None
        self._tail: _Node | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def push_front(self, value) -> None:
        node = _Node(value, prev=None, next=self._head)
        if self._head is not None:
            self._head.prev = node
        else:
            self._tail = node
        self._head = node
        self._size += 1

    def push_back(self, value) -> None:
        node = _Node(value, prev=self._tail, next=None)
        if self._tail is not None:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1

    def pop_front(self):
        if self._head is None:
            raise IndexError("pop_front from empty Deque")
        node = self._head
        self._head = node.next
        if self._head is not None:
            self._head.prev = None
        else:
            self._tail = None
        self._size -= 1
        return node.value

    def pop_back(self):
        if self._tail is None:
            raise IndexError("pop_back from empty Deque")
        node = self._tail
        self._tail = node.prev
        if self._tail is not None:
            self._tail.next = None
        else:
            self._head = None
        self._size -= 1
        return node.value

# ---------------------------------------------------------------------------
# 3. Данные и проверки
# ---------------------------------------------------------------------------

Op = tuple[str, int | None]

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
    raise SystemExit("Не найден каталог data/generated.")

def check_variant(data_dir: Path, variant: int) -> None:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("variant") != variant:
        raise SystemExit(f"Данные для варианта {manifest.get('variant')}, а запущен {variant}.")
    print(f"Данные варианта {variant} (seed={manifest.get('seed')}) из {data_dir}")

def read_data_lines(data_dir: Path, name: str) -> list[str]:
    path = data_dir / name
    if not path.is_file():
        raise SystemExit(f"Не найден файл данных: {path}")
    return path.read_text(encoding="utf-8").splitlines()

def load_append_sizes(data_dir: Path) -> list[int]:
    return [int(line) for line in read_data_lines(data_dir, "ops_append_sizes.txt")]

def load_ops(data_dir: Path, kind: str) -> list[Op]:
    ops: list[Op] = []
    for line in read_data_lines(data_dir, f"ops_{kind}.txt"):
        name, *arg = line.split()
        ops.append((name, int(arg[0]) if arg else None))
    return ops

class SelfCheckError(Exception): pass

def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SelfCheckError(message)

def expect_index_error(call, what: str) -> None:
    try:
        call()
    except IndexError:
        return
    raise SelfCheckError(f"{what}: ожидался IndexError")

def stack_methods(st: Stack) -> dict:
    return {"push": st.push, "pop": st.pop, "peek": st.peek, "len": st.__len__}

def list_stack_methods(a: list) -> dict:
    return {"push": a.append, "pop": a.pop, "peek": lambda: a[-1], "len": a.__len__}

def deque_methods(dq: Deque) -> dict:
    return {"push_front": dq.push_front, "push_back": dq.push_back, "pop_front": dq.pop_front, "pop_back": dq.pop_back, "len": dq.__len__}

def std_deque_methods(d: collections.deque) -> dict:
    return {"push_front": d.appendleft, "push_back": d.append, "pop_front": d.popleft, "pop_back": d.pop, "len": d.__len__}

def apply_op(methods: dict, op: str, arg: int | None):
    try:
        return methods[op]() if arg is None else methods[op](arg)
    except IndexError:
        return "IndexError"

def compare_with_reference(ops: list[Op], own: dict, ref: dict, label: str) -> None:
    for i, (op, arg) in enumerate(ops, start=1):
        call = op if arg is None else f"{op} {arg}"
        got, expected = apply_op(own, op, arg), apply_op(ref, op, arg)
        expect(got == expected, f"{label}, оп. №{i} ({call}): получено {got!r}, эталон {expected!r}")
        expect(own["len"]() == ref["len"](), f"{label}, оп. №{i} ({call}): len = {own['len']()}, эталон {ref['len']()}")

def random_ops(rng: random.Random, pushes: tuple[str, ...], others: tuple[str, ...], count: int, max_size: int) -> list[Op]:
    ops: list[Op] = []
    size = 0
    for _ in range(count):
        op = rng.choice(pushes + others)
        if op in pushes and size >= max_size:
            op = rng.choice(others)
        if op in pushes:
            ops.append((op, rng.randrange(100)))
            size += 1
        else:
            ops.append((op, None))
            size = max(0, size - op.startswith("pop"))
    return ops

def expected_capacity(size: int) -> int:
    cap = DynamicArray.INITIAL_CAPACITY
    while cap < size: cap *= 2
    return cap

def expected_copies(size: int) -> int:
    copies, cap = 0, DynamicArray.INITIAL_CAPACITY
    while cap < size:
        copies += cap
        cap *= 2
    return copies

def check_recursion() -> None:
    for n in range(21):
        expect(factorial(n) == math.factorial(n), f"factorial({n}) неверен")
    fib = [0, 1]
    while len(fib) <= 90: fib.append(fib[-1] + fib[-2])
    for n in range(21):
        expect(fib_naive(n) == fib[n], f"fib_naive({n}) неверен")
    for n in (0, 1, 2, 10, 30, 90):
        CALLS["fib_memo"] = 0
        expect(fib_memo(n) == fib[n], f"fib_memo({n}) неверен")
        expect(CALLS["fib_memo"] <= 2 * n + 1, f"fib_memo({n}) вызовов больше 2n+1")
    
    # Свои инварианты
    CALLS["fib_naive"] = 0
    fib_naive(10)
    expect(CALLS["fib_naive"] == 2 * fib[11] - 1, "fib_naive вызовы != 2*F(n+1)-1")
    CALLS["fib_memo"] = 0
    fib_memo(10)
    expect(CALLS["fib_memo"] == 2 * 10 - 1, "fib_memo вызовы != 2n-1")

    for n, (src, dst, aux) in ((0, "ACB"), (1, "ACB"), (2, "ACB"), (3, "XZY"), (6, "ACB"), (7, "PQR")):
        moves: list[tuple[str, str]] = []
        count = hanoi(n, src, dst, aux, moves)
        expect(count == 2 ** n - 1, f"hanoi({n}) ходов {count}, ожидалось {2**n-1}")
        towers = {src: list(range(n, 0, -1)), dst: [], aux: []}
        for k, (frm, to) in enumerate(moves, start=1):
            disk = towers[frm].pop()
            top = towers[to][-1] if towers[to] else None
            expect(top is None or top > disk, f"hanoi({n}) ход {k} неверен")
            towers[to].append(disk)
        expect(towers[dst] == list(range(n, 0, -1)), f"hanoi({n}) диски не на {dst}")

def check_dynamic_array() -> None:
    arr = DynamicArray()
    ref = []
    for i in range(100):
        arr.append(i * i)
        ref.append(i * i)
        expect(len(arr) == len(ref), "len неверен")
        expect(arr.capacity == expected_capacity(len(ref)), "capacity неверен")
        expect(arr.copies == expected_copies(len(ref)), "copies неверны")
    
    # Свой инвариант
    arr2 = DynamicArray()
    for i in range(8): arr2.append(i)
    expect((8 + arr2.copies) / 8 <= 2.0, "амортизированная стоимость append > 2")

def check_stack() -> None:
    st = Stack()
    for i in range(20): st.push(i)
    for i in reversed(range(20)):
        expect(st.pop() == i, "Stack LIFO неверен")

def check_deque() -> None:
    dq = Deque()
    for i in range(5): dq.push_front(i)
    for i in range(5, 10): dq.push_back(i)
    expect([dq.pop_front() for _ in range(5)] == [4, 3, 2, 1, 0], "Deque pop_front неверен")
    expect([dq.pop_back() for _ in range(5)] == [9, 8, 7, 6, 5], "Deque pop_back неверен")

def check_variant_ops(stack_ops: list[Op], deque_ops: list[Op]) -> None:
    compare_with_reference(stack_ops, stack_methods(Stack()), list_stack_methods([]), "ops_stack.txt")
    compare_with_reference(deque_ops, deque_methods(Deque()), std_deque_methods(collections.deque()), "ops_deque.txt")

def self_check(stack_ops: list[Op], deque_ops: list[Op]) -> None:
    checks = (
        ("рекурсия", check_recursion), ("DynamicArray", check_dynamic_array),
        ("Stack", check_stack), ("Deque", check_deque),
        ("операции варианта", lambda: check_variant_ops(stack_ops, deque_ops)),
    )
    failed = 0
    print("self_check:")
    for name, check in checks:
        try:
            check()
        except Exception as e:
            print(f"  {name}: ОШИБКА — {e}")
            failed += 1
        else:
            print(f"  {name}: OK")
    if failed:
        raise SystemExit(f"self_check: не пройдено — {failed}")
    print("self_check: OK")

# ---------------------------------------------------------------------------
# 4. Замеры
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
    return (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs))

def appends(add, n: int) -> None:
    for i in range(n): add(i)

def steady_ops(add, remove, k: int = FRONT_OPS) -> None:
    for i in range(k):
        add(i)
        remove()

def replay(ops: list[Op], methods: dict) -> None:
    for op, arg in ops:
        try:
            if arg is None: methods[op]()
            else: methods[op](arg)
        except IndexError: pass

def filled_structure(kind: str, n: int):
    if kind == "list": return list(range(n))
    if kind == "deque": return collections.deque(range(n))
    dq = Deque()
    appends(dq.push_back, n)
    return dq

FRONT_CASES = {
    "insert": (
        ("list.insert(0, x) + pop()", "list", lambda a: (functools.partial(a.insert, 0), a.pop)),
        ("deque.appendleft + pop", "deque", lambda d: (d.appendleft, d.pop)),
        ("Deque.push_front + pop_back", "Deque", lambda d: (d.push_front, d.pop_back)),
    ),
    "remove": (
        ("list.append + pop(0)", "list", lambda a: (a.append, functools.partial(a.pop, 0))),
        ("deque.append + popleft", "deque", lambda d: (d.append, d.popleft)),
        ("Deque.push_back + pop_front", "Deque", lambda d: (d.push_back, d.pop_front)),
    ),
}
FRONT_TITLES = {"insert": "Вставка в начало", "remove": "Удаление из начала"}

def run_benchmarks(append_sizes: list[int], stack_ops: list[Op], deque_ops: list[Op]) -> dict:
    results: dict = {}
    print("\nЧисло вызовов:")
    for n in FIB_NS:
        CALLS["fib_naive"] = CALLS["fib_memo"] = 0
        value = fib_naive(n)
        fib_memo(n)
        print(f"  n={n:>2}  F(n)={value:>6}  naive: {CALLS['fib_naive']:>7}  memo: {CALLS['fib_memo']:>2}")

    print("\nСерии append:")
    results["append"] = []
    for n in append_sizes:
        t_own = bench(lambda: appends(DynamicArray().append, n)) / n
        t_list = bench(lambda: appends([].append, n)) / n
        arr = DynamicArray()
        appends(arr.append, n)
        cost = (n + arr.copies) / n
        results["append"].append((n, t_own, t_list, cost))
        print(f"  n={n:>7}  t/n: DA {t_own:.2e} c, list {t_list:.2e} c  copies={arr.copies:>7}  cost={cost:.3f}")

    for key, title in FRONT_TITLES.items():
        print(f"\n{title}:")
        results[key] = {}
        for label, kind, methods in FRONT_CASES[key]:
            points = []
            for n in FRONT_SIZES:
                add, remove = methods(filled_structure(kind, n))
                points.append((n, bench(lambda: steady_ops(add, remove)) / FRONT_OPS))
            results[key][label] = points
            row = "  ".join(f"{t:.2e}" for _, t in points)
            print(f"  {label:28s} {row}   наклон {log_log_slope(points):.2f}")

    print("\nОперации варианта целиком:")
    cases = (
        ("ops_stack.txt", stack_ops, "Stack", lambda: stack_methods(Stack()), "list", lambda: list_stack_methods([])),
        ("ops_deque.txt", deque_ops, "Deque", lambda: deque_methods(Deque()), "deque", lambda: std_deque_methods(collections.deque())),
    )
    for name, ops, own_label, make_own, ref_label, make_ref in cases:
        t_own = bench(lambda: replay(ops, make_own())) / len(ops)
        t_ref = bench(lambda: replay(ops, make_ref())) / len(ops)
        print(f"  {name}: {own_label} {t_own:.2e} c, {ref_label} {t_ref:.2e} c — в {t_own / t_ref:.1f} раз медленнее")
    return results

def plot_results(results: dict, out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError: return

    rows = results["append"]
    ns = [row[0] for row in rows]
    fig, (ax_t, ax_c) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax_t.plot(ns, [row[1] for row in rows], marker="o", label="DynamicArray.append")
    ax_t.plot(ns, [row[2] for row in rows], marker="s", label="list.append")
    ax_t.set_xscale("log")
    ax_t.set_xlabel("n"); ax_t.set_ylabel("t/n, с"); ax_t.set_title("Средняя стоимость append")
    ax_t.grid(True, which="both", linewidth=0.3); ax_t.legend()

    ax_c.plot(ns, [row[3] for row in rows], marker="o", label="(n + copies)/n")
    ax_c.axhline(3, color="grey", linestyle="--", label="оценка")
    ax_c.set_xscale("log"); ax_c.set_ylim(0, 3.5)
    ax_c.set_xlabel("n"); ax_c.set_ylabel("действий на операцию"); ax_c.set_title("Стоимость")
    ax_c.grid(True, which="both", linewidth=0.3); ax_c.legend(loc="lower right")
    fig.tight_layout(); fig.savefig(out_dir / "lab02_append.png", dpi=150)

    fig2, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, (key, title) in zip(axes, FRONT_TITLES.items()):
        for label, points in results[key].items():
            ax.plot([n for n, _ in points], [t for _, t in points], marker="o", label=f"{label} (наклон ≈ {log_log_slope(points):.2f})")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("n"); ax.set_title(title); ax.grid(True, which="both", linewidth=0.3); ax.legend(fontsize=8)
    axes[0].set_ylabel("время, с")
    fig2.tight_layout(); fig2.savefig(out_dir / "lab02_front.png", dpi=150)
    print(f"\nГрафики сохранены в {out_dir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", type=int, required=True)
    ap.add_argument("--data", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path.cwd())
    args = ap.parse_args()

    data_dir = find_data_dir(args.data)
    check_variant(data_dir, args.variant)
    append_sizes = load_append_sizes(data_dir)
    stack_ops = load_ops(data_dir, "stack")
    deque_ops = load_ops(data_dir, "deque")
    self_check(stack_ops, deque_ops)
    results = run_benchmarks(append_sizes, stack_ops, deque_ops)
    plot_results(results, args.out)

if __name__ == "__main__":
    main()