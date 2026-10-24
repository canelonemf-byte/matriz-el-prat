"""Generador de BORRADORES (moción, alegación, solicitud). Nunca presenta, registra ni envía nada:
el interesado los revisa, firma y presenta por sí mismo."""
import datetime as dt
from . import AUTOR, OBJETIVO

CABECERA = ("BORRADOR — NO PRESENTADO. Documento generado por matriz_el_prat para revisión humana. "
            "Debe revisarse, completarse y firmarse por la persona interesada antes de presentarlo.")
RGPD = ("Protección de datos: este borrador no contiene datos personales de terceros. Los datos de la persona "
        "firmante los añade ella misma (RGPD (UE) 2016/679 y LO 3/2018).")

BASES = {
    "mocion": ["RD 2568/1986 (ROF), art. 97.3: definición de moción como propuesta sometida directamente al Pleno",
               "RD 2568/1986 (ROF), art. 91.4: mociones por razones de urgencia en sesiones ordinarias",
               "Ley 7/1985 (LBRL), art. 46.2.b: convocatoria con 2 días hábiles y documentación íntegra a disposición desde la convocatoria",
               "Ley 7/1985 (LBRL), art. 47.1: acuerdos por mayoría simple de los miembros presentes",
               "Ley 7/1985 (LBRL), art. 46.2.e: parte de control del Pleno",
               "Reglament Orgànic Municipal del Prat de Llobregat: PENDIENTE de localizar el texto vigente y su artículo sobre mociones"],
    "alegacion": ["RDL 2/2004 (TRLRHL), art. 17.1: exposición pública del acuerdo provisional durante 30 días como mínimo (hábiles, art. 30.2 Ley 39/2015)",
                  "RDL 2/2004 (TRLRHL), art. 18: legitimación para reclamar",
                  "RDL 2/2004 (TRLRHL), art. 17.3: el Pleno resuelve las reclamaciones",
                  "Ley 39/2015, art. 83: trámite de información pública"],
    "solicitud": ["Ley 39/2015, art. 66: contenido de las solicitudes de iniciación",
                  "Ley 39/2015, art. 16: registros y lugares de presentación",
                  "Ley 39/2015, art. 21: obligación de resolver",
                  "Ley 19/2013 y Llei 19/2014 de Catalunya: derecho de acceso a la información pública (si se piden datos)"],
}


def _pie():
    return f"\n---\nObjetivo: {OBJETIVO}\nAutoría del borrador: {AUTOR}. Generado el {dt.date.today().isoformat()}.\n{RGPD}\n"


def _ben(b):
    b = b or {}
    return (f"### Beneficio para la ciudadanía del Prat\n- Beneficio: {b.get('beneficio') or 'PENDIENTE'}\n"
            f"- Quién se beneficia: {b.get('beneficiarios') or 'PENDIENTE'}\n- Impacto estimado (solo datos reales): {b.get('impacto') or 'PENDIENTE'}\n\n")


def mocion(titulo, exposicion, acuerdos, calculos=None, grupo_politico="", beneficio=None):
    acu = "\n".join(f"{i}. {a}" for i, a in enumerate(acuerdos, 1))
    cal = "\n".join(f"- {c}" for c in (calculos or [])) or "- PENDIENTE"
    return f"""# {CABECERA}

## Moción al Pleno del Ajuntament del Prat de Llobregat: {titulo}

Grupo municipal proponente: {grupo_politico or 'PENDIENTE (una moción solo la puede presentar un grupo municipal o un concejal)'}

{_ben(beneficio)}### Exposición de motivos
{exposicion}

### Datos y cálculos (con fuente)
{cal}

### Propuesta de acuerdos
{acu}

### Fundamento jurídico
""" + "\n".join(f"- {b}" for b in BASES["mocion"]) + _pie()


def alegacion(ordenanza, anuncio_bopb, motivos, peticion, beneficio=None):
    mot = "\n".join(f"{i}. {m}" for i, m in enumerate(motivos, 1))
    return f"""# {CABECERA}

## Alegación (reclamación) en el período de información pública
Ordenanza: {ordenanza}
Anuncio de exposición pública en el BOPB: {anuncio_bopb or 'PENDIENTE (indicar CVE y fecha; el plazo es de 30 días hábiles desde la publicación)'}

Dirigida a: Ple de l'Ajuntament del Prat de Llobregat

Persona interesada: [nombre, DNI y domicilio a completar por la persona firmante]

{_ben(beneficio)}### Motivos
{mot}

### Petición
{peticion}

### Fundamento jurídico
""" + "\n".join(f"- {b}" for b in BASES["alegacion"]) + _pie()


