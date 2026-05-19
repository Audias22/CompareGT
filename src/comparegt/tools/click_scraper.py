"""
CompareGT - Scraper para Click (click.gt)
URLs verificadas el 31/03/2026.
Click usa Shopify - intentamos JSON y HTML.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# URLs REALES de Click
CLICK_CATEGORIES = {
    "laptops": "computadoras-portatiles",
    "audifonos": "audio",
    "monitores": "monitores",
    "teclados": "perifericos",
    "mouse": "perifericos",
    "bocinas": "audio",
    "almacenamiento": "almacenamiento",
    "sillas_gamer": "sillas",
    "componentes_pc": "partes-de-computadoras",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
}


MAX_PRODUCTS = 5


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_click")
def scrape_click(category: str, brand: str) -> str:
    """
    Extrae productos de Click (click.gt) para una categoría y marca.

    Args:
        category: Categoría (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    collection = CLICK_CATEGORIES.get(category_lower)
    if not collection:
        return json.dumps({
            "store": "Click",
            "error": f"Categoría '{category}' no disponible.",
            "products": []
        })

    products = []

    try:
        # Intentar 1: JSON endpoint de Shopify (categoría)
        json_url = f"https://click.gt/collections/{collection}/products.json?limit=50"
        try:
            resp = requests.get(json_url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for product in data.get("products", []):
                    if len(products) >= MAX_PRODUCTS:
                        break
                    name = product.get("title", "")
                    vendor = product.get("vendor", "")
                    if brand_lower not in name.lower() and brand_lower not in vendor.lower():
                        continue
                    variants = product.get("variants", [])
                    if not variants:
                        continue
                    variant = variants[0]
                    price = float(variant.get("price", "0") or "0")
                    handle = product.get("handle", "")
                    products.append({
                        "name": name,
                        "price": price,
                        "available": variant.get("available", False),
                        "url": f"https://click.gt/products/{handle}" if handle else "",
                        "store": "Click"
                    })
        except Exception:
            pass

        # Intentar 2: colección por marca
        if not products:
            try:
                resp = requests.get(
                    f"https://click.gt/collections/{brand_lower}/products.json?limit=50",
                    headers={**HEADERS, "Accept": "application/json"},
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for product in data.get("products", []):
                        if len(products) >= MAX_PRODUCTS:
                            break
                        name = product.get("title", "")
                        variants = product.get("variants", [])
                        if not variants:
                            continue
                        variant = variants[0]
                        price = float(variant.get("price", "0") or "0")
                        handle = product.get("handle", "")
                        products.append({
                            "name": name,
                            "price": price,
                            "available": variant.get("available", False),
                            "url": f"https://click.gt/products/{handle}" if handle else "",
                            "store": "Click"
                        })
            except Exception:
                pass

    except Exception as e:
        return json.dumps({
            "store": "Click",
            "error": f"Error: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Click",
        "total_found": len(products),
        "products": products
    })