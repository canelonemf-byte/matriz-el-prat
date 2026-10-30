from fastapi import FastAPI
import json

app = FastAPI(
    title="Grok Bridge - Proyecto Matriz El Prat",
    description="Endpoint dedicado para que Grok IA lea e interactúe con el registro maestro del proyecto.",
    version="1.7.2",
)


@app.get("/api/grok/sync")
def grok_sync():
    try:
        with open("base_datos_master_mejoras_el_prat.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "system_prompt_for_grok": (
                "Actúa como auditor y analista de este sistema municipal. "
                "Verifica que no haya déficit y propón mejoras respetando la regla de cero números rojos."
            ),
            "proyecto_data": data,
        }
    except Exception as e:
        return {"error": str(e)}


# Para ejecutar: uvicorn api_grok_bridge:app --reload --port 8000
