from __future__ import annotations

import re


def _norm(value: str | None) -> str:
    return (
        (value or "").lower()
        .replace("\u200c", " ")
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("’", "'")
        .replace("‘", "'")
    )


def _has(text: str, alias: str) -> bool:
    alias_n = _norm(alias).strip()
    if not alias_n:
        return False
    if re.search(r"[a-z]", alias_n):
        return re.search(rf"(?<![a-z0-9]){re.escape(alias_n)}(?![a-z0-9])", text) is not None
    return alias_n in text


COUNTRIES = {
    "IR": {"fa": "ایران", "name": "Iran", "lat": 32.4279, "lon": 53.6880, "aliases": ["ایران", "iran", "iranian"]},
    "US": {"fa": "آمریکا", "name": "United States", "lat": 39.8283, "lon": -98.5795, "aliases": ["united states", "u.s.", "usa", "آمریکا", "ایالات متحده"]},
    "GB": {"fa": "بریتانیا", "name": "United Kingdom", "lat": 55.3781, "lon": -3.4360, "aliases": ["united kingdom", "britain", "british", "uk", "بریتانیا", "انگلیس"]},
    "CA": {"fa": "کانادا", "name": "Canada", "lat": 56.1304, "lon": -106.3468, "aliases": ["canada", "canadian", "کانادا"]},
    "DE": {"fa": "آلمان", "name": "Germany", "lat": 51.1657, "lon": 10.4515, "aliases": ["germany", "german", "آلمان"]},
    "FR": {"fa": "فرانسه", "name": "France", "lat": 46.2276, "lon": 2.2137, "aliases": ["france", "french", "فرانسه"]},
    "IT": {"fa": "ایتالیا", "name": "Italy", "lat": 41.8719, "lon": 12.5674, "aliases": ["italy", "italian", "ایتالیا"]},
    "ES": {"fa": "اسپانیا", "name": "Spain", "lat": 40.4637, "lon": -3.7492, "aliases": ["spain", "spanish", "اسپانیا"]},
    "AU": {"fa": "استرالیا", "name": "Australia", "lat": -25.2744, "lon": 133.7751, "aliases": ["australia", "australian", "استرالیا"]},
    "JP": {"fa": "ژاپن", "name": "Japan", "lat": 36.2048, "lon": 138.2529, "aliases": ["japan", "japanese", "ژاپن"]},
    "CN": {"fa": "چین", "name": "China", "lat": 35.8617, "lon": 104.1954, "aliases": ["china", "chinese", "چین"]},
    "AE": {"fa": "امارات", "name": "United Arab Emirates", "lat": 23.4241, "lon": 53.8478, "aliases": ["united arab emirates", "uae", "dubai", "دبی", "امارات"]},
    "TR": {"fa": "ترکیه", "name": "Türkiye", "lat": 38.9637, "lon": 35.2433, "aliases": ["türkiye", "turkiye", "ترکیه"]},
    "SA": {"fa": "عربستان سعودی", "name": "Saudi Arabia", "lat": 23.8859, "lon": 45.0792, "aliases": ["saudi arabia", "saudi", "عربستان سعودی"]},
    "QA": {"fa": "قطر", "name": "Qatar", "lat": 25.3548, "lon": 51.1839, "aliases": ["qatar", "قطر"]},
    "IQ": {"fa": "عراق", "name": "Iraq", "lat": 33.2232, "lon": 43.6793, "aliases": ["iraq", "iraqi", "عراق"]},
    "IN": {"fa": "هند", "name": "India", "lat": 20.5937, "lon": 78.9629, "aliases": ["india", "indian", "هند"]},
    "BR": {"fa": "برزیل", "name": "Brazil", "lat": -14.2350, "lon": -51.9253, "aliases": ["brazil", "brazilian", "برزیل"]},
    "MX": {"fa": "مکزیک", "name": "Mexico", "lat": 23.6345, "lon": -102.5528, "aliases": ["mexico", "mexican", "مکزیک"]},
    "NL": {"fa": "هلند", "name": "Netherlands", "lat": 52.1326, "lon": 5.2913, "aliases": ["netherlands", "dutch", "هلند"]},
    "CH": {"fa": "سوئیس", "name": "Switzerland", "lat": 46.8182, "lon": 8.2275, "aliases": ["switzerland", "swiss", "سوئیس"]},
    "SE": {"fa": "سوئد", "name": "Sweden", "lat": 60.1282, "lon": 18.6435, "aliases": ["sweden", "swedish", "سوئد"]},
    "DK": {"fa": "دانمارک", "name": "Denmark", "lat": 56.2639, "lon": 9.5018, "aliases": ["denmark", "danish", "دانمارک"]},
    "NO": {"fa": "نروژ", "name": "Norway", "lat": 60.4720, "lon": 8.4689, "aliases": ["norway", "norwegian", "نروژ"]},
    "KR": {"fa": "کره جنوبی", "name": "South Korea", "lat": 35.9078, "lon": 127.7669, "aliases": ["south korea", "korean", "کره جنوبی"]},
    "SG": {"fa": "سنگاپور", "name": "Singapore", "lat": 1.3521, "lon": 103.8198, "aliases": ["singapore", "سنگاپور"]},
}


