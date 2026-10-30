import streamlit as st
import json
import pandas as pd

st.set_page_config(
    page_title="Proyecto Matriz El Prat - Propuesta Ciudadana",
    page_icon="🏛️",
    layout="wide",
)

# Cargar base de datos
try:
    with open("base_datos_master_mejoras_el_prat.json", "r", encoding="utf-8") as f:
        data = json.load(f)["registro_maestro_mejoras_el_prat"]
except Exception as e:
    st.error(f"Error cargando la base de datos: {e}")
    st.stop()


def calcular_metricas_ordinarias(catalogo):
    ingresos = 0.0
    gastos = 0.0
    for item in catalogo:
        if item.get("fuera_presupuesto_ordinario"):
            continue
        impacto = float(item.get("impacto_presupuestario_eur") or 0)
        if impacto >= 0:
            ingresos += impacto
        else:
            gastos += impacto
    return ingresos, gastos, ingresos + gastos


ingresos, gastos, superavit = calcular_metricas_ordinarias(data["catalogo_mejoras"])

# Cabecera y Declaración de Independencia
st.title("🏛️ Proyecto Matriz El Prat de Llobregat")
st.subheader("Simulador Presupuestario e Iniciativa Ciudadana Independiente")
st.caption(
    f"Autor: {data['autor']} | Ubicación: {data['municipio']} | "
    f"Versión: {data['version']} ({data['ultima_actualizacion']})"
)

st.warning(
    "⚠️ **Aviso de Independencia:** Este proyecto es una iniciativa privada, individual e independiente "
    "redactada por Lázaro López Paz. **No tiene relación ni vinculación institucional con el Ayuntamiento "
    "de El Prat de Llobregat.** Su objetivo es divulgar ideas de gestión financiera y optimización tributaria "
    "para el conocimiento de la ciudadanía."
)

# Métricas Principales (calculadas desde el catálogo; VPO fuera del ordinario)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingresos Nuevos (BICS y otros)", f"+{ingresos:,.0f} €/año".replace(",", "."))
with col2:
    st.metric("Inversión Rebajas e Incentivos", f"{gastos:,.0f} €/año".replace(",", "."))
with col3:
    st.metric(
        "Superávit Garantizado",
        f"+{superavit:,.0f} €/año".replace(",", "."),
        delta="Cero Números Rojos",
    )
with col4:
    st.metric("Total Propuestas", len(data["catalogo_mejoras"]))

st.caption(
    "Nota: el Plan 1.500 VPO (PRAT-VIV-001, −54 M€) está marcado como inversión plurianual "
    "fuera del presupuesto ordinario y no entra en estas métricas."
)

st.divider()

# Catálogo de Mejoras
st.header("📋 Catálogo de Propuestas e Impacto Presupuestario")

df = pd.DataFrame(data["catalogo_mejoras"])
df_display = df[
    [
        "id",
        "area",
        "titulo",
        "fundamento_legal",
        "impacto_presupuestario_eur",
        "beneficiarios_kpi",
        "estado",
        "fuera_presupuesto_ordinario",
    ]
].copy()
df_display.columns = [
    "ID",
    "Área",
    "Título de la Propuesta",
    "Base Legal",
    "Impacto (€)",
    "Beneficiarios / KPI",
    "Estado",
    "Fuera presup. ordinario",
]

st.dataframe(df_display, use_container_width=True)

# Simulador de Ahorro IBI Residencial
st.divider()
st.header("🧮 Simulador de Ahorro IBI Residencial para Familias")
valor_catastral = st.number_input(
    "Introduce el Valor Catastral de tu Vivienda (€):",
    min_value=10000,
    max_value=500000,
    value=90000,
    step=5000,
)

ibi_actual = valor_catastral * 0.0062
ibi_propuesto = valor_catastral * 0.0048
ahorro = ibi_actual - ibi_propuesto

st.info(
    f"**Cuota IBI Actual (0,62%):** {ibi_actual:,.2f} €/año\n\n"
    f"**Cuota IBI Propuesta (0,48%):** {ibi_propuesto:,.2f} €/año\n\n"
    f"🎉 **Ahorro familiar neto:** **{ahorro:,.2f} €/año** "
    f"(0,14% del valor catastral)"
)

st.divider()
st.markdown(
    "🔗 **Notebook de Análisis en Profundidad:** "
    "[Proyecto Matriz El Prat: Gobernanza, Finanzas y Servicios Municipales]"
    "(https://notebooklm.google.com/notebook/0313f51e-758b-4d6d-80f1-2a29ce453165)"
)
