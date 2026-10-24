"""5 agentes principales y 15 sub-agentes. Flujo: detección (sub-agente) → análisis y cálculo (agente principal)
→ documento BORRADOR → tramitación (la hace la persona interesada; este código nunca presenta nada)."""
import datetime as dt, json, re
from pathlib import Path
import yaml

from . import OBJETIVO, calculos as C, documentos as D, fuentes as F
from .store import Store

ROOT = Path(__file__).resolve().parents[1]
_YAML = next(p for p in (ROOT / "datos_pendientes.yaml", Path(__file__).with_name("datos_pendientes.yaml")) if p.exists())
PENDIENTES = yaml.safe_load(_YAML.read_text(encoding="utf-8"))

KW = {
    "fiscal": re.compile(r"ordenan[cç]a fiscal|ordenanzas? fiscal|IBI|b[eé]n[es]* immobles|bienes inmuebles|tribut|padr[oó]|pressupost|presupuesto", re.I),
    "rom": re.compile(r"reglament org[aà]nic|reglamento org[aá]nico|ROM\b|cartipàs|cartapacio|ple municipal", re.I),
    "vivienda": re.compile(r"habitatge|vivienda|Prat Espais|HPO|VPO|protecci[oó] oficial", re.I),
    "movilidad": re.compile(r"Mas Blau|mobilitat|movilidad|aparcament|estacionament|grua|grúa|retirada de vehicles", re.I),
    "residuos": re.compile(r"residus|residuos|recollida|recogida", re.I),
    "delta": re.compile(r"Ricarda|Delta del Llobregat|espais naturals|ZEPA|Natura 2000", re.I),
    "energia_agua": re.compile(r"energ|aigua|agua|depuradora|dessalinitzadora|desaladora", re.I),
    "aena": re.compile(r"AENA|aeroport|aeropuerto|port de Barcelona|puerto de Barcelona|BICE", re.I),
}


class SubAgente:
    nombre = ""; agente = ""; fuente = ""; tema = ""

    def __init__(self, store: Store):
        self.store = store

    def ingerir(self) -> list[dict]:
        return []

    def ejecutar(self) -> dict:
        if self.nombre in PENDIENTES.get("subagentes_en_espera", {}):
            info = PENDIENTES["subagentes_en_espera"][self.nombre]
            self.store.log_run(self.nombre, self.fuente, "pendiente", 0, info.get("falta", ""))
            res = {"subagente": self.nombre, "estado": "pendiente", "falta": info.get("falta", "")}
            res["detecciones"] = self.detectar_en_almacen()
            return res
        try:
            items = self.ingerir()
        except F.FuenteError as e:
            self.store.log_run(self.nombre, self.fuente, "error", 0, str(e))
            return {"subagente": self.nombre, "estado": "error", "detalle": str(e)[:300], "detecciones": []}
        nuevos = 0
        for it in items:
            rel = self.es_relevante(it)
            nuevos += self.store.add(self.fuente, self.nombre, it["titulo"], it["url"], it.get("fecha_publicacion", ""), rel, it.get("datos"))
        self.store.log_run(self.nombre, self.fuente, "ok", nuevos, f"{len(items)} leídos")
        return {"subagente": self.nombre, "estado": "ok", "leidos": len(items), "nuevos": nuevos, "detecciones": self.detectar_en_almacen()}

    def es_relevante(self, it) -> bool:
        txt = it["titulo"] + json.dumps(it.get("datos", {}), ensure_ascii=False)
        prat = bool(F.KW_PRAT.search(txt)) or it.get("datos", {}).get("es_el_prat") or it.get("datos", {}).get("organo_prat")
        return bool(prat or (self.tema and KW[self.tema].search(txt) and F.KW_LOCAL.search(txt)))

    def detectar_en_almacen(self, limite=20) -> list[dict]:
        if not self.tema:
            return []
        rows = self.store.query("SELECT fuente, titulo, url, fecha_publicacion FROM registros WHERE relevante=1 "
                                "ORDER BY fecha_publicacion DESC LIMIT 500")
        return [r for r in rows if KW[self.tema].search(r["titulo"])][:limite]


