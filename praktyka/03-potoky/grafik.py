import os
import matplotlib.pyplot as plt

# Автоматично створюємо папку 2-potoky, якщо її ще немає
os.makedirs("2-potoky", exist_ok=True)

potoky = [1, 2, 4, 8, 16]
obchyslennya = [1.00, 0.99, 0.99, 0.98, 0.97]
ochikuvannya = [1.0, 2.0, 4.0, 8.0, 15.9]

plt.figure(figsize=(8, 5))
plt.plot(potoky, obchyslennya, "o-", label="Обчислення (CPU-bound)")
plt.plot(potoky, ochikuvannya, "s-", label="Очікування (IO-bound)")
plt.xlabel("Кількість потоків")
plt.ylabel("Прискорення, разів")
plt.title("Порівняння ефективності потоків в CPython")
plt.legend()
plt.grid(True)

plt.savefig("2-potoky/grafik.png", dpi=120)
print("Графік успішно збережено у 2-potoky/grafik.png")