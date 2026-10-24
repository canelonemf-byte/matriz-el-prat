"""python -m matriz_el_prat [ciclo|borradores]"""
import json, sys
from pathlib import Path
from . import agentes, documentos as D

def borradores(dest="borradores"):
    d = Path(dest); d.mkdir(exist_ok=True)
    an = {a["id"]: a for a in agentes.analizar_propuestas()}
    f1, f2 = an["PRAT-FIS-001"], an["PRAT-FIS-002"]
    (d / "mocion_PRAT-FIS-001_ibi.md").write_text(D.mocion(
        "Revisión del tipo general del IBI urbano",
        "El tipo general vigente en 2026 es 0,6199 % (OF1 art. 7, BOPB 23-12-2025, CVE 202510200458). "
        "Se propone estudiar su reducción a 0,48 %, dentro de la horquilla legal del art. 72 TRLRHL (0,4-1,10 %).",
        ["Encargar a Intervención un informe del impacto recaudatorio con el padrón IBI vigente.",
         "Estudiar bonificaciones legales del art. 74 TRLRHL como alternativa para vivienda habitual."],
        [f"Tipo actual {f1['calculo']['tipo_actual_pct']} %; propuesto 0,48 %.",
         f"Impacto declarado {f1['impacto_declarado_eur']} € → exige base liquidable de {f1['base_implicita_eur']:,} € (PENDIENTE de verificar).",
         *f1["calculo"]["avisos"]],
        beneficio={"beneficio": f1["beneficio"], "beneficiarios": f1["beneficiarios"], "impacto": "PENDIENTE de la base liquidable real"}), encoding="utf-8")
    (d / "alegacion_ordenanzas_fiscales.md").write_text(D.alegacion(
        "Ordenances fiscals del Prat de Llobregat (exercici siguiente)", "",
        ["[Motivo a completar con los resultados del análisis]", *f2["calculo"]["avisos"]],
        "Que se estimen las alegaciones y se modifique la ordenanza en los términos expuestos."), encoding="utf-8")
    (d / "solicitud_informacion_padron_ibi.md").write_text(D.solicitud(
        "Acceso a información pública: base liquidable agregada del IBI por clase y uso (sin datos personales)",
        ["Para evaluar propuestas de modificación de la OF1 es necesario conocer la base liquidable total agregada."],
        "Que se facilite la base liquidable agregada del IBI 2026 por clase (urbana, rústica, BICE) y uso catastral."), encoding="utf-8")
    (d / "mocion_reformas_5_puntos.md").write_text(D.mocion_reformas_5_puntos(), encoding="utf-8")
    return sorted(p.name for p in d.iterdir())

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ciclo"
    print(json.dumps(agentes.ciclo() if cmd == "ciclo" else borradores(), ensure_ascii=False, indent=1, default=str))
