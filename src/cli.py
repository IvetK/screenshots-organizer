#!/usr/bin/env python3
# ↑ Říká systému: spuštěno Pythonem 3 (umožní spouštět soubor i jako ./cli.py)

import argparse              # práce s argumenty z příkazové řádky (CLI)
from pathlib import Path     # pohodlná práce s cestami k souborům/složkám

def main():
    # Vytvoříme parser, který popíše, jaké přepínače (parametry) program bere
    parser = argparse.ArgumentParser(description="Screenshots Organizer (dry-run ready)")

    # --src : odkud číst screenshoty (povinné)
    parser.add_argument("--src", required=True, help="Zdrojová složka se screenshoty")
    # --dst : kam je třídit (povinné)
    parser.add_argument("--dst", required=True, help="Cílová složka pro roztříděné soubory")
    # --dry-run : jen simulace, nic fyzicky nepřesouvat
    parser.add_argument("--dry-run", action="store_true", help="Neprovádět změny, jen vypsat, co by se stalo")

    args = parser.parse_args()   # načti hodnoty z příkazové řádky

    # Normalizuj cesty (rozšíří např. ~ na /Users/…)
    src = Path(args.src).expanduser()
    dst = Path(args.dst).expanduser()

    print(f"[INFO] Načítám z: {src}")
    print(f"[INFO] Ukládám do: {dst}")
    if args.dry_run:
        print("[INFO] Režim dry-run zapnutý (žádné přesuny se neprovedou)")

    # TODO: později sem přidáme:
    # - načtení pravidel z rules.py
    # - vyhodnocení kategorií podle klíčových slov
    # - přesun/simulaci přesunu souborů + logování

if __name__ == "__main__":
    main()  # spustí hlavní funkci, když soubor spustíme přímo
