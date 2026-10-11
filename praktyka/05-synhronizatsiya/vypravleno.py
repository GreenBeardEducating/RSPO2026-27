import multiprocessing as mp
import os
import platform
import random
import sys
import time


ZAPAS_POCHATKOVYI = 30_000
PROTSESIV = 4
ZAMOVLEN_NA_PROTSES = 20_000
MAX_U_ZAMOVLENNI = 3


def obrobyty_zamovlennya(zalyshok, vidvantazheno, vidmov, nasinnya, zamok):
    """Один робітник складу. Обробляє свою пачку замовлень."""

    rnd = random.Random(nasinnya)

    moi = 0

    for _ in range(ZAMOVLEN_NA_PROTSES):
        kilkist = rnd.randint(1, MAX_U_ZAMOVLENNI)

        with zamok:

            # перевіряємо, чи вистачає товару
            if zalyshok.value >= kilkist:

                # списуємо
                zalyshok.value = zalyshok.value - kilkist

                # рахуємо, скільки відвантажили
                vidvantazheno.value = vidvantazheno.value + kilkist

                moi += kilkist

            else:
                vidmov.value = vidmov.value + 1

    print("процес", nasinnya, "відвантажив", moi)


def pasport():
    print("=" * 68)
    print("УМОВИ ЗАПУСКУ")
    print("=" * 68)
    print("  Python        :", sys.version.split()[0])
    print("  процесор      :", platform.processor())
    print("  логічних ядер :", os.cpu_count())
    print("  ОС            :", platform.platform())
    print("  навантаження  : %d процесів x %d замовлень"
          % (PROTSESIV, ZAMOVLEN_NA_PROTSES))
    print()


def prognaty(nomer, zamok):
    zalyshok = mp.Value("i", ZAPAS_POCHATKOVYI)
    vidvantazheno = mp.Value("i", 0)
    vidmov = mp.Value("i", 0)

    procesy = [
        mp.Process(
            target=obrobyty_zamovlennya,
            args=(zalyshok, vidvantazheno, vidmov, 1000 + i, zamok)
        )
        for i in range(PROTSESIV)
    ]

    t0 = time.perf_counter()

    for p in procesy:
        p.start()

    for p in procesy:
        p.join()

    tryvalist = time.perf_counter() - t0

    z = zalyshok.value
    v = vidvantazheno.value
    vm = vidmov.value

    # ── перевірка інваріантів ──────────────────────────────────
    porushennya = []

    if z < 0:
        porushennya.append("залишок від'ємний: %d" % z)

    if v + z != ZAPAS_POCHATKOVYI:
        porushennya.append(
            "баланс не сходиться: %d + %d = %d, а має бути %d"
            % (v, z, v + z, ZAPAS_POCHATKOVYI)
        )

    stan = "OK" if not porushennya else "ПОРУШЕНО"

    print(
        "  прогін %d:  залишок %8d   відвантажено %8d   відмов %6d   "
        "%6.2f c   %s"
        % (nomer, z, v, vm, tryvalist, stan)
    )

    for p in porushennya:
        print("             -> " + p)

    return not porushennya


if __name__ == "__main__":

    pasport()

    print("=" * 68)
    print("ПРОГОНИ.  Початковий запас:", ZAPAS_POCHATKOVYI)
    print("=" * 68)

    # Спільний замок для всіх процесів
    zamok = mp.Lock()

    chysto = 0

    PROGONIV = 5

    for i in range(1, PROGONIV + 1):

        if prognaty(i, zamok):
            chysto += 1

    print()
    print("=" * 68)
    print("  Без порушень: %d із %d" % (chysto, PROGONIV))
    print("=" * 68)