#!/usr/bin/env python3
"""
CompareGT - Punto de entrada principal
Ejecuta el sistema multi-agente de comparación de precios.
"""

import sys
import json
from comparegt.crew import CompareGTCrew


def run():
    """Ejecutar CompareGT con parámetros del usuario."""

    # Parámetros de búsqueda (estos vendrán de Streamlit después)
    inputs = {
        "category": "laptops",
        "brand": "HP",
        "budget": "Q5,000 - Q8,000",
        "use_type": "Estudio/Oficina",
    }

    print("=" * 60)
    print("CompareGT - Comparador Inteligente de Precios")
    print("=" * 60)
    print(f"Categoria: {inputs['category']}")
    print(f"Marca: {inputs['brand']}")
    print(f"Presupuesto: {inputs['budget']}")
    print(f"Uso: {inputs['use_type']}")
    print("=" * 60)
    print("\nIniciando agentes...\n")

    try:
        crew_instance = CompareGTCrew()
        result = crew_instance.crew().kickoff(inputs=inputs)

        print("\n" + "=" * 60)
        print("Comparacion completada!")
        print("=" * 60)
        print("\nRESULTADO FINAL:")
        print("-" * 60)
        print(result)

    except Exception as e:
        print(f"\nError al ejecutar CompareGT: {e}")
        raise


def test_scraper():
    """Prueba rápida de un scraper individual."""
    from comparegt.tools.max_scraper import scrape_max

    print("Probando scraper de MAX...")
    result = scrape_max.run(category="laptops", brand="HP")
    data = json.loads(result)

    print(f"Tienda: {data.get('store')}")
    print(f"Productos encontrados: {data.get('total_found', 0)}")

    for p in data.get("products", [])[:3]:
        print(f"\n  -> {p['name']}")
        print(f"     Q{p['price']:,.2f}")
        print(f"     {'Disponible' if p['available'] else 'Agotado'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_scraper()
    else:
        run()