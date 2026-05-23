"""
CompareGT - Scraper para MAX (www.max.com.gt)
MAX usa Next.js (plataforma Distelsa). Los datos de productos están embebidos
en el JSON __NEXT_DATA__ dentro de props.pageProps.productsList.
"""

import json
import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

BASE_URL = "https://www.max.com.gt"

# URLs de categoría verificadas (fallback si la URL por marca no funciona)
MAX_CATEGORIES = {
    "laptops": f"{BASE_URL}/electronicos/computacion/laptops",
    "audifonos": f"{BASE_URL}/audio/audifonos",
    "monitores": f"{BASE_URL}/electronicos/computacion/monitores",
    "impresoras": f"{BASE_URL}/electronicos/computacion/impresoras",
    "teclados": f"{BASE_URL}/electronicos/computacion/accesorios-para-computadoras",
    "mouse": f"{BASE_URL}/electronicos/computacion/accesorios-para-computadoras",
    "bocinas": f"{BASE_URL}/audio/bocinas",
    "sillas_gamer": f"{BASE_URL}/electronicos/gaming",
    "componentes_pc": f"{BASE_URL}/electronicos/computacion",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
}

MAX_PRODUCTS = 5

# Palabras clave por categoría para validar que el producto pertenece a la categoría buscada
_CAT_KEYWORDS = {
    "laptops": ["laptop", "notebook", "portatil", "portátil", "inspiron", "victus",
                "omen", "legion", "ideapad", "thinkpad", "pavilion", "aspire",
                "rog", "tuf", "vivobook", "zenbook", "swift", "predator",
                "alienware", "latitude", "precision", "xps"],
    "monitores": ["monitor", "pantalla", "display"],
    "audifonos": ["audifono", "audífono", "headset", "headphone", "earbuds",
                  "earphone", "auricular"],
    "bocinas": ["bocina", "parlante", "speaker", "soundbar", "subwoofer",
                "charge", "flip", "go ", "clip", "partybox", "xtreme",
                "pulse", "boombox"],
    "teclados": ["teclado", "keyboard"],
    "mouse": ["mouse", "ratón", "raton"],
    "sillas_gamer": ["silla", "chair"],
    "almacenamiento": ["ssd", "hdd", "disco duro", "memoria usb", "microsd",
                       "pendrive", "nvme", "storage"],
    "componentes_pc": ["tarjeta de video", "tarjeta gráfica", "gpu", "fuente de poder",
                       "ram ddr", "procesador", "cpu", "motherboard", "placa madre",
                       "gabinete", "cooler", "ventilador"],
    "impresoras": ["impresora", "printer", "multifuncional", "scanner", "escáner"],
}


def _matches_category(name: str, category_lower: str) -> bool:
    """Verifica si el nombre del producto contiene keywords de la categoría."""
    keywords = _CAT_KEYWORDS.get(category_lower, [])
    if not keywords:
        return True
    name_low = name.lower()
    return any(kw in name_low for kw in keywords)


def _extract_products_from_next_data(html: str, brand_lower: str, category_lower: str, store: str, base: str) -> list:
    """Extrae productos del JSON __NEXT_DATA__ embebido en la página Next.js."""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    products_list = (
        data.get("props", {})
            .get("pageProps", {})
            .get("productsList", [])
    )

    results = []
    for product in products_list:
        if len(results) >= MAX_PRODUCTS:
            break
        name = product.get("title", "")
        if brand_lower not in name.lower():
            continue
        if not _matches_category(name, category_lower):
            continue

        sales_price = product.get("salesPrice") or product.get("regularPrice") or {}
        price = float(sales_price.get("value", 0))
        if price == 0:
            continue

        status = product.get("status", "")
        slug = product.get("slug", "")
        results.append({
            "name": name,
            "price": price,
            "available": status == "IN_STOCK",
            "url": f"{base}/producto/{slug}" if slug else "",
            "store": store,
        })
    return results


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

    # URL por marca+categoría (ya filtrada por marca en el sitio)
    brand_category_url = (
        f"{BASE_URL}/marcas/productos-{brand_lower}/{category_lower}-{brand_lower}"
    )
    # URL genérica de categoría como fallback
    category_url = MAX_CATEGORIES.get(category_lower)

    urls_to_try = [brand_category_url]
    if category_url:
        urls_to_try.append(category_url)

    products = []
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                continue
            products = _extract_products_from_next_data(
                response.text, brand_lower, category_lower, "MAX", BASE_URL
            )
            if products:
                break
        except requests.RequestException:
            continue

    return json.dumps({
        "store": "MAX",
        "total_found": len(products),
        "products": products,
    })