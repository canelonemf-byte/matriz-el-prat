"""IA explicativa con fuentes. Orden: xAI (GROK_API_KEY del entorno o ~/.secrets/xai.env) >
Gemini directo (GEMINI_API_KEY o ~/.secrets/gemini.env) > LiteLLM de AGs-Core > búsqueda determinista
('pendiente_de_clave'). La IA solo recibe hechos con fuente; toda cifra de la respuesta se valida
contra esos hechos (tolerancia 1 %) y las no encontradas se marcan. La clave nunca se registra ni
se guarda en el repositorio. MIT. Autoría: Lázaro López Paz, El Prat de Llobregat, Barcelona, España,
con asistencia de IA."""
from __future__ import annotations
import json, os, pathlib, re, urllib.request
from .analitica import hechos_para_ia

XAI_URL = "https://api.x.ai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
SISTEMA = ("Eres un asistente ciudadano del Prat de Llobregat. Responde en castellano sencillo. USA SOLO las cifras de la lista de HECHOS "
           "(cópialas tal cual, sin redondear ni calcular cifras nuevas salvo restas o sumas simples que expliques); "
           "si la respuesta no está en los hechos, dilo y explica cómo obtenerla (solicitud de acceso, Llei 19/2014 art. 18). "
           "Cita la fuente [n] tras cada cifra. No inventes números, nombres de personas ni datos personales.")


def _xai_key() -> str:
    k = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    if k:
        return k
    f = pathlib.Path(os.getenv("XAI_ENV_FILE", pathlib.Path.home() / ".secrets" / "xai.env"))
    try:
        for line in f.read_text().splitlines():
            if line.strip().startswith(("GROK_API_KEY=", "XAI_API_KEY=")):
                return line.split("=", 1)[1].strip().strip('"\'')
    except OSError:
        pass
    return ""


def _gemini_key() -> str:
    k = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if k:
        return k
    f = pathlib.Path(os.getenv("GEMINI_ENV_FILE", pathlib.Path.home() / ".secrets" / "gemini.env"))
    try:
        for line in f.read_text().splitlines():
            if line.strip().startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
                return line.split("=", 1)[1].strip().strip('"\'')
    except OSError:
        pass
    return ""


def _litellm_vivo() -> bool:
    try:
        urllib.request.urlopen(os.getenv("LITELLM_BASE_URL", "http://localhost:4000") + "/health/liveliness", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


def estado() -> str:
    if os.getenv("MATRIZ_IA_OFF"):
        return "pendiente_de_clave"
    if _xai_key():
        return "xai"
    if _gemini_key():
        return "gemini"
    if _litellm_vivo():
        return "litellm"
    return "pendiente_de_clave"


def modelo(modo: str) -> str:
    return {
        "xai": os.getenv("MATRIZ_XAI_MODEL", "grok-4.7"),
        "gemini": os.getenv("MATRIZ_GEMINI_MODEL", "gemini-3.5-flash"),
        "litellm": os.getenv("MATRIZ_LLM_MODEL", "gemini"),
    }.get(modo, os.getenv("MATRIZ_LLM_MODEL", "gemini"))


def _post(url, body, auth=""):
    h = {"Content-Type": "application/json"}
    if auth:
        h["Authorization"] = "Bearer " + auth
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), h), timeout=180).read())


def chat(sistema: str, usuario: str, modo: str | None = None) -> str:
    modo = modo or estado()
    msgs = [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]
    if modo == "xai":
        return _post(XAI_URL, {"model": modelo(modo), "messages": msgs, "temperature": 0}, _xai_key())["choices"][0]["message"]["content"]
    if modo == "gemini":
        key = _gemini_key()
        url = GEMINI_URL.format(model=modelo(modo), key=key)
        r = _post(url, {"contents": [{"parts": [{"text": sistema + "\n\n" + usuario}]}]})
        return r["candidates"][0]["content"]["parts"][0]["text"]
    if modo == "litellm":
        base = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
        return _post(base + "/v1/chat/completions", {"model": modelo(modo), "messages": msgs, "temperature": 0},
                     os.getenv("LITELLM_API_KEY") or os.getenv("LITELLM_MASTER_KEY", ""))["choices"][0]["message"]["content"]
    raise RuntimeError("sin IA")


