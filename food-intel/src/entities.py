from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BRAND_PATHS = [
    ROOT / "config" / "brands.yml",
    ROOT / "config" / "brands_iran.yml",
    ROOT / "config" / "brands_turkey.yml",
]

# High-frequency public names that are shorter than the legal/company name in the
# catalog. Keeping them here avoids overly broad YAML aliases such as ordinary words.
EXTRA_ALIASES = {
    "pepsico": ["pepsi"],
    "coca_cola": ["coke", "coca‑cola"],
    "mcdonalds": ["mcdonald’s", "mcdonald’s restaurants"],
    "starbucks": ["starbucks coffee"],
    "rbi": ["restaurant brands"],
    "dunkin": ["dunkin donuts", "dunkin’"],
    "dominos": ["domino’s"],
    "chickfila": ["chick fil-a"],
    "snappfood": ["اسنپفود"],
    "mihan_dairy": ["میهن"],
}

CATEGORY_FA = {
    "qsr_fast_food": "فست‌فود و QSR",
    "fast_casual": "فست‌کژوال",
    "restaurant_operations": "عملیات رستوران",
    "menu_product_innovation": "نوآوری منو و محصول",
    "restaurant_technology_ai": "فناوری رستوران و هوش مصنوعی",
    "equipment_automation": "تجهیزات و اتوماسیون",
    "food_cost_pricing": "هزینه غذا و قیمت‌گذاری",
    "supply_chain": "زنجیره تأمین",
    "food_safety": "ایمنی غذا",
    "labor_management": "نیروی انسانی و مدیریت",
    "franchising": "فرنچایز",
    "delivery_drive_thru": "دلیوری و درایو‌ثرو",
    "consumer_behavior": "رفتار مصرف‌کننده",
    "marketing_branding": "بازاریابی و برندینگ",
    "restaurant_design_decor": "طراحی و دکور رستوران/کافه",
    "packaging_design": "بسته‌بندی و طراحی بسته‌بندی",
    "beverage": "نوشیدنی",
    "food_manufacturing": "تولید صنایع غذایی",
    "ingredients_rd": "مواد اولیه و تحقیق‌وتوسعه",
    "retail_food": "خرده‌فروشی غذا",
    "regulation": "قانون‌گذاری و مقررات",
    "sustainability": "پایداری",
    "restaurant_industry": "صنعت رستوران",
    "food_industry": "صنعت غذا",
}

TOPIC_FA = {
    "AI": "هوش مصنوعی",
    "automation": "اتوماسیون",
    "drive-thru": "درایو‌ثرو",
    "delivery": "دلیوری",
    "menu": "منو",
    "food safety": "ایمنی غذا",
    "food cost": "هزینه غذا",
    "franchise": "فرنچایز",
    "labor": "نیروی انسانی",
    "supply chain": "زنجیره تأمین",
    "beverage": "نوشیدنی",
    "protein": "پروتئین",
    "pricing": "قیمت‌گذاری",
    "robotics": "رباتیک",
    "loyalty": "وفاداری مشتری",
    "kiosk": "کیوسک سفارش",
    "POS": "سیستم فروش",
    "KDS": "نمایشگر آشپزخانه",
    "consumer behavior": "رفتار مصرف‌کننده",
    "sustainability": "پایداری",
    "packaging": "بسته‌بندی",
    "branding": "برندینگ",
    "restaurant design": "طراحی رستوران و کافه",
}


def load_brands() -> list[dict]:
    brands = []
    seen = set()
    for path in BRAND_PATHS:
        if not path.exists():
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for brand in payload.get("brands", []):
            if brand.get("id") and brand["id"] not in seen:
                brands.append(brand)
                seen.add(brand["id"])
    return brands


def _normalized(text: str) -> str:
    return (
        text.lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("‑", "-")
        .replace("\u200c", " ")
        .replace("ي", "ی")
        .replace("ك", "ک")
    )


def _contains_alias(text: str, alias: str) -> bool:
    alias = _normalized(alias.strip())
    if not alias:
        return False
    pattern = rf"(?<![\w]){re.escape(alias)}(?![\w])"
    return re.search(pattern, text, flags=re.UNICODE) is not None


def detect_brands(title: str, summary: str, catalog: list[dict] | None = None) -> list[dict]:
    """Detect brand/entity mentions without translating or paraphrasing article text."""
    haystack = _normalized(f"{title} {summary}")
    matches = []
    for brand in catalog or load_brands():
        aliases = [*(brand.get("aliases", []) or []), *EXTRA_ALIASES.get(brand.get("id"), [])]
        if any(_contains_alias(haystack, alias) for alias in aliases):
            match = {
                "id": brand["id"],
                "name": brand["name"],
                "fa": brand.get("fa", brand["name"]),
            }
            if brand.get("market"):
                match["market"] = brand["market"]
            matches.append(match)
    return matches
