Screenshots Organizer
První verze projektu.

# Screenshots Organizer

Malý nástroj, který třídí screenshoty do složek podle klíčových slov (CZ/EN).

## Proč
- Neztratit hodiny ručním tříděním.
- Mít jasná pravidla (klíčová slova), která lze snadno rozšířit.
- Umět cílit na složky na **externím disku**, aby nezabíraly místo na Macu.

## Jak to bude fungovat (plán)
1. Načíst nové screenshoty ze zadané cesty "/Volumes/Elements2023/Screenshot Organizer/screenshots"
2. Podle pravidel/klíčových slov určit kategorii.
3. Přesunout/zkopírovat do cílové složky.
4. Přidat log (co se kam přesunulo).

## Stav projektu
- ✅ Založen repozitář a základní dokumentace.
- 🔧 Pracuji na pravidlech (CZ/EN) a jednoduchém CLI.

## Roadmap
- [ ] `src/cli.py` – příkazová řádka: `organizer --src --dst`
- [ ] `src/rules.py` – klíčová slova (CZ/EN), snadná rozšiřitelnost
- [ ] Logování + „dry-run“ režim
- [ ] Jednoduché testy základních pravidel
