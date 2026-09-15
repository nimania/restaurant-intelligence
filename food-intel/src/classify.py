from __future__ import annotations

import re
from collections import OrderedDict

CATEGORY_RULES = OrderedDict({
    "qsr_fast_food": [
        "fast food", "quick service", "quick-service", "qsr", "drive-thru", "drive thru",
        "mcdonald", "burger king", "wendy", "taco bell", "chick-fil-a", "popeyes",
    ],
    "fast_casual": [
        "fast casual", "fast-casual", "chipotle", "cava", "sweetgreen", "panera",
    ],
    "restaurant_operations": [
        "restaurant operations", "back of house", "front of house", "kitchen operations",
        "throughput", "ticket time", "labor scheduling", "inventory", "mise en place",
    ],
    "menu_product_innovation": [
        "menu", "limited-time offer", "lto", "new flavor", "new product", "menu innovation",
        "menu engineering", "seasonal menu",
    ],
    "restaurant_technology_ai": [
        "artificial intelligence", " ai ", "automation", "robot", "computer vision",
        "digital ordering", "kiosk", "pos", "point of sale", "kds", "kitchen display",
        "voice ordering", "machine learning",
    ],
    "equipment_automation": [
        "equipment", "oven", "fryer", "refrigeration", "robotic", "automated kitchen",
        "foodservice equipment",
    ],
    "food_cost_pricing": [
        "food cost", "prime cost", "pricing", "menu price", "inflation", "commodity cost",
        "margin", "cost of goods", "cogs",
    ],
    "supply_chain": [
        "supply chain", "distribution", "logistics", "supplier", "procurement", "shortage",
        "transportation", "warehouse",
    ],
    "food_safety": [
        "food safety", "recall", "outbreak", "salmonella", "listeria", "e. coli",
        "contamination", "haccp",
    ],
    "labor_management": [
        "labor", "employee", "workers", "wage", "minimum wage", "hiring", "staffing",
        "retention", "manager", "workforce",
    ],
    "franchising": [
        "franchise", "franchising", "franchisee", "franchisor", "unit development",
    ],
    "delivery_drive_thru": [
        "delivery", "doordash", "uber eats", "grubhub", "drive-thru", "drive thru",
        "off-premise", "off premise", "takeout", "takeaway",
    ],
    "consumer_behavior": [
        "consumer", "customer behavior", "guest behavior", "traffic", "loyalty",
        "dining habits", "consumer spending",
    ],
    "marketing_branding": [
        "marketing", "brand campaign", "branding", "advertising", "promotion", "social media",
        "loyalty program",
    ],
    "beverage": [
        "beverage", "coffee", "tea", "soda", "soft drink", "energy drink", "smoothie",
        "lemonade", "cocktail", "mocktail",
    ],
    "food_manufacturing": [
        "food manufacturing", "manufacturer", "processing plant", "food processing",
        "production facility", "packaged food", "cpg",
    ],
    "ingredients_rd": [
        "ingredient", "formulation", "r&d", "research and development", "protein", "flavor",
        "texture", "emulsifier", "sweetener",
    ],
    "retail_food": [
        "grocery", "supermarket", "retail", "private label", "convenience store",
    ],
    "regulation": [
        "regulation", "regulatory", "fda", "usda", "law", "legislation", "ban", "rule",
        "compliance",
    ],
    "sustainability": [
        "sustainability", "sustainable", "carbon", "emissions", "food waste", "packaging waste",
        "regenerative agriculture",
    ],
})

TOPIC_TERMS = [
    "AI", "automation", "drive-thru", "delivery", "menu", "food safety", "food cost",
    "franchise", "labor", "supply chain", "beverage", "protein", "pricing", "robotics",
    "loyalty", "kiosk", "POS", "KDS", "consumer behavior", "sustainability",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def classify(title: str, summary: str = "", defaults: list[str] | None = None) -> tuple[list[str], list[str]]:
    text = f" {_normalize(title)} {_normalize(summary)} "
    categories: list[str] = []

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword.lower() in text for keyword in keywords):
            categories.append(category)

    for default in defaults or []:
        if default not in categories:
            categories.append(default)

    topics = []
    for term in TOPIC_TERMS:
        if term.lower() in text:
            topics.append(term)

    return categories[:8], topics[:12]