def _sub(nombre, agente, fuente, tema, ingerir=None):
    cls = type(nombre, (SubAgente,), {"nombre": nombre, "agente": agente, "fuente": fuente, "tema": tema})
    if ingerir:
        cls.ingerir = lambda self: ingerir()
    return cls


def _boe_ultimos(dias=3):
    out = []
    for i in range(dias):
        out += F.boe_sumario(dt.date.today() - dt.timedelta(days=i))
    return out


SUBAGENTES = [
    _sub("sub_1_1_monitor_boe_dogc", "legal_prat", "boe_sumario+dogc_normativa", "fiscal", lambda: _boe_ultimos() + F.dogc_normativa()),
    _sub("sub_1_2_rastreador_bopb", "legal_prat", "bopb_rss", "fiscal", F.bopb_rss),
    _sub("sub_1_3_gestor_rom_secretaria", "legal_prat", "rom_el_prat", "rom"),
    _sub("sub_2_1_inspector_ejecucion_presupuestaria", "fiscal_prat", "conprel_hacienda", "fiscal"),
    _sub("sub_2_2_calculador_bics_aena_puerto", "fiscal_prat", "of1_ibi_2026", "aena"),
    _sub("sub_2_3_optimizador_ibi_y_tasas", "fiscal_prat", "of1_ibi_2026", "fiscal"),
    _sub("sub_3_1_gestor_vpo_prat_espais", "urba_prat", "prat_espais", "vivienda"),
    _sub("sub_3_2_controlador_movilidad_mas_blau", "urba_prat", "movilidad_mas_blau", "movilidad"),
    _sub("sub_3_3_inspector_dominio_publico_grua", "urba_prat", "of8_of14_tasas", "movilidad"),
    _sub("sub_4_1_gestor_tasa_residuos_pxg", "eco_prat", "of26_residuos", "residuos"),
    _sub("sub_4_2_protector_delta_la_ricarda", "eco_prat", "boe+dogc+bopb (filtro)", "delta"),
    _sub("sub_4_3_monitor_energia_y_agua", "eco_prat", "consumos_municipales", "energia_agua"),
    _sub("sub_5_1_auditor_gestiona_pleno", "audit_prat", "actes_ple", "rom"),
    _sub("sub_5_2_inspector_placsp_contratos", "audit_prat", "placsp_atom", "", F.placsp_atom),
    _sub("sub_5_3_gestor_portal_transparencia", "audit_prat", "elprat_dades_obertes", "", F.elprat_dades_obertes),
]
# sub_2_2, sub_2_3 y sub_4_2 no tienen fuente propia: trabajan sobre lo que ingieren los demás.
for _n in ("sub_2_2_calculador_bics_aena_puerto", "sub_2_3_optimizador_ibi_y_tasas", "sub_4_2_protector_delta_la_ricarda"):
    next(s for s in SUBAGENTES if s.nombre == _n).ejecutar = lambda self: {
        "subagente": self.nombre, "estado": "ok", "leidos": 0, "nuevos": 0, "detecciones": self.detectar_en_almacen()}

BENEFICIO = {  # beneficio ciudadano de cada propuesta; prioridad 1 = mayor beneficio con base legal sólida
    "PRAT-FIS-001": {"beneficio": "IBI más bajo en la vivienda", "beneficiarios": "propietarios y, por repercusión, inquilinos", "prioridad": 2},
    "PRAT-FIS-002": {"beneficio": "más ingresos de grandes infraestructuras para servicios", "beneficiarios": "toda la ciudadanía", "prioridad": 5},
    "PRAT-ECO-001": {"beneficio": "tasa de residuos más justa (paga menos quien recicla)", "beneficiarios": "hogares que separan residuos", "prioridad": 1},
    "PRAT-URB-001": {"beneficio": "aparcamiento más barato para ir a trabajar", "beneficiarios": "trabajadores de Mas Blau", "prioridad": 4},
    "PRAT-VIV-001": {"beneficio": "más vivienda de alquiler asequible", "beneficiarios": "jóvenes y familias en lista de espera", "prioridad": 1},
    "PRAT-LEG-001": {"beneficio": "más transparencia y control del gobierno municipal", "beneficiarios": "concejales y ciudadanía", "prioridad": 3},
}

