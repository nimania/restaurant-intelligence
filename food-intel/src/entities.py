from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BRANDS_PATH = ROOT / "config" / "brands.yml"

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
}


def load_brands() -> list[dict]:
    payload = yaml.safe_load(BRANDS_PATH.read_text(encoding="utf-8")) or {}
    return payload.get("brands", [])


def _normalized(text: str) -> str:
    return (
        text.lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )


def _contains_alias(text: str, alias: str) -> bool:
    alias = _normalized(alias.strip())
    if not alias:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def detect_brands(title: str, summary: str, catalog: list[dict] | None = None) -> list[dict]:
    haystack = _normalized(f"{title} {summary}")
    matches = []
    for brand in catalog or load_brands():
        if any(_contains_alias(haystack, alias) for alias in brand.get("aliases", [])):
            matches.append({"id": brand["id"], "name": brand["name"], "fa": brand.get("fa", brand["name"])})
    return matches


def persian_context(categories: list[str], brands: list[dict], topics: list[str]) -> str:
    cat_labels = [CATEGORY_FA.get(c, c) for c in categories[:2]]
    brand_labels = [b.get("fa") or b.get("name") for b in brands[:2]]
    topic_labels = [TOPIC_FA.get(t, t) for t in topics[:2]]

    parts = []
    if cat_labels:
        parts.append("این خبر در حوزهٔ " + " و ".join(cat_labels) + " است")
    if brand_labels:
        parts.append("به " + " و ".join(brand_labels) + " مربوط می‌شود")
    elif topic_labels:
        parts.append("محور اصلی آن " + " و ".join(topic_labels) + " است")
    if not parts:
        return "این خبر یکی از سیگنال‌های رصدشده در صنعت غذا و رستوران است."
    return " و ".join(parts) + "."
