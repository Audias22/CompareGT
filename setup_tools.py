"""
CompareGT - Script para crear los archivos de scrapers.
Ejecutar desde la RAÍZ del proyecto (donde está pyproject.toml):

    python setup_tools.py
"""

import os

# Directorio base de tools
TOOLS_DIR = os.path.join("src", "comparegt", "tools")
COMPAREGT_DIR = os.path.join("src", "comparegt")

os.makedirs(TOOLS_DIR, exist_ok=True)

# ============================================================
# 1. src/comparegt/__init__.py (limpiar - no debe tener imports de scrapers)
# ============================================================
with open(os.path.join(COMPAREGT_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

print(f"✅ Limpiado: {COMPAREGT_DIR}/__init__.py")

# ============================================================
# 2. src/comparegt/tools/__init__.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''"""CompareGT - Herramientas de Scraping para tiendas guatemaltecas."""

from .max_scraper import scrape_max
from .tecnofacil_scraper import scrape_tecnofacil
from .click_scraper import scrape_click
from .macrosistemas_scraper import scrape_macrosistemas
from .pacifiko_scraper import scrape_pacifiko

__all__ = [
    "scrape_max",
    "scrape_tecnofacil",
    "scrape_click",
    "scrape_macrosistemas",
    "scrape_pacifiko",
]
''')

print(f"✅ Creado: {TOOLS_DIR}/__init__.py")

# ============================================================
# 3. src/comparegt/tools/max_scraper.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "max_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Herramienta de Scraping para MAX (max.com.gt)
Extrae productos de electrónica usando BeautifulSoup.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

MAX_CATEGORIES = {
    "laptops": "https://max.com.gt/collections/laptops",
    "audifonos": "https://max.com.gt/collections/audifonos",
    "monitores": "https://max.com.gt/collections/monitores",
    "impresoras": "https://max.com.gt/collections/impresoras",
    "teclados": "https://max.com.gt/collections/teclados",
    "mouse": "https://max.com.gt/collections/mouse",
    "bocinas": "https://max.com.gt/collections/bocinas-y-parlantes",
    "almacenamiento": "https://max.com.gt/collections/almacenamiento",
    "sillas_gamer": "https://max.com.gt/collections/sillas-gamer",
    "componentes_pc": "https://max.com.gt/collections/componentes",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-GT,es;q=0.9",
}


def _parse_price(price_text: str) -> float:
    """Convierte texto de precio a número float."""
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_max")
def scrape_max(category: str, brand: str) -> str:
    """
    Extrae productos de MAX (max.com.gt) para una categoría y marca específica.

    Args:
        category: Categoría del producto (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con la lista de productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    url = MAX_CATEGORIES.get(category_lower)
    if not url:
        return json.dumps({
            "store": "MAX",
            "error": f"Categoría \\'{category}\\' no encontrada. Disponibles: {list(MAX_CATEGORIES.keys())}",
            "products": []
        })

    products = []
    page = 1

    try:
        while True:
            page_url = f"{url}?page={page}"
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            product_cards = soup.select(".product-card, .grid-product, .product-item")
            if not product_cards:
                product_cards = soup.select("[data-product-card], .collection-product")
            if not product_cards:
                break

            found_in_page = False
            for card in product_cards:
                try:
                    name_el = card.select_one(
                        ".product-card__name, .product-card__title, "
                        ".grid-product__title, .product-item__title, h3, h2"
                    )
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name:
                        continue
                    if brand_lower not in name.lower():
                        continue

                    found_in_page = True

                    price_el = card.select_one(
                        ".product-card__price, .grid-product__price, "
                        ".product-item__price, .price, .money"
                    )
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = _parse_price(price_text)

                    link_el = card.select_one("a[href]")
                    product_url = ""
                    if link_el:
                        href = link_el.get("href", "")
                        if href.startswith("/"):
                            product_url = f"https://max.com.gt{href}"
                        elif href.startswith("http"):
                            product_url = href

                    img_el = card.select_one("img")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", "") or img_el.get("data-src", "")
                        if image_url.startswith("//"):
                            image_url = f"https:{image_url}"

                    sold_out = card.select_one(".sold-out, .agotado, [data-sold-out]")
                    available = sold_out is None

                    products.append({
                        "name": name,
                        "price": price,
                        "available": available,
                        "url": product_url,
                        "image_url": image_url,
                        "store": "MAX"
                    })
                except Exception:
                    continue

            if not found_in_page:
                break
            page += 1
            if page > 10:
                break

    except requests.RequestException as e:
        return json.dumps({
            "store": "MAX",
            "error": f"Error al conectar con MAX: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "MAX",
        "total_found": len(products),
        "products": products
    })
''')

print(f"✅ Creado: {TOOLS_DIR}/max_scraper.py")

# ============================================================
# 4. src/comparegt/tools/tecnofacil_scraper.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "tecnofacil_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Herramienta de Scraping para Tecno Fácil (tecnofacil.com.gt)
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

TECNOFACIL_CATEGORIES = {
    "laptops": "https://www.tecnofacil.com.gt/computadoras/laptops.html",
    "audifonos": "https://www.tecnofacil.com.gt/audio/audifonos.html",
    "monitores": "https://www.tecnofacil.com.gt/computadoras/monitores.html",
    "impresoras": "https://www.tecnofacil.com.gt/computadoras/impresoras.html",
    "teclados": "https://www.tecnofacil.com.gt/accesorios/teclados.html",
    "mouse": "https://www.tecnofacil.com.gt/accesorios/mouse.html",
    "bocinas": "https://www.tecnofacil.com.gt/audio/bocinas.html",
    "almacenamiento": "https://www.tecnofacil.com.gt/computadoras/almacenamiento.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-GT,es;q=0.9",
}


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_tecnofacil")
def scrape_tecnofacil(category: str, brand: str) -> str:
    """
    Extrae productos de Tecno Fácil (tecnofacil.com.gt) para una categoría y marca.

    Args:
        category: Categoría del producto (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con la lista de productos encontrados.
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
    page = 1

    try:
        while True:
            page_url = f"{url}?p={page}" if page > 1 else url
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            product_cards = soup.select(
                ".product-item, .item.product.product-item, "
                ".products-grid .product-item-info"
            )
            if not product_cards:
                break

            found_in_page = False
            for card in product_cards:
                try:
                    name_el = card.select_one(
                        ".product-item-link, .product-item-name a, .product.name a"
                    )
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name or brand_lower not in name.lower():
                        continue

                    found_in_page = True

                    price_el = card.select_one(
                        ".price-wrapper .price, .special-price .price, .price-box .price"
                    )
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = _parse_price(price_text)

                    product_url = ""
                    if name_el and name_el.get("href"):
                        product_url = name_el["href"]

                    img_el = card.select_one(".product-image-photo, img.product-image-photo")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", "") or img_el.get("data-src", "")

                    stock_el = card.select_one(".stock.unavailable, .out-of-stock")
                    available = stock_el is None

                    products.append({
                        "name": name,
                        "price": price,
                        "available": available,
                        "url": product_url,
                        "image_url": image_url,
                        "store": "Tecno Fácil"
                    })
                except Exception:
                    continue

            if not found_in_page:
                break
            page += 1
            if page > 10:
                break

    except requests.RequestException as e:
        return json.dumps({
            "store": "Tecno Fácil",
            "error": f"Error al conectar: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Tecno Fácil",
        "total_found": len(products),
        "products": products
    })
''')

print(f"✅ Creado: {TOOLS_DIR}/tecnofacil_scraper.py")

# ============================================================
# 5. src/comparegt/tools/click_scraper.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "click_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Herramienta de Scraping para Click (click.gt)
Click usa Shopify, accedemos al JSON de productos directamente.
"""

import json
import requests
from crewai.tools import tool

CLICK_CATEGORIES = {
    "laptops": "laptops",
    "audifonos": "audifonos",
    "monitores": "monitores",
    "impresoras": "impresoras",
    "teclados": "teclados",
    "mouse": "mouse",
    "bocinas": "bocinas",
    "almacenamiento": "almacenamiento",
    "sillas_gamer": "sillas-gamer",
    "componentes_pc": "componentes",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


@tool("scrape_click")
def scrape_click(category: str, brand: str) -> str:
    """
    Extrae productos de Click (click.gt) usando el endpoint JSON de Shopify.

    Args:
        category: Categoría del producto (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con la lista de productos encontrados.
    """
    category_lower = category.lower().strip()
    brand_lower = brand.lower().strip()

    collection_handle = CLICK_CATEGORIES.get(category_lower)
    if not collection_handle:
        return json.dumps({
            "store": "Click",
            "error": f"Categoría \\'{category}\\' no disponible.",
            "products": []
        })

    products = []
    page = 1

    try:
        while True:
            url = (
                f"https://click.gt/collections/{collection_handle}"
                f"/products.json?page={page}&limit=50"
            )
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            data = response.json()
            shopify_products = data.get("products", [])
            if not shopify_products:
                break

            for product in shopify_products:
                try:
                    name = product.get("title", "")
                    vendor = product.get("vendor", "")

                    if (brand_lower not in name.lower() and
                        brand_lower not in vendor.lower()):
                        continue

                    variants = product.get("variants", [])
                    if not variants:
                        continue

                    variant = variants[0]
                    price_str = variant.get("price", "0")
                    price = float(price_str) if price_str else 0.0
                    available = variant.get("available", False)

                    handle = product.get("handle", "")
                    product_url = f"https://click.gt/products/{handle}" if handle else ""

                    images = product.get("images", [])
                    image_url = images[0].get("src", "") if images else ""

                    products.append({
                        "name": name,
                        "price": price,
                        "available": available,
                        "url": product_url,
                        "image_url": image_url,
                        "store": "Click"
                    })
                except Exception:
                    continue

            page += 1
            if page > 10:
                break

    except requests.RequestException as e:
        return json.dumps({
            "store": "Click",
            "error": f"Error al conectar: {str(e)}",
            "products": products
        })

    return json.dumps({
        "store": "Click",
        "total_found": len(products),
        "products": products
    })
''')

print(f"✅ Creado: {TOOLS_DIR}/click_scraper.py")

# ============================================================
# 6. src/comparegt/tools/macrosistemas_scraper.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "macrosistemas_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
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


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
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
            "error": f"Categoría \\'{category}\\' no disponible.",
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

                    img_el = card.select_one("img")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", "") or img_el.get("data-src", "")

                    out_of_stock = card.select_one(
                        ".outofstock, .out-of-stock, .stock.out-of-stock"
                    )
                    available = out_of_stock is None

                    products.append({
                        "name": name,
                        "price": price,
                        "available": available,
                        "url": product_url,
                        "image_url": image_url,
                        "store": "Macrosistemas"
                    })
                except Exception:
                    continue

            if not found_in_page:
                break
            page += 1
            if page > 10:
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
''')

print(f"✅ Creado: {TOOLS_DIR}/macrosistemas_scraper.py")

# ============================================================
# 7. src/comparegt/tools/pacifiko_scraper.py
# ============================================================
with open(os.path.join(TOOLS_DIR, "pacifiko_scraper.py"), "w", encoding="utf-8") as f:
    f.write('''"""
CompareGT - Herramienta de Scraping para Pacifiko (pacifiko.com)
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

PACIFIKO_CATEGORIES = {
    "laptops": "https://www.pacifiko.com/computacion/laptops",
    "audifonos": "https://www.pacifiko.com/audio/audifonos",
    "monitores": "https://www.pacifiko.com/computacion/monitores",
    "impresoras": "https://www.pacifiko.com/computacion/impresoras",
    "teclados": "https://www.pacifiko.com/computacion/teclados",
    "mouse": "https://www.pacifiko.com/computacion/mouse",
    "bocinas": "https://www.pacifiko.com/audio/bocinas",
    "almacenamiento": "https://www.pacifiko.com/computacion/almacenamiento",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-GT,es;q=0.9",
}


def _parse_price(price_text: str) -> float:
    cleaned = price_text.replace("Q", "").replace("GTQ", "").replace(",", "").strip()
    match = re.search(r"[\\d]+\\.?\\d*", cleaned)
    return float(match.group()) if match else 0.0


@tool("scrape_pacifiko")
def scrape_pacifiko(category: str, brand: str) -> str:
    """
    Extrae productos de Pacifiko (pacifiko.com) para una categoría y marca.

    Args:
        category: Categoría del producto (laptops, audifonos, monitores, etc.)
        brand: Marca a buscar (HP, Lenovo, Dell, etc.)

    Returns:
        JSON string con la lista de productos encontrados.
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
        while True:
            page_url = f"{url}?page={page}" if page > 1 else url
            response = requests.get(page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            product_cards = soup.select(
                ".product-card, .product-item, "
                ".product-layout, .product-grid-item"
            )
            if not product_cards:
                break

            found_in_page = False
            for card in product_cards:
                try:
                    name_el = card.select_one(
                        ".product-title, .product-name, "
                        "h3 a, h4 a, .card-title"
                    )
                    name = name_el.get_text(strip=True) if name_el else ""
                    if not name or brand_lower not in name.lower():
                        continue

                    found_in_page = True

                    price_el = card.select_one(
                        ".product-price, .price, .special-price, .current-price"
                    )
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = _parse_price(price_text)

                    link_el = card.select_one("a[href]")
                    product_url = ""
                    if link_el:
                        href = link_el.get("href", "")
                        if href.startswith("/"):
                            product_url = f"https://www.pacifiko.com{href}"
                        elif href.startswith("http"):
                            product_url = href

                    img_el = card.select_one("img")
                    image_url = ""
                    if img_el:
                        image_url = img_el.get("src", "") or img_el.get("data-src", "")
                        if image_url.startswith("//"):
                            image_url = f"https:{image_url}"

                    out_of_stock = card.select_one(".out-of-stock, .agotado, .sold-out")
                    available = out_of_stock is None

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
            if page > 10:
                break

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

print(f"✅ Creado: {TOOLS_DIR}/pacifiko_scraper.py")

# ============================================================
# RESUMEN
# ============================================================
print("\n" + "=" * 50)
print("🎉 ¡Todos los archivos creados correctamente!")
print("=" * 50)
print(f"\nArchivos en {TOOLS_DIR}/:")
for f_name in os.listdir(TOOLS_DIR):
    print(f"  📄 {f_name}")