AGENTES = {
    "legal_prat": "Agente Normativo y Gobernanza Local",
    "fiscal_prat": "Agente de Hacienda Pública y Presupuestos",
    "urba_prat": "Agente de Desarrollo Urbano, Movilidad y Vivienda",
    "eco_prat": "Agente de Sostenibilidad y Transición Ecológica",
    "audit_prat": "Agente de Transparencia, Control Interno y Digitalización",
}


def analizar_propuestas() -> list[dict]:
    """Análisis del agente fiscal sobre las propuestas del Registro Maestro (Drive) con tipos y leyes reales."""
    out = []
    for p in PENDIENTES.get("propuestas_registro_maestro", []):
        r = {"id": p["id"], "nombre": p["nombre"], "impacto_declarado_eur": p.get("impacto_declarado_eur", "")}
        if p["id"] == "PRAT-FIS-001":
            r["calculo"] = C.simular_cambio_tipo("urbana", 0.48)
            r["base_implicita_eur"] = C.base_implicita(p["impacto_declarado_eur"], C.TIPOS_PRAT_2026["urbana_general"], 0.48)
            r["comentario"] = "la cifra declarada exige una base liquidable afectada de unos 1.930 M€; verificar con estadística del Catastro"
        elif p["id"] == "PRAT-FIS-002":
            r["calculo"] = C.simular_cambio_tipo("bice", 1.30)
            r["comentario"] = "el tipo BICE ya es 1,30 % en 2026 (máximo legal): los 6,1 M€ adicionales no se pueden obtener por esta vía"
        elif p["id"] == "PRAT-ECO-001":
            r["calculo"] = C.tasa_residuos_pxg(bonificacion_pct=40)
            r["comentario"] = "la tasa debe ser no deficitaria (Ley 7/2022 art. 11.3): la bonificación necesita compensarse"
        elif p["id"] == "PRAT-URB-001":
            r["calculo"] = C.riesgo_beneficio_fiscal_tasa("exención 100 % de la tasa de estacionamiento (OF 23) para trabajadores de Mas Blau")
        else:
            r["calculo"] = {"estado": C.PENDIENTE, "falta": p.get("falta", [])}
        b = BENEFICIO.get(p["id"], {"beneficio": "", "beneficiarios": "", "prioridad": 9})
        r.update(b, impacto_ciudadano_eur=r["calculo"].get("variacion_recaudacion_eur", C.PENDIENTE)
                 if isinstance(r["calculo"], dict) else C.PENDIENTE)
        # baja prioridad si el cálculo demuestra que no aporta beneficio real (p. ej. ya vigente)
        if any("no cambia nada" in a or "no se puede" in a for a in r["calculo"].get("avisos", [])):
            r["prioridad"] = 9
        out.append(r)
    return sorted(out, key=lambda r: r["prioridad"])


def ciclo(store: Store | None = None) -> dict:
    store = store or Store()
    res = {"objetivo": OBJETIVO, "ts": dt.datetime.now().isoformat(timespec="seconds"), "agentes": {}}
    for ag, nombre in AGENTES.items():
        subs = [s(store).ejecutar() for s in SUBAGENTES if s.agente == ag]
        res["agentes"][ag] = {"nombre": nombre, "subagentes": subs}
    res["analisis"] = analizar_propuestas()
    res["almacen"] = store.counts()
    return res