def solicitud(asunto, hechos, solicita, beneficio=None):
    he = "\n".join(f"{i}. {h}" for i, h in enumerate(hechos, 1))
    return f"""# {CABECERA}

## Solicitud por registro de entrada (Ley 39/2015)
Órgano al que se dirige: Ajuntament del Prat de Llobregat (código DIR3 PENDIENTE de verificar)
Asunto: {asunto}

Persona solicitante (art. 66.1.a): [nombre, DNI y medio de notificación a completar]

{_ben(beneficio)}### Hechos y razones (art. 66.1.b)
{he}

### Solicita (art. 66.1.b)
{solicita}

Lugar, fecha y firma (art. 66.1.e): [a completar]

Presentación: la persona interesada la presenta ella misma en la sede electrónica (https://seu.elprat.cat) o en
cualquiera de los registros del art. 16.4 de la Ley 39/2015.

### Fundamento jurídico
""" + "\n".join(f"- {b}" for b in BASES["solicitud"]) + _pie()


def mocion_reformas_5_puntos(grupo_politico=""):
    """Moción de 5 puntos del material de Gemini, CORREGIDA con las leyes y datos reales (docs/gemini/CORRECCIONES.md)."""
    return mocion(
        "Reformas fiscales, de residuos, de movilidad en Mas Blau y de transparencia (2027)",
        "El Prat cuenta en su término con el Aeropuerto Josep Tarradellas Barcelona-El Prat y parte del Puerto de Barcelona. "
        "Los BICE ya tributan al tipo máximo legal del 1,30 % (art. 72.2 TRLRHL; OF1 2026 art. 7.1.d), por lo que no existe margen "
        "adicional por esa vía. Cualquier rebaja del IBI de la vivienda debe financiarse con otros recursos del presupuesto "
        "2026 (poco más de 160 M€ consolidados) y contar con informe de Intervención (LO 2/2012).",
        ["Encargar a Intervención un estudio del impacto de bajar el tipo general del IBI urbano (hoy 0,6199 %) hacia 0,48 % "
         "(mínimo legal 0,4 %, art. 72.1 TRLRHL) y de bonificaciones del art. 74 TRLRHL para vivienda habitual, con el padrón real.",
         "Modificar la OF 26 para implantar el pago por generación (art. 11.3 Ley 7/2022) con reducciones por separación de orgánica "
         "y uso de la deixalleria (art. 11.4), con un porcentaje justificado en un estudio de costes que mantenga la tasa no deficitaria.",
         "Estudiar en la OF 23 una tarifa reducida o simbólica de la Zona Taronja de Mas Blau (hoy 8 €/mes) para trabajadores autorizados, "
         "con informe jurídico sobre el art. 9.1 TRLRHL.",
         "Aprobar un plan de inspección de la vía pública en Mas Blau contra el estacionamiento lucrativo de flotas de aparcamiento del aeropuerto, "
         "con retirada de vehículos conforme a la normativa de tráfico y la OF 8.",
         "Configurar Gestiona para que la convocatoria del Pleno no pueda firmarse sin la documentación íntegra de cada asunto, "
         "como exige el art. 46.2.b LBRL (documentación a disposición desde el mismo día de la convocatoria)."],
        ["Tipo IBI urbano general 2026: 0,6199 %; BICE 1,30 % (OF1 art. 7; BOPB 23-12-2025, CVE 202510200458).",
         "Presupuesto 2026: poco más de 160 M€ consolidados; 117,3 M€ gasto corriente; 21,6 M€ inversiones (elprat.cat).",
         "Zona Taronja Mas Blau: 8 €/mes hasta 16 h/día (desde octubre 2026).",
         "Población: 66.251 habitantes (IDESCAT 2025).",
         "Impacto recaudatorio de la rebaja del IBI: PENDIENTE del padrón."],
        grupo_politico,
        {"beneficio": "IBI y tasa de residuos más justos, aparcamiento laboral más barato, calles libres de aparcamiento ilegal y plenos con documentación a tiempo",
         "beneficiarios": "hogares, trabajadores de Mas Blau y toda la ciudadanía", "impacto": "PENDIENTE (falta padrón IBI y costes de residuos)"})