IRAN_CITIES = {
    "tehran": {"fa": "تهران", "province": "تهران", "lat": 35.6892, "lon": 51.3890, "aliases": ["تهران", "tehran"]},
    "mashhad": {"fa": "مشهد", "province": "خراسان رضوی", "lat": 36.2605, "lon": 59.6168, "aliases": ["مشهد", "mashhad"]},
    "isfahan": {"fa": "اصفهان", "province": "اصفهان", "lat": 32.6546, "lon": 51.6680, "aliases": ["اصفهان", "isfahan", "esfahan"]},
    "shiraz": {"fa": "شیراز", "province": "فارس", "lat": 29.5918, "lon": 52.5837, "aliases": ["شیراز", "shiraz"]},
    "tabriz": {"fa": "تبریز", "province": "آذربایجان شرقی", "lat": 38.0800, "lon": 46.2919, "aliases": ["تبریز", "tabriz"]},
    "karaj": {"fa": "کرج", "province": "البرز", "lat": 35.8400, "lon": 50.9391, "aliases": ["کرج", "karaj"]},
    "qom": {"fa": "قم", "province": "قم", "lat": 34.6416, "lon": 50.8746, "aliases": ["قم", "qom"]},
    "ahvaz": {"fa": "اهواز", "province": "خوزستان", "lat": 31.3183, "lon": 48.6706, "aliases": ["اهواز", "ahvaz"]},
    "rasht": {"fa": "رشت", "province": "گیلان", "lat": 37.2808, "lon": 49.5832, "aliases": ["رشت", "rasht"]},
    "sari": {"fa": "ساری", "province": "مازندران", "lat": 36.5633, "lon": 53.0601, "aliases": ["ساری", "sari"]},
    "nowshahr": {"fa": "نوشهر", "province": "مازندران", "lat": 36.6485, "lon": 51.4962, "aliases": ["نوشهر", "nowshahr", "noshahr"]},
    "chalus": {"fa": "چالوس", "province": "مازندران", "lat": 36.6550, "lon": 51.4204, "aliases": ["چالوس", "chalus"]},
    "babol": {"fa": "بابل", "province": "مازندران", "lat": 36.5513, "lon": 52.6789, "aliases": ["بابل", "babol"]},
    "amol": {"fa": "آمل", "province": "مازندران", "lat": 36.4696, "lon": 52.3507, "aliases": ["آمل", "amol"]},
    "gorgan": {"fa": "گرگان", "province": "گلستان", "lat": 36.8456, "lon": 54.4393, "aliases": ["گرگان", "gorgan"]},
    "bandar_abbas": {"fa": "بندرعباس", "province": "هرمزگان", "lat": 27.1832, "lon": 56.2666, "aliases": ["بندرعباس", "بندر عباس", "bandar abbas"]},
    "kerman": {"fa": "کرمان", "province": "کرمان", "lat": 30.2839, "lon": 57.0834, "aliases": ["کرمان", "kerman"]},
    "yazd": {"fa": "یزد", "province": "یزد", "lat": 31.8974, "lon": 54.3569, "aliases": ["یزد", "yazd"]},
    "urmia": {"fa": "ارومیه", "province": "آذربایجان غربی", "lat": 37.5527, "lon": 45.0761, "aliases": ["ارومیه", "urmia", "orumiyeh"]},
    "ardabil": {"fa": "اردبیل", "province": "اردبیل", "lat": 38.2498, "lon": 48.2933, "aliases": ["اردبیل", "ardabil"]},
    "hamadan": {"fa": "همدان", "province": "همدان", "lat": 34.7992, "lon": 48.5146, "aliases": ["همدان", "hamadan"]},
    "kermanshah": {"fa": "کرمانشاه", "province": "کرمانشاه", "lat": 34.3142, "lon": 47.0650, "aliases": ["کرمانشاه", "kermanshah"]},
    "sanandaj": {"fa": "سنندج", "province": "کردستان", "lat": 35.3219, "lon": 46.9862, "aliases": ["سنندج", "sanandaj"]},
    "zanjan": {"fa": "زنجان", "province": "زنجان", "lat": 36.6769, "lon": 48.4963, "aliases": ["زنجان", "zanjan"]},
    "qazvin": {"fa": "قزوین", "province": "قزوین", "lat": 36.2688, "lon": 50.0041, "aliases": ["قزوین", "qazvin"]},
    "arak": {"fa": "اراک", "province": "مرکزی", "lat": 34.0917, "lon": 49.6892, "aliases": ["اراک", "arak"]},
    "semnan": {"fa": "سمنان", "province": "سمنان", "lat": 35.5769, "lon": 53.3921, "aliases": ["سمنان", "semnan"]},
    "bushehr": {"fa": "بوشهر", "province": "بوشهر", "lat": 28.9234, "lon": 50.8203, "aliases": ["بوشهر", "bushehr"]},
    "birjand": {"fa": "بیرجند", "province": "خراسان جنوبی", "lat": 32.8663, "lon": 59.2211, "aliases": ["بیرجند", "birjand"]},
    "bojnord": {"fa": "بجنورد", "province": "خراسان شمالی", "lat": 37.4747, "lon": 57.3290, "aliases": ["بجنورد", "bojnord"]},
    "khorramabad": {"fa": "خرم‌آباد", "province": "لرستان", "lat": 33.4878, "lon": 48.3558, "aliases": ["خرم آباد", "خرم‌آباد", "khorramabad"]},
    "ilam": {"fa": "ایلام", "province": "ایلام", "lat": 33.6374, "lon": 46.4227, "aliases": ["ایلام", "ilam"]},
    "shahrekord": {"fa": "شهرکرد", "province": "چهارمحال و بختیاری", "lat": 32.3256, "lon": 50.8644, "aliases": ["شهرکرد", "shahrekord"]},
    "kashan": {"fa": "کاشان", "province": "اصفهان", "lat": 33.9850, "lon": 51.4099, "aliases": ["کاشان", "kashan"]},
    "abadan": {"fa": "آبادان", "province": "خوزستان", "lat": 30.3473, "lon": 48.2934, "aliases": ["آبادان", "abadan"]},
    "khorramshahr": {"fa": "خرمشهر", "province": "خوزستان", "lat": 30.4256, "lon": 48.1891, "aliases": ["خرمشهر", "khorramshahr"]},
    "dezful": {"fa": "دزفول", "province": "خوزستان", "lat": 32.3831, "lon": 48.4236, "aliases": ["دزفول", "dezful"]},
    "kish": {"fa": "کیش", "province": "هرمزگان", "lat": 26.5325, "lon": 53.9702, "aliases": ["کیش", "kish"]},
    "qeshm": {"fa": "قشم", "province": "هرمزگان", "lat": 26.8119, "lon": 55.8913, "aliases": ["قشم", "qeshm"]},
    "neyshabur": {"fa": "نیشابور", "province": "خراسان رضوی", "lat": 36.2141, "lon": 58.7961, "aliases": ["نیشابور", "neyshabur", "nishapur"]},
    "sabzevar": {"fa": "سبزوار", "province": "خراسان رضوی", "lat": 36.2126, "lon": 57.6819, "aliases": ["سبزوار", "sabzevar"]},
}


