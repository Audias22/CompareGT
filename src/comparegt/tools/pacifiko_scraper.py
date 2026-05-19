"""
CompareGT - Scraper para Pacifiko (www.pacifiko.com)
URLs verificadas el 31/03/2026.
Pacifiko usa OpenCart.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# URLs REALES de Pacifiko
PACIFIKO_CATEGORIES = {
    "laptops": "https://www.pacifiko.com/laptops",
    "audifonos": "https://www.pacifiko.com/audifonos",
    "monitores": "https://www.pacifiko.com/monitores",
    "impresoras": "https://www.pacifiko.com/impresoras",
    "teclados": "https://www.pacifiko.com/teclados",
    "mouse": "https://www.pacifiko.com/mouse",
    "bocinas": "https://www.pacifiko.com/bocinas-y-parlantes",
    "sillas_gamer": "https://www.pacifiko.com/sillas-para-oficina-y-gaming",
    "componentes_pc": "https://www.pacifiko.com/componentes-de-computadoras",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
}


MAX_PRODUCTS = 5

# Términos que indican accesorios o periféricos (no el producto principal)
_ACCESSORY_KEYWORDS = (
    "batería", "bateria", "cargador", "adaptador", "cable", "funda",
    "mochila", "mouse pad", "soporte", "hub", "repuesto", "compatible con",
    "para portátil", "para laptop",
    # en inglés (productos de Tienda Mundial/Amazon que son accesorios)
    "battery", "charger", "keyboard cover", "keyboard skin", "screen protector",
    "power jack", "case compatible", "replacement keyboard", "wh ",
)

# Palabras clave de categoría para la URL de búsqueda (captura Tienda Mundial)
CATEGORY_SEARCH_KEYWORDS = {
    "laptops": "laptop",
    "audifonos": "audifonos",
    "monitores": "monitor",
    "impresoras": "impresora",
    "teclados": "teclado",
    "mouse": "mouse",
    "bocinas": "bocinas",
    "sillas_gamer": "silla",
    "componentes_pc": "componentes",
}


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    # Match NNNN.NN format (max 2 decimal places) to avoid absorbing concatenated prices
    match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
    return float(match.group()) if match else 0.0


def _extract_cards_from_url(url: str) -> list:
    """Fetches a Pacifiko page and returns all .product-layout cards."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.select(".product-layout")
    except requests.RequestException:
        return []


def _parse_card(card, brand_lower: str) -> dict | None:
    """Extracts product data from a single card. Returns None if invalid."""
    try:
        name_el = card.select_one(
            "h4 a, h3 a, h2 a, .product-title a, .name a, "
            "[class*=title] a, [class*=name] a, .caption h4 a"
        )
        name = ""
        if name_el:
            name = name_el.get("title", "") or name_el.get_text(strip=True)
        if not name or brand_lower not in name.lower():
            return None
        # Excluir accesorios que contienen la marca en su descripción
        name_lower = name.lower()
        if any(kw in name_lower for kw in _ACCESSORY_KEYWORDS):
            return None

        # .price-new = precio actual de venta (descontado o regular).
        # .price-old = precio tachado anterior — NO usar.
        price_el = card.select_one(".price-new")
        if not price_el:
            price_el = card.select_one(".special-price, .product-price")
        if not price_el:
            price_el = card.select_one(".price")
        price_text = price_el.get_text(strip=True) if price_el else "0"
        price = _parse_price(price_text)
        if price == 0:
            return None

        product_url = name_el.get("href", "") if name_el else ""
        out_stock = card.select_one("[class*=out-of-stock], [class*=agotado]")

        return {
            "name": name,
            "price": price,
            "available": out_stock is None,
            "url": product_url,
            "store": "Pacifiko",
        }
    except Exception:
        return None


@tool("scrape_pacifiko")
def scrape_pacifiko(category: str, brand: str) -> str:
    """
    Extrae productos de Pacifiko (www.pacifiko.com) para una categoría y marca.

    Args:
        category: Categoría (laptops, audifonos, monitores, impresoras, bocinas, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    category_url = PACIFIKO_CATEGORIES.get(category_lower)
    if not category_url:
        return json.dumps({
            "store": "Pacifiko",
            "error": f"Categoría '{category}' no disponible.",
            "products": []
        })

    # URL de búsqueda: incluye productos de Tienda Mundial (Amazon import)
    # que NO aparecen en el listado de categoría regular.
    search_keyword = CATEGORY_SEARCH_KEYWORDS.get(category_lower, category_lower)
    search_url = (
        f"https://www.pacifiko.com/index.php?route=product/search"
        f"&search={brand_lower}+{search_keyword}&limit=100"
    )

    # Búsqueda primero: más específica por marca e incluye Tienda Mundial.
    # Categoría después: como suplemento para productos locales no capturados.
    all_cards = _extract_cards_from_url(search_url)
    all_cards += _extract_cards_from_url(f"{category_url}?limit=100")

    products: list[dict] = []
    seen_names: set[str] = set()

    for card in all_cards:
        if len(products) >= MAX_PRODUCTS:
            break
        product = _parse_card(card, brand_lower)
        if product and product["name"] not in seen_names:
            seen_names.add(product["name"])
            products.append(product)

    return json.dumps({
        "store": "Pacifiko",
        "total_found": len(products),
        "products": products
    })