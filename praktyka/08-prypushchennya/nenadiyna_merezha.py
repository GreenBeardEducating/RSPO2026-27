"""Ненадійна мережа — проксі, що стоїть між клієнтом і службою й ламає її."""
import argparse
import random
import socket
import threading
import time

HOST = "127.0.0.1"


def perekachaty(zvidky, kudy, zatrymka_ms, shvydkist,
                vtratyty_p, mitka, stat):
    """Качає байти в один бік, дорогою імітуючи мережеві проблеми."""
    try:
        while True:
            dani = zvidky.recv(4096)
            if not dani:
                break
            if zatrymka_ms:
                time.sleep(zatrymka_ms / 1000)
            if vtratyty_p and random.random() < vtratyty_p:
                stat["vtracheno"] += 1
                print(f"[мережа] {mitka}: загублено {len(dani)} Б — рвемо з'єднання")
                break
            if shvydkist:
                for i in range(0, len(dani), 64):
                    kudy.sendall(dani[i:i + 64])
                    time.sleep(64 / shvydkist)
            else:
                kudy.sendall(dani)
            stat["bajt"] += len(dani)
    except OSError:
        pass
    finally:
        for s in (zvidky, kudy):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def obsluzhyty(kliyent, args, stat):
    if args.obryv_vidrazu and random.random() < args.obryv_vidrazu:
        stat["obirvano"] += 1
        print("[мережа] обрив до служби — запит не дійшов")
        kliyent.close()
        return
    try:
        sluzhba = socket.create_connection((HOST, args.kudy), timeout=5)
    except OSError as e:
        print("[мережа] не змогла з'єднатись зі службою:", e)
        kliyent.close()
        return

    t1 = threading.Thread(
        target=perekachaty,
        args=(kliyent, sluzhba, args.zatrymka, args.shvydkist,
              0.0, "клієнт→служба", stat),
        daemon=True
    )
    t2 = threading.Thread(
        target=perekachaty,
        args=(sluzhba, kliyent, args.zatrymka, args.shvydkist,
              args.vtratyty_vidpovid, "служба→клієнт", stat),
        daemon=True
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slukhaty", type=int, default=50010,
                   help="порт для клієнта")
    p.add_argument("--kudy", type=int, default=50007,
                   help="порт справжньої служби")
    p.add_argument("--zatrymka", type=int, default=0,
                   help="мс на кожну порцію даних")
    p.add_argument("--shvydkist", type=int, default=0,
                   help="байтів на секунду")
    p.add_argument("--vtratyty-vidpovid", type=float, default=0.0,
                   help="ймовірність загубити ВІДПОВІДЬ")
    p.add_argument("--obryv-vidrazu", type=float, default=0.0,
                   help="ймовірність обірвати ще до служби")
    p.add_argument("--vidmova", action="store_true",
                   help="взагалі не приймати з'єднань")
    p.add_argument("--nasinnia", type=int, default=None,
                   help="зерно випадковості")
    args = p.parse_args()

    if args.nasinnia is not None:
        random.seed(args.nasinnia)

    if args.vidmova:
        print(f"[мережа] режим «служба недоступна»: порт {args.slukhaty} ніхто не слухає")
        print("[мережа] Ctrl+C щоб вийти")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return

    stat = {"bajt": 0, "vtracheno": 0, "obirvano": 0}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, args.slukhaty))
    s.listen(8)
    print(f"[мережа] клієнт → {HOST}:{args.slukhaty} → служба :{args.kudy}")
    print(f"[мережа] затримка {args.zatrymka} мс · швидкість "
          f"{args.shvydkist or '∞'} Б/с · втрата відповіді "
          f"{args.vtratyty_vidpovid} · обрив до служби {args.obryv_vidrazu}")
    try:
        while True:
            kliyent, _ = s.accept()
            threading.Thread(
                target=obsluzhyty, args=(kliyent, args, stat), daemon=True
            ).start()
    except KeyboardInterrupt:
        print(f"\n[мережа] перекачано {stat['bajt']} Б · загублено відповідей "
              f"{stat['vtracheno']} · обірвано до служби {stat['obirvano']}")
    finally:
        s.close()


if __name__ == "__main__":
    main()
