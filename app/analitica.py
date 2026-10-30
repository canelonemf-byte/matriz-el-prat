"""Analítica sobre datos oficiales descargados (sin cifras inventadas). MIT. Lázaro López Paz + asistencia de IA."""
from __future__ import annotations
import json, math, pathlib
import numpy as np
import pandas as pd
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
FUENTES = ROOT / "data" / "fuentes"
TRAD = {  # traducción al castellano de capítulos/políticas (nomenclatura oficial Orden EHA/3565/2008)
    ("IN", "1"): "Impuestos directos (IBI, IAE, vehículos, plusvalía)", ("IN", "2"): "Impuestos indirectos (ICIO)",
    ("IN", "3"): "Tasas, precios públicos y otros", ("IN", "4"): "Transferencias corrientes (Estado, Generalitat...)",
    ("IN", "5"): "Ingresos patrimoniales", ("IN", "6"): "Venta de inversiones reales", ("IN", "7"): "Transferencias de capital",
    ("IN", "8"): "Activos financieros", ("IN", "9"): "Préstamos (pasivos financieros)",
    ("DE", "1"): "Personal", ("DE", "2"): "Compras de bienes y servicios", ("DE", "3"): "Intereses de deuda",
    ("DE", "4"): "Transferencias corrientes (subvenciones, entes)", ("DE", "5"): "Fondo de contingencia",
    ("DE", "6"): "Inversiones reales", ("DE", "7"): "Transferencias de capital", ("DE", "8"): "Activos financieros",
    ("DE", "9"): "Devolución de préstamos",
    ("CF", "0"): "Deuda pública", ("CF", "1"): "Servicios públicos básicos (seguridad, urbanismo, limpieza, residuos...)",
    ("CF", "2"): "Protección y promoción social (servicios sociales, empleo, vivienda social)",
    ("CF", "3"): "Bienes públicos preferentes (educación, cultura, deporte, salud)",
    ("CF", "4"): "Actuaciones de carácter económico (comercio, transporte, I+D)", ("CF", "9"): "Actuaciones de carácter general (gobierno y administración)",
}


def cargar(nombre: str):
    p = FUENTES / "app" / f"{nombre}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def cargar_raiz(nombre: str):
    p = FUENTES / nombre
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.suffix == ".yaml" else json.loads(p.read_text(encoding="utf-8"))


def inventario():
    return yaml.safe_load((ROOT / "inventario_obligaciones.yaml").read_text(encoding="utf-8"))


def manifiesto():
    return cargar_raiz("MANIFIESTO.yaml") or []


def liquidacion() -> pd.DataFrame:
    d = cargar("liquidacio")
    if not d:
        return pd.DataFrame(columns=["any", "doc", "codigo", "concepto", "importe", "eur_hab"])
    df = pd.DataFrame(d["filas"])
    df["nombre"] = [TRAD.get((a, str(b)), c) for a, b, c in zip(df["doc"], df["codigo"], df["concepto"])]
    return df


def presupuesto() -> pd.DataFrame:
    d = cargar("pressupost")
    return pd.DataFrame(d["filas"]) if d else pd.DataFrame(columns=["any", "partida", "clasif", "nivel", "codigo", "concepto", "importe"])


def totales_anuales(liq: pd.DataFrame) -> pd.DataFrame:
    """Ingresos = derechos reconocidos (IN); gastos = obligaciones reconocidas (DE); saldo = IN - DE.
    Población implícita = importe / €/hab del propio dataset."""
    if liq.empty:
        return pd.DataFrame()
    t = liq[liq.doc.isin(["IN", "DE"])].pivot_table(index="any", columns="doc", values="importe", aggfunc="sum").fillna(0)
    t = t.rename(columns={"IN": "ingresos", "DE": "gastos"})
    t["saldo"] = t["ingresos"] - t["gastos"]
    x = liq[(liq.doc == "IN") & (liq.eur_hab > 0)]
    t["poblacion"] = (x.importe / x.eur_hab).groupby(x["any"]).median().round()
    t["gasto_por_hab"] = t["gastos"] / t["poblacion"]
    return t.reset_index()


def deflactar(serie: pd.Series, anios: pd.Series, base: int | None = None):
    """Euros constantes: X_real = X_nominal × IPC_base / IPC_año (IPC INE, media anual). Devuelve (serie, base) o (None, None)."""
    ipc = cargar("ipc")
    if not ipc:
        return None, None
    tabla = {int(k): v["media"] for k, v in ipc["anual"].items() if v["meses"] == 12}
    base = base or max(tabla)
    vals = [s * tabla[base] / tabla[a] if a in tabla else np.nan for s, a in zip(serie, anios)]
    return pd.Series(vals, index=serie.index), base


