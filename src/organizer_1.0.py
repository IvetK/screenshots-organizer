#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import re
from datetime import datetime
from PIL import Image
import pytesseract
from pillow_heif import register_heif_opener
import argparse
import random
import json
import imagehash

# Import kategorií ze samostatného souboru
from categories import CATEGORIES, WORD_WEIGHTS, SOCIAL_MEDIA_UI_KEYWORDS
from unidecode import unidecode  # pip install Unidecode

register_heif_opener()

# NASTAVENÍ
MAX_TEST_FILES = 100
SOURCE_FOLDER = "/Volumes/Elements2023/Screenshot Organizer/screenshots"


def filter_social_media_ui_text(text):
    """
    Odstraní UI prvky ze sociálních médií (follow, like, message...)
    a ignoruje metriky typu '10,2 k', '28k', '1.1m' apod.
    """
    if not text:
        return text

    words = text.split()
    filtered_words = []

    for word in words:
        word_lower = word.lower().strip('.,!?;:')

        # 1) UI prvky sociálních sítí (tvůj seznam SOCIAL_MEDIA_UI_KEYWORDS)
        if any(ui_keyword in word_lower for ui_keyword in SOCIAL_MEDIA_UI_KEYWORDS):
            continue

        # 2) Počty/metriky: 10,2 k / 28k / 1.1m / 356K (povolíme i mezeru)
        if re.match(r'^\d{1,3}([.,]\d{1,2})?\s*[km]$', word_lower):
            continue

        filtered_words.append(word)

    return ' '.join(filtered_words)


def normalize_text_simple(s: str) -> str:
    """
    Odstraní diakritiku, převede na malá písmena, sjednotí mezery a odstraní interpunkci.
    Díky tomu bude hledání klíčových slov přesnější.
    """
    if not s:
        return ""
    s = unidecode(s.lower())            # "zahrádka" -> "zahradka"
    s = re.sub(r"[^\w\s]", " ", s)      # pryč tečky/čárky apod.
    s = re.sub(r"\s+", " ", s).strip()  # sjednotit mezery
    return s


def tokenize_words(s: str) -> set:
    """
    Vrátí MNOŽINU slov (celá slova). Eliminujeme podřetězce (např. 'data' v 'candidate').
    """
    return set(re.findall(r"\b\w+\b", s))


def calculate_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def perceptual_hash(filepath):
    """Perceptuální hash pro zjištění vizuálních duplicit"""
    try:
        img = Image.open(filepath).convert('RGB')
        # phash je citlivý na vizuální podobnost
        return str(imagehash.phash(img))
    except Exception:
        return None


def extract_text_from_image(image_path):
    """
    Vylepšené předzpracování obrázku pro OCR:
    - převod do stupňů šedi
    - zvětšení (resize)
    - jednoduchý kontrast/threshold
    - lepší konfigurace pro pytesseract
    """
    try:
        img = Image.open(image_path)
        # převést na grayscale
        img = img.convert('L')

        # zvětšení pro lepší rozpoznání drobného textu
        scale = 1.5
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BILINEAR)

        # jednoduchý kontrast / threshold (nastavit opatrně)
        def enhance(p):
            if p < 50:
                return 0
            if p > 200:
                return 255
            return p
        img = img.point(enhance)

        # Tesseract config: OEM 3 (default LSTM), PSM 6 (blok textu)
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(img, lang='ces+eng', config=config)
        return text.lower().strip()
    except Exception as e:
        return f"[CHYBA: {e}]"


