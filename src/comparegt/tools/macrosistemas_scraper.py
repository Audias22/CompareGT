"""
CompareGT - Herramienta de Scraping para Macrosistemas (macrosistemas.com)
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

MACRO_CATEGORIES = {
    "laptops": "https://www.macrosistemas.com/categoria-producto/laptops/",
    "audifonos": "https://www.macrosistemas.com/categoria-producto/audifonos/",
    "monitores": "https://www.macrosistemas.com/categoria-producto/monitores/",
    "impresoras": "https://www.macrosistemas.com/categoria-producto/impresoras/",
    "teclados": "https://www.macrosistemas.com/categoria-producto/teclados/",
    "mouse": "https://www.macrosistemas.com/categoria-producto/mouse/",
    "bocinas": "https://www.macrosistemas.com/categoria-producto/bocinas/",
    "almacenamiento": "https://www.macrosistemas.com/categoria-producto/almacenamiento/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-GT,es;q=0.9",
}


MAX_PRODUCTS = 10


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_macrosistemas")
def scrape_macrosistemas(category: str, brand: str) -> str:
    """
    Extrae productos de Macrosistemas (macrosistemas.com) para una categoría y marca.

    Args:
        category: Categoría del producto (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con la lista de productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    url = MACRO_CATEGORIES.get(category_lower)
    if not url:
        return json.dumps({
            "store": "Macrosistemas",
            "error": f"Categoría \'{category}\' no disponible.",
            "products": []
        })

    products = []
    page = 1

    try:
        while True:
            page_url = f"{url}page/{page}/" if page > 1 else url
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            if response.status_code == 404:
                break
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            product_cards = soup.select(
                ".product, .type-product, li.product, .products .product"
            )
            if not product_cards:
                break

            found_in_page = False
            for card in product_cards:
                if len(products) >= MAX_PRODUCTS:
                    break
                try:
                    name_el = card.select_one(
                        ".woocommerce-loop-product__title, "
                        "h2.product-title, h2, .product-name a"
                    )
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name or brand_lower not in name.lower():
                        continue

                    found_in_page = True

                    price_el = card.select_one(
                        ".price ins .amount, .price .amount, "
                        ".woocommerce-Price-amount"
                    )
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = _parse_price(price_text)

                    link_el = card.select_one("a.woocommerce-LoopProduct-link, a[href]")
                    product_url = link_el["href"] if link_el and link_el.get("href") else ""

                    out_of_stock = card.select_one(
                        ".outofstock, .out-of-stock, .stock.out-of-stock"
                    )

                    products.append({
                        "name": name,
                        "price": price,
                        "available": out_of_stock is None,
                        "url": product_url,
                        "store": "Macrosistemas"
                    })
                except Exception:
                    continue

            if not found_in_page or len(products) >= MAX_PRODUCTS:
                break
            page += 1
            if page > 5:
                break

    except requests.RequestException as e:
        return json.dumps({
            "store": "Macrosistemas",
            "error": f"Error al conectar: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Macrosistemas",
        "total_found": len(products),
        "products": products
    })
