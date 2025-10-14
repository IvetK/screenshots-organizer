#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import re
from datetime import datetime
from PIL import Image
import pytesseract
from pillow_heif import register_heif_opener

register_heif_opener()

# NASTAVENÍ
MAX_TEST_FILES = 100
SOURCE_FOLDER = "/Volumes/Elements2023/Screenshot Organizer/screenshots"

# UI PRVKY ZE SOCIÁLNÍCH MÉDIÍ - budou ignorovány při kategorizaci
SOCIAL_MEDIA_UI_KEYWORDS = [
    'follow', 'following', 'followers', 'message', 'messages',
    'post', 'posts', 'posted', 'liked', 'like', 'likes', 'love',
    'share', 'shared', 'comment', 'comments', 'reply', 'replies',
    'notification', 'notifications', 'profile', 'settings',
    'views', 'view', 'subscribers', 'subscribe', 'unsubscribe',
    'dm', 'dms', 'story', 'stories', 'reel', 'reels',
    'live', 'explore', 'discover', 'trending', 'saved',
    'archive', 'highlights', 'highlighted', 'tagged', 'mentions',
    'instagram', 'facebook', 'twitter', 'tiktok', 'youtube',
    'snapchat', 'reddit', 'linkedin', 'whatsapp', 'telegram'
]

# VÁHY SLOV - čím specifičtější, tím vyšší váha
WORD_WEIGHTS = {
    # 10 bodů - VELMI SPECIFICKÉ (unikátní pro kategorii)
    "jira": 10, "postman": 10, "api": 10, "sql": 10, "bug": 10, "qa": 10,
    "selenium": 10, "cypress": 10, "pytest": 10, "docker": 10, "kubernetes": 10,
    "stavebnice": 10, "lego": 10, "puzzle": 10, "plastelína": 10, "plastelina": 10,
    "calisthenics": 10, "hiit": 10, "fyzio": 10, "fyzioterapie": 10,
    "workout": 10, "fitness": 10, "exercise": 10, "training": 10, "gym": 10,
    "cvičení": 10, "cviceni": 10, "yoga": 10, "pilates": 10,
    "lunchbox": 10, "svačinka": 10, "svacinka": 10, "bento": 10,
    "decathlon": 10, "columbia": 10, "northface": 10,
    "faktura": 10, "invoice": 10, "hypotéka": 10, "hypoteka": 10, "etf": 10,
    "rekonstrukce": 10, "půdorys": 10, "pudorys": 10, "floorplan": 10,
    "mulč": 10, "mulc": 10, "hnojivo": 10, "kompost": 10,
    "perennials": 10, "trvalky": 10, "allium": 10, "hydrangea": 10, "hortenzie": 10,
    "gravel garden": 10, "štěrkový záhon": 10, "flower bed": 10,
    "garden lighting": 10, "garden composition": 10, "gardening tips": 10,
    "home exchange": 10, "airbnb": 10,
    
    # 5 bodů - STŘEDNĚ SPECIFICKÉ (hlavní slova kategorie)
    "tester": 5, "testing": 5, "test": 5, "coding": 5, "python": 5, "javascript": 5,
    "craft": 5, "crafting": 5, "vyrábění": 5, "vyrabeni": 5, "malování": 5, "malovani": 5,
    "psycholog": 5, "parenting": 5, "výchova": 5, "vychova": 5, "tantrum": 5,
    "kalhoty": 5, "mikina": 5, "boty": 5, "šaty": 5, "saty": 5, "kabát": 5, "kabat": 5,
    "recept": 5, "recipe": 5, "vaření": 5, "vareni": 5, "pečení": 5, "peceni": 5,
    "zahrada": 5, "garden": 5, "gardening": 5, "záhon": 5, "zahon": 5,
    "pěstování": 5, "pestovani": 5, "rostlina": 5, "plant": 5, "plants": 5,
    "květina": 5, "kvetina": 5, "flower": 5, "flowers": 5,
    "dovolená": 5, "dovolena": 5, "hotel": 5, "letiště": 5, "letiste": 5,
    "podcast": 5, "epizoda": 5, "episode": 5,
    "kniha": 5, "book": 5, "čtení": 5, "cteni": 5, "autor": 5,
    
    # 3 body - OBECNĚJŠÍ (ale relevantní)
    "děti": 3, "deti": 3, "kids": 3, "children": 3,
    "tip": 3, "tipy": 3, "tips": 3, "rada": 3, "rady": 3,
    "healthy": 3, "zdravá": 3, "zdrava": 3,
    "design": 3, "styling": 3, "styl": 3, "style": 3,
    "ovoce": 3, "fruit": 3, "zelenina": 3, "vegetable": 3,
    
    # 1 bod - VELMI OBECNÉ (může být všude)
    "vel.": 1, "velikost": 1, "size": 1, "cm": 1,
    "dobrý": 1, "dobry": 1, "good": 1,
    "nový": 1, "novy": 1, "new": 1,
    "tip": 1, "tipy": 1, "tips": 1,
    "meal": 1, "meals": 1, "plan": 1, "plans": 1,
    "body": 1, "results": 1, "result": 1
}