def categorize_text(text, debug=False):
    """
    Vrací tuple: (kategorie (str), matched_terms (list[str]))
    matched_terms jsou top klíčová slova, která rozhodnutí podpořila.
    """
    if not text or text.startswith("[CHYBA"):
        return "Neprirazeno", []

    # 1) FILTROVÁNÍ UI PRVKŮ ZE SOCIÁLNÍCH MÉDIÍ
    filtered_text = filter_social_media_ui_text(text)

    # 2) NORMALIZACE + TOKENIZACE
    norm_text = normalize_text_simple(filtered_text)  # string bez diakritiky, malé písmena
    tokens = tokenize_words(norm_text)                # množina slov

    if debug:
        print("\n" + "="*60)
        print("DEBUG - original (prvních 200):", text[:200])
        print("DEBUG - filtered:", filtered_text[:200])
        print("DEBUG - normalized:", norm_text[:200])
        print("="*60 + "\n")

    # ===== KONTEXTOVÁ PRAVIDLA =====
    # Používáme kombinaci: token matching pro jednotlivá slova + substring matching pro fráze
    
    # Pomocná funkce pro matching
    def matches_keyword(keyword, norm_text, tokens):
        """Zkontroluje keyword - buď jako celé slovo (token) nebo jako frázi v textu"""
        k_norm = normalize_text_simple(keyword)
        # pokud má keyword mezery, hledej jako substring (fráze)
        if ' ' in k_norm:
            return k_norm in norm_text
        # jinak hledej jako celé slovo
        return k_norm in tokens
    
    # Pomocná funkce pro fráze s tolerancí (slova mohou být až 10 slov od sebe)
    def matches_phrase_flexible(phrase, norm_text, max_distance=10):
        """Hledá frázi s tolerancí - slova mohou být až max_distance slov od sebe"""
        words = phrase.split()
        if len(words) == 1:
            return words[0] in norm_text
        
        # Najdi všechny pozice prvního slova
        text_words = norm_text.split()
        for i, text_word in enumerate(text_words):
            if words[0] == text_word:
                # Zkontroluj, jestli jsou další slova fráze do max_distance dalších slov
                for j, phrase_word in enumerate(words[1:], 1):
                    found = False
                    for k in range(1, min(max_distance + 1, len(text_words) - i)):
                        if i + k < len(text_words) and text_words[i + k] == phrase_word:
                            found = True
                            break
                    if not found:
                        break
                else:
                    # Všechna slova fráze nalezena
                    return True
        return False
    
    # PRAVIDLO 1: Recepty - musí mít alespoň 2 triggery
    recipe_triggers = [
        "recept", "recipe", "ingredients", "pasta", "slowcooker", "slow cooker",
        "boredoflunch", "chorizo", "creamy", "chicken", "jidelni plan", "jidelnicek"
    ]
    recipe_hits = sum(1 for k in recipe_triggers if matches_keyword(k, norm_text, tokens))
    if recipe_hits >= 2:
        matched = [k for k in recipe_triggers if matches_keyword(k, norm_text, tokens)]
        if debug:
            print(f"✅ PRAVIDLO 1 AKTIVOVÁNO: Recepty (hits={recipe_hits})")
            print(f"   Matched keywords: {matched}")
        return "Recepty", matched

    # PRAVIDLO 2: Oblečení - musí mít alespoň 2 triggery
    clothing_triggers = [
        "bunda", "jacket", "kabat", "wheat", "bergam", "vyprodej", "sleva",
        "detska", "detska bunda", "zimnich", "zimnich dnu", "velikost", "size", 
        "kalhoty", "pants", "saty", "dress", "boty"
    ]
    clothing_hits = sum(1 for k in clothing_triggers if matches_keyword(k, norm_text, tokens))
    if clothing_hits >= 2:
        matched = [k for k in clothing_triggers if matches_keyword(k, norm_text, tokens)]
        if debug:
            print(f"✅ PRAVIDLO 2 AKTIVOVÁNO: Obleceni_Styl (hits={clothing_hits})")
            print(f"   Matched keywords: {matched}")
        return "Obleceni_Styl", matched

    # PRAVIDLO 3: Zahrada - velmi specifické rostliny
    garden_strong_keywords = [
        "allium", "giganteum", "ambassador", "pinball wizard", "white giant",
        "hydrangea", "hortenzie", "erigeron", "karvinskianus",
        "trvalky", "perennials", "pinus mugo", "salvia", "purple rain",
        "gravel garden", "sterkovy zahon", "osvetleni zahrady", "vysadba trvalek",
        "flower bed", "planting border", "structured planting", "paving",
        "petrazahradnici", "biogarden", "zahradka", "jahody", "stromy", "keře"
    ]
    matched_garden = []
    for k in garden_strong_keywords:
        if ' ' in k:
            if matches_phrase_flexible(normalize_text_simple(k), norm_text, max_distance=10):
                matched_garden.append(k)
        else:
            if matches_keyword(k, norm_text, tokens):
                matched_garden.append(k)
    
    if matched_garden:
        if debug:
            print(f"✅ PRAVIDLO 3 AKTIVOVÁNO: Zahrada")
            print(f"   Matched keywords: {matched_garden}")
        return "Zahrada", matched_garden

    # PRAVIDLO 4: Outdoor / pergola / terasa → Dum_Design
    outdoor_design_keywords = [
        "pergola", "terasa", "patio", "outdoor living", "outdoor seating",
        "venkovni posezeni", "terrace", "deck", "lamelova pergola", "wooden pergola",
        "intertwining outdoor", "family life", "everyday rituals"
    ]
    matched_outdoor = []
    for k in outdoor_design_keywords:
        if ' ' in k:
            if matches_phrase_flexible(normalize_text_simple(k), norm_text, max_distance=10):
                matched_outdoor.append(k)
        else:
            if matches_keyword(k, norm_text, tokens):
                matched_outdoor.append(k)
    
    if matched_outdoor:
        if debug:
            print(f"✅ PRAVIDLO 4 AKTIVOVÁNO: Dum_Design")
            print(f"   Matched keywords: {matched_outdoor}")
        return "Dum_Design", matched_outdoor

    # PRAVIDLO 5: Dětský pokoj (silné triggery)
    kids_room_strong = [
        "detsky pokoj", "detsky", "kids room", "nursery", "montessori",
        "teepee", "baldachyn", "canopy", "girlanda", "bunting", "house bed"
    ]
    kids_found = [k for k in kids_room_strong if matches_keyword(k, norm_text, tokens)]
    if kids_found:
        if debug:
            print(f"✅ PRAVIDLO 5 AKTIVOVÁNO: Dum_Design")
            print(f"   Matched keywords: {kids_found}")
        return "Dum_Design", kids_found

    # PRAVIDLO 6: Dětský pokoj + design keywords → Dum_Design
    kids_room_keywords = [
        "detsky pokoj", "kids room", "bedroom", "pokoj",
        "house bed", "montessori bed"
    ]
    design_keywords = [
        "design", "nabytek", "postel", "bed", "furniture", "interior", "interier", "styl"
    ]
    has_kids_room = any(matches_keyword(k, norm_text, tokens) for k in kids_room_keywords)
    has_design = any(matches_keyword(k, norm_text, tokens) for k in design_keywords)
    if has_kids_room and has_design:
        matched = [k for k in kids_room_keywords + design_keywords if matches_keyword(k, norm_text, tokens)]
        if debug:
            print(f"✅ PRAVIDLO 6 AKTIVOVÁNO: Dum_Design")
            print(f"   Matched keywords: {matched}")
        return "Dum_Design", matched

    # PRAVIDLO 7: Kočárek → Rodina
    stroller_keywords = ["kocarek", "stroller", "bergam", "bambusova", "vlozka", "autosedacka"]
    matched_stroller = [k for k in stroller_keywords if matches_keyword(k, norm_text, tokens)]
    if matched_stroller:
        if debug:
            print(f"✅ PRAVIDLO 7 AKTIVOVÁNO: Rodina")
            print(f"   Matched keywords: {matched_stroller}")
        return "Rodina", matched_stroller

    # PRAVIDLO 8: Zdraví - dermatitida, akné...
    health_issue_keywords = [
        "dermatitida", "akne", "vyrazka", "ekzem", "alergie", "zinkova mast", "masticka"
    ]
    matched_health = [k for k in health_issue_keywords if matches_keyword(k, norm_text, tokens)]
    if matched_health:
        if debug:
            print(f"✅ PRAVIDLO 8 AKTIVOVÁNO: Zdravi")
            print(f"   Matched keywords: {matched_health}")
        return "Zdravi", matched_health

    # PRAVIDLO 9: Podcast + IT context → IT_Prace
    podcast_keywords = ["podcast", "epizoda", "episode"]
    it_keywords = ["kyberbezpecnost", "cybersecurity", "hacking", "scam", "bezpecnost", "utok", "vulnerability", "security"]
    has_podcast = any(matches_keyword(k, norm_text, tokens) for k in podcast_keywords)
    has_it_context = any(matches_keyword(k, norm_text, tokens) for k in it_keywords)
    if has_podcast and has_it_context:
        matched = [k for k in podcast_keywords + it_keywords if matches_keyword(k, norm_text, tokens)]
        if debug:
            print(f"✅ PRAVIDLO 9 AKTIVOVÁNO: IT_Prace")
            print(f"   Matched keywords: {matched}")
        return "IT_Prace", matched

    # PRAVIDLO 10: IT - specific tools
    it_strong_keywords = [
        "jira", "postman", "swagger", "pytest", "selenium",
        "docker", "kubernetes", "jenkins", "cicd", "api testing",
        "github", "gitlab", "sql", "pull request", "merge request",
        "kyberneticke bezpecnosti", "umele inteligence", "ibm", "czechitas",
        "skillsbuild", "digitalni certifikat"
    ]
    matched_it = []
    for k in it_strong_keywords:
        if ' ' in k:
            if matches_phrase_flexible(normalize_text_simple(k), norm_text, max_distance=10):
                matched_it.append(k)
        else:
            if matches_keyword(k, norm_text, tokens):
                matched_it.append(k)
    
    if matched_it:
        if debug:
            print(f"✅ PRAVIDLO 10 AKTIVOVÁNO: IT_Prace")
            print(f"   Matched keywords: {matched_it}")
        return "IT_Prace", matched_it

    # ===== KONEC KONTEXTOVÝCH PRAVIDEL =====

    if debug:
        print(f"❌ Žádné kontextové pravidlo nebylo aktivováno")
        print(f"   → Pokračuji do váhového systému\n")

    # Kontext-aware (hračky) - pro případné výjimky v scoringu
    toy_keywords = ["stavebnice", "hracka", "hra", "puzzle", "lego", "vrtacka"]
    has_toy_context = any(normalize_text_simple(k) in tokens for k in toy_keywords)

    # ===== VÁHOVANÉ BODOVÁNÍ (scoring) =====
    scores = {}
    matches_for_category = {}

    for category, keywords in CATEGORIES.items():
        weighted_score = 0
        matched = []
        for keyword in keywords:
            k_norm = normalize_text_simple(keyword)
            if k_norm in tokens:
                # výjimka pro hračky u oblečení (pokud je to hračka, ignoruj velikosti)
                if category == "Obleceni_Styl" and has_toy_context and k_norm in ["vel", "velikost", "size", "cm"]:
                    continue
                weight = WORD_WEIGHTS.get(keyword, WORD_WEIGHTS.get(k_norm, 3))
                weighted_score += weight
                matched.append((k_norm, weight))
        scores[category] = weighted_score
        # ulož top matched tokeny (max 5)
        matches_for_category[category] = [m[0] for m in sorted(matched, key=lambda x: x[1], reverse=True)[:5]]

    # ===== NEGATIVE HINTS (penalizace chybných kategorií) =====
    NEGATIVE_HINTS = {
        "IT_Prace": [r"\bzahrad", r"\brostlin", r"\bflower\b", r"\bgarden\b"],
        "Dum_Design": [r"\bcommit\b", r"\brepo\b", r"\bendpoint\b", r"\bhttp\b"]
    }
    for cat, patterns in NEGATIVE_HINTS.items():
        if cat in scores:
            penalty = 0
            for p in patterns:
                if re.search(p, norm_text):
                    penalty += 2
            if penalty:
                scores[cat] = max(0, scores[cat] - penalty)
                if debug:
                    print(f"NEGATIVE HINT: snizil jsem score {cat} o {penalty} kvuli '{patterns}'")

    # Minimalni prah a reseni remizy
    if not scores:
        return "Neprirazeno", []
    max_score = max(scores.values())
    if max_score < 3:  # minimální důvěra -> Neprirazeno
        return "Neprirazeno", []

    # zjisti top dvě skóre pro rozhodnutí o remíze
    sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_cat, top_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

    # pokud je rozdil maly -> neurčeno
    if (top_score - second_score) < 2:
        if debug:
            print(f"AMBIGUITY: top {top_cat}={top_score}, runner-up={second_score} -> Neprirazeno")
        return "Neprirazeno", []

    # vrátíme kategorii a top matched terms
    top_matched = matches_for_category.get(top_cat, [])
    if debug:
        print(f"FINAL CATEGORY: {top_cat} (score={top_score}) matched={top_matched}")

    return top_cat, top_matched


