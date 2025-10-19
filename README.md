# Screenshots Organizer 📸

Inteligentní nástroj pro automatické třídění screenshotů do kategorií pomocí OCR a kontextových pravidel. Podporuje češtinu i angličtinu.

## 🎯 Proč tento projekt?

- **Ušetří hodiny času** – automatické třídění namísto ručního procházení stovek obrázků
- **Chytrá kategorizace** – využívá OCR (Tesseract) k rozpoznání textu a kontextová pravidla pro přesné zařazení
- **Flexibilní pravidla** – snadno rozšiřitelná klíčová slova v češtině i angličtině
- **Externí disk ready** – ukládání na externí disk, šetří místo na Macu
- **Bezpečný vývoj** – dry-run režim pro testování bez změn

## ✨ Hlavní funkce

### Aktuálně implementováno ✅

- **OCR zpracování** s vylepšeným předzpracováním obrázků (grayscale, resize, contrast)
- **12 kategorií** pokrývajících různé oblasti života
- **Kontextová pravidla** – chytrá detekce vyžadující kombinace klíčových slov
- **Filtrování social media UI** – ignoruje "follow", "like", metriky typu "1.1M"
- **Detekce duplicit** – MD5 hash i perceptuální hash pro vizuální podobnost
- **Váhový systém** – specifická slova mají vyšší prioritu
- **Debug režim** – podrobný výpis pro ladění pravidel
- **Dry-run test** – simulace třídění s přehledným výstupem

### Podporované kategorie

1. **Recepty** – slow cooker, meal prep, food bloggers
2. **Oblečení & Styl** – móda, capsule wardrobe, barvy
3. **Zahrada** – trvalky, gravel garden, kompozice
4. **Dům & Design** – interiér, půdorysy, outdoor living
5. **Děti - Aktivity** – DIY, crafting, Montessori
6. **Výchova dětí** – gentle parenting, discipline, rozvoj
7. **Zdraví** – fyzio, cvičení, těhotenství, léky
8. **IT & Práce** – QA, cybersecurity, AI, coding bootcamps
9. **Finance** – faktury, investice, hypotéky
10. **Cestování** – destinace, itineráře, tipy
11. **Děti - Svačiny** – bento boxy, zdravé snacky
12. **Svátky** – Vánoce, Velikonoce, Halloween

## 🚀 Jak to funguje

### Architektura

```
organizer_1.1.py         # Hlavní skript s OCR a kategorizací
├── categories.py        # Definice kategorií a klíčových slov
├── cli.py              # CLI rozhraní (v přípravě)
└── README.md           # Dokumentace
```

### Proces kategorizace

1. **Načtení obrázku** – podporuje HEIC, JPG, PNG
2. **OCR extraction** – Tesseract s optimalizací pro screenshot text
3. **Filtrování** – odstranění social media UI prvků a metrik
4. **Normalizace** – odstranění diakritiky, lowercase, tokenizace
5. **Kontextová pravidla** – prioritní kontrola specifických kombinací
6. **Váhové bodování** – fallback pro ambiguní případy
7. **Detekce duplicit** – kontrola MD5 i perceptuálního hashe

### Kontextová pravidla

Systém používá **dvoustupňový přístup**:

**Priorita 1: Kontextová pravidla**
- Vyžadují 2+ triggery NEBO 1 velmi specifický
- Příklad: "Recepty" potřebuje kombinaci jako "slow cooker" + "meal prep"

**Priorita 2: Váhový systém**
- Pokud kontextová pravidla neuspěla
- Slova mají váhy 1-10 podle specifičnosti
- Minimální práh 3 body pro kategorii

## 📦 Instalace

### Požadavky

```bash
# Python 3.8+
python3 --version

# Tesseract OCR
brew install tesseract
brew install tesseract-lang  # pro češtinu
```

### Závislosti

```bash
pip install pillow pytesseract pillow-heif imagehash unidecode
```

## 💻 Použití

### Dry-run test (doporučeno)

```bash
# Test na prvních 100 souborech
python3 organizer_1.1.py --input_dir screenshots

# Test na náhodném vzorku
python3 organizer_1.1.py --input_dir screenshots --sample 50

# S debug výpisem
python3 organizer_1.1.py --input_dir screenshots --sample 20 --debug
```

### Výstup