# KATEGORIE - KOMPLETNÍ KLÍČOVÁ SLOVA
CATEGORIES = {
    "Deti_Aktivity": [
        "svačina", "svacina", "svačiny", "svaciny", "svačinek", "svacinek", "sváča", "svaca",
        "svačinka", "svacinka", "svačinky", "svacinky", "svačinový", "svacinovy", "svačinová", "svacinova",
        "snack", "snacks", "snacking", "mini snack",
        "bento", "krabičkování", "krabickovani", "krabička", "krabicka", "krabičky", "krabicky",
        "box", "lunchbox",
        "cesta", "cesty", "cestou", "trip", "travel", "on the go", "do auta", "auto",
        "děti", "deti", "dětský", "detsky", "dětské", "detske", "kids", "children", "child",
        "vhodná", "vhodne", "vhodné", "suitable", "appropriate",
        "zdravá", "zdrava", "zdravé", "zdrave", "healthy", "health", "nutritious",
        "strava", "food", "jídlo", "jidlo",
        "rychlé", "rychle", "rychlá", "rychla", "quick", "easy", "jednoduchý", "jednoduchy", "jednoduchá", "jednoducha", "fast",
        "výživné", "vyzivne", "výživná", "vyzivna", "nutritious", "nutrition", "nutrient",
        "školka", "skolka", "školky", "skolky", "škola", "skola", "školy", "skoly", "school", "preschool",
        "ovoce", "fruit", "fruits", "ovocné", "ovocne", "apple", "jablko", "jablka", "jablíčka", "jablicka",
        "banán", "banan", "banány", "banany", "banana", "bananas",
        "jahoda", "jahody", "jahůdka", "jahudka", "jahůdky", "jahudky", "strawberry", "strawberries",
        "borůvka", "boruvka", "borůvky", "boruvky", "blueberry", "blueberries",
        "hruška", "hruska", "hrušky", "hrusky", "pear", "pears",
        "zelenina", "vegetable", "veggies", "mrkev", "mrkvička", "mrkvicka", "carrot", "carrots",
        "okurka", "cucumber", "okurky", "cucumbers", "paprika", "paprička", "papricka",
        "sušenka", "susenka", "sušenky", "susenky", "cookie", "cookies", "biscuit", "biscuits",
        "muffin", "muffiny", "muffinek", "cupcake", "cupcakes",
        "tyčinka", "tycinka", "tyčinky", "tycinky", "bar", "bars", "protein bar", "energy bar", "granola", "granola bar",
        "smoothie", "smoothies", "shake", "shakes", "nápoj", "napoj", "nápoje", "napoje", "drink", "drinks", "mixér", "mixer",
        "jogurt", "yogurt", "yoghurt", "tvaroh", "cottage",
        "sýr", "syr", "sýrek", "syrek", "cheese",
        "rohlík", "rohlik", "rohlíky", "rohliky", "bread", "chléb", "chleb", "chlebíček", "chlebicek",
        "sendvič", "sandwich", "wrap", "tortilla",
        "pomazánka", "pomazanka", "pomazánky", "pomazanky", "spread", "hummus",
        "oříšek", "orisek", "oříšky", "orisky", "nut", "nuts", "mandle", "almonds",
        "bez cukru", "sugar free", "no sugar", "low sugar", "naturally sweet",
        "bez ořechů", "bez orechu", "nut free",
        "pouch", "kapsička", "kapsicka",
        "recept", "recipe", "recepty", "recipes"
    ],
    "Deti_Aktivity": [
        "craft", "crafting", "crafts", "tvoření", "tvoreni",
        "vyrábění", "vyrabeni", "making", "diy", "handmade",
        "děti", "deti", "kids", "children", "child",
        "obrázek", "obrazek", "obrázky", "obrazky", "picture", "drawing",
        "malování", "malovani", "painting", "paint", "coloring",
        "barvy", "colors", "pastelky", "crayons", "fixy", "markers",
        "hry", "hra", "game", "games", "playing", "play",
        "aktivita", "aktivity", "activity", "activities",
        "papír", "papir", "paper", "cardboard", "karton",
        "lepení", "lepeni", "gluing", "glue", "lepidlo",
        "nůžky", "nuzky", "scissors", "stříhání", "strihani", "cutting",
        "origami", "plastelína", "plastelina", "playdough",
        "kreativita", "creativity", "creative", "tvořivost", "tvorivost",
        "montessori", "waldorf", "sensory",
        "worksheet", "pracovní list", "pracovni list", "printable",
        "omalovánky", "omalovanky", "coloring pages",
        "template", "šablona", "sablona", "tracing",
        "fine motor", "gross motor", "motorika",
        "třídění", "trideni", "sorting",
        "počítání", "pocitani", "counting",
        "abeceda", "alphabet", "phonics",
        "experiment", "science", "STEAM", "STEM",
        "slime", "sensory bin", "busy book"
    ],
    "Vychova_Deti": [
        "výchova", "vychova", "parenting", "parent", "parents", "rodičovství", "rodicovstvi",
        "děti", "deti", "kid", "kids", "children", "child",
        "psycholog", "psychologist", "dětský psycholog", "detsky psycholog",
        "tip", "tipy", "tips", "rada", "rady", "advice", "how to",
        "jak vychovávat", "jak vychovavat", "raising", "bringing up",
        "uklidnit", "calm", "calming", "tantrum", "vztek", "anger",
        "rozvoj", "development", "rozvíjet", "rozvijet", "develop",
        "emoce", "emotions", "emotional", "citová", "citova", "emoční", "emocni",
        "chování", "chovani", "behavior", "behaviour", "discipline", "disciplína", "disciplina",
        "komunikace", "communication", "mluvení", "mluveni", "talking",
        "hranice", "boundaries", "limits", "pravidla", "rules",
        "sourozenec", "sourozenecký", "sourozenci", "sibling", "siblings",
        "školka", "skolka", "škola", "skola", "school", "preschool", "adaptation",
        "spánek", "spanek", "sleep", "sleeping", "routine", "rutina",
        "montessori", "waldorf", "pedagogika", "education",
        "respekt", "respect", "respectful", "gentle", "empatie", "empathy",
        "attachment", "citová vazba", "citova vazba", "gentle parenting", "respectful parenting",
        "time out", "natural consequences", "přirozené důsledky", "prirozene dusledky",
        "odměna", "odmena", "odměny", "odmeny", "trest",
        "screen time", "obrazovky", "spánková hygiena", "spankova hygiena",
        "routine chart", "navyk", "habit", "temperament",
        "emoční regulace", "emocni regulace", "adhd", "autismus"
    ],
    "IT_Prace": [
        # 🧠 Obecné / kariéra / komunita
        "it", "ajťák", "ajtak", "ajťačka", "ajtacka", "holky v it", "zeny v it", "ženy v it",
        "women in tech", "women go tech", "womenwhocode", "girls who code",
        "female engineer", "female developer", "dev girl", "coder girl", "tech girl",
        "career switch", "career pivot", "career in tech", "tech career", "techlife", "work in tech",
        "digital skills", "digitální dovednosti", "digitalni dovednosti",
        "it svět", "it svet", "it kariera", "kariera v it", "rekvalifikace it",
        "junior tester", "junior developer", "junior coder",
        "tech recruiter", "it recruiter", "linkedin", "cv", "resume", "portfolio", "career tips",
        "self learning", "learning tech", "bootcamp", "coding bootcamp", "tech course",
        "kurz it", "it kurz", "mentor", "mentoring", "internship", "stáž", "staz",
        "pracovní prostředí", "pracovni prostredi", "remote job", "hybrid work", "wfh", "work from home",
        
        # 🔐 Kyberbezpečnost / hacking / data protection
        "cyberbezpečnost", "kyberbezpečnost", "kybernetická bezpečnost", "kyberneticka bezpecnost",
        "data security", "data breach", "hacking", "hack", "hacker", "ethical hacking",
        "penetration test", "pentest", "malware", "phishing", "spoofing",
        "encryption", "hashing", "cyber attack", "cybercrime", "cyber defense",
        "threat", "threat detection", "vulnerability", "zero day", "incident", "incident response",
        "forensics", "SOC", "CVE", "OWASP", "firewall", "VPN",
        "password manager", "password hygiene", "2FA", "MFA", "two factor authentication",
        "data leak", "privacy", "GDPR", "personal data", "information security", "infosec",
        "cyber awareness", "security awareness", "security training", "phishing email",
        "data loss prevention", "dark web", "cyber hygiene",
        
        # 🤖 Umělá inteligence / automatizace / data
        "machine learning", "deep learning", "neural network", "neuronová síť", "neuronova sit",
        "data science", "data analyst", "data analysis", "datová analýza", "datova analyza",
        "visualization", "vizualizace dat", "big data", "analytics",
        "prompt engineering", "prompting", "prompt", "ai tools", "ai apps",
        "gen ai", "generativní ai", "generativni ai", "chatbot", "bot",
        "automation engineer", "automate", "automating", "robot", "rpa",
        "robotic process automation", "macro", "script", "scripting", "workflow automation",
        "zapier", "make com", "integromat", "integration", "power automate",
        "no code", "low code", "nocode", "lowcode",
        
        # 💡 Programování / vývoj / nástroje
        "developer life", "devlife", "debug", "debugging",
        "frontend", "backend", "fullstack", "cloud", "aws", "azure", "gcp", "google cloud",
        "cloud computing", "microservices", "api testing", "post request", "get request",
        "automation test", "qa engineer", "test engineer", "unit testing", "mock data",
        "json schema", "data validation", "api docs", "env variables",
        "gitlab", "bitbucket", "merge", "branch", "pull request", "commit message",
        "version control", "ci pipeline", "build", "deploy", "deployment", "release",
        "devops", "sre", "infrastructure", "monitoring", "logging", "debug logs",
        "terminal", "console", "command line", "bash", "shell",
        "python script", "nodejs", "typescript", "reactjs", "nextjs", "vuejs",
        "django", "flask", "fastapi", "express", "npm", "yarn", "package", "dependency",
        "virtualenv", "venv",
        
        # 🧩 QA / Testování (původní + doplnění)
        "qa", "quality assurance", "tester", "testing", "test",
        "bug", "issue", "defect", "chyba",
        "jira", "confluence", "agile", "scrum", "sprint",
        "postman", "api", "endpoint", "request", "response",
        "sql", "database", "databáze", "databaze", "query", "dotaz",
        "cybersecurity", "security", "bezpečnost", "bezpecnost", "cyber",
        "změna profese", "zmena profese", "career change", "rekvalifikace", "retraining",
        "ai", "artificial intelligence", "umělá inteligence", "umela inteligence",
        "chatgpt", "gpt", "claude", "copilot", "gemini",
        "czechitas", "coding", "programování", "programovani",
        "python", "javascript", "html", "css", "react", "code",
        "github", "git", "repository", "commit",
        "cursor", "notion", "notes", "dokumentace", "documentation",
        "web", "website", "app", "application", "developer", "dev",
        "automation", "automatizace", "jenkins", "ci/cd", "ci", "cd",
        "selenium", "playwright", "cypress", "pytest",
        "unit test", "integration test", "regression",
        "test case", "test plan", "bug report", "severity", "priority",
        "swagger", "openapi", "json", "yaml", "http", "rest", "soap",
        "oauth", "jwt", "token",
        "docker", "kubernetes", "pipeline", "newman", "bruno",
        "xpath", "selector", "postgres", "mysql", "sqlite",
        "smoke test", "sanity test", "test automation", "test scenario", "test data",
        "assert", "assertion", "expected result", "repro steps", "bug tracking",
        "ticket", "story", "task", "epic", "test report", "test summary",
        "qa process", "qa tools", "qa team", "qa workflow", "test documentation",
        "manual testing", "exploratory testing", "test environment", "staging", "production",
        "environment variables", "postman collection", "bruno api", "swagger ui",
        
        # 🌐 IT kultura / inspirace / učení
        "learn to code", "study tech", "it blog", "tech blog", "it meme", "tech meme",
        "it humor", "code humor", "programming meme", "debug life", "commit joke",
        "tech inspiration", "productivity", "time blocking", "notion template", "learning plan",
        "studygram", "study motivation", "career growth", "skill development",
        "upskill", "reskill", "learn python", "learn sql", "learn testing", "learn automation",
        "self-taught", "autodidact", "growth mindset", "learning path",
        
        # 👩‍💻 České komunity, projekty, vzdělávání
        "engeto", "green fox", "coding bootcamp prague", "mentee",
        "it kurz", "online kurz", "vzdělávání", "vzdelavani",
        "kurzy programovani", "kurzy testovani", "tester akademie",
        "banking app project", "czechi bank", "qa academy",
        "manual testing course", "cybersecurity certificate", "google certificate",
        "future skills", "digitální akademie", "digitalni akademie"
    ],
    "Finance": [
        "faktura", "faktury", "invoice", "invoices",
        "peníze", "penize", "money", "cash", "finance", "financial",
        "rozpočet", "rozpocet", "budget", "budgeting",
        "účet", "ucet", "account", "bank", "banka", "banking",
        "platba", "payment", "transakce", "transaction",
        "úspora", "uspora", "úspory", "uspory", "savings", "saving",
        "daň", "dan", "daně", "dane", "tax", "taxes", "daňové", "danove",
        "pojištění", "pojisteni", "insurance",
        "smlouva", "contract", "agreement",
        "investice", "investment", "investing", "invest",
        "půjčka", "pujcka", "loan", "credit", "úvěr", "uver",
        "hypotéka", "hypoteka", "mortgage",
        "účtenka", "uctenka", "receipt", "doklad",
        "náklad", "naklad", "náklady", "naklady", "expense", "expenses", "cost",
        "příjem", "prijem", "příjmy", "prijmy", "income", "revenue",
        "dluh", "debt", "závazek", "zavazek",
        "výpis", "vypis", "statement", "cashflow", "net worth", "portfolio",
        "etf", "fond", "mutual fund", "index",
        "dividenda", "inflace", "kurz", "měna", "mena", "exchange rate",
        "spoření", "sporeni", "stavebko", "penzijko", "penzijní", "penzijni",
        "úrok", "urok", "sazba", "APR", "RPSN",
        "rezerva", "nouzový fond", "nouzovy fond"
    ],
    "Zdravi": [
        "zdraví", "zdravi", "health", "healthy", "wellness",
        "rada", "rady", "tip", "tipy", "advice", "doporučení", "doporuceni",
        "lék", "lek", "léky", "leky", "medicine", "medication", "pills",
        "léčba", "lecba", "treatment", "therapy", "terapie",
        "léčivý", "lecivy", "healing", "remedy", "postup", "procedure",
        "cvičení", "cviceni", "exercise", "workout", "fitness", "training",
        "calisthenics", "bodyweight", "hiit", "tabata",
        "fyzio", "fyzioterapie", "physiotherapy", "physio", "rehab", "rehabilitace",
        "porod", "po porodu", "postpartum", "after birth", "pregnancy",
        "těhotenství", "tehotenstvi", "pregnant", "těhotná", "tehotna",
        "pánevní", "panevni", "pelvic", "floor", "dno",
        "doktor", "doctor", "lékař", "lekar", "physician", "specialist",
        "bolest", "pain", "ache", "záda", "zada", "back", "klouby", "joints",
        "prevence", "prevention", "preventive", "screening",
        "jóga", "yoga", "pilates", "stretching", "protahování", "protahovani",
        "gym", "posilovna", "strength", "síla", "sila",
        "výživa", "vyziva", "nutrition", "strava", "diet",
        "vitamíny", "vitaminy", "vitamins", "supplements", "doplňky", "doplnky",
        "spánek", "spanek", "sleep", "recovery", "regenerace",
        "mentální", "mentalni", "mental health", "psycholog", "wellbeing",
        "imunita", "immunity", "nachlazení", "nachlazeni",
        "mikrobiom", "gut", "střevo", "strevo", "probiotika", "omega 3",
        "minerály", "minerals", "krevní testy", "krevni testy",
        "kardio", "běh", "beh", "running", "kroky", "steps",
        "horečka", "horecka", "prevence zranění", "prevence zraneni",
        "zhubnout", "hubnutí", "hubnuti", "lose weight", "weight loss",
        "kila", "kilo", "kg", "pounds", "lbs", "váha", "vaha"
    ],
    "Dum_Design": [
        "stavba", "building", "výstavba", "vystavba", "novostavba",
        "rekonstrukce", "renovation", "přestavba", "prestavba", "rekonštrukce",
        "dům", "dum", "house", "home", "byt", "flat", "apartment",
        "vybavení", "vybaveni", "equipment", "furnishing",
        "nábytek", "nabytek", "furniture", "ikea", "jysk", "kika",
        "osvětlení", "osvetleni", "lighting", "light", "světlo", "svetlo", "lampa", "lamp",
        "obraz", "obrazy", "picture", "art", "wall art",
        "dekorace", "decoration", "decor", "deko", "výzdoba", "vyzdoba",
        "styling", "style", "design", "interior", "interiér", "interier",
        "scandi", "scandinavian", "nordic", "minimalist", "minimalistický", "minimalisticky",
        "barvy", "colors", "paint", "malování", "malovani",
        "podlaha", "floor", "flooring", "dlažba", "dlazba", "parkety",
        "kuchyň", "kuchyn", "kitchen", "koupelna", "bathroom",
        "obývák", "obyvak", "living room", "ložnice", "loznice", "bedroom",
        "moodboard", "vizualizace", "render", "skica",
        "půdorys", "pudorys", "floorplan", "dispozice",
        "obklad", "stěrka", "sterka", "mikrocement", "beton",
        "akustika", "akustické panely", "akusticke panely",
        "závěsy", "zavesy", "záclony", "zaclony", "rolety", "žaluzie", "zaluzie",
        "pergola", "půdorys 4kk", "kuchyňská linka", "kuchynska linka"
    ],
    "Zahrada": [
        # 🌸 1. Rostliny a druhy
        "rostlina", "plant", "plants", "květina", "kvetina", "flower", "flowers", "kytka",
        "trvalky", "perennials", "zelenina", "vegetable", "vegetables", "veggie",
        "ovoce", "fruit", "jahody", "maliny", "berries",
        "bylinky", "herbs", "sukulent", "succulent", "kaktus", "cactus",
        "allium", "okrasný česnek", "ornamental onion", "giganteum", "ambassador",
        "pinball wizard", "white giant", "green craze",
        "hydrangea", "hortenzie", "erigeron", "karvinskianus",
        "pinus mugo", "mugo", "borovice", "salvia", "sage", "purple rain",
        "sesleria", "thymus", "thyme", "dianthus", "karafiát", "aster", "asters",
        "trávy", "traviny", "grasses", "keř", "shrubs", "strom", "trees",
        
        # 🌿 2. Výsadba, záhony a styl
        "záhon", "zahon", "bed", "flower bed", "výsadba", "vysadba",
        "přesazení", "presazeni", "pěstování", "pestovani", "growing",
        "gravel garden", "štěrkový záhon", "dry garden", "suchý záhon",
        "layered mix", "mix výsadby", "border", "planting border",
        "small garden", "malá zahrada", "naturalistický styl", "naturalistic planting",
        "modern garden", "moderní zahrada", "coastal garden", "pobřežní zahrada",
        "structured planting", "kompozice trvalek",
        
        # 🌼 3. Kvetení a sezónnost
        "spring bloom", "summer bloom", "autumn colour", "winter texture",
        "dlouhé kvetení", "long flowering", "seasonal interest",
        "celoroční efekt", "continuous bloom",
        
        # 🪴 4. Nádoby a pěstování v květináčích
        "pots", "planters", "květináče", "venkovní květináče",
        "potted plants", "container gardening", "borders", "výsadba do záhonu",
        "gravel mulch", "štěrkový mulč",
        
        # 🌾 5. Povrchy, materiály a cesty
        "limestone", "vápencový kámen", "chippings", "štěrkové cesty",
        "pavers", "dlaždice", "paving", "chodník",
        "neutral tones", "natural stone", "pathway", "garden path",
        "mulč", "mulc", "mulching",
        
        # 💡 6. Osvětlení a atmosféra
        "garden lighting", "osvětlení zahrady", "uplights", "zahradní světla",
        "focal point", "osvětlení stromů", "highlight plants",
        "evening garden", "ambient lighting", "noční zahrada",
        
        # 🌱 7. Design, kompozice a plánování
        "plánování", "planovani", "planning", "design zahrady", "layout",
        "garden composition", "výsadba vrstvení", "focal point", "accent plant",
        "textura", "texture contrast", "colour harmony", "barevná kompozice",
        "design", "garden design", "gardening", "zahrada", "zahrádka", "zahradka",
        "zahrádkář", "zahradkar", "gardener", "gardening tips",
        
        # 💧 8. Péče o rostliny
        "hnojivo", "hnojiva", "fertilizer", "kompost", "compost",
        "škůdce", "škůdci", "skudce", "skudci", "pest", "pests",
        "zalévání", "zalevani", "watering", "water",
        "kapková závlaha", "kapkova zavlaha",
        "pruning", "řez", "rez", "střih", "strih",
        "USDA zone", "mrazuvzdorné", "mrazuvzdorne", "zimování", "zimovani",
        
        # 🏡 9. Prostory kolem domu
        "terasa", "terrace", "patio", "balkon", "balcony",
        "trávník", "travnik", "lawn", "grass", "posečení", "poseceni", "mowing",
        "bazén", "pool", "pool cover",
        
        # Původní slova (zachováno)
        "rada", "rady", "tip", "tipy", "advice", "tutorial",
        "aranžmá", "aranzma", "arrangement", "vazba", "bouquet",
        "pokojová", "pokojove", "indoor", "houseplant", "house plant",
        "nástroje", "nastroje", "zahradní nůžky", "zahradni nuzky"
    ],
    "Traveling": [
        "místo", "misto", "place", "places", "destination", "destinace",
        "geografie", "geography", "mapa", "map", "maps",
        "tip", "tipy", "tips", "doporučení", "doporuceni", "recommendation",
        "kam jet", "kde jet", "where to go", "travel to",
        "dovolená", "dovolena", "vacation", "holiday", "holidays",
        "výlet", "vylet", "trip", "excursion", "day trip", "weekend trip",
        "cestování", "cestovani", "travel", "traveling", "travelling",
        "home exchange", "výměna domů", "vymena domu", "house swap",
        "registrace", "registration", "profil", "profile",
        "děti", "deti", "kids", "children", "family", "rodina", "rodinná", "rodinna",
        "pláž", "plaz", "beach", "beaches", "moře", "more", "sea", "ocean",
        "hory", "mountains", "hiking", "trek", "wandering",
        "město", "mesto", "city", "cities", "town", "village", "vesnice",
        "hotel", "hotels", "ubytování", "ubytovani", "accommodation", "airbnb", "booking",
        "restaurace", "restaurant", "café", "kavárna", "kavarna", "bistro",
        "atrakce", "attraction", "památka", "pamatka", "monument", "sightseeing",
        "itinerary", "itinerář", "itinerar", "plán", "plan", "route", "trasa",
        "letiště", "letiste", "airport", "let", "flight", "letadlo", "plane",
        "vlak", "train", "autobus", "bus", "metro", "subway",
        "bucket list", "must see", "must visit", "top places",
        "austrálie", "australia", "rakousko", "austria", "belgie", "belgium",
        "česko", "cesko", "czech", "chorvatsko", "croatia",
        "francie", "france", "řecko", "recko", "greece", "itálie", "italie", "italy",
        "německo", "nemecko", "germany", "polsko", "poland", "portugalsko", "portugal",
        "španělsko", "spanelsko", "spain", "švýcarsko", "svycarsko", "switzerland",
        "velká británie", "velka britanie", "uk", "england", "london",
        "usa", "america", "kanada", "canada", "mexiko", "mexico",
        "thajsko", "thailand", "vietnam", "bali", "indonésie", "indonesie",
        "egypt", "maroko", "morocco", "turecko", "turkey",
        "roadtrip", "camping", "kemp", "glamping", "vanlife",
        "national park", "NP", "trail", "hiking trail",
        "itinerary kids", "playground", "pumptrack",
        "car rental", "půjčovna auta", "pujcovna auta",
        "travel insurance", "cestovní pojištění", "cestovni pojisteni",
        "visa", "ESTA", "border", "checklist"
    ],
    "Recepty": [
        "recept", "recepty", "recipe", "recipes",
        "snídaně", "snidane", "breakfast", "brunch", "ráno", "rano", "morning",
        "oběd", "obed", "lunch", "poledne",
        "večeře", "vecere", "dinner", "večer", "vecer", "evening",
        "co vařit", "co varit", "what to cook", "co uvařit", "co uvarit",
        "jídlo", "jidlo", "food", "meal", "dish", "pokrm",
        "vaření", "vareni", "cooking", "cook", "cooked",
        "pečení", "peceni", "baking", "bake", "baked", "peču", "pecu", "pekla",
        "dezert", "dessert", "sladké", "sladke", "sweet", "cake", "cakes", "dort", "dorty", "koláč", "kolac", "kolace",
        "muffin", "muffins", "muffiny", "cupcake", "cupcakes",
        "cookie", "cookies", "brownie", "brownies", "pie", "pies",
        "zdravá", "zdrava", "healthy", "health",
        "rychlé", "rychle", "quick", "easy", "jednoduchý", "jednoduchy", "fast",
        "výživné", "vyzivne", "nutritious", "nutrition",
        "strava", "diet", "jídelníček", "jidelnicek", "menu", "meal prep",
        "protein", "proteinový", "proteinovy", "white", "maso", "meat", "chicken", "beef", "pork", "fish",
        "butter", "máslo", "maslo", "flour", "mouka", "sugar", "cukr",
        "salt", "sůl", "sul", "pepper", "pepř", "pepr",
        "oil", "olej", "olive", "olivový", "olivovy",
        "sauce", "omáčka", "omacka", "gravy", "dressing",
        "melt", "heat", "whisk", "mix", "stir", "blend",
        "add", "přidat", "pridat", "pour", "nalít", "nalit",
        "chop", "nakrájet", "nakrajet", "slice", "dice",
        "ingredient", "ingredients", "ingredience", "složení", "slozeni",
        "instructions", "postup", "directions", "step", "krok",
        "ovoce", "fruit", "fruits", "jablko", "apple", "apples",
        "banán", "banan", "banány", "banany", "banana", "bananas",
        "jahoda", "jahody", "strawberry", "strawberries",
        "malina", "maliny", "raspberry", "raspberries",
        "borůvka", "boruvka", "borůvky", "boruvky", "blueberry", "blueberries",
        "pomeranč", "pomeranc", "orange", "oranges", "citron", "lemon",
        "hruška", "hruska", "hrušky", "hrusky", "pear", "pears",
        "broskev", "broskve", "peach", "peaches",
        "zelenina", "vegetable", "vegetables", "veggie", "veggies",
        "rajče", "rajce", "rajčata", "rajcata", "tomato", "tomatoes",
        "okurka", "cucumber", "cucumbers",
        "paprika", "pepper", "peppers", "bell pepper",
        "mrkev", "carrot", "carrots",
        "cibule", "onion", "onions", "česnek", "cesnek", "garlic",
        "brokolice", "broccoli", "květák", "kvetak", "cauliflower",
        "špenát", "spenat", "spinach", "salát", "salat", "lettuce",
        "cuketa", "zucchini", "courgette",
        "vegan", "vegetarian", "vegetariánský", "vegetariansky",
        "bezlepkový", "bezlepkovy", "gluten free", "bez lepku",
        "polévka", "polevka", "soup", "soups", "salát", "salat", "salad", "salads",
        "pasta", "těstoviny", "testoviny", "spaghetti", "penne",
        "rýže", "ryze", "rice", "quinoa", "bulgur",
        "instant pot", "air fryer", "airfryer", "thermomix", "multicooker",
        "mealplan", "jídelní plán", "jidelni plan",
        "low carb", "keto", "paleo", "whole30", "macro",
        "kalorie", "calories", "high protein", "bez cukru", "no sugar",
        "skillet", "one pot", "sheet pan"
    ],
    "Obleceni_Styl": [
        "oblečení", "obleceni", "outfit", "outfits", "clothes", "clothing", "wear",
        "styl", "style", "styling", "fashion", "móda", "moda",
        "tip", "tipy", "tips", "inspiration", "inspirace",
        "jak se oblékat", "jak se oblkat", "how to wear", "how to dress",
        "trendy", "trend", "trends", "lookbook", "look",
        "kombinace", "combination", "pairing", "mix and match",
        "kalhoty", "pants", "trousers", "rifle", "jeans", "džíny", "dziny",
        "legíny", "leginy", "leggings", "tepláky", "teplaky", "sweatpants", "joggers",
        "kraťasy", "kratasy", "shorts", "bermudy", "bermuda",
        "outdoor", "outdoorové", "outdoorove", "outdorové", "outdorove", "sportovní", "sportovni", "sport",
        "mikina", "hoodie", "hoody", "sweatshirt", "fleece", "flís", "flis",
        "svetr", "sweater", "pullover", "kardigan", "cardigan",
        "tričko", "tricko", "tshirt", "t-shirt", "top", "crop top",
        "košile", "kosile", "shirt", "blouse", "blůza", "bluza",
        "boty", "shoes", "boots", "sneakers", "tenisky", "botky",
        "sandály", "sandaly", "sandals", "žabky", "zabky", "flip flops",
        "baleríny", "baleriny", "flats", "lodičky", "lodicky", "heels",
        "šaty", "saty", "dress", "dresses", "šatičky", "saticky",
        "sukně", "sukne", "skirt", "skirts",
        "kabát", "kabat", "coat", "jacket", "bunda", "bundy", "parka",
        "sako", "blazer", "vesta", "vest", "gilet",
        "kabelka", "bag", "handbag", "purse", "taška", "taska",
        "batoh", "backpack", "ruksak", "crossbody",
        "doplňky", "doplnky", "accessories", "jewelry", "šperky", "sperky",
        "náhrdelník", "nahrdelnik", "necklace", "náušnice", "nausnice", "earrings",
        "šátek", "satek", "scarf", "čepice", "cepice", "hat", "cap",
        "pásek", "pasek", "belt", "hodinky", "watch",
        "materiál", "material", "bavlna", "cotton", "polyester",
        "vlna", "wool", "kašmír", "kasmir", "cashmere",
        "len", "linen", "džínovina", "dzinovina", "denim",
        "koženka", "leather", "kůže", "kuze",
        "vel.", "velikost", "size", "sizes", "cm",
        "barvy", "colors", "colour", "odstín", "odstin",
        "černá", "cerna", "black", "bílá", "bila", "white",
        "šedá", "seda", "grey", "gray", "modrá", "modra", "blue",
        "červená", "cervena", "red", "zelená", "zelena", "green",
        "zara", "hm", "h&m", "mango", "reserved", "cos", "uniqlo",
        "nike", "adidas", "puma", "new balance", "vans",
        "decathlon", "columbia", "northface", "patagonia",
        "capsule wardrobe", "minimalist", "versatile", "basic", "essentials",
        "OOTD", "try on", "haul",
        "color analysis", "barevná typologie", "barevna typologie",
        "winter palette", "soft autumn", "stylista", "stylist",
        "fit check", "mirror selfie", "capsule closet"
    ],
    "Fotografie_Tips": [
        "fotografie", "photography", "photo", "photos", "fotky",
        "tip", "tipy", "tips", "tutorial", "návod", "navod",
        "setup", "set up", "nastavení", "nastaveni",
        "rodinné", "rodinne", "family", "portrait", "portrét", "portret",
        "světlo", "svetlo", "light", "lighting", "osvětlení", "osvetleni",
        "kompozice", "composition", "framing",
        "pozadí", "pozadi", "background", "backdrop",
        "póza", "poza", "pose", "posing",
        "úprava", "uprava", "editing", "edit", "retouch",
        "filtr", "filter", "preset",
        "mobilní", "mobilni", "phone", "iphone", "smartphone",
        "camera", "fotoaparát", "fotoaparat", "objektiv", "lens",
        "instagram", "instagrammable",
        "exposure", "ISO", "shutter", "aperture",
        "rule of thirds", "bokeh", "depth of field",
        "RAW", "Lightroom", "color grading",
        "white balance", "WB", "histogram",
        "prime lens", "wide angle", "macro",
        "golden hour", "blue hour", "backlight", "HDR"
    ],
    "Knihy_Cetba": [
        "kniha", "knihy", "book", "books", "čtení", "cteni", "reading",
        "román", "roman", "novel", "fiction",
        "recenze", "review", "doporučení", "doporuceni", "recommendation",
        "autor", "author", "writer", "spisovatel",
        "bestseller", "best seller", "oblíbené", "oblibene",
        "žánr", "zanr", "genre", "thriller", "fantasy", "sci-fi",
        "audiokniha", "audiobook", "podcast kniha",
        "e-book", "ebook", "kindle",
        "knihovna", "library", "půjčovna", "pujcovna",
        "čtenářský", "ctenarsky", "book club", "literární", "literarni",
        "tip", "tipy", "tips", "must read",
        "top 10", "seznam", "list",
        "reading list", "TBR", "goodreads",
        "nonfiction", "biografie", "memoár", "memoar",
        "dětská kniha", "detska kniha", "quote from book"
    ],
    "Podcast": [
        "podcast", "podcasts", "podcasty",
        "tip", "tipy", "tips", "doporučení", "doporuceni", "recommendation",
        "poslech", "listening", "audio",
        "epizoda", "episode", "díl", "dil",
        "host", "moderátor", "moderator", "hosté", "hoste", "guest",
        "spotify", "apple podcast", "youtube",
        "oblíbené", "oblibene", "favorite", "favourite",
        "téma", "tema", "topic", "subject",
        "rozhovor", "interview", "talk", "discussion",
        "séria", "seria", "series", "show",
        "top", "best", "must listen",
        "show notes", "timestamps", "episode notes",
        "poslech na cestu", "podcast tip"
    ],
    "Christmas_Holidays": [
        "christmas", "vánoce", "vanoce", "xmas", "vánoční", "vanocni",
        "dekorace", "decoration", "decor", "výzdoba", "vyzdoba", "decorating",
        "stromek", "tree", "christmas tree", "jedle",
        "ozdoba", "ornament", "ornaments", "baňka", "banka", "bauble",
        "advent", "adventní", "adventni", "calendar", "kalendář", "kalendar",
        "adventní kalendář", "adventni kalendar", "věnec", "venec", "wreath",
        "cukroví", "cukrovi", "cookies", "baking", "perníček", "pernicek", "gingerbread",
        "dárek", "darek", "gift", "gifts", "present",
        "oslava", "celebration", "party",
        "silvestr", "new year", "nový rok", "novy rok",
        "easter", "velikonoce", "valentýn", "valentyn", "valentine",
        "halloween", "holiday", "holidays", "prázdniny", "prazdniny",
        "betlém", "betlem", "vánoční trhy", "vanocni trhy",
        "wrapping", "balení dárků", "baleni darku", "gift wrap",
        "wishlist", "světýlka", "svetylka", "koledy",
        "mikuláš", "mikulas"
    ],
    "Citaty_Moudra": [
        "citát", "citat", "quote", "quotes",
        "moudro", "wisdom", "inspirace", "inspiration",
        "motivace", "motivation", "motivational",
        "myšlenka", "myslenka", "thought", "thoughts",
        "život", "zivot", "life", "living",
        "vztah", "relationship", "láska", "laska", "love",
        "manželství", "manzelstvi", "marriage", "partner", "partnerství", "partnerstvi",
        "filozofie", "philosophy", "philosophical",
        "slova", "words", "saying", "proverb",
        "mindfulness", "mindset", "vědomí", "vedomi",
        "pozitivita", "positive", "happiness", "štěstí", "stesti",
        "rodina", "family", "rodinný", "rodinny",
        "affirmation", "afirmace", "mantra",
        "stoic", "stoicism", "seneca", "epiktetos", "epictetus",
        "life lesson", "growth mindset"
    ],
    "Rodina": [
        "rodina", "family", "maia", "maya", "oli", "oliver", "oliverek",
        "babi", "babička", "babicka", "děda", "deda", "dedecek",
        "dovolená", "dovolena", "vacation", "holiday", "holidays",
        "oslava", "narozeniny", "birthday", "party", "celebration",
        "výlet", "vylet", "trip", "excursion",
        "pláž", "plaz", "beach", "moře", "more",
        "bazén", "bazen", "pool", "swimming",
        "maminka", "mama", "mum", "mom", "tatínek", "tata", "dad",
        "děti", "deti", "kids", "children",
        "moment", "vzpomínka", "vzpominka", "memory", "memories",
        "momlife", "dadlife", "siblings", "playtime",
        "first day of school", "první den ve škole", "prvni den ve skole",
        "back to school", "family trip", "birthday party", "milestone", "selfie"
    ]
}

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