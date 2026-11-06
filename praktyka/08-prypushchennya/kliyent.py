"""Клієнт служби «журнал замірів».

За замовчуванням працює наївно. Виправлення вмикаються прапорцями:
--taimaut, --sprob, --kliuch.
"""
import argparse
import json
import socket
import time
import uuid

HOST = "127.0.0.1"


def poslaty(port, zapyt, taimaut):
    """Одна спроба: з'єднатись, надіслати JSON-рядок і прочитати відповідь."""
    with socket.create_connection((HOST, port), timeout=taimaut) as s:
        s.settimeout(taimaut)
        with s.makefile("rwb") as f:
            f.write((json.dumps(zapyt, ensure_ascii=False) + "\n").encode("utf-8"))
            f.flush()
            ryadok = f.readline()
            if not ryadok:
                raise ConnectionError("з'єднання закрито без відповіді")
            return json.loads(ryadok.decode("utf-8"))


def poslaty_z_povtoramy(port, zapyt, taimaut, sprob):
    """Повторні спроби з експоненційною витримкою."""
    ostannya = None
    for sproba in range(sprob):
        try:
            return poslaty(port, zapyt, taimaut), sproba + 1
        except (OSError, ConnectionError, json.JSONDecodeError) as e:
            ostannya = e
            if sproba + 1 < sprob:
                time.sleep(0.2 * (2 ** sproba))
    raise ostannya


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=50007,
                   help="50007 — напряму до служби, 50010 — через проксі")
    p.add_argument("--kilkist", type=int, default=10)
    p.add_argument("--taimaut", type=float, default=None,
                   help="таймаут однієї спроби в секундах")
    p.add_argument("--sprob", type=int, default=1,
                   help="максимальна кількість спроб для одного запису")
    p.add_argument("--kliuch", action="store_true",
                   help="використовувати ключ ідемпотентності")
    args = p.parse_args()

    if args.kilkist < 1 or args.sprob < 1:
        p.error("--kilkist і --sprob мають бути не меншими за 1")

    print(f"[клієнт] порт {args.port} · таймаут {args.taimaut} · "
          f"спроб {args.sprob} · ключ {'так' if args.kliuch else 'ні'}")

    nadislano = 0
    pomylok = 0
    povtoriv = 0
    t_start = time.perf_counter()

    for i in range(args.kilkist):
        zapys = {"rozmir": "1200x800", "chas": round(0.15 + i * 0.01, 3)}
        zapyt = {"dia": "dodaty", "zapys": zapys}
        if args.kliuch:
            # Один ключ на логічний запис; той самий ключ використовується в усіх повторах.
            zapyt["kliuch"] = str(uuid.uuid4())

        t0 = time.perf_counter()
        try:
            vidpovid, sprob = poslaty_z_povtoramy(
                args.port, zapyt, args.taimaut, args.sprob
            )
            povtoriv += sprob - 1
            nadislano += 1
            print(f"  {i + 1:>3}. {vidpovid} · "
                  f"{1000 * (time.perf_counter() - t0):.0f} мс"
                  + (f" · спроб {sprob}" if sprob > 1 else ""))
        except Exception as e:
            pomylok += 1
            print(f"  {i + 1:>3}. ПОМИЛКА {type(e).__name__}: {e} · "
                  f"{1000 * (time.perf_counter() - t0):.0f} мс")

    zagalom = time.perf_counter() - t_start
    print(f"\n[клієнт] успішно {nadislano} з {args.kilkist} · "
          f"помилок {pomylok} · зайвих спроб {povtoriv} · "
          f"разом {zagalom:.2f} с")

    # Лічильник читаємо напряму зі служби, оминаючи проксі.
    try:
        stan = poslaty(50007, {"dia": "stan"}, 5)
        print(f"[служба] записів: {stan['vsogo']} · "
              f"унікальних ключів: {stan['unikalnyh_kliuchiv']}")
        if stan["vsogo"] > args.kilkist:
            print(f"ДУБЛІКАТИ: {stan['vsogo'] - args.kilkist} зайвих записів")
        elif stan["vsogo"] > nadislano:
            print("НЕВИЗНАЧЕНІСТЬ: служба прийняла більше записів, "
                  "ніж клієнт підтвердив")
        elif stan["vsogo"] < args.kilkist:
            print(f"МОЖЛИВІ ВТРАТИ: на {args.kilkist - stan['vsogo']} записів менше")
        else:
            print("Кількість записів відповідає кількості запитів")
    except OSError as e:
        print("[клієнт] не вдалося отримати стан служби:", e)


if __name__ == "__main__":
    main()
