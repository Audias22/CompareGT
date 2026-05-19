"""
CompareGT - Orquestación Multi-Agente con CrewAI
- Rastreo: Python puro llamando funciones internas de los scrapers directamente
- Emparejamiento + Análisis: LLM
"""

import os
import json
import time
import logging
import importlib
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from comparegt.tools.alertador_tool import registrar_alerta

logger = logging.getLogger(__name__)

_GROQ_BASE = "https://api.groq.com/openai/v1"

_FALLBACK_CHAIN = [
    {
        "name":    "LLaMA 3.3 70B (Groq)",
        "model":   "groq/llama-3.3-70b-versatile",
        "base":    _GROQ_BASE,
        "api_key": lambda: os.environ.get("OPENAI_API_KEY", ""),
    },
    {
        "name":    "LLaMA 3.1 8B Instant (Groq)",
        "model":   "groq/llama-3.1-8b-instant",
        "base":    _GROQ_BASE,
        "api_key": lambda: os.environ.get("OPENAI_API_KEY", ""),
    },
]


def _build_llm(model_def: dict) -> LLM:
    return LLM(
        model=model_def["model"],
        base_url=model_def["base"],
        api_key=model_def["api_key"](),
    )


def _should_fallback(exc: Exception) -> bool:
    msg = str(exc).lower()
    is_rate_limit   = "429" in msg or "rate_limit" in msg or "rate limit" in msg
    is_decommission = "model_decommissioned" in msg or "decommission" in msg or "no longer supported" in msg
    is_unavailable  = "model" in msg and ("not found" in msg or "unavailable" in msg or "does not exist" in msg)
    return is_rate_limit or is_decommission or is_unavailable


def _extract_wait_seconds(msg: str) -> float:
    import re
    m = re.search(r"try again in\s+(?:(\d+)h)?(?:(\d+)m)?(\d+(?:\.\d+)?)s", msg, re.IGNORECASE)
    if m:
        h = int(m.group(1) or 0)
        mn = int(m.group(2) or 0)
        s = float(m.group(3) or 0)
        return h * 3600 + mn * 60 + s
    m2 = re.search(r"please wait\s+(\d+(?:\.\d+)?)\s+second", msg, re.IGNORECASE)
    if m2:
        return float(m2.group(1))
    return 0.0


def _is_tpm_error(msg: str) -> bool:
    if "429" not in msg and "rate_limit" not in msg.lower() and "rate limit" not in msg.lower():
        return False
    wait = _extract_wait_seconds(msg)
    return 0 < wait <= 120


def _run_scrapers(category: str, brand: str) -> str:
    """
    Llama las funciones internas de cada scraper directamente,
    sin pasar por el objeto Tool de CrewAI.
    """
    # Importar los módulos y llamar las funciones subyacentes directamente
    scraper_configs = [
        ("MAX",         "comparegt.tools.max_scraper",         "scrape_max"),
        ("Tecno Fácil", "comparegt.tools.tecnofacil_scraper",  "scrape_tecnofacil"),
        ("Click",       "comparegt.tools.click_scraper",       "scrape_click"),
        ("Pacifiko",    "comparegt.tools.pacifiko_scraper",    "scrape_pacifiko"),
    ]

    all_products = []

    for store_name, module_path, func_name in scraper_configs:
        try:
            print(f"[CompareGT] Scraping {store_name}...")
            mod = importlib.import_module(module_path)

            # El @tool de CrewAI envuelve la función. La función original
            # está disponible en el módulo con el mismo nombre pero como
            # objeto Tool. Accedemos a la función Python interna via .func
            tool_obj = getattr(mod, func_name)
            
            # Intentar obtener la función Python subyacente
            fn = getattr(tool_obj, "func", None)
            
            if fn is not None:
                # CrewAI 1.x: la función original está en .func
                raw = fn(category=category, brand=brand)
            else:
                # Fallback: buscar función privada con prefijo _ en el módulo
                private_fn = getattr(mod, f"_{func_name}", None)
                if private_fn:
                    raw = private_fn(category=category, brand=brand)
                else:
                    raise ValueError(f"No se encontró función callable para {store_name}")

            data = json.loads(raw) if isinstance(raw, str) else raw
            products = data.get("products", [])
            all_products.extend(products)
            print(f"[CompareGT] {store_name}: {len(products)} productos encontrados")

        except Exception as e:
            logger.warning(f"[CompareGT] Error scraping {store_name}: {e}")
            continue

    return json.dumps(all_products, ensure_ascii=False)


