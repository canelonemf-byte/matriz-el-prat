"""Calculadoras tributarias con fórmulas legales reales (RDL 2/2004, TRLRHL) y tipos vigentes de El Prat.

Tipos IBI 2026: Ordenança fiscal núm. 1 del Prat de Llobregat, art. 7, publicada en el BOPB de 23-12-2025,
CVE 202510200458 (https://bop.diba.cat/anuncio/ver-pdf/3878031). Comprobado el 2026-10-24.
Lo que no consta en una fuente oficial se devuelve como PENDIENTE; nunca se inventa.
"""
PENDIENTE = "PENDIENTE"
FUENTE_OF1_2026 = {"titulo": "Ordenança fiscal núm. 1 IBI, exercici 2026, art. 7", "boletin": "BOPB 23-12-2025",
                   "cve": "202510200458", "url": "https://bop.diba.cat/anuncio/ver-pdf/3878031"}
# Tipos de gravamen OF1 2026 (en tanto por ciento)
TIPOS_PRAT_2026 = {"urbana_general": 0.6199, "urbana_diferenciado": 0.8350, "rustica": 0.4939, "bice": 1.3000}
# Umbrales de valor catastral para el tipo diferenciado (OF1 art. 7.1.b; usos de la norma 20 RD 1020/1993)
UMBRALES_DIFERENCIADO = {"C": 1_000_000, "G": 10_000_000, "I": 3_500_000, "K": 10_000_000, "O": 7_500_000}
# Horquillas legales TRLRHL art. 72.1 y 72.2 (sin los incrementos del art. 72.3)
LIMITES_TRLRHL = {"urbana": (0.4, 1.10), "rustica": (0.3, 0.90), "bice": (0.4, 1.30)}


def tipo_aplicable(clase: str, uso: str = "", valor_catastral: float = 0.0) -> float:
    if clase == "bice":
        return TIPOS_PRAT_2026["bice"]
    if clase == "rustica":
        return TIPOS_PRAT_2026["rustica"]
    umbral = UMBRALES_DIFERENCIADO.get(uso.upper())
    # Nota: el diferenciado solo afecta como máximo al 10 % de inmuebles de cada uso con mayor VC (art. 72.4 TRLRHL);
    # esa condición requiere el padrón, por lo que aquí se devuelve el tipo y se avisa.
    if umbral and valor_catastral > umbral:
        return TIPOS_PRAT_2026["urbana_diferenciado"]
    return TIPOS_PRAT_2026["urbana_general"]


def cuota_ibi(base_liquidable, clase="urbana", uso="", valor_catastral=None, bonificacion_pct=0.0, tipo=None) -> dict:
    """Cuota íntegra = base liquidable × tipo (art. 71 TRLRHL); cuota líquida = íntegra − bonificaciones (arts. 73-74)."""
    if base_liquidable in (None, "", PENDIENTE):
        return {"estado": PENDIENTE, "falta": ["base_liquidable (recibo IBI o Sede Electrónica del Catastro)"]}
    t = tipo if tipo is not None else tipo_aplicable(clase, uso, valor_catastral if valor_catastral is not None else base_liquidable)
    lo, hi = LIMITES_TRLRHL["urbana" if clase == "urbana" else clase]
    integra = round(base_liquidable * t / 100, 2)
    liquida = round(integra * (1 - bonificacion_pct / 100), 2)
    return {"estado": "ok", "clase": clase, "tipo_pct": t, "cuota_integra": integra, "cuota_liquida": liquida,
            "dentro_limites_trlrhl": lo <= t <= hi, "limites_trlrhl": [lo, hi],
            "fundamento": ["TRLRHL arts. 65-72", "OF1 El Prat 2026 art. 7"], "fuente": FUENTE_OF1_2026}


def simular_cambio_tipo(clase: str, tipo_nuevo: float, base_liquidable_total=None) -> dict:
    """Variación de recaudación = base liquidable total × (tipo_nuevo − tipo_actual). Comprueba legalidad (art. 72)."""
    key = {"urbana": "urbana_general", "rustica": "rustica", "bice": "bice"}[clase]
    actual = TIPOS_PRAT_2026[key]
    lo, hi = LIMITES_TRLRHL[clase]
    avisos = []
    if not lo <= tipo_nuevo <= hi:
        avisos.append(f"tipo {tipo_nuevo} % fuera de la horquilla legal {lo}-{hi} % (art. 72 TRLRHL): no es aprobable")
    if abs(tipo_nuevo - actual) < 1e-9:
        avisos.append(f"el tipo {tipo_nuevo} % ya es el vigente en 2026: la propuesta no cambia nada")
    if clase == "bice" and actual >= hi:
        avisos.append("los BICE ya tributan al máximo legal (1,30 %): no se puede subir más")
    if clase == "urbana":
        avisos.append("art. 72.4 TRLRHL: los tipos diferenciados solo caben para usos NO residenciales; una rebaja "
                      "'solo residencial' exige bajar el tipo general, que afecta a todos los inmuebles urbanos "
                      "sin tipo diferenciado; la alternativa son bonificaciones legales (art. 74 TRLRHL)")
    out = {"clase": clase, "tipo_actual_pct": actual, "tipo_nuevo_pct": tipo_nuevo, "legal": lo <= tipo_nuevo <= hi,
           "avisos": avisos, "fuente": FUENTE_OF1_2026}
    if base_liquidable_total in (None, "", PENDIENTE):
        out.update(estado=PENDIENTE, variacion_recaudacion_eur=PENDIENTE,
                   falta=[f"base_liquidable_total_{clase} (padrón IBI / Catastro, estadística por municipio)"])
    else:
        out.update(estado="ok", variacion_recaudacion_eur=round(base_liquidable_total * (tipo_nuevo - actual) / 100, 2))
    return out


