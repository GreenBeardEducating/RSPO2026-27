"""Практична 06: чистий Python, Numba @njit та @njit(parallel=True)"""

import os
import json
import platform
import sys
from time import perf_counter
from pathlib import Path

import numpy as np
from numba import njit, prange, get_num_threads

# Параметри відповідають попереднім замірам Мандельброта.
# Якщо у 1-poslidovno/mandelbrot.py інші константи, змінити їх тут і в numpy_versiya.py.
W = 692
H = 519
MAX_ITER = 100
XMIN, XMAX = -2.0, 0.6
YMIN, YMAX = -1.2, 1.2

ROOT = Path(__file__).resolve().parent
RESULTS_PATH = ROOT / "numba_results.json"
REPORT_PATH = ROOT.parent / "zamiry.md"
ARGS = (W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX)


def poslidovno():
    """Еталонний алгоритм на чистому Python; повертає int32-масив H×W."""
    out = np.empty((H, W), dtype=np.int32)
    for y in range(H):
        cy = YMIN + (YMAX - YMIN) * y / H
        for x in range(W):
            cx = XMIN + (XMAX - XMIN) * x / W
            zx = 0.0
            zy = 0.0
            n = 0
            while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                n += 1
            out[y, x] = n
    return out


@njit
def mandelbrot_numba(W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX):
    out = np.empty((H, W), dtype=np.int32)
    for y in range(H):
        cy = YMIN + (YMAX - YMIN) * y / H
        for x in range(W):
            cx = XMIN + (XMAX - XMIN) * x / W
            zx = 0.0
            zy = 0.0
            n = 0
            while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                n += 1
            out[y, x] = n
    return out


@njit(parallel=True)
def mandelbrot_prange(W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX):
    out = np.empty((H, W), dtype=np.int32)
    for y in prange(H):
        cy = YMIN + (YMAX - YMIN) * y / H
        for x in range(W):
            cx = XMIN + (XMAX - XMIN) * x / W
            zx = 0.0
            zy = 0.0
            n = 0
            while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                n += 1
            out[y, x] = n
    return out


def measure(fn, repeats=3):
    times = []
    result = None
    for _ in range(repeats):
        t0 = perf_counter()
        result = fn(*ARGS)
        times.append(perf_counter() - t0)
    return min(times), times, result


def machine_info():
    return {
        "processor": platform.processor() or platform.uname().processor or "невідомо",
        "logical_cores": os.cpu_count() or 1,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "numba": __import__("numba").__version__,
        "numba_threads": get_num_threads(),
    }


def write_report(data):
    m = data["machine"]
    rows = [
        "# Практична 06 — NumPy та Numba", "",
        f"- Процесор: {m['processor']}",
        f"- Логічних процесорів: {m['logical_cores']}",
        f"- Потоків Numba: {m['numba_threads']}",
        f"- Python: {m['python']} · NumPy: {m['numpy']} · Numba: {m['numba']}",
        f"- Мандельброт: {W} × {H}, MAX_ITER={MAX_ITER}", "",
        "| Реалізація | Час, с | Прискорення | Збіг з еталоном |",
        "|---|---:|---:|---|",
        f"| Чистий Python | {data['python_time']:.6f} | ×1.00 | еталон |",
        f"| Numba `@njit` | {data['njit_time']:.6f} | ×{data['python_time']/data['njit_time']:.2f} | так |",
        f"| Numba `prange` | {data['prange_time']:.6f} | ×{data['python_time']/data['prange_time']:.2f} | так |",
        "", "## Час компіляції (перший виклик, окремо)", "",
        f"- `@njit`: {data['njit_compile_time']:.6f} с",
        f"- `prange`: {data['prange_compile_time']:.6f} с", "",
        "## Окремі прогони", "",
        f"- Чистий Python: {data['python_runs']}",
        f"- `@njit`: {data['njit_runs']}",
        f"- `prange`: {data['prange_runs']}", "",
        "Numba-версії перевірені через `np.array_equal` проти еталона.",
        "Час прискорення розрахований відносно найкращого із трьох замірів Numba та одного еталонного прогону.",
    ]
    REPORT_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main():
    print("=== Практична 06: Numba ===")
    print(f"Python {platform.python_version()} | NumPy {np.__version__} | Numba {__import__('numba').__version__}")
    print(f"Зображення: {W} × {H}; MAX_ITER={MAX_ITER}")
    print("Обчислюю еталон чистим Python — це може зайняти кілька секунд...")
    t0 = perf_counter()
    base = poslidovno()
    python_time = perf_counter() - t0
    print(f"Еталон: {python_time:.4f} с")

    t0 = perf_counter()
    njit_first = mandelbrot_numba(*ARGS)
    njit_compile_time = perf_counter() - t0
    assert np.array_equal(njit_first, base), "@njit не збігається з еталоном"
    print(f"Компіляція + перший виклик @njit: {njit_compile_time:.4f} с; assert OK")

    njit_time, njit_runs, njit_result = measure(mandelbrot_numba)
    assert np.array_equal(njit_result, base), "@njit не збігається з еталоном"
    print(f"@njit: прогони {[round(x, 6) for x in njit_runs]}, мінімум {njit_time:.6f} с, прискорення ×{python_time/njit_time:.2f}; assert OK")

    t0 = perf_counter()
    parallel_first = mandelbrot_prange(*ARGS)
    prange_compile_time = perf_counter() - t0
    assert np.array_equal(parallel_first, base), "prange не збігається з еталоном"
    print(f"Компіляція + перший виклик prange: {prange_compile_time:.4f} с; assert OK")

    prange_time, prange_runs, prange_result = measure(mandelbrot_prange)
    assert np.array_equal(prange_result, base), "prange не збігається з еталоном"
    print(f"prange: прогони {[round(x, 6) for x in prange_runs]}, мінімум {prange_time:.6f} с, прискорення ×{python_time/prange_time:.2f}; assert OK")

    data = {
        "machine": machine_info(), "width": W, "height": H, "max_iter": MAX_ITER,
        "python_time": python_time, "njit_compile_time": njit_compile_time,
        "njit_time": njit_time, "njit_runs": njit_runs,
        "prange_compile_time": prange_compile_time, "prange_time": prange_time,
        "prange_runs": prange_runs, "python_runs": [python_time],
    }
    RESULTS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    write_report(data)
    print(f"\nЗбережено: {RESULTS_PATH}")
    print(f"Створено/оновлено: {REPORT_PATH}")
    input("\nНатисніть Enter, щоб закрити програму...")


if __name__ == "__main__":
    main()
