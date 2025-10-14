# -*- coding: utf-8 -*-
"""
Kategorie a klíčová slova pro organizaci screenshotů
"""

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
    "meal": 1, "meals": 1, "plan": 1, "plans": 1,
    "body": 1, "results": 1, "result": 1
}

# KATEGORIE - KOMPLETNÍ KLÍČOVÁ SLOVA
CATEGORIES = {
    "Deti_Svaciny": [
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
        "it", "ajťák", "ajtak", "ajťačka", "ajtacka", "holky v it", "zeny v it", "ženy v it",
        "women in tech", "women go tech", "womenwhocode", "girls who code",
        "qa", "quality assurance", "tester", "testing", "test",
        "bug", "issue", "defect", "chyba",
        "jira", "confluence", "agile", "scrum", "sprint",
        "postman", "api", "endpoint", "request", "response",
        "sql", "database", "databáze", "databaze", "query", "dotaz",
        "python", "javascript", "html", "css", "react", "code", "coding",
        "github", "git", "repository", "commit",
        "developer", "dev", "programming", "programování", "programovani"
    ],
    "Finance": [
        "faktura", "faktury", "invoice", "invoices",
        "peníze", "penize", "money", "cash", "finance", "financial",
        "rozpočet", "rozpocet", "budget", "budgeting",
        "účet", "ucet", "account", "bank", "banka", "banking",
        "platba", "payment", "transakce", "transaction",
        "investice", "investment", "etf", "fond"
    ],
    "Zdravi": [
        "zdraví", "zdravi", "health", "healthy", "wellness",
        "cvičení", "cviceni", "exercise", "workout", "fitness", "training",
        "calisthenics", "bodyweight", "hiit", "tabata",
        "fyzio", "fyzioterapie", "physiotherapy", "physio",
        "jóga", "yoga", "pilates", "stretching", "gym"
    ],
    "Dum_Design": [
        "rekonstrukce", "renovation", "dům", "dum", "house", "home", "byt",
        "nábytek", "nabytek", "furniture", "ikea",
        "design", "interior", "interiér", "interier",
        "půdorys", "pudorys", "floorplan"
    ],
    "Zahrada": [
        "zahrada", "garden", "gardening", "záhon", "zahon",
        "rostlina", "plant", "plants", "květina", "kvetina", "flower", "flowers",
        "trvalky", "perennials", "allium", "hydrangea", "hortenzie",
        "gravel garden", "štěrkový záhon",
        "pěstování", "pestovani", "výsadba", "vysadba",
        "hnojivo", "kompost", "mulč", "mulc"
    ],
    "Traveling": [
        "dovolená", "dovolena", "vacation", "holiday", "holidays",
        "cestování", "cestovani", "travel", "traveling",
        "hotel", "letiště", "letiste", "airport",
        "místo", "misto", "place", "destination"
    ],
    "Recepty": [
        "recept", "recepty", "recipe", "recipes",
        "vaření", "vareni", "cooking", "pečení", "peceni", "baking",
        "jídlo", "jidlo", "food", "meal"
    ],
    "Obleceni_Styl": [
        "oblečení", "obleceni", "outfit", "clothes", "clothing",
        "styl", "style", "fashion", "móda", "moda",
        "kalhoty", "mikina", "boty", "šaty", "saty", "kabát", "kabat"
    ],
    "Fotografie_Tips": [
        "fotografie", "photography", "photo", "photos",
        "tip", "tipy", "tips", "tutorial"
    ],
    "Knihy_Cetba": [
        "kniha", "knihy", "book", "books", "čtení", "cteni", "reading"
    ],
    "Podcast": [
        "podcast", "podcasts", "podcasty", "epizoda", "episode"
    ],
    "Christmas_Holidays": [
        "christmas", "vánoce", "vanoce", "xmas", "vánoční", "vanocni",
        "stromek", "advent", "cukroví", "cukrovi"
    ],
    "Citaty_Moudra": [
        "citát", "citat", "quote", "quotes",
        "moudro", "wisdom", "inspirace", "inspiration"
    ],
    "Rodina": [
        "rodina", "family", "maia", "maya", "oli", "oliver",
        "maminka", "mama", "tatínek", "tata", "děti", "deti"
    ]
}