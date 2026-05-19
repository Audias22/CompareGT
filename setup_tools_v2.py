"""
CompareGT - Setup Tools V2 (URLs corregidas)
Ejecutar desde la RAÍZ del proyecto (donde está pyproject.toml):

    python setup_tools_v2.py
"""

import os

TOOLS_DIR = os.path.join("src", "comparegt", "tools")
os.makedirs(TOOLS_DIR, exist_ok=True)

# ============================================================
# 1. src/comparegt/tools/__init__.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''"""CompareGT - Herramientas de Scraping para tiendas guatemaltecas."""

from .max_scraper import scrape_max
from .tecnofacil_scraper import scrape_tecnofacil
from .click_scraper import scrape_click
from .pacifiko_scraper import scrape_pacifiko

__all__ = [
    "scrape_max",
    "scrape_tecnofacil",
    "scrape_click",
    "scrape_pacifiko",
]
''')
print(f"✅ {TOOLS_DIR}/__init__.py")

# ============================================================
# 2. MAX SCRAPER - URLs reales: www.max.com.gt/electronicos/...
# ============================================================
with open(os.path.join(TOOLS_DIR, "max_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Scraper para MAX (www.max.com.gt)
URLs verificadas el 31/03/2026.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# URLs REALES de MAX verificadas
MAX_CATEGORIES = {
    "laptops": "https://www.max.com.gt/electronicos/computacion/laptops",
    "audifonos": "https://www.max.com.gt/audio/audifonos",
    "monitores": "https://www.max.com.gt/electronicos/computacion/monitores",
    "impresoras": "https://www.max.com.gt/electronicos/computacion/impresoras",
    "teclados": "https://www.max.com.gt/electronicos/computacion/accesorios-para-computadoras",
    "mouse": "https://www.max.com.gt/electronicos/computacion/accesorios-para-computadoras",
    "bocinas": "https://www.max.com.gt/audio/bocinas",
    "sillas_gamer": "https://www.max.com.gt/electronicos/gaming",
    "componentes_pc": "https://www.max.com.gt/electronicos/computacion",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
}


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_max")
def scrape_max(category: str, brand: str) -> str:
    """
    Extrae productos de MAX (www.max.com.gt) para una categoría y marca.

    Args:
        category: Categoría (laptops, audifonos, monitores, impresoras, bocinas, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, Asus, etc.)

    Returns:
        JSON string con productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    url = MAX_CATEGORIES.get(category_lower)
    if not url:
        return json.dumps({
            "store": "MAX",
            "error": f"Categoría \\'{category}\\' no encontrada.",
            "products": []
        })

    products = []

    try:
        # Intentar también la URL por marca directamente
        brand_urls = [
            url,
            f"https://www.max.com.gt/marcas/productos-{brand_lower}/{category_lower}-{brand_lower}",
        ]

        for page_url in brand_urls:
            try:
                response = requests.get(page_url, headers=HEADERS, timeout=20)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                # MAX: buscar productos en diferentes selectores posibles
                # Intentar encontrar datos JSON embebidos en la página
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "ItemList":
                            for item in data.get("itemListElement", []):
                                offer = item.get("item", item)
                                name = offer.get("name", "")
                                if brand_lower not in name.lower():
                                    continue
                                price_info = offer.get("offers", {})
                                price = float(price_info.get("price", 0))
                                products.append({
                                    "name": name,
                                    "price": price,
                                    "available": price_info.get("availability", "") != "OutOfStock",
                                    "url": offer.get("url", ""),
                                    "image_url": offer.get("image", ""),
                                    "store": "MAX"
                                })
                    except (json.JSONDecodeError, ValueError):
                        continue

                # También intentar selectores HTML comunes
                selectors = [
                    "[data-product]", ".product-card", ".product-item",
                    ".grid-product", "article.product", ".product-grid-item",
                    ".product-list-item", ".card-product"
                ]
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        for card in cards:
                            try:
                                # Nombre
                                name_el = card.select_one(
                                    "h2, h3, h4, .product-name, .product-title, "
                                    "[class*=title], [class*=name], a[title]"
                                )
                                name = ""
                                if name_el:
                                    name = name_el.get("title", "") or name_el.get_text(strip=True)
                                if not name or brand_lower not in name.lower():
                                    continue

                                # Precio
                                price_el = card.select_one(
                                    "[class*=price], .money, [data-price]"
                                )
                                price_text = price_el.get_text(strip=True) if price_el else "0"
                                price = _parse_price(price_text)
                                if price == 0:
                                    continue

                                # URL
                                link_el = card.select_one("a[href]")
                                product_url = ""
                                if link_el:
                                    href = link_el.get("href", "")
                                    if href.startswith("/"):
                                        product_url = f"https://www.max.com.gt{href}"
                                    elif href.startswith("http"):
                                        product_url = href

                                # Imagen
                                img_el = card.select_one("img[src], img[data-src]")
                                image_url = ""
                                if img_el:
                                    image_url = img_el.get("src", "") or img_el.get("data-src", "")
                                    if image_url.startswith("//"):
                                        image_url = f"https:{image_url}"

                                # Evitar duplicados
                                if not any(p["name"] == name for p in products):
                                    products.append({
                                        "name": name,
                                        "price": price,
                                        "available": True,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "store": "MAX"
                                    })
                            except Exception:
                                continue
                        break  # Si encontramos productos con un selector, no seguir

                if products:
                    break  # Si ya encontramos productos, no probar otra URL

            except requests.RequestException:
                continue

    except Exception as e:
        return json.dumps({
            "store": "MAX",
            "error": f"Error: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "MAX",
        "total_found": len(products),
        "products": products
    })
''')
print(f"✅ {TOOLS_DIR}/max_scraper.py")

