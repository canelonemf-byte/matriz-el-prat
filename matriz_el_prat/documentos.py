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
               "Ley 7/1985 (LBRL), art. 46.2.e: parte de control del Pleno",
               "Reglament Orgànic Municipal del Prat de Llobregat: PENDIENTE de localizar el texto vigente y su artículo sobre mociones"],
    "alegacion": ["RDL 2/2004 (TRLRHL), art. 17.1: exposición pública mínima de 30 días hábiles del acuerdo provisional",
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