def base_implicita(variacion_eur: float, tipo_actual: float, tipo_nuevo: float) -> float:
    """Base liquidable que haría falta para que una cifra de impacto declarada sea coherente."""
    return round(variacion_eur / ((tipo_nuevo - tipo_actual) / 100), 2)


def tasa_residuos_pxg(tarifa_base=None, bonificacion_pct=0.0, coste_servicio_total=None, recaudacion_prevista=None) -> dict:
    """Ley 7/2022 art. 11.3: tasa específica, diferenciada y NO deficitaria; puede incluir pago por generación.
    Las bonificaciones deben compensarse para que la recaudación cubra el coste (TRLRHL art. 24.2 como límite superior)."""
    falta = [n for n, v in [("tarifa_base (OF 26 El Prat 2026)", tarifa_base), ("coste_servicio_total", coste_servicio_total),
                            ("recaudacion_prevista", recaudacion_prevista)] if v in (None, "", PENDIENTE)]
    out = {"fundamento": ["Ley 7/2022 art. 11.3", "TRLRHL arts. 20 y 24"], "falta": falta}
    if tarifa_base not in (None, "", PENDIENTE):
        out["cuota_bonificada"] = round(tarifa_base * (1 - bonificacion_pct / 100), 2)
    if coste_servicio_total not in (None, "", PENDIENTE) and recaudacion_prevista not in (None, "", PENDIENTE):
        rec = recaudacion_prevista * (1 - bonificacion_pct / 100)
        out.update(recaudacion_con_bonificacion=round(rec, 2), cobertura_coste=round(rec / coste_servicio_total, 4),
                   no_deficitaria=rec >= coste_servicio_total)
    out["estado"] = "ok" if not falta else PENDIENTE
    return out


def riesgo_beneficio_fiscal_tasa(descripcion: str) -> dict:
    """TRLRHL art. 9.1: no se pueden reconocer beneficios fiscales en tributos locales salvo los previstos en ley."""
    return {"descripcion": descripcion, "riesgo": "alto",
            "motivo": "una exención total en una tasa no prevista en norma con rango de ley vulnera el art. 9.1 TRLRHL; "
                      "alternativa: tarifa reducida por capacidad económica (art. 24.4) o un precio público/abono distinto",
            "fundamento": ["TRLRHL art. 9.1", "TRLRHL art. 24.4"]}


# Datos agregados reales (Catastro, Dirección General del Catastro; consultados 2026-10-24)
PADRON_IBI = {
    "fuente_ibi_2025": "https://www.catastro.hacienda.gob.es/jaxi/tabla.do?path=/est2025/ibi/&file=U04008.px&type=pcaxis&L=0",
    "fuente_usos_2026": "https://www.catastro.hacienda.gob.es/jaxi/tabla.do?path=/est2026/catastro/urbano/&file=URBO4208.px&type=pcaxis&L=0",
    "urbana_2025": {"recibos": 39422, "base_liquidable_eur": 3_429_161_000, "cuota_liquida_eur": 21_842_645},
    "bice_2025": {"recibos": 168, "base_liquidable_eur": 2_886_336_000, "cuota_liquida_eur": 37_522_370},
    "residencial_2026": {"inmuebles": 26351, "valor_catastral_eur": 1_479_340_030},
    "urbano_total_2026": {"inmuebles": 40260, "valor_catastral_eur": 3_444_815_740},
    "ultima_valoracion_catastral": 1997,
}


def impacto_rebaja_ibi(tipo_nuevo: float, tipo_actual: float | None = None) -> dict:
    """Impacto de bajar el tipo general urbano. Base liquidable = valor catastral (ponencia de 1997, sin reducción art. 67).

    - residencial: los 26.351 inmuebles de uso residencial (Catastro 2026).
    - cota_superior: toda la base urbana si todo tributara al tipo general (los inmuebles con tipo diferenciado
      no cambiarían, por eso el impacto real queda entre ambos valores).
    No descuenta bonificaciones (cuota líquida 2025 = 99,1 % de la íntegra)."""
    actual = tipo_actual if tipo_actual is not None else TIPOS_PRAT_2026["urbana_general"]
    if not LIMITES_TRLRHL["urbana"][0] <= tipo_nuevo <= LIMITES_TRLRHL["urbana"][1]:
        raise ValueError("tipo fuera de los límites del art. 72.1 TRLRHL")
    dif = (actual - tipo_nuevo) / 100
    r = PADRON_IBI["residencial_2026"]; t = PADRON_IBI["urbano_total_2026"]
    vc_medio = r["valor_catastral_eur"] / r["inmuebles"]
    return {"tipo_actual": actual, "tipo_nuevo": tipo_nuevo,
            "perdida_recaudacion_residencial_eur": round(r["valor_catastral_eur"] * dif),
            "perdida_recaudacion_cota_superior_eur": round(t["valor_catastral_eur"] * dif),
            "valor_catastral_medio_vivienda_eur": round(vc_medio),
            "cuota_media_vivienda_actual_eur": round(vc_medio * actual / 100, 2),
            "ahorro_medio_por_vivienda_eur": round(vc_medio * dif, 2),
            "viviendas_beneficiadas": r["inmuebles"],
            "peso_sobre_cuota_bice_2025_pct": round(r["valor_catastral_eur"] * dif / PADRON_IBI["bice_2025"]["cuota_liquida_eur"] * 100, 1),
            "fuentes": [PADRON_IBI["fuente_usos_2026"], PADRON_IBI["fuente_ibi_2025"]]}