def cagr(v0: float, v1: float, n: int) -> float:
    """Tasa de crecimiento anual compuesta: (V_final / V_inicial)^(1/n) − 1."""
    if v0 <= 0 or v1 <= 0 or n <= 0:
        return float("nan")
    return (v1 / v0) ** (1 / n) - 1


def tendencia_log(anios, valores, horizonte: int = 2):
    """Ajuste log-lineal ln(y) = a + b·t por mínimos cuadrados. Crecimiento anual = e^b − 1.
    Previsión con intervalo de predicción al 95 % (± t·s·sqrt(1 + 1/n + (t0−t̄)²/Sxx)). Requiere ≥ 4 puntos > 0."""
    a = np.array([x for x, y in zip(anios, valores) if y and y > 0], dtype=float)
    y = np.array([math.log(y) for y in valores if y and y > 0])
    if len(a) < 4:
        return None
    b, c = np.polyfit(a, y, 1)
    res = y - (b * a + c); n = len(a); s = math.sqrt((res ** 2).sum() / (n - 2)); sxx = ((a - a.mean()) ** 2).sum()
    tcrit = {2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23}.get(n - 2, 2.2 if n < 30 else 1.96)
    prev = []
    for k in range(1, horizonte + 1):
        t0 = a.max() + k; m = b * t0 + c; e = tcrit * s * math.sqrt(1 + 1 / n + (t0 - a.mean()) ** 2 / sxx)
        prev.append({"any": int(t0), "prevision": math.exp(m), "min95": math.exp(m - e), "max95": math.exp(m + e)})
    return {"crecimiento_anual": math.exp(b) - 1, "r2": 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum(), "prevision": prev, "n": n}


def ejecucion(liq: pd.DataFrame, pres: pd.DataFrame, anio: int, clasif: str = "E", partida: str = "D") -> pd.DataFrame:
    """Grado de ejecución = obligaciones (o derechos) reconocidos / previsión INICIAL × 100.
    Ojo: se compara con el presupuesto inicial (no el definitivo con modificaciones), por eso puede superar el 100 %."""
    doc = {("D", "E"): "DE", ("I", "E"): "IN", ("D", "F"): "CF"}[(partida, clasif)]
    p = pres[(pres["any"] == anio) & (pres.partida == partida) & (pres.clasif == clasif) & (pres.nivel == 1)][["codigo", "importe"]]
    l = liq[(liq["any"] == anio) & (liq.doc == doc)][["codigo", "nombre", "importe"]]
    if p.empty or l.empty:
        return pd.DataFrame()
    m = l.merge(p, on="codigo", how="outer", suffixes=("_ejecutado", "_inicial")).fillna(0)
    m["nombre"] = [TRAD.get((doc, str(c)), n) if not n else n for c, n in zip(m.codigo, m.nombre)]
    m["ejecucion_pct"] = np.where(m.importe_inicial > 0, m.importe_ejecutado / m.importe_inicial * 100, np.nan)
    m["no_ejecutado"] = m.importe_inicial - m.importe_ejecutado
    return m.sort_values("codigo")


def contratos_unicos(df: pd.DataFrame) -> pd.DataFrame:
    """El registro repite filas (lotes/publicaciones). Se deduplica por órgano + expediente + adjudicatario + importe."""
    return df.drop_duplicates(subset=["organo", "expediente", "adjudicatario", "importe"]) if not df.empty else df


def contratos_detalle() -> pd.DataFrame:
    d = cargar("contractes_detall")
    return contratos_unicos(pd.DataFrame(d["filas"])) if d else pd.DataFrame()


def personal() -> pd.DataFrame:
    d = cargar("personal")
    return pd.DataFrame(d["filas"]) if d else pd.DataFrame(columns=["any", "nivel", "codigo", "concepto", "importe"])


GRUPOS_PERSONAL = {"10": "Órganos de gobierno (cargos electos y directivos)", "11": "Personal eventual (de confianza)", "12": "Funcionarios",
                   "13": "Personal laboral", "14": "Otro personal", "15": "Incentivos (productividad, gratificaciones)",
                   "16": "Seguridad Social y gastos sociales"}


def personal_grupos(df: pd.DataFrame) -> pd.DataFrame:
    g = df[df.nivel == 2].copy()
    g["grupo"] = g.codigo.map(GRUPOS_PERSONAL)
    return g.pivot_table(index="any", columns="grupo", values="importe", aggfunc="sum").fillna(0)


