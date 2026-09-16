from __future__ import annotations

from collections import OrderedDict
import re

CATEGORY_RULES_TR = OrderedDict({
    "qsr_fast_food": ["fast food", "hızlı servis", "hamburger", "döner", "dürüm", "çiğ köfte"],
    "fast_casual": ["fast casual", "fast-casual"],
    "restaurant_operations": ["restoran operasyon", "operasyon", "mutfak", "servis süresi", "stok", "verimlilik"],
    "menu_product_innovation": ["menü", "yeni ürün", "yeni lezzet", "ürün lansmanı", "inovasyon", "sezonluk"],
    "restaurant_technology_ai": ["yapay zeka", "yapay zekâ", "otomasyon", "robot", "dijital sipariş", "kiosk", "pos", "makine öğrenmesi"],
    "equipment_automation": ["ekipman", "fırın", "soğutma", "endüstriyel mutfak", "otomatik mutfak", "makine"],
    "food_cost_pricing": ["gıda maliyeti", "maliyet", "fiyat", "fiyatlandırma", "enflasyon", "marj", "hammadde fiyat"],
    "supply_chain": ["tedarik zinciri", "lojistik", "tedarikçi", "satın alma", "depo", "dağıtım"],
    "food_safety": ["gıda güvenliği", "geri çağırma", "salmonella", "listeria", "kontaminasyon", "haccp"],
    "labor_management": ["çalışan", "personel", "iş gücü", "istihdam", "maaş", "yönetici", "insan kaynakları"],
    "franchising": ["franchise", "bayilik", "franchising"],
    "delivery_drive_thru": ["paket servis", "teslimat", "online sipariş", "gel-al", "drive thru", "arabaya servis"],
    "consumer_behavior": ["tüketici", "müşteri davranış", "müşteri", "sadakat", "harcama", "talep"],
    "marketing_branding": ["pazarlama", "marka", "kampanya", "reklam", "promosyon", "sosyal medya", "sadakat programı"],
    "beverage": ["içecek", "kahve", "çay", "gazoz", "meyve suyu", "enerji içeceği", "maden suyu"],
    "food_manufacturing": ["gıda üretim", "gıda sanayi", "üretim tesisi", "fabrika", "paketli gıda", "kapasite"],
    "ingredients_rd": ["hammadde", "ar-ge", "arge", "formülasyon", "protein", "aroma", "tatlandırıcı"],
    "retail_food": ["market", "süpermarket", "perakende", "özel marka", "mağaza"],
    "regulation": ["yönetmelik", "mevzuat", "bakanlık", "denetim", "yasak", "düzenleme", "uyum"],
    "sustainability": ["sürdürülebilirlik", "karbon", "emisyon", "gıda atığı", "ambalaj atığı", "su verimliliği"],
    "restaurant_industry": ["restoran sektörü", "yeme içme sektörü", "gastronomi sektörü", "horeca"],
    "food_industry": ["gıda sektörü", "gıda sanayi", "gıda ve içecek sektörü"],
})

TOPIC_TERMS_TR = {
    "AI": ["yapay zeka", "yapay zekâ"],
    "automation": ["otomasyon", "robot"],
    "delivery": ["teslimat", "paket servis", "online sipariş"],
    "menu": ["menü"],
    "food safety": ["gıda güvenliği"],
    "food cost": ["gıda maliyeti", "maliyet"],
    "franchise": ["franchise", "bayilik"],
    "labor": ["çalışan", "personel", "iş gücü"],
    "supply chain": ["tedarik zinciri"],
    "beverage": ["içecek", "kahve", "çay"],
    "pricing": ["fiyat", "fiyatlandırma"],
    "robotics": ["robot", "robotik"],
    "loyalty": ["sadakat"],
    "consumer behavior": ["tüketici davranış", "müşteri davranış"],
    "sustainability": ["sürdürülebilirlik"],
    "packaging": ["ambalaj"],
    "branding": ["marka", "markalaşma"],
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def classify_tr(title: str, summary: str = "") -> tuple[list[str], list[str]]:
    text = f" {_norm(title)} {_norm(summary)} "
    categories: list[str] = []
    for category, terms in CATEGORY_RULES_TR.items():
        if any(term in text for term in terms):
            categories.append(category)
    topics: list[str] = []
    for topic, terms in TOPIC_TERMS_TR.items():
        if any(term in text for term in terms):
            topics.append(topic)
    return categories[:10], topics[:14]
