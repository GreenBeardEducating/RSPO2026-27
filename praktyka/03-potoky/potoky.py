import os
import time
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter, process_time

# --- Параметри задачі Мандельброта з тижня 2 ---
W, H = 3449, 2586
MAX_ITER = 10

def ryadok(y):
    """Обчислення одного рядка зображення (одиниця роботи)."""
    row = []
    cy = -1.2 + (y / H) * 2.4
    for x in range(W):
        cx = -2.0 + (x / W) * 3.0
        zx, zy = 0.0, 0.0
        n = 0
        while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
            zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
            n += 1
        row.append(n)
    return row

def poslidovno():
    return [ryadok(y) for y in range(H)]

def potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H)))

def zamir(fn, prohoniv=3, *args):
    chasy = []
    res = None
    for _ in range(prohoniv):
        t0 = perf_counter()
        res = fn(*args)
        chasy.append(perf_counter() - t0)
    return min(chasy), chasy, res

def navantazhennya(fn, *a):
    c0, t0 = process_time(), perf_counter()
    fn(*a)
    return (process_time() - c0) / (perf_counter() - t0)

# --- Задача на очікування ---
def zapyt(nomer):
    time.sleep(0.5)  # симуляція очікування мережі
    return nomer

def ochikuvannya_poslidovno():
    return [zapyt(i) for i in range(32)]

def ochikuvannya_potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(zapyt, range(32)))

if __name__ == "__main__":
    print("=== 1. ОБЧИСЛЕННЯ (CPU-bound) ===")
    t_base, chasy, base = zamir(poslidovno, 3)
    print("послідовно", [round(c, 2) for c in chasy], "мінімум", round(t_base, 2))

    for n in (2, 4, 8, os.cpu_count()):
        t, chasy, r = zamir(potokamy, 3, n)
        assert r == base, "результат розійшовся з послідовним"
        print("потоків", n, [round(c, 2) for c in chasy],
              "мінімум", round(t, 2), "прискорення", round(t_base / t, 2))

    print("\nПроцесорний / настінний час, 8 потоків:", round(navantazhennya(potokamy, 8), 2))

    print("\n=== 2. ОЧІКУВАННЯ (IO-bound) ===")
    t0 = perf_counter()
    base_o = ochikuvannya_poslidovno()
    t_base_o = perf_counter() - t0
    print("очікування послідовно", round(t_base_o, 2))

    for n in (2, 4, 8, 16, 32):
        t, chasy, r = zamir(ochikuvannya_potokamy, 3, n)
        assert r == base_o, "результат очікування розійшовся"
        print("очікування, потоків", n, [round(c, 2) for c in chasy],
              "прискорення", round(t_base_o / t, 1))