def formacion(df: pd.DataFrame) -> pd.Series:
    return df[df.codigo == "160200"].set_index("any").importe


def anomalias_contratos(df: pd.DataFrame) -> pd.DataFrame:
    """Marca contratos atípicos: (1) IQR sobre ln(importe) por tipo: fuera de [Q1−1,5·IQR, Q3+1,5·IQR];
    (2) z-score de ln(importe) > 3; (3) contrato menor por encima de umbrales LCSP art. 118 (15.000 € servicios/suministros,
    40.000 € obras; el dataset puede incluir IVA, por eso es 'revisar', no una infracción)."""
    if df.empty:
        return df
    d = df[df.importe > 0].copy()
    d["ln"] = np.log(d.importe)
    out = []
    for tipo, g in d.groupby("tipo"):
        q1, q3 = g.ln.quantile([.25, .75]); iqr = q3 - q1
        z = (g.ln - g.ln.mean()) / (g.ln.std() or 1)
        g = g.assign(z=z, iqr_alto=g.ln > q3 + 1.5 * iqr)
        out.append(g)
    d = pd.concat(out)
    obra = d.tipo.str.contains("OBRES", case=False, na=False)
    menor = d.procedimiento.str.contains("enor", na=False)
    d["menor_sobre_umbral"] = menor & (((~obra) & (d.importe > 15000)) | (obra & (d.importe > 40000)))
    d["motivo"] = [", ".join(m for m, f in (("IQR alto", a), ("z>3", z > 3), ("menor > umbral LCSP", u)) if f)
                   for a, z, u in zip(d.iqr_alto, d.z, d.menor_sobre_umbral)]
    return d[d.motivo != ""].sort_values("importe", ascending=False)


def fraccionamiento(df: pd.DataFrame) -> pd.DataFrame:
    """Señal de posible fraccionamiento: mismo órgano + mismo adjudicatario (persona jurídica) + mismo año, ≥3 contratos menores
    cuya suma supera 15.000 €. Es solo un indicio para revisar."""
    if df.empty:
        return df
    m = df[df.procedimiento.str.contains("enor", na=False) & ~df.adjudicatario.str.startswith("(no se muestra")]
    g = m.groupby(["organo", "any", "adjudicatario"]).agg(n=("importe", "size"), total=("importe", "sum")).reset_index()
    return g[(g.n >= 3) & (g.total > 15000)].sort_values("total", ascending=False)


def zscore_variaciones(liq: pd.DataFrame, doc: str = "CF") -> pd.DataFrame:
    """Variación interanual por partida y z-score de esa variación respecto a su propio histórico; |z| > 2 = cambio inusual."""
    p = liq[liq.doc == doc].pivot_table(index="any", columns="nombre", values="importe", aggfunc="sum").sort_index()
    v = p.pct_change(fill_method=None) * 100
    z = (v - v.mean()) / v.std()
    last = v.index.max()
    return pd.DataFrame({"variacion_pct": v.loc[last], "z": z.loc[last]}).dropna().sort_values("z", key=abs, ascending=False), last