```
🧪 DRY RUN TEST - FILTROVÁNÍ SOCIAL MEDIA UI + OCR improvements
======================================================================
📁 Testovací složka: /path/to/screenshots
📊 Nalezeno souborů: 1543
🧪 Testuji: 100 souborů

⚠️  SIMULACE - žádné změny!
✨ Ignoruji UI prvky: follow, like, message, 1.1M, 356K atd.

[1/100] Screenshot_2024-01-15.png 📖 ✅ → Recepty | klíčová slova: slow cooker, meal prep
[2/100] Screenshot_2024-01-16.png 📖 ✅ → IT_Prace | klíčová slova: jira, api testing
...
```

## 🎨 Přizpůsobení

### Přidání nových klíčových slov

```python
# V categories.py
CATEGORIES = {
    "Nova_Kategorie": [
        "klicove", "slovo", "keyword",
        "fráze s mezerou"  # fungují i fráze
    ]
}
```

### Úprava vah

```python
# V categories.py
WORD_WEIGHTS = {
    "velmi_specifické": 10,  # unikátní pro kategorii
    "středně_specifické": 5,  # hlavní slova
    "obecné": 3,             # relevantní
    "velmi_obecné": 1        # může být všude
}
```

### Nové kontextové pravidlo

```python
# V organizer_1.1.py - funkce categorize_text()
# Přidat před váhový systém

nova_kategorie_triggers = [
    "velmi", "specificky", "trigger",
    "unikatni kombinace"
]
matched = [k for k in nova_kategorie_triggers 
           if matches_keyword(k, norm_text, tokens)]
if len(matched) >= 2:
    return "Nova_Kategorie", matched
```

## 🛠️ Roadmap

### Aktuální verze (v1.1) ✅
- [x] OCR s Tesseract
- [x] 12 kategorií s kontextovými pravidly
- [x] Filtrování social media UI
- [x] Detekce duplicit (MD5 + perceptual hash)
- [x] Dry-run test režim
- [x] Debug výpis

### Příští kroky
- [ ] **Skutečný přesun souborů** – implementace --move režimu
- [ ] **Logování** – JSON log všech operací
- [ ] **CLI vylepšení** – dokončení cli.py s argumenty
- [ ] **Statistiky** – přehled kategorií, úspěšnost
- [ ] **Export reportu** – markdown nebo HTML výstup
- [ ] **Konfigurace** – YAML/JSON pro nastavení
- [ ] **Batch processing** – zpracování po dávkách pro velké složky
- [ ] **Inkrementální update** – zpracovat jen nové soubory

### Budoucí nápady
- [ ] Web UI pro snadnější používání
- [ ] Machine learning model pro lepší kategorizaci
- [ ] Podpora dalších formátů (PDF, video thumbnails)
- [ ] Multi-kategorie – jeden screenshot do více složek
- [ ] Automatické přejmenování podle kategorie + data
- [ ] iCloud sync monitoring

## 🐛 Známé limity

- OCR kvalita závisí na čitelnosti textu na screenshotu
- Social media screenshoty s primárně UI prvky mohou končit v "Nepřiřazeno"
- Velmi krátké texty (1-2 slova) jsou těžko kategorizovatelné
- Tesseract někdy špatně rozpozná speciální znaky

## 📝 Tipy pro nejlepší výsledky

1. **Začni s testem** – vždy použij `--sample 20 --debug` pro novou kategorii
2. **Specifická slova** – přidávej velmi specifické triggery do pravidel
3. **Kombinace** – kontextová pravidla jsou přesnější než jednotlivá slova
4. **Váhy** – důležitá slova označuj vysokou váhou (8-10)
5. **Testuj často** – po změně pravidel vždy projeď test

## 📄 Struktura projektu

```
screenshot-organizer/
├── organizer_1.1.py       # Hlavní skript
├── categories.py          # Kategorie + klíčová slova
├── cli.py                 # CLI (v přípravě)
├── README.md             # Dokumentace
└── screenshots/          # Testovací složka
```

## 🤝 Příspěvky

Momentálně osobní projekt, ale nápady a feedback vítány!

## 📜 Licence

MIT License - používej svobodně

---

**Status:** 🟢 Aktivní vývoj | **Verze:** 1.1 | **Poslední update:** Říjen 2025