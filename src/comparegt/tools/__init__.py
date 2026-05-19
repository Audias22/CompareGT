"""CompareGT - Herramientas de Scraping para tiendas guatemaltecas."""

from .max_scraper import scrape_max
from .tecnofacil_scraper import scrape_tecnofacil
from .click_scraper import scrape_click
from .pacifiko_scraper import scrape_pacifiko
from .macrosistemas_scraper import scrape_macrosistemas

__all__ = [
    "scrape_max",
    "scrape_tecnofacil",
    "scrape_click",
    "scrape_pacifiko",
    "scrape_macrosistemas",
]