# ============================================================
# 3. TECNO FÁCIL SCRAPER - URLs reales
# ============================================================
with open(os.path.join(TOOLS_DIR, "tecnofacil_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Scraper para Tecno Fácil (www.tecnofacil.com.gt)
URLs verificadas el 31/03/2026.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

# URLs REALES de Tecno Fácil
TECNOFACIL_CATEGORIES = {
    "laptops": "https://www.tecnofacil.com.gt/electronicos-en-guatemala/computacion/computadoras",
    "audifonos": "https://www.tecnofacil.com.gt/audio-en-guatemala/audifonos",
    "monitores": "https://www.tecnofacil.com.gt/electronicos-en-guatemala/computacion/monitores",
    "impresoras": "https://www.tecnofacil.com.gt/electronicos-en-guatemala/computacion/impresoras",
    "teclados": "https://www.tecnofacil.com.gt/electronicos-en-guatemala/computacion/accesorios-para-computadoras",
    "mouse": "https://www.tecnofacil.com.gt/electronicos-en-guatemala/computacion/accesorios-para-computadoras",
    "bocinas": "https://www.tecnofacil.com.gt/audio-en-guatemala/bocinas",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
}


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_tecnofacil")
def scrape_tecnofacil(category: str, brand: str) -> str:
    """
    Extrae productos de Tecno Fácil (www.tecnofacil.com.gt) para una categoría y marca.

    Args:
        category: Categoría (laptops, audifonos, monitores, impresoras, bocinas, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    url = TECNOFACIL_CATEGORIES.get(category_lower)
    if not url:
        return json.dumps({
            "store": "Tecno Fácil",
            "error": f"Categoría \\'{category}\\' no disponible.",
            "products": []
        })

    products = []

    try:
        brand_urls = [
            url,
            f"https://www.tecnofacil.com.gt/marcas/productos-{brand_lower}/{category_lower}-{brand_lower}",
        ]

        for page_url in brand_urls:
            try:
                response = requests.get(page_url, headers=HEADERS, timeout=20)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                # Buscar JSON-LD
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "ItemList":
                            for item in data.get("itemListElement", []):
                                offer = item.get("item", item)
                                name = offer.get("name", "")
                                if brand_lower not in name.lower():
                                    continue
                                price_info = offer.get("offers", {})
                                price = float(price_info.get("price", 0))
                                products.append({
                                    "name": name,
                                    "price": price,
                                    "available": price_info.get("availability", "") != "OutOfStock",
                                    "url": offer.get("url", ""),
                                    "image_url": offer.get("image", ""),
                                    "store": "Tecno Fácil"
                                })
                    except (json.JSONDecodeError, ValueError):
                        continue

                # Selectores HTML
                selectors = [
                    "[data-product]", ".product-card", ".product-item",
                    "article.product", ".product-grid-item", ".card-product"
                ]
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        for card in cards:
                            try:
                                name_el = card.select_one(
                                    "h2, h3, h4, .product-name, .product-title, "
                                    "[class*=title], [class*=name], a[title]"
                                )
                                name = ""
                                if name_el:
                                    name = name_el.get("title", "") or name_el.get_text(strip=True)
                                if not name or brand_lower not in name.lower():
                                    continue

                                price_el = card.select_one("[class*=price], .money, [data-price]")
                                price_text = price_el.get_text(strip=True) if price_el else "0"
                                price = _parse_price(price_text)
                                if price == 0:
                                    continue

                                link_el = card.select_one("a[href]")
                                product_url = ""
                                if link_el:
                                    href = link_el.get("href", "")
                                    if href.startswith("/"):
                                        product_url = f"https://www.tecnofacil.com.gt{href}"
                                    elif href.startswith("http"):
                                        product_url = href

                                img_el = card.select_one("img[src], img[data-src]")
                                image_url = ""
                                if img_el:
                                    image_url = img_el.get("src", "") or img_el.get("data-src", "")

                                if not any(p["name"] == name for p in products):
                                    products.append({
                                        "name": name,
                                        "price": price,
                                        "available": True,
                                        "url": product_url,
                                        "image_url": image_url,
                                        "store": "Tecno Fácil"
                                    })
                            except Exception:
                                continue
                        break

                if products:
                    break

            except requests.RequestException:
                continue

    except Exception as e:
        return json.dumps({
            "store": "Tecno Fácil",
            "error": f"Error: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Tecno Fácil",
        "total_found": len(products),
        "products": products
    })
''')
print(f"✅ {TOOLS_DIR}/tecnofacil_scraper.py")

# ============================================================
# 4. CLICK SCRAPER - URL real: click.gt/collections/...
# ============================================================
with open(os.path.join(TOOLS_DIR, "click_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
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


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
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
            "error": f"Categoría \\'{category}\\' no disponible.",
            "products": []
        })

    products = []

    try:
        # Intentar 1: JSON endpoint de Shopify
        json_url = f"https://click.gt/collections/{collection}/products.json?limit=250"
        try:
            resp = requests.get(json_url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for product in data.get("products", []):
                    name = product.get("title", "")
                    vendor = product.get("vendor", "")
                    if brand_lower not in name.lower() and brand_lower not in vendor.lower():
                        continue
                    variants = product.get("variants", [])
                    if not variants:
                        continue
                    variant = variants[0]
                    price = float(variant.get("price", "0") or "0")
                    available = variant.get("available", False)
                    handle = product.get("handle", "")
                    images = product.get("images", [])
                    products.append({
                        "name": name,
                        "price": price,
                        "available": available,
                        "url": f"https://click.gt/products/{handle}" if handle else "",
                        "image_url": images[0].get("src", "") if images else "",
                        "store": "Click"
                    })
        except Exception:
            pass

        # Intentar 2: También probar con la marca como colección
        if not products:
            brand_url = f"https://click.gt/collections/{brand_lower}"
            try:
                resp = requests.get(
                    f"{brand_url}/products.json?limit=250",
                    headers={**HEADERS, "Accept": "application/json"},
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for product in data.get("products", []):
                        name = product.get("title", "")
                        variants = product.get("variants", [])
                        if not variants:
                            continue
                        variant = variants[0]
                        price = float(variant.get("price", "0") or "0")
                        available = variant.get("available", False)
                        handle = product.get("handle", "")
                        images = product.get("images", [])
                        products.append({
                            "name": name,
                            "price": price,
                            "available": available,
                            "url": f"https://click.gt/products/{handle}" if handle else "",
                            "image_url": images[0].get("src", "") if images else "",
                            "store": "Click"
                        })
            except Exception:
                pass

        # Intentar 3: HTML scraping como fallback
        if not products:
            html_url = f"https://click.gt/collections/{collection}"
            try:
                resp = requests.get(html_url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(
                        ".product-card, .grid-product, [data-product], "
                        ".product-item, article"
                    )
                    for card in cards:
                        name_el = card.select_one(
                            "h2, h3, h4, .product-title, [class*=title], a[title]"
                        )
                        name = ""
                        if name_el:
                            name = name_el.get("title", "") or name_el.get_text(strip=True)
                        if not name or brand_lower not in name.lower():
                            continue
                        price_el = card.select_one("[class*=price], .money")
                        price_text = price_el.get_text(strip=True) if price_el else "0"
                        price = _parse_price(price_text)
                        if price == 0:
                            continue
                        link_el = card.select_one("a[href]")
                        product_url = ""
                        if link_el:
                            href = link_el.get("href", "")
                            if href.startswith("/"):
                                product_url = f"https://click.gt{href}"
                            elif href.startswith("http"):
                                product_url = href
                        if not any(p["name"] == name for p in products):
                            products.append({
                                "name": name,
                                "price": price,
                                "available": True,
                                "url": product_url,
                                "image_url": "",
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
''')
print(f"✅ {TOOLS_DIR}/click_scraper.py")

# ============================================================
# 5. PACIFIKO SCRAPER - URL real: www.pacifiko.com/laptops
# ============================================================
with open(os.path.join(TOOLS_DIR, "pacifiko_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
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


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


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

    url = PACIFIKO_CATEGORIES.get(category_lower)
    if not url:
        return json.dumps({
            "store": "Pacifiko",
            "error": f"Categoría \\'{category}\\' no disponible.",
            "products": []
        })

    products = []
    page = 1

    try:
        while page <= 5:
            page_url = f"{url}?limit=100&page={page}" if page > 1 else f"{url}?limit=100"

            response = requests.get(page_url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Pacifiko (OpenCart): buscar productos
            cards = soup.select(
                ".product-layout, .product-card, .product-thumb, "
                ".product-grid-item, .product-item, [class*=product-col]"
            )

            if not cards:
                # Intentar con selectores más genéricos
                cards = soup.select("div[class*=product]")

            if not cards:
                break

            found_in_page = False
            for card in cards:
                try:
                    # Nombre
                    name_el = card.select_one(
                        "h4 a, h3 a, h2 a, .product-title a, .name a, "
                        "[class*=title] a, [class*=name] a, .caption h4 a"
                    )
                    name = ""
                    if name_el:
                        name = name_el.get("title", "") or name_el.get_text(strip=True)
                    if not name or brand_lower not in name.lower():
                        continue

                    found_in_page = True

                    # Precio
                    price_el = card.select_one(
                        ".price-new, .special-price, .product-price, "
                        "[class*=price]:not(.price-old), .price"
                    )
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = _parse_price(price_text)
                    if price == 0:
                        continue

                    # URL
                    product_url = name_el.get("href", "") if name_el else ""

                    # Imagen
                    img_el = card.select_one("img[src], img[data-src]")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", "") or img_el.get("data-src", "")
                        if image_url.startswith("//"):
                            image_url = f"https:{image_url}"

                    # Disponibilidad
                    out_stock = card.select_one("[class*=out-of-stock], [class*=agotado]")
                    available = out_stock is None

                    if not any(p["name"] == name for p in products):
                        products.append({
                            "name": name,
                            "price": price,
                            "available": available,
                            "url": product_url,
                            "image_url": image_url,
                            "store": "Pacifiko"
                        })
                except Exception:
                    continue

            if not found_in_page:
                break

            page += 1

    except requests.RequestException as e:
        return json.dumps({
            "store": "Pacifiko",
            "error": f"Error al conectar: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Pacifiko",
        "total_found": len(products),
        "products": products
    })
''')
print(f"✅ {TOOLS_DIR}/pacifiko_scraper.py")

# ============================================================
# RESUMEN
# ============================================================
print("\\n" + "=" * 50)
print("🎉 Scrapers V2 con URLs corregidas!")
print("=" * 50)
print(f"\\nArchivos en {TOOLS_DIR}/:")
for f_name in sorted(os.listdir(TOOLS_DIR)):
    print(f"  📄 {f_name}")
print("\\n⚠️  NOTA: Macrosistemas fue removido temporalmente")
print("    (su sitio web da timeout). Se agrega después.")