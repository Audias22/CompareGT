"""
CompareGT - Interfaz Web con Streamlit v2
Comparador Inteligente de Precios de Electrónica en Guatemala
Wizard de 7 pasos — diseño premium dark mode.
"""

import sys
import os
import json
import re
import time
import threading

from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
_env_loaded = False
for _p in [
    os.path.join(_root, ".env"),
    os.path.join(_root, ".venv", ".env"),
    os.path.join(_root, "src", "comparegt", ".env"),
]:
    if os.path.exists(_p):
        load_dotenv(_p, override=True)
        _env_loaded = True
        print(f"[DEBUG] .env cargado desde: {_p}")
        break

if not _env_loaded or not os.environ.get("OPENAI_API_KEY"):
    st.error("⚠️ No se encontró el archivo .env con las API keys. Crea un archivo .env en la raíz del proyecto.")
    st.stop()

print(f"[DEBUG] OPENAI_API_KEY present: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"[DEBUG] OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
print(f"[DEBUG] OPENAI_MODEL_NAME: {os.environ.get('OPENAI_MODEL_NAME')}")

sys.path.insert(0, os.path.join(_root, "src"))

import streamlit as st
import streamlit.components.v1 as components

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CompareGT - Comparador de Precios",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*,body,.stApp{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important}
            .stApp{
    background:#0f172a!important;
    background-image:
        linear-gradient(to right,#4f4f4f2e 1px,transparent 1px),
        linear-gradient(to bottom,#4f4f4f2e 1px,transparent 1px)!important;
    background-size:14px 24px!important;
}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stSidebar"]{display:none!important}
.main .block-container{padding:1.5rem 2.5rem 2rem;max-width:1100px;background:#080C14}

/* ── Header ── */
.cgt-header{
    background:linear-gradient(135deg,#0A1628 0%,#0D2445 50%,#0A1628 100%);
    padding:2rem 2rem 1.6rem;border-radius:16px;margin-bottom:1.8rem;
    text-align:center;border:1px solid #1E3A5F;
}
.cgt-header h1{
    color:#F0F6FF;font-size:2.1rem;font-weight:800;
    margin:0;letter-spacing:-0.03em;
    display:flex;align-items:center;justify-content:center;gap:12px;
}
.logo-badge{
    display:inline-flex;align-items:center;justify-content:center;
    width:42px;height:42px;
    background:linear-gradient(135deg,#00D4FF,#0066FF);
    border-radius:10px;font-size:1.2rem;flex-shrink:0;
}
.cgt-header .subtitle{color:#6B8CAE;font-size:0.92rem;margin:0.5rem 0 1.1rem;font-weight:400}
.cgt-header .stores{display:flex;justify-content:center;gap:8px;flex-wrap:wrap}
.cgt-header .store-tag{
    background:rgba(0,212,255,0.07);color:#00D4FF;
    border:1px solid rgba(0,212,255,0.2);
    padding:4px 13px;border-radius:20px;font-size:0.77rem;font-weight:600;
}

/* ── Step dots ── */
.step-bar{display:flex;justify-content:center;align-items:center;gap:8px;margin-bottom:1.8rem}
.step-dot{width:12px;height:12px;border-radius:50%;background:#1E3A5F;transition:all 0.25s}
.step-dot.active{background:#00D4FF;width:28px;border-radius:6px;box-shadow:0 0 12px rgba(0,212,255,0.5)}
.step-dot.done{background:#00E676}

/* ── Section titles ── */
.sec-title{font-size:1.18rem;font-weight:800;color:#F0F6FF;margin-bottom:0.2rem;letter-spacing:-0.02em}
.sec-sub{font-size:0.85rem;color:#6B8CAE;margin-bottom:1.3rem;font-weight:400}

/* ── Category cards (paso 1) ── */
button[data-testid="baseButton-secondary"][aria-label*="💻"],
button[data-testid="baseButton-secondary"][aria-label*="🎧"],
button[data-testid="baseButton-secondary"][aria-label*="🖥"],
button[data-testid="baseButton-secondary"][aria-label*="🖨"],
button[data-testid="baseButton-secondary"][aria-label*="⌨"],
button[data-testid="baseButton-secondary"][aria-label*="🖱"],
button[data-testid="baseButton-secondary"][aria-label*="🔊"],
button[data-testid="baseButton-secondary"][aria-label*="💾"],
button[data-testid="baseButton-secondary"][aria-label*="🪑"],
button[data-testid="baseButton-secondary"][aria-label*="🔧"]{
    background:#0F1923!important;border:1px solid #1E3A5F!important;
    border-radius:16px!important;min-height:100px!important;
    color:#F0F6FF!important;font-size:0.85rem!important;font-weight:700!important;
    transition:all .2s ease!important;
    white-space:pre-wrap!important;line-height:1.6!important;
}
button[data-testid="baseButton-secondary"][aria-label*="💻"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🎧"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🖥"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🖨"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="⌨"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🖱"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🔊"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="💾"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🪑"]:hover,
button[data-testid="baseButton-secondary"][aria-label*="🔧"]:hover{
    border-color:#00D4FF!important;background:#0A1628!important;
    box-shadow:0 8px 32px rgba(0,212,255,0.15)!important;
    transform:translateY(-3px)!important;color:#00D4FF!important;
}

/* ── Brand + Budget pills ── */
button[data-testid="baseButton-secondary"]{
    background:#0F1923!important;color:#6B8CAE!important;
    border:1px solid #1E3A5F!important;border-radius:100px!important;
    font-size:0.88rem!important;font-weight:500!important;
    transition:all .18s ease!important;width:100%!important;
}
button[data-testid="baseButton-secondary"]:hover{
    background:rgba(0,212,255,0.08)!important;border-color:#00D4FF!important;
    color:#00D4FF!important;
}

/* ── Use type cards ── */
button[aria-label*="Estudio/Oficina"]{background:#0D1E3D!important;color:#4D9FFF!important;border:1px solid #1E4080!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Gaming"]{background:#1A0D2E!important;color:#A855F7!important;border:1px solid #4B1D8C!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Diseño/Edición"]{background:#2E1A0D!important;color:#FF8C42!important;border:1px solid #8C3D1D!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Música"]{background:#0D2E2E!important;color:#00D4FF!important;border:1px solid #1D6B6B!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Llamadas/Trabajo"]{background:#0D2E1A!important;color:#00E676!important;border:1px solid #1D6B3D!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Uso en casa"]{background:#0D2E2E!important;color:#00D4FF!important;border:1px solid #1D6B6B!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Portátil/Outdoor"]{background:#2E1A0D!important;color:#FF8C42!important;border:1px solid #8C3D1D!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Oficina/Escritura"]{background:#0D1E3D!important;color:#4D9FFF!important;border:1px solid #1E4080!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Hogar"]{background:#0D2E2E!important;color:#00D4FF!important;border:1px solid #1D6B6B!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Oficina/Empresa"]{background:#2E1A0D!important;color:#FF8C42!important;border:1px solid #8C3D1D!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Alta velocidad"]{background:#1A0D2E!important;color:#A855F7!important;border:1px solid #4B1D8C!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Backup/Archivo"]{background:#0D1E3D!important;color:#4D9FFF!important;border:1px solid #1E4080!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Todas las opciones"]{background:#161B26!important;color:#6B8CAE!important;border:1px solid #2D3748!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}
button[aria-label*="Oficina"]{background:#0D1E3D!important;color:#4D9FFF!important;border:1px solid #1E4080!important;border-radius:14px!important;min-height:90px!important;font-size:1rem!important;font-weight:700!important;}

/* ── Volver ── */
button[aria-label="← Volver"]{
    background:transparent!important;color:#6B8CAE!important;
    border:1px solid #1E3A5F!important;border-radius:8px!important;
    font-size:0.83rem!important;font-weight:500!important;
    width:100%!important;transition:all 0.15s!important;
}
button[aria-label="← Volver"]:hover{
    background:rgba(30,58,95,0.3)!important;color:#F0F6FF!important;border-color:#2D5080!important;
}

/* ── Comparar ── */
button[aria-label*="Comparar Precios"]{
    background:linear-gradient(90deg,#0066FF,#00D4FF)!important;
    color:white!important;border:none!important;border-radius:12px!important;
    min-height:56px!important;font-size:0.95rem!important;font-weight:800!important;
    text-transform:uppercase!important;letter-spacing:0.05em!important;
    box-shadow:0 4px 24px rgba(0,212,255,0.3)!important;width:100%!important;transition:all 0.2s!important;
}
button[aria-label*="Comparar Precios"]:hover{
    box-shadow:0 8px 32px rgba(0,212,255,0.45)!important;transform:translateY(-1px)!important;
}

/* ── Nueva búsqueda ── */
button[aria-label*="Nueva búsqueda"]{
    background:transparent!important;color:#00D4FF!important;
    border:1px solid #00D4FF!important;border-radius:10px!important;
    font-size:0.95rem!important;font-weight:600!important;
    width:100%!important;transition:all 0.15s!important;
}
button[aria-label*="Nueva búsqueda"]:hover{background:rgba(0,212,255,0.08)!important}

/* ── Limpiar ── */
button[aria-label*="Limpiar"]{
    background:transparent!important;color:#FF4757!important;
    border:1px solid #FF4757!important;border-radius:8px!important;
    font-size:0.8rem!important;font-weight:600!important;
    width:100%!important;transition:all 0.15s!important;
}
button[aria-label*="Limpiar"]:hover{background:rgba(255,71,87,0.08)!important}

/* ── Summary card ── */
.summary-card{
    background:#0F1923;border:1px solid #1E3A5F;border-left:4px solid #00D4FF;
    border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.4rem;
}
.summary-label{
    font-size:0.71rem;color:#6B8CAE;text-transform:uppercase;
    letter-spacing:0.08em;font-weight:600;margin-bottom:10px;
}
.summary-chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{
    background:linear-gradient(135deg,rgba(0,212,255,0.12),rgba(0,102,255,0.12));
    border:1px solid rgba(0,212,255,0.25);
    color:#00D4FF;padding:5px 14px;border-radius:20px;font-size:0.82rem;font-weight:600;
}

/* ── Metrics ── */
.metrics-row{display:flex;gap:12px;margin-bottom:1.5rem;flex-wrap:wrap}
.metric-box{
    flex:1;min-width:150px;background:#0F1923;border:1px solid #1E3A5F;
    border-radius:12px;padding:1.1rem 1.3rem;text-align:center;
}
.metric-box.m1{border-bottom:3px solid #00D4FF}
.metric-box.m2{border-bottom:3px solid #0066FF}
.metric-box.m3{border-bottom:3px solid #00E676}
.metric-box .mlabel{font-size:0.68rem;color:#6B8CAE;text-transform:uppercase;letter-spacing:0.08em;font-weight:600}
.metric-box .mvalue{font-size:1.75rem;font-weight:800;color:#00D4FF;margin:4px 0;letter-spacing:-0.03em}
.metric-box.m2 .mvalue{color:#0066FF}
.metric-box.m3 .mvalue{color:#00E676}
.metric-box .msub{font-size:0.73rem;color:#6B8CAE}

/* ── Expanders ── */
details[data-testid="stExpander"]{
    background:#0F1923!important;border:1px solid #1E3A5F!important;
    border-radius:10px!important;margin-bottom:6px!important;
}
[data-testid="stExpanderDetails"]{background:#080C14!important}
summary[data-testid="stExpanderToggle"]{
    color:#F0F6FF!important;font-weight:600!important;
    overflow:hidden!important;
    text-overflow:ellipsis!important;
    padding-left:16px!important;
}

/* ── Alerts ── */
[data-testid="stAlert"]{background:#0F1923!important;border-radius:10px!important}

/* ── Footer ── */
.cgt-footer{
    text-align:center;color:#2D5080;font-size:0.73rem;
    padding:1.5rem 0 0.5rem;border-top:1px solid #0F1923;margin-top:2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Data constants ─────────────────────────────────────────────────────────────

CATEGORIES = [
    ("laptops",        "💻", "Laptops"),
    ("audifonos",      "🎧", "Audífonos"),
    ("monitores",      "🖥️", "Monitores"),
    ("impresoras",     "🖨️", "Impresoras"),
    ("teclados",       "⌨️", "Teclados"),
    ("mouse",          "🖱️", "Mouse"),
    ("bocinas",        "🔊", "Bocinas"),
    ("almacenamiento", "💾", "Almacen."),
    ("sillas_gamer",   "🪑", "Sillas Gamer"),
    ("componentes_pc", "🔧", "Componentes"),
]

BRANDS = {
    "laptops":        ["HP", "Lenovo", "Dell", "Asus", "Acer", "MSI", "Apple"],
    "audifonos":      ["JBL", "Sony", "Logitech", "HyperX", "Razer", "Skullcandy"],
    "monitores":      ["LG", "Samsung", "Dell", "Asus", "Acer", "BenQ"],
    "impresoras":     ["HP", "Epson", "Canon", "Brother"],
    "teclados":       ["Logitech", "Razer", "HyperX", "Redragon", "Corsair"],
    "mouse":          ["Logitech", "Razer", "HyperX", "Redragon", "Corsair"],
    "bocinas":        ["JBL", "Sony", "Bose", "Marshall", "Harman Kardon"],
    "almacenamiento": ["Kingston", "Samsung", "WD", "Seagate", "SanDisk"],
    "sillas_gamer":   ["Cougar", "Xigmatek", "Primus", "DXRacer"],
    "componentes_pc": ["EVGA", "Corsair", "ASUS", "MSI", "Gigabyte"],
}

BUDGETS = {
    "laptops":        ["Sin límite", "Menos de Q5,000", "Q5,000 - Q8,000", "Q8,000 - Q12,000", "Más de Q12,000"],
    "audifonos":      ["Sin límite", "Menos de Q200", "Q200 - Q500", "Q500 - Q1,000", "Más de Q1,000"],
    "monitores":      ["Sin límite", "Menos de Q2,000", "Q2,000 - Q4,000", "Q4,000 - Q8,000", "Más de Q8,000"],
    "impresoras":     ["Sin límite", "Menos de Q1,000", "Q1,000 - Q3,000", "Q3,000 - Q5,000", "Más de Q5,000"],
    "teclados":       ["Sin límite", "Menos de Q200", "Q200 - Q500", "Q500 - Q1,000", "Más de Q1,000"],
    "mouse":          ["Sin límite", "Menos de Q150", "Q150 - Q400", "Q400 - Q800", "Más de Q800"],
    "bocinas":        ["Sin límite", "Menos de Q300", "Q300 - Q800", "Q800 - Q2,000", "Más de Q2,000"],
    "almacenamiento": ["Sin límite", "Menos de Q200", "Q200 - Q500", "Q500 - Q1,000", "Más de Q1,000"],
    "sillas_gamer":   ["Sin límite", "Menos de Q1,500", "Q1,500 - Q3,000", "Q3,000 - Q5,000", "Más de Q5,000"],
    "componentes_pc": ["Sin límite", "Menos de Q500", "Q500 - Q2,000", "Q2,000 - Q5,000", "Más de Q5,000"],
}

USE_TYPES_BY_CATEGORY = {
    "laptops": [
        ("Estudio/Oficina",    "💻", "#0077B6", "Productividad y tareas cotidianas"),
        ("Gaming",             "🎮", "#7B2D8B", "Alto rendimiento gráfico"),
        ("Diseño/Edición",     "⚙️", "#B85042", "Procesamiento de video e imagen"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "monitores": [
        ("Estudio/Oficina",    "💻", "#0077B6", "Productividad y tareas cotidianas"),
        ("Gaming",             "🎮", "#7B2D8B", "Alta tasa de refresco y baja latencia"),
        ("Diseño/Edición",     "⚙️", "#B85042", "Color preciso y alta resolución"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "componentes_pc": [
        ("Estudio/Oficina",    "💻", "#0077B6", "Rendimiento cotidiano y productividad"),
        ("Gaming",             "🎮", "#7B2D8B", "Máximo rendimiento en juegos"),
        ("Diseño/Edición",     "⚙️", "#B85042", "Procesamiento gráfico y de video"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "sillas_gamer": [
        ("Gaming",             "🎮", "#7B2D8B", "Largas sesiones de juego"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "audifonos": [
        ("Música",             "🎵", "#0077B6", "Calidad de audio y bajos potentes"),
        ("Gaming",             "🎮", "#7B2D8B", "Sonido posicional y micrófono"),
        ("Llamadas/Trabajo",   "📞", "#2D6A4F", "Claridad vocal y cancelación de ruido"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "bocinas": [
        ("Uso en casa",        "🏠", "#0077B6", "Potencia y calidad para interiores"),
        ("Portátil/Outdoor",   "🎒", "#B85042", "Resistente y con batería integrada"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "teclados": [
        ("Gaming",             "🎮", "#7B2D8B", "Switches mecánicos y RGB"),
        ("Oficina/Escritura",  "⌨️", "#0077B6", "Silencioso y cómodo para largas horas"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "mouse": [
        ("Gaming",             "🎮", "#7B2D8B", "Alta precisión y botones programables"),
        ("Oficina",            "💼", "#0077B6", "Ergonómico y silencioso"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "impresoras": [
        ("Hogar",              "🏠", "#0077B6", "Fotos y documentos ocasionales"),
        ("Oficina/Empresa",    "🏢", "#B85042", "Alto volumen y bajo costo por página"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
    "almacenamiento": [
        ("Alta velocidad",     "⚡", "#7B2D8B", "NVMe / SSD para máximo rendimiento"),
        ("Backup/Archivo",     "💾", "#0077B6", "Gran capacidad a bajo costo"),
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ],
}

STORE_COLORS = {
    "MAX":           "#003F8A",
    "Tecno Fácil":   "#D62828",
    "Click":         "#F77F00",
    "Pacifiko":      "#2D6A4F",
    "Macrosistemas": "#7B2D8B",
}
ALL_STORES = ["MAX", "Tecno Fácil", "Click", "Pacifiko"]

# ── Utilities ──────────────────────────────────────────────────────────────────

def _parse_crew_output(raw) -> dict | None:
    """Extrae el JSON del output del crew (directo o dentro de ```json``` blocks)."""
    text = str(raw).strip()
    block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if block:
        try:
            return json.loads(block.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    return None


def _dedup_prices(all_prices: list) -> list:
    """Por tienda: si aparece más de una vez, quedar con el menor precio."""
    seen: dict = {}
    for entry in all_prices:
        store = entry.get("store", "")
        price = entry.get("price", 0)
        if store not in seen or price < seen[store].get("price", 0):
            seen[store] = entry
    return list(seen.values())


def _parse_budget_range(budget_str: str) -> tuple:
    if budget_str == "Sin límite":
        return (0.0, float("inf"))
    m = re.match(r"Menos de Q([\d,]+)", budget_str)
    if m:
        return (0.0, float(m.group(1).replace(",", "")))
    m = re.match(r"Más de Q([\d,]+)", budget_str)
    if m:
        return (float(m.group(1).replace(",", "")), float("inf"))
    m = re.match(r"Q([\d,]+)\s*-\s*Q([\d,]+)", budget_str)
    if m:
        return (float(m.group(1).replace(",", "")), float(m.group(2).replace(",", "")))
    return (0.0, float("inf"))


def _filter_by_budget(comparisons: list, budget_str: str) -> list:
    """Filtra los grupos cuyo mejor precio esté fuera del rango seleccionado."""
    if budget_str == "Sin límite":
        return comparisons
    lo, hi = _parse_budget_range(budget_str)
    return [c for c in comparisons
            if lo <= c.get("best_price", {}).get("price", 0) <= hi]



def _validate_comparisons(data: dict | None) -> dict | None:
    """Descarta comparisons alucinados por el LLM.
    - Elimina comparisons donde algún precio es 0 o negativo.
    - Elimina comparisons donde el nombre del producto está vacío.
    - Recalcula best_price, worst_price y savings desde all_prices reales.
    """
    if not data or "comparisons" not in data:
        return data

    cleaned = []
    for comp in data["comparisons"]:
        all_prices = comp.get("all_prices", [])
        if not all_prices:
            continue
        # Descartar si algún precio no es numérico positivo
        valid_prices = [
            e for e in all_prices
            if isinstance(e.get("price"), (int, float)) and e["price"] > 0
        ]
        if not valid_prices:
            continue
        # Descartar si no tiene nombre de producto
        product_name = comp.get("product", "").strip()
        if not product_name:
            continue

        # Recalcular best/worst/savings desde los datos reales
        avail = [e for e in valid_prices if e.get("available", True)]
        all_p = [e["price"] for e in valid_prices]

        if avail:
            best_entry = min(avail, key=lambda x: x["price"])
            comp["best_price"] = {"store": best_entry["store"], "price": best_entry["price"]}
        else:
            cheapest = min(valid_prices, key=lambda x: x["price"])
            comp["best_price"] = {"store": cheapest["store"], "price": cheapest["price"]}

        most_expensive = max(valid_prices, key=lambda x: x["price"])
        comp["worst_price"] = {"store": most_expensive["store"], "price": most_expensive["price"]}
        comp["savings"] = max(all_p) - min(all_p) if len(all_p) >= 2 else 0
        comp["all_prices"] = valid_prices
        cleaned.append(comp)

    data["comparisons"] = cleaned
    return data if cleaned else data


def _h(text: str) -> str:
    """HTML-escape básico."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _run_crew(category: str, brand: str, budget: str, use_type: str):
    from comparegt.crew import kickoff_with_fallback
    return kickoff_with_fallback(inputs={
        "category": category,
        "brand":    brand,
        "budget":   budget,
        "use_type": use_type,
    })


def _cat_name(key: str) -> str:
    return next((n for k, ic, n in CATEGORIES if k == key), key)


def _cat_icon(key: str) -> str:
    return next((ic for k, ic, n in CATEGORIES if k == key), "")


def _hex_rgba(hex_color: str, alpha: float) -> str:
    """Convierte color hex a rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ── HTML builders ──────────────────────────────────────────────────────────────

def _agent_cards_html(phase: int) -> str:
    """
    HTML para las 4 tarjetas de progreso de agentes.
    phase: 0=Rastreador activo, 1=Emparejador, 2=Analista, 3=todos completados
    """
    agents = [
        ("1", "🔎", "Rastreador",  "Buscando en tiendas"),
        ("2", "🤖", "Emparejador", "Identificando productos"),
        ("3", "📊", "Analista",    "Comparando precios"),
        ("4", "🔔", "Alertador",   "No activado"),
    ]
    parts = []
    for i, (num, icon, name, desc) in enumerate(agents):
        if i == 3:
            bg, border = "#0F1923", "#1E3A5F"
            status = "○ No activado"
            s_color, n_color, d_color = "#1E3A5F", "#6B8CAE", "#6B8CAE"
            anim = ""
        elif i < phase:
            bg, border = "#091A0F", "#00E676"
            status = "✓ Completado"
            s_color, n_color, d_color = "#00E676", "#00E676", "#6B8CAE"
            anim = ""
        elif i == phase:
            bg, border = "#050C1A", "#00D4FF"
            status = "↻ En progreso"
            s_color, n_color, d_color = "#00D4FF", "#00D4FF", "#F0F6FF"
            anim = "animation:cgt-pulse 2s ease-in-out infinite;"
        else:
            bg, border = "#0F1923", "#1E3A5F"
            status = "○ Pendiente"
            s_color, n_color, d_color = "#1E3A5F", "#6B8CAE", "#6B8CAE"
            anim = ""

        arrow = (
            f'<div style="color:#1E3A5F;font-size:1.3rem;padding:0 3px;align-self:center;">→</div>'
            if i < 3 else ""
        )
        parts.append(
            f'<div style="flex:1;background:{bg};border:2px solid {border};'
            f'border-radius:12px;padding:16px 10px;text-align:center;min-width:110px;{anim}">'
            f'<div style="font-size:1.8rem;line-height:1;margin-bottom:6px;">{icon}</div>'
            f'<div style="font-size:0.6rem;color:#6B8CAE;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px;">AGENTE {num}</div>'
            f'<div style="font-weight:700;color:{n_color};font-size:0.9rem;margin-bottom:3px;">{name}</div>'
            f'<div style="font-size:0.7rem;color:{d_color};margin-bottom:8px;">{desc}</div>'
            f'<div style="font-size:0.7rem;font-weight:700;color:{s_color};">{status}</div>'
            f'</div>{arrow}'
        )

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>'
        'body{margin:0;padding:4px 0;background:#080C14;'
        'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}'
        '@keyframes cgt-pulse{'
        '0%,100%{box-shadow:0 0 0 0 rgba(0,212,255,0.35)}'
        '50%{box-shadow:0 0 0 8px rgba(0,212,255,0)}'
        '}'
        '</style>'
        '</head><body>'
        '<div style="display:flex;align-items:stretch;gap:6px;">'
        + "".join(parts)
        + '</div></body></html>'
    )


def _store_search_url(store: str, product_name: str) -> str:
    """Construye una URL de búsqueda en la tienda dado el nombre del producto."""
    from urllib.parse import quote_plus
    q = quote_plus(product_name)
    store_l = store.lower()
    if "pacifiko" in store_l:
        return f"https://www.pacifiko.com/index.php?route=product/search&search={q}"
    if "max" in store_l:
        return f"https://www.max.com.gt/buscar?q={q}"
    if "tecno" in store_l:
        return f"https://www.tecnofacil.com.gt/buscar?q={q}"
    if "click" in store_l:
        return f"https://click.gt/search?q={q}"
    if "macro" in store_l:
        return f"https://www.macrosistemas.com/?s={q}"
    return ""


STORE_DOMAINS = {
    "pacifiko": "https://www.pacifiko.com",
    "max":      "https://www.max.com.gt",
    "tecno":    "https://www.tecnofacil.com.gt",
    "click":    "https://click.gt",
    "macro":    "https://www.macrosistemas.com",
}


def _normalize_url(url: str, store: str) -> str:
    """Si la URL es relativa (no empieza con http), antepone el dominio de la tienda."""
    url = url.strip()
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    store_l = store.lower()
    for key, domain in STORE_DOMAINS.items():
        if key in store_l:
            return domain + (url if url.startswith("/") else "/" + url)
    return url


def _pivot_table_html(comparisons: list) -> tuple:
    """
    Tabla pivoteada: columnas = tiendas.
    Retorna (html_str, height_px).

    - Nombre del producto: solo texto, sin link (el producto puede estar en varias tiendas).
    - Cada celda de precio: link a la URL directa del producto en esa tienda (campo "url"
      del scraper), o fallback a búsqueda en esa tienda si no hay URL directa.
    - Mejor precio (mínimo disponible): fondo verde + checkmark.
    - Empate: AMBAS celdas en verde.
    - Agotado: fondo rosa + "No disp." sin link.
    - Sin datos para esa tienda: "—".
    """
    # Tiendas que realmente aparecen en los datos
    stores_in_data: set = set()
    for comp in comparisons:
        for e in _dedup_prices(comp.get("all_prices", [])):
            stores_in_data.add(e.get("store", ""))

    visible = [s for s in ALL_STORES if s in stores_in_data] or ALL_STORES

    # Encabezado
    th_product = (
        '<th style="padding:10px 14px;text-align:left;min-width:200px;'
        'background:#1E2D3D;color:white;font-weight:700;">'
        'Producto</th>'
    )
    th_stores = ""
    for s in visible:
        c = STORE_COLORS.get(s, "#555")
        th_stores += (
            f'<th style="padding:10px 14px;text-align:center;min-width:110px;'
            f'background:{c};color:white;font-weight:700;">'
            f'{_h(s)}</th>'
        )

    # Filas
    rows = ""
    for ri, comp in enumerate(comparisons):
        name = _h(comp.get("product", ""))
        all_prices = _dedup_prices(comp.get("all_prices", []))
        price_map = {e["store"]: e for e in all_prices}
        raw_product = comp.get("product", "")

        avail_prices = [
            e["price"] for e in all_prices
            if e.get("available", True) and e.get("price", 0) > 0
        ]
        min_p = min(avail_prices) if avail_prices else None

        row_bg = "#ffffff" if ri % 2 == 0 else "#f8fafc"

        td_name = (
            f'<td style="padding:10px 14px;background:{row_bg};'
            f'font-size:0.86rem;font-weight:500;color:#1A202C;'
            f'border-bottom:1px solid #E2E8F0;">{name}</td>'
        )

        td_stores = ""
        for s in visible:
            bdr = "border-bottom:1px solid #E2E8F0;border-left:1px solid #E2E8F0;"
            if s not in price_map:
                td_stores += (
                    f'<td style="padding:10px 14px;text-align:center;'
                    f'background:#fafafa;{bdr}">'
                    f'<span style="color:#CBD5E0;font-size:0.82rem;">&#8212;</span></td>'
                )
            else:
                e = price_map[s]
                price = e.get("price", 0)
                avail = e.get("available", True)

                direct_url = _normalize_url(e.get("url", ""), s)
                cell_url = direct_url if direct_url else _store_search_url(s, raw_product)

                if not avail:
                    td_stores += (
                        f'<td style="padding:10px 14px;text-align:center;'
                        f'background:#fff5f5;{bdr}">'
                        f'<span style="color:#D62828;font-size:0.8rem;font-weight:500;">'
                        f'No disp.</span></td>'
                    )
                elif min_p is not None and abs(price - min_p) < 0.01:
                    inner = (
                        f'<span style="font-weight:700;color:#1a7f37;font-size:0.98rem;">'
                        f'Q{price:,.0f}</span><br>'
                        f'<span style="font-size:0.72rem;color:#1a7f37;">&#10003; mejor</span>'
                    )
                    linked = (
                        f'<a href="{cell_url}" target="_blank" '
                        f'style="text-decoration:none;display:block;">{inner}</a>'
                        if cell_url else inner
                    )
                    td_stores += (
                        f'<td style="padding:10px 14px;text-align:center;'
                        f'background:#d4edda;{bdr}">{linked}</td>'
                    )
                else:
                    inner = (
                        f'<span style="font-size:0.94rem;color:#00B4D8;'
                        f'text-decoration:underline dotted;">Q{price:,.0f}</span>'
                    )
                    linked = (
                        f'<a href="{cell_url}" target="_blank" '
                        f'style="text-decoration:none;display:block;'
                        f'text-align:center;">{inner}</a>'
                        if cell_url else inner
                    )
                    td_stores += (
                        f'<td style="padding:10px 14px;text-align:center;'
                        f'background:{row_bg};{bdr}">{linked}</td>'
                    )

        rows += f"<tr>{td_name}{td_stores}</tr>\n"

    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<base target="_blank">'
        '<style>'
        'body{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}'
        'table{width:100%;border-collapse:collapse;'
        'border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.09);}'
        'tr:hover td{filter:brightness(0.965);}'
        'a:hover span{opacity:0.82;}'
        '</style></head><body>'
        f'<table><thead><tr>{th_product}{th_stores}</tr></thead>'
        f'<tbody>{rows}</tbody></table>'
        '</body></html>'
    )
    height = 56 + len(comparisons) * 54 + 16
    return html, height

# ── Session state defaults ─────────────────────────────────────────────────────

_DEFAULTS = {
    "step":               1,
    "category":           None,
    "brand":              None,
    "budget":             None,
    "use_type":           None,
    "result_data":        None,
    "error_msg":          None,
    "crew_started":       False,
    "result_holder":      {},
    "done_event":         None,
    "alertador_started":  False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="cgt-header">
  <h1><span class="logo-badge">🔍</span> CompareGT</h1>
  <p class="subtitle">Comparador Inteligente de Precios de Electrónica en Guatemala</p>
  <div class="stores">
    <span class="store-tag">MAX</span>
    <span class="store-tag">Tecno Fácil</span>
    <span class="store-tag">Click</span>
    <span class="store-tag">Pacifiko</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Step dots ──────────────────────────────────────────────────────────────────

_step = st.session_state.step
if _step <= 7:
    _dots = ""
    for _i in range(1, 6):
        if _i < _step:
            _cls = "done"
        elif _i == min(_step, 5):
            _cls = "active"
        else:
            _cls = ""
        _dots += f'<div class="step-dot {_cls}"></div>'
    st.markdown(f'<div class="step-bar">{_dots}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Categorías (grid de cards premium)
# ══════════════════════════════════════════════════════════════════════════════

if _step == 1:
    st.markdown('<div class="sec-title">¿Qué tipo de producto estás buscando?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Seleccioná una categoría para comenzar</div>', unsafe_allow_html=True)

    _row1 = st.columns(5)
    _row2 = st.columns(5)
    for _i, (_key, _icon, _name) in enumerate(CATEGORIES):
        _col = _row1[_i] if _i < 5 else _row2[_i - 5]
        _label = {"almacenamiento": "Almacen.", "componentes_pc": "Componentes", "sillas_gamer": "Sillas Gamer"}.get(_key, _name)
        with _col:
            if st.button(f"{_icon}\n{_label}", key=f"cat_{_key}", use_container_width=True):
                st.session_state.category = _key
                st.session_state.brand    = None
                st.session_state.budget   = None
                st.session_state.use_type = None
                st.session_state.step     = 2
                st.rerun()

elif _step == 2:
    _ck = st.session_state.category
    st.markdown(f'<div class="sec-title">{_cat_icon(_ck)} {_cat_name(_ck)} — ¿Cuál es tu marca preferida?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Elegí la marca que querés comparar entre tiendas</div>', unsafe_allow_html=True)

    _brands = BRANDS.get(_ck, [])
    _ncols = min(len(_brands), 7)
    _bcols = st.columns(_ncols)
    for _i, _b in enumerate(_brands):
        with _bcols[_i % _ncols]:
            if st.button(_b, key=f"brand_{_b}", use_container_width=True):
                st.session_state.brand = _b
                st.session_state.step  = 3
                st.rerun()
    st.write("")
    if st.button("← Volver", key="back_2"):
        st.session_state.step = 1
        st.rerun()

elif _step == 3:
    st.markdown('<div class="sec-title">💰 ¿Cuál es tu rango de presupuesto?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Usaremos esto para filtrar los resultados</div>', unsafe_allow_html=True)

    _budgets = BUDGETS.get(st.session_state.category, [])
    _pcols = st.columns(len(_budgets))
    for _i, _bg in enumerate(_budgets):
        with _pcols[_i]:
            if st.button(_bg, key=f"budget_{_bg}", use_container_width=True):
                st.session_state.budget = _bg
                st.session_state.step   = 4
                st.rerun()
    st.write("")
    if st.button("← Volver", key="back_3"):
        st.session_state.step = 2
        st.rerun()

elif _step == 4:
    st.markdown('<div class="sec-title">🎯 ¿Para qué vas a usar el producto?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Ayuda al agente a hacer recomendaciones más precisas</div>', unsafe_allow_html=True)

    _ck = st.session_state.category
    _use_options = USE_TYPES_BY_CATEGORY.get(_ck, [
        ("Todas las opciones", "🔍", "#4A5568", "Sin filtro de uso específico"),
    ])
    _uc1, _uc2 = st.columns(2)
    for _i, (_uname, _uicon, _ucolor, _usub) in enumerate(_use_options):
        _ucol = _uc1 if _i % 2 == 0 else _uc2
        with _ucol:
            if st.button(f"{_uicon} {_uname}", key=f"use_{_uname}", use_container_width=True):
                st.session_state.use_type = _uname
                st.session_state.step     = 5
                st.rerun()
            st.caption(_usub)
    st.write("")
    if st.button("← Volver", key="back_4"):
        st.session_state.step = 3
        st.rerun()

elif _step == 5:
    _ck = st.session_state.category
    st.markdown('<div class="sec-title">✅ Tu búsqueda está lista</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="summary-card">
      <div class="summary-label">Vas a comparar</div>
      <div class="summary-chips">
        <span class="chip">📦 {_cat_name(_ck)}</span>
        <span class="chip">🏷️ {st.session_state.brand}</span>
        <span class="chip">💰 {st.session_state.budget}</span>
        <span class="chip">🎯 {st.session_state.use_type}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _sc1, _sc2 = st.columns([4, 1])
    with _sc1:
        if st.button(
            "🔍 Comparar Precios en 4 Tiendas",
            key="compare",
            use_container_width=True,
        ):
            st.session_state.crew_started  = False
            st.session_state.result_holder = {}
            st.session_state.done_event    = threading.Event()
            st.session_state.step          = 6
            st.rerun()
    with _sc2:
        if st.button("← Volver", key="back_5", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

    st.markdown(
        '<p style="text-align:center;color:#6B8CAE;font-size:0.8rem;margin-top:0.8rem;">'
        'El proceso tarda entre 1 y 3 minutos — los agentes buscan en tiempo real.'
        '</p>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PASO 6 — Loading con tarjetas de agentes
# ══════════════════════════════════════════════════════════════════════════════

elif _step == 6:
    _ck = st.session_state.category
    st.markdown(
        f'<div class="sec-title">🤖 Buscando '
        f'{st.session_state.brand} {_cat_name(_ck)}...</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sec-sub">Los agentes de IA están trabajando. No cierres esta ventana.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.crew_started:
        st.session_state.crew_started = True
        _result_holder = {}
        _done_event    = threading.Event()
        st.session_state.result_holder = _result_holder
        st.session_state.done_event    = _done_event

        def _crew_worker(category, brand, budget, use_type, result_holder, done_event):
            try:
                result_holder["result"] = _run_crew(category, brand, budget, use_type)
            except Exception as _exc:
                result_holder["error"] = str(_exc)
            finally:
                done_event.set()

        _crew_thread = threading.Thread(
            target=_crew_worker,
            args=(
                st.session_state.category,
                st.session_state.brand,
                st.session_state.budget,
                st.session_state.use_type,
                _result_holder,
                _done_event,
            ),
            daemon=True,
        )
        st.session_state.crew_thread = _crew_thread
        _crew_thread.start()

    _card_ph  = st.empty()
    _phase    = 0
    _deadline = time.time() + 300
    while not st.session_state.done_event.is_set():
        if time.time() > _deadline:
            st.session_state.result_holder["error"] = "Timeout: el crew tardó más de 300 segundos."
            st.session_state.done_event.set()
            break
        with _card_ph.container():
            components.html(_agent_cards_html(_phase), height=165, scrolling=False)
        _phase = min(_phase + 1, 2)
        time.sleep(20)

    with _card_ph.container():
        components.html(_agent_cards_html(3), height=165, scrolling=False)
    time.sleep(0.8)

    _err = st.session_state.result_holder.get("error")
    _raw = st.session_state.result_holder.get("result")

    st.session_state.error_msg    = _err
    _parsed = _parse_crew_output(_raw) if not _err else None
    st.session_state.result_data  = _validate_comparisons(_parsed) if _parsed else None
    st.session_state.crew_started = False
    st.session_state.step         = 7
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PASO 7 — Resultados
# ══════════════════════════════════════════════════════════════════════════════

elif _step == 7:
    _ck = st.session_state.category

    # ── Error state ──────────────────────────────────────────────────────────
    if st.session_state.error_msg:
        st.error(f"❌ Error al ejecutar la búsqueda:\n\n{st.session_state.error_msg}")
        st.info("💡 Intentá con otra categoría o marca, o verificá tu conexión a internet.")

    elif not st.session_state.result_data:
        st.warning("⚠️ No se pudo interpretar el resultado. Intentá de nuevo.")

    else:
        _data           = st.session_state.result_data
        _raw_comps      = _data.get("comparisons", [])
        _recommendation = _data.get("recommendation", "")

        _comparisons = _filter_by_budget(_raw_comps, st.session_state.budget or "Sin límite")

        if not _comparisons:
            st.info(
                f"🔍 No se encontraron productos de **{st.session_state.brand}** "
                f"en **{_cat_name(_ck)}** con presupuesto **{st.session_state.budget}**.\n\n"
                "Probá seleccionar **Sin límite** o ajustá el rango."
            )
        else:
            st.markdown(
                f'<div class="sec-title">Resultados: {st.session_state.brand} {_cat_name(_ck)}</div>',
                unsafe_allow_html=True,
            )

            _total = len(_comparisons)

            def _real_saving(c):
                all_p = [e["price"] for e in _dedup_prices(c.get("all_prices", []))
                         if e.get("price", 0) > 0]
                calc = (max(all_p) - min(all_p)) if len(all_p) >= 2 else 0
                return calc if calc > 0 else max(float(c.get("savings") or 0), 0)

            _max_sav = max((_real_saving(c) for c in _comparisons), default=0)
            _best_c  = next(
                (c for c in _comparisons if _real_saving(c) == _max_sav and _max_sav > 0),
                _comparisons[0],
            )
            _bp  = _best_c.get("best_price", {})
            _bpv = _bp.get("price", 0)
            _bps = _bp.get("store", "")

            st.markdown(f"""
            <div class="metrics-row">
              <div class="metric-box m1">
                <div class="mlabel">Productos comparados</div>
                <div class="mvalue">{_total}</div>
                <div class="msub">grupos emparejados</div>
              </div>
              <div class="metric-box m2">
                <div class="mlabel">Mejor precio</div>
                <div class="mvalue">Q{_bpv:,.0f}</div>
                <div class="msub">en {_h(_bps)}</div>
              </div>
              <div class="metric-box m3">
                <div class="mlabel">Máximo ahorro</div>
                <div class="mvalue">Q{_max_sav:,.0f}</div>
                <div class="msub">vs precio más alto</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Tabla pivoteada ───────────────────────────────────────────────
            st.markdown(
                '<div style="font-weight:700;font-size:0.95rem;color:#F0F6FF;'
                'margin-bottom:0.7rem;letter-spacing:-0.01em;">📊 Comparativa de precios por tienda</div>',
                unsafe_allow_html=True,
            )
            _thtml, _theight = _pivot_table_html(_comparisons)
            components.html(_thtml, height=_theight, scrolling=False)

            # ── Recomendación ─────────────────────────────────────────────────
            if _recommendation:
                st.markdown(f"""
                <div style="background:#0A1628;border:1px solid #1E3A5F;
                            border-left:4px solid #00D4FF;
                            border-radius:14px;padding:1.4rem 1.6rem;margin-top:1.5rem;">
                  <div style="display:flex;align-items:flex-start;gap:14px;">
                    <div style="font-size:2rem;line-height:1;flex-shrink:0;">🧠</div>
                    <div>
                      <div style="font-size:0.68rem;color:#00D4FF;font-weight:700;
                                  text-transform:uppercase;letter-spacing:0.09em;
                                  margin-bottom:8px;">
                        Recomendación del Agente Analista
                      </div>
                      <div style="color:#F0F6FF;font-size:0.92rem;line-height:1.65;
                                  white-space:pre-wrap;font-weight:400;">
                        {_h(_recommendation)}
                      </div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Detalle expandible ────────────────────────────────────────────
            st.markdown(
                '<div style="margin-top:1.5rem;font-weight:700;color:#F0F6FF;'
                'font-size:0.95rem;margin-bottom:0.4rem;letter-spacing:-0.01em;">'
                '🔎 Detalle por producto</div>',
                unsafe_allow_html=True,
            )
            for _pi, _comp in enumerate(_comparisons):
                _pname  = _comp.get("product", f"Producto {_pi + 1}")
                # Truncar nombre si es muy largo para evitar overlap en expander
                _pname_short = _pname[:55] + "..." if len(_pname) > 55 else _pname
                _pbest  = _comp.get("best_price", {})
                _psav   = _comp.get("savings", 0)
                _label  = f"{_pname_short} | Q{_pbest.get('price', 0):,.0f} en {_pbest.get('store', '')}"
                if _psav > 0:
                    _label += f" (ahorro Q{_psav:,.0f})"

                with st.expander(_label, expanded=(_pi == 0)):
                    _pd = _dedup_prices(_comp.get("all_prices", []))
                    _ps = sorted(_pd, key=lambda x: x.get("price", 0))
                    _min_p = min(
                        (e["price"] for e in _ps if e.get("available", True) and e.get("price", 0) > 0),
                        default=None,
                    )
                    for _pe in _ps:
                        _es  = _pe.get("store", "")
                        _ep  = _pe.get("price", 0)
                        _ea  = _pe.get("available", True)
                        _eu  = _normalize_url(_pe.get("url", ""), _es)
                        _is_best = _min_p is not None and abs(_ep - _min_p) < 0.01 and _ea
                        _link_html = (
                            f' — <a href="{_eu}" target="_blank" '
                            f'style="color:#00B4D8;text-decoration:underline;">ver en tienda</a>'
                            if _eu else ""
                        )
                        if not _ea:
                            st.markdown(
                                f'<div style="background:rgba(214,40,40,0.08);border:1px solid rgba(214,40,40,0.25);'
                                f'border-radius:8px;padding:10px 14px;margin-bottom:6px;">'
                                f'<span style="color:#FF6B6B;font-weight:600;">⚠️ {_h(_es)}</span>'
                                f'<span style="color:#6B8CAE;"> — Q{_ep:,.0f} — Agotado</span></div>',
                                unsafe_allow_html=True,
                            )
                        elif _is_best:
                            st.markdown(
                                f'<div style="background:rgba(0,230,118,0.08);border:1px solid rgba(0,230,118,0.25);'
                                f'border-radius:8px;padding:10px 14px;margin-bottom:6px;">'
                                f'<span style="color:#00E676;font-weight:700;">⭐ {_h(_es)}</span>'
                                f'<span style="color:#F0F6FF;font-weight:600;"> — Q{_ep:,.0f} — Disponible</span>'
                                f'<span style="color:#00E676;font-weight:700;"> ← MEJOR PRECIO</span>'
                                f'{_link_html}</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="background:rgba(0,180,216,0.06);border:1px solid rgba(0,180,216,0.2);'
                                f'border-radius:8px;padding:10px 14px;margin-bottom:6px;">'
                                f'<span style="color:#00B4D8;font-weight:600;">📌 {_h(_es)}</span>'
                                f'<span style="color:#F0F6FF;"> — Q{_ep:,.0f} — Disponible</span>'
                                f'{_link_html}</div>',
                                unsafe_allow_html=True,
                            )

            # ── Alertador en background ───────────────────────────────────────
            if not st.session_state.alertador_started:
                st.session_state.alertador_started = True

                def _alertador_bg(comparisons, category, brand):
                    try:
                        from comparegt.crew import CompareGTCrew
                        CompareGTCrew().run_alertador(comparisons, category, brand)
                    except Exception:
                        pass

                threading.Thread(
                    target=_alertador_bg,
                    args=(
                        _comparisons,
                        st.session_state.category,
                        st.session_state.brand,
                    ),
                    daemon=True,
                ).start()

    # ── Historial de Alertas ──────────────────────────────────────────────────
    _alerts_path = os.path.join(_root, "alerts.json")
    _alerts_all: list = []
    if os.path.exists(_alerts_path):
        try:
            _alerts_all = json.loads(open(_alerts_path, encoding="utf-8").read())
        except Exception:
            _alerts_all = []

    _alerts_recent = sorted(
        _alerts_all, key=lambda a: a.get("timestamp", ""), reverse=True
    )[:10]

    st.markdown("<br>", unsafe_allow_html=True)
    _ah_col1, _ah_col2 = st.columns([5, 1])
    with _ah_col1:
        st.markdown(
            '<div style="font-weight:700;font-size:0.95rem;color:#F0F6FF;letter-spacing:-0.01em;">'
            '🔔 Historial de Alertas</div>',
            unsafe_allow_html=True,
        )
    with _ah_col2:
        if _alerts_all and st.button("🗑️ Limpiar", key="clear_alerts", use_container_width=True):
            open(_alerts_path, "w", encoding="utf-8").write("[]")
            st.rerun()

    if not _alerts_recent:
        st.caption("Sin alertas registradas aún. Las bajadas de precio ≥ 5% aparecerán aquí.")
    else:
        for _al in _alerts_recent:
            _al_pct = _al.get("pct_drop", 0)
            if _al_pct >= 15:
                _al_bg  = "rgba(255,71,87,0.08)"
                _al_brd = "rgba(255,71,87,0.3)"
                _al_badge = (
                    f'<span style="background:linear-gradient(135deg,#FF4757,#FF6B35);'
                    f'color:white;border-radius:12px;padding:3px 11px;'
                    f'font-size:0.75rem;font-weight:700;">🔥 -{_al_pct:.1f}%</span>'
                )
            else:
                _al_bg  = "#0F1923"
                _al_brd = "#1E3A5F"
                _al_badge = (
                    f'<span style="background:linear-gradient(135deg,#00E676,#00B4D8);'
                    f'color:#080C14;border-radius:12px;padding:3px 11px;'
                    f'font-size:0.75rem;font-weight:700;">↓ -{_al_pct:.1f}%</span>'
                )
            st.markdown(
                f'<div style="background:{_al_bg};border:1px solid {_al_brd};'
                f'border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'flex-wrap:wrap;gap:6px;">'
                f'<div>'
                f'<span style="font-weight:600;font-size:0.88rem;color:#F0F6FF;">'
                f'{_h(_al.get("product",""))}{(" — <a href=" + chr(34) + _normalize_url(_al.get("url",""), _al.get("store","")) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " style=" + chr(34) + "color:#00B4D8;text-decoration:underline;" + chr(34) + ">ver en tienda</a>") if _al.get("url") else ""}</span><br>'
                f'<span style="font-size:0.78rem;color:#6B8CAE;">'
                f'Mejor precio en <b style="color:#F0F6FF">{_h(_al.get("store",""))}</b> — '
                f'<span style="text-decoration:line-through;color:#6B8CAE;">'
                f'Q{_al.get("old_price",0):,.0f}</span> → '
                f'<b style="color:#00E676;">Q{_al.get("new_price",0):,.0f}</b>'
                f'&nbsp;(ahorro <span style="color:#00D4FF;">Q{_al.get("savings",0):,.0f}</span>)'
                f'</span><br>'
                f'<span style="font-size:0.72rem;color:#2D5080;">{_al.get("timestamp","")}</span>'
                f'</div>'
                f'<div>{_al_badge}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ── Botón Nueva búsqueda ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _, _center, _ = st.columns([2, 2, 2])
    with _center:
        if st.button("🔄 Nueva búsqueda", key="new_search", use_container_width=True):
            for _k in list(_DEFAULTS.keys()):
                if _k in st.session_state:
                    del st.session_state[_k]
            st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────

st.markdown(
    '<div class="cgt-footer">CompareGT •</div>',
    unsafe_allow_html=True,
)