def enrich_geo(title: str, summary: str, source: dict | None = None) -> dict:
    source = source or {}
    text = _norm(f"{title} {summary}")

    cities = []
    for city_id, city in IRAN_CITIES.items():
        if any(_has(text, alias) for alias in city["aliases"]):
            cities.append({
                "id": city_id,
                "fa": city["fa"],
                "province": city["province"],
                "country": "IR",
                "lat": city["lat"],
                "lon": city["lon"],
            })

    countries = []
    for code, country in COUNTRIES.items():
        if any(_has(text, alias) for alias in country["aliases"]):
            countries.append({
                "code": code,
                "fa": country["fa"],
                "name": country["name"],
                "lat": country["lat"],
                "lon": country["lon"],
                "basis": "text",
            })

    if cities and not any(c["code"] == "IR" for c in countries):
        country = COUNTRIES["IR"]
        countries.insert(0, {"code": "IR", "fa": country["fa"], "name": country["name"], "lat": country["lat"], "lon": country["lon"], "basis": "city"})

    source_country = str(source.get("country") or "").upper()
    if not countries and source_country in COUNTRIES:
        country = COUNTRIES[source_country]
        countries.append({
            "code": source_country,
            "fa": country["fa"],
            "name": country["name"],
            "lat": country["lat"],
            "lon": country["lon"],
            "basis": "source",
        })

    primary = countries[0] if countries else None
    return {
        "primary_country": primary,
        "countries": countries[:5],
        "cities": cities[:8],
        "confidence": "high" if cities or any(c.get("basis") == "text" for c in countries) else ("medium" if countries else "unknown"),
    }