def alertas(hoy=None) -> list[dict]:
    import datetime as dt
    hoy = hoy or dt.date.today()
    al = []
    inv = inventario()
    for i in inv["checklist"]:
        if i["estado"] in ("no_encontrado", "desactualizado", "sin_documentos", "solo_enlace"):
            al.append({"nivel": "alta" if i["estado"] in ("no_encontrado", "sin_documentos") else "media", "tipo": "transparencia",
                       "texto": f"{i['obligacion']}: {i['estado']}", "fuente": i.get("url", ""), "base_legal": i.get("base_legal", "")})
    al.append({"nivel": "alta", "tipo": "plazo", "texto": "Ordenanzas fiscales 2027: aprobación inicial 22-10-2026. Plazo de alegaciones de 30 días hábiles "
               "desde su publicación en el BOPB (aún no publicada a 2026-10-24). Audiencia pública anunciada el 17-11-2026.",
               "fuente": "https://bop.diba.cat/", "base_legal": "TRLRHL art. 17"})
    liq, pres = liquidacion(), presupuesto()
    if not liq.empty and not pres.empty:
        ult = int(liq["any"].max())
        e = ejecucion(liq, pres, ult)
        for _, r in e.iterrows():
            if r.importe_inicial > 1e6 and r.ejecucion_pct > 115:
                al.append({"nivel": "media", "tipo": "desviacion", "texto": f"{ult}: {r.nombre} ejecutado al {r.ejecucion_pct:.0f} % del inicial "
                           f"({r.importe_ejecutado:,.0f} € vs {r.importe_inicial:,.0f} €)", "fuente": "liquidacio + pressupost (Generalitat)", "base_legal": ""})
            if r.importe_inicial > 1e6 and r.ejecucion_pct < 70:
                al.append({"nivel": "media", "tipo": "infraejecucion", "texto": f"{ult}: {r.nombre} solo ejecutado al {r.ejecucion_pct:.0f} % "
                           f"({r.no_ejecutado:,.0f} € sin gastar)", "fuente": "liquidacio + pressupost (Generalitat)", "base_legal": ""})
    f = formacion(personal())
    if len(f) >= 2:
        a, b = f.index.max(), sorted(f.index)[-2]
        if f[a] < 0.5 * f[b]:
            al.append({"nivel": "media", "tipo": "personal", "texto": f"Formación del personal (160200): {f[b]:,.0f} € en {b} → {f[a]:,.0f} € en {a} (presupuesto inicial)",
                       "fuente": "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6", "base_legal": "TREBEP art. 14.g (derecho a la formación)"})
    for x in (cargar("ens") or {}).get("filas", []):
        if x["any"] == str(hoy.year - 1) and x["tipusens"] != "Municipis" and not x["liquidaci_decofin"]:
            al.append({"nivel": "baja", "tipo": "entes", "texto": f"{x['ens']}: sin registro de envío de liquidación {x['any']} en el inventario de la Generalitat",
                       "fuente": "https://analisi.transparenciacatalunya.cat/d/7fnj-etev", "base_legal": "Orden HAP/2105/2012"})
    return al


def hechos_para_ia() -> list[dict]:
    """Hechos verificables (con fuente) que la IA puede citar. La IA no debe usar números fuera de esta lista."""
    h = []
    t = totales_anuales(liquidacion())
    for _, r in t.tail(5).iterrows():
        h.append({"hecho": f"Año {int(r['any'])}: ingresos reconocidos {r.ingresos:,.0f} €, gastos {r.gastos:,.0f} €, saldo {r.saldo:,.0f} €, "
                           f"población {r.poblacion:,.0f}", "fuente": "https://analisi.transparenciacatalunya.cat/d/ytva-5kp3"})
    aoc = cargar_raiz("aoc_dades_obertes_agregado.json") or {}
    if aoc.get("endeutament"):
        d = aoc["endeutament"][-1]; h.append({"hecho": f"Deuda viva {d['any']}: {d['deute_viu_eur']:,.0f} €", "fuente": "dadesobertes.seu-e.cat endeutament"})
    if aoc.get("pmp"):
        d = aoc["pmp"][-1]; h.append({"hecho": f"Periodo medio de pago a proveedores ({d['periode']}): {d['pmp_dies']} días", "fuente": "dadesobertes.seu-e.cat pmp"})
    liq = liquidacion()
    if not liq.empty:
        u = int(liq["any"].max())
        for _, r in liq[(liq["any"] == u) & (liq.doc.isin(["CF", "IN", "IT"]))].iterrows():
            h.append({"hecho": f"{u} {r['doc']} {r.nombre}: {r.importe:,.0f} €", "fuente": "https://analisi.transparenciacatalunya.cat/d/ytva-5kp3"})
    for a in alertas()[:15]:
        h.append({"hecho": "Alerta: " + a["texto"], "fuente": a["fuente"]})
    pe = personal()
    if not pe.empty:
        g = personal_grupos(pe); a = int(g.index.max())
        h.append({"hecho": f"Presupuesto inicial {a}, capítulo 1 (personal): total {g.loc[a].sum():,.0f} €; " +
                           "; ".join(f"{k} {v:,.0f} €" for k, v in g.loc[a].items() if v), "fuente": "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6"})
        f = formacion(pe)
        h.append({"hecho": "Formación del personal (concepto 160200), presupuesto inicial: " + "; ".join(f"{int(k)} {v:,.0f} €" for k, v in f.tail(3).items()),
                  "fuente": "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6"})
    # Contratos 2024+: cifra de atípicos a revisar (IQR/z/LCSP). Indicios, no infracciones.
    det = contratos_detalle()
    if not det.empty:
        n_rev = int(len(anomalias_contratos(det)))
        h.append({"hecho": f"Contratos únicos desde 2024: {len(det):,}; contratos atípicos a revisar (IQR/z-score/LCSP art. 118): {n_rev}",
                  "fuente": "https://contractaciopublica.cat (detalle en data/fuentes/app/contractes_detall.json)"})
    return h
