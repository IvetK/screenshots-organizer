#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import re
from datetime import datetime
from PIL import Image
import pytesseract
from pillow_heif import register_heif_opener

# Import kategorií ze samostatného souboru
from categories import CATEGORIES, WORD_WEIGHTS, SOCIAL_MEDIA_UI_KEYWORDS

register_heif_opener()

# NASTAVENÍ
MAX_TEST_FILES = 100
SOURCE_FOLDER = "/Volumes/Elements2023/Screenshot Organizer/screenshots"


def filter_social_media_ui_text(text):
    """
    Odstraní UI prvky ze sociálních médií z textu.
    Ignoruje slova jako follow, like, message a počty typu 1.1M, 356K.
    """
    if not text:
        return text
    
    # Rozdělíme text na slova
    words = text.split()
    filtered_words = []
    
    for word in words:
        word_lower = word.lower().strip('.,!?;:')
        
        # Ignorujeme UI prvky ze sociálních médií
        if any(ui_keyword in word_lower for ui_keyword in SOCIAL_MEDIA_UI_KEYWORDS):
            continue
        
        # Ignorujeme počty ve formátu 1.1M, 356K, 267K atd.
        if re.match(r'^\d+[.,]?\d*[km]$', word_lower):
            continue
        
        # Pokud slovo prošlo, přidáme ho
        filtered_words.append(word)
    
    return ' '.join(filtered_words)


def calculate_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        text = pytesseract.image_to_string(img, lang='ces+eng')
        return text.lower().strip()
    except Exception as e:
        return f"[CHYBA: {e}]"


def categorize_text(text):
    if not text or text.startswith("[CHYBA"):
        return "Neprirazeno"
    
    # FILTROVÁNÍ UI PRVKŮ ZE SOCIÁLNÍCH MÉDIÍ
    filtered_text = filter_social_media_ui_text(text)
    
    # KONTEXT-AWARE PRAVIDLA
    toy_keywords = ["stavebnice", "hračka", "hracka", "hra", "puzzle", "lego", 
                    "vrtačka", "vrtacka", "nástroje pro děti", "nastroje pro deti"]
    has_toy_context = any(keyword in filtered_text for keyword in toy_keywords)
    
    # WEIGHTED SCORING - váhované bodování
    scores = {}
    
    for category, keywords in CATEGORIES.items():
        weighted_score = 0
        for keyword in keywords:
            if keyword.lower() in filtered_text:
                # SPECIÁLNÍ PRAVIDLO: Pokud je to hračka, ignoruj "vel.", "cm" pro Oblečení
                if category == "Obleceni_Styl" and has_toy_context:
                    if keyword in ["vel.", "velikost", "size", "cm"]:
                        continue
                
                # Získej váhu slova (výchozí = 3 body pokud není ve slovníku)
                weight = WORD_WEIGHTS.get(keyword, 3)
                weighted_score += weight
        
        scores[category] = weighted_score
    
    # Najdi kategorii s nejvyšším skóre
    max_score = max(scores.values())
    
    # Pokud žádná shoda, vrať Neprirazeno
    if max_score == 0:
        return "Neprirazeno"
    
    # PRAVIDLO PRO REMÍZU: Pokud fitness/exercise context, preferuj Zdravi
    fitness_keywords = ["exercise", "fitness", "workout", "training", "calisthenics", "gym"]
    has_fitness_context = any(keyword in filtered_text for keyword in fitness_keywords)
    
    if has_fitness_context and "Zdravi" in scores and scores["Zdravi"] == max_score:
        return "Zdravi"
    
    # Vrať kategorii s nejvyšším vážený skóre
    for category, score in scores.items():
        if score == max_score:
            return category
    
    return "Neprirazeno"


def is_image_file(filename):
    extensions = ['.heic', '.jpg', '.jpeg', '.png', '.HEIC', '.JPG', '.JPEG', '.PNG']
    return any(filename.lower().endswith(ext) for ext in extensions)


def dry_run_test():
    print("=" * 70)
    print("🧪 DRY RUN TEST - FILTROVÁNÍ SOCIAL MEDIA UI")
    print("=" * 70)
    
    if not os.path.exists(SOURCE_FOLDER):
        print(f"❌ Složka neexistuje: {SOURCE_FOLDER}")
        return
    
    all_files = [f for f in os.listdir(SOURCE_FOLDER) if is_image_file(f)]
    total_files = len(all_files)
    
    if total_files == 0:
        print(f"❌ Ve složce nejsou žádné obrázky!")
        return
    
    test_files = all_files[:MAX_TEST_FILES]
    
    print(f"📁 Testovací složka: {SOURCE_FOLDER}")
    print(f"📊 Nalezeno souborů: {total_files}")
    print(f"🧪 Testuji prvních: {len(test_files)}")
    print("=" * 70)
    print("\n⚠️  SIMULACE - žádné změny!")
    print("✨ Ignoruji UI prvky: follow, like, message, 1.1M, 356K atd.\n")
    
    input("Stiskni Enter...")
    
    stats = {category: [] for category in list(CATEGORIES.keys()) + ["Neprirazeno"]}
    duplicates = []
    errors = []
    seen_hashes = {}
    
    print("\n" + "=" * 70)
    print("🔍 SPOUŠTÍM TEST...")
    print("=" * 70 + "\n")
    
    for idx, filename in enumerate(test_files, 1):
        source_path = os.path.join(SOURCE_FOLDER, filename)
        print(f"[{idx}/{len(test_files)}] {filename[:40]}...", end=" ")
        
        try:
            file_hash = calculate_file_hash(source_path)
            if file_hash in seen_hashes:
                print(f"🗑️  DUPLICITA")
                duplicates.append((filename, seen_hashes[file_hash]))
                continue
            
            seen_hashes[file_hash] = filename
            
            print("📖", end=" ")
            text = extract_text_from_image(source_path)
            
            category = categorize_text(text)
            
            stats[category].append({
                'filename': filename,
                'text_preview': text[:100] if text else "[prázdné]"
            })
            
            print(f"✅ → {category}")
            
        except Exception as e:
            print(f"❌ CHYBA: {e}")
            errors.append((filename, str(e)))
    
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
    try:
        dry_run_test()
    except KeyboardInterrupt:
        print("\n\n❌ Přerušeno")
    except Exception as e:
        print(f"\n\n❌ Chyba: {e}")