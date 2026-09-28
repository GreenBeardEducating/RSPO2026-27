import os
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

# Параметри задачі Мандельброта з тижня 2
W, H = 3449, 2586
MAX_ITER = 10

def ryadok(y):
    """Обчислення одного рядка зображення (верхній рівень)."""
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

def protsesamy(n):
    with ProcessPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H), chunksize=8))

def porozhniy_pul(n):
    with ProcessPoolExecutor(max_workers=n) as ex:
        list(ex.map(abs, range(n)))  # примусовий запуск процесів

def zamir(fn, prohoniv=3, *args):
    chasy = []
    res = None
    for _ in range(prohoniv):
        t0 = perf_counter()
        res = fn(*args)
        chasy.append(perf_counter() - t0)
    return min(chasy), chasy, res

if __name__ == "__main__":
    t_base, chasy, base = zamir(poslidovno, 3)
    print("послідовно", [round(c, 2) for c in chasy], "мінімум", round(t_base, 2))

    for n in (1, 2, 4, 8, os.cpu_count()):
        t, chasy, r = zamir(protsesamy, 3, n)
        assert r == base, "результат розійшовся з послідовним"
        s = t_base / t
        eff = (s / n) * 100
        print(f"процесів {n}: {[round(c, 2) for c in chasy]} | мінімум {round(t, 2)}с | прискорення ×{round(s, 2)} | ефективність {round(eff)}%")

    print("\n--- Вимірювання накладних витрат пулу процесів ---")
    for n in (2, os.cpu_count()):
        t_pool, _, _ = zamir(porozhniy_pul, 3, n)
        print(f"порожній пул, {n} процесів: {round(t_pool, 3)} с")