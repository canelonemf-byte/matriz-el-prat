# Material de Gemini (generado con Gemini, revisado)

Fuente: conversación compartida https://share.gemini.google/oPC41xW8nuU8 (creada el 23-10-2026, publicada el 24-10-2026).
Contiene: «Informe Ejecutivo Pleno Municipal El Prat», «Proyecto Magna El Prat 2027-2031», «Proyecto Reformas El Prat 2027-2030»,
la arquitectura de 5 agentes y 15 sub-agentes, la tabla de fuentes, 5 KPI, el flujo de trabajo y el registro maestro.
Aquí se resume y se corrige; no se copian los PDF/HTML (no estaban accesibles). Todo lo que no está en `../../catalogo_mejoras.yaml`
ni en `CORRECCIONES.md` se ha integrado así:

| contenido Gemini | dónde está en matriz_el_prat |
|---|---|
| 5 agentes / 15 sub-agentes | `matriz_el_prat/agentes.py` (funcionan de verdad en el autopilot de AGs-Core) |
| tabla de fuentes | `matriz_el_prat/fuentes.py` y `datos_pendientes.yaml` (solo fuentes comprobadas) |
| 5 KPI | `KPI.md` |
| flujo detección → análisis → documento → tramitación | `README.md` |
| moción de 5 puntos | `matriz_el_prat/documentos.py` → `mocion_reformas_5_puntos()` (BORRADOR corregido) |
| registro maestro | `catalogo_mejoras.yaml` (valores originales + verificación) |
