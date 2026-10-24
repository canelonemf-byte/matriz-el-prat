"""IA explicativa con fuentes: usa LiteLLM de AGs-Core (LITELLM_BASE_URL) o GEMINI_API_KEY si existen; si no, 'pendiente de clave'
y respuesta determinista por búsqueda de hechos. Nunca inventa cifras: solo puede usar los hechos facilitados. MIT."""
from __future__ import annotations
import json, os, re, urllib.request
from .analitica import hechos_para_ia

SISTEMA = ("Eres un asistente ciudadano del Prat de Llobregat. Responde en castellano sencillo. USA SOLO las cifras de la lista de HECHOS; "
           "si la respuesta no está en los hechos, dilo y explica cómo obtenerla (p. ej. solicitud de acceso a la información, Llei 19/2014). "
           "Cita la fuente [n] de cada cifra. No inventes números.")


def estado() -> str:
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    base = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    try:
        urllib.request.urlopen(base + "/health/liveliness", timeout=2)
        return "litellm"
    except Exception:  # noqa: BLE001
        return "pendiente_de_clave"


def _busqueda(pregunta: str, hechos):
    pal = {w for w in re.findall(r"\w{4,}", pregunta.lower())}
    sc = sorted(((sum(w in h["hecho"].lower() for w in pal), i, h) for i, h in enumerate(hechos)), reverse=True)
    top = [(i, h) for s, i, h in sc if s > 0][:6]
    if not top:
        return "No encuentro ese dato en las fuentes cargadas. Puedes pedirlo con una solicitud de acceso a la información pública (Llei 19/2014, art. 18)."
    return "Datos encontrados (sin IA generativa, modo pendiente de clave):\n" + "\n".join(f"- {h['hecho']} [fuente: {h['fuente']}]" for i, h in top)


def preguntar(pregunta: str) -> dict:
    hechos = hechos_para_ia()
    modo = estado()
    lista = "\n".join(f"[{i}] {h['hecho']} (fuente: {h['fuente']})" for i, h in enumerate(hechos))
    msgs = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": f"HECHOS:\n{lista}\n\nPREGUNTA: {pregunta}"}]
    try:
        if modo == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.environ['GEMINI_API_KEY']}"
            body = {"contents": [{"parts": [{"text": SISTEMA + "\n\n" + msgs[1]["content"]}]}]}
            r = json.loads(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=60).read())
            txt = r["candidates"][0]["content"]["parts"][0]["text"]
        elif modo == "litellm":
            base = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
            body = {"model": os.getenv("MATRIZ_LLM_MODEL", "gemini"), "messages": msgs, "temperature": 0}
            req = urllib.request.Request(base + "/v1/chat/completions", json.dumps(body).encode(),
                                         {"Content-Type": "application/json", "Authorization": "Bearer " + os.getenv("LITELLM_API_KEY", "")})
            txt = json.loads(urllib.request.urlopen(req, timeout=60).read())["choices"][0]["message"]["content"]
        else:
            return {"modo": modo, "respuesta": _busqueda(pregunta, hechos), "hechos": hechos}
        return {"modo": modo, "respuesta": txt, "hechos": hechos}
    except Exception as e:  # noqa: BLE001
        return {"modo": f"error_{modo}", "respuesta": f"IA no disponible ({str(e)[:120]}).\n" + _busqueda(pregunta, hechos), "hechos": hechos}
