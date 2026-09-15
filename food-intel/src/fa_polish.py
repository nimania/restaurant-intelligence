from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BRAND_PATHS = [ROOT / "config" / "brands.yml", ROOT / "config" / "brands_iran.yml"]

# Terms that frequently become awkward or inconsistent in generic machine translation.
# Replacing them before translation keeps restaurant-industry terminology stable.
TERM_GLOSSARY = [
    ("same-store sales", "فروش شعب هم‌مقایسه"),
    ("same store sales", "فروش شعب هم‌مقایسه"),
    ("comparable sales", "فروش قابل‌مقایسه"),
    ("average check", "میانگین مبلغ فاکتور"),
    ("average ticket", "میانگین مبلغ سفارش"),
    ("guest traffic", "تعداد مراجعه مشتریان"),
    ("customer traffic", "تعداد مراجعه مشتریان"),
    ("store traffic", "تعداد مراجعه مشتریان"),
    ("quick-service restaurant", "رستوران خدمات سریع"),
    ("quick service restaurant", "رستوران خدمات سریع"),
    ("quick-service", "خدمات سریع"),
    ("fast casual", "فست‌کژوال"),
    ("drive-thru", "درایو‌ثرو"),
    ("drive thru", "درایو‌ثرو"),
    ("foodservice", "خدمات غذایی"),
    ("food service", "خدمات غذایی"),
    ("franchisee", "فرنچایزگیرنده"),
    ("franchisor", "فرنچایزدهنده"),
    ("menu engineering", "مهندسی منو"),
    ("menu mix", "ترکیب فروش منو"),
    ("unit economics", "اقتصاد هر واحد"),
    ("prime cost", "هزینه‌های اصلی"),
    ("cost of goods sold", "بهای تمام‌شده کالای فروش‌رفته"),
    ("COGS", "بهای تمام‌شده کالای فروش‌رفته"),
    ("back of house", "بخش پشتی عملیات"),
    ("back-of-house", "بخش پشتی عملیات"),
    ("front of house", "بخش خدمات مشتری"),
    ("front-of-house", "بخش خدمات مشتری"),
    ("point of sale", "سیستم فروش"),
    ("POS system", "سیستم فروش"),
    ("kitchen display system", "نمایشگر آشپزخانه"),
    ("KDS", "نمایشگر آشپزخانه"),
    ("labor cost", "هزینه نیروی انسانی"),
    ("labor costs", "هزینه نیروی انسانی"),
    ("labor shortage", "کمبود نیروی انسانی"),
    ("throughput", "ظرفیت و سرعت سرویس"),
    ("daypart", "بازه زمانی فروش"),
    ("off-premise", "فروش خارج از محل"),
    ("dine-in", "سرویس حضوری"),
    ("takeout", "سفارش بیرون‌بر"),
    ("take-out", "سفارش بیرون‌بر"),
    ("loyalty program", "برنامه وفاداری مشتری"),
    ("loyalty programs", "برنامه‌های وفاداری مشتری"),
    ("digital ordering", "سفارش‌گیری دیجیتال"),
    ("online ordering", "سفارش آنلاین"),
    ("voice ordering", "سفارش‌گیری صوتی"),
]

COMMON_FIXES = [
    (r"فروش (?:در )?همان فروشگاه(?:‌ها|ها)?", "فروش شعب هم‌مقایسه"),
    (r"فروش فروشگاه(?:‌های|های) یکسان", "فروش شعب هم‌مقایسه"),
    (r"ترافیک (?:مهمان|مشتری|مشتریان)", "تعداد مراجعه مشتریان"),
    (r"چک متوسط", "میانگین مبلغ فاکتور"),
    (r"درایو\s*(?:از طریق|ترو|ثرو)", "درایو‌ثرو"),
    (r"نقطه فروش", "سیستم فروش"),
    (r"هزینه کالا(?:های)? فروخته شده", "بهای تمام‌شده کالای فروش‌رفته"),
    (r"خدمات سریع رستوران", "رستوران خدمات سریع"),
]


@lru_cache(maxsize=1)
def brand_replacements() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in BRAND_PATHS:
        if not path.exists():
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for brand in payload.get("brands", []):
            fa = (brand.get("fa") or "").strip()
            if not fa:
                continue
            variants = [brand.get("name", ""), *(brand.get("aliases", []) or [])]
            for value in variants:
                value = str(value or "").strip()
                if not value or not re.search(r"[A-Za-z]", value):
                    continue
                key = (value.lower(), fa)
                if key not in seen:
                    seen.add(key)
                    pairs.append((value, fa))
    return sorted(pairs, key=lambda x: len(x[0]), reverse=True)


def _replace_ascii_phrase(text: str, source: str, target: str) -> str:
    # ASCII-aware boundaries avoid matching fragments inside larger English words.
    pattern = rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])"
    return re.sub(pattern, target, text, flags=re.IGNORECASE)


def prepare_for_translation(text: str) -> str:
    value = str(text or "")
    for source, target in sorted(TERM_GLOSSARY, key=lambda x: len(x[0]), reverse=True):
        value = _replace_ascii_phrase(value, source, target)
    for source, target in brand_replacements():
        value = _replace_ascii_phrase(value, source, target)
    return value


def normalize_persian(text: str) -> str:
    value = str(text or "")
    value = value.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    value = value.replace("ۀ", "هٔ").replace("ة", "ه")
    value = value.replace("\u00a0", " ").replace("\u200e", "").replace("\u200f", "")
    value = value.replace("\u202a", "").replace("\u202b", "").replace("\u202c", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s*([،؛؟!])\s*", r"\1 ", value)
    value = re.sub(r"\s+([,.!?;:])", r"\1", value)
    value = re.sub(r"([,.!?;:])(?=[\u0600-\u06FFA-Za-z])", r"\1 ", value)
    value = re.sub(r"\s+\n", "\n", value)
    value = re.sub(r"\n\s+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r" {2,}", " ", value)
    return value.strip()


def polish_persian(text: str) -> str:
    value = normalize_persian(text)
    for source, target in brand_replacements():
        value = _replace_ascii_phrase(value, source, target)
    for source, target in sorted(TERM_GLOSSARY, key=lambda x: len(x[0]), reverse=True):
        value = _replace_ascii_phrase(value, source, target)
    for pattern, replacement in COMMON_FIXES:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    # Collapse duplicates produced when a translator renders both a brand name and its
    # transliteration, e.g. «استارباکس (استارباکس)».
    value = re.sub(r"\b([^()،؛]{2,35})\s*\(\s*\1\s*\)", r"\1", value, flags=re.IGNORECASE)
    value = normalize_persian(value)
    return value