def kickoff_with_fallback(inputs: dict):
    category = inputs.get("category", "")
    brand    = inputs.get("brand", "")

    # Paso 1: Scraping sin LLM
    print("[CompareGT] Iniciando scraping directo (sin LLM)...")
    productos_json = _run_scrapers(category, brand)
    productos = json.loads(productos_json)
    print(f"[CompareGT] Total productos recolectados: {len(productos)}")

    if not productos:
        raise RuntimeError(f"No se encontraron productos de {brand} en {category} en ninguna tienda.")

    # Paso 2: LLM para Emparejador y Analista
    available = [m for m in _FALLBACK_CHAIN if m["api_key"]()]
    if not available:
        raise RuntimeError("No hay API keys configuradas.")

    last_error = None

    for i, model_def in enumerate(available):
        tpm_retries = 0
        while True:
            print(f"[CompareGT] Modelo activo: {model_def['name']}"
                  + (f" (reintento {tpm_retries})" if tpm_retries else ""))
            try:
                os.environ["OPENAI_API_KEY"]    = model_def["api_key"]()
                os.environ["OPENAI_API_BASE"]   = model_def["base"]
                os.environ["OPENAI_MODEL_NAME"] = model_def["model"]

                inputs_con_productos = {**inputs, "productos_scrapeados": productos_json}
                result = CompareGTCrew().crew().kickoff(inputs=inputs_con_productos)
                print(f"[CompareGT] Éxito con: {model_def['name']}")
                return result

            except Exception as exc:
                last_error = exc
                msg = str(exc)

                if _is_tpm_error(msg) and tpm_retries < 3:
                    wait = _extract_wait_seconds(msg) + 3
                    print(f"[CompareGT] TPM limit. Esperando {wait:.0f}s y reintentando...")
                    time.sleep(wait)
                    tpm_retries += 1
                    continue

                if _should_fallback(exc):
                    if i < len(available) - 1:
                        print(f"[CompareGT] {model_def['name']} no disponible. Cambiando a: {available[i+1]['name']}")
                        time.sleep(1)
                    else:
                        print("[CompareGT] Todos los modelos agotados.")
                        raise exc
                    break
                else:
                    raise exc

    raise last_error


@CrewBase
class CompareGTCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def emparejador(self) -> Agent:
        return Agent(
            config=self.agents_config["emparejador"],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def analista(self) -> Agent:
        return Agent(
            config=self.agents_config["analista"],
            verbose=True,
            allow_delegation=False,
        )

    @task
    def emparejamiento_productos(self) -> Task:
        return Task(config=self.tasks_config["emparejamiento_productos"])

    @task
    def analisis_precios(self) -> Task:
        return Task(config=self.tasks_config["analisis_precios"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def run_alertador(self, comparisons: list, category: str, brand: str) -> None:
        model_def = next((m for m in _FALLBACK_CHAIN if m["api_key"]()), None)
        if not model_def:
            logger.warning("[Alertador] Sin API key disponible.")
            return

        llm = _build_llm(model_def)

        alertador_agent = Agent(
            role="Monitor de Precios y Generador de Alertas",
            goal="Analizar comparaciones de precios y registrar bajadas significativas usando la herramienta registrar_alerta.",
            backstory="Sos un sistema de monitoreo de precios del mercado guatemalteco. Registrás bajadas de precio >= 5% automáticamente.",
            tools=[registrar_alerta],
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        comparisons_json = json.dumps(comparisons, ensure_ascii=False)

        alertador_task = Task(
            description=(
                f"Analizar estas comparaciones y registrar alertas donde worst_price.price > best_price.price.\n\n"
                f"Comparaciones: {comparisons_json}\n\n"
                f"Categoría: {category} | Marca: {brand}\n\n"
                f"Por cada comparación con diferencia de precio, llamá a registrar_alerta con: "
                f"product, store (de best_price.store), old_price (worst_price.price), "
                f"new_price (best_price.price), category='{category}', brand='{brand}'."
            ),
            expected_output="Resumen de alertas registradas y descartadas.",
            agent=alertador_agent,
        )

        try:
            Crew(
                agents=[alertador_agent],
                tasks=[alertador_task],
                process=Process.sequential,
                verbose=False,
            ).kickoff()
            logger.info("[Alertador] Completado.")
        except Exception as exc:
            logger.warning(f"[Alertador] Error: {exc}")