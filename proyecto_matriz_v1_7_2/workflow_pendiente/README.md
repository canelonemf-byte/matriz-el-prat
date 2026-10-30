# Workflow pendiente de activación

Copia `auditoria_diaria.yml` a `.github/workflows/auditoria_diaria.yml` en la raíz del repositorio cuando dispongas de un token o cuenta con permiso para crear workflows (scope OAuth `workflow`, o la UI de GitHub).

El YAML ya configura `working-directory: proyecto_matriz_v1_7_2` y `cache-dependency-path` hacia este subproyecto.