def is_image_file(filename):
    extensions = ['.heic', '.jpg', '.jpeg', '.png', '.HEIC', '.JPG', '.JPEG', '.PNG']
    return any(filename.lower().endswith(ext) for ext in extensions)


def dry_run_test(folder=None, max_test_files=100, sample=None, debug=False):
    """
    Dry run test - simulace kategorizace bez pohybu souborů.
    
    Args:
        folder: Cesta ke složce se screenshoty
        max_test_files: Maximum souborů k testování
        sample: Počet náhodných souborů k testování (None = všechny)
        debug: Zapnout debug výpis
    """
    print("=" * 70)
    print("🧪 DRY RUN TEST - FILTROVÁNÍ SOCIAL MEDIA UI + OCR improvements")
    print("=" * 70)
    
    SOURCE = folder if folder else SOURCE_FOLDER

    if not os.path.exists(SOURCE):
        print(f"❌ Složka neexistuje: {SOURCE}")
        return

    all_files = [f for f in os.listdir(SOURCE) if is_image_file(f)]
    total_files = len(all_files)

    if total_files == 0:
        print(f"❌ Ve složce nejsou žádné obrázky!")
        return

    # náhodný vzorek nebo prvních N
    if sample and sample > 0:
        if sample >= total_files:
            test_files = all_files[:max_test_files]
        else:
            test_files = random.sample(all_files, min(sample, max_test_files))
    else:
        test_files = all_files[:max_test_files]

    print(f"📁 Testovací složka: {SOURCE}")
    print(f"📊 Nalezeno souborů: {total_files}")
    print(f"🧪 Testuji: {len(test_files)} souborů")
    if sample:
        print(f"   (náhodný vzorek: {sample})")
    print("=" * 70)
    print("\n⚠️  SIMULACE - žádné změny!")
    print("✨ Ignoruji UI prvky: follow, like, message, 1.1M, 356K atd.\n")
    input("Stiskni Enter pro spuštění...")

    stats = {category: [] for category in list(CATEGORIES.keys()) + ["Neprirazeno"]}
    duplicates = []
    errors = []
    seen_hashes = {}
    seen_p_hashes = {}

    print("\n" + "=" * 70)
    print("🔍 SPOUŠTÍM TEST...")
    print("=" * 70 + "\n")

    for idx, filename in enumerate(test_files, 1):
        source_path = os.path.join(SOURCE, filename)
        print(f"[{idx}/{len(test_files)}] {filename[:40]}...", end=" ")

        try:
            # klasický MD5 hash
            file_hash = calculate_file_hash(source_path)
            if file_hash in seen_hashes:
                print("🗑️  DUPLICITA (identické soubory)")
                duplicates.append((filename, seen_hashes[file_hash]))
                continue
            seen_hashes[file_hash] = filename

            # perceptual hash (vizuální duplicity)
            p_hash = perceptual_hash(source_path)
            if p_hash:
                if p_hash in seen_p_hashes:
                    print("⚠️  VIZUÁLNÍ DUPLIKÁT (podobné obrázky)")
                    duplicates.append((filename, seen_p_hashes[p_hash]))
                    # pouze upozorníme, ale budeme dál zpracovávat
                else:
                    seen_p_hashes[p_hash] = filename

            print("📖", end=" ")
            text = extract_text_from_image(source_path)
            cat, matched_terms = categorize_text(text, debug=debug)

            # uložíme do statistik
            stats[cat].append({
                'filename': filename,
                'text_preview': text[:150] if text else "[prázdné]",
                'matched': matched_terms
            })

            # výpis do terminálu : kategorie + top matched terms
            matched_str = ", ".join(matched_terms[:3]) if matched_terms else "(žádné)"
            print(f"✅ → {cat}    |  klíčová slova: {matched_str}")

        except Exception as e:
            print(f"❌ CHYBA: {e}")
            errors.append((filename, str(e)))

    # Souhrn výsledků
    print("\n" + "=" * 70)
    print("📊 VÝSLEDKY")
    print("=" * 70)

    print(f"\n✅ Testováno: {len(test_files)}")
    print(f"🗑️  Duplicity: {len(duplicates)}")
    print(f"❌ Chyby: {len(errors)}")

    print(f"\n📂 KATEGORIE:\n")
    for category in CATEGORIES.keys():
        count = len(stats[category])
        if count > 0:
            print(f"   📁 {category}: {count}")
            for item in stats[category][:2]:
                print(f"      - {item['filename'][:50]}")
                if item['text_preview'] and item['text_preview'] != "[prázdné]":
                    preview = item['text_preview'].replace('\n', ' ')[:80]
                    print(f"        💬 \"{preview}...\"")
                    print(f"        🔎 matched: {', '.join(item['matched'][:3]) if item['matched'] else '(žádné)'}")
            print()

    if stats["Neprirazeno"]:
        print(f"   📁 Neprirazeno: {len(stats['Neprirazeno'])}")
        print(f"      ({len(stats['Neprirazeno'])/len(test_files)*100:.1f}%)\n")
        for item in stats["Neprirazeno"][:5]:
            print(f"      - {item['filename'][:50]}")
            if item['text_preview']:
                preview = item['text_preview'].replace('\n', ' ')[:80]
                print(f"        💬 \"{preview}...\"")

    print("\n" + "=" * 70)
    print("✅ TEST DOKONČEN!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kategorizace screenshotů")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="screenshots",
        help="Cesta ke složce se screenshoty (default: ./screenshots)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Kolik náhodných screenshotů použít pro test (např. --sample 100)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Zobrazí detailní výstup při testování"
    )
    args = parser.parse_args()

    input_dir = args.input_dir

    if not os.path.exists(input_dir):
        print(f"❌ Složka '{input_dir}' neexistuje.")
        exit(1)

    # Vyber náhodný vzorek, pokud je --sample zadán
    files = [f for f in os.listdir(input_dir) if is_image_file(f)]
    
    if args.sample:
        print(f"➡️ Použit náhodný vzorek {min(args.sample, len(files))} obrázků ze složky '{input_dir}'\n")
    else:
        print(f"➡️ Zpracovávám všech {len(files)} obrázků ze složky '{input_dir}'\n")

    # Spuštění dry run testu
    dry_run_test(
        folder=input_dir, 
        sample=args.sample,
        debug=args.debug
    )