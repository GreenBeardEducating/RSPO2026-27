"""Практична 06: векторизований NumPy-варіант Мандельброта."""

import json
import platform
from time import perf_counter
from pathlib import Path

import numpy as np

W = 692
H = 519
MAX_ITER = 1000
XMIN, XMAX = -2.0, 0.6
YMIN, YMAX = -1.2, 1.2
ROOT = Path(__file__).resolve().parent
NUMBA_RESULTS = ROOT / "numba_results.json"
NUMPY_RESULTS = ROOT / "numpy_results.json"
REPORT_PATH = ROOT.parent / "zamiry.md"


def poslidovno():
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


def mandelbrot_numpy(endpoint=False):
    # endpoint=False відповідає формулі x/W, y/H у послідовній версії.
    xs = np.linspace(XMIN, XMAX, W, endpoint=endpoint)
    ys = np.linspace(YMIN, YMAX, H, endpoint=endpoint)
    cx, cy = np.meshgrid(xs, ys)
    zx = np.zeros((H, W), dtype=np.float64)
    zy = np.zeros((H, W), dtype=np.float64)
    out = np.full((H, W), MAX_ITER, dtype=np.int32)
    active = np.ones((H, W), dtype=bool)

    for n in range(MAX_ITER):
        zx_n = zx * zx - zy * zy + cx
        zy_n = 2.0 * zx * zy + cy
        zx = np.where(active, zx_n, zx)
        zy = np.where(active, zy_n, zy)
        escaped = active & (zx * zx + zy * zy > 4.0)
        out[escaped] = n + 1
        active &= ~escaped
        if not active.any():
            break
    return out


def main():
    print("=== Практична 06: NumPy ===")
    print(f"Python {platform.python_version()} | NumPy {np.__version__}")
    print(f"Зображення: {W} × {H}; MAX_ITER={MAX_ITER}")
    print("Обчислюю еталон чистим Python — це може зайняти кілька секунд...")
    t0 = perf_counter()
    base = poslidovno()
    python_time = perf_counter() - t0
    print(f"Еталон: {python_time:.4f} с")

    t0 = perf_counter()
    result = mandelbrot_numpy(endpoint=False)
    numpy_time = perf_counter() - t0
    mismatch = int(np.count_nonzero(result != base))
    print(f"NumPy endpoint=False: {numpy_time:.4f} с; розбіжних точок: {mismatch} із {base.size}")

    t0 = perf_counter()
    wrong_endpoint = mandelbrot_numpy(endpoint=True)
    endpoint_time = perf_counter() - t0
    mismatch_endpoint = int(np.count_nonzero(wrong_endpoint != base))
    print(f"NumPy endpoint=True: {endpoint_time:.4f} с; розбіжних точок: {mismatch_endpoint} із {base.size}")

    data = {
        "python_time": python_time,
        "numpy_time": numpy_time,
        "numpy_speedup": python_time / numpy_time if numpy_time else None,
        "mismatches_endpoint_false": mismatch,
        "mismatches_endpoint_true": mismatch_endpoint,
        "pixels": int(base.size),
        "width": W, "height": H, "max_iter": MAX_ITER,
    }
    NUMPY_RESULTS.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Додаємо NumPy-результат до звіту, не видаляючи виміри Numba.
    if REPORT_PATH.exists():
        report = REPORT_PATH.read_text(encoding="utf-8")
        row = f"| NumPy `endpoint=False` | {numpy_time:.6f} | ×{python_time/numpy_time:.2f} | {mismatch} розбіжних точок |"
        if "| NumPy `endpoint=False` |" in report:
            lines = report.splitlines()
            lines = [row if line.startswith("| NumPy `endpoint=False` |") else line for line in lines]
            report = "\n".join(lines) + "\n"
        else:
            marker = "## Час компіляції (перший виклик, окремо)"
            if marker in report:
                report = report.replace(marker, "## NumPy\n\n" + row + "\n\n" + marker)
            else:
                report += "\n## NumPy\n\n" + row + "\n"
        report += f"\nNumPy з `endpoint=True` (контрольний варіант): {mismatch_endpoint} розбіжних точок із {base.size}.\n"
        REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Збережено: {NUMPY_RESULTS}")
    print(f"Звіт оновлено: {REPORT_PATH}")
    input("\nНатисніть Enter, щоб закрити програму...")


if __name__ == "__main__":
    main()
