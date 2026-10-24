"""Control ciudadano del Ajuntament del Prat de Llobregat — app Streamlit.
Ejecutar: streamlit run app/main.py   |   Autoría: Lázaro López Paz, El Prat de Llobregat, Barcelona, España, con asistencia de IA.
Código MIT; textos y documentación CC BY 4.0. Solo datos públicos oficiales, sin datos personales."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from app import analitica as A, ia

st.set_page_config(page_title="Control ciudadano · El Prat", page_icon="🏛️", layout="wide")
E = lambda x: f"{x:,.0f} €".replace(",", ".")
LIQ, PRES = A.liquidacion(), A.presupuesto()
TOT = A.totales_anuales(LIQ)
AOC = A.cargar_raiz("aoc_dades_obertes_agregado.json") or {}
CAT = A.cargar_raiz("catastro_estadisticas.json") or {}
FUENTE_LIQ = "https://analisi.transparenciacatalunya.cat/d/ytva-5kp3"


def fuente(*urls):
    st.caption("Fuente: " + " · ".join(f"[{u}]({u})" if u.startswith("http") else u for u in urls))


def pendiente(que, como):
    st.warning(f"**Pendiente:** {que}\n\n**Cómo obtenerlo:** {como}")


def sankey(anio):
    l = LIQ[LIQ["any"] == anio]
    ing, gas = l[(l.doc == "IN") & (l.importe > 0)], l[(l.doc == "CF") & (l.importe > 0)]
    nodos = list(ing.nombre) + ["Ayuntamiento"] + list(gas.nombre)
    c = len(ing); src, dst, val = [], [], []
    for i, v in enumerate(ing.importe):
        src.append(i); dst.append(c); val.append(v)
    for j, v in enumerate(gas.importe):
        src.append(c); dst.append(c + 1 + j); val.append(v)
    saldo = ing.importe.sum() - gas.importe.sum()
    if saldo > 0:
        nodos.append("Sobrante del año (no gastado)"); src.append(c); dst.append(len(nodos) - 1); val.append(saldo)
    fig = go.Figure(go.Sankey(node=dict(label=nodos, pad=12), link=dict(source=src, target=dst, value=val)))
    fig.update_layout(height=520, margin=dict(l=5, r=5, t=10, b=10))
    return fig


PAGINAS = ["🏠 Inicio", "💶 De dónde viene y a dónde va el dinero", "📊 Presupuesto y ejecución", "👥 Personal (sueldos y formación)", "💰 Sobrantes y dinero disponible",
           "📈 Tendencias y análisis", "🏦 Deuda y pago a proveedores", "📝 Contratos y proveedores", "🤝 Subvenciones y convenios",
           "🛠️ Servicios municipales y KPIs", "🏢 Empresas y entes municipales", "🏗️ Inversiones y proyectos futuros", "🏠 Impuestos (IBI y otros)",
           "🔎 Transparencia", "🚨 Alertas", "🤖 Pregunta a la IA", "📚 Glosario y fuentes"]
pag = st.sidebar.radio("Secciones", PAGINAS)
st.sidebar.caption("Autoría: Lázaro López Paz, El Prat de Llobregat (Barcelona, España), con asistencia de IA. Código MIT · textos CC BY 4.0. "
                   "Solo datos públicos oficiales. Esta app no presenta nada ante el Ajuntament.")
ULT = int(TOT["any"].max()) if not TOT.empty else None

if pag == PAGINAS[0]:
    st.title("Control ciudadano del Ajuntament del Prat de Llobregat")
    st.write("Para saber **en qué se gasta el dinero de los contribuyentes**, si se cumple lo previsto y qué se puede mejorar. Cada cifra lleva su fuente oficial.")
    if ULT:
        r = TOT[TOT["any"] == ULT].iloc[0]
        c = st.columns(4)
        c[0].metric(f"Ingresos {ULT}", E(r.ingresos)); c[1].metric(f"Gastos {ULT}", E(r.gastos))
        c[2].metric("Sobrante del año (ingresos − gastos)", E(r.saldo)); c[3].metric("Gasto por habitante", E(r.gasto_por_hab))
        c = st.columns(4)
        if AOC.get("endeutament"):
            d = AOC["endeutament"][-1]; c[0].metric(f"Deuda viva {d['any']}", E(d["deute_viu_eur"]))
        if AOC.get("pmp"):
            p = AOC["pmp"][-1]; c[1].metric(f"Pago a proveedores ({p['periode']})", f"{p['pmp_dies']} días", help="Máximo legal: 30 días")
        c[2].metric("Población (implícita en datos)", f"{r.poblacion:,.0f}".replace(",", "."))
        al = A.alertas(); c[3].metric("Alertas activas", len(al))
        fuente(FUENTE_LIQ, "https://dadesobertes.seu-e.cat")
        st.subheader(f"El dinero de {ULT}, de un vistazo")
        st.plotly_chart(sankey(ULT), use_container_width=True)
        st.caption("Izquierda: de dónde viene el dinero (derechos reconocidos). Derecha: en qué se gasta por grandes áreas (obligaciones reconocidas).")
        st.subheader("Alertas más importantes")
        for a in [a for a in al if a["nivel"] == "alta"][:6]:
            st.error(a["texto"])
    else:
        pendiente("datos de liquidación", "ejecutar `python -m app.fetchers`")

elif pag == PAGINAS[1]:
    st.title("De dónde viene y a dónde va el dinero")
    anio = st.select_slider("Año", sorted(LIQ["any"].unique()), value=ULT)
    st.plotly_chart(sankey(anio), use_container_width=True)
    l = LIQ[LIQ["any"] == anio]
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("De dónde viene"); x = l[l.doc == "IN"][["nombre", "importe"]].sort_values("importe", ascending=False)
        st.plotly_chart(px.pie(x, names="nombre", values="importe", hole=.4), use_container_width=True)
        tot = x.importe.sum(); top = x.iloc[0]
        st.info(f"De cada 100 € que ingresa el Ayuntamiento, **{top.importe / tot * 100:.0f} €** vienen de «{top.nombre}».")
    with c2:
        st.subheader("A dónde va (por áreas)"); y = l[l.doc == "CF"][["nombre", "importe"]].sort_values("importe", ascending=False)
        st.plotly_chart(px.pie(y, names="nombre", values="importe", hole=.4), use_container_width=True)
        st.subheader("A dónde va (por tipo de gasto)")
        st.dataframe(l[l.doc == "DE"][["nombre", "importe"]].sort_values("importe", ascending=False), hide_index=True)
    st.subheader("Principales impuestos y tasas")
    st.dataframe(l[l.doc == "IT"][["concepto", "importe"]].sort_values("importe", ascending=False), hide_index=True)
    fuente(FUENTE_LIQ)

elif pag == PAGINAS[2]:
    st.title("Presupuesto previsto vs. lo realmente ejecutado")
    st.latex(r"\text{Ejecución (\%)} = \frac{\text{Obligaciones reconocidas}}{\text{Presupuesto inicial}} \times 100")
    st.caption("Se compara con el presupuesto INICIAL (no con el definitivo tras modificaciones): por eso algunas partidas superan el 100 %.")
    anios = sorted(set(LIQ["any"]) & set(PRES["any"]))
    anio = st.selectbox("Año", anios[::-1])
    for t, (p, c) in {"Gastos por tipo (capítulos)": ("D", "E"), "Ingresos por tipo (capítulos)": ("I", "E")}.items():
        st.subheader(t); e = A.ejecucion(LIQ, PRES, anio, c, p)
        if e.empty:
            pendiente("datos de ese año", "refrescar fetchers"); continue
        fig = go.Figure([go.Bar(name="Previsto", x=e.nombre, y=e.importe_inicial), go.Bar(name="Ejecutado", x=e.nombre, y=e.importe_ejecutado)])
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(e[["nombre", "importe_inicial", "importe_ejecutado", "ejecucion_pct", "no_ejecutado"]].round(1), hide_index=True)
    st.subheader(f"Presupuesto inicial {int(PRES['any'].max())} por áreas (programas)")
    f = PRES[(PRES["any"] == PRES["any"].max()) & (PRES.partida == "D") & (PRES.clasif == "F") & (PRES.nivel == 2)]
    st.plotly_chart(px.treemap(f, path=["concepto"], values="importe"), use_container_width=True)
    pendiente("ejecución trimestral del año en curso", "el portal de transparencia solo enlaza fuera (estado 'solo_enlace'); pedirla por acceso a la información (Llei 19/2014 art. 18)")
    fuente("https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6", FUENTE_LIQ)

elif pag == "👥 Personal (sueldos y formación)":
    st.title("Personal: sueldos, Seguridad Social y formación")
    st.caption("Capítulo 1 del presupuesto INICIAL por concepto económico (la ejecución real por concepto no está en datos abiertos).")
    pe = A.personal()
    if pe.empty:
        pendiente("capítulo 1 por concepto", "ejecutar `python -m app.fetchers personal`")
    else:
        g = A.personal_grupos(pe)
        st.plotly_chart(px.bar(g.loc[2016:], barmode="stack", labels={"value": "€", "any": "Año"}), use_container_width=True)
        anio = st.selectbox("Año", sorted(g.index)[::-1])
        st.dataframe(g.loc[anio].rename("previsto (€)").to_frame(), use_container_width=True)
        st.metric(f"Total personal previsto {anio}", E(g.loc[anio].sum()))
        f = A.formacion(pe)
        st.subheader("Formación del personal (concepto 160200)")
        st.plotly_chart(px.line(f.loc[2016:], markers=True, labels={"value": "€", "any": "Año"}), use_container_width=True)
        if len(f) > 1 and f.iloc[-1] < 0.5 * f.iloc[-2]:
            st.warning(f"La formación baja de {E(f.iloc[-2])} a {E(f.iloc[-1])}.")
        st.dataframe(pe[(pe["any"] == anio) & (pe.nivel >= 3)][["codigo", "concepto", "importe"]], hide_index=True)
        st.info("Los sueldos de cada cargo electo son públicos (Llei 19/2014 art. 11) y figuran en el portal de transparencia; pendiente cargarlos como datos abiertos. No se muestran sueldos de empleados concretos.")
        fuente("https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6",
               "https://seu-e.cat/ca/web/elpratdellobregat/govern-obert-i-transparencia/informacio-institucional-i-organitzativa/organitzacio-politica-i-retribucions/carrecs-electes")

elif pag == PAGINAS[4]:
    st.title("Sobrantes: dinero que podría mejorar la vida en El Prat")
    st.latex(r"\text{Sobrante del año} = \text{Derechos reconocidos} - \text{Obligaciones reconocidas}")
    st.plotly_chart(px.bar(TOT, x="any", y="saldo", labels={"saldo": "€", "any": "Año"}, title="Sobrante (o déficit) cada año"), use_container_width=True)
    st.metric("Suma de sobrantes de los últimos 5 años", E(TOT.tail(5).saldo.sum()))
    st.caption("Aproximación al resultado presupuestario sin ajustes (no incluye desviaciones de financiación ni créditos financiados con remanente).")
    e = A.ejecucion(LIQ, PRES, ULT)
    if not e.empty:
        st.subheader(f"Créditos no gastados en {ULT} (previsto − ejecutado)")
        x = e[e.no_ejecutado > 0][["nombre", "importe_inicial", "importe_ejecutado", "no_ejecutado"]]
        st.dataframe(x, hide_index=True); st.metric("Total no ejecutado", E(x.no_ejecutado.sum()))
    pendiente("remanente de tesorería para gastos generales", "figura en el expediente de liquidación (Decreto de aprobación) y en la Cuenta General; la última publicada es de 2022. Pedir por acceso a la información o consultar la Sindicatura de Comptes.")
    st.info("**Límites legales:** el sobrante no se puede gastar libremente. La LOEPSF (Ley Orgánica 2/2012) obliga a cumplir la estabilidad presupuestaria, "
            "la regla de gasto y el límite de deuda; el superávit se destina en principio a reducir deuda (art. 32), salvo las inversiones financieramente "
            "sostenibles (DA 6ª) o las excepciones que fije cada año la ley. Las reglas fiscales estuvieron suspendidas 2020-2023.")
    fuente(FUENTE_LIQ, "https://www.boe.es/buscar/act.php?id=BOE-A-2012-5730")

elif pag == PAGINAS[5]:
    st.title("Tendencias y análisis")
    serie = st.selectbox("Serie", ["gastos", "ingresos", "gasto_por_hab"])
    real, base = A.deflactar(TOT[serie], TOT["any"])
    df = TOT[["any", serie]].copy(); df["real"] = real
    log = st.checkbox("Escala logarítmica", value=False)
    fig = go.Figure([go.Scatter(x=df["any"], y=df[serie], name="Euros corrientes"), go.Scatter(x=df["any"], y=df.real, name=f"Euros constantes de {base}")])
    if log:
        fig.update_yaxes(type="log")
    tl = A.tendencia_log(df["any"], df[serie])
    if tl:
        pv = pd.DataFrame(tl["prevision"])
        fig.add_trace(go.Scatter(x=pv["any"], y=pv.prevision, name="Previsión", mode="markers+lines",
                                 error_y=dict(type="data", symmetric=False, array=pv.max95 - pv.prevision, arrayminus=pv.prevision - pv.min95)))
    st.plotly_chart(fig, use_container_width=True)
    a0, a1 = int(df["any"].min()), int(df["any"].max())
    c = st.columns(3)
    c[0].metric(f"Crecimiento anual compuesto {a0}-{a1}", f"{A.cagr(df[serie].iloc[0], df[serie].iloc[-1], a1 - a0) * 100:.1f} %")
    if tl:
        c[1].metric("Crecimiento por tendencia log-lineal", f"{tl['crecimiento_anual'] * 100:.1f} %/año", help=f"R² = {tl['r2']:.2f}")
    if real.notna().sum() > 1:
        rr = df.dropna(); c[2].metric("Crecimiento real (descontando inflación)", f"{A.cagr(rr.real.iloc[0], rr.real.iloc[-1], int(rr['any'].iloc[-1] - rr['any'].iloc[0])) * 100:.1f} %/año")
    with st.expander("Fórmulas (explicadas)"):
        st.latex(r"\text{CAGR} = \left(\frac{V_{final}}{V_{inicial}}\right)^{1/n} - 1")
        st.latex(r"\text{Euros constantes} = \text{Euros del año} \times \frac{IPC_{base}}{IPC_{año}}")
        st.latex(r"\ln(y) = a + b\,t \;\Rightarrow\; \text{crecimiento anual} = e^{b}-1")
        st.write("La previsión prolonga la tendencia log-lineal; la barra muestra el intervalo de predicción al 95 %. No es un presupuesto: solo indica hacia dónde va la serie si nada cambia.")
    st.subheader(f"Cambios inusuales por área en el último año (z-score)")
    z, ult = A.zscore_variaciones(LIQ)
    st.dataframe(z.round(2)); st.caption(f"Variación {ult} frente al año anterior. |z| > 2 indica un cambio fuera de lo habitual para esa área.")
    fuente(FUENTE_LIQ, "https://www.ine.es/consul/serie.do?s=IPC251852")

elif pag == PAGINAS[6]:
    st.title("Deuda y pago a proveedores")
    d = pd.DataFrame(AOC.get("endeutament", []))
    if not d.empty:
        d["deuda_por_hab"] = d.deute_viu_eur / d.cens
        st.plotly_chart(px.bar(d, x="any", y="deute_viu_eur", title="Deuda viva (€)"), use_container_width=True)
        st.plotly_chart(px.line(d, x="any", y="deuda_por_hab", title="Deuda por habitante (€)"), use_container_width=True)
    p = pd.DataFrame(AOC.get("pmp", []))
    if not p.empty:
        fig = px.line(p, x="periode", y="pmp_dies", title="Periodo medio de pago a proveedores (días)"); fig.add_hline(y=30, line_dash="dash", annotation_text="Máximo legal 30 días")
        st.plotly_chart(fig, use_container_width=True)
    fuente("https://dadesobertes.seu-e.cat (datasets endeutament y PMP, CODI_ENS 816910007)")

elif pag == PAGINAS[7]:
    st.title("Contratos y proveedores")
    k = A.cargar("contractes") or {}
    ag = pd.DataFrame(k.get("agregado", []))
    if ag.empty:
        pendiente("contratos", "ejecutar `python -m app.fetchers contractes`")
    else:
        org = st.multiselect("Órgano contratante", sorted(ag.organo.unique()), default=sorted(ag.organo.unique()))
        g = ag[ag.organo.isin(org)]
        st.plotly_chart(px.bar(g.groupby(["any", "organo"], as_index=False).importe.sum(), x="any", y="importe", color="organo", title="Importe adjudicado por año"), use_container_width=True)
        st.plotly_chart(px.bar(g.groupby(["any", "procedimiento"], as_index=False).n.sum(), x="any", y="n", color="procedimiento", title="Nº de contratos por procedimiento"), use_container_width=True)
        st.subheader("Mayores adjudicatarios desde 2022 (solo empresas y entidades)")
        st.dataframe(pd.DataFrame(k["top_adjudicatarios_desde_2022"]).query("organo in @org"), hide_index=True)
        st.caption("Por protección de datos, los adjudicatarios que pueden ser personas físicas no se nombran; se agregan: " +
                   "; ".join(f"{o}: {v['n']} contratos, {E(v['importe'])}" for o, v in k.get("no_nombrados_desde_2022", {}).items()))
        det = A.contratos_detalle()
        if not det.empty:
            st.subheader("Contratos atípicos (2024 en adelante)")
            st.write("Se marcan por importe inusual dentro de su tipo (IQR y z-score sobre el logaritmo del importe) o contratos menores por encima de los umbrales de la LCSP. **Son indicios para revisar, no irregularidades probadas.**")
            st.dataframe(A.anomalias_contratos(det)[["organo", "any", "expediente", "objeto", "procedimiento", "adjudicatario", "importe", "motivo"]].head(100), hide_index=True)
            st.subheader("Posible fraccionamiento de contratos menores")
            st.dataframe(A.fraccionamiento(det).head(50), hide_index=True)
            st.caption("Mismo órgano, misma empresa y mismo año: 3 o más contratos menores que suman más de 15.000 €. Puede tener explicaciones legítimas (servicios distintos).")
        fuente(k.get("dataset", ""), "https://contractaciopublica.cat")

elif pag == PAGINAS[8]:
    st.title("Subvenciones y convenios")
    s = pd.DataFrame([{"any": int(a), **v} for a, v in AOC.get("subvencions_per_any", {}).items()]).sort_values("any")
    if not s.empty:
        st.plotly_chart(px.bar(s, x="any", y="import_eur", hover_data=["n"], title="Subvenciones otorgadas (importe total, €)"), use_container_width=True)
        st.dataframe(s, hide_index=True)
    c = pd.DataFrame([{"any": int(a), "convenios": v if not isinstance(v, dict) else v.get("n")} for a, v in AOC.get("convenis_per_any", {}).items()]).sort_values("any")
    st.plotly_chart(px.bar(c, x="any", y="convenios", title="Convenios registrados por año"), use_container_width=True)
    st.caption("Solo agregados: no se muestran beneficiarios (pueden ser personas físicas).")
    pendiente("ejecución de los convenios (qué se ha cumplido y pagado)", "la página del portal está 'sin_documentos'; pedirla por acceso a la información (Llei 19/2014 art. 8.1.b y 18)")
    fuente("https://dadesobertes.seu-e.cat (subvencions, convenis; CODI_ENS 816910007)")

elif pag == PAGINAS[9]:
    st.title("Servicios municipales: coste y tiempos")
    cs = pd.DataFrame((A.cargar("cost_serveis") or {}).get("filas", []))
    if not cs.empty:
        u = int(cs["any"].max()); x = cs[(cs["any"] == u) & (cs.coste > 0)].sort_values("coste", ascending=False)
        pob = TOT.set_index("any").poblacion.get(u)
        x["coste_por_hab"] = x.coste / pob if pob else None
        st.subheader(f"Coste efectivo de cada servicio ({u})")
        st.plotly_chart(px.bar(x, x="coste", y="servicio", orientation="h", hover_data=["gestion"]), use_container_width=True)
        st.dataframe(x[["servicio", "gestion", "coste", "coste_por_hab"]].round(2), hide_index=True)
        sv = st.selectbox("Evolución de un servicio", sorted(cs.servicio.unique()))
        st.plotly_chart(px.line(cs[cs.servicio == sv], x="any", y="coste"), use_container_width=True)
        st.caption("Coste 0 = servicio prestado por otra administración o empresa municipal (p. ej. agua: Aigües del Prat).")
    st.subheader("Indicadores de innovación y tiempos de servicio")
    kpis = pd.DataFrame([
        {"indicador": "Periodo medio de pago a proveedores", "valor": f"{AOC['pmp'][-1]['pmp_dies']} días" if AOC.get("pmp") else "pendiente", "objetivo": "≤ 30 días (legal)", "beneficio": "pymes locales cobran antes"},
        {"indicador": "Ejecución de inversiones", "valor": "ver Presupuesto y ejecución", "objetivo": "pendiente (sin objetivo oficial)", "beneficio": "obras terminadas a tiempo"},
        {"indicador": "Tiempo de respuesta a solicitudes de acceso a la información", "valor": "pendiente", "objetivo": "≤ 1 mes (Llei 19/2014 art. 33)", "beneficio": "transparencia real"},
        {"indicador": "Tiempo de concesión de licencias de obra", "valor": "pendiente", "objetivo": "pendiente (sin objetivo oficial)", "beneficio": "menos espera para vecinos y negocios"},
        {"indicador": "Tiempo de respuesta a quejas y sugerencias", "valor": "pendiente", "objetivo": "pendiente (sin objetivo oficial)", "beneficio": "problemas resueltos antes"},
        {"indicador": "Espera para cita en servicios sociales", "valor": "pendiente", "objetivo": "pendiente (sin objetivo oficial)", "beneficio": "atención rápida a quien lo necesita"},
        {"indicador": "Trámites disponibles 100 % en línea", "valor": "pendiente", "objetivo": "pendiente (sin objetivo oficial)", "beneficio": "menos desplazamientos"},
    ])
    st.dataframe(kpis, hide_index=True)
    pendiente("tiempos de servicio (licencias, quejas, servicios sociales, OAC)", "no se publican como datos abiertos; pedirlos por acceso a la información (Llei 19/2014 art. 18) y a la Carta de Servicios municipal si existe")
    fuente("https://analisi.transparenciacatalunya.cat/d/7e8k-3vki")

elif pag == PAGINAS[10]:
    st.title("Empresas y entes municipales")
    e = pd.DataFrame((A.cargar("ens") or {}).get("filas", []))
    if not e.empty:
        u = e["any"].max(); x = e[e["any"] == u]
        st.write(f"Entes que el inventario oficial de la Generalitat vincula al Ajuntament ({u}):")
        st.dataframe(x[["ens", "codi10", "tipusens", "pressupostdecofin", "liquidaci_decofin", "dataliquidaci_decofin"]], hide_index=True)
        st.caption("'Tramès' = enviado a la administración tutelar. Vacío = sin registro en ese inventario (las sociedades mercantiles pueden rendir por otra vía).")
    k = pd.DataFrame((A.cargar("contractes") or {}).get("agregado", []))
    if not k.empty:
        st.subheader("Contratación de cada ente")
        st.plotly_chart(px.bar(k.groupby(["any", "organo"], as_index=False).importe.sum(), x="any", y="importe", color="organo"), use_container_width=True)
    pendiente("cuentas anuales, plantilla y retribuciones de Prat Espais, Aigües del Prat y El Prat Comunicació", "Registro Mercantil (cuentas depositadas) y portal de transparencia de cada sociedad; si no constan, acceso a la información (Llei 19/2014 art. 3.1.b)")
    fuente("https://analisi.transparenciacatalunya.cat/d/7fnj-etev", "https://analisi.transparenciacatalunya.cat/d/hb6v-jcbf")

elif pag == PAGINAS[11]:
    st.title("Inversiones y proyectos futuros")
    inv = LIQ[(LIQ.doc == "DE") & (LIQ.codigo.astype(str) == "6")]
    pi = PRES[(PRES.partida == "D") & (PRES.clasif == "E") & (PRES.nivel == 1) & (PRES.codigo == "6")]
    fig = go.Figure([go.Bar(name="Inversión prevista (inicial)", x=pi["any"], y=pi.importe), go.Bar(name="Inversión ejecutada", x=inv["any"], y=inv.importe)])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Capítulo 6 'Inversiones reales'. Si lo ejecutado es menor que lo previsto, hay obras retrasadas o anuladas.")
    if not pi.empty:
        st.metric(f"Inversión prevista en {int(pi['any'].max())}", E(pi[pi['any'] == pi['any'].max()].importe.sum()))
    p26 = PRES[(PRES["any"] == PRES["any"].max()) & (PRES.partida == "I") & (PRES.nivel == 1) & (PRES.codigo == "9")]
    if not p26.empty:
        st.info(f"El presupuesto {int(PRES['any'].max())} prevé {E(p26.importe.sum())} de ingresos por nuevos préstamos (capítulo 9 de ingresos).")
    pendiente("Plan de Actuación Municipal (PAM), plan de inversiones plurianual y proyectos urbanísticos (p. ej. Mas Blau, Eixample Nord) con importes y plazos",
              "documentos del PAM y anexo de inversiones del presupuesto en seu-e.cat; planeamiento en el Registre de Planejament Urbanístic de Catalunya (RPUC); "
              "si faltan, acceso a la información. Se añadirán cuando se verifiquen sus URL oficiales.")
    fuente(FUENTE_LIQ, "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6")

elif pag == PAGINAS[12]:
    st.title("Impuestos: IBI y otros")
    ti = pd.DataFrame(AOC.get("tipus_impositius", []))
    if not ti.empty:
        u = ti.ANY.max(); st.subheader(f"Tipos y coeficientes {u}"); st.dataframe(ti[ti.ANY == u][["DESC_ESTRUCTURA", "IMPORT"]], hide_index=True)
    ibi = CAT.get("ibi", {})
    if ibi:
        c = st.columns(2)
        c[0].metric(f"IBI urbano {ibi['anyo']}: recibos", f"{ibi['urbana']['Recibos']:,.0f}".replace(",", "."), E(ibi['urbana']['Cuota líquida']))
        c[1].metric(f"IBI bienes especiales (aeropuerto, puerto...) {ibi['anyo']}", f"{ibi['bice']['Recibos']:,.0f} recibos", E(ibi['bice']['Cuota líquida']))
        st.write(f"Recibo medio urbano: **{E(ibi['urbana']['Cuota líquida'] / ibi['urbana']['Recibos'])}** (cuota líquida / recibos).")
        fuente(ibi.get("fuente", ""))
    it = LIQ[(LIQ.doc == "IT")]
    st.plotly_chart(px.line(it, x="any", y="importe", color="concepto", title="Recaudación por impuesto/tasa (derechos reconocidos)"), use_container_width=True)
    st.info("La revisión catastral es de 1997: los valores catastrales están muy desactualizados, lo que condiciona el tipo del IBI.")
    fuente(FUENTE_LIQ, "https://www.catastro.hacienda.gob.es/es-ES/estadisticas.html")

elif pag == PAGINAS[13]:
    st.title("Transparencia: ¿publica el Ayuntamiento lo que la ley le obliga?")
    inv = A.inventario()
    r = inv["resumen_checklist"]; st.plotly_chart(px.pie(names=list(r), values=list(r.values()), hole=.4), use_container_width=True)
    df = pd.DataFrame(inv["checklist"])
    est = st.multiselect("Estado", sorted(df.estado.unique()), default=sorted(df.estado.unique()))
    st.dataframe(df[df.estado.isin(est)][["obligacion", "estado", "base_legal", "fecha", "nota", "url"]], hide_index=True)
    st.caption(f"Auditoría {inv.get('fecha_auditoria')} · revisión en navegador {inv.get('revision_navegador', '')}")

elif pag == PAGINAS[14]:
    st.title("Alertas")
    al = pd.DataFrame(A.alertas())
    st.dataframe(al, hide_index=True)
    st.caption("Plazos, publicaciones que faltan o están desfasadas, y desviaciones de ejecución (>115 % o <70 % del presupuesto inicial en partidas > 1 M€).")

elif pag == PAGINAS[15]:
    st.title("Pregunta a la IA sobre el dinero del Ayuntamiento")
    modo = ia.estado()
    if modo == "pendiente_de_clave":
        st.warning("IA generativa **pendiente de clave** (GEMINI_API_KEY o LiteLLM de AGs-Core). Mientras, se responde buscando en los datos oficiales cargados.")
    else:
        st.success(f"IA activa vía {modo}. Solo puede usar cifras de las fuentes cargadas y debe citarlas.")
    q = st.text_input("Tu pregunta", "¿Cuánto se gastó en servicios sociales el último año?")
    if st.button("Preguntar") and q:
        r = ia.preguntar(q); st.markdown(r["respuesta"])
        with st.expander("Hechos y fuentes que puede usar la IA"):
            st.dataframe(pd.DataFrame(r["hechos"]), hide_index=True)

else:
    st.title("Glosario y fuentes")
    for t, d in {"Derechos reconocidos": "Dinero que el Ayuntamiento tiene derecho a cobrar en el año (aunque aún no lo haya cobrado).",
                 "Obligaciones reconocidas": "Gastos que el Ayuntamiento se ha comprometido a pagar porque el servicio u obra ya se ha hecho.",
                 "Presupuesto inicial": "Lo que se aprueba a principio de año. Luego se modifica (presupuesto definitivo).",
                 "Capítulo": "Agrupación de gastos o ingresos por su naturaleza (personal, compras, inversiones...).",
                 "Política de gasto / programa": "Agrupación por finalidad: servicios sociales, educación, seguridad...",
                 "Remanente de tesorería": "Ahorro acumulado disponible tras pagar y cobrar lo pendiente. Se calcula en la liquidación.",
                 "Regla de gasto": "Límite legal al crecimiento del gasto (LOEPSF art. 12).",
                 "Estabilidad presupuestaria": "Obligación de no tener déficit estructural (LOEPSF art. 3 y 11).",
                 "PMP": "Periodo medio de pago a proveedores; máximo legal 30 días.",
                 "Contrato menor": "Contrato pequeño sin licitación: < 15.000 € (servicios/suministros) o < 40.000 € (obras), sin IVA (LCSP art. 118).",
                 "Euros constantes": "Euros corregidos por la inflación (IPC) para comparar años.",
                 "IQR / z-score": "Medidas estadísticas para detectar valores fuera de lo normal.",
                 "IBI": "Impuesto sobre Bienes Inmuebles; se paga sobre el valor catastral.",
                 "BICE": "Bienes inmuebles de características especiales (aeropuerto, puerto, autopistas...)."}.items():
        st.markdown(f"**{t}:** {d}")
    st.subheader("Manifiesto de fuentes (URL, fecha, SHA-256)")
    st.dataframe(pd.DataFrame(A.manifiesto()), hide_index=True)
    st.write("Actualizar datos: `python -m app.fetchers` (también lo pueden ejecutar los agentes matriz_* de AGs-Core).")
