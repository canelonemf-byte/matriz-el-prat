# Hallazgos de transparencia (auditoría automática 2026-10-24) — BORRADOR de trabajo

Fuente: `inventario_obligaciones.yaml` (regenerable con `python scripts/generar_inventario.py`; el sub-agente
`sub_5_3_gestor_portal_transparencia` lo repite en cada ciclo). Cada carencia es un posible **beneficio ciudadano**:
publicarla permite controlar el gasto y ejercer derechos. Antes de reclamar, confirmar en navegador: el portal AOC
carga parte del contenido con JavaScript.

| prioridad | carencia | base legal | beneficio para la ciudadanía |
|---|---|---|---|
| 1 | **Ordenanzas fiscales 2027** aprobadas inicialmente (Ple 22-10-2026) sin texto localizado aún | TRLRHL art. 17.1-2 | 30 días para reclamar: vecinos y grupos pueden pedir bonificaciones (IBI vivienda, residuos) |
| 1 | **Cuenta general**: última actualización 11-10-2022 | Llei 19/2014 art. 11.1.c; Ley 19/2013 art. 8.1.e; TRLRHL art. 212 | ver la situación patrimonial real y el remanente disponible |
| 1 | **Ejecución presupuestaria trimestral**: sin contenido | Llei 19/2014 art. 11.1.a; Ley 19/2013 art. 8.1.d | seguir durante el año si se ejecutan las inversiones prometidas |
| 2 | **Bases de ejecución del presupuesto**: sin contenido | Llei 19/2014 art. 11.1.a | conocer las reglas de gasto y subvenciones |
| 2 | **Auditorías / control financiero**: sin informes (2023) | Llei 19/2014 art. 11.1.c | saber si el dinero se usa correctamente |
| 2 | **Modificaciones de contratos**: 2023 | Llei 19/2014 art. 13.1.d | detectar sobrecostes |
| 2 | **Tipos impositivos** del dataset AOC en 2025 (IBI 0,63) cuando en 2026 rige 0,6199 | Llei 19/2014 art. 11 | evitar información fiscal errónea |
| 2 | **Convocatorias del Pleno**: 01-04-2025 | LBRL art. 46.2.b; Llei 19/2014 art. 10 | saber qué se vota con antelación |
| 3 | Resoluciones de acceso a la información, proyectos normativos en curso, plan anual normativo, convenios urbanísticos, ejecución de convenios, agenda de altos cargos: sin contenido o antiguos | Llei 19/2014 arts. 10, 14, 55; Ley 39/2015 art. 132 | participación previa y control |
| 3 | Mociones aprobadas: no hay listado propio (solo dentro de las actas) | Llei 19/2014 art. 10.1 | seguimiento del cumplimiento de mociones |
| 3 | OF 23 (aparcamiento) y OF de residuos: texto consolidado no localizado | TRLRHL art. 17.4 | conocer tarifas y bonificaciones |

Siguiente paso posible (lo decide y presenta el autor): solicitud de acceso a la información (Llei 19/2014 art. 18;
plazo de 1 mes; reclamación ante la GAIP) — plantilla `documentos.solicitud()`.


## Correcciones tras revisión en navegador (2026-10-24)

- `bases-d-execucio-del-pressupost-188` → **publicado**: bases 2020-2025; la más reciente: https://seu.elprat.cat/siac/Tablon_ver_doc.aspx?id=12762
- **solo_enlace** (solo introducción + enlace externo, sin documento propio): organigrama, ejecución presupuestaria trimestral, auditorías de cuentas (actualizada 24/07/2023), resoluciones de acceso a la información, plan anual normativo, agenda de altos cargos (solo enlaza a la lista de concejales).
- **sin_documentos**: ejecución de convenios y convenios urbanísticos.
- `mociones_aprobadas`: no hay apartado específico; extraer de las actas del Pleno (`actes-de-ple`).
- `of_tasa_residuos` y `of23_aparcamiento` → **publicado** en CIDO (aprobación definitiva 15/09/2026): https://cido.diba.cat/normativa_local/20498914/ordenances-fiscals-per-a-lany-2026-ajuntament-del-prat-de-llobregat
- `of_2027_aprobacion_inicial`: a 2026-10-24 aún no publicadas en CIDO ni BOPB.

Recuento actualizado del checklist (57): publicado 33, desactualizado 10, solo_enlace 6, no_verificado 4, no_encontrado 2, sin_documentos 2.
