# 🏛️ Proyecto Matriz El Prat de Llobregat (v1.7.2 Streamlit)

> **Propuesta Ciudadana Independiente para la Optimización Presupuestaria, Transparencia y Mejora de Servicios Públicos**

**Versión 1.7.2** — 2026-10-30

> Este directorio (`proyecto_matriz_v1_7_2/`) convive con el repositorio principal `matriz-el-prat` sin sustituir su código, catálogo YAML ni tests existentes.

---

### ⚠️ AVISO DE DESVINCULACIÓN INSTITUCIONAL E INDEPENDENCIA
Este proyecto es una **iniciativa privada, individual e independiente** elaborada a título personal por **Lázaro López Paz** (El Prat de Llobregat, Barcelona, España), con asistencia de inteligencia artificial.

* **Sin relación oficial:** Este trabajo **NO** representa, **NO** está vinculado ni cuenta con el patrocinio del **Ayuntamiento de El Prat de Llobregat**.
* **Finalidad:** Divulgación ciudadana de ideas de gestión financiera y optimización tributaria.

---

## 📌 Resumen del Ecosistema

El proyecto articula **12 iniciativas ciudadanas independientes** diseñadas bajo una **Regla de Oro Presupuestaria de Cero Déficit y Cero Subidas de Impuestos para los Residentes**. El balance ordinario estimado (excluyendo la inversión plurianual VPO) es de **+300.000 €/año**.

1. **Rebaja del IBI Residencial al 0,48%** (PRAT-FIS-001, −2,7 M€). El ahorro familiar es el **0,14% del valor catastral** (p. ej. **126 €/año** con 90.000 €; **280–540 €/año** con 200.000–386.000 €).
2. **Recargo del IBI BICS al 1,30%** para AENA / Puerto de Barcelona (PRAT-FIS-002, Art. 72.2 TRLRHL, **+6,1 M€/año**).
3. **Bonificación del 40% en la Tasa de Residuos** por Pago por Generación / PxG (PRAT-ECO-001, −1,2 M€).
4. **Tarjeta de Movilidad Laboral Mas Blau** (PRAT-URB-001, impacto 0 € en presupuesto ordinario).
5. **Plan 1.500 VPO** en Eixample Sud y ARE (PRAT-VIV-001, −54 M€): **inversión plurianual fuera del presupuesto ordinario**.
6. **Bloqueo tecnológico en Gestiona** por falta de expediente previo (PRAT-LEG-001; borrador de moción ciudadana).
7. **Plan de Shock de Limpieza**, hidrolimpieza y control GPS/NFC a la contrata (PRAT-LIM-001).
8. **Control de incivismo canino** y neutralización de orines **sin ADN** (PRAT-LIM-002, +0,15 M€).
9. **Impuesto de Perros con devolución 100%** condicionada a evidencia de limpieza y uso de pipican (PRAT-LIM-003, +0,45 M€).
10. **Complemento salarial dignificador** para +600 trabajadores de servicios públicos (PRAT-SAL-001, −1,8 M€).
11. **Programa Bono-Comercio Prat** (PRAT-COM-001, −0,7 M€).
12. **Plan de Excelencia en Servicios Públicos** (PRAT-SER-001, impacto 0 €).

---

## 📁 Contenido de este directorio

```
proyecto_matriz_v1_7_2/
├── app.py                                  # Aplicación interactiva web (Streamlit)
├── api_grok_bridge.py                      # Bridge FastAPI para sincronización con Grok
├── base_datos_master_mejoras_el_prat.json  # Base de datos central (v1.7.2)
├── proyecto_matriz_el_prat.json            # Definición de la matriz de agentes
├── el_prat_multi_agent_system.py           # Orquestador Python multi-agente
├── requirements.txt                        # Dependencias de este subproyecto
├── workflow_pendiente/auditoria_diaria.yml # Workflow listo para copiar a .github/workflows/
└── README.md                               # Esta documentación
```

---

## 🚀 Instalación y Ejecución Local

Desde la raíz del repositorio:

```bash
git clone https://github.com/canelonemf-byte/matriz-el-prat.git
cd matriz-el-prat/proyecto_matriz_v1_7_2
pip install -r requirements.txt
streamlit run app.py
```

Diagnóstico CLI:

```bash
cd matriz-el-prat/proyecto_matriz_v1_7_2
python el_prat_multi_agent_system.py
```

Bridge FastAPI (opcional):

```bash
cd matriz-el-prat/proyecto_matriz_v1_7_2
uvicorn api_grok_bridge:app --reload --port 8000
```

---

## ⚙️ Workflow de GitHub Actions (pendiente de activar)

El archivo `workflow_pendiente/auditoria_diaria.yml` **no** está en `.github/workflows/` porque el token OAuth usado para este PR no tiene scope `workflow`.

Para activarlo manualmente:

1. Copiar `proyecto_matriz_v1_7_2/workflow_pendiente/auditoria_diaria.yml` a `.github/workflows/auditoria_diaria.yml` (en la raíz del repo).
2. El YAML ya usa `defaults.run.working-directory: proyecto_matriz_v1_7_2` y cache de pip con `cache-dependency-path` apuntando a este subdirectorio.

---

## 🔗 Recursos y Enlaces Públicos

* **Cuaderno Interactivo en NotebookLM:** [Proyecto Matriz El Prat: Gobernanza, Finanzas y Servicios Municipales](https://notebooklm.google.com/notebook/0313f51e-758b-4d6d-80f1-2a29ce453165)
* **Autoría:** Lázaro López Paz, El Prat de Llobregat, Barcelona, España, con asistencia de inteligencia artificial
* **Repositorio:** https://github.com/canelonemf-byte/matriz-el-prat
