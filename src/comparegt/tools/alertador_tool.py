"""
CompareGT - Herramienta del Agente Alertador
Registra bajadas de precio en alerts.json (raíz del proyecto).
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from crewai.tools import tool

# alerts.json vive en la raíz del proyecto (4 niveles arriba de este archivo)
_ALERTS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "alerts.json"
_MIN_PCT_DROP = 3.0


def _load_alerts() -> list:
    if _ALERTS_FILE.exists():
        try:
            return json.loads(_ALERTS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_alerts(alerts: list) -> None:
    _ALERTS_FILE.write_text(
        json.dumps(alerts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@tool("registrar_alerta")
def registrar_alerta(
    product: str,
    store: str,
    old_price: float,
    new_price: float,
    category: str,
    brand: str,
    url: str = "",
) -> str:
    """
    Registra una bajada de precio en alerts.json.
    Solo registra si la bajada porcentual >= 5% o si new_price es el mínimo histórico
    para ese producto.

    Args:
        product:   Nombre del producto comparado.
        store:     Tienda donde se encontró el mejor precio.
        old_price: Precio más alto encontrado (peor precio entre tiendas).
        new_price: Precio más bajo encontrado (mejor precio entre tiendas).
        category:  Categoría del producto (ej: laptops).
        brand:     Marca del producto (ej: HP).
        url:       URL directa del producto en la tienda.

    Returns:
        JSON confirmando si se registró la alerta o indicando el motivo por el que no.
    """
    try:
        old_price = float(old_price)
        new_price = float(new_price)
    except (TypeError, ValueError):
        return json.dumps({"registered": False, "reason": "Precios inválidos"})

    if old_price <= 0 or new_price <= 0 or new_price >= old_price:
        return json.dumps({"registered": False, "reason": "No hay bajada de precio"})

    pct_drop = (old_price - new_price) / old_price * 100
    savings = old_price - new_price

    alerts = _load_alerts()

    # Verificar si new_price es el mínimo histórico para este producto
    historical_min = min(
        (a["new_price"] for a in alerts if a.get("product") == product),
        default=float("inf"),
    )
    is_historical_min = new_price < historical_min

    if pct_drop < _MIN_PCT_DROP and not is_historical_min:
        return json.dumps({
            "registered": False,
            "reason": f"Bajada de {pct_drop:.1f}% menor al umbral de {_MIN_PCT_DROP}%",
        })

    alert = {
        "id":        str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product":   product,
        "store":     store,
        "old_price": round(old_price, 2),
        "new_price": round(new_price, 2),
        "savings":   round(savings, 2),
        "pct_drop":  round(pct_drop, 1),
        "category":  category,
        "brand":     brand,
        "url":       url,
    }

    alerts.append(alert)
    _save_alerts(alerts)

    return json.dumps({
        "registered": True,
        "alert_id":   alert["id"],
        "pct_drop":   alert["pct_drop"],
        "savings":    alert["savings"],
        "message": (
            f"Alerta registrada: {product} en {store} "
            f"bajó {pct_drop:.1f}% (Q{savings:,.0f})"
        ),
    })