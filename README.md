# matriz_el_prat

Sistema multi-agente de auditoría ciudadana y gobernanza municipal del Prat de Llobregat (Barcelona, España).
Autoría: Lázaro López Paz, El Prat de Llobregat, Barcelona, España (ORCID 0000-0001-8601-1963), con asistencia de IA. Licencia MIT.

## Objetivo
Mejorar la vida de la ciudadanía del Prat de Llobregat. Todo hallazgo o propuesta indica su **beneficio ciudadano**
(impuestos y tasas más bajos o más justos, vivienda social, movilidad, medio ambiente, transparencia), **quién se beneficia**
y su **impacto estimado solo con datos reales** (si no hay datos: PENDIENTE). Las propuestas se ordenan por beneficio ciudadano.

## Flujo
1. **Detección** (sub-agente): lee fuentes públicas oficiales y guarda cada registro en SQLite con URL de origen y fecha (retención permanente).
2. **Análisis y cálculo** (agente principal): fórmulas del TRLRHL (RDL 2/2004) con los tipos vigentes de la OF1 2026.
3. **Documento técnico**: BORRADORES de moción al Pleno, alegación en información pública (BOPB) y solicitud por registro (Ley 39/2015).
4. **Tramitación**: la hace la persona interesada. Este código **nunca presenta, registra ni envía nada**.

## Agentes
| agente | sub-agentes | fuente |
|---|---|---|
| legal_prat | sub_1_1_monitor_boe_dogc, sub_1_2_rastreador_bopb, sub_1_3_gestor_rom_secretaria | API BOE, DOGC (n6hn-rmy7), RSS BOPB; ROM pendiente |
| fiscal_prat | sub_2_1_inspector_ejecucion_presupuestaria, sub_2_2_calculador_bics_aena_puerto, sub_2_3_optimizador_ibi_y_tasas | OF1 2026 (BOPB CVE 202510200458); CONPREL pendiente |
| urba_prat | sub_3_1_gestor_vpo_prat_espais, sub_3_2_controlador_movilidad_mas_blau, sub_3_3_inspector_dominio_publico_grua | pendientes de datos |
| eco_prat | sub_4_1_gestor_tasa_residuos_pxg, sub_4_2_protector_delta_la_ricarda, sub_4_3_monitor_energia_y_agua | filtro sobre BOE/DOGC/BOPB; resto pendiente |
| audit_prat | sub_5_1_auditor_gestiona_pleno, sub_5_2_inspector_placsp_contratos, sub_5_3_gestor_portal_transparencia | PLACSP ATOM, dades obertes El Prat |

Lo que falta está en `datos_pendientes.yaml`. El catálogo de mejoras (6 propuestas, valores originales + verificación verificado/no_verificado/incorrecto con fuente) está en `catalogo_mejoras.yaml`; los originales en `data/`.

## Uso
```bash
pip install -r requirements.txt
python -m matriz_el_prat ciclo        # ingesta + análisis
python -m matriz_el_prat borradores   # genera borradores en borradores/
pytest -q
```

## Protección de datos
No se recogen datos personales; NIF/DNI/NIE y correos se enmascaran antes de guardar (RGPD (UE) 2016/679, LO 3/2018).