_NUM = re.compile(r"(?<![\w\[])(\d{1,3}(?:[.,\s ]\d{3})+(?:[,.]\d+)?|\d+(?:[,.]\d+)?)\s*(M€|millones|mill\.|k€|mil\b|%)?", re.I)


def _valor(t: str, suf: str | None):
    t = t.replace(" ", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t) or re.fullmatch(r"\d+,\d+", t):
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    v = float(t)
    s = (suf or "").lower()
    return v * 1e6 if s in ("m€", "millones", "mill.") else v * 1e3 if s in ("k€", "mil") else v


def numeros(texto: str) -> list[tuple[str, float]]:
    return [(m.group(0).strip(), _valor(m.group(1), m.group(2))) for m in _NUM.finditer(texto)]


def validar(texto: str, fuentes: str) -> list[str]:
    """Cifras de la respuesta (>= 100, no años 1990-2035) que no aparecen en los datos (tolerancia 1 % para redondeos)."""
    base = []
    for crudo, v in numeros(fuentes):  # "15,414" es ambiguo (decimal o miles): se aceptan ambas lecturas
        base += [v, v * 1000] if re.fullmatch(r"\d{1,3}[,.]\d{3}", crudo) else [v]
    malos = []
    for crudo, v in numeros(texto):
        if v < 100 or (1990 <= v <= 2035 and float(v).is_integer() and "." not in crudo and "," not in crudo):
            continue
        if not any(abs(v - b) <= 0.01 * max(abs(b), 1) for b in base):
            malos.append(crudo)
    return sorted(set(malos))


def _busqueda(pregunta: str, hechos):
    pal = {w for w in re.findall(r"\w{4,}", pregunta.lower())}
    sc = sorted(((sum(w in h["hecho"].lower() for w in pal), i, h) for i, h in enumerate(hechos)), reverse=True)
    top = [(i, h) for s, i, h in sc if s > 0][:6]
    if not top:
        return "No encuentro ese dato en las fuentes cargadas. Puedes pedirlo con una solicitud de acceso a la información pública (Llei 19/2014, art. 18)."
    return "Datos encontrados (sin IA generativa):\n" + "\n".join(f"- {h['hecho']} [fuente: {h['fuente']}]" for i, h in top)


def con_validacion(txt: str, fuentes: str) -> tuple[str, list[str]]:
    malos = validar(txt, fuentes)
    if malos:
        txt += "\n\n> ⚠️ Cifras no encontradas en los datos de origen (verificar antes de usar): " + ", ".join(malos)
    return txt, malos


def preguntar(pregunta: str) -> dict:
    hechos = hechos_para_ia()
    modo = estado()
    lista = "\n".join(f"[{i}] {h['hecho']} (fuente: {h['fuente']})" for i, h in enumerate(hechos))
    if modo == "pendiente_de_clave":
        return {"modo": modo, "modelo": "", "respuesta": _busqueda(pregunta, hechos), "hechos": hechos, "no_verificadas": []}
    try:
        txt = chat(SISTEMA, f"HECHOS:\n{lista}\n\nPREGUNTA: {pregunta}", modo)
        txt, malos = con_validacion(txt, lista)
        return {"modo": modo, "modelo": modelo(modo), "respuesta": txt, "hechos": hechos, "no_verificadas": malos}
    except Exception as e:  # noqa: BLE001  (sin detalles que puedan contener la clave)
        # Cascada: si falla el proveedor preferido, intentar el siguiente
        for alt in ("gemini", "litellm"):
            if alt == modo:
                continue
            if alt == "gemini" and not _gemini_key():
                continue
            if alt == "litellm" and not _litellm_vivo():
                continue
            try:
                txt = chat(SISTEMA, f"HECHOS:\n{lista}\n\nPREGUNTA: {pregunta}", alt)
                txt, malos = con_validacion(txt, lista)
                return {"modo": alt, "modelo": modelo(alt), "respuesta": txt, "hechos": hechos, "no_verificadas": malos,
                        "fallback_desde": modo}
            except Exception:  # noqa: BLE001
                continue
        return {"modo": f"error_{modo}", "modelo": modelo(modo), "respuesta": f"IA no disponible ({type(e).__name__}).\n" + _busqueda(pregunta, hechos),
                "hechos": hechos, "no_verificadas": []}
