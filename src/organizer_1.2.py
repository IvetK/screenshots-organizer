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
from categories_v1 import CATEGORIES, WORD_WEIGHTS, SOCIAL_MEDIA_UI_KEYWORDS
from unidecode import unidecode  # pip install Unidecode

register_heif_opener()

# ========================================================================
# NASTAVENÍ
# ========================================================================
MAX_TEST_FILES = 100

# VÝCHOZÍ CESTA (použije se pouze pokud nezadáš --input_dir)
# Doporučení: Vždy používej --input_dir při spuštění:
# python3 organizer_1.1.py --input_dir "/tvoje/cesta/screenshots"
DEFAULT_SOURCE_FOLDER = "/Volumes/Elements2023/Screenshot Organizer/screenshots"

# ========================================================================
# FUNKCE
# ========================================================================

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
    
    # PRAVIDLO 1: Recepty - vyžaduje 2+ triggery NEBO 1 velmi specifický
    recepty_very_specific = [
        # ===== VELMI SPECIFICKÉ NÁSTROJE =====
        "slowcooker", "slow cooker", "instant pot", "air fryer",
        "airfryer", "thermomix", "multicooker",
        
        # ===== FOOD BLOGGER ÚČTY =====
        "mycookingdiary", "toprecepty", "receptyonline", "boredoflunch",
        
        # ===== SPECIFICKÉ POKRMY =====
        "slowcooker chorizo", "creamy chicken", "sundried tomato pasta",
        
        # ===== JASNÉ INDIKÁTORY =====
        "cookbook", "meal prep", "mealplan",
        "jidelni plan", "food blog", "food diary"
    ]
    
    recepty_kombinacni = [
        "ingredience", "ingredients",
        "cooking", "vareni", "peceni", "baking",
        "foodie", "recept", "recipe",
        "muffin", "muffins", "muffiny",
        "cupcake", "cupcakes",
        "cookie", "cookies",
        "brownie", "brownies",
        "cake", "buchta", "kolac", "kolace",
        "dort", "dorty", "dessert", "sladke",
        "chorizo", "sundried tomato", "pasta", "creamy", "chicken",
        "vegan", "vegetarian", "vegetariansky",
        "gluten free", "bezlepkovy", "bez lepku",
        "low carb", "keto", "paleo", "whole30",
        "sheet pan", "one pot", "skillet",
        "co varit", "co uvarit", "what to cook",
        "recept na", "recipe for"
    ]
    
    recepty_kontextove = [
        "food", "jidlo", "strava",
        "cooking", "baking"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_recepty_specific = [k for k in recepty_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_recepty_specific:
        if debug:
            print(f"✅ PRAVIDLO 1 AKTIVOVÁNO: Recepty (velmi specifické)")
            print(f"   Matched keywords: {matched_recepty_specific}")
        return "Recepty", matched_recepty_specific
    
    # Kontrola kombinací
    matched_recepty_kombinacni = [k for k in recepty_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_recepty_kontextove = [k for k in recepty_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_recepty_kombinacni) >= 2 or (len(matched_recepty_kombinacni) >= 1 and len(matched_recepty_kontextove) >= 1):
        all_matched_recepty = matched_recepty_kombinacni + matched_recepty_kontextove
        if debug:
            print(f"✅ PRAVIDLO 1 AKTIVOVÁNO: Recepty (kombinace)")
            print(f"   Matched keywords: {all_matched_recepty}")
        return "Recepty", all_matched_recepty

    # PRAVIDLO 2: Oblečení - musí mít alespoň 2 triggery
    clothing_triggers = [
        # ===== ZNAČKY / OBCHODY =====
        "zara", "hm", "h&m", "mango", "reserved", "cos", "uniqlo",
        "nike", "adidas", "puma", "new balance", "vans",
        "decathlon", "columbia", "northface", "patagonia",
        "wheat", "bergam",
        # ===== FASHION KONCEPTY =====
        "capsule wardrobe", "capsule closet",
        "ootd", "try on", "haul", "lookbook",
        "color analysis", "barevna typologie",
        "winter palette", "soft autumn",
        "fit check", "mirror selfie",
        "stylista", "stylist",
        "vyprodej", "sleva",
        # ===== SPECIFICKÉ KOUSKY =====
        "dzinovina", "denim",
        "kardigan", "cardigan",
        "blazer",
        "crop top",
        "crossbody",
        "lodicky", "heels",
        "baleriny", "flats",
        "bunda", "bundy", "jacket",
        "kabat", "coat", "parka",
        "saty", "dress", "dresses",
        "sukne", "skirt",
        "kalhoty", "pants",
        "boty", "shoes",
        # ===== MATERIÁLY =====
        "kasmir", "cashmere",
        "linen", "len",
        "leather", "kozenka", "kuze",
        # ===== KONTEXTOVÉ FRÁZE =====
        "outfit", "outfits",
        "kombinace", "mix and match",
        "trendy", "trend",
        # ===== VELIKOSTI (důležité pro PRAVIDLO 2) =====
        "detska", "detska bunda", "zimnich", "zimnich dnu", 
        "velikost", "size"
    ]
    clothing_hits = sum(1 for k in clothing_triggers if matches_keyword(k, norm_text, tokens))
    if clothing_hits >= 2:
        matched = [k for k in clothing_triggers if matches_keyword(k, norm_text, tokens)]
        if debug:
            print(f"✅ PRAVIDLO 2 AKTIVOVÁNO: Obleceni_Styl (hits={clothing_hits})")
            print(f"   Matched keywords: {matched}")
        return "Obleceni_Styl", matched

    # PRAVIDLO 3: Zahrada - velmi specifické rostliny
    garden_triggers = [
        # ===== VELMI SPECIFICKÉ ROSTLINY =====
        "allium", "giganteum", "ambassador",
        "hydrangea", "hortenzie",
        "erigeron", "karvinskianus",
        "pinus mugo", "mugo",
        "salvia", "purple rain",
        "sesleria", "thymus", "dianthus",
        # ===== ZAHRADNÍ STYLY =====
        "gravel garden", "sterkovy zahon",
        "naturalistic planting", "naturalisticky styl",
        "layered mix", "mix vysadby",
        "structured planting", "kompozice trvalek",
        "coastal garden",
        # ===== OSVĚTLENÍ ZAHRADY =====
        "garden lighting", "osvetleni zahrady", "uplights",
        "zahradni svetla", "osvetleni stromu",
        # ===== SPECIFICKÉ POJMY =====
        "gravel mulch", "sterkovy mulc",
        "container gardening", "potted plants",
        "garden composition",
        "mrazuvzdorne",
        "kapkova zavlaha",
        "garden path", "sterkove cesty",
        "flower bed", "planting border",
        # ===== ZÁKLADNÍ ALE BEZPEČNÉ =====
        "trvalky", "perennials",
        "garden design", "design zahrady",
        "gardening", "gardener", "zahradkar",
        "bylinky", "herbs",
        "sukulent", "succulent",
        "travy", "grasses",
        # ===== AKTIVITY =====
        "pestovani", "growing",
        "vysadba", "planting",
        "pruning",
        "mulching", "mulc",
        # ===== Z TVÝCH PŘÍKLADŮ =====
        "zahradka", "zahon", "pitko", "ptaci",
        "petrazahradnici", "biogarden", "jahody", "rostliny", "oklepavaji"
    ]
    matched_garden = [k for k in garden_triggers if matches_keyword(k, norm_text, tokens)]
    if matched_garden:
        if debug:
            print(f"✅ PRAVIDLO 3 AKTIVOVÁNO: Zahrada")
            print(f"   Matched keywords: {matched_garden}")
        return "Zahrada", matched_garden

    # PRAVIDLO 4: Dum_Design - interiér, architektura, outdoor
    dum_design_triggers = [
        # ===== ARCHITEKTONICKÉ PROJEKTY =====
        "pudorys", "floorplan",
        "pudorys 4kk",
        "vizualizace", "render",
        "rekonstrukce", "renovation",
        "navrh domu", "plan domu",
        "moderni dum", "bungalov",
        
        # ===== NÁBYTKOVÉ OBCHODY =====
        "ikea", "jysk", "kika",
        
        # ===== SPECIFICKÉ STYLY =====
        "scandi", "scandinavian", "nordic",
        "japandi",
        "boho", "bohemian",
        "industrial",
        
        # ===== VELMI SPECIFICKÉ PRVKY =====
        "vestavena skrin", "walk-in closet",
        "satna", "open closet",
        "kuchynsky ostrov", "kitchen island",
        "barove zidle",
        "mikrocement", "terazzo",
        "akusticke panely",
        "lamely", "slat wall", "wood slats",
        "accent wall", "green wall",
        "moodboard",
        
        # ===== OUTDOOR =====
        "pergola", "lamelova pergola",
        "outdoor living", "outdoor seating",
        "baldachyn",
        
        # ===== DĚTSKÝ POKOJ =====
        "detsky pokoj", "kids room",
        "playroom",
        
        # ===== NÁBYTEK =====
        "sedaci souprava", "sofa",
        "vestaveny nabytek",
        "ulozny system", "storage system",
        
        # ===== SPECIFICKÉ MÍSTNOSTI =====
        "home office", "study nook",
        "living working",
        "minimal bedroom", "cozy bedroom",
        "modern hallway", "entry design",
        
        # ===== MATERIÁLY =====
        "parkety", "vinyl flooring",
        "marble", "mramor",
        "obklad", "sterka"
    ]
    matched_dum = [k for k in dum_design_triggers if matches_keyword(k, norm_text, tokens)]
    if matched_dum:
        if debug:
            print(f"✅ PRAVIDLO 4 AKTIVOVÁNO: Dum_Design")
            print(f"   Matched keywords: {matched_dum}")
        return "Dum_Design", matched_dum

    # PRAVIDLO 5: Deti_Aktivity - vyžaduje 2+ triggery NEBO 1 velmi specifický
    deti_aktivity_very_specific = [
        "montessori", "waldorf",
        "sensory bin", "sensory play",
        "busy book", "quiet book",
        "slime", "kinetic sand",
        "play dough", "plastelina",
        "pracovni list", "worksheet",
        "omalovanky", "coloring pages",
        "printable", "sablona",
        "phonics", "alphabet learning", "abeceda",
        "counting activity", "pocitani",
        "toddler activity", "preschool activity",
        "kids craft", "crafts for kids",
        "detske tvoreni"
    ]
    
    deti_aktivity_kombinacni = [
        "craft", "crafting", "tvoreni",
        "vyrabeni", "making", "diy",
        "malovani", "painting",
        "drawing", "kresba",
        "lepeni", "gluing",
        "strihani", "cutting",
        "pastelky", "crayons", "fixy", "markers",
        "origami",
        "kreativita", "creative",
        "aktivita", "activity",
        "trideni", "sorting",
        "experiment"
    ]
    
    deti_aktivity_kontextove = [
        "deti", "kids", "children",
        "detsky", "toddler", "preschool"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_very_specific = [k for k in deti_aktivity_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_very_specific:
        if debug:
            print(f"✅ PRAVIDLO 5 AKTIVOVÁNO: Deti_Aktivity (velmi specifické)")
            print(f"   Matched keywords: {matched_very_specific}")
        return "Deti_Aktivity", matched_very_specific
    
    # Kontrola kombinací
    matched_kombinacni = [k for k in deti_aktivity_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_kontextove = [k for k in deti_aktivity_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_kombinacni) >= 2 or (len(matched_kombinacni) >= 1 and len(matched_kontextove) >= 1):
        all_matched = matched_kombinacni + matched_kontextove
        if debug:
            print(f"✅ PRAVIDLO 5 AKTIVOVÁNO: Deti_Aktivity (kombinace)")
            print(f"   Matched keywords: {all_matched}")
        return "Deti_Aktivity", all_matched

    # PRAVIDLO 6: Vychova_Deti - vyžaduje 2+ triggery NEBO 1 velmi specifický
    vychova_deti_very_specific = [
        "gentle parenting", "respectful parenting", "attachment parenting",
        "positive discipline", "pozitivni vychova",
        "detsky psycholog", "child psychologist",
        "jak vychovavat", "raising children",
        "tantrum", "tantrums",
        "sibling rivalry", "sourozenci zlounost",
        "time out", "time-out",
        "natural consequences", "prirozene dusledky",
        "routine chart", "behavioral chart",
        "screen time limits", "obrazovky deti",
        "spankova hygiena deti",
        "emocni regulace deti",
        "citova vazba", "attachment theory",
        "toddler discipline", "preschooler behavior",
        "parenting tips", "parenting advice",
        "vychovne metody"
    ]
    
    vychova_deti_kombinacni = [
        "vychova", "parenting",
        "rodicovstvi", "parent", "parents",
        "discipline", "disciplina",
        "chovani", "behavior", "behaviour",
        "hranice", "boundaries", "limits", "pravidla",
        "respekt", "respect", "respectful",
        "empatie", "empathy",
        "odmena", "odmeny", "reward", "trest", "punishment",
        "vztek", "anger", "uklidnit", "calming",
        "rozvoj deti", "child development",
        "emocni inteligence",
        "socialni dovednosti",
        "adaptace skolka", "school adaptation",
        "sourozenec", "siblings",
        "navyk", "habit", "rutina", "routine",
        "temperament"
    ]
    
    vychova_deti_kontextove = [
        "deti", "kids", "children", "child",
        "detsky", "toddler", "preschooler",
        "rodicovstvi", "motherhood", "fatherhood"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_vychova_specific = [k for k in vychova_deti_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_vychova_specific:
        if debug:
            print(f"✅ PRAVIDLO 6 AKTIVOVÁNO: Vychova_Deti (velmi specifické)")
            print(f"   Matched keywords: {matched_vychova_specific}")
        return "Vychova_Deti", matched_vychova_specific
    
    # Kontrola kombinací
    matched_vychova_kombinacni = [k for k in vychova_deti_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_vychova_kontextove = [k for k in vychova_deti_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_vychova_kombinacni) >= 2 or (len(matched_vychova_kombinacni) >= 1 and len(matched_vychova_kontextove) >= 1):
        all_matched_vychova = matched_vychova_kombinacni + matched_vychova_kontextove
        if debug:
            print(f"✅ PRAVIDLO 6 AKTIVOVÁNO: Vychova_Deti (kombinace)")
            print(f"   Matched keywords: {all_matched_vychova}")
        return "Vychova_Deti", all_matched_vychova

    # PRAVIDLO 7: Zdraví
    zdravi_very_specific = [
        # ===== MEDICÍNA =====
        "lek", "leky", "medication", "pills",
        "lecba", "treatment", "therapy", "terapie",
        "fyzioterapie", "physiotherapy", "rehab", "rehabilitace",
        "doktor", "doctor", "lekar", "physician", "medical specialist",
        "krevni testy", "blood test", "screening",
        "prevence zraneni", "injury prevention",
        
        # ===== TĚHOTENSTVÍ & POROD =====
        "porod", "po porodu", "postpartum", "after birth",
        "tehotenstvi", "pregnancy", "pregnant", "tehotna",
        "panevni dno", "pelvic floor",
        
        # ===== NEMOCI & PŘÍZNAKY =====
        "horecka", "fever",
        "nachlazeni", "cold", "flu",
        "imunita", "immunity",
        "dermatitida", "akne", "vyrazka", "ekzem", "alergie",
        "zinkova mast", "masticka",
        
        # ===== ZDRAVOTNÍ LÁTKY =====
        "probiotika", "probiotics",
        "omega 3",
        "mikrobiom", "gut health"
    ]
    
    zdravi_kombinacni = [
        "calisthenics", "bodyweight",
        "hiit", "tabata",
        "protahovani", "stretching",
        "cviceni", "workout",
        "rehabilitacni cviceni",
        "vitaminy", "vitamins",
        "supplements", "doplnky",
        "minerals", "mineraly"
    ]
    
    zdravi_kontextove = [
        "zdravi", "health",
        "prevence", "prevention",
        "regenerace", "recovery"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_zdravi_specific = [k for k in zdravi_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_zdravi_specific:
        if debug:
            print(f"✅ PRAVIDLO 7 AKTIVOVÁNO: Zdravi (velmi specifické)")
            print(f"   Matched keywords: {matched_zdravi_specific}")
        return "Zdravi", matched_zdravi_specific
    
    # Kontrola kombinací
    matched_zdravi_kombinacni = [k for k in zdravi_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_zdravi_kontextove = [k for k in zdravi_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_zdravi_kombinacni) >= 2 or (len(matched_zdravi_kombinacni) >= 1 and len(matched_zdravi_kontextove) >= 1):
        all_matched_zdravi = matched_zdravi_kombinacni + matched_zdravi_kontextove
        if debug:
            print(f"✅ PRAVIDLO 7 AKTIVOVÁNO: Zdravi (kombinace)")
            print(f"   Matched keywords: {all_matched_zdravi}")
        return "Zdravi", all_matched_zdravi

    # PRAVIDLO 8: IT_Prace - vyžaduje 2+ triggery NEBO 1 velmi specifický
    it_prace_very_specific = [
        # ===== VELMI SPECIFICKÉ IT NÁSTROJE =====
        "jira", "postman", "swagger", "newman", "bruno api",
        "selenium", "playwright", "cypress", "pytest",
        "gitlab", "github actions", "bitbucket",
        
        # ===== IT KOMUNITY & VZDĚLÁVÁNÍ =====
        "czechitas", "women go tech", "women in tech",
        "engeto", "green fox", "itnetwork",
        "coding bootcamp", "qa academy", "tester akademie",
        "rekvalifikace it", "it rekvalifikace", "kariera v it",
        "skillsbuild", "digitalni certifikat",
        "sladovani kariery s materstvi",
        "career in it", "work in it", "it industry", "it field",
        "tech career", "tech industry",
        
        # ===== KYBERBEZPEČNOST =====
        "kyberbezpecnost", "cyberbezpecnost", "kyberneticka bezpecnost",
        "cybersecurity", "cybersecurity courses",
        "hands on cybersecurity",
        "penetration test", "pentest",
        "phishing", "malware", "ransomware",
        "ethical hacking", "cyber attack",
        "owasp", "vulnerability scan",
        "threat detection", "incident response",
        "soc analyst",
        
        # ===== AI & AUTOMATION =====
        "prompt engineering", "chatgpt", "claude ai", "copilot",
        "machine learning", "deep learning", "neural network",
        "data science", "data analyst",
        "robotic process automation",
        "ai tools", "ai apps", "generative ai",
        "artificial intelligence",
        
        # ===== QA SPECIFIKA =====
        "test case", "test plan", "test scenario",
        "bug report", "bug tracking",
        "regression test", "smoke test", "sanity test",
        "test automation", "api testing",
        "manual testing", "exploratory testing",
        "qa engineer", "qa process", "qa tools"
    ]
    
    it_prace_kombinacni = [
        "junior developer", "junior tester", "junior coder",
        "career switch", "career change",
        "devops", "frontend", "backend", "fullstack",
        "scrum", "agile",
        "pipeline", "deployment",
        "unit test", "integration test",
        "endpoint", "rest api", "soap",
        "pull request", "merge request",
        "code review", "debugging",
        "test environment", "staging", "production"
    ]
    
    it_prace_kontextove = [
        "developer", "tester", "coder",
        "programming", "programovani", "coding",
        "software", "automation", "testing"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_it_specific = [k for k in it_prace_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_it_specific:
        if debug:
            print(f"✅ PRAVIDLO 8 AKTIVOVÁNO: IT_Prace (velmi specifické)")
            print(f"   Matched keywords: {matched_it_specific}")
        return "IT_Prace", matched_it_specific
    
    # Kontrola kombinací
    matched_it_kombinacni = [k for k in it_prace_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_it_kontextove = [k for k in it_prace_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_it_kombinacni) >= 2 or (len(matched_it_kombinacni) >= 1 and len(matched_it_kontextove) >= 1):
        all_matched_it = matched_it_kombinacni + matched_it_kontextove
        if debug:
            print(f"✅ PRAVIDLO 8 AKTIVOVÁNO: IT_Prace (kombinace)")
            print(f"   Matched keywords: {all_matched_it}")
        return "IT_Prace", all_matched_it

    # PRAVIDLO 9: Finance - pouze nejjasnější finanční termíny
    finance_triggers = [
        # ===== ÚČETNICTVÍ & DANĚ =====
        "faktura", "invoice",
        "danove priznani", "tax return",
        "vypis z uctu", "bank statement",
        "uctenka", "receipt",
        
        # ===== INVESTICE =====
        "etf", "dividenda", "dividend",
        "portfolio", "net worth",
        "akcie", "stocks",
        
        # ===== FINANČNÍ PRODUKTY =====
        "hypoteka", "mortgage",
        "penzijko", "penzijni sporeni",
        "stavebko",
        
        # ===== FINANČNÍ PLÁNOVÁNÍ =====
        "nouzovy fond", "emergency fund",
        "fire movement",
        "apr", "rpsn",
        "inflace", "inflation"
    ]
    
    matched_finance = [k for k in finance_triggers if matches_keyword(k, norm_text, tokens)]
    if matched_finance:
        if debug:
            print(f"✅ PRAVIDLO 9 AKTIVOVÁNO: Finance")
            print(f"   Matched keywords: {matched_finance}")
        return "Finance", matched_finance

    # PRAVIDLO 10: Traveling - vyžaduje 2+ triggery NEBO 1 velmi specifický
    traveling_very_specific = [
        # ===== CESTOVATELSKÉ FRÁZE =====
        "kam jet", "kde jet", "where to go", "travel to",
        "must visit", "must see", "top places",
        "bucket list",
        "travel itinerary", "itinerar", "itinerary",
        "roadtrip", "road trip",
        
        # ===== CESTOVATELSKÉ SLUŽBY =====
        "home exchange", "vymena domu", "house swap",
        "airbnb", "booking com",
        "car rental", "pujcovna auta",
        "travel insurance", "cestovni pojisteni",
        "attractions", "tours",
        
        # ===== DOKUMENTY & LETIŠTĚ =====
        "visa", "esta visa", "esta application", "passport",
        "letiste", "airport",
        "flight", "letadlo",
        "border crossing", "checklist cestovani",
        
        # ===== OUTDOOROVÉ CESTOVÁNÍ =====
        "glamping", "vanlife", "campervan",
        "national park", "hiking trail",
        "camping trip"
    ]
    
    traveling_kombinacni = [
        "dovolena", "vacation", "holiday",
        "vylet", "trip", "weekend trip",
        "cestovani", "traveling", "travelling",
        "ubytovani", "accommodation",
        "sightseeing", "pamatka", "monument",
        # ZEMĚ
        "australia", "austria", "belgium",
        "chorvatsko", "croatia",
        "france", "francie",
        "recko", "greece",
        "italie", "italy",
        "nemecko", "germany",
        "polsko", "poland",
        "portugalsko", "portugal",
        "spanelsko", "spain",
        "svycarsko", "switzerland",
        "uk", "england", "london",
        "usa", "canada", "mexico",
        "thajsko", "thailand", "vietnam", "bali",
        "egypt", "maroko", "morocco", "turecko", "turkey"
    ]
    
    traveling_kontextove = [
        "travel", "cestovani",
        "destination", "destinace",
        "trip", "journey"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_traveling_specific = [k for k in traveling_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_traveling_specific:
        if debug:
            print(f"✅ PRAVIDLO 10 AKTIVOVÁNO: Traveling (velmi specifické)")
            print(f"   Matched keywords: {matched_traveling_specific}")
        return "Traveling", matched_traveling_specific
    
    # Kontrola kombinací
    matched_traveling_kombinacni = [k for k in traveling_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_traveling_kontextove = [k for k in traveling_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_traveling_kombinacni) >= 2 or (len(matched_traveling_kombinacni) >= 1 and len(matched_traveling_kontextove) >= 1):
        all_matched_traveling = matched_traveling_kombinacni + matched_traveling_kontextove
        if debug:
            print(f"✅ PRAVIDLO 10 AKTIVOVÁNO: Traveling (kombinace)")
            print(f"   Matched keywords: {all_matched_traveling}")
        return "Traveling", all_matched_traveling

    # PRAVIDLO 11: Deti_Svaciny - vyžaduje 2+ triggery NEBO 1 velmi specifický
    deti_svaciny_very_specific = [
        # ===== SVAČINOVÁ TERMINOLOGIE =====
        "svacina", "svaciny", "svacinek", "svaca",
        "svacinka", "svacinky", "svacinovy", "svacinova",
        "svacina do skolky", "svacina na cestu",
        "zdrava svacina", "zdrava svacina",
        
        # ===== BENTO & LUNCHBOXY =====
        "bento", "bento box",
        "krabickovani", "lunchbox",
        "svacinkovy box", "snack box",
        
        # ===== POUCHES & TYČINKY =====
        "pouch", "kapsicka", "ovocny pouch",
        "tycinka", "tycinky", "granola bar", "energy bar"
    ]
    
    deti_svaciny_kombinacni = [
        "snack", "snacks", "snacking",
        "on the go", "do auta", "na cestu",
        "skolka", "school", "preschool",
        "bez cukru", "sugar free", "no sugar",
        "bez orechu", "nut free",
        "vhodne pro deti", "suitable for kids"
    ]
    
    deti_svaciny_kontextove = [
        "deti", "kids", "children",
        "detsky", "detske",
        "zdrava", "healthy"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_svaciny_specific = [k for k in deti_svaciny_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_svaciny_specific:
        if debug:
            print(f"✅ PRAVIDLO 11 AKTIVOVÁNO: Deti_Svaciny (velmi specifické)")
            print(f"   Matched keywords: {matched_svaciny_specific}")
        return "Deti_Svaciny", matched_svaciny_specific
    
    # Kontrola kombinací
    matched_svaciny_kombinacni = [k for k in deti_svaciny_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_svaciny_kontextove = [k for k in deti_svaciny_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_svaciny_kombinacni) >= 2 or (len(matched_svaciny_kombinacni) >= 1 and len(matched_svaciny_kontextove) >= 1):
        all_matched_svaciny = matched_svaciny_kombinacni + matched_svaciny_kontextove
        if debug:
            print(f"✅ PRAVIDLO 11 AKTIVOVÁNO: Deti_Svaciny (kombinace)")
            print(f"   Matched keywords: {all_matched_svaciny}")
        return "Deti_Svaciny", all_matched_svaciny

    # PRAVIDLO 12: Holidays - vyžaduje 2+ triggery NEBO 1 velmi specifický
    holidays_very_specific = [
        # ===== VÁNOCE =====
        "vanoce", "christmas", "xmas", "vanocni",
        "adventni kalendar", "advent calendar",
        "christmas tree", "vanocni stromek",
        "christmas market", "vanocni trhy",
        "santa claus", "jezisek",
        "wreath", "venec",
        
        # ===== VELIKONOCE =====
        "velikonoce", "easter",
        "kraslice", "easter egg",
        "pomlazka", "egg hunt",
        "malovani vajicek", "easter bunny",
        "easter basket", "easter decoration",
        
        # ===== HALLOWEEN =====
        "halloween",
        "pumpkin carving",
        "trick or treat",
        
        # ===== OSTATNÍ SVÁTKY =====
        "silvestr", "new year's eve", "novy rok",
        "mikulas", "cert", "andel",
        "mother's day", "svatek matek",
        "father's day", "svatek otcu",
        "valentine's day", "valentyn"
    ]
    
    holidays_kombinacni = [
        "advent", "adventni",
        "wrapping", "gift wrap", "baleni darku",
        "holiday decor", "holiday decoration",
        "fireworks", "ohnostroj",
        "new year party",
        "valentine card",
        "pumpkin", "dyne",
        "kostym", "mask"
    ]
    
    holidays_kontextove = [
        "holiday", "holidays", "svatek",
        "celebration", "oslava",
        "tradition", "tradice"
    ]
    
    # Kontrola velmi specifických (stačí 1)
    matched_holidays_specific = [k for k in holidays_very_specific if matches_keyword(k, norm_text, tokens)]
    if matched_holidays_specific:
        if debug:
            print(f"✅ PRAVIDLO 12 AKTIVOVÁNO: Holidays (velmi specifické)")
            print(f"   Matched keywords: {matched_holidays_specific}")
        return "Holidays", matched_holidays_specific
    
    # Kontrola kombinací
    matched_holidays_kombinacni = [k for k in holidays_kombinacni if matches_keyword(k, norm_text, tokens)]
    matched_holidays_kontextove = [k for k in holidays_kontextove if matches_keyword(k, norm_text, tokens)]
    
    # 2+ kombinační NEBO 1 kombinační + 1 kontextové
    if len(matched_holidays_kombinacni) >= 2 or (len(matched_holidays_kombinacni) >= 1 and len(matched_holidays_kontextove) >= 1):
        all_matched_holidays = matched_holidays_kombinacni + matched_holidays_kontextove
        if debug:
            print(f"✅ PRAVIDLO 12 AKTIVOVÁNO: Holidays (kombinace)")
            print(f"   Matched keywords: {all_matched_holidays}")
        return "Holidays", all_matched_holidays

    # ===== KONEC KONTEXTOVÝCH PRAVIDEL =====

    if debug:
        print(f"❌ Žádné kontextové pravidlo nebylo aktivováno")
        print(f"   → Pokračuji do váhového systému\n")

    # Kontext-aware (hračky) - pro případné výjimky v scoringu
    toy_keywords = ["stavebnice", "hracka", "hra", "puzzle", "lego", "vrtacka"]
    has_toy_context = any(normalize_text_simple(k) in tokens for k in toy_keywords)

    # ===== VÁŽOVANÉ BODOVÁNÍ (scoring) =====
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
        # uložíme top matched tokeny (max 5)
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
    
    # ========================================================================
    # VYLEPŠENÍ: Kontrola složky a lepší error handling
    # ========================================================================
    if folder:
        SOURCE = folder
        print(f"📁 Používám zadanou cestu: {SOURCE}")
    else:
        SOURCE = DEFAULT_SOURCE_FOLDER
        print(f"⚠️  POZOR: Používám výchozí cestu!")
        print(f"   {SOURCE}")
        print(f"   💡 Doporučení: Použij --input_dir při spuštění\n")

    # Kontrola existence složky
    if not os.path.exists(SOURCE):
        print(f"\n❌ CHYBA: Složka neexistuje!")
        print(f"   Cesta: {SOURCE}")
        print(f"\n💡 ŘEŠENÍ:")
        print(f"   1. Zkontroluj, že je externí disk připojený")
        print(f"   2. Nebo použij --input_dir s platnou cestou:")
        print(f"      python3 organizer_1.1.py --input_dir \"/tvoje/cesta\"")
        return

    # Kontrola, že je to opravdu složka (ne soubor)
    if not os.path.isdir(SOURCE):
        print(f"\n❌ CHYBA: Cesta není složka!")
        print(f"   Cesta: {SOURCE}")
        return

    all_files = [f for f in os.listdir(SOURCE) if is_image_file(f)]
    total_files = len(all_files)

    if total_files == 0:
        print(f"\n❌ Ve složce nejsou žádné obrázky!")
        print(f"   Cesta: {SOURCE}")
        print(f"\n💡 Podporované formáty: .heic, .jpg, .jpeg, .png")
        return

    # náhodný vzorek nebo prvních N
    if sample and sample > 0:
        if sample >= total_files:
            test_files = all_files[:max_test_files]
        else:
            test_files = random.sample(all_files, min(sample, max_test_files))
    else:
        test_files = all_files[:max_test_files]

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
        default=None,  # ZMĚNA: default=None místo "screenshots"
        help="Cesta ke složce se screenshoty (povinné doporučení)"
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

    # ========================================================================
    # VYLEPŠENÍ: Lepší zprávy a kontrola
    # ========================================================================
    if not input_dir:
        print("\n⚠️  VAROVÁNÍ: Nezadal jsi --input_dir")
        print(f"   Použiji výchozí cestu: {DEFAULT_SOURCE_FOLDER}")
        print(f"\n💡 DOPORUČENÍ: Vždy zadávej cestu:")
        print(f"   python3 organizer_1.1.py --input_dir \"/tvoje/cesta\"\n")
        input_dir = DEFAULT_SOURCE_FOLDER

    # Vyber náhodný vzorek, pokud je --sample zadán
    if os.path.exists(input_dir):
        files = [f for f in os.listdir(input_dir) if is_image_file(f)]
        
        if args.sample:
            print(f"➡️ Použit náhodný vzorek {min(args.sample, len(files))} obrázků ze složky '{input_dir}'\n")
        else:
            print(f"➡️ Zpracovávám všech {len(files)} obrázků ze složky '{input_dir}'\n")
    else:
        print(f"\n❌ Složka neexistuje: {input_dir}")
        print(f"\n💡 Zkontroluj cestu nebo připoj externí disk")
        exit(1)

    # Spuštění dry run testu
    dry_run_test(
        folder=input_dir, 
        sample=args.sample,
        debug=args.debug
    )